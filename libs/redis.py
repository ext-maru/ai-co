class Redis:
    def __init__(self, *args, **kwargs): pass
    def get(self, key): return None
    def set(self, key, value): return True
    def pipeline(self): return self
    def execute(self): return []
