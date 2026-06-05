import os
from glb_parser import parse_glb

def inspect_skins_and_meshes(vrm_path):
    if not os.path.exists(vrm_path):
        print(f"❌ File not found: {vrm_path}")
        return

    print(f"🧐 Parsing asset structural layers: {vrm_path}")
    parsed_data = parse_glb(vrm_path)
    gltf_json = parsed_data.json

    meshes = gltf_json.get("meshes", [])
    nodes = gltf_json.get("nodes", [])
    skins = gltf_json.get("skins", [])

    print("\n==================================================")
    print(f"📊 STRUCTURE SUMMARY | VRM VERSION: {parsed_data.vrm_version}")
    print(f"Total Meshes: {len(meshes)} | Total Nodes: {len(nodes)} | Total Skins: {len(skins)}")
    print("==================================================\n")

    # 1. Map meshes to the structural scene nodes that actually invoke them
    node_mesh_map = {}
    for node_idx, node in enumerate(nodes):
        if "mesh" in node:
            m_idx = node["mesh"]
            s_idx = node.get("skin", "NONE (Static/Unskinned)")
            
            if m_idx not in node_mesh_map:
                node_mesh_map[m_idx] = []
            node_mesh_map[m_idx].append({
                "node_index": node_idx,
                "node_name": node.get("name", f"Node_{node_idx}"),
                "skin_index": s_idx
            })

    # 2. Iterate and print out detailed Mesh composition profiles
    print("📦 --- MESH LIST & INSTANCE BINDINGS ---")
    for mesh_idx, mesh in enumerate(meshes):
        mesh_name = mesh.get("name", f"Mesh_{mesh_idx}")
        primitives = mesh.get("primitives", [])
        
        print(f"\n[Mesh Index {mesh_idx}] Name: '{mesh_name}'")
        print(f"  └── Submesh Primitives: {len(primitives)}")
        
        # Check targets for blendshapes
        for p_idx, prim in enumerate(primitives):
            has_morphs = "targets" in prim
            morph_count = len(prim["targets"]) if has_morphs else 0
            print(f"      ├── Prim {p_idx} -> Mode: {prim.get('mode', 4)} | Morph Targets: {morph_count}")

        # Show where this mesh lives in your skeleton structure
        if mesh_idx in node_mesh_map:
            print("  └── Node Instances using this Mesh:")
            for inst in node_mesh_map[mesh_idx]:
                print(f"      └── 🏠 Node {inst['node_index']} ('{inst['node_name']}') -> Linked Skin: {inst['skin_index']}")
        else:
            print("  └── ⚠️ Orphan Warning: This mesh is defined but not instanced by any active scene node.")

    print("\n")
    print("🦴 --- SKIN DELEGATION LAYERS ---")
    if not skins:
        print("No skin clusters are registered inside this asset template.")
    for skin_idx, skin in enumerate(skins):
        skin_name = skin.get("name", f"Skin_{skin_idx}")
        joints = skin.get("joints", [])
        skeleton_root = skin.get("skeleton", "Not Defined")
        
        print(f"\n[Skin Index {skin_idx}] Name: '{skin_name}'")
        print(f"  ├── Root Joint Node Reference: {skeleton_root}")
        print(f"  ├── Total Bound GPU Joint Nodes: {len(joints)}")
        print(f"  └── Bone Node Index Map (First 15): {joints[:15]}...")

    print("\n==================================================")

if __name__ == "__main__":
    vrm_path = input("Enter path to VRM file to scan: ").strip()
    inspect_skins_and_meshes(vrm_path)