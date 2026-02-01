# face_loader.py
# Loads face mesh + morph targets from a GLB and maps them to exported JSON names
import struct
import json
from panda3d.core import GeomNode, Vec3, GeomVertexData, GeomVertexWriter

class MorphTarget:
    def __init__(self, name, deltas):
        self.name = name
        self.deltas = deltas  # list of Vec3
        self.weight = 0.0

class FaceMesh:
    def __init__(self, geom_node: GeomNode, base_positions):
        self.geom_node = geom_node
        self.base_positions = base_positions  # list of Vec3
        self.morphs = {}  # name -> MorphTarget
        
# ---- GLB Parsing Utilities ----
def load_glb_json(glb_path):
    """Extract JSON chunk from a GLB file"""
    with open(glb_path, "rb") as f:
        data = f.read()

    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b'glTF':
        raise ValueError("Not a valid GLB file")

    offset = 12
    json_chunk = None

    while offset < len(data):
        chunk_len, chunk_type = struct.unpack_from("<I4s", data, offset)
        offset += 8
        chunk_data = data[offset:offset + chunk_len]
        offset += chunk_len

        if chunk_type == b'JSON':
            json_chunk = chunk_data
            break

    if json_chunk is None:
        raise ValueError("No JSON chunk found in GLB")

    return json.loads(json_chunk.decode("utf-8"))

def load_buffer(glb_path):
    """Return the binary buffer of the GLB (first BIN chunk)"""
    with open(glb_path, "rb") as f:
        data = f.read()

    offset = 12
    while offset < len(data):
        chunk_len, chunk_type = struct.unpack_from("<I4s", data, offset)
        offset += 8
        chunk_data = data[offset:offset + chunk_len]
        offset += chunk_len

        if chunk_type == b'BIN\x00':
            return chunk_data

    raise ValueError("No BIN chunk found in GLB")

def read_accessor_data(gltf_json, buffer_bytes, accessor_index):
    accessor = gltf_json["accessors"][accessor_index]
    bufferView = gltf_json["bufferViews"][accessor["bufferView"]]
    start = bufferView.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    length = accessor["count"]
    componentType = accessor["componentType"]
    type_str = accessor["type"]

    if componentType != 5126 or type_str != "VEC3":
        raise ValueError(f"Unsupported accessor type: {componentType} {type_str}")

    vertex_data = []
    for i in range(length):
        offset = start + i * 12
        x, y, z = struct.unpack_from("<fff", buffer_bytes, offset)
        vertex_data.append(Vec3(x, y, z))
    return vertex_data

# ---- Face Loader ----
def load_face_mesh(glb_path, face_mesh_name=None):
    gltf = load_glb_json(glb_path)
    buffer_bytes = load_buffer(glb_path)

    # Find the face mesh with morph targets
    target_mesh = None
    target_prim = None
    for mesh in gltf.get("meshes", []):
        if face_mesh_name is None or mesh.get("name") == face_mesh_name:
            for prim in mesh.get("primitives", []):
                if "targets" in prim:
                    target_mesh = mesh
                    target_prim = prim
                    break
        if target_mesh:
            break

    if not target_mesh or not target_prim:
        raise ValueError("No face mesh with morph targets found")

    # Base positions
    base_accessor_index = target_prim["attributes"]["POSITION"]
    base_positions = read_accessor_data(gltf, buffer_bytes, base_accessor_index)

    geom_node = GeomNode(target_mesh.get("name", "FaceMesh"))
    face_mesh = FaceMesh(geom_node, base_positions)

    # Get names from 'targetNames' if available
    target_names = target_prim.get("targetNames", [])

    # Read morph targets
    for i, target in enumerate(target_prim["targets"]):
        # Use targetNames[i] if present, fallback to morph_i
        name = target_names[i] if i < len(target_names) else f"morph_{i}"
        pos_accessor_index = target.get("POSITION")
        if pos_accessor_index is not None:
            deltas = read_accessor_data(gltf, buffer_bytes, pos_accessor_index)
            face_mesh.morphs[name] = MorphTarget(name, deltas)

    print(f"✅ Loaded FaceMesh '{face_mesh.geom_node.get_name()}' with {len(face_mesh.morphs)} morphs")
    return face_mesh

