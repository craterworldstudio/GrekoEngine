import numpy as np
import math

class Transform:
    def __init__(self, camera=False):
        self.owner = None
        self._just_released = False
        self.authority = "PYTHON"

        self.position = np.zeros(3)
        self.rotation = np.zeros(3)  # Euler XYZ (radians)
        self.scale = np.ones(3)
        self.world_matrix = np.identity(4, dtype=np.float32)
        self.camera = camera

        self.was_native = False

                # Camera-specific data (only used if camera=True)
        self.up = np.array([0.0, 1.0, 0.0])
        self.yaw = 0.0
        self.pitch = 0.0
        self.target = np.zeros(3)

    def update(self, dt, context):
        gn = context.gn
        entity_index = context.scene.get_all().index(self.owner)
        auth = gn.get_entity_authority(entity_index)

        if auth == 0:   # AUTH_PYTHON
            self.authority = "PYTHON"
        else:           # AUTH_NATIVE
            self.authority = "NATIVE"

        if self.authority == "NATIVE":
            self._just_released = False
            self.was_native = True
        elif self.authority == "PYTHON" and self.was_native:
            self._just_released = True

        if self.camera:
            self.position = np.array(gn.get_camera_position())
            target = np.array(gn.get_camera_target())

            forward = target - self.position
            forward /= np.linalg.norm(forward)

            right = np.cross(np.array([0.0, 1.0, 0.0]), forward)
            right /= np.linalg.norm(right)

            up = np.cross(forward, right)

            R = np.identity(4, dtype=np.float32)
            R[0, :3] = right
            R[1, :3] = up
            R[2, :3] = forward

            T = np.identity(4, dtype=np.float32)
            T[:3, 3] = self.position

            self.world_matrix = T @ R

            if self.authority == "PYTHON": gn.update_entity_transform(entity_index, self.world_matrix.astype(np.float32).flatten())
            return
        
        if self._just_released:
            pos = np.array(gn.get_entity_position(entity_index))
            rot = np.array(gn.get_entity_rotation(entity_index))  # degrees from ImGui
            scl = np.array(gn.get_entity_scale(entity_index))

            self.position = pos
            self.rotation = np.radians(rot)   # IMPORTANT
            self.scale = scl

            self._just_released = False

        tx, ty, tz = self.position
        rx, ry, rz = self.rotation
        sx, sy, sz = self.scale

        # Basic rotation matrices
        cx, sx_ = math.cos(rx), math.sin(rx)
        cy, sy_ = math.cos(ry), math.sin(ry)
        cz, sz_ = math.cos(rz), math.sin(rz)

        Rx = np.array([[1,0,0,0],
                       [0,cx,-sx_,0],
                       [0,sx_,cx,0],
                       [0,0,0,1]])

        Ry = np.array([[cy,0,sy_,0],
                       [0,1,0,0],
                       [-sy_,0,cy,0],
                       [0,0,0,1]])

        Rz = np.array([[cz,-sz_,0,0],
                       [sz_,cz,0,0],
                       [0,0,1,0],
                       [0,0,0,1]])

        S = np.diag([sx, sy, sz, 1])
        T = np.identity(4)
        T[:3, 3] = [tx, ty, tz]

        self.world_matrix = T @ Rz @ Ry @ Rx @ S 

        #print("Entity:", self.owner.name) #type: ignore
        #print("Position:", self.position) #type: ignore
        #print("Matrix:\n", self.world_matrix)

        

        if self.authority == "PYTHON": gn.update_entity_transform(entity_index, self.world_matrix.astype(np.float32).flatten())