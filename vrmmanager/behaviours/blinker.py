import random
from direct.task.TaskManagerGlobal import taskMgr
from direct.task import Task
from direct.interval.IntervalGlobal import Sequence, LerpFunc
from panda3d.core import Character

class Blinker:
    def __init__(self, char_entity):
        self.char = char_entity
        self.model = char_entity.model
        self.bundle = None
        
        # FLAG: Safe Bundle Search
        # We look specifically for the Character bundle that holds blendshapes.
        char_nodes = self.model.find_all_matches("**/+Character")
        if char_nodes:
            # We store the bundle directly to avoid 'None' attribute errors.
            self.bundle = char_nodes[0].node().get_bundle(0)
            print(f"👁️  Blinker: Linked to {self.char.name}'s blendshapes.")

    def start(self):
        if not self.bundle:
            print("⚠️  Blinker: No blendshapes found. Blinking disabled.")
            return
            
        # FLAG: Use taskMgr directly
        # Instead of 'base.taskMgr', we use the global taskMgr to avoid 'Undefined' errors.
        taskMgr.doMethodLater(random.uniform(2, 5), self.blink_task, f"blink-{self.char.name}")

    def blink_task(self, task):
        blink_seq = Sequence(
            LerpFunc(self.set_blink_value, duration=0.1, fromData=0, toData=1),
            LerpFunc(self.set_blink_value, duration=0.1, fromData=1, toData=0)
        )
        blink_seq.start()
        
        task.delayTime = random.uniform(2, 6)
        return Task.again

    def set_blink_value(self, val):
        # FLAG: set_control_effect
        # VRoid models usually use 'Blink' or 'EyeBlink'. 
        # We check if it exists before setting to prevent crashes.
        if self.bundle:
            self.bundle.set_control_effect("Blink", val)