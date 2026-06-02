import re

VRM0_EXPRESSION_MAP = {
    "joy": "happy",
    "fun": "relaxed",
    "sorrow": "sad",
    "angry": "angry",

    "blink": "blink",
    "blink_l": "blinkLeft",
    "blink_r": "blinkRight",

    "a": "aa",
    "i": "ih",
    "u": "ou",
    "e": "ee",
    "o": "oh",
}

def adapt_vrm1(parsed_glb):
    ext = parsed_glb.vrm_extension

    return {
        "version": 1,
        "humanoid": ext.get("humanoid", {}),
        "expressions": ext.get("expressions", {}),
        "lookAt": ext.get("lookAt", {}),
        "meta": ext.get("meta", {}),
    }

def adapt_vrm0(parsed_glb):
    ext = parsed_glb.vrm_extension

    blendshape_master = ext.get("blendShapeMaster", {})
    blend_groups = blendshape_master.get("blendShapeGroups", [])

    expressions = {}

    for group in blend_groups:
        raw_name = group.get("presetName") or group.get("name")

        if not raw_name:
            continue

        normalized = normalize_expression_name(raw_name)

        expressions[normalized] = group

    return {
        "version": 0,

        # Normalize humanoid location
        "humanoid": ext.get("humanoid", {}),

        # Unified expressions
        "expressions": expressions,

        "lookAt": ext.get("firstPerson", {}),

        "meta": ext.get("meta", {}),
    }


def normalize_expression_name(name: str):
    key = name.lower().strip()
    return VRM0_EXPRESSION_MAP.get(key, key)


def adapt_vrm(parsed_glb):
    version = parsed_glb.vrm_version

    if version == 1:
        return adapt_vrm1(parsed_glb)

    elif version == 0:
        return adapt_vrm0(parsed_glb)

    raise RuntimeError("Not a VRM file")