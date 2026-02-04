import core.greko_native as gn # type: ignore
import numpy as np
import time
import sys
import os
#global index_offset

# FLAG: The New Connections
from core.glb_parser import parse_glb
from core.mesh_data import package_mesh

def run_engine():

    all_vertices = []
    all_normals  = []
    all_uvs      = []
    all_joints   = []
    all_weights  = []
    all_indices  = []

    index_offset = 0
    
    # 1. Initialize Window
    if gn.init_renderer(1280, 720) != 0:
        print("❌ Critical Error: Could not initialize native renderer.")
        sys.exit(1)

    # 2. FLAG: Load VRM (GLB) Data
    vrm_path = "assets/kisayo.vrm"
    if not os.path.exists(vrm_path):
        print(f"❌ VRM File not found at: {vrm_path}")
        gn.terminate()
        return

    # Use your parser to get the JSON and BIN chunks
    parsed_data = parse_glb(vrm_path)
    
    # 3. FLAG: Package first mesh primitive
    # Most VRMs have the main body as the first mesh
    print(f"📦 Loading {len(parsed_data.json['meshes'])} meshes...")
    
    all_meshes = []
    total_indices = 0
    
    for mesh_idx, mesh in enumerate(parsed_data.json["meshes"]):
        mesh_name = mesh.get("name", f"Mesh_{mesh_idx}")
        
        for prim_idx, primitive in enumerate(mesh["primitives"]):
            packed = package_mesh(parsed_data.json, parsed_data.bin_blob, primitive)
            all_meshes.append(packed)
            total_indices += len(packed['indices'])
            
            print(f"  ✓ {mesh_name} (Primitive {prim_idx}): {len(packed['indices'])} indices")
    
    print(f"🚀 Total meshes: {len(all_meshes)}, Total indices: {total_indices}")
    

    # 4. FLAG: The Big Upload
    # This sends the data through bridge.cpp to the GPU
    for mesh in all_meshes:
        v = mesh["vertices"]
        n = mesh["normals"]
        uv = mesh["uvs"]
        j = mesh["joints"]
        w = mesh["weights"]
        idx = mesh["indices"]
    
        all_vertices.append(v)
        all_normals.append(n)
        all_uvs.append(uv)
        all_joints.append(j)
        all_weights.append(w)
    
        all_indices.append(idx + index_offset)
        index_offset += v.shape[0]

    vertices = np.vstack(all_vertices)
    normals  = np.vstack(all_normals)
    uvs      = np.vstack(all_uvs)
    joints   = np.vstack(all_joints)
    weights  = np.vstack(all_weights)
    indices  = np.hstack(all_indices)

 
    gn.upload_mesh(
        vertices,
        normals,
        uvs,
        joints,
        weights,
        indices
    )
    print(f"🎨 Uploaded mesh with {len(indices)} indices")

    # 4.5 FLAG: Upload texture (single-texture pipeline for now)
    for mesh in all_meshes:
        tex = mesh.get("texture")
        if tex is not None:
            gn.upload_texture(tex.tobytes())
            print("🎨 Texture uploaded")
            break
        


    print(f"🚀 Kisayo Uploaded! Index Count: {len(indices)}") # type: ignore        
    #last_time = time.time()
    running = True
    while running:
        if gn.should_close():
            running = False

        gn.clear_screen()
        
        # 5. FLAG: Draw the Model
        # We pass the index count because your current renderer.cpp 
        # doesn't use the global current_index_count yet.
        gn.draw_mesh()
        
        gn.swap_buffers()

    gn.terminate()

if __name__ == "__main__":
    run_engine()