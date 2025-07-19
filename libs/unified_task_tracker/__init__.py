"""
統合タスクトラッカー (Unified Task Tracker)

エルダーズギルド統合タスク管理システム
"""

from .models import (
    Task, TaskHistory, TaskDependency,
    TaskStatus, TaskPriority, TaskVisibility,
    ValidationError
)

from .database import (
    TaskDatabase, TaskRepository, TaskHistoryRepository, TaskDependencyRepository,
    DatabaseError
)

__version__ = "1.0.0"
__author__ = "クロードエルダー (Claude Elder)"

__all__ = [
    # Models
    "Task",
    "TaskHistory", 
    "TaskDependency",
    "TaskStatus",
    "TaskPriority",
    "TaskVisibility",
    "ValidationError",
    
    # Database
    "TaskDatabase",
    "TaskRepository",
    "TaskHistoryRepository",
    "TaskDependencyRepository",
    "DatabaseError",
]