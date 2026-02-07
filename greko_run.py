import core.greko_native as gn
import sys
import os
import numpy as np

from core.glb_parser import parse_glb
from core.mesh_data import package_mesh

def run_engine():
    # Initialize renderer
    if gn.init_renderer(1280, 720) != 0:
        print("❌ Renderer init failed")
        sys.exit(1)

    # Load VRM
    vrm_path = "assets/kisayo.vrm"
    if not os.path.exists(vrm_path):
        print(f"❌ VRM not found: {vrm_path}")
        gn.terminate()
        return

    parsed_data = parse_glb(vrm_path)
    
    # FLAG: Render Parts List
    # We store each mesh piece separately instead of combining them.
    render_parts = []
    
    for mesh_idx, mesh in enumerate(parsed_data.json["meshes"]):
        mesh_name = mesh.get("name", f"Mesh_{mesh_idx}")
        
        for prim_idx, primitive in enumerate(mesh["primitives"]):
            packed = package_mesh(parsed_data.json, parsed_data.bin_blob, primitive)
            
            # FLAG: Check for transparency tags
            # We look at the mesh name or the material index to identify face parts
            is_transparent = False
            if "Face" in mesh_name or "Eye" in mesh_name or "Hair" in mesh_name:
                is_transparent = True

            tex_id = 0
            if packed.get('texture') is not None:
                tex_id = gn.upload_texture(bytes(packed['texture']), True)

            render_parts.append({
                "name": mesh_name,
                "vertices": packed['vertices'],
                "normals": packed['normals'],
                "uvs": packed['uvs'],
                "joints": packed['joints'],
                "weights": packed['weights'],
                "indices": packed['indices'],
                "tex_id": tex_id,
                "transparent": is_transparent # Tag it for sorting
            })

    # FLAG: The Sorting Logic
    # We create two groups so Opaque draws first and Transparent draws last.
    opaque_parts = [p for p in render_parts if not p["transparent"]]
    transparent_parts = [p for p in render_parts if p["transparent"]]
    
    # Combine them: Opaque first, then Transparent
    sorted_parts = opaque_parts + transparent_parts

    print(f"📦 Sorting Complete: {len(opaque_parts)} opaque, {len(transparent_parts)} transparent.")

    # Position camera to view Kisayo
    gn.set_camera_position(0.0, 1.5, 3.0)
    gn.set_camera_target(0.0, 1.0, 0.0)
    
    print("\n🚀 Multi-Draw Engine Ready!")
    print("🎮 Use WASD + mouse to navigate. ESC to toggle mouse.")
    
   # 1. During Setup (ONLY ONCE)
    for part in sorted_parts:
        gn.upload_mesh(
            part["vertices"], part["normals"], part["uvs"],
            part["joints"], part["weights"], part["indices"],
            part["tex_id"]
        )
    
    # Main Loop remains the same
    while not gn.should_close():
        gn.clear_screen()
        gn.draw_scene() 
        gn.swap_buffers()

    gn.terminate()

if __name__ == "__main__":
    run_engine()