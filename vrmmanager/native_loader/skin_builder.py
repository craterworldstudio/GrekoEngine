from panda3d.core import NodePath, LMatrix4f, LQuaternionf

def get_node_transform(node_json):
    """Extract local transform from glTF node"""
    mat = LMatrix4f.ident_mat()

    if "translation" in node_json:
        t = node_json["translation"]
        mat = mat * LMatrix4f.translate_mat(t[0], t[1], t[2])

    if "rotation" in node_json:
        r = node_json["rotation"]
        quat = LQuaternionf(r[3], r[0], r[1], r[2])
        rot_mat = LMatrix4f()
        quat.extract_to_matrix(rot_mat)
        mat = mat * rot_mat

    if "scale" in node_json:
        s = node_json["scale"]
        mat = mat * LMatrix4f.scale_mat(s[0], s[1], s[2])

    return mat


def build_vrm_skeleton(gltf_json, bin_blob, skin_index, read_accessor_func):
    """
    Build skeleton as NodePath hierarchy (NO Character/CharacterJoint)
    Returns: (root_np, joints_list, ibms)
    """
    skin_data = gltf_json["skins"][skin_index]
    joint_node_indices = skin_data["joints"]
    
    # Read IBMs from glTF (we'll use these for skinning)
    ibm_accessor_idx = skin_data.get("inverseBindMatrices")
    if ibm_accessor_idx is not None:
        ibm_data = read_accessor_func(gltf_json, bin_blob, ibm_accessor_idx)
    else:
        # No IBMs - create identity matrices
        ibm_data = [(1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1)] * len(joint_node_indices)
    
    # Convert IBMs to LMatrix4f
    ibms = []
    for m in ibm_data:
        ibm_mat = LMatrix4f(
            m[0], m[4], m[8], m[12],
            m[1], m[5], m[9], m[13],
            m[2], m[6], m[10], m[14],
            m[3], m[7], m[11], m[15]
        )
        ibms.append(ibm_mat)
    
    # Build hierarchy map
    parent_map = {}
    for node_idx in joint_node_indices:
        node_json = gltf_json["nodes"][node_idx]
        for child_idx in node_json.get("children", []):
            if child_idx in joint_node_indices:
                parent_map[child_idx] = node_idx
    
    joints_map = {}
    joints_list = []  # Ordered list matching glTF skin
    
    # Create root NodePath
    root_np = NodePath("Skeleton")
    
    def create_joint_recursive(node_idx):
        if node_idx in joints_map:
            return joints_map[node_idx]
        
        node_json = gltf_json["nodes"][node_idx]
        joint_name = node_json.get("name", f"Joint_{node_idx}")
        local_transform = get_node_transform(node_json)
        
        # Find parent
        parent_idx = parent_map.get(node_idx)
        if parent_idx is not None:
            parent_np = create_joint_recursive(parent_idx)
        else:
            parent_np = root_np
        
        # Create joint as simple NodePath
        joint_np = parent_np.attach_new_node(joint_name)
        joint_np.set_mat(local_transform)
        
        joints_map[node_idx] = joint_np
        return joint_np
    
    # Create all joints
    for node_idx in joint_node_indices:
        joint_np = create_joint_recursive(node_idx)
        joints_list.append(joint_np)
    
    return root_np, joints_list, ibms