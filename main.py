import os
from platform import node
import sys
from textwrap import indent

# FLAG: The Muzzle
# We redirect the low-level system error stream to 'devnull' (a black hole).
# This is the only way to stop C++ libraries from talking to your terminal.
#f = open(os.devnull, 'w')
#os.dup2(f.fileno(), sys.stderr.fileno())

from panda3d.core import load_prc_file_data, DirectionalLight, AmbientLight, VBase4, LineSegs, Shader, Character, LVecBase4f, TextNode
from panda3d.core import load_prc_file_data, LoaderFileTypeRegistry
#region FLAGS OLD
# --- 1. THE NATIVE VRM/GLB FIX (CRITICAL) ---
# FLAG: This forces Panda3D to use the C++ Assimp loader instead of the Python one.
# This is the primary fix for the 'KeyError: 0' crash.
load_prc_file_data("", "load-file-type p3assimp glb")
load_prc_file_data("", "load-file-type p3assimp vrm")

# FLAG: We disable the Python-based gltf loader to prevent it from 'stealing' the file.
load_prc_file_data("", "gltf-library assimp") 

# --- 2. GPU & MEMORY OPTIMIZATION (GT 710 SUPPORT) ---
# FLAG: Resize massive VRoid textures to 1024 to prevent VRAM overflow.
load_prc_file_data("", "max-texture-dimension 1024")

# FLAG: Enable texture compression to save your 1GB/2GB VRAM.
load_prc_file_data("", "texture-compression #t")

# FLAG: Offload skeletal animation to the GPU (Hardware Skinning).
load_prc_file_data("", "hardware-animated-vertices #t")

# --- 3. LOADER COMPATIBILITY & SILENCING ---
# FLAG: Tell the loader to ignore the VRoid-specific tags that usually cause crashes.
load_prc_file_data("", "gltf-ignore-extensions #t")
load_prc_file_data("", "gltf-ignore-materials #t")

# FLAG: Disable sRGB linearization by the loader; we handle this in our MToon shader.
load_prc_file_data("", "gltf-linearize-srgb #f")

# --- 4. DEBUGGING & LOGGING ---
# FLAG: Set to 'warning' to hide the wall of text, or 'debug' to see every bone name.
load_prc_file_data("", "notify-level-loader warning")
load_prc_file_data("", "notify-level-gltf warning")
#endregion FLAGS OLD

# --- 1. GLOBAL LOADER OVERRIDE (Must be at the very top) ---

# FLAG: Anti-Debone (The "Don't Delete My Bones" Kit)
# This prevents Assimp from merging or deleting 'empty' nodes.
#load_prc_file_data("", "assimp-post-process-steps -debone") # Specifically tells Assimp NO DEBONING
#load_prc_file_data("", "assimp-post-process-steps -optimize-graph")
#load_prc_file_data("", "assimp-post-process-steps -optimize-meshes")


#load_prc_file_data("", "assimp-optimize-graph false")
#load_prc_file_data("", "assimp-collapse-nodes false")
load_prc_file_data("", "assimp-unused-textures false") 
load_prc_file_data("", "assimp-skip-animations false")
load_prc_file_data("", "assimp-keep-nodes #t")



load_prc_file_data("", "load-file-type p3assimp glb")
load_prc_file_data("", "load-file-type p3assimp vrm")
load_prc_file_data("", "load-file-type gltf panda3d-gltf")
load_prc_file_data("", "load-file-type glb panda3d-gltf")
load_prc_file_data("", "gltf-library assimp") # Force C++ backend

# --- 2. PERFORMANCE & GT 710 OPTIMIZATIONS ---
load_prc_file_data("", "max-texture-dimension 1024")
load_prc_file_data("", "texture-compression #t")
load_prc_file_data("", "hardware-animated-vertices #t")
load_prc_file_data("", "gltf-ignore-extensions #t")
load_prc_file_data("", "gltf-ignore-materials #t")
load_prc_file_data("", "gltf-linearize-srgb #f")

# --- 3. SILENCE THE CRASH LOGS ---
load_prc_file_data("", "notify-level-loader error")
load_prc_file_data("", "notify-level-gltf error")
load_prc_file_data("", "notify-level-assimp error")
load_prc_file_data("", "notify-level-p3assimp error")
load_prc_file_data("", "assimp-log-level error")


