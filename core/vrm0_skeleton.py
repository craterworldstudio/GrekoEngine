import numpy as np

from core.vrm0_accessor import read_accessor


MAX_GPU_JOINTS = 1000


class VRM0Skeleton:
    def __init__(self, gn, gltf_json, bin_blob):
        self.gn = gn
        self.json = gltf_json
        self.nodes = gltf_json.get("nodes", [])
        self.skins = gltf_json.get("skins", [])

        print(
            f"[VRM0Skeleton] Found {len(self.skins)} skin(s); "
            "building unified GPU joint layout"
        )

        self.skin_remaps = []
        self.node_to_joint = {}
        self.joint_nodes = []

        self._build_unified_joint_layout()

        self.joint_count = len(self.joint_nodes)
        if self.joint_count > MAX_GPU_JOINTS:
            raise ValueError(
                f"VRM0 skeleton has {self.joint_count} unique joints, "
                f"but the GPU layout supports {MAX_GPU_JOINTS}."
            )

        self.joint_names = [
            self.nodes[node_idx].get("name", f"joint_{node_idx}")
            if 0 <= node_idx < len(self.nodes)
            else f"joint_{node_idx}"
            for node_idx in self.joint_nodes
        ]

        rest_positions, rest_rotations, rest_scales = self._read_rest_pose()
        self.inverse_bind_matrices = self._build_inverse_bind_matrices(
            gltf_json,
            bin_blob,
        )
        self.joint_parents = self._build_joint_parent_indices()

        self.gn.setup_cpp_skeleton(
            self.joint_count,
            self.joint_parents,
            self.inverse_bind_matrices,
            np.asarray(rest_positions, dtype=np.float32),
            np.asarray(rest_rotations, dtype=np.float32),
            np.asarray(rest_scales, dtype=np.float32),
        )

        print(
            f"[VRM0Skeleton] C++ sync complete: "
            f"{self.joint_count} unified joints."
        )

    def _build_unified_joint_layout(self):
        for skin_index, skin in enumerate(self.skins):
            remap = {}
            skin_joints = skin.get("joints", [])

            for skin_local_index, node_index in enumerate(skin_joints):
                node_index = int(node_index)

                if node_index not in self.node_to_joint:
                    self.node_to_joint[node_index] = len(self.joint_nodes)
                    self.joint_nodes.append(node_index)

                remap[skin_local_index] = self.node_to_joint[node_index]

            self.skin_remaps.append(remap)
            print(
                f"[VRM0Skeleton] Skin {skin_index}: "
                f"{len(skin_joints)} local joints, {len(remap)} remap entries."
            )

    def _read_rest_pose(self):
        rest_positions = []
        rest_rotations = []
        rest_scales = []

        for node_index in self.joint_nodes:
            node = self.nodes[node_index] if 0 <= node_index < len(self.nodes) else {}

            rest_positions.append(node.get("translation", [0.0, 0.0, 0.0]))
            rest_rotations.append(node.get("rotation", [0.0, 0.0, 0.0, 1.0]))
            rest_scales.append(node.get("scale", [1.0, 1.0, 1.0]))

        return rest_positions, rest_rotations, rest_scales

    def _build_inverse_bind_matrices(self, gltf_json, bin_blob):
        identity = np.eye(4, dtype=np.float32).reshape(16)
        master_ibms = np.tile(identity, (len(self.joint_nodes), 1))

        assigned_by_skin = np.full(len(self.joint_nodes), -1, dtype=np.int32)

        for skin_index, skin in enumerate(self.skins):
            ibm_accessor = skin.get("inverseBindMatrices")
            if ibm_accessor is None:
                continue

            raw_ibms = np.asarray(
                read_accessor(gltf_json, bin_blob, ibm_accessor),
                dtype=np.float32,
            ).reshape(-1, 16)

            remap = self.skin_remaps[skin_index]
            skin_joint_count = len(skin.get("joints", []))
            usable_count = min(skin_joint_count, raw_ibms.shape[0])

            if usable_count != skin_joint_count:
                print(
                    f"[VRM0Skeleton] Skin {skin_index}: IBM count "
                    f"{raw_ibms.shape[0]} does not match joint count "
                    f"{skin_joint_count}; using {usable_count}."
                )

            for skin_local_index in range(usable_count):
                master_index = remap[skin_local_index]
                previous_skin = assigned_by_skin[master_index]

                # If the same node appears in more than one skin, the large
                # body skin's bind matrix is authoritative for this asset.
                should_write = previous_skin == -1 or skin_index == 1
                if should_write:
                    master_ibms[master_index] = raw_ibms[skin_local_index]
                    assigned_by_skin[master_index] = skin_index

        assigned_count = int(np.count_nonzero(assigned_by_skin >= 0))
        print(
            f"[VRM0Skeleton] Harmonized {assigned_count}/"
            f"{len(self.joint_nodes)} inverse bind matrices."
        )

        return np.asarray(master_ibms, dtype=np.float32)

    def _build_joint_parent_indices(self):
        parent_by_node = {}
        for node_index, node in enumerate(self.nodes):
            for child_index in node.get("children", []):
                parent_by_node[int(child_index)] = node_index

        joint_parents = []
        for node_index in self.joint_nodes:
            parent_node = parent_by_node.get(node_index)
            joint_parents.append(self.node_to_joint.get(parent_node, -1))

        return joint_parents

    def get_skin_remap(self, skin_index: int) -> dict:
        if 0 <= skin_index < len(self.skin_remaps):
            return self.skin_remaps[skin_index]

        if self.skin_remaps:
            print(
                f"[VRM0Skeleton] Skin {skin_index} missing; "
                "falling back to skin 0 remap."
            )
            return self.skin_remaps[0]

        return {}

    def get_vrm_bone_gpu_index(self, vrm_bone_name: str) -> int:
        try:
            vrm_ext = self.json.get("extensions", {}).get("VRM", {})
            human_bones = vrm_ext.get("humanoid", {}).get("humanBones", [])
            for bone_entry in human_bones:
                if bone_entry.get("bone") == vrm_bone_name:
                    node_index = bone_entry.get("node")
                    return self.node_to_joint.get(node_index, -1)
        except Exception as exc:
            print(f"Error parsing bone index for {vrm_bone_name}: {exc}")

        return -1
