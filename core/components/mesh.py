class MeshComponent:
    def __init__(self, shape_type, **kwargs):
        self.owner = None
        self.shape_type = shape_type
        self.params = kwargs