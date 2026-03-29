#from datetime import time
import time as timen
import math
import tempfile
import sys
import os, shutil, importlib, sysconfig
import numpy as np

#from core import skeleton
import importlib.util
import sys

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
from core.skeleton import Skeleton
from core.behaviours_manager import MorphBehaviorManager, SkeletonBehaviorManager
from core.mesh_data import package_mesh
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

    def setup_load(self): 
        vrm_path = self.assets_path #"assets/kiyo.vrm"
        
        if not os.path.exists(vrm_path):
            print(f"❌ VRM not found: {vrm_path}")
            self.gn.terminate()
            return

        print(f"📂 Loading VRM: {vrm_path}")


        self.parsed_data = parse_glb(vrm_path)
        print("🦴 Building Skeleton...")
        self.skeleton = Skeleton(self.gn, self.parsed_data.json, self.parsed_data.bin_blob)
        print("Joint names:", self.skeleton.joint_names[:5])
        print("Joint count:", len(self.skeleton.joint_nodes))

        self.gn.set_joint_names(self.skeleton.joint_names)
        self.gn.set_joint_count(len(self.skeleton.joint_nodes))

        
        self.animator = Animator(self.gn, self.skeleton)
        self.Mmanager = MorphBehaviorManager()
        self.Smanager = SkeletonBehaviorManager(self.skeleton)
        

        # FLAG: Render Parts List
        # We store each mesh piece separately instead of combining them.
        render_parts = []
        primitive_count = 0

        for mesh_idx, mesh in enumerate(self.parsed_data.json["meshes"]):
            mesh_name = mesh.get("name", f"Mesh_{mesh_idx}")

            for prim_idx, primitive in enumerate(mesh["primitives"]):
                packed = package_mesh(self.parsed_data.json, self.parsed_data.bin_blob, primitive)

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
                    "transparent": is_transparent # Tag it for sorting
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

        # Position camera to view Kisayo
        self.gn.set_camera_position(0.0, 1.5, 3.0)
        self.gn.set_camera_target(0.0, 1.0, 0.0)

        print("\n🚀 Multi-Draw Engine Ready!")
        print("🎮 Use WASDEQ + mouse to navigate. ESC to toggle mouse.")

       # 1. During Setup (ONLY ONCE)
        MORPH_SLOTS = ["Fcl_EYE_Close", "Fcl_ALL_Surprised", "Fcl_MTH_E", "Fcl_MTH_I"]
        #face_mesh_index = -1
        self.face_mesh_indices = []
        self.face_morph_library = {} 


        for i, part in enumerate(sorted_parts):
            if "Face" in part["name"]:
                # Save every morph the VRM has into our library
                self.face_mesh_indices.append(i)
                self.face_morph_library = part["morph_targets"]

            all_morphs = part["morph_targets"]
            upload_list = []

            for i, slot_name in enumerate(MORPH_SLOTS):
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
                self.scene.get_all().index(self.model_entity)
            )

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
        self.model_entity.get("transform").position = np.array([0.0, 0.0, 0.0]) # type: ignore

        self.scene.add(self.model_entity)

        self.camera_entity = Entity("MainCamera")
        self.camera_entity.add_component("transform", Transform(camera=True) )
        self.camera_entity.add_component("Camera", CameraComponent())

        self.scene.add(self.camera_entity)

        cube_entity = Entity("TargetCube")
        cube_entity.add_component("transform", Transform())
        cube_entity.get("transform").position = np.array([1.0, 0.0, 0.0]) #type: ignore
        cube_entity.get("transform").scale = np.array([0.5, 0.5, 0.5]) #type: ignore
        cube_entity.add_component("mesh", MeshComponent("cube", size=1.0))
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
        skeletonM.load_behaviors() #type: ignore
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
    engine = Engine(gn, "./assets/kisayov2.vrm")
    
    engine.init_entities()
    engine.gameloop()