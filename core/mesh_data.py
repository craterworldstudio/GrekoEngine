import numpy as np
from core.gltf_accessors import read_accessor

def package_mesh(gltf_json, bin_blob, primitive_data):
    """
    Combines Geometry and Skinning into a single data package.
    NO PANDA3D ALLOWED HERE.
    """
    attrs = primitive_data["attributes"]
    
    # 1. Get Geometry (from old geometry_builder logic)
    pos = np.array(read_accessor(gltf_json, bin_blob, attrs["POSITION"]), dtype=np.float32)
    if "NORMAL" in attrs:
        normals = np.array(read_accessor(gltf_json, bin_blob, attrs["NORMAL"]), dtype=np.float32)
    else:
        # Generate flat normals if missing (shouldn't happen with VRM)
        normals = np.zeros_like(pos)
        normals[:, 1] = 1.0  # Point up as default

    uv = np.array(read_accessor(gltf_json, bin_blob, attrs["TEXCOORD_0"]), dtype=np.float32)
    
    # 2. Get Skinning (from old skin_builder logic)
    # FLAG: We ensure these are 4-component vectors for the shader
    joints = np.array(read_accessor(gltf_json, bin_blob, attrs["JOINTS_0"]), dtype=np.uint32)
    weights = np.array(read_accessor(gltf_json, bin_blob, attrs["WEIGHTS_0"]), dtype=np.float32)
    
    # 3. Get Indices
    indices = np.array(read_accessor(gltf_json, bin_blob, primitive_data["indices"]), dtype=np.uint32)

    texture_bytes = extract_base_color_texture_bytes( gltf_json, bin_blob, primitive_data)
    
    return {
        "vertices": pos,
        "normals": normals,
        "uvs": uv,
        "joints": joints,
        "weights": weights,
        "indices": indices,
        "index_count": len(indices),
        "texture": texture_bytes
    }

def extract_base_color_texture_bytes(gltf_json, bin_blob, primitive):
    mat_idx = primitive.get("material")
    if mat_idx is None:
        return None

    material = gltf_json["materials"][mat_idx]
    pbr = material.get("pbrMetallicRoughness")
    if not pbr:
        return None

    tex_info = pbr.get("baseColorTexture")
    if not tex_info:
        return None

    tex_idx = tex_info["index"]
    image_idx = gltf_json["textures"][tex_idx]["source"]
    image = gltf_json["images"][image_idx]

    # Case 1: embedded image (VRM does this)
    if "bufferView" in image:
        bv = gltf_json["bufferViews"][image["bufferView"]]
        start = bv["byteOffset"]
        end = start + bv["byteLength"]
        return bin_blob[start:end]

    # Case 2: external file (rare for VRM)
    if "uri" in image:
        with open(image["uri"], "rb") as f:
            return f.read()

    return None
    
