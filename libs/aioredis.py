class Redis:
    """Redisクラス"""
    def __init__(self, *args, **kwargs):
        """初期化メソッド"""
        pass

    async def get(self, key):
        """getメソッド"""
        return None

    async def set(self, key, value):
        """setメソッド"""
        return True


async def create_redis(*args, **kwargs):
    """redis作成メソッド"""
    return Redis()


from_url = create_redis
