from core.behaviours_manager import SkeletonBehaviorBase

class LookAt(SkeletonBehaviorBase):
    def __init__(self):
        self.head_index = None

    def setup(self, skeleton):
        #self.head_index = animator.get_bone_index("J_Bip_C_Head")
        self.head_index = skeleton.joint_names.index("J_Bip_C_Head")
        #for i, name in enumerate(skeleton.joint_names):
        #   name = skeleton.nodes[node_index].get("name", "")
        #   if name == "J_Bip_C_Head":
        #       self.head_index = i
        #       print("Found Head at index:", i, "| Name:", name)
        #       break

        if self.head_index is None:
            print("⚠ Head bone not found — LookAt disabled ❌")

    def update(self, gn, animator, target):
        if self.head_index is None:
            return

        gn.apply_look_at(
            self.head_index,
            target[0], target[1], target[2]
        )