import random
from direct.task import Task
from direct.task.TaskManagerGlobal import taskMgr
from direct.interval.IntervalGlobal import Sequence, LerpFunc  # <-- This is needed
from vrmmanager.face_loader import FaceMorphController

class HybridBlinker:
    def __init__(self, face_controller):
        self.face = face_controller
        self.blink_name = "Fcl_EYE_Close"  # Both eyes
        self.blink_right = "Fcl_EYE_Close_R"
        self.blink_left = "Fcl_EYE_Close_L"

    def start(self):
        if not self.face:
            print("⚠️ Face controller missing! Blinking disabled.")
            return
        taskMgr.doMethodLater(random.uniform(2, 5), self.blink_task, "blink-task")

    def blink_task(self, task):
        blink_seq = Sequence(
            LerpFunc(lambda v: self.face.set_morph(self.blink_name, v), duration=0.1, fromData=0, toData=1),
            LerpFunc(lambda v: self.face.set_morph(self.blink_name, v), duration=0.1, fromData=1, toData=0)
        )
        blink_seq.start()
        task.delayTime = random.uniform(2, 6)
        return Task.again

