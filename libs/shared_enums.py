"""
Shared Enums - 共有列挙型定義
"""

from enum import Enum

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Status(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(Enum):
    FEATURE = "feature"
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    MAINTENANCE = "maintenance"
