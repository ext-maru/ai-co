#!/usr/bin/env python3
"""
Test for Personal Task Management Features
個人タスク管理機能のテスト
"""

import asyncio
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.todo_tracker_integration import TodoTrackerIntegration
from libs.postgres_claude_task_tracker import TaskPriority, TaskStatus, TaskType


@pytest.fixture
async def mock_tracker():
    """モックタスクトラッカー"""
    tracker = AsyncMock()
    
    # create_task のモック
    tracker.create_task = AsyncMock(return_value="personal-task-123")
    
    # list_tasks のモック（個人タスクを返す）
    tracker.list_tasks = AsyncMock(return_value=[
        {
            "task_id": "task-001",
            "title": "Claude Elderの個人タスク1",
            "status": "in_progress",
            "priority": "high",
            "assigned_to": "claude_elder",
            "created_by": "claude_elder",
            "tags": ["user-claude_elder", "session-20250721-150000"],
            "metadata": {"user_id": "claude_elder", "session_id": "session-20250721-150000"}
        },
        {
            "task_id": "task-002",
            "title": "Claude Elderの個人タスク2",
            "status": "pending",
            "priority": "medium",
            "assigned_to": "claude_elder",
            "created_by": "claude_elder",
            "tags": ["user-claude_elder", "session-20250721-150000"],
            "metadata": {"user_id": "claude_elder", "session_id": "session-20250721-150000"}
        }
    ])
    
    # sync_with_todo_list のモック
    tracker.sync_with_todo_list = AsyncMock(return_value=2)
    
    # get_task_statistics のモック
    tracker.get_task_statistics = AsyncMock(return_value={
        "total_tasks": 50,
        "status_distribution": {"pending": 20, "in_progress": 15, "completed": 15}
    })
    
    return tracker


@pytest.fixture
async def personal_integration(mock_tracker):
    """個人用統合システムのフィクスチャ"""
    with patch('libs.todo_tracker_integration.create_postgres_task_tracker', AsyncMock(return_value=mock_tracker)):
        integration = TodoTrackerIntegration(
            auto_sync=False,
            user_id="claude_elder"
        )
        await integration.initialize()
        return integration


