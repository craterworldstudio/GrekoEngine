from datetime import time
import time as timen
import math
from core.behaviours_manager import BehaviorManager
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
    vrm_path = "assets/kisayov2.vrm"
    if not os.path.exists(vrm_path):
        print(f"❌ VRM not found: {vrm_path}")
        gn.terminate()
        return
    
    print(f"📂 Loading VRM: {vrm_path}")

    parsed_data = parse_glb(vrm_path)
    
    # FLAG: Render Parts List
    # We store each mesh piece separately instead of combining them.
    render_parts = []
    primitive_count = 0
    
    for mesh_idx, mesh in enumerate(parsed_data.json["meshes"]):
        mesh_name = mesh.get("name", f"Mesh_{mesh_idx}")
        
        for prim_idx, primitive in enumerate(mesh["primitives"]):
            packed = package_mesh(parsed_data.json, parsed_data.bin_blob, primitive)

            # FLAG: Check for transparency tags
            # We look at the mesh name or the material index to identify face parts
            is_transparent = False
            #texture_id = 0
            if "Face" in mesh_name or "Eye" in mesh_name or "Hair" in mesh_name:
                is_transparent = True

            tex_id = 0
            if packed.get('texture') is not None:
                tex_id = gn.upload_texture(bytes(packed['texture']), srgb=True)
                print(f"     ✅ Texture ID: {tex_id}")

            render_parts.append({
                "name": mesh_name,
                "vertices": packed['vertices'],
                "normals": packed['normals'],
                "uvs": packed['uvs'],
                "joints": packed['joints'],
                "weights": packed['weights'],
                "indices": packed['indices'],
                "morph_targets": packed['morph_targets'],
                "tex_id": tex_id,
                "transparent": is_transparent # Tag it for sorting
            })

            primitive_count += 1
            print(f"   ✅ Packed {mesh_name} - Primitive {prim_idx} (Vertices: {len(packed['vertices'])})") 
        


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
    MORPH_SLOTS = ["Fcl_EYE_Close", "Fcl_ALL_Surprised", "Fcl_MTH_E", "Fcl_MTH_I"]
    #face_mesh_index = -1
    face_mesh_indices = []
    face_morph_library = {} 
    

    for i, part in enumerate(sorted_parts):
        if "Face" in part["name"]:
            # Save every morph the VRM has into our library
            face_mesh_indices.append(i)
            face_morph_library = part["morph_targets"]
            print(f"🎯 Face detected at index {i}")
            

        #if "Fcl_MTH_A" in part["morph_targets"]:
        #    face_mesh_index = i
            


        all_morphs = part["morph_targets"]
        upload_list = []

        print(f"\n📦 Part: {part.get('name', 'Unknown')}")
        for i, slot_name in enumerate(MORPH_SLOTS):
            if slot_name in all_morphs:
                data = all_morphs[slot_name]
                # FLAG: Print the "Energy" of the morph
                print(f"  Slot {i} ({slot_name}): Size {len(data)}, Sum {np.sum(np.abs(data)):.2f}")
                upload_list.append(data)
            else:
                print(f"  Slot {i} ({slot_name}): EMPTY (Zeros)")
                upload_list.append(np.zeros_like(part["vertices"]))
        #blink_array = all_morphs.get("Fcl_EYE_Close", None)
        #if blink_array is None:
        #    blink_array = np.zeros_like(part["vertices"], dtype=np.float32)

        gn.upload_mesh(
            part["vertices"], 
            part["normals"], 
            part["uvs"],
            part["joints"], 
            part["weights"], 
            part["indices"],
            upload_list,
            part["tex_id"]
        )

    manager = BehaviorManager()
    manager.load_behaviors()

    # Pass THIS index to the manager/sequencer
    manager.face_mesh_indices = face_mesh_indices # Set it here
    manager.inject_morph_library(face_morph_library) 
    
    # Main Loop remains the same
    while not gn.should_close():
        gn.clear_screen()

        manager.update_all(gn)
    
        gn.draw_scene() 
        gn.swap_buffers()

    gn.terminate()

if __name__ == "__main__":
    run_engine()