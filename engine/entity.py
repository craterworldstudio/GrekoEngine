from panda3d.core import NodePath, LPoint3f

class Entity:
    def __init__(self, name="NewEntity"):
        self.name = name
        
        # --- THE BODY FLAG ---
        # We replace manual x, y, z variables with a single NodePath.
        # This is the "bridge" to the 3D world.
        self.model: NodePath | None = None
        
        # --- STATE FLAGS ---
        self.is_active = True    
        self.is_started = False   
        self.show_debug = False   

    def start(self):
        """Called once when the entity enters the scene."""
        self.is_started = True
        print(f"Entity {self.name} started.")

    def update(self, dt: float):
        """Called every frame."""
        pass

    # --- TRANSFORM HELPERS ---
    # Instead of variables, we use methods that talk to the GPU directly.
    
    def set_position(self, x, y, z):
        if self.model:
            self.model.set_pos(x, y, z)

    def get_position(self) -> LPoint3f:
        return self.model.get_pos() if self.model else LPoint3f(0,0,0)

    def destroy(self):
        """The Cleanup Flag."""
        self.is_active = False
        if self.model:
            self.model.remove_node() # Removes it from the 3D world entirely