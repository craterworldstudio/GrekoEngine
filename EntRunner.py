import os
import subprocess
import json

# --- ASSET CONFIGURATION ---
ACTIVE_CHARACTER = {
    "name": "Kisayo",
    "source_path": "assets/kisayo.vrm",
    "fixed_path": "assets/kisayo_fixed.glb",
    "scale": 1.0,
    "start_pos": (0, 5, 0),
    # FLAG: Force Rebuild
    # Set this to True if you change your fixer logic or the .vrm file.
    # Set to False to skip the fixing process and boot instantly.
    "force_rebuild": True,
    "use_json_lighting": True,
}

def run_preflight_fixer(char_data):
    source = char_data["source_path"]
    target = char_data["fixed_path"]
    
    # FLAG: Existence Check
    # We check if the file already exists before trying to build it.
    exists = os.path.exists(target)
    
    if char_data["force_rebuild"] or not exists:
        reason = "Force rebuild enabled" if char_data["force_rebuild"] else "Fixed model not found"
        print(f"🛠️  Pre-flight: {reason}. Patching {char_data['name']}...")
        
        try:
            # We call the fixer script with the paths as arguments
            subprocess.run([
                "python", "vrmmanager/vrmFixer.py", 
                source, 
                target
            ], check=True)
            print("✅ Fixer completed successfully.")
        except Exception as e:
            print(f"⚠️  Fixer failed: {e}")
    else:
        # FLAG: Fast Boot
        # If the file exists and we aren't forcing a rebuild, we skip straight to the engine.
        print(f"⏭️  Fixed model found for {char_data['name']}. Skipping build for speed.")

if __name__ == "__main__":
    # 1. Run the Fixer logic
    run_preflight_fixer(ACTIVE_CHARACTER)
    
    # 2. Save the details to a temp file
    with open("current_session.json", "w") as f:
        json.dump(ACTIVE_CHARACTER, f)
        
    # 3. Launch the Engine
    print("🚀 Launching Greko Engine...")
    subprocess.run(["python", "main.py"])