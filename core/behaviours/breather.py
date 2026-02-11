import time
import math

class Breather:
    def __init__(self):
        # We'll use the Surprise morph for a subtle chest/face expansion
        self.target_name = "Fcl_ALL_Surprised" 

    def update(self):
        t = time.time()
        # Slow, rhythmic breathing cycle (roughly 3 seconds)
        # We keep the weight very low (0.05) for a subtle "alive" look
        weight = (math.sin(t * 2.0) + 1.0) * 0.5 * 0.05
        return { self.target_name: weight }