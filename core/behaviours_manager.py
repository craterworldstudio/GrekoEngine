import sys
import importlib
import inspect
import pkgutil

import core.behaviours
from core.BehaviourBaseClasses import (
    BehaviorBase,
    SkeletonBehaviorBase
)

# Explicit imports so PyInstaller includes them
import core.behaviours.blinker
import core.behaviours.breather
import core.behaviours.lookAt
import core.behaviours.mouthSequencer


# ==========================================
# MODULE DISCOVERY
# ==========================================
def get_behaviour_modules():
    """
    Returns imported behavior modules.
    Works in development and PyInstaller builds.
    """

    module_names = [
        "blinker",
        "breather",
        "lookAt",
        "mouthSequencer"
    ]

    modules = []

    for name in module_names:
        try:
            module = importlib.import_module(
                f"core.behaviours.{name}"
            )
            modules.append((name, module))
        except Exception as e:
            print(f"❌ Failed to load behavior module {name}: {e}")

    return modules


# ==========================================
# SKELETON BEHAVIOR MANAGER
# ==========================================
class SkeletonBehaviorManager:
    def __init__(self, skeleton):
        self.skeleton = skeleton
        self.active_behaviors = []

    def load_behaviors(self, *args, **kwargs):
        self.active_behaviors.clear()

        for module_name, module in get_behaviour_modules():
            for name, obj in inspect.getmembers(module, inspect.isclass):

                if (
                    issubclass(obj, SkeletonBehaviorBase)
                    and obj is not SkeletonBehaviorBase
                ):
                    try:
                        instance = obj()
                        instance.setup(
                            self.skeleton,
                            *args,
                            **kwargs
                        )

                        self.active_behaviors.append(instance)

                        print(
                            f"🦴 Loaded Skeleton Behavior: "
                            f"{name} from {module_name}"
                        )

                    except Exception as e:
                        print(
                            f"❌ Failed skeleton behavior "
                            f"{name}: {e}"
                        )

    def update(self, dt, context):
        animator = context.animator
        target_index = context.target_index
        gn = context.gn

        for behavior in self.active_behaviors:
            try:
                behavior.update(
                    gn,
                    animator,
                    target_index
                )
            except Exception as e:
                print(
                    f"❌ Skeleton update failed: {e}"
                )


# ==========================================
# MORPH BEHAVIOR MANAGER
# ==========================================
class MorphBehaviorManager:
    def __init__(self, skeleton, gn, vrm_version=2):
        # Cache skeleton context across the lifecycles
        self.skeleton = skeleton
        self.gn = gn
        self.vrm_version = vrm_version
        self.active_behaviors = []
        self.face_mesh_indices = []

    def load_behaviors(self, *args, **kwargs):
        self.active_behaviors.clear()

        for module_name, module in get_behaviour_modules():
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BehaviorBase)
                    and obj is not BehaviorBase
                    and not issubclass(obj, SkeletonBehaviorBase) # Prevent overlap leaks
                ):
                    try:
                        instance = obj()
                        
                        # FIX: Execute the new decoupled setup pipeline
                        instance.setup(
                            self.skeleton,
                            self.gn,
                            self.vrm_version,
                            *args,
                            **kwargs
                        )
                        
                        self.active_behaviors.append(instance)
                        print(f"🧩 Loaded Morph Behavior: {name} from {module_name}")
                    except Exception as e:
                        print(f"❌ Failed morph behavior {name}: {e}")

    def inject_morph_library(self, library):
        for behavior in self.active_behaviors:
            if hasattr(behavior, "morph_library"):
                behavior.morph_library = library
                print(f"📖 Library injected into {type(behavior).__name__}")

            if hasattr(behavior, "face_indices"):
                behavior.face_indices = self.face_mesh_indices
                print(f"🎯 Assigned Face Indices {self.face_mesh_indices} to {type(behavior).__name__}")

    def trigger_mouth_sequence(self, filename):
        for behavior in self.active_behaviors:
            if type(behavior).__name__ == "MouthSequencer":
                behavior.load(filename)
                print(f"🎬 Triggered mouth sequence: {filename}")

    def update(self, dt, context):
        gn = context.gn

        # [0] Blink, [1] Breath, [2] Mouth/Viseme
        current_weights = [0.0, 0.0, 0.0, 0.0]

        # Fetch the master blendshape map we parsed from the VRM asset JSON
        # If it doesn't exist, fall back to an empty dictionary
        vrm_blendshape_config = getattr(self.skeleton, "json", {}).get("extensions", {}).get("VRM", {}).get("blendShapeMaster", {}).get("blendShapeGroups", [])
        
        # Build a live runtime lookup map for VRM0: e.g., {"blink": [10, 11, 18, 19]}
        vrm0_target_lookup = {}
        if vrm_blendshape_config:
            for group in vrm_blendshape_config:
                preset_name = group.get("presetName", "").lower()
                binds = group.get("binds", [])
                if preset_name and binds:
                    # Capture all target primitive morph indices for this preset
                    vrm0_target_lookup[preset_name] = [int(b.get("index", 0)) for b in binds]

        for behavior in self.active_behaviors:
            try:
                weights = behavior.update(gn)
                if not weights:
                    continue

                b_name = type(behavior).__name__

                # ==========================================
                # VRM 1.0 PATHWAY (Direct String Match)
                # ==========================================
                if "VRMC_vrm" in self.skeleton.json.get("extensions", {}):
                    if b_name == "Blinker":
                        target = getattr(behavior, "target_name", "Fcl_EYE_Close")
                        if target in weights:
                            current_weights[0] = max(current_weights[0], weights[target])

                    elif b_name == "Breather":
                        target = getattr(behavior, "target_name", "Fcl_ALL_Surprised")
                        if target in weights:
                            current_weights[1] = max(current_weights[1], weights[target])

                # ==========================================
                # VRM 0.0 PATHWAY (Index Resolution)
                # ==========================================
                else:
                    if b_name == "Blinker":
                        # Behavior outputs {"blink": weight}
                        if "blink" in weights and "blink" in vrm0_target_lookup:
                            # Send raw weight value directly to C++ layout mapping position
                            current_weights[0] = max(current_weights[0], weights["blink"])
                            
                            # FLAG: Direct Shader Uniform Drive
                            # If your engine allows driving indices directly via C++, pass them here:
                            for morph_idx in vrm0_target_lookup["blink"]:
                                # gn.set_raw_mesh_morph(mesh_index=1, target_idx=morph_idx, weight=weights["blink"])
                                pass

                    elif b_name == "Breather":
                        # Behavior outputs {"fun": weight}
                        if "fun" in weights and "fun" in vrm0_target_lookup:
                            current_weights[1] = max(current_weights[1], weights["fun"])

            except Exception as e:
                print(f"❌ Morph target weight resolution failed: {e}")

        # Dispatch the processed unified parameters down to OpenGL
        #print(current_weights)
        gn.set_morph_weights(*current_weights)