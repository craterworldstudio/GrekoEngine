
import json
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, GraphicsWindow, ClockObject, load_prc_file_data, VBase4
from direct.gui.DirectGui import DirectSlider, DirectLabel, DirectFrame, DirectButton, DGG
from panda3d.core import LVecBase4f, TextNode
from .entity import Entity

class VroidEngine(ShowBase):
    '''
    <h3> Base Class for the VRoid Engine
    containing core loop and entity management. 
    </h3>
    add_entity
    update_loop
    setup_debug_ui
    update_debug_lights
    '''
    def __init__(self, title="My VRM Engine", width=1280, height=720):
    


        '''# --- LOADER FLAG ---
        # This tells Panda3D: "If you see .vrm, use the gltf loader"
        from panda3d.core import LoaderOptions
        self.gltf_settings = gltf.GltfSettings()'''
        #gltf.patch_loader(self.loader)

        load_prc_file_data("", "load-file-type gltf vrm")
        load_prc_file_data("", "load-file-type gltf glb")
        load_prc_file_data("", "gl-check-errors #f")

        # Initialize the Panda3D window and hardware drivers
        super().__init__()
        
        # --- WINDOW SETUP ---
        self.win: GraphicsWindow = self.win
        properties = WindowProperties()
        properties.setTitle(title)
        properties.setSize(width, height)
        self.win.requestProperties(properties)
        
        # --- ENGINE FLAGS & STATE ---
        self.entities = []
        self.is_engine_running = True # Master Flag: keeps the system alive
        
        # Performance Flag: Show FPS in the corner
        self.set_frame_rate_meter(True) 
        
        # --- THE GAME LOOP (Task Manager) ---
        # Instead of a 'while True', Panda3D uses 'Tasks'.
        # This tells the engine to run 'self.update_loop' every single frame.
        self.taskMgr.add(self.update_loop, "MainUpdateLoop")

    def add_entity(self, entity: Entity):
        """Register a new entity into the engine loop."""
        self.entities.append(entity)

    def update_loop(self, task):
        """The core loop that replaces your old GameLoop logic."""
        
        # Delta Time (dt): The time (in seconds) since the last frame.
        # Essential for keeping animations smooth regardless of FPS.
        dt = ClockObject.get_global_clock().getDt()
    
        # Iterate through all entities (Logic identical to your 2D loop)
        for ent in self.entities:
            # 1. Initialization Flag: Start the entity if it hasn't been yet
            if not ent.is_started:
                ent.start()
            
            # 2. Activity Flag: Only update if the entity is active
            if ent.is_active:
                ent.update(dt)

        # Flag: task.cont (Continue)
        # Telling the Task Manager to run this function again next frame.
        # If we returned task.done, the loop would stop.
        return task.cont
    

    # --- NEW: LIGHTING TWEAK MENU ---
    def setup_debug_ui(self, sun_np, amb_np):
        """FLAG: Modernized, Compact Glass UI for Real-time Tweak"""
        self.sun_np = sun_np
        self.amb_np = amb_np
    
        # 1. THE MAIN PANEL (Glass Background)
        # Using base.a2dTopLeft anchors the UI so it doesn't float toward the center on wide screens.
        self.debug_panel = DirectFrame(
            parent=self.a2dTopLeft,
            frameSize=(0, 0.65, -0.65, 0), # Width: 0.65, Height: 0.65
            pos=(0.05, 0, -0.05),        # Small margin from the corner
            frameColor=(0, 0, 0, 0.4),   # Semi-transparent black 'Glass'
            relief=DGG.FLAT
        )
    
        # 2. THE HEADER
        DirectLabel(
            parent=self.debug_panel,
            text="GREKO ENGINE // LIGHTING",
            scale=0.04,
            pos=(0.02, 0, -0.05),
            text_align=TextNode.ALeft,
            text_fg=(0.8, 0.8, 1, 1),    # Light blue 'Cyber' text
            frameColor=(0,0,0,0)
        )
    
        # 3. COMPACT SLIDER HELPER
        def make_compact_slider(label_text, pos_z, command, range_val, start_val):
            # Label above the slider
            DirectLabel(
                parent=self.debug_panel, text=label_text, scale=0.03, 
                pos=(0.02, 0, pos_z + 0.05), text_align=TextNode.ALeft,
                frameColor=(0,0,0,0), text_fg=(1,1,1,1)
            )
            # The Slider itself
            return DirectSlider(
                parent=self.debug_panel,
                range=range_val, value=start_val, 
                scale=0.2, pos=(0.25, 0, pos_z), 
                frameSize=(-1.2, 1.2, -0.04, 0.04), # Makes the bar thin
                frameColor=(0.3, 0.3, 0.3, 1),
                thumb_relief=DGG.FLAT,
                thumb_frameSize=(-0.06, 0.06, -0.15, 0.15), # Smaller thumb
                thumb_frameColor=(0.8, 0.8, 1, 1),
                command=command
            )
    
        # Sliders using the helper
        self.sun_slider = make_compact_slider("SUN INTENSITY", -0.15, self._update_debug_lights, (0, 2), sun_np.node().get_color()[0])
        self.amb_slider = make_compact_slider("AMBIENT FILL", -0.28, self._update_debug_lights, (0, 1), amb_np.node().get_color()[0])
        self.pitch_slider = make_compact_slider("SUN PITCH", -0.41, self._update_debug_lights, (-90, 0), sun_np.get_p())
    
        # 4. FLAT SAVE BUTTON
        self.save_btn = DirectButton(
            parent=self.debug_panel,
            text="SAVE TO JSON",
            scale=0.1,
            text_scale=0.4,
            pos=(0.3, 0, -0.58),
            frameSize=(-2.5, 2.5, -0.4, 0.8),
            relief=DGG.FLAT,
            frameColor=(0.2, 0.5, 0.2, 0.8), # Translucent Green
            text_fg=(1,1,1,1),
            command=self.save_lighting_to_json
        )

        self.accept("tab", self.toggle_debug_ui)

    def _update_debug_lights(self):
        # 1. Check if the sliders actually exist before reading them
        if not hasattr(self, 'sun_slider'): return

        s_val = self.sun_slider['value']
        a_val = self.amb_slider['value']
        p_val = self.pitch_slider['value']

        # 2. Update Sun (Directional Light)
        # We apply a slight warm tint (R and G are higher than B)
        if self.sun_np:
            self.sun_np.node().set_color(VBase4(s_val, s_val, s_val * 0.85, 1))
            self.sun_np.set_p(p_val)

        # 3. Update Ambient (Shadow Fill)
        # We apply a slight cool tint (B is higher than R and G)
        if self.amb_np:
            self.amb_np.node().set_color(VBase4(a_val * 0.9, a_val * 0.9, a_val, 1))

        # 4. Feedback for you to copy-paste later
        print(f"☀️ SUN: {s_val:.2f} (P: {p_val}) | 🌑 AMB: {a_val:.2f}")

    def save_lighting_to_json(self):
        try:
            data = {
                "sun_intensity": self.sun_slider['value'],
                "amb_intensity": self.amb_slider['value'],
                "sun_pitch": self.pitch_slider['value']
            }
            with open("lighting.json", "w") as f:
                json.dump(data, f, indent=4)
            print("💾 Settings saved to lighting.json!")
        except Exception as e:
            print(f"❌ Save failed: {e}")

    def toggle_debug_ui(self):
        """FLAG: The 'Invisibility Cloak' for your UI."""
        if hasattr(self, 'debug_panel'):
            if self.debug_panel.is_hidden():
                self.debug_panel.show()
                # Restore mouse if needed, or keep it as is
            else:
                self.debug_panel.hide()
                print("🙈 UI Hidden. Press 'Tab' to show it again.")