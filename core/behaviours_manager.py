#from dbm.ndbm import library
import os, sys
import importlib
import inspect
import pkgutil
import core.behaviours
from core.BehaviourBaseClasses import *

#import core.behaviours.blinker
#import core.behaviours.breather
#import core.behaviours.lookAt
#import core.behaviours.mouthSequencer

def _get_behaviour_modules():
    """Works both in development and when frozen by PyInstaller."""
    import pkgutil
    import core.behaviours

    if getattr(sys, 'frozen', False):
        # When frozen, pkgutil can't walk the zip — enumerate explicitly
        module_names = [
            'blinker', 'breather', 'lookAt', 'mouthSequencer'
        ]
        modules = []
        for name in module_names:
            try:
                mod = importlib.import_module(f"core.behaviours.{name}")
                modules.append((None, name, False, mod))
            except ImportError:
                pass
        return modules
    else:
        result = []
        for loader, module_name, is_pkg in pkgutil.iter_modules(core.behaviours.__path__):
            mod = importlib.import_module(f"core.behaviours.{module_name}")
            result.append((loader, module_name, is_pkg, mod))
        return result

class SkeletonBehaviorManager:
    def __init__(self, skeleton):
        self.active_behaviors = []
        self.skeleton = skeleton

    def load_behaviors(self, *args, **kwargs):
        from greko_run import resource_path

        behavior_dir = resource_path("core/behaviours")

        


        for loader, module_name, is_pkg, module  in _get_behaviour_modules():
                #module = importlib.import_module(f"core.behaviours.{module_name}")

            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, SkeletonBehaviorBase)
                    and obj is not SkeletonBehaviorBase
                ):
                    print(f"🦴 Loaded Skeleton Behavior: {name} from {module_name}")
                    instance = obj()
                    self.active_behaviors.append(instance)
                    instance.setup(self.skeleton, *args, **kwargs)


    def update(self, dt, context):
        animator, target_index, gn = context.animator, context.target_index, context.gn
        for behavior in self.active_behaviors:
            behavior.update(gn, animator, target_index)

class MorphBehaviorManager:
    def __init__(self):
        self.active_behaviors = []
        self.face_mesh_indices = []

    def load_behaviors(self):
        """Scans core/behaviours and imports everything"""

        

        #behavior_dir = "core/behaviours"

        """
        for filename in os.listdir(behavior_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = f"core.behaviours.{filename[:-3]}"
                module = importlib.import_module(module_name)
                
                # FLAG: Reflection
                # Find any class inside the file that looks like a behavior
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BehaviorBase) and obj is not BehaviorBase:
                        print(f"🧩 Loaded Morph Behavior: {name} from {filename}")
                        self.active_behaviors.append(obj())
        """

        for loader, module_name, is_pkg, module in _get_behaviour_modules():
            module = importlib.import_module(f"core.behaviours.{module_name}")

            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BehaviorBase) and obj is not BehaviorBase:
                    print(f"🧩 Loaded Morph Behavior: {name} from {module_name}")
                    self.active_behaviors.append(obj())

    def inject_morph_library(self, library):
        for b in self.active_behaviors:
            # We check if the behavior has a 'morph_library' attribute
            if hasattr(b, "morph_library"):
                b.morph_library = library
                print(f"📖 Library injected into {type(b).__name__}")

            if hasattr(b, "face_indices"):
                b.face_indices = self.face_mesh_indices
                print(f"🎯 Assigned Face Indices {self.face_mesh_indices} to {type(b).__name__}")

    def trigger_mouth_sequence(self, filename):
        for b in self.active_behaviors:
            if type(b).__name__ == "MouthSequencer":
                b.load(filename)
                print(f"🎬 Triggered mouth sequence: {filename}")



    def update(self, dt, context):
        """Runs the logic for every behavior found"""
        gn = context.gn
        current_weights = [0.0, 0.0, 0.0, 0.0]

        for behavior in self.active_behaviors:
            weights_to_apply = behavior.update(gn)
            
            if "Fcl_EYE_Close" in weights_to_apply:
                current_weights[0] = max(current_weights[0], weights_to_apply["Fcl_EYE_Close"])

            if "Fcl_ALL_Surprised" in weights_to_apply:
                current_weights[1] = max(current_weights[1], weights_to_apply["Fcl_ALL_Surprised"])

            if "PHONEME_ACTIVE" in weights_to_apply:
                current_weights[2] = max(current_weights[2], weights_to_apply["PHONEME_ACTIVE"])
        
        gn.set_morph_weights(*current_weights)