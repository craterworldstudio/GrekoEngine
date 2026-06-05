#greko_run.py
#from datetime import time
import time as timen
import math
import tempfile
import sys
import os, shutil, importlib, sysconfig, json
import numpy as np

#from core import skeleton
import importlib.util
import sys

from core import skeleton
from core.utils.vrmdata import export_vrm_debug

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)

def load_native(path):

    # 🔥 CRITICAL: Use MEIPASS if available
    if hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
        print("!")
    else:
        base_dir = os.path.abspath(".")

    #target_dir = os.path.join(base_dir, "core")
    ext = sysconfig.get_config_var('EXT_SUFFIX')
    target_dir = os.path.join(tempfile.gettempdir(), "greko_runtime")
    os.makedirs(target_dir, exist_ok=True)

    # FORCE correct module name
    target_path = os.path.join(target_dir, "greko_native"+ext)

    shutil.copy2(path, target_path)

    if target_dir not in sys.path:
        sys.path.insert(0, target_dir)

    imp = "greko_native"
    for imp in ['core.greko_native', 'greko_native']:
        if imp in sys.modules:
            return sys.modules[imp]

    importlib.invalidate_caches()

    return importlib.import_module(imp)

def choose_vrm(folder):
    vrms = [f for f in os.listdir(folder) if f.endswith(".vrm")]
    
    print("\nAvailable VRMs:")
    for i, v in enumerate(vrms):
        print(f"[{i}] {v}")
    
    idx = int(input("Select VRM: "))
    return os.path.join(folder, vrms[idx])

#import core.greko_native as gn
#gn = load_native("")

from core.glb_parser import parse_glb
from core.vrm0_loader import load_vrm0
from core.vrm_adapter import adapt_vrm
from core.skeleton import Skeleton
from core.vrm0_skeleton import VRM0Skeleton
from core.behaviours_manager import MorphBehaviorManager, SkeletonBehaviorManager
from core.mesh_data import package_mesh
from core.vrm0_mesh import package_vrm0_mesh
from core.animator import Animator

from core.scene import Scene, UpdateContext
from core.entity import Entity
from core.components.transform import Transform
from core.components.camera import CameraComponent
from core.components.mesh import MeshComponent

class Engine:
    def __init__(self, gn, assets_path):
        self.gn = gn
        self.assets_path = assets_path
        self.eye_constraints = {
            "inner_yaw": 8.0,
            "outer_yaw": 6.0,
            "up_pitch": 4.0,
            "down_pitch": 3.0
        }

    def setup_load(self): 
        vrm_path = self.assets_path #"assets/kiyo.vrm"
        
        if not os.path.exists(vrm_path):
            print(f"❌ VRM not found: {vrm_path}")
            self.gn.terminate()
            return

        print(f"📂 Loading VRM: {vrm_path}")

        self.gn.set_eye_constraints(
            self.eye_constraints["inner_yaw"],
            self.eye_constraints["outer_yaw"],
            self.eye_constraints["up_pitch"],
            self.eye_constraints["down_pitch"]
        )

        self.parsed_data = parse_glb(vrm_path)
        #self.vrm_data = adapt_vrm(self.parsed_data)
        #print(self.parsed_data)
        from core.utils.vrmdata import export_vrm_debug

        if self.parsed_data.vrm_version == 0:
            #export_vrm_debug(self.parsed_data)
            print("⚠️ Detected VRM0 format. Applying VRM0-specific processing...")
            
            self.parsed_data = load_vrm0(vrm_path)

            #print("\n===== VRM0 DEBUG =====")
