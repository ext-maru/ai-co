#!/usr/bin/env python3
"""
Test for Session Inheritance Features
セッション継承機能のテスト
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
async def mock_tracker_with_previous_tasks():
    """前回のセッションタスクがあるモックトラッカー"""
    tracker = AsyncMock()
    
    # 前回のセッションからのタスクと現在のセッションのタスクを含むリスト
    tracker.list_tasks = AsyncMock(return_value=[
        {
            "task_id": "prev-task-1",
            "title": "前回のタスク1",
            "status": "pending",
            "priority": "high",
            "assigned_to": "claude_elder",
            "tags": ["user-claude_elder", "session-old123"],
            "metadata": {"session_id": "session-old123", "user_id": "claude_elder"}
        },
        {
            "task_id": "prev-task-2", 
            "title": "前回のタスク2",
            "status": "in_progress",
            "priority": "medium",
            "assigned_to": "claude_elder",
            "tags": ["user-claude_elder", "session-old456"],
            "metadata": {"session_id": "session-old456", "user_id": "claude_elder"}
        },
        {
            "task_id": "current-task-1",
            "title": "現在のタスク",
            "status": "pending", 
            "priority": "low",
            "assigned_to": "claude_elder",
            "tags": ["user-claude_elder", "session-current"],
            "metadata": {"session_id": "session-current", "user_id": "claude_elder"}
        },
        {
            "task_id": "completed-task",
            "title": "完了済みタスク",
            "status": "completed",
            "priority": "medium", 
            "assigned_to": "claude_elder",
            "tags": ["user-claude_elder", "session-old123"],
            "metadata": {"session_id": "session-old123", "user_id": "claude_elder"}
        }
    ])
    
    tracker.update_task = AsyncMock()
    tracker.get_task_statistics = AsyncMock(return_value={
        "total_tasks": 10,
        "status_distribution": {"pending": 3, "in_progress": 2, "completed": 5}
    })
    
    return tracker


@pytest.fixture
async def integration_with_previous_tasks(mock_tracker_with_previous_tasks):
    """前回タスクありの統合システム"""
    with patch('libs.todo_tracker_integration.create_postgres_task_tracker', 
               AsyncMock(return_value=mock_tracker_with_previous_tasks)):
        integration = TodoTrackerIntegration(
            auto_sync=False,
            user_id="claude_elder"
        )
        # 現在のセッションIDを固定値に設定
        integration.session_id = "session-current"
        await integration.initialize()
        return integration


class TestSessionInheritance:
    """セッション継承機能のテスト"""

    async def test_get_pending_tasks_from_previous_sessions(self, integration_with_previous_tasks):
        """前回セッションの未完了タスク取得テスト"""
        previous_tasks = await integration_with_previous_tasks.get_pending_tasks_from_previous_sessions()
        
        # 前回のセッションから2個のタスクが取得されることを確認
        assert len(previous_tasks) == 2
        
        # 現在のセッションのタスクは含まれない
        task_ids = [task["task_id"] for task in previous_tasks]
        assert "prev-task-1" in task_ids
        assert "prev-task-2" in task_ids
        assert "current-task-1" not in task_ids  # 現在のセッション
        assert "completed-task" not in task_ids  # 完了済み

    async def test_inherit_pending_tasks_without_confirmation(self, integration_with_previous_tasks, mock_tracker_with_previous_tasks):
        """確認なしでの継承テスト"""
        inherited_count = await integration_with_previous_tasks.inherit_pending_tasks(
            confirm_prompt=False
        )
        
        # 2個のタスクが継承されることを確認
        assert inherited_count == 2
        
        # update_taskが2回呼ばれることを確認
        assert mock_tracker_with_previous_tasks.update_task.call_count == 2
        
        # 呼び出し内容を確認
        for call in mock_tracker_with_previous_tasks.update_task.call_args_list:
            task_id, kwargs = call[0][0], call[1]
            
            # タグに現在のセッションIDが含まれていることを確認
            assert "session-current" in kwargs["tags"]
            
            # metadataが正しくJSON化されていることを確認
            metadata = json.loads(kwargs["metadata"])
            assert metadata["session_id"] == "session-current"
            assert "inherited_from" in metadata
            assert "inherited_at" in metadata

    async def test_inherit_pending_tasks_no_previous_tasks(self):
        """前回タスクがない場合のテスト"""
        mock_tracker = AsyncMock()
        mock_tracker.list_tasks = AsyncMock(return_value=[])  # 空のリスト
        mock_tracker.get_task_statistics = AsyncMock(return_value={})
        
        with patch('libs.todo_tracker_integration.create_postgres_task_tracker', 
                   AsyncMock(return_value=mock_tracker)):
            integration = TodoTrackerIntegration(user_id="test_user")
            await integration.initialize()
            
            inherited_count = await integration.inherit_pending_tasks(confirm_prompt=False)
            
            # 継承されるタスクは0個
            assert inherited_count == 0
            
            # update_taskは呼ばれない
            mock_tracker.update_task.assert_not_called()

    async def test_auto_inherit_if_pending_few_tasks(self, integration_with_previous_tasks):
        """少数タスクの自動継承提案テスト"""
        # inputをモック化
        with patch('builtins.input', return_value='y'):
            result = await integration_with_previous_tasks.auto_inherit_if_pending()
        
        # 継承が実行されたことを確認
        assert result == True

    async def test_auto_inherit_if_pending_many_tasks(self):
        """多数タスクの場合の自動継承テスト"""
        mock_tracker = AsyncMock()
        
        # 5個の前回タスクを作成
        many_tasks = []
        for i in range(5):
            many_tasks.append({
                "task_id": f"prev-task-{i}",
                "title": f"前回のタスク{i}",
                "status": "pending",
                "priority": "medium",
                "assigned_to": "claude_elder",
                "tags": ["user-claude_elder", f"session-old{i}"],
                "metadata": {"session_id": f"session-old{i}", "user_id": "claude_elder"}
            })
        
        mock_tracker.list_tasks = AsyncMock(return_value=many_tasks)
        mock_tracker.get_task_statistics = AsyncMock(return_value={})
        
        with patch('libs.todo_tracker_integration.create_postgres_task_tracker', 
                   AsyncMock(return_value=mock_tracker)):
            integration = TodoTrackerIntegration(user_id="claude_elder")
            integration.session_id = "session-current"
            await integration.initialize()
            
            # 出力をキャプチャ
            import io
            import contextlib
            
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = await integration.auto_inherit_if_pending()
            
            # 多数タスクの場合は自動継承しない
            assert result == False
            
            # メッセージが出力されることを確認
            assert "個の未完了タスクがあります" in output.getvalue()

    async def test_session_id_uniqueness(self):
        """セッションIDの一意性テスト"""
        integrations = []
        
        # 複数の統合システムを作成
        for i in range(5):
            integration = TodoTrackerIntegration(user_id=f"user{i}")
            integrations.append(integration)
        
        # 全てのセッションIDが異なることを確認
        session_ids = [integration.session_id for integration in integrations]
        assert len(session_ids) == len(set(session_ids))  # 重複なし

    async def test_inherited_task_metadata_structure(self, integration_with_previous_tasks, mock_tracker_with_previous_tasks):
        """継承タスクのメタデータ構造テスト"""
        await integration_with_previous_tasks.inherit_pending_tasks(confirm_prompt=False)
        
        # update_taskの呼び出しを確認
        calls = mock_tracker_with_previous_tasks.update_task.call_args_list
        assert len(calls) == 2
        
        for call in calls:
            metadata_json = call[1]["metadata"]
            metadata = json.loads(metadata_json)
            
            # 必要なフィールドが含まれていることを確認
            assert "session_id" in metadata
            assert "user_id" in metadata
            assert "inherited_from" in metadata
            assert "inherited_at" in metadata
            
            # 値が正しいことを確認
            assert metadata["session_id"] == "session-current"
            assert metadata["user_id"] == "claude_elder"
            assert isinstance(metadata["inherited_at"], str)


# 実行
if __name__ == "__main__":
    pytest.main([__file__, "-v"])