import gltf, json
import simplepbr
from engine.base_engine import VroidEngine
from engine.entity import Entity
from vrmmanager.vrm_handler import VRMHandler
from engine.camera_controller import CameraController


# --- THE CHARACTER BRAIN ---
class VRoidCharacter(Entity):
    def __init__(self, engine, char_config, sun_light):

        super().__init__(name=char_config["name"])
        self.engine = engine
        self.handler = VRMHandler(engine)

        # FLAG: Terminal Silencer
        # We temporarily redirect stderr to stop the aiBone spam.
        actual_stderr = sys.stderr
        null_f = open(os.devnull, 'w')
        sys.stderr = null_f

        try:
            # This is where the noisy loading happens
            vrm_path = char_config["fixed_path"]
            self.model = self.handler.load_character(vrm_path)
        finally:
            # FLAG: Restore the Terminal
            # We MUST bring back stderr or we won't see actual Python crashes!
            sys.stderr = actual_stderr
            null_f.close() # FLAG: Always restore stderr!
        
        if self.model:
            print(f"🎉 VRoidCharacter {char_config['name']} initialized successfully.")
            pos = char_config.get("start_pos", (0, 5, 0))
            self.model.reparent_to(self.engine.render)
            #self.model.set_scale(10.0)
            # --- THE MTOON SHADER IMPLEMENTATION ---
            # Flag: We use GLSL 330 for compatibility with your GT 710.

            mtoon_shader = Shader.load(
                Shader.SL_GLSL,
                vertex="shaders/mtoon.vert",
                fragment="shaders/mtoon.frag"
            )

            # --- APPLYING THE FLAGS ---
            # Flag: Priority 10 ensures this overrides simplepbr's global shader.
            self.model.set_shader(mtoon_shader, 10)
            
            # Flag: Pass the sun and ambient light specifically to the shader
            self.model.set_shader_input("sun", sun_light) 
            self.model.set_shader_input("ambient", ambient_np.node().get_color())
            # Remove flatten_strong() if you want to keep MToon material separation!
            # self.model.flatten_strong() 

            #FOR DEV ONLY NO OTHER PURPOSE!
            #self.list_blendshapes()

            self.model.set_h(0)
            self.model.set_pos(*pos)
            self.model.set_p(90)
            print(f"✅ {self.name} is rendered with MToon logic.")

    def update(self, dt: float):
        """
        This runs every frame. We can put logic here!
        """
        if self.model:
            # Example Logic: A very slow "Idle" rotation
            '''current_h = self.model.get_h()
            self.model.set_h(current_h + (10 * dt))'''


            pass

    #FOR DEV ONLY NO OTHER PURPOSE!
    def list_blendshapes(self):
        print(f"\n--- 📂 TOTAL FILENAME DUMP: {self.name} ---")

        def walk(node_path, depth=0):
            node = node_path.node()
            indent = "  " * depth
            print(f"{indent}↳ [{type(node).__name__}] {node_path.get_name()}")

            if hasattr(node, 'get_bundle'):
                bundle = node.get_bundle(0)
                print(f"{indent}    📦 ANIM BUNDLE FOUND: {bundle.get_name()}")
                # This might contain the 'Blink' even if Sliders are missing!

            # FLAG: Interrogate Geometry
            if hasattr(node, 'get_num_geoms'):
                for i in range(node.get_num_geoms()):
                    geom = node.get_geom(i)
                    vdata = geom.get_vertex_data()

                    # FLAG: The Slider Table Check
                    # We check if the table exists. If it does, we found the morphs!
                    table = vdata.get_slider_table()
                    if table:
                        num_sliders = table.get_num_sliders()
                        print(f"{indent}    💎 FOUND SLIDER TABLE: {num_sliders} shapes")
                        for s in range(num_sliders):
                            slider = table.get_slider(s)
                            slider_name = slider.get_name()
                            print(f"{indent}      - {slider_name}")

                            # Save to file for later use in blink.py
                            with open("blendshapes_reference.txt", "a") as f:
                                f.write(f"{slider_name}\n")

            for child in node_path.get_children():
                walk(child, depth + 1)

        # Clear the reference file before starting
        open("blendshapes_reference.txt", "w").close()
        walk(self.model)
        print("-------------------------------------------\n")

