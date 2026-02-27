import numpy as np
import math

class Transform:
    def __init__(self):
        self.position = np.zeros(3)
        self.rotation = np.zeros(3)  # Euler XYZ (radians)
        self.scale = np.ones(3)
        self.world_matrix = np.identity(4, dtype=np.float32)

    def update(self, dt, context):
        gn = context.gn
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