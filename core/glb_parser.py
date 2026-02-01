import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


GLB_MAGIC = 0x46546C67  # b'glTF'
CHUNK_TYPE_JSON = 0x4E4F534A  # b'JSON'
CHUNK_TYPE_BIN = 0x004E4942   # b'BIN\0'


@dataclass
class ParsedGLB:
    json: dict
    bin_blob: Optional[memoryview]
    header: dict

class GLBParseError(RuntimeError):
    pass


def parse_glb(path: str | Path) -> ParsedGLB:
    path = Path(path)

    if not path.exists():
        raise GLBParseError(f"GLB file not found: {path}")

    data = path.read_bytes()
    size = len(data)

    if size < 12:
        raise GLBParseError("File too small to be a valid GLB")

    # ---- Header ----
    magic, version, length = struct.unpack_from("<III", data, 0)

    if magic != GLB_MAGIC:
        raise GLBParseError("Invalid GLB magic (not a glTF binary file)")

    if length != size:
        raise GLBParseError(
            f"GLB length mismatch: header={length}, actual={size}"
        )

    if version != 2:
        raise GLBParseError(f"Unsupported GLB version: {version}")

    header = {
        "version": version,
        "length": length,
    }

    # ---- Chunk parsing ----
    offset = 12
    json_chunk = None
    bin_chunk = None

    while offset < size:
        if offset + 8 > size:
            raise GLBParseError("Unexpected EOF while reading chunk header")

        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8

        chunk_end = offset + chunk_length
        if chunk_end > size:
            raise GLBParseError("Chunk length exceeds file size")

        chunk_data = memoryview(data)[offset:chunk_end]

        if chunk_type == CHUNK_TYPE_JSON:
            if json_chunk is not None:
                raise GLBParseError("Multiple JSON chunks found")
            try:
                json_text = chunk_data.tobytes().decode("utf-8")
                json_chunk = json.loads(json_text)
            except Exception as e:
                raise GLBParseError(f"Failed to decode JSON chunk: {e}")

        elif chunk_type == CHUNK_TYPE_BIN:
            if bin_chunk is not None:
                raise GLBParseError("Multiple BIN chunks found")
            bin_chunk = chunk_data  # memoryview, zero-copy

        else:
            # Unknown chunk — allowed by spec, but log loudly
            print(f"[GLB] Skipping unknown chunk type: 0x{chunk_type:08X}")

        # Chunks are padded to 4-byte alignment
        offset = (chunk_end + 3) & ~3

    if json_chunk is None:
        raise GLBParseError("Missing JSON chunk (invalid GLB)")

    # ---- Minimal debug output (Phase 1 acceptance) ----
    asset = json_chunk.get("asset", {})
    print("[GLB] Generator:", asset.get("generator"))
    print("[GLB] glTF version:", asset.get("version"))
    print("[GLB] Extensions used:", json_chunk.get("extensionsUsed", []))

    if bin_chunk:
        print("[GLB] BIN chunk size:", len(bin_chunk))
    else:
        print("[GLB] No BIN chunk present")

    return ParsedGLB(
        json=json_chunk,
        bin_blob=bin_chunk,
        header=header,
    )
