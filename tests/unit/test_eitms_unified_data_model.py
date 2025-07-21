#!/usr/bin/env python3
"""
EITMS統一データモデル - テストスイート

TDD原則に基づくテスト実装
- Red: 失敗するテストを先に書く
- Green: 最小限の実装でテストを通す  
- Refactor: コードを改善する

Author: クロードエルダー（Claude Elder）
Created: 2025/07/21
"""

import asyncio
import json
import pytest
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# テスト対象のモジュールをインポート
import sys
sys.path.append('/home/aicompany/ai_co')

from libs.eitms_unified_data_model import (
    UnifiedTask,
    TaskType,
    TaskStatus,
    Priority,
    SystemSync,
    EitmsUnifiedDatabase,
    EitmsUnifiedManager
)


class TestUnifiedTask:
    """UnifiedTaskクラスのテスト"""
    
    def test_unified_task_creation_with_defaults(self):
        """デフォルト値でのタスク作成テスト"""
        task = UnifiedTask()
        
        assert task.id is not None
        assert len(task.id) > 0
        assert task.title == ""
        assert task.description == ""
        assert task.task_type == TaskType.TODO
        assert task.status == TaskStatus.CREATED
        assert task.priority == Priority.MEDIUM
        assert task.assignee == "claude_elder"
        assert task.created_by == "claude_elder"
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)
        assert task.dependencies == []
        assert task.sub_tasks == []
        assert task.tags == []
        assert task.context == {}
        assert task.session_data == {}
    
    def test_unified_task_creation_with_parameters(self):
        """パラメータ指定でのタスク作成テスト"""
        task = UnifiedTask(
            title="テストタスク",
            description="テスト用タスクです",
            task_type=TaskType.PROJECT_TASK,
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            assignee="test_user",
            tags=["test", "development"],
            context={"project": "eitms"}
        )
        
        assert task.title == "テストタスク"
        assert task.description == "テスト用タスクです"
        assert task.task_type == TaskType.PROJECT_TASK
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == Priority.HIGH
        assert task.assignee == "test_user"
        assert task.tags == ["test", "development"]
        assert task.context == {"project": "eitms"}
    
    def test_unified_task_to_dict(self):
        """タスクの辞書変換テスト"""
        task = UnifiedTask(
            title="辞書テスト",
            description="辞書変換のテスト",
            task_type=TaskType.ISSUE,
            priority=Priority.CRITICAL,
            tags=["dict", "test"],
            github_issue_number=123
        )
        
        task_dict = task.to_dict()
        
        assert isinstance(task_dict, dict)
        assert task_dict['title'] == "辞書テスト"
        assert task_dict['description'] == "辞書変換のテスト"
        assert task_dict['task_type'] == "issue"
        assert task_dict['priority'] == "critical"
        assert task_dict['tags'] == ["dict", "test"]
        assert task_dict['github_issue_number'] == 123
        assert 'id' in task_dict
        assert 'created_at' in task_dict
        assert 'updated_at' in task_dict
    
    def test_unified_task_from_dict(self):
        """辞書からのタスク復元テスト"""
        data = {
            'id': 'test-id-123',
            'title': '復元テスト',
            'description': '辞書からの復元テスト',
            'task_type': 'project_task',
            'status': 'in_progress',
            'priority': 'high',
            'created_at': '2025-07-21T10:00:00+00:00',
            'updated_at': '2025-07-21T11:00:00+00:00',
            'tags': ['restore', 'test'],
            'github_issue_number': 456,
            'assignee': 'test_assignee',
            'context': {'env': 'test'}
        }
        
        task = UnifiedTask.from_dict(data)
        
        assert task.id == 'test-id-123'
        assert task.title == '復元テスト'
        assert task.description == '辞書からの復元テスト'
        assert task.task_type == TaskType.PROJECT_TASK
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == Priority.HIGH
        assert task.tags == ['restore', 'test']
        assert task.github_issue_number == 456
        assert task.assignee == 'test_assignee'
        assert task.context == {'env': 'test'}
    
    def test_unified_task_enum_validation(self):
        """Enum値の検証テスト"""
        # 正常なEnum値
        task = UnifiedTask(
            task_type=TaskType.PLANNING,
            status=TaskStatus.BLOCKED,
            priority=Priority.LOW
        )
        
        assert task.task_type == TaskType.PLANNING
        assert task.status == TaskStatus.BLOCKED
        assert task.priority == Priority.LOW
    
    def test_unified_task_time_handling(self):
        """時間データの処理テスト"""
        now = datetime.now(timezone.utc)
        task = UnifiedTask()
        
        # 作成時刻が自動設定される
        assert abs((task.created_at - now).total_seconds()) < 1
        assert abs((task.updated_at - now).total_seconds()) < 1
        
        # 開始・完了時刻は初期状態ではNone
        assert task.started_at is None
        assert task.completed_at is None


