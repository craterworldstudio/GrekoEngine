# verifyMorph.py
# Verifies whether morph targets (blendshapes) exist in a GLB file
# AFTER vrmFixer.py processing.
# This ONLY inspects the JSON chunk (authoritative truth).

import json
import struct
import sys
import os

def verify_morphs(glb_path):
    if not os.path.exists(glb_path):
        print(f"❌ File not found: {glb_path}")
        return

    print(f"🔍 Verifying morph targets in: {glb_path}")

    with open(glb_path, "rb") as f:
        data = f.read()

    # ---- GLB HEADER ----
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b'glTF':
        print("❌ Not a valid GLB file")
        return

    offset = 12
    json_chunk = None

    # ---- CHUNK WALK ----
    while offset < len(data):
        chunk_len, chunk_type = struct.unpack_from("<I4s", data, offset)
        offset += 8

        chunk_data = data[offset:offset + chunk_len]
        offset += chunk_len

        if chunk_type == b'JSON':
            json_chunk = chunk_data
            break

    if json_chunk is None:
        print("❌ No JSON chunk found")
        return

    gltf = json.loads(json_chunk.decode("utf-8"))

    # ---- MORPH INSPECTION ----
    meshes = gltf.get("meshes", [])
    if not meshes:
        print("❌ No meshes found in GLB")
        return

    found_any = False

    for mi, mesh in enumerate(meshes):
        mesh_name = mesh.get("name", f"Mesh_{mi}")
        primitives = mesh.get("primitives", [])

        for pi, prim in enumerate(primitives):
            targets = prim.get("targets")
            if targets:
                found_any = True
                print(f"✅ Mesh '{mesh_name}', Primitive {pi}: {len(targets)} morph targets")

                # Detailed target breakdown
                for ti, target in enumerate(targets):
                    attrs = ", ".join(target.keys())
                    print(f"   └─ Target {ti}: attributes [{attrs}]")

    if not found_any:
        print("❌ NO morph targets found in any mesh")
        print("⚠️  This means vrmFixer OR export removed them")

    else:
        print("🎯 Morph targets ARE present in the GLB")
        print("👉 If Panda3D cannot see them, Assimp is 100% the culprit")

if __name__ == "__main__":

    path = "/home/tori/Codestuff/GrekoGameEngine/assets/kisayo_fixed.glb"
    verify_morphs(path)
    '''
    if len(sys.argv) < 2:
        print("Usage: python verifyMorph.py <file.glb>")
    else:
        path = "/home/tori/Codestuff/GrekoGameEngine/assets/kisayo_fixed.glb"
        verify_morphs(sys.argv[1])
'''