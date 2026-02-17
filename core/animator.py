from unicodedata import name
import numpy as np
import math

def quaternion_from_axis_angle(axis, angle):
    axis = axis / np.linalg.norm(axis)
    s = math.sin(angle / 2.0)
    x, y, z = axis * s
    w = math.cos(angle / 2.0)
    return np.array([x, y, z, w], dtype=np.float32)

def ease_in_out(t):
    return t * t * (3 - 2 * t)


class Animator:
    def __init__(self, skeleton):
        self.skeleton = skeleton
        self.time = 0.0
        self.active_clip = None
        self.clip_time = 0.0


        # cache bone indices by name
        self.bones = {}
        for i, node_index in enumerate(skeleton.joint_nodes):
            name = skeleton.nodes[node_index].get("name", "")
            self.bones[name] = i

    def update(self, dt):
        self.time += dt

        if self.active_clip == "hi":
            self.play_hi(dt)


    def rotate_bone(self, bone_name, axis, angle):
        if bone_name not in self.bones:
            return

        idx = self.bones[bone_name]
        quat = quaternion_from_axis_angle(axis, angle)
        self.skeleton.local_rotation[idx] = quat
        
    def play_clip(self, name):
        self.active_clip = name
        self.clip_time = 0.0

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


