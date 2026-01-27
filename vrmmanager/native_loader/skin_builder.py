from panda3d.core import Character, CharacterJoint, Mat4

def build_vrm_skeleton(gltf_json, bin_blob, skin_index, read_accessor_func):
    skin_data = gltf_json["skins"][skin_index]
    joint_node_indices = skin_data["joints"]
    ibm_data = read_accessor_func(gltf_json, bin_blob, skin_data["inverseBindMatrices"])
    
    char_node = Character(skin_data.get("name", "Skeleton"))
    bundle = char_node.get_bundle(0) 
    
    # 1. Map out the hierarchy first (Node Index -> Parent Node Index)
    parent_map = {}
    for node_idx in joint_node_indices:
        node_json = gltf_json["nodes"][node_idx]
        for child_idx in node_json.get("children", []):
            if child_idx in joint_node_indices:
                parent_map[child_idx] = node_idx

    joints_map = {}

    # 2. Recursive function to build joints in the correct order
    def create_joint_recursive(node_idx):
        if node_idx in joints_map:
            return joints_map[node_idx]

        node_json = gltf_json["nodes"][node_idx]
        joint_name = node_json.get("name", f"Joint_{node_idx}")
        
        # Get IBM
        idx_in_skin = joint_node_indices.index(node_idx)
        ibm_mat = Mat4(*ibm_data[idx_in_skin])
        
        # Find Parent Joint
        parent_idx = parent_map.get(node_idx)
        if parent_idx is not None:
            # Recursively ensure parent is created first
            parent_joint = create_joint_recursive(parent_idx)
        else:
            # This is a Root (Hips), its parent is the bundle itself
            parent_joint = bundle

        # THE CONSTRUCTOR FLAG:
        # Argument 3 (Parent) is now a verified PartGroup (either another Joint or the Bundle)
        joint = CharacterJoint(char_node, bundle, parent_joint, joint_name, ibm_mat)
        joints_map[node_idx] = joint
        return joint

    # 3. Start the build for every joint
    for node_idx in joint_node_indices:
        create_joint_recursive(node_idx)

    return char_node, joints_map, parent_map