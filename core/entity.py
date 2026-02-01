import numpy as np

class Entity:
    def __init__(self, name="NewEntity"):
        self.name = name
        
        # FLAG: TRS Data (Transform, Rotation, Scale)
        # We use float32 because it's the native format for GPUs.
        self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.rotation = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32) # Quaternion [x, y, z, w]
        self.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        
        # FLAG: The Mesh Link
        # This will be the ID of the mesh data uploaded to the C++ renderer.
        self.mesh_id = None
        
        # FLAG: The Skeleton
        # A flat array of 128 matrices (16 floats each) for hardware skinning.
        self.joint_matrices = np.eye(4, dtype=np.float32).flatten().tolist() * 128
        
        self.is_active = True

    def set_position(self, x, y, z):
        self.position = np.array([x, y, z], dtype=np.float32)

    def get_model_matrix(self):
        # FLAG: Manual Matrix Math
        # In the next step, we'll add a helper to combine T, R, and S 
        # into a single 4x4 matrix to send to the shader.
        pass

    def update(self, dt):
        """Logic for movement/animations goes here."""
        pass