class TestPersonalTaskManagement:
    """個人タスク管理機能のテスト"""

    async def test_initialization_with_user_id(self, personal_integration):
        """ユーザーID付き初期化のテスト"""
        assert personal_integration.user_id == "claude_elder"
        assert personal_integration.session_id.startswith("session-")
        assert not personal_integration._running

    async def test_create_personal_task(self, personal_integration, mock_tracker):
        """個人タスク作成のテスト"""
        # タスク作成
        task_id = await personal_integration.create_task_with_todo_sync(
            title="個人タスクテスト",
            task_type=TaskType.FEATURE,
            priority=TaskPriority.HIGH
        )

        # 検証
        assert task_id == "personal-task-123"
        
        # create_task の呼び出しを検証
        call_args = mock_tracker.create_task.call_args[1]
        assert call_args["assigned_to"] == "claude_elder"
        assert call_args["created_by"] == "claude_elder"
        assert f"user-claude_elder" in call_args["tags"]
        assert call_args["metadata"]["user_id"] == "claude_elder"
        assert "session_id" in call_args["metadata"]

    async def test_sync_personal_only(self, personal_integration, mock_tracker):
        """個人タスクのみの同期テスト"""
        # 個人タスクのみ同期
        await personal_integration.sync_both_ways(personal_only=True)

        # list_tasks が assigned_to フィルターで呼ばれたことを確認
        mock_tracker.list_tasks.assert_called_with(
            assigned_to="claude_elder",
            limit=20
        )

    async def test_sync_all_tasks(self, personal_integration, mock_tracker):
        """全タスク同期のテスト"""
        # sync_tracker_to_todo_list をモック
        mock_tracker.sync_tracker_to_todo_list = AsyncMock(return_value=[
            {"id": "all-1", "content": "全体タスク1", "status": "pending", "priority": "high"},
            {"id": "all-2", "content": "全体タスク2", "status": "in_progress", "priority": "medium"}
        ])

        # 全タスク同期
        await personal_integration.sync_both_ways(personal_only=False)

        # sync_tracker_to_todo_list が呼ばれたことを確認
        mock_tracker.sync_tracker_to_todo_list.assert_called_once()

    async def test_get_my_tasks(self, personal_integration, mock_tracker):
        """自分のタスク取得テスト"""
        # 自分のタスクを取得
        my_tasks = await personal_integration.get_my_tasks()

        # 検証
        assert len(my_tasks) == 2
        assert all(task["assigned_to"] == "claude_elder" for task in my_tasks)
        mock_tracker.list_tasks.assert_called_with(assigned_to="claude_elder")

    async def test_get_my_tasks_with_filter(self, personal_integration, mock_tracker):
        """フィルター付き自分のタスク取得テスト"""
        # ステータスフィルター付きで取得
        await personal_integration.get_my_tasks(status_filter=["pending", "in_progress"])

        # 検証
        mock_tracker.list_tasks.assert_called_with(
            assigned_to="claude_elder",
            status__in=["pending", "in_progress"]
        )

    async def test_get_sync_status_with_personal_stats(self, personal_integration):
        """個人統計付き同期ステータステスト"""
        status = await personal_integration.get_sync_status()

        # 検証
        assert status["user_id"] == "claude_elder"
        assert "session_id" in status
        assert "my_tasks_stats" in status
        assert status["my_tasks_stats"]["total"] == 2
        assert status["my_tasks_stats"]["pending"] == 1
        assert status["my_tasks_stats"]["in_progress"] == 1

    async def test_format_tasks_to_todos(self, personal_integration):
        """タスクからTodoへの変換テスト"""
        tasks = [
            {
                "task_id": "test-123",
                "title": "テストタスク",
                "status": "in_progress",
                "priority": "high",
                "metadata": {"todo_id": "todo-test-123"}
            }
        ]

        todos = personal_integration._format_tasks_to_todos(tasks)

        assert len(todos) == 1
        assert todos[0]["id"] == "todo-test-123"
        assert todos[0]["content"] == "テストタスク"
        assert todos[0]["status"] == "in_progress"
        assert todos[0]["priority"] == "high"

    async def test_multiple_users(self):
        """複数ユーザーのテスト"""
        # 異なるユーザーで統合システムを作成
        with patch('libs.todo_tracker_integration.create_postgres_task_tracker', AsyncMock(return_value=AsyncMock())):
            integration1 = TodoTrackerIntegration(user_id="claude_elder")
            integration2 = TodoTrackerIntegration(user_id="maru")
            integration3 = TodoTrackerIntegration(user_id="task_sage")

            # 各ユーザーIDが正しく設定されているか確認
            assert integration1.user_id == "claude_elder"
            assert integration2.user_id == "maru"
            assert integration3.user_id == "task_sage"

            # セッションIDが異なることを確認
            assert integration1.session_id != integration2.session_id
            assert integration2.session_id != integration3.session_id


class TestPersonalTaskCLI:
    """個人タスク管理CLIのテスト"""

    @patch('libs.todo_tracker_integration.create_postgres_task_tracker')
    @patch('sys.argv', ['todo-tracker-sync', 'my-tasks', '--user', 'test_user'])
    async def test_my_tasks_command(self, mock_create_tracker):
        """my-tasksコマンドのテスト"""
        # モックトラッカーセットアップ
        mock_tracker = AsyncMock()
        mock_tracker.list_tasks = AsyncMock(return_value=[
            {
                "task_id": "task-001",
                "title": "テストタスク",
                "status": "pending",
                "priority": "high",
                "tags": ["test"],
                "assigned_to": "test_user"
            }
        ])
        mock_tracker.get_task_statistics = AsyncMock(return_value={})
        mock_create_tracker.return_value = mock_tracker

        # main関数をインポートして実行
        from libs.todo_tracker_integration import main
        
        # 出力をキャプチャ
        import io
        import contextlib
        
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            await main()

        # 出力を確認
        result = output.getvalue()
        assert "test_user's Tasks" in result
        assert "テストタスク" in result


# 実行
if __name__ == "__main__":
    pytest.main([__file__, "-v"])