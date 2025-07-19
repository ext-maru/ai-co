"""
統合タスクトラッカー データモデルのテスト (TDD)
"""

import pytest
from datetime import datetime
from typing import Optional
import uuid

# これから実装するモデルをインポート
from libs.unified_task_tracker.models import (
    Task, TaskHistory, TaskDependency,
    TaskStatus, TaskPriority, TaskVisibility,
    ValidationError
)


class TestTaskModel:
    """タスクモデルのテスト"""
    
    def test_create_task_with_minimal_fields(self):
        """最小限のフィールドでタスクを作成"""
        task = Task(
            title="データモデル設計",
            description="統合タスクトラッカーのデータモデルを設計する"
        )
        
        assert task.id is not None
        assert isinstance(task.id, str)
        assert task.title == "データモデル設計"
        assert task.description == "統合タスクトラッカーのデータモデルを設計する"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.visibility == TaskVisibility.PRIVATE
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.github_issue_number is None
    
    def test_create_task_with_all_fields(self):
        """全フィールドを指定してタスクを作成"""
        task_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        task = Task(
            id=task_id,
            title="緊急バグ修正",
            description="認証システムのクリティカルバグ",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            visibility=TaskVisibility.PUBLIC,
            github_issue_number=42,
            assignee="dwarf-workshop",
            labels=["bug", "critical", "auth"],
            estimated_hours=4.5,
            actual_hours=2.0,
            created_at=created_at,
            due_date=datetime(2025, 7, 20, 18, 0, 0)
        )
        
        assert task.id == task_id
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.visibility == TaskVisibility.PUBLIC
        assert task.github_issue_number == 42
        assert task.assignee == "dwarf-workshop"
        assert task.labels == ["bug", "critical", "auth"]
        assert task.estimated_hours == 4.5
        assert task.actual_hours == 2.0
        assert task.created_at == created_at
    
    def test_task_validation_empty_title(self):
        """空のタイトルは検証エラー"""
        with pytest.raises(ValidationError) as exc_info:
            Task(title="", description="説明")
        
        assert "title cannot be empty" in str(exc_info.value)
    
    def test_task_validation_title_too_long(self):
        """長すぎるタイトルは検証エラー"""
        with pytest.raises(ValidationError) as exc_info:
            Task(title="a" * 256, description="説明")
        
        assert "title must be 255 characters or less" in str(exc_info.value)
    
    def test_task_validation_negative_hours(self):
        """負の時間は検証エラー"""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                title="タスク",
                description="説明",
                estimated_hours=-1.0
            )
        
        assert "estimated_hours cannot be negative" in str(exc_info.value)
    
    def test_task_update(self):
        """タスクの更新"""
        task = Task(title="元のタイトル", description="元の説明")
        original_created_at = task.created_at
        original_updated_at = task.updated_at
        
        # 少し待機して時間差を作る
        import time
        time.sleep(0.01)
        
        task.update(
            title="更新されたタイトル",
            status=TaskStatus.COMPLETED,
            actual_hours=3.5
        )
        
        assert task.title == "更新されたタイトル"
        assert task.status == TaskStatus.COMPLETED
        assert task.actual_hours == 3.5
        assert task.created_at == original_created_at
        assert task.updated_at > original_updated_at
    
    def test_task_to_dict(self):
        """タスクの辞書変換"""
        task = Task(
            title="テストタスク",
            description="辞書変換のテスト",
            labels=["test", "unit-test"]
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["id"] == task.id
        assert task_dict["title"] == "テストタスク"
        assert task_dict["description"] == "辞書変換のテスト"
        assert task_dict["status"] == "pending"
        assert task_dict["priority"] == "medium"
        assert task_dict["visibility"] == "private"
        assert task_dict["labels"] == ["test", "unit-test"]
        assert "created_at" in task_dict
        assert "updated_at" in task_dict
    
    def test_task_from_dict(self):
        """辞書からタスクを作成"""
        data = {
            "id": "test-123",
            "title": "復元タスク",
            "description": "辞書から復元",
            "status": "in_progress",
            "priority": "high",
            "visibility": "public",
            "github_issue_number": 123,
            "labels": ["restored"],
            "created_at": "2025-07-19T12:00:00",
            "updated_at": "2025-07-19T13:00:00"
        }
        
        task = Task.from_dict(data)
        
        assert task.id == "test-123"
        assert task.title == "復元タスク"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.visibility == TaskVisibility.PUBLIC
        assert task.github_issue_number == 123


class TestTaskHistoryModel:
    """タスク履歴モデルのテスト"""
    
    def test_create_task_history(self):
        """タスク履歴の作成"""
        history = TaskHistory(
            task_id="task-123",
            field_name="status",
            old_value="pending",
            new_value="in_progress",
            changed_by="claude-elder"
        )
        
        assert history.id is not None
        assert history.task_id == "task-123"
        assert history.field_name == "status"
        assert history.old_value == "pending"
        assert history.new_value == "in_progress"
        assert history.changed_by == "claude-elder"
        assert history.changed_at is not None
    
    def test_task_history_with_none_values(self):
        """None値を含む履歴"""
        history = TaskHistory(
            task_id="task-456",
            field_name="assignee",
            old_value=None,
            new_value="dwarf-workshop",
            changed_by="task-sage"
        )
        
        assert history.old_value is None
        assert history.new_value == "dwarf-workshop"
    
    def test_task_history_to_dict(self):
        """履歴の辞書変換"""
        history = TaskHistory(
            task_id="task-789",
            field_name="priority",
            old_value="medium",
            new_value="high",
            changed_by="incident-sage",
            comment="緊急度が上がったため"
        )
        
        history_dict = history.to_dict()
        
        assert history_dict["task_id"] == "task-789"
        assert history_dict["field_name"] == "priority"
        assert history_dict["old_value"] == "medium"
        assert history_dict["new_value"] == "high"
        assert history_dict["changed_by"] == "incident-sage"
        assert history_dict["comment"] == "緊急度が上がったため"


class TestTaskDependencyModel:
    """タスク依存関係モデルのテスト"""
    
    def test_create_task_dependency(self):
        """タスク依存関係の作成"""
        dependency = TaskDependency(
            task_id="task-child",
            depends_on_task_id="task-parent",
            dependency_type="blocks"
        )
        
        assert dependency.id is not None
        assert dependency.task_id == "task-child"
        assert dependency.depends_on_task_id == "task-parent"
        assert dependency.dependency_type == "blocks"
        assert dependency.created_at is not None
    
    def test_dependency_validation_same_task(self):
        """同じタスクへの依存は検証エラー"""
        with pytest.raises(ValidationError) as exc_info:
            TaskDependency(
                task_id="task-123",
                depends_on_task_id="task-123",
                dependency_type="blocks"
            )
        
        assert "cannot depend on itself" in str(exc_info.value)
    
    def test_dependency_validation_invalid_type(self):
        """無効な依存タイプは検証エラー"""
        with pytest.raises(ValidationError) as exc_info:
            TaskDependency(
                task_id="task-123",
                depends_on_task_id="task-456",
                dependency_type="invalid"
            )
        
        assert "invalid dependency_type" in str(exc_info.value)
    
    def test_dependency_to_dict(self):
        """依存関係の辞書変換"""
        dependency = TaskDependency(
            task_id="task-abc",
            depends_on_task_id="task-xyz",
            dependency_type="requires"
        )
        
        dep_dict = dependency.to_dict()
        
        assert dep_dict["task_id"] == "task-abc"
        assert dep_dict["depends_on_task_id"] == "task-xyz"
        assert dep_dict["dependency_type"] == "requires"


class TestTaskStatusEnum:
    """タスクステータス列挙型のテスト"""
    
    def test_status_values(self):
        """ステータス値の確認"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.ON_HOLD.value == "on_hold"
    
    def test_status_from_string(self):
        """文字列からステータスを取得"""
        assert TaskStatus.from_string("pending") == TaskStatus.PENDING
        assert TaskStatus.from_string("in_progress") == TaskStatus.IN_PROGRESS
        assert TaskStatus.from_string("completed") == TaskStatus.COMPLETED
    
    def test_status_from_invalid_string(self):
        """無効な文字列はエラー"""
        with pytest.raises(ValueError):
            TaskStatus.from_string("invalid_status")


class TestTaskPriorityEnum:
    """タスク優先度列挙型のテスト"""
    
    def test_priority_values(self):
        """優先度値の確認"""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.URGENT.value == "urgent"
    
    def test_priority_numeric_values(self):
        """優先度の数値表現"""
        assert TaskPriority.LOW.numeric_value == 1
        assert TaskPriority.MEDIUM.numeric_value == 2
        assert TaskPriority.HIGH.numeric_value == 3
        assert TaskPriority.URGENT.numeric_value == 4
    
    def test_priority_comparison(self):
        """優先度の比較"""
        assert TaskPriority.URGENT.numeric_value > TaskPriority.HIGH.numeric_value
        assert TaskPriority.HIGH.numeric_value > TaskPriority.MEDIUM.numeric_value
        assert TaskPriority.MEDIUM.numeric_value > TaskPriority.LOW.numeric_value