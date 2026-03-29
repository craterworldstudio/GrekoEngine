import numpy as np
from core.gltf_accessors import read_accessor
#import core.greko_native as gn

class Skeleton:
    def __init__(self, gn, json_data, bin_blob):
        self.gn = gn
        self.nodes = json_data.get("nodes", [])
        skin = json_data.get("skins", [0])[0] if json_data.get("skins") else {}
        self.joint_nodes = skin.get("joints", [])
        self.joint_names = [self.nodes[idx].get("name", f"Joint_{i}") for i, idx in enumerate(self.joint_nodes)]
        
        
        # We will let C++ handle the layout.
        ibm_accessor_idx = skin.get("inverseBindMatrices")
        raw_ibms = read_accessor(json_data, bin_blob, ibm_accessor_idx) # type: ignore
        # Just keep it as a flat array of floats
        self.inverse_bind_matrices = np.array(raw_ibms, dtype=np.float32).reshape(-1, 16)

        rest_positions = []
        rest_rotations = []
        rest_scales = []

        for node_idx in self.joint_nodes:
            node = self.nodes[node_idx]
            # glTF defaults: T=[0,0,0], R=[0,0,0,1], S=[1,1,1]
            rest_positions.append(node.get("translation", [0.0, 0.0, 0.0]))
            rest_rotations.append(node.get("rotation", [0.0, 0.0, 0.0, 1.0])) # X, Y, Z, W
            rest_scales.append(node.get("scale", [1.0, 1.0, 1.0]))

        # 2. Map Parent Indices
        self.parent_map = {}
        for node_idx, node in enumerate(self.nodes):
            for child_idx in node.get("children", []):
                self.parent_map[child_idx] = node_idx

        node_to_joint_idx = {node_idx: i for i, node_idx in enumerate(self.joint_nodes)}
        self.joint_parents = []
        for node_idx in self.joint_nodes:
            parent_node = self.parent_map.get(node_idx)
            self.joint_parents.append(node_to_joint_idx.get(parent_node, -1))

        # 3. SHIP IT TO C++ IMMEDIATELY
        self.gn.setup_cpp_skeleton(
            len(self.joint_nodes),
            self.joint_parents,
            self.inverse_bind_matrices,
            np.array(rest_positions, dtype=np.float32),
            np.array(rest_rotations, dtype=np.float32),
            np.array(rest_scales, dtype=np.float32)
        )        # Finally, trigger a hierarchy update so we aren't at (0,0,0)
        # (Since we have no set_bone_local_rotation for all bones yet, 
        # C++ defaults to identity which is fine for a start)
        print(f"🦴 C++ Skeleton Sync Complete: {len(self.joint_nodes)} bones.")