class TestSystemSync:
    """SystemSyncクラスのテスト"""
    
    def test_system_sync_creation(self):
        """SystemSync作成テスト"""
        sync = SystemSync(task_id="test-task-123")
        
        assert sync.task_id == "test-task-123"
        assert sync.todo_synced is False
        assert sync.issue_synced is False
        assert sync.tracker_synced is False
        assert sync.planning_synced is False
        assert isinstance(sync.last_sync, datetime)
        assert sync.sync_errors == []
    
    def test_system_sync_to_dict(self):
        """SystemSync辞書変換テスト"""
        sync = SystemSync(
            task_id="dict-test-456",
            todo_synced=True,
            issue_synced=True,
            sync_errors=["error1", "error2"]
        )
        
        sync_dict = sync.to_dict()
        
        assert sync_dict['task_id'] == "dict-test-456"
        assert sync_dict['todo_synced'] is True
        assert sync_dict['issue_synced'] is True
        assert sync_dict['tracker_synced'] is False
        assert sync_dict['planning_synced'] is False
        assert sync_dict['sync_errors'] == ["error1", "error2"]
        assert 'last_sync' in sync_dict


@pytest.mark.asyncio
class TestEitmsUnifiedDatabase:
    """EitmsUnifiedDatabaseクラスのテスト"""
    
    async def test_database_initialization(self):
        """データベース初期化テスト"""
        # 一時ファイルでテスト
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = EitmsUnifiedDatabase(db_path)
            await db.initialize()
            
            # データベースファイルが作成される
            assert Path(db_path).exists()
            
            # 接続が確立される
            assert db._connection is not None
            
            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_database_save_and_get_task(self):
        """タスク保存・取得テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = EitmsUnifiedDatabase(db_path)
            await db.initialize()
            
            # タスク作成
            task = UnifiedTask(
                title="データベーステスト",
                description="保存・取得のテスト",
                task_type=TaskType.PROJECT_TASK,
                priority=Priority.HIGH,
                tags=["db", "test"],
                context={"test": True}
            )
            
            # 保存
            success = await db.save_task(task)
            assert success is True
            
            # 取得
            retrieved_task = await db.get_task(task.id)
            assert retrieved_task is not None
            assert retrieved_task.id == task.id
            assert retrieved_task.title == "データベーステスト"
            assert retrieved_task.description == "保存・取得のテスト"
            assert retrieved_task.task_type == TaskType.PROJECT_TASK
            assert retrieved_task.priority == Priority.HIGH
            assert retrieved_task.tags == ["db", "test"]
            assert retrieved_task.context == {"test": True}
            
            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_database_list_tasks(self):
        """タスク一覧取得テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = EitmsUnifiedDatabase(db_path)
            await db.initialize()
            
            # 複数タスク作成
            tasks = [
                UnifiedTask(title=f"タスク{i}", task_type=TaskType.TODO, 
                           status=TaskStatus.CREATED if i % 2 == 0 else TaskStatus.COMPLETED)
                for i in range(5)
            ]
            
            # 保存
            for task in tasks:
                await db.save_task(task)
            
            # 全件取得
            all_tasks = await db.list_tasks()
            assert len(all_tasks) == 5
            
            # タスク種別フィルター
            todo_tasks = await db.list_tasks(task_type=TaskType.TODO)
            assert len(todo_tasks) == 5
            
            # ステータスフィルター
            created_tasks = await db.list_tasks(status=TaskStatus.CREATED)
            assert len(created_tasks) == 3  # 0, 2, 4番目
            
            completed_tasks = await db.list_tasks(status=TaskStatus.COMPLETED)
            assert len(completed_tasks) == 2  # 1, 3番目
            
            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_database_delete_task(self):
        """タスク削除テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = EitmsUnifiedDatabase(db_path)
            await db.initialize()
            
            # タスク作成・保存
            task = UnifiedTask(title="削除テスト")
            await db.save_task(task)
            
            # 存在確認
            retrieved = await db.get_task(task.id)
            assert retrieved is not None
            
            # 削除
            success = await db.delete_task(task.id)
            assert success is True
            
            # 削除確認
            deleted_task = await db.get_task(task.id)
            assert deleted_task is None
            
            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_database_get_stats(self):
        """統計取得テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = EitmsUnifiedDatabase(db_path)
            await db.initialize()
            
            # テストデータ作成
            tasks = [
                UnifiedTask(title="TODO1", task_type=TaskType.TODO, status=TaskStatus.CREATED),
                UnifiedTask(title="TODO2", task_type=TaskType.TODO, status=TaskStatus.COMPLETED),
                UnifiedTask(title="ISSUE1", task_type=TaskType.ISSUE, status=TaskStatus.IN_PROGRESS),
                UnifiedTask(title="PROJECT1", task_type=TaskType.PROJECT_TASK, status=TaskStatus.CREATED)
            ]
            
            for task in tasks:
                await db.save_task(task)
            
            # 統計取得
            stats = await db.get_stats()
            
            assert stats['total_tasks'] == 4
            assert stats['task_type_distribution']['todo'] == 2
            assert stats['task_type_distribution']['issue'] == 1  
            assert stats['task_type_distribution']['project_task'] == 1
            assert stats['status_distribution']['created'] == 2
            assert stats['status_distribution']['completed'] == 1
            assert stats['status_distribution']['in_progress'] == 1
            assert 'generated_at' in stats
            
            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


