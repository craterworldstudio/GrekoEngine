import struct
from typing import List, Tuple, Union

class GLTFValidationError(RuntimeError):
    pass

# componentType → (struct format char, byte size)
_COMPONENT_TYPE_MAP = {
    5126: ("f", 4),  # FLOAT
    5125: ("I", 4),  # UNSIGNED_INT (32-bit indices)  <-- ADD THIS
    5123: ("H", 2),  # UNSIGNED_SHORT (16-bit indices)
    5121: ("B", 1),  # UNSIGNED_BYTE (rarely used for indices)
}

# accessor.type → number of components
_TYPE_COMPONENT_COUNT = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT4": 16,
}

def validate_gltf(json_data: dict) -> None:
    if "buffers" not in json_data:
        raise GLTFValidationError("Missing 'buffers'")

    if len(json_data["buffers"]) != 1:
        raise GLTFValidationError(
            "Only single-buffer glTF files are supported (VRM requirement)"
        )

    if "bufferViews" not in json_data:
        raise GLTFValidationError("Missing 'bufferViews'")

    if "accessors" not in json_data:
        raise GLTFValidationError("Missing 'accessors'")


def get_buffer_view(
    json_data: dict,
    bin_blob: memoryview,
    index: int
) -> tuple[memoryview, dict]:
    try:
        bv = json_data["bufferViews"][index]
    except IndexError:
        raise GLTFValidationError(f"bufferView {index} out of range")

    offset = bv.get("byteOffset", 0)
    length = bv["byteLength"]

    end = offset + length
    if end > len(bin_blob):
        raise GLTFValidationError("bufferView exceeds BIN size")

    return bin_blob[offset:end], bv


def read_accessor(
    json_data: dict,
    bin_blob: memoryview,
    accessor_index: int
) -> List[Union[int, Tuple[float, ...]]]:

    try:
        acc = json_data["accessors"][accessor_index]
    except IndexError:
        raise GLTFValidationError(f"Accessor {accessor_index} out of range")

    if "bufferView" not in acc:
        raise GLTFValidationError("Sparse accessors are not supported")

    buffer_view_index = acc["bufferView"]
    raw_view, bv = get_buffer_view(json_data, bin_blob, buffer_view_index)

    component_type = acc["componentType"]
    accessor_type = acc["type"]
    count = acc["count"]

    if component_type not in _COMPONENT_TYPE_MAP:
        raise GLTFValidationError(f"Unsupported componentType {component_type}")

    if accessor_type not in _TYPE_COMPONENT_COUNT:
        raise GLTFValidationError(f"Unsupported accessor type {accessor_type}")

    fmt_char, component_size = _COMPONENT_TYPE_MAP[component_type]
    component_count = _TYPE_COMPONENT_COUNT[accessor_type]

    accessor_offset = acc.get("byteOffset", 0)
    stride = bv.get("byteStride")

    element_size = component_size * component_count
    if stride is None:
        stride = element_size

    fmt = "<" + fmt_char * component_count

    results = []

    for i in range(count):
        start = accessor_offset + i * stride
        end = start + element_size

        if end > len(raw_view):
            raise GLTFValidationError(
                "Accessor read exceeds bufferView bounds"
            )

        values = struct.unpack_from(fmt, raw_view, start)

        # SCALAR returns int, vectors return tuple
        if component_count == 1:
            results.append(values[0])
        else:
            results.append(values)

    return results
