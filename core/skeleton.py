import numpy as np
from core.gltf_accessors import read_accessor


def compose_matrix(translation, rotation, scale):
    # translation: [x, y, z]
    # rotation: [x, y, z, w] (quaternion)
    # scale: [x, y, z]

    t = np.identity(4, dtype=np.float32)
    t[:3, 3] = translation

    x, y, z, w = rotation
    r = np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w,     2*x*z + 2*y*w,     0],
        [2*x*y + 2*z*w,     1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w,     0],
        [2*x*z - 2*y*w,     2*y*z + 2*x*w,     1 - 2*x*x - 2*y*y, 0],
        [0,                 0,                 0,                 1]
    ], dtype=np.float32)

    s = np.identity(4, dtype=np.float32)
    s[0, 0] = scale[0]
    s[1, 1] = scale[1]
    s[2, 2] = scale[2]

    return t @ r @ s

def decompose_matrix(m):
    translation = m[:3, 3].copy()

    scale = np.array([
        np.linalg.norm(m[:3, 0]),
        np.linalg.norm(m[:3, 1]),
        np.linalg.norm(m[:3, 2])
    ], dtype=np.float32)

    rot = np.zeros((3, 3), dtype=np.float32)
    rot[:, 0] = m[:3, 0] / scale[0]
    rot[:, 1] = m[:3, 1] / scale[1]
    rot[:, 2] = m[:3, 2] / scale[2]

    quat = matrix_to_quaternion(rot)

    return translation, quat, scale


def matrix_to_quaternion(m):
    q = np.empty(4, dtype=np.float32)
    trace = np.trace(m)

    if trace > 0:
        s = np.sqrt(trace + 1.0) * 2
        q[3] = 0.25 * s
        q[0] = (m[2,1] - m[1,2]) / s
        q[1] = (m[0,2] - m[2,0]) / s
        q[2] = (m[1,0] - m[0,1]) / s
    else:
        if m[0,0] > m[1,1] and m[0,0] > m[2,2]:
            s = np.sqrt(1.0 + m[0,0] - m[1,1] - m[2,2]) * 2
            q[3] = (m[2,1] - m[1,2]) / s
            q[0] = 0.25 * s
            q[1] = (m[0,1] + m[1,0]) / s
            q[2] = (m[0,2] + m[2,0]) / s
        elif m[1,1] > m[2,2]:
            s = np.sqrt(1.0 + m[1,1] - m[0,0] - m[2,2]) * 2
            q[3] = (m[0,2] - m[2,0]) / s
            q[0] = (m[0,1] + m[1,0]) / s
            q[1] = 0.25 * s
            q[2] = (m[1,2] + m[2,1]) / s
        else:
            s = np.sqrt(1.0 + m[2,2] - m[0,0] - m[1,1]) * 2
            q[3] = (m[1,0] - m[0,1]) / s
            q[0] = (m[0,2] + m[2,0]) / s
            q[1] = (m[1,2] + m[2,1]) / s
            q[2] = 0.25 * s

    return q



class Skeleton:
    def __init__(self, gltf_json, bin_blob):
        self.nodes = gltf_json["nodes"]
        self.skin = gltf_json["skins"][0]  # VRM uses one skin

        self.joint_nodes = self.skin["joints"]
        self.joint_names = []

        for node_index in self.joint_nodes:
            name = self.nodes[node_index].get("name", "Unnamed")
            self.joint_names.append(name)


        # Read inverse bind matrices
        ibm_accessor = self.skin["inverseBindMatrices"]
        ibm_raw = read_accessor(gltf_json, bin_blob, ibm_accessor)

        self.inverse_bind = (
            np.array(ibm_raw, dtype=np.float32)
            .reshape(-1, 4, 4)
            .transpose(0, 2, 1)
        )


        #self.local_matrices = []
        self.global_matrices = []
        self.parent_map = {}
        self.joint_index_map = {
            node_index: i for i, node_index in enumerate(self.joint_nodes)
        }

        self._build_hierarchy()
        #self._init_local_matrices()
        self.bind_locals = []
        self.global_matrices = []

        for node_index in self.joint_nodes:
            node = self.nodes[node_index]

            t = node.get("translation", [0, 0, 0])
            r = node.get("rotation", [0, 0, 0, 1])
            s = node.get("scale", [1, 1, 1])

            local = compose_matrix(t, r, s)

            self.bind_locals.append(local)
            self.global_matrices.append(np.identity(4, dtype=np.float32))


        #self.bind_locals = [m.copy() for m in self.local_matrices]

        joint_count = len(self.bind_locals)

        self.bind_translation = np.zeros((joint_count, 3), dtype=np.float32)
        self.bind_rotation = np.zeros((joint_count, 4), dtype=np.float32)
        self.bind_scale = np.ones((joint_count, 3), dtype=np.float32)

        self.local_translation = np.zeros((joint_count, 3), dtype=np.float32)
        self.local_rotation = np.zeros((joint_count, 4), dtype=np.float32)
        self.local_scale = np.ones((joint_count, 3), dtype=np.float32)

        # Decompose bind matrices into TRS
        for i, m in enumerate(self.bind_locals):
            t, r, s = decompose_matrix(m)

            self.bind_translation[i] = t
            self.bind_rotation[i] = r
            self.bind_scale[i] = s

            self.local_translation[i] = t
            self.local_rotation[i] = r
            self.local_scale[i] = s



        #for i, node_index in enumerate(self.joint_nodes):
        #    name = self.nodes[node_index].get("name", "Unnamed")
        #    print(i, name)

        

    def _build_hierarchy(self):
        # Build parent lookup
        for parent_index, node in enumerate(self.nodes):
            for child in node.get("children", []):
                self.parent_map[child] = parent_index

    #def _init_local_matrices(self):
    #    for node_index in self.joint_nodes:
    #        node = self.nodes[node_index]
#
    #        t = node.get("translation", [0, 0, 0])
    #        r = node.get("rotation", [0, 0, 0, 1])
    #        s = node.get("scale", [1, 1, 1])
#
    #        local = compose_matrix(t, r, s)
#
    #        self.local_matrices.append(local)
    #        self.global_matrices.append(np.identity(4, dtype=np.float32))

    def update(self):
        for i, node_index in enumerate(self.joint_nodes):
            local = compose_matrix(
                self.local_translation[i],
                self.local_rotation[i],
                self.local_scale[i]
            )

            parent_node = self.parent_map.get(node_index)

            if parent_node is not None:
                parent_joint_index = self.joint_index_map.get(parent_node)

                if parent_joint_index is not None:
                    self.global_matrices[i] = (
                        self.global_matrices[parent_joint_index] @ local
                    )
                    continue

            self.global_matrices[i] = local


    def get_skinning_buffer(self):
        final = []

        for i in range(len(self.joint_nodes)):
            mat = self.global_matrices[i] @ self.inverse_bind[i]
            final.append(mat.T.flatten())

        return np.concatenate(final).astype(np.float32)
