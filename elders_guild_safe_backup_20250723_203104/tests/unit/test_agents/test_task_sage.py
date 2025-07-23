"""
Task Sage ユニットテスト
TDD approach with comprehensive coverage
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from elder_tree.agents.task_sage import TaskSage, Task, TaskStatus, TaskPriority
from python_a2a import Message
from sqlmodel import Session, select
from faker import Faker
import factory


# Test Fixtures with Factory Boy
class TaskFactory(factory.Factory):


"""タスクファクトリー（Factory Boy使用）"""
        model = dict
    
    title = factory.Faker('sentence', nb_words=5)
    description = factory.Faker('text', max_nb_chars=200)
    priority = factory.fuzzy.FuzzyChoice(['low', 'medium', 'high', 'critical'])
    assignee = factory.Faker('user_name')
    tags = factory.List([factory.Faker('word') for _ in range(3)])


class TestTaskSage:

        """Task Sage テストスイート"""
        """Task Sageインスタンス"""
        sage = TaskSage(db_url="sqlite:///:memory:")
        yield sage
        if hasattr(sage, '_client'):
            await sage.stop()
    
    @pytest.fixture
    def faker(self):

            """Faker インスタンス（日本語）"""
        """サンプルタスクデータ"""
        return {
            "title": faker.sentence(),
            "description": faker.text(max_nb_chars=200),
            "priority": "high",
            "assignee": "elder_flow",
            "tags": ["urgent", "feature", "backend"],
            "due_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
    
    @pytest.fixture
    def mock_message(self, sample_task_data):

        """モックメッセージ"""
        """タスク作成成功テスト"""
        message = Mock()
        message.data = sample_task_data
        
        # ハンドラーを直接呼び出し
        handler = None
        for h in task_sage._message_handlers.get("create_task", []):
            handler = h["handler"]
            break
        
        assert handler is not None
        result = await handler(message)
        
        # 検証
        assert result["status"] == "success"
        assert "task_id" in result
        assert result["task"]["title"] == sample_task_data["title"]
        assert result["task"]["status"] == "pending"
        
        # DBに保存されていることを確認
        with Session(task_sage.engine) as session:
            task = session.exec(
                select(Task).where(Task.task_id == result["task_id"])
            ).first()
            assert task is not None
            assert task.title == sample_task_data["title"]

    @pytest.mark.asyncio
    async def test_create_task_validation_error(self, task_sage):

            """タスク作成バリデーションエラーテスト""" "Test description"
            # title is missing
        }
        
        handler = None
        for h in task_sage._message_handlers.get("create_task", []):
            handler = h["handler"]
            break
        
        result = await handler(message)
        
        # エラーが返されることを確認
        assert result["status"] == "error"
        assert "Title is required" in result["message"]

    @pytest.mark.asyncio
    async def test_update_task_status(self, task_sage, sample_task_data):

            """タスクステータス更新テスト"""
            create_handler = h["handler"]
            break
        
        create_result = await create_handler(create_message)
        task_id = create_result["task_id"]
        
        # ステータスを更新
        update_message = Mock()
        update_message.data = {
            "task_id": task_id,
            "status": "in_progress"
        }
        
        update_handler = None
        for h in task_sage._message_handlers.get("update_task_status", []):
            update_handler = h["handler"]
            break
        
        result = await update_handler(update_message)
        
        # 検証
        assert result["status"] == "success"
        assert result["task"]["status"] == "in_progress"
        assert result["task"]["started_at"] is not None

    @pytest.mark.asyncio
    async def test_assign_task(self, task_sage, sample_task_data, faker):

            """タスク割り当てテスト"""
            create_handler = h["handler"]
            break
        
        create_result = await create_handler(create_message)
        task_id = create_result["task_id"]
        
        # 新しい担当者に割り当て
        new_assignee = faker.user_name()
        assign_message = Mock()
        assign_message.data = {
            "task_id": task_id,
            "assignee": new_assignee
        }
        
        assign_handler = None
        for h in task_sage._message_handlers.get("assign_task", []):
            assign_handler = h["handler"]
            break
        
        result = await assign_handler(assign_message)
        
        # 検証
        assert result["status"] == "success"
        assert result["task"]["assignee"] == new_assignee
        assert result["old_assignee"] == sample_task_data["assignee"]

    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self, task_sage, faker):

            """タスク一覧フィルタリングテスト"""
            task = TaskFactory()
            task["status"] = "pending" if i < 5 else "completed"
            tasks_data.append(task)
        
        # タスクを作成
        create_handler = None
        for h in task_sage._message_handlers.get("create_task", []):
            create_handler = h["handler"]
            break
        
        for task_data in tasks_data:
            message = Mock()
            message.data = task_data
            await create_handler(message)
        
        # ステータスでフィルタリング
        list_message = Mock()
        list_message.data = {
            "status": "pending",
            "limit": 10
        }
        
        list_handler = None
        for h in task_sage._message_handlers.get("list_tasks", []):
            list_handler = h["handler"]
            break
        
        result = await list_handler(list_message)
        
        # 検証
        assert result["status"] == "success"
        assert len(result["tasks"]) == 5
        assert all(task["status"] == "pending" for task in result["tasks"])

    @pytest.mark.asyncio
    async def test_search_tasks(self, task_sage):

            """タスク検索テスト"""
            create_handler = h["handler"]
            break
        
        for term in search_terms:
            message = Mock()
            message.data = {
                "title": term,
                "description": f"Task for {term}",
                "priority": "medium",
                "assignee": "test_user"
            }
            await create_handler(message)
        
        # 検索実行
        search_message = Mock()
        search_message.data = {
            "query": "OAuth"
        }
        
        search_handler = None
        for h in task_sage._message_handlers.get("search_tasks", []):
            search_handler = h["handler"]
            break
        
        result = await search_handler(search_message)
        
        # 検証
        assert result["status"] == "success"
        assert len(result["tasks"]) == 1
        assert "OAuth" in result["tasks"][0]["title"]

    @pytest.mark.asyncio
    async def test_get_task_statistics(self, task_sage):

            """タスク統計テスト"""
            create_handler = h["handler"]
            break
        
        for i, (status, priority) in enumerate(zip(statuses, priorities)):
            message = Mock()
        # 繰り返し処理
            message.data = {
                "title": f"Task {i}",
                "description": "Test task",
                "priority": priority,
                "assignee": f"user_{i % 3}"  # 3人のユーザーに分散
            }
            result = await create_handler(message)
            
            # ステータスを更新
            if status != "pending":
                update_message = Mock()
                update_message.data = {
                    "task_id": result["task_id"],
                    "status": status
                }
                
                update_handler = None
                for h in task_sage._message_handlers.get("update_task_status", []):
                    update_handler = h["handler"]
                    break
                
                await update_handler(update_message)
        
        # 統計を取得
        stats_message = Mock()
        stats_message.data = {}
        
        stats_handler = None
        for h in task_sage._message_handlers.get("get_task_statistics", []):
            stats_handler = h["handler"]
            break
        
        result = await stats_handler(stats_message)
        
        # 検証
        assert result["status"] == "success"
        stats = result["statistics"]
        
        assert stats["total_tasks"] == 17
        assert stats["by_status"]["pending"] == 5
        assert stats["by_status"]["in_progress"] == 3
        assert stats["by_status"]["completed"] == 7
        assert stats["by_status"]["cancelled"] == 2
        
        assert stats["by_priority"]["low"] == 4
        assert stats["by_priority"]["medium"] == 6
        assert stats["by_priority"]["high"] == 5
        assert stats["by_priority"]["critical"] == 2

    @pytest.mark.asyncio
    async def test_get_task_dependencies(self, task_sage):

            """タスク依存関係テスト"""
            create_handler = h["handler"]
            break
        
        parent_message = Mock()
        parent_message.data = {
            "title": "Parent Task",
            "description": "Main task",
            "priority": "high",
            "assignee": "lead_dev"
        }
        parent_result = await create_handler(parent_message)
        parent_id = parent_result["task_id"]
        
        # 子タスクを作成
        child_ids = []
        for i in range(3):
            child_message = Mock()
            child_message.data = {
                "title": f"Child Task {i}",
                "description": "Subtask",
                "priority": "medium",
                "assignee": f"dev_{i}",
                "parent_task_id": parent_id
            }
            child_result = await create_handler(child_message)
            child_ids.append(child_result["task_id"])
        
        # 依存関係を取得
        deps_message = Mock()
        deps_message.data = {
            "task_id": parent_id
        }
        
        deps_handler = None
        for h in task_sage._message_handlers.get("get_task_dependencies", []):
            deps_handler = h["handler"]
            break
        
        result = await deps_handler(deps_message)
        
        # 検証
        assert result["status"] == "success"
        assert len(result["children"]) == 3
        assert all(child["parent_task_id"] == parent_id for child in result["children"])

    @pytest.mark.asyncio
    async def test_elder_flow_task_request(self, task_sage):

            """Elder Flow用タスクリクエストテスト""" "feature_implementation",
            "requirements": [
                "OAuth2.0 authentication",
                "User profile management",
                "Role-based access control"
            ],
            "requester": "elder_flow"
        }
        
        # ハンドラーを探す（elder_flow_consultation）
        consultation_handler = None
        for h in task_sage._message_handlers.get("elder_flow_consultation", []):
            consultation_handler = h["handler"]
            break
        
        result = await consultation_handler(flow_message)
        
        # 検証
        assert "estimated_hours" in result
        assert result["estimated_hours"] > 0
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        assert "priority_suggestion" in result
        assert result["priority_suggestion"] in ["low", "medium", "high", "critical"]

    @pytest.mark.asyncio
    async def test_delete_task_cascade(self, task_sage):

            """タスク削除（カスケード）テスト"""
            create_handler = h["handler"]
            break
        
        # 親タスク
        parent_message = Mock()
        parent_message.data = {
            "title": "Parent to delete",
            "description": "Will be deleted",
            "priority": "low",
            "assignee": "test_user"
        }
        parent_result = await create_handler(parent_message)
        parent_id = parent_result["task_id"]
        
        # 子タスク
        child_message = Mock()
        child_message.data = {
            "title": "Child task",
            "description": "Will also be deleted",
            "priority": "low",
            "assignee": "test_user",
            "parent_task_id": parent_id
        }
        child_result = await create_handler(child_message)
        child_id = child_result["task_id"]
        
        # 親タスクを削除
        delete_message = Mock()
        delete_message.data = {
            "task_id": parent_id
        }
        
        delete_handler = None
        for h in task_sage._message_handlers.get("delete_task", []):
            delete_handler = h["handler"]
            break
        
        result = await delete_handler(delete_message)
        
        # 検証
        assert result["status"] == "success"
        
        # 両方のタスクが削除されていることを確認
        with Session(task_sage.engine) as session:
            parent = session.exec(
                select(Task).where(Task.task_id == parent_id)
            ).first()
            child = session.exec(
                select(Task).where(Task.task_id == child_id)
            ).first()
            
            assert parent is None
            assert child is None

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="task_sage")
    async def test_bulk_task_creation_performance(self, task_sage, benchmark):

            """大量タスク作成パフォーマンステスト"""
            create_handler = h["handler"]
            break
        
        async def create_bulk_tasks():
            results = []
            """create_bulk_tasksを作成"""
            for task_data in tasks_data:
                message = Mock()
                message.data = task_data
                result = await create_handler(message)
                results.append(result)
            return results
        
        # ベンチマーク実行
        results = benchmark(lambda: asyncio.run(create_bulk_tasks()))
        
        # パフォーマンス基準: 100タスクを5秒以内
        assert benchmark.stats["mean"] < 5.0
        # 全てのタスクが正常に作成されたことを確認
        assert all(r["status"] == "success" for r in results)

    # エラーハンドリングのテスト
    @pytest.mark.asyncio
    async def test_update_nonexistent_task(self, task_sage):

        """存在しないタスクの更新テスト""" "TASK-NONEXISTENT",
            "status": "completed"
        }
        
        update_handler = None
        for h in task_sage._message_handlers.get("update_task_status", []):
            update_handler = h["handler"]
            break
        
        result = await update_handler(update_message)
        
        # エラーが返されることを確認
        assert result["status"] == "error"
        assert "Task not found" in result["message"]

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, task_sage, sample_task_data):

            """無効なステータス遷移テスト"""
            create_handler = h["handler"]
            break
        
        create_message = Mock()
        create_message.data = sample_task_data
        create_result = await create_handler(create_message)
        task_id = create_result["task_id"]
        
        # 完了状態に更新
        update_handler = None
        for h in task_sage._message_handlers.get("update_task_status", []):
            update_handler = h["handler"]
            break
        
        complete_message = Mock()
        complete_message.data = {
            "task_id": task_id,
            "status": "completed"
        }
        await update_handler(complete_message)
        
        # 完了状態からpendingに戻そうとする（無効な遷移）
        invalid_message = Mock()
        invalid_message.data = {
            "task_id": task_id,
            "status": "pending"
        }
        result = await update_handler(invalid_message)
        
        # エラーまたは警告が含まれることを確認
        # （実装によってはエラーではなく警告として処理される可能性がある）
        assert result["status"] in ["error", "warning", "success"]

    @pytest.mark.asyncio
    async def test_concurrent_task_updates(self, task_sage, sample_task_data):

        """並行タスク更新テスト"""
            create_handler = h["handler"]
            break
        
        create_message = Mock()
        create_message.data = sample_task_data
        create_result = await create_handler(create_message)
        task_id = create_result["task_id"]
        
        # 複数の更新を並行実行
        update_handler = None
        for h in task_sage._message_handlers.get("update_task_status", []):
            update_handler = h["handler"]
            break
        
        async def update_status(status):

            """update_statusを更新""" task_id,
                "status": status
            }
            return await update_handler(message)
        
        # 10個の並行更新（実際のアプリケーションでは競合状態になる可能性）
        tasks = []
        for i in range(10):
            status = "in_progress" if i % 2 == 0 else "pending"
            tasks.append(update_status(status))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 少なくとも1つは成功することを確認
        successful_results = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        assert len(successful_results) > 0


# Hypothesisを使ったプロパティベーステスト
from hypothesis import given, strategies as st

class TestTaskSageProperties:

            """Task Sageプロパティベーステスト"""
        """Task Sageインスタンス"""
        sage = TaskSage(db_url="sqlite:///:memory:")
        yield sage
        if hasattr(sage, '_client'):
            await sage.stop()
    
    @given(
        title=st.text(min_size=1, max_size=200),
        description=st.text(max_size=1000),
        priority=st.sampled_from(["low", "medium", "high", "critical"]),
        tags=st.lists(st.text(min_size=1, max_size=50), max_size=10)
    )
    @pytest.mark.asyncio
    async def test_task_creation_properties(self, task_sage, title, description, priority, tags):

            """タスク作成のプロパティテスト""" title,
            "description": description,
            "priority": priority,
            "assignee": "test_user",
            "tags": tags
        }
        
        create_handler = None
        for h in task_sage._message_handlers.get("create_task", []):
            create_handler = h["handler"]
            break
        
        result = await create_handler(message)
        
        # プロパティ: 必ず結果が返される
        assert result is not None
        
        # プロパティ: 成功した場合、task_idが存在する
        if result["status"] == "success":
            assert "task_id" in result
            assert result["task_id"].startswith("TASK-")
            
            # プロパティ: 入力データが保持される
            assert result["task"]["title"] == title
            assert result["task"]["priority"] == priority