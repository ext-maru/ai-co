"""
BaseWorker - Elders Guild Integration

既存のcore.base_workerから実装をインポート
"""

# 既存実装からインポート
from core.base_worker import BaseWorker


# 互換性のための関数
def setup(*args, **kwargs):
    """セットアップ関数"""
    return BaseWorker


def main(*args, **kwargs):
    """メイン関数"""
    return BaseWorker


# Export
__all__ = ["BaseWorker", "setup", "main"]
