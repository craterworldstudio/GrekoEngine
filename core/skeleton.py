import numpy as np
from core.gltf_accessors import read_accessor
#import core.greko_native as gn

class Skeleton:
    def __init__(self, gn, json_data, bin_blob, vrm_data=None):
        self.gn = gn
        self.nodes = json_data.get("nodes", [])
        self.json = json_data
        #skin = json_data.get("skins", [0])[0] if json_data.get("skins") else {}
        skins = json_data.get("skins", [])
        skin = skins[0] if skins else {}
        self.joint_nodes = skin.get("joints", [])
        self.joint_names = [self.nodes[idx].get("name", f"Joint_{i}") for i, idx in enumerate(self.joint_nodes)]
        self.vrm_data = vrm_data

        self.humanoid_bones = {}

        if vrm_data:
            humanoid = vrm_data.get("humanoid", {})
            human_bones = humanoid.get("humanBones", [])

            # VRM1 format
            if isinstance(human_bones, dict):
            
                for bone_name, bone_data in human_bones.items():
                    node = bone_data.get("node")

                    if node is not None:
                        self.humanoid_bones[bone_name] = node

            # VRM0 format
            elif isinstance(human_bones, list):
            
                for bone in human_bones:
                    bone_name = bone.get("bone")
                    node = bone.get("node")

                    if bone_name and node is not None:
                        self.humanoid_bones[bone_name] = node
        
        # We will let C++ handle the layout.
        ibm_accessor_idx = skin.get("inverseBindMatrices")
        #raw_ibms = read_accessor(json_data, bin_blob, ibm_accessor_idx) # type: ignore
        ## Just keep it as a flat array of floats
        #self.inverse_bind_matrices = np.array(raw_ibms, dtype=np.float32).reshape(-1, 16)

        if ibm_accessor_idx is not None:
            raw_ibms = read_accessor(json_data, bin_blob, ibm_accessor_idx)

            self.inverse_bind_matrices = (
                np.array(raw_ibms, dtype=np.float32)
                .reshape(-1, 16)
            )

        else:
            print("⚠️ Missing inverseBindMatrices")

            self.inverse_bind_matrices = np.array([
                np.identity(4, dtype=np.float32).flatten()
                for _ in self.joint_nodes
            ], dtype=np.float32)

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

        #node_to_joint_idx = {node_idx: i for i, node_idx in enumerate(self.joint_nodes)}
        self.node_to_joint_idx = { node_idx: i for i, node_idx in enumerate(self.joint_nodes)}
        
        self.joint_parents = []
        for node_idx in self.joint_nodes:
            parent_node = self.parent_map.get(node_idx)
            self.joint_parents.append(self.node_to_joint_idx.get(parent_node, -1))

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

    def get_vrm_bone_gpu_index(self, vrm_bone_name: str) -> int:
        """
        Robust bone index lookup that smoothly handles VRM0, VRM1, 
        and raw VRoid structural naming conventions.
        """
        # Clean the search term
        bone_query = vrm_bone_name.strip()
        bone_query_lower = bone_query.lower()

        # =========================================================================
        # STRATEGY 1: CACHED METADATA DICTIONARY LOOKUP
        # =========================================================================
        # Check standard lookup variants in your pre-parsed dictionary
        for variant in [bone_query, bone_query_lower, bone_query.capitalize()]:
            node_idx = self.humanoid_bones.get(variant)
            if node_idx is not None:
                gpu_idx = self.node_to_joint_idx.get(int(node_idx), -1)
                if gpu_idx != -1:
                    return gpu_idx

        # =========================================================================
        # STRATEGY 2: INTELLIGENT FUZZY KEYWORD FALLBACK (For VRoid Naming Layouts)
        # =========================================================================
        # If metadata maps failed or are absent, inspect the actual string labels
        for idx, joint_name in enumerate(self.joint_names):
            name_lower = joint_name.lower()
            #print(name_lower, bone_query_lower in name_lower)
            # Special Rule: Head Matching
            if bone_query_lower == "head":
                if "head" in name_lower and "neck" not in name_lower:
                    return idx
                    
            # Special Rule: Left Eye Matching
            elif bone_query_lower == "lefteye":
                if ("eye" in name_lower or "faceeye" in name_lower) and ("_l_" in name_lower or "left" in name_lower):
                    return idx
                    
            # Special Rule: Right Eye Matching
            elif bone_query_lower == "righteye":
                if ("eye" in name_lower or "faceeye" in name_lower) and ("_r_" in name_lower or "right" in name_lower):
                    return idx

            # General catch-all for other structural joints (hips, spine, chest, etc.)
            elif bone_query_lower in name_lower:
                return idx

        # =========================================================================
        # STRATEGY 3: EXACT STRING FALLBACK
        # =========================================================================
        for idx, joint_name in enumerate(self.joint_names):
            if joint_name.lower() == bone_query_lower:
                return idx

        print(f"❌ [Skeleton] Critical Error: Unified bone lookup failed for '{vrm_bone_name}'")
        return -1