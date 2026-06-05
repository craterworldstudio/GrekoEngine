class SkeletonBehaviorBase:
    
    def setup(self, *args, **kwargs): pass
    def update(self, *args, **kwargs): pass

class BehaviorBase:
    def setup(self, *args, **kwargs): pass
    def update(self, *args, **kwargs) -> dict[str, float]: return {"": 0.0}