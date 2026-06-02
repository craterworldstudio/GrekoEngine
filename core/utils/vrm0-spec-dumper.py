import json
from pathlib import Path

from core.glb_parser import parse_glb


def make_json_safe(obj):
    """
    Converts bytes/memoryviews/etc into JSON-safe objects.
    """

    if isinstance(obj, memoryview):
        return {
            "__type__": "memoryview",
            "length": len(obj)
        }

    if isinstance(obj, bytes):
        return {
            "__type__": "bytes",
            "length": len(obj)
        }

    if isinstance(obj, dict):
        return {
            str(k): make_json_safe(v)
            for k, v in obj.items()
        }

    if isinstance(obj, list):
        return [
            make_json_safe(v)
            for v in obj
        ]

    return obj


def export_vrm0_full(vrm_path, out_path="vrm0_data.json"):

    parsed = parse_glb(vrm_path)

    data = {
        "vrm_version": parsed.vrm_version,
        "header": parsed.header,
        "vrm_extension": parsed.vrm_extension,

        # FULL GLTF JSON
        "gltf": parsed.json,
    }

    safe_data = make_json_safe(data)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            safe_data,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(f"✅ Full VRM dump exported to: {out_path}")


if __name__ == "__main__":

    vrm_path = input("VRM Path: ").strip()

    export_vrm0_full(vrm_path)