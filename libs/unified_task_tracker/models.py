"""
統合タスクトラッカー データモデル

Domain-Driven Design (DDD) アプローチによるエンティティ定義
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field


class ValidationError(Exception):
    """バリデーションエラー"""
    pass


class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """タスク優先度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskVisibility(Enum):
    """タスク可視性"""
    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


@dataclass
class Task:
    """
    タスクエンティティ
    
    統合タスクトラッカーの中核エンティティ
    """
    
    # 必須フィールド
    title: str
    description: str
    
    # 自動生成フィールド
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # デフォルト値を持つフィールド
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    visibility: TaskVisibility = TaskVisibility.PRIVATE
    progress: int = 0
    
    # オプショナルフィールド
    assignee: Optional[str] = None
    creator: Optional[str] = None
    parent_task_id: Optional[str] = None
    
    # GitHub連携
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None
    
    # 時間管理
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    
    # メタデータ
    labels: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化後のバリデーション"""
        self._validate()
    
    def _validate(self):
        """バリデーション実行"""
        # タイトル検証
        if not self.title or not self.title.strip():
            raise ValidationError("title cannot be empty")
        
        if len(self.title) > 255:
            raise ValidationError("title must be 255 characters or less")
        
        # 時間検証
        if self.estimated_hours is not None and self.estimated_hours < 0:
            raise ValidationError("estimated_hours cannot be negative")
        
        if self.actual_hours is not None and self.actual_hours < 0:
            raise ValidationError("actual_hours cannot be negative")
        
        # 進捗検証
        if not (0 <= self.progress <= 100):
            raise ValidationError("progress must be between 0 and 100")
    
    def update(self, **kwargs):
        """タスクの更新"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.now()
        self._validate()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "visibility": self.visibility.value,
            "assignee": self.assignee,
            "creator": self.creator,
            "parent_task_id": self.parent_task_id,
            "github_issue_number": self.github_issue_number,
            "github_issue_url": self.github_issue_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "progress": self.progress,
            "labels": self.labels.copy(),
            "tags": self.tags.copy(),
            "metadata": self.metadata.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """辞書からタスクを作成"""
        # Enum値の変換
        if "status" in data and isinstance(data["status"], str):
            data["status"] = TaskStatus(data["status"])
        
        if "priority" in data and isinstance(data["priority"], str):
            data["priority"] = TaskPriority(data["priority"])
        
        if "visibility" in data and isinstance(data["visibility"], str):
            data["visibility"] = TaskVisibility(data["visibility"])
        
        # 日時の変換
        for date_field in ["created_at", "updated_at", "due_date", "completed_at"]:
            if data.get(date_field) and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        # リストとdictのデフォルト値
        data.setdefault("labels", [])
        data.setdefault("tags", [])
        data.setdefault("metadata", {})
        
        return cls(**data)


@dataclass
class TaskHistory:
    """
    タスク履歴エンティティ
    
    タスクの変更履歴を記録
    """
    
    task_id: str
    field_name: str
    new_value: str
    changed_by: str
    
    # 自動生成フィールド
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    changed_at: datetime = field(default_factory=datetime.now)
    
    # オプショナル
    old_value: Optional[str] = None
    comment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "comment": self.comment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskHistory':
        """辞書から履歴を作成"""
        if data.get("changed_at") and isinstance(data["changed_at"], str):
            data["changed_at"] = datetime.fromisoformat(data["changed_at"])
        
        return cls(**data)


@dataclass
class TaskDependency:
    """
    タスク依存関係エンティティ
    
    タスク間の依存関係を定義
    """
    
    task_id: str
    depends_on_task_id: str
    dependency_type: str  # "requires", "blocks", "relates_to"
    
    # 自動生成フィールド
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初期化後のバリデーション"""
        # 自己依存の防止
        if self.task_id == self.depends_on_task_id:
            raise ValidationError("Task cannot depend on itself")
        
        # 依存関係タイプの検証
        valid_types = ["requires", "blocks", "relates_to"]
        if self.dependency_type not in valid_types:
            raise ValidationError(f"dependency_type must be one of {valid_types}")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "depends_on_task_id": self.depends_on_task_id,
            "dependency_type": self.dependency_type,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskDependency':
        """辞書から依存関係を作成"""
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        return cls(**data)