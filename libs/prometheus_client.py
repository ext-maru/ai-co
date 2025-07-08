class Counter:
    def __init__(self, *args, **kwargs): pass
    def inc(self, amount=1): pass
    def labels(self, **kwargs): return self
class Histogram:
    def __init__(self, *args, **kwargs): pass
    def observe(self, value): pass
    def labels(self, **kwargs): return self
class Gauge:
    def __init__(self, *args, **kwargs): pass
    def set(self, value): pass
    def labels(self, **kwargs): return self
