#!/usr/bin/env python3
"""
Task Sage Data Models
タスク管理のためのデータモデル定義
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from uuid import uuid4


class TaskStatus(Enum):


"""タスクステータス"""
    """タスク優先度"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    BLOCKER = 5


@dataclass
class TaskSpec:

    """タスク仕様（作成時のパラメータ）""" str
    description: str = ""
    estimated_hours: float = 0.0
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: List[str] = field(default_factory=list)
    project_id: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    complexity_factors: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):

    
    """バリデーション"""
            raise ValueError("タイトルは必須です")
        if self.estimated_hours < 0:
            raise ValueError("見積もり時間は0以上である必要があります")


@dataclass
class Task:

            """タスクエンティティ""" str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Elder Tree拡張
    delegated_to: Optional[str] = None  # 委譲先のServant/Magic
    knowledge_refs: List[str] = field(default_factory=list)  # 関連知識ID
    incident_refs: List[str] = field(default_factory=list)  # 関連インシデントID
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    complexity_factors: Dict[str, Any] = field(default_factory=dict)
    
    # プロジェクト関連
    project_id: Optional[str] = None
    
    @classmethod
    def from_spec(cls, spec: TaskSpec) -> "Task":
        """TaskSpecからTaskを作成"""
        return cls(
            id=str(uuid4()),
            title=spec.title,
            description=spec.description,
            priority=spec.priority,
            assignee=spec.assignee,
            estimated_hours=spec.estimated_hours,
            tags=spec.tags,
            project_id=spec.project_id,
            due_date=spec.due_date,
            dependencies=spec.dependencies,
            complexity_factors=spec.complexity_factors
        )


@dataclass
class TaskUpdate:

        """タスク更新情報""" Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:

    
    """辞書形式に変換（Noneを除外）""" v for k, v in self.__dict__.items() if v is not None}


@dataclass
class EffortEstimate:



"""工数見積もり結果""" float
    confidence: float  # 0.0-1.0
    breakdown: Dict[str, float]
    factors: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):

    
    """バリデーション"""
            raise ValueError("信頼度は0.0から1.0の間である必要があります")
        if self.hours < 0:
            raise ValueError("見積もり時間は0以上である必要があります")


@dataclass
class ProjectSpec:

            """プロジェクト仕様""" str
    description: str = ""
    target_completion: Optional[datetime] = None
    resource_constraints: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):

    
    """バリデーション"""
            raise ValueError("プロジェクト名は必須です")


@dataclass
class Project:

            """プロジェクトエンティティ""" str
    name: str
    description: str = ""
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    target_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    resource_constraints: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    task_ids: List[str] = field(default_factory=list)
    
    @classmethod
    def from_spec(cls, spec: ProjectSpec) -> "Project":
        """ProjectSpecからProjectを作成"""
        return cls(
            id=str(uuid4()),
            name=spec.name,
            description=spec.description,
            target_completion=spec.target_completion,
            resource_constraints=spec.resource_constraints,
            tags=spec.tags
        )


@dataclass
class ProjectPlan:

        """プロジェクト計画""" str
    total_estimated_hours: float
    critical_path: List[str]  # タスクIDのリスト
    milestones: List["Milestone"]
    resource_allocation: Dict[str, float]
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Milestone:



"""マイルストーン""" str
    name: str
    target_date: datetime
    task_ids: List[str]
    status: str = "pending"
    completed_date: Optional[datetime] = None


@dataclass
class ProgressReport:



"""進捗レポート""" str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    completion_percentage: float
    hours_spent: float
    hours_remaining: float
    estimated_completion_date: Optional[datetime] = None
    issues: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def on_track(self) -> bool:

    
    """スケジュール通りかどうか"""
    """依存関係グラフ"""
    nodes: Dict[str, Task]  # task_id -> Task
    edges: Dict[str, List[str]]  # task_id -> [dependent_task_ids]
    
    def get_execution_order(self) -> List[str]:

    
    """実行順序を取得（トポロジカルソート）"""
    """バリデーション結果"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)