#
            #print("Meshes:", len(self.parsed_data.json.get("meshes", [])))
            #print("Nodes:", len(self.parsed_data.json.get("nodes", [])))
            #print("Skins:", len(self.parsed_data.json.get("skins", [])))

            skin0 = self.parsed_data.json["skins"][0]
            skin1 = self.parsed_data.json["skins"][1]

            #print("Skin joints:", len(skin0["joints"]))
            #print("First 20 skin 0 joints:", skin0["joints"][:20])
            #print("Skin 1 joints:", len(skin1["joints"]))
            #print("First 20 skin 1 joints:", skin1["joints"][:20])

            

            # TEST FIRST MESH
            mesh = self.parsed_data.json["meshes"][0]
            primitive = mesh["primitives"][0]

            attrs = primitive["attributes"]

            from core.vrm0_accessor import read_accessor

            joints = read_accessor(
                self.parsed_data.json,
                self.parsed_data.bin_blob,
                attrs["JOINTS_0"]
            )

            joints = np.array(joints)

            #unique = np.unique(joints)
#
            #print("UNIQUE JOINT COUNT:", len(unique))
            #print("FIRST 50 UNIQUE:", unique[:50])
#
            #print("======================\n")

            print("🦴 Building Skeleton...")

            
            self.skeleton = VRM0Skeleton(
                self.gn,
                self.parsed_data.json,
                self.parsed_data.bin_blob
            )

            counts = np.bincount(joints.flatten())

            used = np.where(counts > 0)[0]

            #print("Highest 50 GPU joints used:")
            #print(used[-50:])
            

        else:
            print("⚠️ Detected VRM1 format. Applying VRM1-specific processing...")
            print("🦴 Building Skeleton...")    
            self.skeleton = Skeleton(self.gn, self.parsed_data.json, self.parsed_data.bin_blob)
            #print("Joint names:", self.skeleton.joint_names[:5])
            #print("Joint count:", len(self.skeleton.joint_nodes))

        self.gn.set_joint_names(self.skeleton.joint_names)
        self.gn.set_joint_count(len(self.skeleton.joint_nodes))

        
        self.animator = Animator(self.gn, self.skeleton)
        self.Mmanager = MorphBehaviorManager(self.skeleton, self.gn, self.parsed_data.vrm_version)
        self.Smanager = SkeletonBehaviorManager(self.skeleton)
        

        # FLAG: Render Parts List
        # We store each mesh piece separately instead of combining them.
        render_parts = []
        primitive_count = 0

        mesh_to_skin = {}

        for node_idx, node in enumerate(self.parsed_data.json["nodes"]):
            if "mesh" in node:
                #print( "NODE", node_idx, "MESH", node.get("mesh"), "SKIN", node.get("skin"))
                pass
            if "mesh" in node and "skin" in node:
            
                mesh_index = node["mesh"]
                skin_index = node["skin"]

                mesh_to_skin[mesh_index] = skin_index

                #print(    f"[VRM0] Mesh {mesh_index} uses Skin {skin_index}")

        for mesh_idx, mesh in enumerate(self.parsed_data.json["meshes"]):
            mesh_name = mesh.get("name", f"Mesh_{mesh_idx}")

            for prim_idx, primitive in enumerate(mesh["primitives"]):
                if self.parsed_data.vrm_version == 0:

                    skin_index = mesh_to_skin.get(mesh_idx, 0)
                    if skin_index == 2:
                        continue
                    
                    packed = package_vrm0_mesh(
                        self.parsed_data.json,
                        self.parsed_data.bin_blob,
                        primitive,
                        mesh,
                        self.skeleton,
                        skin_index
                    )

                    

                else:
                    packed = package_mesh(
                        self.parsed_data.json,
                        self.parsed_data.bin_blob,
                        primitive,
                        mesh
                    )

                # FLAG: Check for transparency tags
                # We look at the mesh name or the material index to identify face parts
                is_transparent = any(x in mesh_name for x in ["Face", "Eye", "Hair"])

                tex_id = 0
                if packed.get('texture') is not None:
                    tex_id = self.gn.upload_texture(bytes(packed['texture']), srgb=True)
                    #print(f"     ✅ Texture ID: {tex_id}")

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
                    "transparent": is_transparent, # Tag it for sorting
                    "vertex_count": int(packed["vertices"].shape[0])
                })

                primitive_count += 1
                #print(f"   ✅ Packed {mesh_name} - Primitive {prim_idx} (Vertices: {len(packed['vertices'])})") 



        # FLAG: The Sorting Logic
        # We create two groups so Opaque draws first and Transparent draws last.
        opaque_parts = [p for p in render_parts if not p["transparent"]]
        transparent_parts = [p for p in render_parts if p["transparent"]]

        # Combine them: Opaque first, then Transparent
        sorted_parts = opaque_parts + transparent_parts

        print(f"📦 Sorting Complete: {len(opaque_parts)} opaque, {len(transparent_parts)} transparent.")

        # =========================================================================
        # 🔗 VRM 0.0 STARTUP BLENDSHAPE BINDING
        # =========================================================================
        if self.parsed_data.vrm_version == 0:
            vrm_ext = self.parsed_data.json.get("extensions", {})
            if "VRM" in vrm_ext:
                print("📦 [Loader] Compiling VRM0 Compound Expression Groups to C++ VBO Slots...")
                vrm0_groups = vrm_ext.get("VRM", {}).get("blendShapeMaster", {}).get("blendShapeGroups", [])

                # Target pipeline destination slots
                slot_mapping = {
                    "blink": 0, # Slot 0 -> Blinker
                    "fun":   1  # Slot 1 -> Breather
                }

                from core.vrm0_accessor import read_accessor

                for group in vrm0_groups:
                    preset_name = group.get("presetName", "").lower()
                    if preset_name in slot_mapping:
                        slot_idx = slot_mapping[preset_name]
                        binds = group.get("binds", [])
                        if not binds:
                            continue
                        
                        # Track if we have initialized our target math space
                        accumulated_deltas = None
                        target_mesh_idx = None

                        print(f"🧬 Compiling Compound Preset '{preset_name}' into C++ Slot {slot_idx}...")

                        for bind in binds:
                            mesh_idx = int(bind.get("mesh", 1))
                            morph_target_idx = int(bind.get("index", 0))

                            # Scale factor (glTF weights use a 0-100 range scale value)
                            bind_weight = float(bind.get("weight", 100.0)) / 100.0

                            target_mesh_idx = mesh_idx # Maintain reference

                            meshes_list = self.parsed_data.json.get("meshes", [])
                            if mesh_idx < len(meshes_list):
                                mesh_node = meshes_list[mesh_idx]
                                primitives = mesh_node.get("primitives", [])
                                if primitives:
                                    primitive = primitives[0]
                                    targets = primitive.get("targets", [])

                                    if morph_target_idx < len(targets):
                                        position_accessor_idx = targets[morph_target_idx].get("POSITION")

                                        if position_accessor_idx is not None:
                                            # Pull individual vertex track offset array stream
                                            raw_deltas = read_accessor(self.parsed_data.json, self.parsed_data.bin_blob, position_accessor_idx)
                                            np_deltas = np.array(raw_deltas, dtype=np.float32)

                                            # Accumulate the weighted blend value
                                            if accumulated_deltas is None:
                                                accumulated_deltas = np_deltas * bind_weight
                                            else:
                                                # Match structural shape sizes to avoid indexing overflow steps
                                                if accumulated_deltas.shape == np_deltas.shape:
                                                    accumulated_deltas += (np_deltas * bind_weight)

                        # If we have successfully accumulated a non-empty morph target matrix, blit it down!
                        if accumulated_deltas is not None and target_mesh_idx is not None:
                            # Ensure data layout is continuous memory float32 arrays
                            cooked_buffer = np.ascontiguousarray(accumulated_deltas, dtype=np.float32)

                            self.gn.update_morph_data(
                                target_mesh_idx,
                                slot_idx,
                                cooked_buffer
                            )
                            print(f"✅ Blit Fully Compiled Compound Shape for '{preset_name}' to C++ Mesh {target_mesh_idx} Slot {slot_idx}")

            # Position camera to view Kisayo
        self.gn.set_camera_position(0.0, 1.5, 3.0)
        self.gn.set_camera_target(0.0, 1.0, 0.0)

        print("\n🚀 Multi-Draw Engine Ready!")
        print("🎮 Use WASDEQ + mouse to navigate. ESC to toggle mouse.")

       # 1. During Setup (ONLY ONCE)
        #MORPH_SLOTS = ["Fcl_EYE_Close", "Fcl_ALL_Surprised", "Fcl_MTH_E", "Fcl_MTH_I"]
        #face_mesh_index = -1
        


        for i, part in enumerate(sorted_parts):
            #if "Face" in part["name"]:
            #    # Save every morph the VRM has into our library
            #    self.face_mesh_indices.append(i)
            #    self.face_morph_library = part["morph_targets"]
            upload_list = []
            
            if isinstance(part["morph_targets"], list):
                upload_list = part["morph_targets"]
            elif isinstance(part["morph_targets"], dict):
                upload_list = list(part["morph_targets"].values())

            all_morphs = part["morph_targets"]

            self.gn.upload_mesh(
                part["vertices"], 
                part["normals"], 
                part["uvs"],
                part["joints"], 
                part["weights"], 
                part["indices"],
                upload_list,
                part["tex_id"],
                self.scene.get_all().index(self.model_entity),
                part["vertex_count"]
            )
            
            

        self.face_mesh_indices = []
        self.face_morph_library = {} 
    
        for i, part in enumerate(sorted_parts):
            if "Face" in part["name"]:
                self.face_mesh_indices.append(i)
                self.face_morph_library = part["morph_targets"]
                print(f"✅ Detected Face Mesh: '{part['name']}' at Render Index {i} with {len(part['morph_targets'])} morph targets.")
        
        # Fallback mechanism: If no explicit mesh is tagged "Face", 
        # default target allocation directly to Mesh Index 1
        if not self.face_mesh_indices and len(sorted_parts) > 1:
            print("⚠️ No explicit 'Face' string found in mesh names. Falling back to default Mesh Index 1 for morph tracking.")
            self.face_mesh_indices.append(1)
            
            # Check if the packed parsing layer completely missed the tracks
            if not sorted_parts[1]["morph_targets"]:
                print("💥 Detector alert: 'morph_targets' dictionary is completely empty! Generating synthetic runtime tracking keys...")
                
                # Synthetic mapping: maps behavior keys to dummy arrays 
                # This prevents runtime key errors when Blinker/Breather try to read from the dictionary!
                # We initialize them to empty tracks since the actual heavy vertex math 
                # is already safely blitted into C++ slots 0 and 1 via `update_morph_data`!
                dummy_vertex_offsets = np.zeros_like(sorted_parts[1]["vertices"])
                self.face_morph_library = {
                    "Fcl_EYE_Close": dummy_vertex_offsets,
                    "Fcl_ALL_Surprised": dummy_vertex_offsets,
                    "Fcl_MTH_E": dummy_vertex_offsets,
                    "Fcl_MTH_I": dummy_vertex_offsets
                }
            else:
                self.face_morph_library = sorted_parts[1]["morph_targets"]

        #print("🎯 Final Target Parameters:", self.face_mesh_indices, list(self.face_morph_library.items()))

        """for i, slot_name in enumerate(MORPH_SLOTS):
                if slot_name in all_morphs:
                    data = all_morphs[slot_name]
                    upload_list.append(data)
                else:
                    upload_list.append(np.zeros_like(part["vertices"]))

            self.gn.upload_mesh(
                part["vertices"], 
                part["normals"], 
                part["uvs"],
                part["joints"], 
                part["weights"], 
                part["indices"],
                upload_list,
                part["tex_id"],
                self.scene.get_all().index(self.model_entity),
                part["vertex_count"]
            )"""

    def init_entities(self):
        
        # Initialize renderer
        if self.gn.init_renderer(1280, 720) != 0:
            print("❌ Renderer init failed")
            sys.exit(1)
        
        self.context = UpdateContext()
        self.context.gn=self.gn
        self.scene = Scene(self.context)
        self.context.scene = self.scene

        self.model_entity = Entity("Kisayo")
        self.model_entity.add_component("transform", Transform())
        if hasattr(self, 'parsed_data') and self.parsed_data.vrm_version == 0:
            print("🔄 VRM0 asset orientation correction applied: Rotating model 180° around Y-Axis.")
            # If your engine uses Euler angles (Pitch, Yaw, Roll) in degrees or radians:
            # Assuming radians here. Adjust to 180.0 if your engine expects degrees!
            self.model_entity.get("transform").rotation = np.array([0.0, 180.0, 0.0]) # type: ignore
        else:
            self.model_entity.get("transform").rotation = np.array([0.0, 0.0, 0.0]) # type: ignore

        self.scene.add(self.model_entity)

        self.camera_entity = Entity("MainCamera")
        self.camera_entity.add_component("transform", Transform(camera=True) )
        self.camera_entity.add_component("Camera", CameraComponent())

        self.scene.add(self.camera_entity)

        cube_entity = Entity("TargetCube")
        cube_entity.add_component("transform", Transform())
        cube_entity.get("transform").position = np.array([1.0, 0.0, 0.0]) #type: ignore
        cube_entity.get("transform").scale = np.array([0.5, 0.5, 0.5]) #type: ignore
        cube_entity.add_component("mesh", MeshComponent("cube", size=0.1))
        self.scene.add(cube_entity)
        self.setup_load()
        self.gn.set_entity_list([e.name for e in self.scene.get_all()])

        
        
        

        self.model_entity.add_component("skeleton", self.skeleton)
        self.model_entity.add_component("animator", self.animator)
        self.model_entity.add_component("morph_manager", self.Mmanager)
        self.model_entity.add_component("skeleton_manager", self.Smanager)

        
        

        morph = self.model_entity.get("morph_manager")
        skeletonM = self.model_entity.get("skeleton_manager")
        skeleton = self.model_entity.get("skeleton")
        morph.load_behaviors() # type: ignore
        skeletonM.load_behaviors(self.gn) #type: ignore
        self.context.skeleton = skeleton

        morph.face_mesh_indices = self.face_mesh_indices # type: ignore
        morph.inject_morph_library(self.face_morph_library) # type: ignore
        
        

        #self.scene.update_list()
        #gn.set_entity_list([e.name for e in self.scene.get_all()])
        #self.animator.play_clip("hi")


    def gameloop(self):
        last_time = timen.time()
        animator = self.model_entity.get("animator")
        #morph.trigger_mouth_sequence("test.gpseq")
        self.context.animator = animator
        camera_comp = self.camera_entity.get("Camera")
        
        import sys
        print([k for k in sys.modules.keys() if "greko" in k])
        while not self.gn.should_close():
            self.gn.clear_screen()
            current_time = timen.time()
            dt = current_time - last_time
            last_time = current_time

            selected = self.context.gn.get_selected_entity_index() # type: ignore
            self.context.target_index = selected
            #self.context.target_index = camera_comp.position  # type: ignore

            #if gn.is_key_down(290):  # F1 Editor Mode
            #    animator.active_clip = None  # type: ignore
#
            #else:
            #    animator.update(dt, self.context) # type: ignore

            self.scene.update(dt, self.context)
            self.gn.draw_scene() 
            self.gn.swap_buffers()

        self.gn.terminate()

if __name__ == "__main__":
    import core.greko_native as gn
    cfg = json.load(open('./config.json', 'r'))

    engine = Engine(gn, "./sample/loli.vrm")
    engine.eye_constraints = cfg.get("eye_constraints", engine.eye_constraints)
    engine.init_entities()
    engine.gameloop()