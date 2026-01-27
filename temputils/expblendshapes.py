# read_named_blendshapes.py
import json
import sys
import os

def read_named_blendshapes(json_path, out_file="blendshapes_reference.txt"):
    if not os.path.exists(json_path):
        print(f"❌ File not found: {json_path}")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    # Expecting the JSON has the VRM structure with blendShapeGroups
    blend_groups = data.get("extensions", {}).get("VRM", {}).get("blendShapeMaster", {}).get("blendShapeGroups", [])
    if not blend_groups:
        print("❌ No blendShapeGroups found in JSON")
        return

    print(f"🔍 Found {len(blend_groups)} blendshape groups")

    with open(out_file, "w") as out:
        for group in blend_groups:
            name = group.get("name", "Unnamed")
            preset = group.get("presetName", "None")
            binds = group.get("binds", [])
            out.write(f"Blendshape Group: {name} | Preset: {preset}\n")
            print(f"Blendshape Group: {name} | Preset: {preset}")
            for bind in binds:
                mesh_index = bind.get("mesh")
                target_index = bind.get("index")
                out.write(f"  → Mesh {mesh_index}, Target {target_index}\n")
                print(f"  → Mesh {mesh_index}, Target {target_index}")
            out.write("\n")

    print(f"✅ Blendshape info exported to '{out_file}'")


if __name__ == "__main__":
    '''
    if len(sys.argv) < 2:
        print("Usage: python read_named_blendshapes.py <blendshapes.json>")
        sys.exit(1)
'''
    json_file = "assets/kisayo_fixed_export.json" #sys.argv[1]
    read_named_blendshapes(json_file)
