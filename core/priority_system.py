"""優先度システム"""

class PriorityMixin:
    """優先度管理のMixin"""
    
    def __init__(self):
        self.priority_levels = {
            'critical': 10,
            'high': 7,
            'normal': 5,
            'low': 3
        }
    
    def get_priority(self, level='normal'):
        """優先度レベルを取得"""
        return self.priority_levels.get(level, 5)
    
    def setup_priority_consumer(self):
        """優先度ベースのコンシューマー設定"""
        # 実装はワーカーに委譲
        pass

from enum import Enum

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 10
    HIGH = 7
    NORMAL = 5
    LOW = 3

__all__ = ["PriorityMixin", "TaskPriority"]

from enum import Enum

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 10
    HIGH = 7
    NORMAL = 5
    LOW = 3

__all__ = ["PriorityMixin", "TaskPriority"]

from enum import Enum

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 10
    HIGH = 7
    NORMAL = 5
    LOW = 3

__all__ = ["PriorityMixin", "TaskPriority"]

from core import BaseWorker

class PriorityAwareBaseWorker(BaseWorker):
    """Base worker with priority support"""
    def __init__(self, worker_type, worker_id=None):
        super().__init__(worker_type, worker_id)
        self.priority_enabled = True
    
    def process_by_priority(self, messages):
        """Process messages by priority"""
        return sorted(messages, key=lambda x: x.get("priority", 5), reverse=True)
