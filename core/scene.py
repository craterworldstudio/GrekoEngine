class UpdateContext:
    def __init__(
            self, 
            gn=None,
            scene=None,
            skeleton=None, 
            animator=None,
            target_index=None):
        
        self.gn = gn
        self.scene = scene
        self.target_index = target_index
        self.animator = animator
        self.skeleton = skeleton

class Scene:
    def __init__(self, context):
        self.entities = []
        self.context = context

    def add(self, entity):
        existing_names = {e.name for e in self.entities}

        base_name = entity.name
        if base_name not in existing_names:
            self.entities.append(entity)
            self.update_list()
            return    
        # Duplicate detected → generate numbered name
        index = 1
        while f"{base_name}{index}" in existing_names:
            index += 1

        entity.name = f"{base_name}{index}"
        print("[!] Duplicate Entity Name. Renaming as ", entity.name)
        self.entities.append(entity)
        self.update_list()

    def rm(self, entity):
        self.entities.remove(entity)
        self.update_list()

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

    def update_list(self):
        entities = self.get_all()
    
        # Send names to C++
        self.context.gn.set_entity_list([e.name for e in entities])
    
        # Build shape descriptor list automatically
        shape_data = []
    
        for index, entity in enumerate(entities):
            mesh = entity.get("mesh")
            if mesh:
                shape_dict = {
                    "type": mesh.shape_type,
                    "entity": index
                }
    
                shape_dict.update(mesh.params)
                shape_data.append(shape_dict)
    
        if shape_data:
            self.context.gn.upload_shapes(shape_data)