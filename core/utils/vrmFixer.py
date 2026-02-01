import json
import struct, sys, os

def fix_vrm_for_panda(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"❌ Error: Input file not found at {os.path.abspath(input_path)}")
        return
    
    print(f"🛠️  Patching {input_path} for Panda3D...")
    try:
        with open(input_path, 'rb') as f:
            data = f.read()

        # GLB header is 12 bytes: Magic (4), Version (4), Length (4)
        # JSON chunk header is 8 bytes: Length (4), Type (4)
        json_len = struct.unpack('<I', data[12:16])[0]
        json_data = data[20:20+json_len].decode('utf-8')
        gltf_dict = json.loads(json_data)

        # FLAG: The "Panda-Killer" Extensions
        # These tell the loader 'Don't load me unless you understand VRM 1.0'
        # By removing them, Panda treats it as a standard GLB skeleton.
        #forbidden = [ 'VRMC_springBone', 'VRMC_node_constraint']
        forbidden = []

        '''# 1. Remove from Required: This stops the "Unknown Extension" crash.
        if 'extensionsRequired' in gltf_dict:
            gltf_dict['extensionsRequired'] = [
                e for e in gltf_dict['extensionsRequired'] if e not in forbidden
            ]'''

        #We hide this to enable blendshapes!
        """if 'extensionsUsed' in gltf_dict:
            gltf_dict['extensionsUsed'] = [
                e for e in gltf_dict['extensionsUsed'] if e not in forbidden
            ]"""

        # Re-pack the JSON
        new_json_str = json.dumps(gltf_dict)
        # Must pad with spaces to 4-byte boundary for GLB spec
        while len(new_json_str) % 4 != 0:
            new_json_str += ' '

        new_json_bytes = new_json_str.encode('utf-8')
        new_json_len = len(new_json_bytes)

        # Reconstruct the GLB
        # Header + JSON Chunk + Binary Chunk (rest of the file)
        new_data = (
            data[:8] + 
            struct.pack('<I', 12 + 8 + new_json_len + (len(data) - (20 + json_len))) +
            struct.pack('<I', new_json_len) +
            data[16:20] + 
            new_json_bytes + 
            data[20+json_len:]
        )

        with open(output_path, 'wb') as f:
            f.write(new_data)
        print(f"✅ Created Panda-friendly model: {output_path}")

    except FileNotFoundError:
        print(f"❌ Error: Could not find {input_path}")
        
    except Exception as e:
        print(f"❌ Failed to patch VRM: {e}")

# Run the fix
if __name__ == "__main__":
    # Check if we were given paths via entry.py
    # sys.argv[0] is the script name, [1] is input, [2] is output
    if len(sys.argv) > 2:
        fix_vrm_for_panda(sys.argv[1], sys.argv[2])
    else:
        # Fallback for manual testing
        fix_vrm_for_panda("assets/kisayo.vrm", "assets/kisayo_fixed.glb")