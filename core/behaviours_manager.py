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
        self.morph_library = {}
        self.morph_slot_assignments = {
            "Blinker": 0,
            "Breather": 1,
            "MouthSequencer": 2
        }
        self.morph_slot_targets = {
            0: None,
            1: None,
            2: None,
            3: None,
            4: None,
            5: None,
            6: None,
            7: None,
            8: None,
            9: None
        }

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
        self.morph_library = library

        for behavior in self.active_behaviors:
            if hasattr(behavior, "morph_library"):
                behavior.morph_library = library
                print(f"📖 Library injected into {type(behavior).__name__}")

            if hasattr(behavior, "face_indices"):
                behavior.face_indices = self.face_mesh_indices
                print(f"🎯 Assigned Face Indices {self.face_mesh_indices} to {type(behavior).__name__}")

        if self.vrm_version == 0:
            self.assign_default_vrm0_slots()

    def assign_default_vrm0_slots(self):
        if not self.morph_library:
            return

        def pick(keys):
            for query in keys:
                for name in self.morph_library.keys():
                    if query in name.lower():
                        return name
            return None

        # 🟩 Added common Japanese VRM0 blendshape keyword matches
        blink_name = pick(["blink", "eye_close", "まばたき", " 瞬き", "閉じる"])
        breath_name = pick(["fun", "joy", "surprised", "breath", "喜", "笑い"])
        closed_name = pick(["fcl_mth_close", "mouth_close", "口閉", "ん"])
        
        mouth_a_name = pick(["fcl_mth_a", "mouth_a", "あ", "ア"])
        mouth_e_name = pick(["fcl_mth_e", "mouth_e", "え", "エ"])
        mouth_i_name = pick(["fcl_mth_i", "mouth_i", "い", "イ"])
        mouth_o_name = pick(["fcl_mth_o", "mouth_o", "お", "オ"])
        mouth_u_name = pick(["fcl_mth_u", "mouth_u", "う", "ウ"])

        # (Rest of your combining loop remains exactly the same...)

        # Handle left/right separated blink morphs by combining them if needed
        if blink_name:
            # Find all blink-like keys
            blink_keys = [k for k in self.morph_library.keys() if "blink" in k.lower() or "eye_close" in k.lower()]
            if len(blink_keys) > 1:
                # Combine arrays safely
                arrays = [self.morph_library[k].ravel() for k in blink_keys]
                # Ensure same length by padding/truncating
                max_len = max(a.size for a in arrays)
                import numpy as _np
                combined = _np.zeros((max_len,), dtype=_np.float32)
                for a in arrays:
                    combined[:a.size] += a
                combined = combined.reshape((-1, 3)) if combined.size % 3 == 0 else combined
                # Store under synthetic name
                synth_name = "__combined_blink__"
                self.morph_library[synth_name] = combined
                self.handle_morph_assignment(0, synth_name)
            else:
                self.handle_morph_assignment(0, blink_name)
        if breath_name:
            self.handle_morph_assignment(3, breath_name)
        if closed_name:
            self.handle_morph_assignment(4, closed_name)
        if mouth_a_name:
            self.handle_morph_assignment(5, mouth_a_name)
        if mouth_e_name:
            self.handle_morph_assignment(6, mouth_e_name)
        if mouth_i_name:
            self.handle_morph_assignment(7, mouth_i_name)
        if mouth_o_name:
            self.handle_morph_assignment(8, mouth_o_name)
        if mouth_u_name:
            self.handle_morph_assignment(9, mouth_u_name)

    def trigger_mouth_sequence(self, filename):
        for behavior in self.active_behaviors:
            if type(behavior).__name__ == "MouthSequencer":
                behavior.load(filename)
                print(f"🎬 Triggered mouth sequence: {filename}")

    def handle_morph_assignment(self, slot_id, morph_name):
        if slot_id not in self.morph_slot_targets:
            print(f"❌ Unknown morph slot id: {slot_id}")
            return

        if morph_name not in self.morph_library:
            print(f"❌ Morph slot assignment failed: '{morph_name}' not found in loaded morph library")
            return

        self.morph_slot_targets[slot_id] = morph_name
        print(f"🧩 Assigned morph '{morph_name}' to slot {slot_id}")

        # Blink and breath use direct GPU slot updates.
        # Mouth sequencer phoneme slots are mapped and applied later by the sequencer.
        # Direct GPU-updated slots: Blink Unified (0), Blink Left (1), Blink Right (2), Breath (3)
        if slot_id in (0, 1, 2, 3):
            for mesh_index in self.face_mesh_indices:
                self.gn.update_morph_data(
                    mesh_index,
                    slot_id,
                    self.morph_library[morph_name]
                )

            # If a unified blink is assigned to slot 0 and left/right are unassigned,
            # also populate the left/right slots so both eyes respond.
            if slot_id == 0:
                for side in (1, 2):
                    if self.morph_slot_targets.get(side) is None:
                        for mesh_index in self.face_mesh_indices:
                            self.gn.update_morph_data(
                                mesh_index,
                                side,
                                self.morph_library[morph_name]
                            )

        if slot_id >= 4:
            phoneme_key_map = {
                4: "REST",
                5: "A",
                6: "E",
                7: "I",
                8: "O",
                9: "U"
            }
            phoneme_key = phoneme_key_map.get(slot_id)
            if phoneme_key:
                for behavior in self.active_behaviors:
                    if type(behavior).__name__ == "MouthSequencer":
                        if hasattr(behavior, "set_phoneme_target"):
                            behavior.set_phoneme_target(phoneme_key, morph_name)
                        break

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
                slot_index = self.morph_slot_assignments.get(b_name, None)

                # ==========================================
                # VRM 1.0 PATHWAY (Direct String Match)
                # ==========================================
                if "VRMC_vrm" in self.skeleton.json.get("extensions", {}):
                    if slot_index is not None:
                        for target_name, weight in weights.items():
                            current_weights[slot_index] = max(current_weights[slot_index], weight)

                # ==========================================
                # VRM 0.0 PATHWAY (Index Resolution)
                # ==========================================
                else:
                    if slot_index is not None:
                        for target_name, weight in weights.items():
                            # Mouth sequencer reports PHONEME_ACTIVE to turn the preloaded slot on/off.
                            if target_name == "PHONEME_ACTIVE":
                                current_weights[slot_index] = max(current_weights[slot_index], weight)
                                continue

                            # If the behavior emits a direct morph key, accept it as well.
                            if target_name in self.morph_library:
                                current_weights[slot_index] = max(current_weights[slot_index], weight)
                                continue

                            assigned_target = self.morph_slot_targets.get(slot_index)
                            if assigned_target and target_name == assigned_target:
                                current_weights[slot_index] = max(current_weights[slot_index], weight)

                            # Fallback for VRM0 standard preset names
                            if b_name == "Blinker" and target_name in {"blink", "blink_r", "blink_l", "__combined_blink__"}:
                                current_weights[slot_index] = max(current_weights[slot_index], weight)
                            elif b_name == "Breather" and target_name in {"fun", "joy", "surprised"}:
                                current_weights[slot_index] = max(current_weights[slot_index], weight)

            except Exception as e:
                print(f"❌ Morph target weight resolution failed: {e}")
                raise e

        # Dispatch the processed unified parameters down to OpenGL
        #print(current_weights)
        gn.set_morph_weights(*current_weights)