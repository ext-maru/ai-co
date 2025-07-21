#!/usr/bin/env python3
"""
Test for TodoList and Task Tracker Integration
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.todo_tracker_integration import TodoTrackerIntegration
from libs.todo_hook_system import TodoHookSystem, TodoCommandWrapper
from libs.postgres_claude_task_tracker import TaskPriority, TaskStatus, TaskType


@pytest.fixture
async def mock_tracker():
    """モックタスクトラッカー"""
    tracker = AsyncMock()
    tracker.sync_with_todo_list = AsyncMock(return_value=3)
    tracker.sync_tracker_to_todo_list = AsyncMock(return_value=[
        {"id": "task-1", "content": "Test task 1", "status": "pending", "priority": "high"},
        {"id": "task-2", "content": "Test task 2", "status": "in_progress", "priority": "medium"}
    ])
    tracker.create_task = AsyncMock(return_value="test-task-id")
    tracker.update_task = AsyncMock()
    tracker.get_task_statistics = AsyncMock(return_value={
        "total_tasks": 10,
        "status_distribution": {"pending": 5, "in_progress": 3, "completed": 2}
    })
    return tracker


@pytest.fixture
async def integration_system(mock_tracker):
    """統合システムのフィクスチャ"""
    with patch('libs.todo_tracker_integration.create_postgres_task_tracker', AsyncMock(return_value=mock_tracker)):
        integration = TodoTrackerIntegration(auto_sync=False)
        await integration.initialize()
        return integration


class TestTodoTrackerIntegration:
    """TodoTrackerIntegration のテスト"""

    async def test_initialization(self, integration_system):
        """初期化テスト"""
        assert integration_system.tracker is not None
        assert not integration_system._running
        assert integration_system.sync_interval == 300

    async def test_sync_both_ways(self, integration_system, mock_tracker):
        """双方向同期テスト"""
        # TodoListデータを設定
        test_todos = [
            {"id": "todo-1", "content": "Test todo 1", "status": "pending", "priority": "high"},
            {"id": "todo-2", "content": "Test todo 2", "status": "completed", "priority": "low"}
        ]
        integration_system._todo_cache = test_todos

        # 同期実行（全タスク同期）
        await integration_system.sync_both_ways(personal_only=False)

        # 検証
        mock_tracker.sync_with_todo_list.assert_called_once_with(test_todos)
        mock_tracker.sync_tracker_to_todo_list.assert_called_once()
        assert len(integration_system._todo_cache) == 2

    async def test_sync_personal_only(self, integration_system, mock_tracker):
        """個人タスクのみ同期テスト"""
        # TodoListデータを設定
        test_todos = [
            {"id": "todo-1", "content": "Personal todo", "status": "pending", "priority": "high"}
        ]
        integration_system._todo_cache = test_todos

        # 個人タスクのみ同期（デフォルト）
        await integration_system.sync_both_ways()

        # 検証：個人タスクフィルターでlist_tasksが呼ばれる
        mock_tracker.sync_with_todo_list.assert_called_once_with(test_todos)
        mock_tracker.list_tasks.assert_called_with(
            assigned_to="claude_elder",
            limit=20
        )

    async def test_create_task_with_todo_sync(self, integration_system, mock_tracker):
        """タスク作成とTodo同期のテスト"""
        # タスク作成
        task_id = await integration_system.create_task_with_todo_sync(
            title="New feature",
            task_type=TaskType.FEATURE,
            priority=TaskPriority.HIGH,
            created_by="test_user"
        )

        # 検証
        assert task_id == "test-task-id"
        
        # create_taskの呼び出しを検証（個人タスク設定が追加されているか）
        call_args = mock_tracker.create_task.call_args[1]
        assert call_args["assigned_to"] == "claude_elder"  # デフォルトユーザー（setdefault）
        assert call_args["created_by"] == "test_user"      # 明示的に指定された値
        assert "user-claude_elder" in call_args["tags"]
        assert call_args["metadata"]["user_id"] == "claude_elder"
        assert "session_id" in call_args["metadata"]
        
        # TodoListに追加されているか確認
        todos = integration_system.get_current_todos()
        assert len(todos) == 1
        assert todos[0]["content"] == "New feature"
        assert todos[0]["priority"] == "high"

    async def test_update_task_with_todo_sync(self, integration_system, mock_tracker):
        """タスク更新とTodo同期のテスト"""
        # タスク更新
        await integration_system.update_task_with_todo_sync(
            "test-task-id",
            status=TaskStatus.COMPLETED
        )

        # 検証
        mock_tracker.update_task.assert_called_once_with(
            "test-task-id",
            status=TaskStatus.COMPLETED
        )

    async def test_get_sync_status(self, integration_system):
        """同期ステータス取得テスト"""
        status = await integration_system.get_sync_status()

        assert "auto_sync_enabled" in status
        assert "sync_interval" in status
        assert "user_id" in status
        assert "session_id" in status
        assert "my_tasks_stats" in status
        assert "global_tracker_stats" in status  # 新しいキー名
        assert not status["sync_running"]

    async def test_import_export_todos(self, integration_system, mock_tracker):
        """インポート/エクスポートテスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_todos = [
                {"id": "import-1", "content": "Import test", "status": "pending", "priority": "high"}
            ]
            json.dump(test_todos, f)
            temp_path = f.name

        try:
            # インポート
            count = await integration_system.import_todos_from_json(temp_path)
            assert count == 3  # モックが返す値に合わせる
            mock_tracker.sync_with_todo_list.assert_called()

            # エクスポート
            await integration_system.export_todos_to_json(temp_path)
            mock_tracker.sync_tracker_to_todo_list.assert_called()

            # エクスポートされたデータを確認
            with open(temp_path, 'r') as f:
                exported = json.load(f)
            assert len(exported) == 2  # モックが返す2つのタスク

        finally:
            Path(temp_path).unlink()

    async def test_auto_sync(self, integration_system):
        """自動同期テスト"""
        # 自動同期開始
        await integration_system.start_auto_sync()
        assert integration_system._running

        # 少し待機
        await asyncio.sleep(0.1)

        # 自動同期停止
        await integration_system.stop_auto_sync()
        assert not integration_system._running


