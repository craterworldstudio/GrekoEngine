# core/vrm0_accessors.py

import struct
import numpy as np


class VRM0AccessorError(RuntimeError):
    pass


# ============================================
# glTF Component Types
# ============================================

_COMPONENT_TYPE_MAP = {

    # BYTE
    5120: ("b", 1, np.int8),

    # UNSIGNED_BYTE
    5121: ("B", 1, np.uint8),

    # SHORT
    5122: ("h", 2, np.int16),

    # UNSIGNED_SHORT
    5123: ("H", 2, np.uint16),

    # UNSIGNED_INT
    5125: ("I", 4, np.uint32),

    # FLOAT
    5126: ("f", 4, np.float32),
}


# ============================================
# Accessor Type Component Counts
# ============================================

_TYPE_COMPONENT_COUNT = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT4": 16,
}


# ============================================
# Main Reader
# ============================================

def read_accessor(
    json_data,
    bin_blob,
    accessor_index
):
    DEBUG_ACCESSORS = True
    accessor = json_data["accessors"][accessor_index]

    if "bufferView" not in accessor:
        raise VRM0AccessorError(
            "Sparse accessors unsupported"
        )

    buffer_view = json_data["bufferViews"][
        accessor["bufferView"]
    ]

    component_type = accessor["componentType"]
    accessor_type = accessor["type"]
    count = accessor["count"]

    if component_type not in _COMPONENT_TYPE_MAP:
        raise VRM0AccessorError(
            f"Unsupported component type: {component_type}"
        )

    if accessor_type not in _TYPE_COMPONENT_COUNT:
        raise VRM0AccessorError(
            f"Unsupported accessor type: {accessor_type}"
        )

    fmt_char, component_size, np_dtype = \
        _COMPONENT_TYPE_MAP[component_type]

    component_count = _TYPE_COMPONENT_COUNT[
        accessor_type
    ]

    # ============================================
    # OFFSETS
    # ============================================

    bv_offset = buffer_view.get(
        "byteOffset",
        0
    )

    accessor_offset = accessor.get(
        "byteOffset",
        0
    )

    absolute_offset = bv_offset + accessor_offset

    # ============================================
    # STRIDE
    # ============================================

    element_size = (
        component_size *
        component_count
    )

    stride = buffer_view.get(
        "byteStride",
        element_size
    )

    # ============================================
    # DEBUG
    # ============================================

    #print("\n[VRM0 ACCESSOR]")
    #print("Accessor:", accessor_index)
    #print("Type:", accessor_type)
    #print("ComponentType:", component_type)
    #print("Count:", count)
    #print("Stride:", stride)
    #print("Element Size:", element_size)

    # ============================================
    # READ
    # ============================================

    fmt = "<" + (fmt_char * component_count)

    results = []

    for i in range(count):

        start = absolute_offset + (i * stride)
        end = start + element_size

        if end > len(bin_blob):
            raise VRM0AccessorError(
                "Accessor exceeds BIN size"
            )

        values = struct.unpack_from(
            fmt,
            bin_blob,
            start
        )

        results.append(values)

    array = np.array(
        results,
        dtype=np_dtype
    )

    # ============================================
    # NORMALIZATION
    # ============================================

    normalized = accessor.get(
        "normalized",
        False
    )

    if normalized:

        print("[VRM0] Applying normalization")

        if component_type == 5121:
            # UNSIGNED_BYTE
            array = array.astype(np.float32) / 255.0

        elif component_type == 5123:
            # UNSIGNED_SHORT
            array = array.astype(np.float32) / 65535.0

        elif component_type == 5120:
            # BYTE
            array = np.maximum(
                array.astype(np.float32) / 127.0,
                -1.0
            )

        elif component_type == 5122:
            # SHORT
            array = np.maximum(
                array.astype(np.float32) / 32767.0,
                -1.0
            )

    # ============================================
    # CLEANUP
    # ============================================

    if accessor_type == "SCALAR":
        array = array.reshape(-1)

    # ============================================
    # DEBUG SAMPLES
    # ============================================

    #print("Sample values:")
    #print(array[:5])
#
    #print("Min:", array.min())
    #print("Max:", array.max())

    return array