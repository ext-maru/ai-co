"""
統合タスクトラッカー データベース層のテスト
"""

import pytest
import asyncio
from datetime import datetime
import tempfile
import os

from libs.unified_task_tracker.database import (
    TaskDatabase,
    TaskRepository,
    TaskHistoryRepository,
    TaskDependencyRepository,
    DatabaseError
)
from libs.unified_task_tracker.models import (
    Task, TaskHistory, TaskDependency,
    TaskStatus, TaskPriority, TaskVisibility
)


class TestTaskDatabase:
    """タスクデータベースのテスト"""
    
    @pytest.fixture
    async def db(self):
        """テスト用データベース"""
        # インメモリDBを使用
        db = TaskDatabase(":memory:")
        await db.initialize()
        yield db
        await db.close()
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, db):
        """データベース初期化テスト"""
        # テーブルが作成されていることを確認
        tables = await db.get_tables()
        assert "tasks" in tables
        assert "task_history" in tables
        assert "task_dependencies" in tables
    
    @pytest.mark.asyncio
    async def test_database_migration(self):
        """データベースマイグレーションテスト"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # 初回マイグレーション
            db = TaskDatabase(db_path)
            await db.initialize()
            version = await db.get_schema_version()
            assert version == 1
            await db.close()
            
            # 再接続してバージョン確認
            db = TaskDatabase(db_path)
            await db.initialize()
            version = await db.get_schema_version()
            assert version == 1
            await db.close()
        finally:
            os.unlink(db_path)


class TestTaskRepository:
    """タスクリポジトリのテスト"""
    
    @pytest.fixture
    async def repo(self):
        """テスト用リポジトリ"""
        db = TaskDatabase(":memory:")
        await db.initialize()
        repo = TaskRepository(db)
        yield repo
        await db.close()
    
    @pytest.mark.asyncio
    async def test_create_task(self, repo):
        """タスク作成テスト"""
        task = Task(
            title="テストタスク",
            description="リポジトリテスト用タスク"
        )
        
        created_task = await repo.create(task)
        
        assert created_task.id == task.id
        assert created_task.title == "テストタスク"
    
    @pytest.mark.asyncio
    async def test_get_task_by_id(self, repo):
        """IDでタスク取得テスト"""
        task = Task(title="取得テスト", description="説明")
        await repo.create(task)
        
        fetched_task = await repo.get_by_id(task.id)
        
        assert fetched_task is not None
        assert fetched_task.id == task.id
        assert fetched_task.title == "取得テスト"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, repo):
        """存在しないタスクの取得"""
        fetched_task = await repo.get_by_id("nonexistent-id")
        assert fetched_task is None
    
    @pytest.mark.asyncio
    async def test_update_task(self, repo):
        """タスク更新テスト"""
        task = Task(title="更新前", description="説明")
        await repo.create(task)
        
        task.title = "更新後"
        task.status = TaskStatus.IN_PROGRESS
        updated_task = await repo.update(task)
        
        assert updated_task.title == "更新後"
        assert updated_task.status == TaskStatus.IN_PROGRESS
        
        # DBから再取得して確認
        fetched_task = await repo.get_by_id(task.id)
        assert fetched_task.title == "更新後"
        assert fetched_task.status == TaskStatus.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_delete_task(self, repo):
        """タスク削除テスト"""
        task = Task(title="削除テスト", description="説明")
        await repo.create(task)
        
        success = await repo.delete(task.id)
        assert success is True
        
        # 削除確認
        fetched_task = await repo.get_by_id(task.id)
        assert fetched_task is None
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self, repo):
        """フィルタ付きタスク一覧取得"""
        # テストデータ作成
        tasks = [
            Task(title="高優先度タスク1", description="説明", 
                 priority=TaskPriority.HIGH, status=TaskStatus.PENDING),
            Task(title="高優先度タスク2", description="説明", 
                 priority=TaskPriority.HIGH, status=TaskStatus.IN_PROGRESS),
            Task(title="低優先度タスク", description="説明", 
                 priority=TaskPriority.LOW, status=TaskStatus.PENDING),
            Task(title="完了タスク", description="説明", 
                 status=TaskStatus.COMPLETED),
        ]
        
        for task in tasks:
            await repo.create(task)
        
        # フィルタテスト
        high_priority_tasks = await repo.list_tasks(priority=TaskPriority.HIGH)
        assert len(high_priority_tasks) == 2
        
        pending_tasks = await repo.list_tasks(status=TaskStatus.PENDING)
        assert len(pending_tasks) == 2
        
        high_pending_tasks = await repo.list_tasks(
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING
        )
        assert len(high_pending_tasks) == 1
    
    @pytest.mark.asyncio
    async def test_list_tasks_pagination(self, repo):
        """ページネーションテスト"""
        # 10個のタスクを作成
        for i in range(10):
            task = Task(title=f"タスク{i}", description="説明")
            await repo.create(task)
        
        # ページネーション
        page1 = await repo.list_tasks(limit=5, offset=0)
        assert len(page1) == 5
        
        page2 = await repo.list_tasks(limit=5, offset=5)
        assert len(page2) == 5
        
        # タイトルが異なることを確認
        page1_titles = {t.title for t in page1}
        page2_titles = {t.title for t in page2}
        assert len(page1_titles & page2_titles) == 0
    
    @pytest.mark.asyncio
    async def test_get_task_by_github_issue(self, repo):
        """GitHub Issue番号でタスク取得"""
        task = Task(
            title="GitHub連携タスク",
            description="説明",
            github_issue_number=42
        )
        await repo.create(task)
        
        fetched_task = await repo.get_by_github_issue(42)
        assert fetched_task is not None
        assert fetched_task.github_issue_number == 42


class TestTaskHistoryRepository:
    """タスク履歴リポジトリのテスト"""
    
    @pytest.fixture
    async def repos(self):
        """テスト用リポジトリセット"""
        db = TaskDatabase(":memory:")
        await db.initialize()
        task_repo = TaskRepository(db)
        history_repo = TaskHistoryRepository(db)
        yield task_repo, history_repo
        await db.close()
    
    @pytest.mark.asyncio
    async def test_create_history(self, repos):
        """履歴作成テスト"""
        task_repo, history_repo = repos
        
        # タスク作成
        task = Task(title="履歴テスト", description="説明")
        await task_repo.create(task)
        
        # 履歴作成
        history = TaskHistory(
            task_id=task.id,
            field_name="status",
            old_value="pending",
            new_value="in_progress",
            changed_by="test-user"
        )
        
        created_history = await history_repo.create(history)
        assert created_history.task_id == task.id
        assert created_history.field_name == "status"
    
    @pytest.mark.asyncio
    async def test_get_task_history(self, repos):
        """タスクの履歴取得テスト"""
        task_repo, history_repo = repos
        
        # タスク作成
        task = Task(title="履歴テスト", description="説明")
        await task_repo.create(task)
        
        # 複数の履歴作成
        changes = [
            ("status", "pending", "in_progress"),
            ("priority", "medium", "high"),
            ("assignee", None, "claude-elder")
        ]
        
        for field, old_val, new_val in changes:
            history = TaskHistory(
                task_id=task.id,
                field_name=field,
                old_value=old_val,
                new_value=new_val,
                changed_by="test-user"
            )
            await history_repo.create(history)
        
        # 履歴取得
        histories = await history_repo.get_task_history(task.id)
        assert len(histories) == 3
        
        # 時系列順であることを確認
        for i in range(len(histories) - 1):
            assert histories[i].changed_at <= histories[i + 1].changed_at


class TestTaskDependencyRepository:
    """タスク依存関係リポジトリのテスト"""
    
    @pytest.fixture
    async def repos(self):
        """テスト用リポジトリセット"""
        db = TaskDatabase(":memory:")
        await db.initialize()
        task_repo = TaskRepository(db)
        dep_repo = TaskDependencyRepository(db)
        yield task_repo, dep_repo
        await db.close()
    
    @pytest.mark.asyncio
    async def test_create_dependency(self, repos):
        """依存関係作成テスト"""
        task_repo, dep_repo = repos
        
        # タスク作成
        parent = Task(title="親タスク", description="説明")
        child = Task(title="子タスク", description="説明")
        await task_repo.create(parent)
        await task_repo.create(child)
        
        # 依存関係作成
        dependency = TaskDependency(
            task_id=child.id,
            depends_on_task_id=parent.id,
            dependency_type="requires"
        )
        
        created_dep = await dep_repo.create(dependency)
        assert created_dep.task_id == child.id
        assert created_dep.depends_on_task_id == parent.id
    
    @pytest.mark.asyncio
    async def test_get_dependencies(self, repos):
        """タスクの依存関係取得テスト"""
        task_repo, dep_repo = repos
        
        # タスク作成
        tasks = []
        for i in range(4):
            task = Task(title=f"タスク{i}", description="説明")
            await task_repo.create(task)
            tasks.append(task)
        
        # 依存関係作成 (task3 depends on task0, task1, task2)
        for i in range(3):
            dep = TaskDependency(
                task_id=tasks[3].id,
                depends_on_task_id=tasks[i].id,
                dependency_type="requires"
            )
            await dep_repo.create(dep)
        
        # 依存関係取得
        dependencies = await dep_repo.get_dependencies(tasks[3].id)
        assert len(dependencies) == 3
        
        depends_on_ids = {d.depends_on_task_id for d in dependencies}
        expected_ids = {tasks[0].id, tasks[1].id, tasks[2].id}
        assert depends_on_ids == expected_ids
    
    @pytest.mark.asyncio
    async def test_get_dependents(self, repos):
        """依存されているタスク取得テスト"""
        task_repo, dep_repo = repos
        
        # タスク作成
        parent = Task(title="親タスク", description="説明")
        child1 = Task(title="子タスク1", description="説明")
        child2 = Task(title="子タスク2", description="説明")
        
        await task_repo.create(parent)
        await task_repo.create(child1)
        await task_repo.create(child2)
        
        # 依存関係作成
        for child in [child1, child2]:
            dep = TaskDependency(
                task_id=child.id,
                depends_on_task_id=parent.id,
                dependency_type="blocks"
            )
            await dep_repo.create(dep)
        
        # 依存されているタスク取得
        dependents = await dep_repo.get_dependents(parent.id)
        assert len(dependents) == 2
        
        dependent_ids = {d.task_id for d in dependents}
        expected_ids = {child1.id, child2.id}
        assert dependent_ids == expected_ids