class TestTodoHookSystem:
    """TodoHookSystem のテスト"""

    @pytest.fixture
    def hook_system(self, integration_system):
        """フックシステムのフィクスチャ"""
        return TodoHookSystem(integration_system)

    async def test_hook_initialization(self, hook_system):
        """フックシステム初期化テスト"""
        assert hook_system.integration is not None
        assert not hook_system._running

    async def test_extract_todos_from_json(self, hook_system):
        """JSON形式のTodo抽出テスト"""
        content = '''
        [{"id": "todo-1", "content": "Test", "status": "pending", "priority": "high"}]
        '''
        todos = hook_system._extract_todos_from_content(content)
        assert len(todos) == 1
        assert todos[0]["content"] == "Test"

    async def test_extract_todos_from_text(self, hook_system):
        """テキスト形式のTodo抽出テスト"""
        content = '''
        - Task 1 | pending | high
        - Task 2 | in_progress | medium
        '''
        todos = hook_system._extract_todos_from_content(content)
        assert len(todos) == 2
        assert todos[0]["content"] == "Task 1"
        assert todos[1]["status"] == "in_progress"

    async def test_create_hook_file(self, hook_system):
        """フックファイル作成テスト"""
        test_todos = [{"id": "test-1", "content": "Test", "status": "pending", "priority": "high"}]
        
        hook_system.create_hook_file(test_todos)
        
        assert hook_system.hook_file.exists()
        
        with open(hook_system.hook_file, 'r') as f:
            saved_todos = json.load(f)
        
        assert saved_todos == test_todos
        
        # クリーンアップ
        hook_system.hook_file.unlink()


class TestTodoCommandWrapper:
    """TodoCommandWrapper のテスト"""

    @pytest.fixture
    async def wrapper(self):
        """コマンドラッパーのフィクスチャ"""
        return TodoCommandWrapper()

    @patch('libs.todo_tracker_integration.TodoTrackerIntegration')
    async def test_add_todo_command(self, mock_integration_class, wrapper):
        """Todo追加コマンドテスト"""
        mock_integration = AsyncMock()
        mock_integration.initialize = AsyncMock()
        mock_integration.create_task_with_todo_sync = AsyncMock(return_value="new-task-id")
        mock_integration_class.return_value = mock_integration

        result = await wrapper._add_todo(["New task", "high"])
        
        assert "Added todo" in result
        mock_integration.create_task_with_todo_sync.assert_called_once()

    @patch('libs.todo_tracker_integration.TodoTrackerIntegration')
    async def test_list_todos_command(self, mock_integration_class, wrapper):
        """Todo一覧コマンドテスト"""
        mock_integration = AsyncMock()
        mock_integration.initialize = AsyncMock()
        mock_integration.tracker = AsyncMock()
        mock_integration.tracker.sync_tracker_to_todo_list = AsyncMock(return_value=[
            {"id": "todo-1", "content": "Task 1", "status": "pending", "priority": "high"},
            {"id": "todo-2", "content": "Task 2", "status": "in_progress", "priority": "medium"}
        ])
        mock_integration_class.return_value = mock_integration

        result = await wrapper._list_todos([])
        
        assert "Active Todos" in result
        assert "Task 1" in result
        assert "Task 2" in result

    async def test_invalid_command(self, wrapper):
        """無効なコマンドテスト"""
        with pytest.raises(ValueError, match="Unknown command"):
            await wrapper.execute("invalid-command", [])


# 実行
if __name__ == "__main__":
    pytest.main([__file__, "-v"])