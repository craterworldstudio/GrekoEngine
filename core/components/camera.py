import numpy as np

class CameraComponent:
    def __init__(self):
        # World-space data
        self.position = np.zeros(3)
        self.front = np.array([0.0, 0.0, -1.0])
        self.up = np.array([0.0, 1.0, 0.0])

        # Rotation
        self.yaw = 0.0
        self.pitch = 0.0

        #target
        self.target = np.zeros(3)

    def update(self, dt, context):
        gn = context.gn

        """Pull camera state from C++ layer."""
        self.position = np.array(gn.get_camera_position())
        self.front = np.array(gn.get_camera_front())
        self.yaw = gn.get_camera_yaw()
        self.pitch = gn.get_camera_pitch()
        self.target = np.array(gn.get_camera_target())

    def push_to_native(self, gn):
        """Push ECS camera state back to C++."""
        gn.set_camera_position(
            float(self.position[0]),
            float(self.position[1]),
            float(self.position[2])
        )

        # Optional: if you later expose rotation setter
        # gn.set_camera_rotation(self.yaw, self.pitch)