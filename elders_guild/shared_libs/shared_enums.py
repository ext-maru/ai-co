"""
Shared Enums - 共有列挙型定義
"""

from enum import Enum


class Priority(Enum):
    """Priorityクラス"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(Enum):
    """Statusクラス"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(Enum):
    """TaskTypeクラス"""

    FEATURE = "feature"

    ENHANCEMENT = "enhancement"
    MAINTENANCE = "maintenance"
