"""
基本モック集 - エルダー評議会承認
"""
from unittest.mock import MagicMock, Mock, patch

class MockBaseCommand:
    """BaseCommandモック"""
    def __init__(self):
        self.name = "mock_command"
        self.description = "Mock command"
        
    def execute(self, *args, **kwargs):
        return {"status": "success"}

class MockWorker:
    """基本ワーカーモック"""
    def __init__(self):
        self.is_running = False
        self.name = "mock_worker"
        
    def start(self):
        self.is_running = True
        
    def stop(self):
        self.is_running = False

class MockConnection:
    """接続モック"""
    def __init__(self):
        self.is_open = True
        
    def close(self):
        self.is_open = False

# コマンドモック
StartCommand = MagicMock(spec=MockBaseCommand)
StopCommand = MagicMock(spec=MockBaseCommand)
BaseCommand = MockBaseCommand

# ワーカーモック
TaskWorker = MagicMock(spec=MockWorker)
PMWorker = MagicMock(spec=MockWorker)
ResultWorker = MagicMock(spec=MockWorker)