@pytest.mark.asyncio
class TestEitmsUnifiedManager:
    """EitmsUnifiedManagerクラスのテスト"""
    
    async def test_manager_initialization(self):
        """マネージャー初期化テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = EitmsUnifiedManager(db_path)
            await manager.initialize()
            
            # データベースが初期化されている
            assert manager.db._connection is not None
            
            manager.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_manager_create_task(self):
        """タスク作成テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = EitmsUnifiedManager(db_path)
            await manager.initialize()
            
            # タスク作成
            task_id = await manager.create_task(
                title="マネージャーテスト",
                description="マネージャーでのタスク作成テスト",
                task_type=TaskType.ISSUE,
                priority=Priority.CRITICAL
            )
            
            assert task_id != ""
            assert len(task_id) > 0
            
            # 作成されたタスクを取得して確認
            task = await manager.db.get_task(task_id)
            assert task is not None
            assert task.title == "マネージャーテスト"
            assert task.task_type == TaskType.ISSUE
            assert task.priority == Priority.CRITICAL
            
            manager.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_manager_update_task_status(self):
        """タスクステータス更新テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = EitmsUnifiedManager(db_path)
            await manager.initialize()
            
            # タスク作成
            task_id = await manager.create_task(
                title="ステータステスト",
                description="ステータス更新のテスト"
            )
            
            # ステータス更新: IN_PROGRESS
            success = await manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
            assert success is True
            
            task = await manager.db.get_task(task_id)
            assert task.status == TaskStatus.IN_PROGRESS
            assert task.started_at is not None
            
            # ステータス更新: COMPLETED
            success = await manager.update_task_status(task_id, TaskStatus.COMPLETED)
            assert success is True
            
            task = await manager.db.get_task(task_id)
            assert task.status == TaskStatus.COMPLETED
            assert task.completed_at is not None
            
            manager.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_manager_link_github_issue(self):
        """GitHub Issue連携テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = EitmsUnifiedManager(db_path)
            await manager.initialize()
            
            # タスク作成
            task_id = await manager.create_task(title="GitHub連携テスト")
            
            # GitHub Issue連携
            success = await manager.link_github_issue(task_id, 123)
            assert success is True
            
            # 確認
            task = await manager.db.get_task(task_id)
            assert task.github_issue_number == 123
            
            manager.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_manager_link_planning_doc(self):
        """計画書連携テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = EitmsUnifiedManager(db_path)
            await manager.initialize()
            
            # タスク作成
            task_id = await manager.create_task(title="計画書連携テスト")
            
            # 計画書連携
            doc_path = "/docs/plans/test_plan.md"
            success = await manager.link_planning_doc(task_id, doc_path)
            assert success is True
            
            # 確認
            task = await manager.db.get_task(task_id)
            assert task.planning_doc_path == doc_path
            
            manager.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    async def test_manager_get_dashboard_data(self):
        """ダッシュボードデータ取得テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = EitmsUnifiedManager(db_path)
            await manager.initialize()
            
            # テストデータ作成
            await manager.create_task("進行中1", task_type=TaskType.PROJECT_TASK)
            task_id = await manager.create_task("進行中2", task_type=TaskType.PROJECT_TASK)
            await manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
            
            await manager.create_task("TODO1", task_type=TaskType.TODO)
            await manager.create_task("TODO2", task_type=TaskType.TODO)
            
            # ダッシュボードデータ取得
            dashboard = await manager.get_dashboard_data()
            
            assert 'stats' in dashboard
            assert 'in_progress_tasks' in dashboard
            assert 'today_todos' in dashboard
            
            # 統計データ確認
            assert dashboard['stats']['total_tasks'] == 4
            
            # 進行中タスク確認 (1件)
            assert len(dashboard['in_progress_tasks']) == 1
            assert dashboard['in_progress_tasks'][0]['title'] == "進行中2"
            
            # TODOタスク確認 (2件作成したが、1つは進行中に変更したので実際は3件)
            assert len(dashboard['today_todos']) >= 2
            
            manager.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestTaskTypeEnum:
    """TaskType Enumのテスト"""
    
    def test_task_type_values(self):
        """TaskType値のテスト"""
        assert TaskType.TODO.value == "todo"
        assert TaskType.PROJECT_TASK.value == "project_task"
        assert TaskType.ISSUE.value == "issue"
        assert TaskType.PLANNING.value == "planning"
    
    def test_task_type_from_string(self):
        """文字列からのTaskType変換テスト"""
        assert TaskType("todo") == TaskType.TODO
        assert TaskType("project_task") == TaskType.PROJECT_TASK
        assert TaskType("issue") == TaskType.ISSUE
        assert TaskType("planning") == TaskType.PLANNING


