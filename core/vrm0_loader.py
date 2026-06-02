# core/vrm0_loader.py

import json
import struct

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


GLB_MAGIC = 0x46546C67  # glTF
CHUNK_TYPE_JSON = 0x4E4F534A
CHUNK_TYPE_BIN = 0x004E4942


@dataclass
class VRM0ParsedGLB:
    json: dict
    bin_blob: memoryview | None
    header: dict

    vrm_version: int = 0
    vrm_extension: Optional[dict] = None


class VRM0LoaderError(RuntimeError):
    pass


def load_vrm0(vrm_path: str | Path):

    path = Path(vrm_path)

    if not path.exists():
        raise VRM0LoaderError(f"VRM0 file not found: {path}")

    print(f"[VRM0] Loading: {path}")

    raw = path.read_bytes()

    if len(raw) < 12:
        raise VRM0LoaderError("Invalid GLB/VRM file")

    # =========================
    # HEADER
    # =========================

    magic, version, total_length = struct.unpack_from(
        "<III",
        raw,
        0
    )

    if magic != GLB_MAGIC:
        raise VRM0LoaderError("Invalid GLB magic")

    if version != 2:
        raise VRM0LoaderError(
            f"Unsupported GLB version: {version}"
        )

    if total_length != len(raw):
        raise VRM0LoaderError(
            "GLB length mismatch"
        )

    header = {
        "version": version,
        "length": total_length,
    }

    # =========================
    # CHUNKS
    # =========================

    offset = 12

    json_chunk = None
    bin_chunk = None

    while offset < len(raw):

        if offset + 8 > len(raw):
            raise VRM0LoaderError(
                "Unexpected EOF while reading chunk header"
            )

        chunk_length, chunk_type = struct.unpack_from(
            "<II",
            raw,
            offset
        )

        offset += 8

        chunk_end = offset + chunk_length

        if chunk_end > len(raw):
            raise VRM0LoaderError(
                "Chunk exceeds file size"
            )

        chunk_data = memoryview(raw)[offset:chunk_end]

        # =========================
        # JSON
        # =========================

        if chunk_type == CHUNK_TYPE_JSON:

            if json_chunk is not None:
                raise VRM0LoaderError(
                    "Multiple JSON chunks found"
                )

            try:
                json_text = chunk_data.tobytes().decode("utf-8")
                json_chunk = json.loads(json_text)

            except Exception as e:
                raise VRM0LoaderError(
                    f"Failed to decode JSON chunk: {e}"
                )

        # =========================
        # BIN
        # =========================

        elif chunk_type == CHUNK_TYPE_BIN:

            if bin_chunk is not None:
                raise VRM0LoaderError(
                    "Multiple BIN chunks found"
                )

            bin_chunk = chunk_data

        else:
            print(
                f"[VRM0] Skipping unknown chunk type:"
                f" 0x{chunk_type:08X}"
            )

        # 4-byte alignment
        offset = (chunk_end + 3) & ~3

    # =========================
    # VALIDATION
    # =========================

    if json_chunk is None:
        raise VRM0LoaderError(
            "Missing JSON chunk"
        )

    extensions = json_chunk.get("extensions", {})

    if "VRM" not in extensions:
        raise VRM0LoaderError(
            "This is not a VRM0 file"
        )

    vrm_ext = extensions["VRM"]

    # =========================
    # DEBUG
    # =========================

    asset = json_chunk.get("asset", {})

    print("[VRM0] Generator:",
          asset.get("generator"))

    print("[VRM0] glTF Version:",
          asset.get("version"))

    print("[VRM0] Nodes:",
          len(json_chunk.get("nodes", [])))

    print("[VRM0] Meshes:",
          len(json_chunk.get("meshes", [])))

    print("[VRM0] Skins:",
          len(json_chunk.get("skins", [])))

    if bin_chunk:
        print("[VRM0] BIN Size:",
              len(bin_chunk))

    print("[VRM0] VRM0 extension loaded successfully")

    # =========================
    # RETURN
    # =========================

    return VRM0ParsedGLB(
        json=json_chunk,
        bin_blob=bin_chunk,
        header=header,
        vrm_version=0,
        vrm_extension=vrm_ext,
    )