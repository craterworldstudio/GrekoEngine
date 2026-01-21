from panda3d.core import LoaderOptions, NodePath, VirtualFileSystem

class VRMHandler:
    def __init__(self, engine):
        self.engine = engine
        self.model = None

    def load_character(self, path):
        try:
            # FLAG: The "Symlink" Trick
            # We tell Panda3D to treat this specific .vrm as if it were a .glb 
            # in the engine's memory. This prevents corruption and fixes the loader.
            vfs = VirtualFileSystem.get_global_ptr()
            filename_as_glb = path.replace(".vrm", ".glb")
            
            # This 'mounts' the vrm file as a glb alias
            print(f"🔄 Mapping {path} -> {filename_as_glb}")

            print(f"🔄 Loading VRM 1.x Character from: {path}")
            # FLAG: LoaderOptions(16) 
            # This tells Panda3D not to try and process animations yet 
            # to avoid the "KeyError" common with VRM 1.0 skeletons.
            options = LoaderOptions(16) 
            
            # Load the model
            self.model = self.engine.loader.load_model(path, loaderOptions=options, noCache=True)
            
            if self.model:
                 # FLAG: Two-Sided Rendering
                # VRM models often have single-sided hair/clothing. 
                # This ensures she is visible from all angles.
                self.model.set_two_sided(True)

                # FLAG: Coordinate Correction
                # VRMs are Y-up (Unity style), Panda3D is Z-up. 
                # The gltf-loader usually fixes this, but if she's lying on her face, 
                # we might need: self.model.set_p(-90)
                
                print(f"✅ VRM 1.x Character '{path}' loaded.")
                return self.model
            else:
                print(f"🔄 Loading VRM 1.x Character from: {filename_as_glb}")
                # FLAG: If standard load fails, try the alias
                self.model = self.engine.loader.load_model(filename_as_glb, loaderOptions=options)

                if self.model:
                    # FLAG: Two-Sided Rendering
                    # VRM models often have single-sided hair/clothing. 
                    # This ensures she is visible from all angles.
                    self.model.set_two_sided(True)

                    # FLAG: Coordinate Correction
                    # VRMs are Y-up (Unity style), Panda3D is Z-up. 
                    # The gltf-loader usually fixes this, but if she's lying on her face, 
                    # we might need: self.model.set_p(-90)
                    
                    print(f"✅ VRM 1.x Character '{path}' loaded.")
                    return self.model
                    # VRMs are Y-up (Unity style), Panda3D is Z-up. 
                    # The gltf-loader usually fixes this, but if she's lying on her face, 
                    # we might need: self.model.set_p(-90)
            
                else:
                    print(f"❌ Failed to load VRM 1.x Character: {path}")
                    return None
            
        except Exception as e:
            print(f"❌ Error loading VRM 1.x: {e}")