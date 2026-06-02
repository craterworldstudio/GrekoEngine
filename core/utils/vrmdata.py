import json
from pathlib import Path


def export_vrm_debug(parsed_glb, output_path="vrm_debug.json"):

    data = {
        "vrm_version": parsed_glb.vrm_version,
        "humanoid_map": {},
        "blendshapes": {},
        "mesh_morphs": {}
    }

    ext = parsed_glb.vrm_extension

    # =========================================
    # VRM0
    # =========================================

    if parsed_glb.vrm_version == 0:

        # -----------------------------
        # Humanoid Bones
        # -----------------------------

        humanoid = ext.get("humanoid", {})
        human_bones = humanoid.get("humanBones", [])

        for bone in human_bones:

            bone_name = bone.get("bone")
            node = bone.get("node")

            data["humanoid_map"][bone_name] = node

        # -----------------------------
        # Blendshape Groups
        # -----------------------------

        blend_master = ext.get("blendShapeMaster", {})
        groups = blend_master.get("blendShapeGroups", [])

        for i, group in enumerate(groups):

            name = (
                group.get("presetName")
                or group.get("name")
                or f"group_{i}"
            )

            data["blendshapes"][name] = []

            binds = group.get("binds", [])

            for bind in binds:

                data["blendshapes"][name].append({
                    "mesh": bind.get("mesh"),
                    "morph_index": bind.get("index"),
                    "weight": bind.get("weight")
                })

    # =========================================
    # VRM1
    # =========================================

    elif parsed_glb.vrm_version == 1:

        humanoid = ext.get("humanoid", {})
        human_bones = humanoid.get("humanBones", {})

        for bone_name, bone_data in human_bones.items():

            data["humanoid_map"][bone_name] = bone_data.get("node")

        expressions = ext.get("expressions", {})

        for expr_name, expr_data in expressions.items():

            morphs = expr_data.get("morphTargetBinds", [])

            data["blendshapes"][expr_name] = morphs

    # =========================================
    # Mesh Morph Targets
    # =========================================

    meshes = parsed_glb.json.get("meshes", [])

    for mesh_idx, mesh in enumerate(meshes):

        mesh_name = mesh.get("name", f"mesh_{mesh_idx}")

        target_names = (
            mesh.get("extras", {})
            .get("targetNames", [])
        )

        data["mesh_morphs"][mesh_name] = {}

        for i, morph_name in enumerate(target_names):

            data["mesh_morphs"][mesh_name][i] = morph_name

    # =========================================
    # Write File
    # =========================================

    output_path = Path(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"📄 VRM debug exported -> {output_path}")