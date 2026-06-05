import time
import math

from core.BehaviourBaseClasses import BehaviorBase

class Breather(BehaviorBase):
    def __init__(self):
        # We'll use the Surprise morph for a subtle chest/face expansion
        #self.target_name = "Fcl_ALL_Surprised" 
        pass

    def setup(self, skeleton, gn, vrm_version=2):
        self.gn = gn

        print(f"[Breather] Detected VRM version: {vrm_version}")
        if vrm_version == 1:
            self.target_name = "Fcl_ALL_Surprised" 
        if vrm_version == 0:
            # Fall back to a minor mix of 'fun' or 'joy' for VRM0 expansion layout
            self.target_name = "fun"



    def update(self, gn):
        t = time.time()
        # Slow, rhythmic breathing cycle (roughly 3 seconds)
        # We keep the weight very low (0.05) for a subtle "alive" look
        weight = (math.sin(t * 2.0) + 1.0) * 0.5 * 0.05
        return { self.target_name: weight }