import os
import gltf
from panda3d.core import load_prc_file_data
from direct.showbase.ShowBase import ShowBase

# FLAG: Usual loader flags
load_prc_file_data("", "gltf-ignore-extensions #t")
load_prc_file_data("", "notify-level-gltf debug")

class NativeTest(ShowBase):
    def __init__(self):
        super().__init__()
        
        vrm_path = "assets/kisayo.vrm"
        glb_path = "assets/kisayo.glb"
        
        # FLAG: OS-Level Symlink
        # We create a virtual link: kisayo.glb -> kisayo.vrm
        # This makes the file appear to have a .glb extension to Panda3D
        if os.path.exists(vrm_path):
            if not os.path.exists(glb_path):
                print(f"🔗 Creating symlink: {glb_path} -> {vrm_path}")
                os.symlink(os.path.abspath(vrm_path), os.path.abspath(glb_path))
        else:
            print(f"❌ Physical file not found at {vrm_path}")

        print("\n--- ATTEMPTING LOAD ---")
        try:
            # Now we load the .glb extension
            self.model = self.loader.load_model(glb_path, noCache=True) #type: ignore 
            
            if self.model:
                print("🎉 SUCCESS: Native VRM loaded via OS Symlink!")
                self.model.reparent_to(self.render) # type: ignore
            else:
                print("❌ FAILED: Loader found the file but couldn't parse the VRM data.")
        except Exception as e:
            print(f"💥 CRASH: {e}")

app = NativeTest()
app.run()