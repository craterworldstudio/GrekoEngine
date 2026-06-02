import numpy as np

from core.mesh_data import extract_base_color_texture
from core.vrm0_accessor import read_accessor


def _read_attribute(gltf_json, bin_blob, attrs, name, dtype, fallback_shape=None):
    accessor_id = attrs.get(name)
    if accessor_id is None:
        if fallback_shape is None:
            raise KeyError(f"Missing required vertex attribute: {name}")
        return np.zeros(fallback_shape, dtype=dtype)

    return np.asarray(read_accessor(gltf_json, bin_blob, accessor_id), dtype=dtype)


def package_vrm0_mesh(
    gltf_json,
    bin_blob,
    primitive_data,
    mesh_data,
    skeleton,
    skin_index,
):
    attrs = primitive_data["attributes"]

    pos = _read_attribute(gltf_json, bin_blob, attrs, "POSITION", np.float32)
    vertex_count = pos.shape[0]

    normals = _read_attribute(
        gltf_json,
        bin_blob,
        attrs,
        "NORMAL",
        np.float32,
        fallback_shape=(vertex_count, 3),
    )
    uv = _read_attribute(
        gltf_json,
        bin_blob,
        attrs,
        "TEXCOORD_0",
        np.float32,
        fallback_shape=(vertex_count, 2),
    )
    weights = _read_attribute(
        gltf_json,
        bin_blob,
        attrs,
        "WEIGHTS_0",
        np.float32,
        fallback_shape=(vertex_count, 4),
    )
    joints_raw = _read_attribute(
        gltf_json,
        bin_blob,
        attrs,
        "JOINTS_0",
        np.uint32,
        fallback_shape=(vertex_count, 4),
    )

    if "indices" in primitive_data:
        indices = np.asarray(
            read_accessor(gltf_json, bin_blob, primitive_data["indices"]),
            dtype=np.uint32,
        )
    else:
        indices = np.arange(vertex_count, dtype=np.uint32)

    # glTF JOINTS_0 values are indices into the mesh node's skin, not into any
    # global skeleton array. Translate them here, once, before upload.
    remap = skeleton.get_skin_remap(skin_index)
    max_remap_index = max(remap.keys()) if remap else 0
    max_raw_index = int(joints_raw.max()) if joints_raw.size else 0
    lookup_size = max(max_remap_index, max_raw_index) + 1

    lookup_table = np.zeros(lookup_size, dtype=np.uint32)
    for skin_local_index, master_index in remap.items():
        lookup_table[int(skin_local_index)] = np.uint32(master_index)

    joints = lookup_table[joints_raw.ravel()].reshape(joints_raw.shape) # type: ignore

    invalid_joints = joints >= skeleton.joint_count
    if np.any(invalid_joints):
        bad_count = int(np.count_nonzero(invalid_joints))
        print(
            f"[VRM0Mesh] Skin {skin_index}: clamped {bad_count} "
            "joint assignments outside unified skeleton bounds."
        )
        joints[invalid_joints] = 0

    weight_sums = np.sum(weights, axis=1)
    zero_weight_vertices = weight_sums < 0.01
    if np.any(zero_weight_vertices):
        weights[zero_weight_vertices] = np.array(
            [1.0, 0.0, 0.0, 0.0],
            dtype=np.float32,
        )

    target_names = mesh_data.get("extras", {}).get("targetNames", [])
    morph_targets = {}
    for target_index, target in enumerate(primitive_data.get("targets", [])):
        name = (
            target_names[target_index]
            if target_index < len(target_names)
            else f"target_{target_index}"
        )

        position_accessor = target.get("POSITION")
        if position_accessor is None:
            morph_targets[name] = np.zeros((vertex_count, 3), dtype=np.float32)
            continue

        # glTF morph target POSITION data is a relative delta. Keep it relative
        # so expression weights add clean offsets in the vertex shader.
        morph_targets[name] = np.asarray(
            read_accessor(gltf_json, bin_blob, position_accessor),
            dtype=np.float32,
        )

    texture_bytes, base_color_factor = extract_base_color_texture(
        gltf_json,
        bin_blob,
        primitive_data,
    )

    return {
        "vertices": pos,
        "normals": normals,
        "uvs": uv,
        "joints": joints,
        "weights": weights,
        "indices": indices,
        "index_count": len(indices),
        "morph_targets": morph_targets,
        "texture": texture_bytes,
        "base_color_factor": base_color_factor,
        "vertex_count": vertex_count,
    }
