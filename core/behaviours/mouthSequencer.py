import time
#import core.greko_native as gn

class MouthSequencer:
    def __init__(self):
        self.phrase = ["Fcl_MTH_A", "Fcl_MTH_E", "Fcl_MTH_I", "Fcl_MTH_O", "Fcl_MTH_U"]
        self.current_index = 0
        self.step_duration = 0.5  # Seconds per vowel
        self.last_step_time = 0
        self.face_index = 0 
        
        # We need access to the full library of morph arrays
        self.morph_library = {} 
        self.target_slot = 2  # We'll use Slot 2 for the 'active' vowel

    def update(self, gn):
        if not self.morph_library or self.face_index == -1:
            return {} # Wait until data is injected
        
        now = time.time()
        
        if now - self.last_step_time > self.step_duration:
            self.last_step_time = now
            
            # 1. Get the name of the next vowel in the sequence
            vowel_name = self.phrase[self.current_index]
            
            # 2. Tell the engine to swap the GPU buffer for the Face mesh (Index 0)
            if vowel_name in self.morph_library:
                # FLAG: Dynamic Swap
                # This pushes the new vertex offsets to the GPU immediately
                gn.update_morph_data(self.face_index, self.target_slot, self.morph_library[vowel_name])
                print(f"👄 Mouth Swapped to: {vowel_name}")

            

            # 3. Increment sequence
            self.current_index = (self.current_index + 1) % len(self.phrase)

        # We return a weight of 1.0 for Slot 2 so the mouth is always 'on'
        return { "PHONEME_ACTIVE": 1.0 }
    