def create_grid(app, size=50, step=1):
    """
    size: How far the grid goes in each direction (e.g., 50 units).
    step: The gap between lines (1 unit is standard).
    """
    
    ls = LineSegs()
    ls.set_color(0.4, 0.4, 0.4, 1) # Darker gray for a professional look
    ls.set_thickness(1.0)

    # Draw the lines along the X axis
    for i in range(-size, size + 1, step):
        ls.move_to(i, -size, 0)
        ls.draw_to(i, size, 0)
        
    # Draw the lines along the Y axis
    for i in range(-size, size + 1, step):
        ls.move_to(-size, i, 0)
        ls.draw_to(size, i, 0)
        
    # FLAG: Create the Node
    grid_node = ls.create()
    grid_np = app.render.attach_new_node(grid_node)
    return grid_np

# --- THE CLEANUP LOGIC ---
def force_cpp_loader():
    # FLAG: LoaderFileTypeRegistry
    # This is the actual name of the registry in Panda3D's Python API.
    registry = LoaderFileTypeRegistry.get_global_ptr()
    
    # FLAG: unregister_type
    # We find the Python 'gltf' plugin and kick it out of the engine.
    # This forces Panda3D to use the C++ Assimp loader for .glb files.
    gltf_plugin = registry.get_type_from_extension("glb")
    if gltf_plugin:
        registry.unregister_type(gltf_plugin)
        print("🚫 Python glTF loader unregistered. C++ Assimp is now active.")

#--------------------------------------ENTRY POINT FOR RUNNING THE ENGINE----------------------------------------#
if __name__ == "__main__":
    # --- LOAD SESSION DATA ---
    session_file = "current_session.json"
    if os.path.exists(session_file):
        with open(session_file, "r") as f:
            session_data = json.load(f)
    else:
        session_data = {"name": "Kiyo_Fallback", "fixed_path": "assets/kisayo_.glb", "start_pos": (0, 5, 0)}

    # --- FLAG: LOAD LIGHTING JSON ---
    lighting_file = "lighting.json"
    if os.path.exists(lighting_file):
        with open(lighting_file, "r") as f:
            l_cfg = json.load(f)
    else:
        # Defaults if file is missing
        l_cfg = {"sun_intensity": 0.5, "amb_intensity": 0.2, "sun_pitch": -60}

    app = VroidEngine(title=f"Greko VRM Engine v1.0 - {session_data['name']}", width=1280, height=720)

    force_cpp_loader()
    
    # 1. DARKER BACKGROUND
    bg_color = pow(0.15, 2.2) 
    app.win.set_clear_color((bg_color, bg_color, bg_color, 1))

    # 2. CONTROLS
    cam_control = CameraController(app)
    cam_control.mouse_senst = 5
    cam_control.move_speed = 10.0
    cam_control.update(5, 10.0)

    # 3. THE KEY LIGHT (SUN)
    # FLAG: Intensity Mapping
    # We apply the intensity from JSON to the RGB channels
    si = l_cfg["sun_intensity"]
    sun = DirectionalLight('sun')
    sun.set_color(VBase4(si, si, si * 0.9, 1)) 
    sun_np = app.render.attach_new_node(sun)
    
    # FLAG: Sun Pitch from JSON
    # This lets you change the time of day via the JSON file
    sun_np.set_hpr(45, l_cfg["sun_pitch"], 0)
    app.render.set_light(sun_np)

    # 4. THE AMBIENT LIGHT
    ai = l_cfg["amb_intensity"]
    ambient = AmbientLight('ambient')
    ambient.set_color(VBase4(ai, ai, ai * 1.1, 1)) # Slightly blue-ish ambient
    ambient_np = app.render.attach_new_node(ambient)
    app.render.set_light(ambient_np)

    simplepbr.init(use_normal_maps=False, max_lights=4, exposure=1, msaa_samples=4)

    # FLAG: Pass Lighting Config to Character
    # This allows the shader to use these values for toon math
    player = VRoidCharacter(app, session_data, sun_np)
    app.add_entity(player)

    grid = create_grid(app, size=30, step=1)
    app.setup_debug_ui(sun_np, ambient_np)
    
    print(f"🚀 Engine running!")
    app.run()