import time

from core.BehaviourBaseClasses import SkeletonBehaviorBase

class LookAt(SkeletonBehaviorBase):
    def __init__(self):
        self.head_index = None
        self.left_eye_index  = None
        self.right_eye_index = None
        self._last_time      = time.perf_counter()
        self.gn = None


    def setup(self, skeleton, gn):
        try:
            #self.head_index = animator.get_bone_index("J_Bip_C_Head")
            self.head_index = skeleton.get_vrm_bone_gpu_index     ("Head")#("J_Bip_C_Head")
            self.left_eye_index = skeleton.get_vrm_bone_gpu_index ("leftEye")#("J_Adj_L_FaceEye")
            self.right_eye_index = skeleton.get_vrm_bone_gpu_index("rightEye")#("J_Adj_R_FaceEye")
            #for i, name in enumerate(skeleton.joint_names):
            #   name = skeleton.nodes[node_index].get("name", "")
            #   if name == "J_Bip_C_Head":
            #       self.head_index = i
            #       print("Found Head at index:", i, "| Name:", name)
            #       break
        except ValueError as e:
            print(f"⚠ LookAt setup failed — bone not found: {e}")


        if self.head_index is None:
            print("⚠ Head bone not found — LookAt disabled ❌")

        if (self.left_eye_index or self.right_eye_index) is None:
            print("⚠ Eye bones not found — LookAt disabled ❌")

        gn.init_lookat(
            #self.head_index,
            self.left_eye_index,
            self.right_eye_index
        )


    def update(self, gn, animator, target_index):
        if (self.head_index or self.right_eye_index or self.left_eye_index) is None:
            return

        if target_index is None or target_index < 0:
            return
        
        now = time.perf_counter()
        dt  = min(now - self._last_time, 0.05)  # cap at 50ms to survive hitches
        self._last_time = now

        #print("Target index:", target_index)
        gn.apply_look_at(
            self.head_index,
            self.left_eye_index,
            self.right_eye_index,
            target_index,#, target_index[0], target_index[1], target_index[2]
            dt
            )
