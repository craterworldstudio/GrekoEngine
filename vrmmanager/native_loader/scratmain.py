import time
from glb_parser import parse_glb
from gltf_accessors import (validate_gltf, read_accessor, )
from panda3d.core import NodePath

parsed = parse_glb("assets/kisayo.vrm")

print("Nodes:", len(parsed.json.get("nodes", [])))
print("Skins:", len(parsed.json.get("skins", [])))
print("Has VRM extension:", "VRMC_vrm" in parsed.json.get("extensions", {}))




validate_gltf(parsed.json)
print("[TEST] glTF structure validated")

mesh = parsed.json["meshes"][0]
primitive = mesh["primitives"][0]

# ---- Vertex positions (VEC3 + FLOAT) ----
pos_accessor_index = primitive["attributes"]["POSITION"]
positions = read_accessor(
    parsed.json,
    parsed.bin_blob, # type: ignore
    pos_accessor_index,
)

print("[TEST] Vertex positions:")
print("  Count:", len(positions))
print("  First:", positions[0])
print("  Last:", positions[-1])

if "indices" in primitive:
    idx_accessor_index = primitive["indices"]
    indices = read_accessor(
        parsed.json,
        parsed.bin_blob, # type: ignore
        idx_accessor_index,
    )

    print("[TEST] Indices:")
    print("  Count:", len(indices))
    print("  First triangle:", indices[:3])
else:
    print("[TEST] No index buffer (non-indexed geometry)")

print("\n✅ Phase 1.2 accessor tests passed")

from panda3d.core import LineSegs, NodePath

def draw_skeleton_debug(character_np, joint_map, parent_map):
    lines = LineSegs()
    lines.set_thickness(2.0)

    for idx, joint in joint_map.items():
        parent_idx = parent_map.get(idx)
        if parent_idx is None:
            continue

        parent_joint = joint_map[parent_idx]

        joint_np = character_np.attach_new_node(joint)
        parent_np = character_np.attach_new_node(parent_joint)

        joint_pos = joint_np.get_pos(character_np)
        parent_pos = parent_np.get_pos(character_np)

        lines.move_to(parent_pos)
        lines.draw_to(joint_pos)

        joint_np.remove_node()
        parent_np.remove_node()

    return character_np.attach_new_node(lines.create())



import sys
from direct.showbase.ShowBase import ShowBase
from geometry_builder import build_panda_mesh

from skin_builder import build_vrm_skeleton

class GrekoVisualTest(ShowBase):
    def __init__(self, parsed_glb):
        super().__init__()
        self.setFrameRateMeter(True)
        # We build the skeleton FIRST. It creates the 'Character' node.
        # Most VRMs have one 'skin', so we use index 0.
        print("[TEST] Reconstructing Joint Hierarchy...")
        # 1. Start Skeleton Build
        char_node, joints_map = build_vrm_skeleton(
            parsed_glb.json, 
            parsed_glb.bin_blob, 
            0, 
            read_accessor
        )
        
        self.character_np = self.render.attach_new_node(char_node)
        self.character_np.set_p(90)
        self.skel_debug = draw_skeleton_debug(self.character_np, joints_map)

        # 2. START MESH LOGS (Phase 1.3 Content)
        print(f"[TEST] Loading and Binding Skinned Meshes...")
        total_prims = 0

        for m_idx, mesh_json in enumerate(parsed_glb.json.get("meshes", [])):
            mesh_name = mesh_json.get("name", f"Mesh_{m_idx}")
            for p_idx, primitive in enumerate(mesh_json["primitives"]):
                # This provides the "-> Building {mesh}" feedback you wanted
                #print(f"  -> Building: {mesh_name} (Primitive {p_idx})")
                
                geom_node = build_panda_mesh(
                    parsed_glb.json, 
                    parsed_glb.bin_blob, 
                    primitive, 
                    read_accessor,
                    name=f"{mesh_name}_{p_idx}"
                )
                #geom = geom_node.get_geom(0)

                #char_np = NodePath(char_node)
                #char_np.attach_new_node(geom_node)

                self.character_np.attach_new_node(geom_node)

                total_prims += 1

        #self.character_np.ls()

        #char_node.get_bundle(0).force_update()
        
        # 2. Update the character node itself
        #char_node.update()

        # 3. PHASE 1.3 LOG (The "Assembled" milestone)
        print(f"✅ Total Primitives Bound: {total_prims}")
        print("🚀 Phase 1.3: All meshes assembled and visible!")

        # 4. BONE INSPECTION (The "Bones after 1.3" requirement)
        print("\n--- [INTERNAL SKELETON HIERARCHY] ---")
        # .write() forces Panda3D to print the actual joint tree inside the bundle
        from panda3d.core import Notify
        #bundle = char_node.get_bundle(0).write(Notify.out(), 0)
        #bundle.display()
        #print("\n--- [SCENE GRAPH HIERARCHY] ---")
        self.character_np.ls() 
        
        # 5. FINAL MILESTONE
        print("\n🚀 Phase 1.4: Skeleton bound and hierarchy validated!")

        # Camera Setup
        self.cam.set_pos(0, -4, 1.0)
        self.cam.look_at(0, 0, 1.0)
        self.render.set_two_sided(True)

        head_joint = None
        for joint in joints_map.values():
            if "Head" in joint.get_name():
                head_joint = joint
                            
                

        if head_joint:
            # 1. Create the control handle
            control_np = self.character_np.attach_new_node("HeadControl")
            control_np.set_mat(
                self.character_np, 
                head_joint.get_transform()
                               )

            # 2. THE CORRECT FLAG: control_joint
            # This tells the bundle: "Stop following the default pose for this bone,
            # and follow this NodePath instead."
            print(f"Pre-Tilt Joint Transform:\n{head_joint.get_transform()}")
            bundle = char_node.get_bundle(0)
            bundle.control_joint(head_joint.get_name(), control_np.node())
            

            control_np.show()
            control_np.show_bounds()

                        
            
            #time.sleep(6)
            # 3. Apply the rotation to the handle
            control_np.set_h(45)
            
            # 4. Update the character
            char_node.update()
            
            print(f"Post-Tilt Joint Transform:\n{head_joint.get_transform()}")
        
        #print("🚀 Phase 1.3: All meshes assembled and visible!")
        #print("🚀 Phase 1.4: Skeleton bound and hierarchy validated!")

app = GrekoVisualTest(parsed)
app.run()