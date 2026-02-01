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
    uv = np.array(read_accessor(gltf_json, bin_blob, attrs["TEXCOORD_0"]), dtype=np.float32)
    
    # 2. Get Skinning (from old skin_builder logic)
    # FLAG: We ensure these are 4-component vectors for the shader
    joints = np.array(read_accessor(gltf_json, bin_blob, attrs["JOINTS_0"]), dtype=np.uint32)
    weights = np.array(read_accessor(gltf_json, bin_blob, attrs["WEIGHTS_0"]), dtype=np.float32)
    
    # 3. Get Indices
    indices = np.array(read_accessor(gltf_json, bin_blob, primitive_data["indices"]), dtype=np.uint32)
    
    return {
        "vertices": pos,
        "uvs": uv,
        "joints": joints,
        "weights": weights,
        "indices": indices,
        "index_count": len(indices)
    }