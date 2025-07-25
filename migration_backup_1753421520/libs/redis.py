class Redis:
    """Redisクラス"""
    def __init__(self, *args, **kwargs):
        """初期化メソッド"""
        pass

    def get(self, key):
        """getメソッド"""
        return None

    def set(self, key, value):
        """setメソッド"""
        return True

    def pipeline(self):
        """pipelineメソッド"""
        return self

    def execute(self):
        """execute実行メソッド"""
        return []
