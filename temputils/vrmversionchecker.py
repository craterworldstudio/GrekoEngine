import json
import struct

def identify_vrm_version(file_path):
    with open(file_path, 'rb') as f:
        # --- FLAG: GLB Magic Check ---
        # The first 4 bytes of any valid VRM/GLB must be 'glTF'
        magic = f.read(4)
        if magic != b'glTF':
            return "Not a valid glTF/VRM file."

        # Skip glTF version and total file length (8 bytes)
        f.seek(12)

        # --- FLAG: JSON Chunk Header ---
        # Read the length of the first chunk (JSON metadata)
        chunk_length = struct.unpack('<I', f.read(4))[0]
        chunk_type = f.read(4)

        if chunk_type != b'JSON':
            return "Could not find JSON metadata chunk."

        # Read and parse the JSON chunk
        json_chunk = f.read(chunk_length)
        data = json.loads(json_chunk)

        # --- THE VERSION FLAGS ---
        # We look into the 'extensions' dictionary for specific keys
        extensions = data.get('extensions', {})

        if 'VRM' in extensions:
            # VRM 0.x uses the key "VRM"
            return "Confirmed: This is a VRM 0.x file."
        
        if 'VRMC_vrm' in extensions:
            # VRM 1.x uses the key "VRMC_vrm"
            return "Confirmed: This is a VRM 1.x file."

        return "This is a glTF file, but it doesn't seem to have VRM extensions."

# Usage
print(identify_vrm_version("assets/Kiyo.vrm"))