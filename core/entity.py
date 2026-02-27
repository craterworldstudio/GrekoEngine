class Entity:
    def __init__(self, name):
        self.name = name
        self.components = {}

    def add_component(self, name, component):
        self.components[name] = component

    def get(self, name):
        return self.components.get(name) if not None else None

    def has(self, name):
        return name in self.components

    def update(self, dt, context):
        for component in self.components.values():
            if hasattr(component, "update"):
                component.update(dt, context)