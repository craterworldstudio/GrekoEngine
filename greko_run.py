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
        return os.path.join(sys._MEIPASS, relative)  # type: ignore
    return os.path.join(os.path.abspath("."), relative)

def load_native(path):

    # 🔥 CRITICAL: Use MEIPASS if available
    if hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS #type: ignore
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

        if not os.path.exists(self.assets_path):
            print(f"❌ VRM not found: {self.assets_path}")
            self.gn.terminate()
            return
        
        self.eye_constraints = {
            "inner_yaw": 8.0,
            "outer_yaw": 6.0,
            "up_pitch": 4.0,
            "down_pitch": 3.0
        }

        file_name = os.path.basename(self.assets_path)
        model_name = os.path.splitext(file_name)[0]
        self.model_name = model_name

    def setup_load(self): 
        vrm_path = self.assets_path #"assets/kiyo.vrm"
        
        
        
        

        print(f"📂 Loading VRM: {vrm_path}")

        self.gn.set_eye_constraints(
            self.eye_constraints["inner_yaw"],
            self.eye_constraints["outer_yaw"],
            self.eye_constraints["up_pitch"],
            self.eye_constraints["down_pitch"]
        )
        
        #print(self.model_name)
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

            #skin0 = self.parsed_data.json["skins"][0]
            #skin1 = self.parsed_data.json["skins"][1]

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
                # We use explicit material alpha mode when available, otherwise only
                # treat face/eye meshes as transparent for proper draw ordering.
                is_transparent = False
                material_index = primitive.get("material")
                if material_index is not None:
                    material = self.parsed_data.json.get("materials", [])[material_index]
                    alpha_mode = material.get("alphaMode", "OPAQUE")
                    is_transparent = alpha_mode != "OPAQUE"
                if not is_transparent:
                    mesh_name_lower = mesh_name.lower()
                    if "face" in mesh_name_lower or "eye" in mesh_name_lower:
                        is_transparent = True

                tex_id = 0
                if packed.get('texture') is not None:
                    tex_id = self.gn.upload_texture(bytes(packed['texture']), srgb=True)
                    #print(f"     ✅ Texture ID: {tex_id}")

                render_parts.append({
                    "name": mesh_name,
                    "src_mesh_idx": mesh_idx,
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

        # We'll collect any precompiled VRM0 morph buffers here and apply them
        # after we have uploaded meshes to the GPU so we can map glTF mesh
        # indices to actual renderer scene mesh indices.
        precompiled_morphs = []

        # =========================================================================
        # 🔗 VRM 0.0 STARTUP BLENDSHAPE PRE-COMPILE
        # =========================================================================
        if self.parsed_data.vrm_version == 0:
            vrm_ext = self.parsed_data.json.get("extensions", {})
            if "VRM" in vrm_ext:
                print("📦 [Loader] Pre-compiling VRM0 Compound Expression Groups...")
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

                        accumulated_deltas = None
                        target_mesh_idx = None

                        print(f"🧬 Precompiling Compound Preset '{preset_name}' into GPU slot {slot_idx}...")

                        for bind in binds:
                            mesh_idx = int(bind.get("mesh", 0))
                            morph_target_idx = int(bind.get("index", 0))
                            bind_weight = float(bind.get("weight", 100.0)) / 100.0

                            target_mesh_idx = mesh_idx

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
                                            raw_deltas = read_accessor(self.parsed_data.json, self.parsed_data.bin_blob, position_accessor_idx)
                                            np_deltas = np.array(raw_deltas, dtype=np.float32)

                                            if accumulated_deltas is None:
                                                accumulated_deltas = np_deltas * bind_weight
                                            else:
                                                if accumulated_deltas.shape == np_deltas.shape:
                                                    accumulated_deltas += (np_deltas * bind_weight)

                        if accumulated_deltas is not None and target_mesh_idx is not None:
                            cooked_buffer = np.ascontiguousarray(accumulated_deltas, dtype=np.float32)
                            precompiled_morphs.append((int(target_mesh_idx), int(slot_idx), cooked_buffer))
                            print(f"✅ Precompiled '{preset_name}' for glTF mesh {target_mesh_idx} -> slot {slot_idx}")

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

        # Build a mapping from original glTF mesh index -> scene mesh index
        gltf_to_scene = {}
        for scene_idx, part in enumerate(sorted_parts):
            if "src_mesh_idx" in part:
                gltf_to_scene[int(part["src_mesh_idx"]) ] = scene_idx

        # Apply any precompiled VRM0 morph buffers to the correct scene meshes
        if precompiled_morphs:
            for (gltf_mesh_idx, slot_idx, buf) in precompiled_morphs:
                scene_idx = gltf_to_scene.get(int(gltf_mesh_idx))
                if scene_idx is None:
                    print(f"⚠️ Precompiled morph target references unknown glTF mesh {gltf_mesh_idx}; skipping")
                    continue
                try:
                    expected_vertices = sorted_parts[scene_idx]["vertex_count"]
                    expected_elements = int(expected_vertices) * 3

                    # buf may be a (N,3) array; ensure we pass a flat float32 array of correct length
                    flat = buf.ravel()
                    if flat.size != expected_elements:
                        print(f"⚠️ Morph size mismatch for scene mesh {scene_idx}: expected {expected_elements} floats, got {flat.size}. Resizing to fit.")
                        new_buf = np.zeros((expected_elements,), dtype=np.float32)
                        copy_count = min(flat.size, expected_elements)
                        new_buf[:copy_count] = flat[:copy_count]
                        flat = new_buf

                    self.gn.update_morph_data(scene_idx, slot_idx, flat)
                    print(f"✅ Applied precompiled morph for glTF mesh {gltf_mesh_idx} -> scene mesh {scene_idx} slot {slot_idx}")
                except Exception as e:
                    print(f"❌ Failed to apply precompiled morph to scene mesh {scene_idx}: {e}")
        self.face_morph_names = []


        for i, part in enumerate(sorted_parts):
            name_lower = part["name"].lower()
            if "face" in name_lower or "eye" in name_lower:
                self.face_mesh_indices.append(i)
                self.face_morph_library = part["morph_targets"]
                print(f"✅ Detected Face/Eye Mesh: '{part['name']}' at Render Index {i} with {len(part['morph_targets'])} morph targets.")

        # Fallback mechanism: If no explicit face/eye mesh was tagged,
        # choose the first mesh that contains morph targets.
        if not self.face_mesh_indices:
            for i, part in enumerate(sorted_parts):
                if part["morph_targets"]:
                    self.face_mesh_indices.append(i)
                    self.face_morph_library = part["morph_targets"]
                    print(f"⚠️ No explicit face/eye mesh name found. Using first morph-enabled mesh '{part['name']}' at index {i}.")
                    break

        if self.face_mesh_indices and not self.face_morph_library:
            print("💥 Detector alert: selected face mesh has no morph targets. Falling back to synthetic placeholders.")
            dummy_vertex_offsets = np.zeros_like(sorted_parts[self.face_mesh_indices[0]]["vertices"])
            self.face_morph_library = {
                "Fcl_EYE_Close": dummy_vertex_offsets,
                "Fcl_ALL_Surprised": dummy_vertex_offsets,
                "Fcl_MTH_E": dummy_vertex_offsets,
                "Fcl_MTH_I": dummy_vertex_offsets
            }

        self.face_morph_names = list(self.face_morph_library.keys())

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
                        
        self.model_entity = Entity(self.model_name)
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

        # Expose the available VRM morph names to the renderer GUI
        if hasattr(self.gn, 'set_face_morph_targets_dual'):
            self.process_and_sync_morphs(self.face_morph_names, self.gn)
        elif hasattr(self.gn, 'set_face_morph_targets'):
            # Backwards-compatible single-list caller
            self.gn.set_face_morph_targets(self.face_morph_names)

        if hasattr(self.gn, 'set_face_morph_slot_selections'):
            self.gn.set_face_morph_slot_selections([
                self.face_morph_names.index(morph.morph_slot_targets.get(0)) if morph.morph_slot_targets.get(0) in self.face_morph_names else -1, #type: ignore 
                self.face_morph_names.index(morph.morph_slot_targets.get(1)) if morph.morph_slot_targets.get(1) in self.face_morph_names else -1, #type: ignore 
                self.face_morph_names.index(morph.morph_slot_targets.get(2)) if morph.morph_slot_targets.get(2) in self.face_morph_names else -1, #type: ignore 
                self.face_morph_names.index(morph.morph_slot_targets.get(3)) if morph.morph_slot_targets.get(3) in self.face_morph_names else -1, #type: ignore 
                self.face_morph_names.index(morph.morph_slot_targets.get(4)) if morph.morph_slot_targets.get(4) in self.face_morph_names else -1, #type: ignore 
                self.face_morph_names.index(morph.morph_slot_targets.get(5)) if morph.morph_slot_targets.get(5) in self.face_morph_names else -1, #type: ignore 
                self.face_morph_names.index(morph.morph_slot_targets.get(6)) if morph.morph_slot_targets.get(6) in self.face_morph_names else -1, #type: ignore 
                self.face_morph_names.index(morph.morph_slot_targets.get(7)) if morph.morph_slot_targets.get(7) in self.face_morph_names else -1, #type: ignore 
                self.face_morph_names.index(morph.morph_slot_targets.get(8)) if morph.morph_slot_targets.get(8) in self.face_morph_names else -1, #type: ignore 
                self.face_morph_names.index(morph.morph_slot_targets.get(9)) if morph.morph_slot_targets.get(9) in self.face_morph_names else -1  #type: ignore  
            ])

        # Register the morph selection callback so the native GUI can tell Python
        # when the user chooses a different face blendshape for a behavior slot.
        if hasattr(self.gn, 'register_morph_assignment_callback'):
            self.gn.register_morph_assignment_callback(morph.handle_morph_assignment) # type: ignore
        
        

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

        if hasattr(self.gn, 'clear_morph_assignment_callback'):
            self.gn.clear_morph_assignment_callback()
        self.gn.terminate()


    def process_and_sync_morphs(self, raw_morph_list, renderer_module=None):
        """
        Takes raw model strings (e.g., Japanese), parses out digit tracking prefixes,
        dynamically translates them to English, and pushes them to the C++ dual wrapper binding.

        """
        import re
        try:
            from deep_translator import GoogleTranslator
            have_translator = True
        except Exception:
            GoogleTranslator = None
            have_translator = False

        translated_display_names = []
        translator = GoogleTranslator(source='auto', target='en') if have_translator else None   #type: ignore

        if not have_translator:
            print("⚠️ deep-translator not available. Install with: pip install deep-translator")

        for raw_name in raw_morph_list:
            prefix_match = re.match(r"^([0-9]+\s*\.\s*)", raw_name)
            prefix = prefix_match.group(1) if prefix_match else ""
            clean_name = raw_name[len(prefix):].strip()
            
            if clean_name and translator is not None:
                try:
                    english_text = translator.translate(clean_name)
                    translated_display_names.append(f"{prefix}{english_text}")
                except Exception:
                    translated_display_names.append(raw_name)
            else:
                # No translator available or empty clean name: fall back to raw
                translated_display_names.append(raw_name)
    

        target_renderer = renderer_module
        if target_renderer is None:
            try:
                import core.greko_native as default_gn
                target_renderer = default_gn
            except Exception:
                target_renderer = None


        if target_renderer is None:
            print("⚠️ process_and_sync_morphs: No renderer module available to sync morphs.")
            return

        # Prefer the new dual API if available
        if hasattr(target_renderer, 'set_face_morph_targets_dual'):
            target_renderer.set_face_morph_targets_dual(raw_morph_list, translated_display_names)
        elif hasattr(target_renderer, 'set_face_morph_targets'):
            # Backwards-compatible: send the raw list and use it as display names too
            target_renderer.set_face_morph_targets(raw_morph_list)
        else:
            print("⚠️ Renderer binding lacks face morph target setter.")

    


if __name__ == "__main__":
    import core.greko_native as gn
    cfg = json.load(open('./config.json', 'r'))

    #engine = Engine(gn, "./sample/darkness0.vrm")
    engine = Engine(gn, "./assets/furina3.vrm")
    engine.eye_constraints = cfg.get("eye_constraints", engine.eye_constraints)
    engine.init_entities()
    engine.gameloop()