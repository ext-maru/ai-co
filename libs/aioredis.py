class Redis:
    def __init__(self, *args, **kwargs): pass
    async def get(self, key): return None
    async def set(self, key, value): return True
async def create_redis(*args, **kwargs): return Redis()
from_url = create_redis