class TestTaskStatusEnum:
    """TaskStatus Enumのテスト"""
    
    def test_task_status_values(self):
        """TaskStatus値のテスト"""
        assert TaskStatus.DRAFT.value == "draft"
        assert TaskStatus.CREATED.value == "created"
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.FAILED.value == "failed"


class TestPriorityEnum:
    """Priority Enumのテスト"""
    
    def test_priority_values(self):
        """Priority値のテスト"""
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"


# 統合テスト
@pytest.mark.asyncio
class TestEitmsIntegration:
    """EITMS統合テスト"""
    
    async def test_full_workflow(self):
        """完全ワークフローテスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = EitmsUnifiedManager(db_path)
            await manager.initialize()
            
            # 1. 計画タスク作成
            planning_id = await manager.create_task(
                title="新機能設計書作成",
                description="新機能のアーキテクチャ設計",
                task_type=TaskType.PLANNING,
                priority=Priority.HIGH
            )
            
            # 2. Issue作成（計画から派生）
            issue_id = await manager.create_task(
                title="新機能実装",
                description="設計に基づく実装",
                task_type=TaskType.ISSUE,
                priority=Priority.HIGH
            )
            await manager.link_github_issue(issue_id, 456)
            
            # 3. プロジェクトタスク作成（Issueから派生）
            project_id = await manager.create_task(
                title="フロントエンド実装",
                description="UI/UX実装",
                task_type=TaskType.PROJECT_TASK,
                priority=Priority.MEDIUM
            )
            
            # 4. TODO作成（プロジェクトタスクから派生）
            todo_id = await manager.create_task(
                title="ボタンコンポーネント実装",
                description="再利用可能なボタンコンポーネント",
                task_type=TaskType.TODO,
                priority=Priority.MEDIUM
            )
            
            # 5. ワークフロー実行
            await manager.update_task_status(planning_id, TaskStatus.COMPLETED)
            await manager.update_task_status(issue_id, TaskStatus.IN_PROGRESS)
            await manager.update_task_status(project_id, TaskStatus.IN_PROGRESS)
            await manager.update_task_status(todo_id, TaskStatus.COMPLETED)
            
            # 6. 統計確認
            stats = await manager.db.get_stats()
            assert stats['total_tasks'] == 4
            assert stats['status_distribution']['completed'] == 2
            assert stats['status_distribution']['in_progress'] == 2
            
            # 7. ダッシュボード確認
            dashboard = await manager.get_dashboard_data()
            assert len(dashboard['in_progress_tasks']) == 2
            
            manager.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


# pytest実行用のメイン関数
if __name__ == "__main__":
    pytest.main([__file__, "-v"])