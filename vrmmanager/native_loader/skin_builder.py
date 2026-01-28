"""from panda3d.core import Character, CharacterJoint, Mat4

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

	return char_node, joints_map, parent_map"""

from panda3d.core import Character, CharacterJoint, LMatrix4f, LVecBase3f, LQuaternionf

def get_node_transform(node_json):
	"""Extract the local transform matrix from a glTF node.
	
	glTF nodes can specify transforms in two ways:
	1. As a 4x4 matrix
	2. As separate translation, rotation (quaternion), and scale (TRS)
	"""
	# Check if node has a matrix property
	
	
	if "matrix" in node_json:
		# Matrix is provided directly (column-major order in glTF)
		m = node_json["matrix"]
		# glTF uses column-major, Panda3D uses row-major
		return LMatrix4f(
			m[0], m[4], m[8], m[12],
			m[1], m[5], m[9], m[13],
			m[2], m[6], m[10], m[14],
			m[3], m[7], m[11], m[15]
		)
	
	# Build from TRS components
	# LMatrix4f does not have 'set_identity'. Use ident_mat() to start fresh.
	mat = LMatrix4f.ident_mat()
	
	# Translation
	if "translation" in node_json:
		t = node_json["translation"]
		# Use the static constructor for a translation matrix
		mat = LMatrix4f.translate_mat(t[0], t[1], t[2]) * mat
	
	# Rotation (quaternion: x, y, z, w in glTF)
	if "rotation" in node_json:
		r = node_json["rotation"]
		quat = LQuaternionf(r[3], r[0], r[1], r[2]) # w, x, y, z
		rot_mat = LMatrix4f()
		quat.extract_to_matrix(rot_mat)
		mat = rot_mat * mat
	
	# Scale
	if "scale" in node_json:
		s = node_json["scale"]
		mat = LMatrix4f.scale_mat(s[0], s[1], s[2]) * mat
	
	return mat


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
	ibm_map = {}  # Store IBMs separately

	# 2. Recursive function to build joints in the correct order
	def create_joint_recursive(node_idx):
		if node_idx in joints_map:
			return joints_map[node_idx]

		node_json = gltf_json["nodes"][node_idx]
		joint_name = node_json.get("name", f"Joint_{node_idx}")
		
		# THE FIX: Get the LOCAL transform from the glTF node
		# This is the bind pose local transform, NOT the inverse bind matrix
		local_transform = get_node_transform(node_json)
		
		# Store the inverse bind matrix separately
		idx_in_skin = joint_node_indices.index(node_idx)
		m = ibm_data[idx_in_skin]
		ibm_mat = LMatrix4f(
            m[0], m[4], m[8], m[12],
            m[1], m[5], m[9], m[13],
            m[2], m[6], m[10], m[14],
            m[3], m[7], m[11], m[15]
        )
		ibm_map[node_idx] = ibm_mat
		
		# Find Parent Joint
		parent_idx = parent_map.get(node_idx)
		if parent_idx is not None:
			# Recursively ensure parent is created first
			parent_joint = create_joint_recursive(parent_idx)
		else:
			# This is a Root (Hips), its parent is the bundle itself
			parent_joint = bundle

		# THE CRITICAL FIX:
		# Use the LOCAL transform as the default_value, NOT the inverse bind matrix!
		# Panda3D's hardware skinning will compute:
		#   jointMatrix = currentJointGlobalTransform * inverseBindMatrix
		# The IBM gets applied by JointVertexTransform internally
		joint = CharacterJoint(char_node, bundle, parent_joint, joint_name, local_transform)
		
		joints_map[node_idx] = joint
		# 3. Store the IBM (Inverse Bind Matrix) in a map 
		# We will use this in the next step to "glue" the mesh.
		idx_in_skin = joint_node_indices.index(node_idx)
		ibm_mat = LMatrix4f(*ibm_data[idx_in_skin])
		ibm_map[node_idx] = ibm_mat

		return joint

	# 3. Start the build for every joint
	for node_idx in joint_node_indices:
		create_joint_recursive(node_idx)

	return char_node, joints_map, parent_map