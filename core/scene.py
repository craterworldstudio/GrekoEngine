class UpdateContext:
    def __init__(
            self, 
            gn=None, 
            skeleton=None, 
            animator=None,
            target=None):
        
        self.gn = gn
        self.target = target
        self.animator = animator
        self.skeleton = skeleton

class Scene:
    def __init__(self):
        self.entities = []

    def add(self, entity):
        self.entities.append(entity)

    def get_all(self):
        return self.entities

    def find(self, name):
        for e in self.entities:
            if e.name == name:
                return e
        return None
    
    def update(self, dt, context):
        for entity in self.entities:
            entity.update(dt, context)