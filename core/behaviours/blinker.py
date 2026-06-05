import time
import math

from core.BehaviourBaseClasses import BehaviorBase

class Blinker(BehaviorBase):
    def __init__(self):
        # Native VRM Names
        self.target_name = "Fcl_EYE_Close"  
        self.blink_right = "Fcl_EYE_Close_R"
        self.blink_left = "Fcl_EYE_Close_L"
        
        self.strength = 1.0 
        self.interval = 4.0
        self.blink_duration = 0.5 #inversely proportional to blink speed

    def setup(self, skeleton, gn, vrm_version=2):
        self.gn = gn
        print(f"[Blinker] Detected VRM version: {vrm_version}")
        # Define naming keys based on version specification
        if vrm_version == 1:
            self.target_name = "Fcl_EYE_Close"
            self.blink_right = "Fcl_EYE_Close_R"
            self.blink_left  = "Fcl_EYE_Close_L"
        if vrm_version == 0:
            self.target_name = "blink"
            self.blink_right = "blink_r"
            self.blink_left  = "blink_l"


    def update(self, gn):
        """Calculates a natural-ish blink timing and returns weights"""
        t = time.time()
        weight = 0.0
        
        # Logic: If we are in the first 0.2s of our interval, blink!
        cycle_pos = t % self.interval
        if cycle_pos < self.blink_duration:
            # FLAG: Smooth Animation
            # Sine creates a smooth 'in and out' so the eyelids don't pop
            weight = math.sin((cycle_pos / self.blink_duration) * math.pi) * self.strength
        
        # Return a dictionary of weights
        # This allows one behavior to control multiple facial expressions at once
        return { self.target_name: weight }
        #return {
        #    self.target_name: weight,
        #    self.blink_right: weight,
        #    self.blink_left: weight
        #}