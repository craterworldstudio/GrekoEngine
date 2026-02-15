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


class Skeleton:
    def __init__(self, gltf_json, bin_blob):
        self.nodes = gltf_json["nodes"]
        self.skin = gltf_json["skins"][0]  # VRM uses one skin

        self.joint_nodes = self.skin["joints"]

        # Read inverse bind matrices
        ibm_accessor = self.skin["inverseBindMatrices"]
        ibm_raw = read_accessor(gltf_json, bin_blob, ibm_accessor)

        self.inverse_bind = (
            np.array(ibm_raw, dtype=np.float32)
            .reshape(-1, 4, 4)
            .transpose(0, 2, 1)
        )


        self.local_matrices = []
        self.global_matrices = []
        self.parent_map = {}
        self.joint_index_map = {
            node_index: i for i, node_index in enumerate(self.joint_nodes)
        }

        self._build_hierarchy()
        self._init_local_matrices()

        self.bind_locals = [m.copy() for m in self.local_matrices]


        #for i, node_index in enumerate(self.joint_nodes):
        #    name = self.nodes[node_index].get("name", "Unnamed")
        #    print(i, name)

        

    def _build_hierarchy(self):
        # Build parent lookup
        for parent_index, node in enumerate(self.nodes):
            for child in node.get("children", []):
                self.parent_map[child] = parent_index

    def _init_local_matrices(self):
        for node_index in self.joint_nodes:
            node = self.nodes[node_index]

            t = node.get("translation", [0, 0, 0])
            r = node.get("rotation", [0, 0, 0, 1])
            s = node.get("scale", [1, 1, 1])

            local = compose_matrix(t, r, s)

            self.local_matrices.append(local)
            self.global_matrices.append(np.identity(4, dtype=np.float32))

    def update(self):
        for i, node_index in enumerate(self.joint_nodes):
            parent_node = self.parent_map.get(node_index)

            if parent_node is not None:
                parent_joint_index = self.joint_index_map.get(parent_node)

                if parent_joint_index is not None:
                    self.global_matrices[i] = (
                        self.global_matrices[parent_joint_index] @ self.local_matrices[i]
                    )
                    continue

            # No parent in joint list → root
            self.global_matrices[i] = self.local_matrices[i]

    def get_skinning_buffer(self):
        final = []

        for i in range(len(self.joint_nodes)):
            mat = self.global_matrices[i] @ self.inverse_bind[i]
            final.append(mat.T.flatten())

        return np.concatenate(final).astype(np.float32)
