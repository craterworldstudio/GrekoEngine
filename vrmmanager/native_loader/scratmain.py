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

from panda3d.core import LineSegs, NodePath, Point3

def draw_skeleton_debug(character_np, joint_map, parent_map):
    lines = LineSegs()
    lines.set_thickness(2.0)

    for joint_idx, joint in joint_map.items():
        parent_idx = parent_map.get(joint_idx)
        if parent_idx is None:
            continue

        parent_joint = joint_map[parent_idx]

        # Get joint transforms (joint-local → character space)
        joint_mat = joint.get_transform()
        parent_mat = parent_joint.get_transform()

        joint_pos = joint_mat.xform_point(Point3(0, 0, 0))
        parent_pos = parent_mat.xform_point(Point3(0, 0, 0))

        lines.move_to(parent_pos)
        lines.draw_to(joint_pos)

    return character_np.attach_new_node(lines.create())




import sys
from direct.showbase.ShowBase import ShowBase
from geometry_builder import build_panda_mesh
from direct.actor.Actor import Actor

from skin_builder import build_vrm_skeleton

class GrekoVisualTest(ShowBase):
    def __init__(self, parsed_glb):
        super().__init__()
        self.setFrameRateMeter(True)
        # We build the skeleton FIRST. It creates the 'Character' node.
        # Most VRMs have one 'skin', so we use index 0.
        print("[TEST] Reconstructing Joint Hierarchy...")
        # 1. Start Skeleton Build
        char_node, joints_map, parent_map = build_vrm_skeleton(
            parsed_glb.json, 
            parsed_glb.bin_blob, 
            0, 
            read_accessor
        )
        temp_np = NodePath(char_node)

        self.character_np = Actor(temp_np)
        #self.character_np = self.render.attach_new_node(char_node)
        self.character_np.reparent_to(self.render)

        
        self.character_np.set_p(90)

        # 2. START MESH LOGS (Phase 1.3 Content)
        print(f"[TEST] Loading and Binding Skinned Meshes...")
        total_prims = 0
        skin_joints_indices = parsed_glb.json["skins"][0]["joints"]
        ordered_joints = [joints_map[idx] for idx in skin_joints_indices]

        for m_idx, mesh_json in enumerate(parsed_glb.json.get("meshes", [])):
            mesh_name = mesh_json.get("name", f"Mesh_{m_idx}")
            for p_idx, primitive in enumerate(mesh_json["primitives"]):
                # This provides the "-> Building {mesh}" feedback you wanted
                print(f"  -> Building: {mesh_name} (Primitive {p_idx})")
                
                
                geom_node = build_panda_mesh(
                    parsed_glb.json, 
                    parsed_glb.bin_blob, 
                    primitive, 
                    read_accessor,
                    joints_list=ordered_joints,
                    name=f"{mesh_name}_{p_idx}"
                )
                
                
                self.character_np.attach_new_node(geom_node)
                #char_node.addGeom(geom_node)
                total_prims += 1

        print("[TEST] Forcing Bundle Bind...")
        
        bundle = char_node.get_bundle(0)
        char_node.force_update()
        #self.character_np.postFlatten()

        self.character_np.node().set_final(True)
        
        # 3. PHASE 1.3 LOG (The "Assembled" milestone)
        print(f"✅ Total Primitives Bound: {total_prims}")
        print("🚀 Phase 1.3: All meshes assembled and visible!")

        # 4. BONE INSPECTION (The "Bones after 1.3" requirement)
        #print("\n--- [INTERNAL SKELETON HIERARCHY] ---")
        # .write() forces Panda3D to print the actual joint tree inside the bundle
        #from panda3d.core import Notify
        #bundle = char_node.get_bundle(0).write(Notify.out(), 0)
        #bundle.display()

        print("\n--- [SCENE GRAPH HIERARCHY] ---")
        self.character_np.ls() 
        
        # 5. FINAL MILESTONE
        print("\n🚀 Phase 1.,5,6: Skeleton bound and hierarchy validated!")

        # Camera Setup
        self.cam.set_pos(0, -4, 1.0)
        self.cam.look_at(0, 0, 1.0)
        self.render.set_two_sided(True)

        head_joint = None
        for joint in joints_map.values():
            if "Head" in joint.get_name():
                head_joint = joint
                            

        if head_joint:
            head_bone_name = head_joint.get_name()

            # 1. The Actor Handshake
            # This creates a NodePath that 'lives' at the joint's location
            self.head_control = self.character_np.controlJoint(None, "modelRoot", head_bone_name)

            if self.head_control:
                print(f"Pre-Tilt Joint Transform:\n{head_joint.get_transform()}")
                bundle = char_node.get_bundle(0)
                bundle.control_joint(head_bone_name, self.head_control.node())

                def tilt_head_task(task):
                    if task.time < 2.0:
                        return task.cont  # Wait for 2 seconds
                    
                    if task.time < 3.0:
                        # Smoothly interpolate from 0 to 45 degrees over 1 second
                        # (task.time - 2.0) gives us a 0.0 to 1.0 range
                        current_tilt = (task.time - 2.0) * 45
                        self.head_control.set_p(current_tilt)
                        return task.cont
                    
                    # Final position lock
                    self.head_control.set_p(45)

                    bundle.force_update()
                    char_node.update()

                    print("✅ Delayed Tilt Complete!")
                    print(f"Post-Tilt Joint Transform:\n{head_joint.get_transform()}")
                    return task.done

                # 3. Add the task to the manager
                self.taskMgr.add(tilt_head_task, "TiltHeadTask")

                # 2. Apply movement to the NodePath
                #print("Tilting head 45 degrees forward...")
                #self.head_control.set_p(45) # Use P for forward/back tilt in Panda's Z-up

                # 3. THE MISSING FLAG: Force the Bundle to sync
                # This pushes the NodePath's transform into the actual bone math
                bundle = char_node.get_bundle(0)
                bundle.force_update()

                # 4. Final calculation of the hierarchy
                char_node.update()
        
        
        
        #print("🚀 Phase 1.3: All meshes assembled and visible!")
        #print("🚀 Phase 1.4: Skeleton bound and hierarchy validated!")

app = GrekoVisualTest(parsed)
app.run()