import os
import importlib
import inspect

class BehaviorManager:
    def __init__(self):
        self.active_behaviors = []

    def load_behaviors(self):
        """Scans core/behaviours and imports everything"""
        behavior_dir = "core/behaviours"
        for filename in os.listdir(behavior_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = f"core.behaviours.{filename[:-3]}"
                module = importlib.import_module(module_name)
                
                # FLAG: Reflection
                # Find any class inside the file that looks like a behavior
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and name != "BehaviorBase":
                        print(f"🧩 Loaded Behavior: {name} from {filename}")
                        self.active_behaviors.append(obj())

    def update_all(self, gn):
        """Runs the logic for every behavior found"""

        current_weights = [0.0, 0.0, 0.0, 0.0]

        for behavior in self.active_behaviors:
            weights_to_apply = behavior.update()
            
            if "Fcl_EYE_Close" in weights_to_apply:
                current_weights[0] = max(current_weights[0], weights_to_apply["Fcl_EYE_Close"])

            #if "Fcl_ALL_Surprised" in weights_to_apply:
            #    current_weights[1] = max(current_weights[1], weights_to_apply["Fcl_ALL_Surprised"])
        
        gn.set_morph_weights(*current_weights)