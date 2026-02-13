#import core.greko_native as gn
import time
from pathlib import Path

from core.behaviours_manager import BehaviorBase


class PhonemeEvent:
    def __init__(self, phoneme: str, duration: float):
        self.phoneme = phoneme
        self.duration = duration

PHONEME_MAP = {
    "A": "Fcl_MTH_A",
    "E": "Fcl_MTH_E",
    "I": "Fcl_MTH_I",
    "O": "Fcl_MTH_O",
    "U": "Fcl_MTH_U",
    "REST": None
}


class MouthSequencer(BehaviorBase):
    def __init__(self):
        #self.phrase = ["Fcl_MTH_A", "Fcl_MTH_E", "Fcl_MTH_I", "Fcl_MTH_O", "Fcl_MTH_U"]
        #self.step_duration = 0.5  # Seconds per vowel
        self.last_update_time = time.time()
        self.current_time = 0.0
        self.playing = False
        self.current_index = 0
        self.current_mapped_name = None

        # We need access to the full library of morph arrays
        self.morph_library = {} 
        self.timeline = []
        self.face_indices = []


        self.target_slot = 2  # Slot reserved for phoneme morphs

        # Project root resolution
        self.project_root = Path(__file__).resolve().parents[2]
        self.gpseq_dir = self.project_root / "GEN_PHENOME_SEQ"


    def load(self, filename):
        path = self.gpseq_dir / filename

        if not path.exists():
            print(f"[GPSEQ] File not found: {path}")
            return

        text = path.read_text()
        self.timeline = self.parse_gpseq(text)

        print(f"[GPSEQ] Loaded {len(self.timeline)} events")

        self.current_index = 0
        self.current_time = 0.0
        self.playing = True

    def parse_gpseq(self, text):
        events = []

        for line in text.splitlines():
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(";")

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                tokens = part.split()
                if len(tokens) != 2:
                    continue

                phoneme, duration = tokens

                try:
                    duration = float(duration)
                except ValueError:
                    continue

                events.append(PhonemeEvent(phoneme, duration))
 
        return events
    

    #def update(self, gn):
    #    if not self.morph_library or not self.face_indices:
    #        return {} # Wait until data is injected
    #    
    #    now = time.time()
    #    
    #    if now - self.last_step_time > self.step_duration:
    #        self.last_step_time = now
    #        
    #        # 1. Get the name of the next vowel in the sequence
    #        vowel_name = self.phrase[self.current_index]
    #        
    #        # 2. Tell the engine to swap the GPU buffer for the Face mesh (Index 0)
    #        if vowel_name in self.morph_library:
    #            # FLAG: Dynamic Swap
    #            # This pushes the new vertex offsets to the GPU immediately
    #            for idx in self.face_indices:
    #                gn.update_morph_data(idx, self.target_slot, self.morph_library[vowel_name])
#
    #                #gn.update_morph_data(self.face_index, self.target_slot, self.morph_library[vowel_name])
    #                #print(f"👄 Mouth Swapped to: {vowel_name}")
#
    #        
#
    #        # 3. Increment sequence
    #        self.current_index = (self.current_index + 1) % len(self.phrase)
#
    #    # We return a weight of 1.0 for Slot 2 so the mouth is always 'on'
    #    return { "PHONEME_ACTIVE": 1.0 }
    

    def update(self, gn):

        if not self.morph_library or not self.face_indices:
            return {}

        if not self.playing or not self.timeline:
            return {"PHONEME_ACTIVE": 0.0}

        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now

        if self.current_index >= len(self.timeline):
            self.playing = False
            self.current_mapped_name = None
            return {"PHONEME_ACTIVE": 0.0}

        event = self.timeline[self.current_index]

        # Apply morph swap if exists
        mapped_name = PHONEME_MAP.get(event.phoneme)

        # REST or unknown phoneme
        if mapped_name is None:
            if self.current_mapped_name is not None:
                self.current_mapped_name = None
            return {"PHONEME_ACTIVE": 0.0}
        
        if mapped_name != self.current_mapped_name:
            

            if mapped_name in self.morph_library:
                for idx in self.face_indices:
                    gn.update_morph_data(
                        idx,
                        self.target_slot,
                        self.morph_library[mapped_name]
                    )
                self.current_mapped_name = mapped_name

        self.current_time += dt

        if self.current_time >= event.duration:
            self.current_time = 0.0
            self.current_index += 1

        return {"PHONEME_ACTIVE": 1.0}
