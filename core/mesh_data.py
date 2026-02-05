import numpy as np
from core.gltf_accessors import read_accessor

def package_mesh(gltf_json, bin_blob, primitive_data):
    attrs = primitive_data["attributes"]

    # === Geometry ===
    pos = np.array(
        read_accessor(gltf_json, bin_blob, attrs["POSITION"]),
        dtype=np.float32
    )

    if "NORMAL" in attrs:
        normals = np.array(
            read_accessor(gltf_json, bin_blob, attrs["NORMAL"]),
            dtype=np.float32
        )
    else:
        normals = np.zeros_like(pos, dtype=np.float32)
        normals[:, 1] = 1.0

    uv = np.array(
        read_accessor(gltf_json, bin_blob, attrs["TEXCOORD_0"]),
        dtype=np.float32
    )

    # === Skinning ===
    joints = np.array(
        read_accessor(gltf_json, bin_blob, attrs["JOINTS_0"]),
        dtype=np.uint32
    )
    weights = np.array(
        read_accessor(gltf_json, bin_blob, attrs["WEIGHTS_0"]),
        dtype=np.float32
    )

    # === Indices ===
    indices = np.array(
        read_accessor(gltf_json, bin_blob, primitive_data["indices"]),
        dtype=np.uint32
    )

    # === Material ===
    texture_bytes, base_color_factor = extract_base_color_texture(
        gltf_json, bin_blob, primitive_data
    )

    return {
        "vertices": pos,
        "normals": normals,
        "uvs": uv,
        "joints": joints,
        "weights": weights,
        "indices": indices,
        "index_count": len(indices),

        # MATERIAL
        "texture": texture_bytes,
        "base_color_factor": base_color_factor,
    }


def extract_base_color_texture(gltf_json, bin_blob, primitive):
    mat_idx = primitive.get("material")
    if mat_idx is None:
        return None, [1.0, 1.0, 1.0, 1.0]

    material = gltf_json["materials"][mat_idx]
    pbr = material.get("pbrMetallicRoughness", {})

    base_color_factor = pbr.get("baseColorFactor", [1.0, 1.0, 1.0, 1.0])

    tex_info = pbr.get("baseColorTexture")
    if not tex_info:
        return None, base_color_factor

    tex_idx = tex_info["index"]
    image_idx = gltf_json["textures"][tex_idx]["source"]
    image = gltf_json["images"][image_idx]

    # Embedded image (VRM standard)
    if "bufferView" in image:
        bv = gltf_json["bufferViews"][image["bufferView"]]
        start = bv.get("byteOffset", 0)
        end = start + bv["byteLength"]
        return bin_blob[start:end], base_color_factor

    # External image (rare)
    if "uri" in image:
        with open(image["uri"], "rb") as f:
            return f.read(), base_color_factor

    return None, base_color_factor
