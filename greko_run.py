import core.greko_native as gn # type: ignore
import time
import sys
import os

# FLAG: The New Connections
from core.glb_parser import parse_glb
from core.mesh_data import package_mesh

def run_engine():
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
    mesh_info = parsed_data.json["meshes"][0]["primitives"][0]
    packed = package_mesh(parsed_data.json, parsed_data.bin_blob, mesh_info)

    # 4. FLAG: The Big Upload
    # This sends the data through bridge.cpp to the GPU
    gn.upload_mesh(
        packed["vertices"],
        packed["uvs"],
        packed["joints"],
        packed["weights"],
        packed["indices"]
    )

    print(f"🚀 Kisayo Uploaded! Index Count: {len(packed['indices'])}")

    last_time = time.time()
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