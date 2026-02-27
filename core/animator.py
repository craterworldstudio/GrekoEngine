from unicodedata import name
import numpy as np
import math
import core.greko_native as gn

def quaternion_from_axis_angle(axis, angle):
    norm = np.linalg.norm(axis)

    if norm < 1e-8:
        return np.array([0, 0, 0, 1], dtype=np.float32)

    axis = axis / norm

    s = math.sin(angle / 2.0)
    x, y, z = axis * s
    w = math.cos(angle / 2.0)

    q = np.array([x, y, z, w], dtype=np.float32)

    # Normalize quaternion to prevent drift
    q /= np.linalg.norm(q)

    return q


def ease_in_out(t):
    return t * t * (3 - 2 * t)


class Animator:
    def __init__(self, skeleton):
        self.skeleton = skeleton
        self.time = 0.0
        self.active_clip = None
        self.clip_time = 0.0

        self.pose_buffer = {}

        # cache bone indices by name
        self.bones = {}
        for i, node_index in enumerate(skeleton.joint_nodes):
            name = skeleton.nodes[node_index].get("name", "")
            self.bones[name] = i

    def commit_pose(self):
        for idx, quat in self.pose_buffer.items():
            gn.set_bone_local_rotation(
                idx,
                float(quat[0]),
                float(quat[1]),
                float(quat[2]),
                float(quat[3])
            )
        self.pose_buffer.clear()

    def update(self, dt, context):
        self.time += dt
        gn = context.gn
        #if self.active_clip == "hi":
        #    self.play_hi(dt)
        gn.reset_to_bind_pose()

        self.commit_pose()


    def rotate_bone(self, bone_name, axis, angle):
        if bone_name not in self.bones:
            return

        idx = self.bones[bone_name]
        quat = quaternion_from_axis_angle(axis, angle)
        
        # FLAG: Native Call
        # Instead of storing it in a Python list, send it straight to C++
        # We pass (index, x, y, z, w)
        self.pose_buffer[idx] = quat
        #gn.set_bone_local_rotation(idx, float(quat[0]), float(quat[1]), float(quat[2]), float(quat[3]))
        
    def play_clip(self, name):
        self.active_clip = name
        self.clip_time = 0.0

    #Test for Arm Rotation and SKeleton System
    def play_hi(self, dt):
        self.clip_time += dt

        raise_duration = 0.5
        wave_duration = 1.0
        lower_duration = 0.5

        total_duration = raise_duration + wave_duration + lower_duration

        if self.clip_time > total_duration:
            self.active_clip = None
            return

        upper_arm = "J_Bip_R_UpperArm"
        lower_arm = "J_Bip_R_LowerArm"
        shoulder  = "J_Bip_R_Shoulder"
        hand      = "J_Bip_R_Hand"

        axis_x = np.array([1,0,0], dtype=np.float32)
        axis_y = np.array([0,1,0], dtype=np.float32)
        axis_z = np.array([0,0,1], dtype=np.float32)

        # -------- Phase 1: Raise to shoulder level --------
        if self.clip_time < raise_duration:
            t = self.clip_time / raise_duration
            t = ease_in_out(t)

            # Lift arm forward (not sideways)
            self.rotate_bone(upper_arm, axis_z, -math.radians(45) * t)

            # Slight shoulder assist
            self.rotate_bone(shoulder, axis_x, -math.radians(15) * t)

            # Bend elbow slightly
            self.rotate_bone(lower_arm, axis_z, -math.radians(40) * t)

            # Rotate palm outward toward camera
            self.rotate_bone(hand, axis_y, math.radians(40) * t)

        # -------- Phase 2: Wave --------
        elif self.clip_time < raise_duration + wave_duration:
            wave_t = self.clip_time - raise_duration

            # Hold raised pose
            self.rotate_bone(upper_arm, axis_z, -math.radians(45))
            self.rotate_bone(shoulder, axis_x, -math.radians(15))
            self.rotate_bone(lower_arm, axis_z, -math.radians(40))
            self.rotate_bone(hand, axis_y, math.radians(40))

            # Small wrist wave
            wave = math.sin(wave_t * 8.0) * math.radians(15)
            self.rotate_bone(hand, axis_x, wave)

        # -------- Phase 3: Lower --------
        else:
            t = (self.clip_time - raise_duration - wave_duration) / lower_duration
            t = ease_in_out(t)

            self.rotate_bone(upper_arm, axis_z, -math.radians(45) * (1 - t))
            self.rotate_bone(shoulder, axis_x, -math.radians(15) * (1 - t))
            self.rotate_bone(lower_arm, axis_z, -math.radians(40) * (1 - t))
            self.rotate_bone(hand, axis_y, math.radians(40) * (1 - t))


