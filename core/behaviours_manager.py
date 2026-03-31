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
    def __init__(self):
        self.active_behaviors = []
        self.face_mesh_indices = []

    def load_behaviors(self):
        self.active_behaviors.clear()

        for module_name, module in get_behaviour_modules():
            for name, obj in inspect.getmembers(module, inspect.isclass):

                if (
                    issubclass(obj, BehaviorBase)
                    and obj is not BehaviorBase
                ):
                    try:
                        instance = obj()
                        self.active_behaviors.append(instance)

                        print(
                            f"🧩 Loaded Morph Behavior: "
                            f"{name} from {module_name}"
                        )

                    except Exception as e:
                        print(
                            f"❌ Failed morph behavior "
                            f"{name}: {e}"
                        )

    def inject_morph_library(self, library):
        for behavior in self.active_behaviors:

            if hasattr(behavior, "morph_library"):
                behavior.morph_library = library
                print(
                    f"📖 Library injected into "
                    f"{type(behavior).__name__}"
                )

            if hasattr(behavior, "face_indices"):
                behavior.face_indices = self.face_mesh_indices
                print(
                    f"🎯 Assigned Face Indices "
                    f"{self.face_mesh_indices} to "
                    f"{type(behavior).__name__}"
                )

    def trigger_mouth_sequence(self, filename):
        for behavior in self.active_behaviors:
            if type(behavior).__name__ == "MouthSequencer":
                behavior.load(filename)
                print(
                    f"🎬 Triggered mouth sequence: "
                    f"{filename}"
                )

    def update(self, dt, context):
        gn = context.gn

        current_weights = [0.0, 0.0, 0.0, 0.0]

        for behavior in self.active_behaviors:
            try:
                weights = behavior.update(gn)

                if not weights:
                    continue

                if "Fcl_EYE_Close" in weights:
                    current_weights[0] = max(
                        current_weights[0],
                        weights["Fcl_EYE_Close"]
                    )

                if "Fcl_ALL_Surprised" in weights:
                    current_weights[1] = max(
                        current_weights[1],
                        weights["Fcl_ALL_Surprised"]
                    )

                if "PHONEME_ACTIVE" in weights:
                    current_weights[2] = max(
                        current_weights[2],
                        weights["PHONEME_ACTIVE"]
                    )

            except Exception as e:
                print(
                    f"❌ Morph update failed: {e}"
                )

        gn.set_morph_weights(*current_weights)
