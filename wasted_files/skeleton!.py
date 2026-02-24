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
        self._build_update_order()

        #self._init_local_matrices()

        # Cache bind-pose local transforms for every node in the GLTF graph.
        # This allows joint updates to walk through non-joint parents correctly.
        self.node_bind_locals = []
        for node in self.nodes:
            t = node.get("translation", [0, 0, 0])
            r = node.get("rotation", [0, 0, 0, 1])
            s = node.get("scale", [1, 1, 1])
            self.node_bind_locals.append(compose_matrix(t, r, s))
            
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

        self.override_rotation = [None] * joint_count
        self.override_translation = [None] * joint_count

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

    def _build_update_order(self):
        children = {i: [] for i in range(len(self.joint_nodes))}

        for joint_i, node_index in enumerate(self.joint_nodes):
            parent_node = self.parent_map.get(node_index)
            parent_joint = self.joint_index_map.get(parent_node)

            if parent_joint is not None:
                children[parent_joint].append(joint_i)

        order = []

        def dfs(j):
            order.append(j)
            for c in children[j]:
                dfs(c)

        # start from roots
        for joint_i, node_index in enumerate(self.joint_nodes):
            parent_node = self.parent_map.get(node_index)
            if self.joint_index_map.get(parent_node) is None:
                dfs(joint_i)

        self.update_order = order

        

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

    def get_skinning_buffer(self):
        final = []

        for i in range(len(self.joint_nodes)):
            mat = self.global_matrices[i] @ self.inverse_bind[i]
            final.append(mat.T.flatten())

        return np.concatenate(final).astype(np.float32)

    def update(self):
        #joint_local_matrices = [
        #        compose_matrix(
        #            self.local_translation[i],
        #            self.local_rotation[i],
        #            self.local_scale[i]
        #        )
        #        for i in range(len(self.joint_nodes))
        #    ]
        joint_local_matrices = []

        for i in range(len(self.joint_nodes)):
        
            t = self.override_translation[i] if self.override_translation[i] is not None else self.local_translation[i]
            r = self.override_rotation[i] if self.override_rotation[i] is not None else self.local_rotation[i]

            if np.isnan(r).any(): # type: ignore
                print("NaN rotation at joint", i)
                r = np.array([0,0,0,1], dtype=np.float32)
                        

            joint_local_matrices.append(
                compose_matrix(
                    t,
                    r,
                    self.local_scale[i]
                )
            )

        print("Local matrix head:\n", joint_local_matrices[18])
        print("Override[18]:", self.override_rotation[18])
        print("Local[18]:", self.local_rotation[18])
        
        
        for i in self.update_order:
            node_index = self.joint_nodes[i]
            parent_node = self.parent_map.get(node_index)
            parent_joint = self.joint_index_map.get(parent_node)

            if parent_joint is not None:
                self.global_matrices[i] = (
                    self.global_matrices[parent_joint] @ joint_local_matrices[i]
                )
            else:
                self.global_matrices[i] = joint_local_matrices[i]

        head_index = 18  # or whatever index your head is
        child_index = 19 # pick one child bone index manually
        
        print("Head Global:\n", self.global_matrices[head_index])
        print("Child Global:\n", self.global_matrices[child_index])
        print("----")
        

'''
        for i, node_index in enumerate(self.joint_nodes):
            #local = compose_matrix(
            joint_local_matrices = [
                compose_matrix(

                self.local_translation[i],
                self.local_rotation[i],
                self.local_scale[i]
            ) for i in range(len(self.joint_nodes))
            ]

            node_globals = {}

            #parent_node = self.parent_map.get(node_index)
            def resolve_node_global(node_index):
                cached = node_globals.get(node_index)
                if cached is not None:
                    return cached
                
                joint_index = self.joint_index_map.get(node_index)
                if joint_index is not None:
                    local = joint_local_matrices[joint_index]
                else:
                    local = self.node_bind_locals[node_index]

                parent_index = self.parent_map.get(node_index)
                if parent_index is None:
                    global_matrix = local
                else:
                    global_matrix = resolve_node_global(parent_index) @ local

                node_globals[node_index] = global_matrix
                return global_matrix

            for i, node_index in enumerate(self.joint_nodes):
                self.global_matrices[i] = resolve_node_global(node_index)



            #if parent_node is not None:
            #    parent_joint_index = self.joint_index_map.get(parent_node)

            #    if parent_joint_index is not None:
            #        self.global_matrices[i] = (
            #            self.global_matrices[parent_joint_index] @ local
            #        )
            #        continue

            #self.global_matrices[i] = local

    '''
