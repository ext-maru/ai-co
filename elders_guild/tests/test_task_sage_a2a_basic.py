#!/usr/bin/env python3
"""
📋 Task Sage A2A Agent - 基本テストスイート
Elder Loop Phase 2: TDD厳密テスト設計

Knowledge Sageパターンを適用した基本機能テスト
"""

import asyncio
import pytest
import json
import logging
from datetime import datetime
from unittest.mock import AsyncMock, patch

# python-a2a imports
from python_a2a import Message, TextContent, MessageRole, A2AError

# Task Sage A2A Agent
import sys
sys.path.append("/home/aicompany/ai_co/elders_guild")
from task_sage.a2a_agent import TaskSageAgent
from task_sage.business_logic import TaskProcessor


class TestTaskSageA2ABasic:
    """Task Sage A2A Agent基本機能テスト"""
    
    @pytest.fixture
    async def task_agent(self):
        """Task Sage A2A Agentインスタンス作成"""
        agent = TaskSageAgent(host="localhost", port=8002)
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.fixture
    def sample_task_data(self):
        """サンプルタスクデータ"""
        return {
            "title": "Task Sage A2A変換テスト",
            "description": "Elder LoopによるTask Sage A2A実装テスト",
            "estimated_hours": 8.0,
            "priority": 3,  # TaskPriority.HIGH.value
            "tags": ["a2a", "elder-loop", "test"],
            "complexity_factors": {
                "lines_of_code": 1200,
                "complexity": "medium",
                "dependencies": ["knowledge-sage"]
            }
        }
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, task_agent):
        """エージェント初期化テスト"""
        assert task_agent.agent_name == "task-sage"
        assert task_agent.description.startswith("Elders Guild Task Management Sage")
        assert task_agent.host == "localhost"
        assert task_agent.port == 8002
        assert task_agent.task_processor is not None
        print("✅ Agent initialization test passed")
    
    @pytest.mark.asyncio
    async def test_create_task_skill(self, task_agent, sample_task_data):
        """タスク作成スキルテスト"""
        # Arrange
        message_content = json.dumps(sample_task_data)
        message = Message(
            content=TextContent(text=message_content),
            role=MessageRole.USER
        )
        
        # Act
        response = await task_agent.create_task_skill(message)
        
        # Assert
        assert isinstance(response, Message)
        assert isinstance(response.content, TextContent)
        
        response_data = json.loads(response.content.text)
        assert response_data["success"] is True
        assert "task_id" in response_data["data"]
        assert response_data["data"]["title"] == sample_task_data["title"]
        assert response_data["data"]["status"] == "pending"
        assert response_data["data"]["priority"] == sample_task_data["priority"]
        
        print(f"✅ Task creation skill test passed: {response_data['data']['task_id']}")
    
    @pytest.mark.asyncio
    async def test_get_task_skill(self, task_agent, sample_task_data):
        """タスク取得スキルテスト"""
        # Arrange - 事前にタスクを作成
        create_message = Message(
            content=TextContent(text=json.dumps(sample_task_data)),
            role=MessageRole.USER
        )
        create_response = await task_agent.create_task_skill(create_message)
        create_data = json.loads(create_response.content.text)
        task_id = create_data["data"]["task_id"]
        
        # Act
        get_message = Message(
            content=TextContent(text=json.dumps({"task_id": task_id})),
            role=MessageRole.USER
        )
        response = await task_agent.get_task_skill(get_message)
        
        # Assert
        assert isinstance(response, Message)
        response_data = json.loads(response.content.text)
        assert response_data["success"] is True
        assert response_data["data"]["task_id"] == task_id
        assert response_data["data"]["title"] == sample_task_data["title"]
        assert response_data["data"]["description"] == sample_task_data["description"]
        
        print(f"✅ Task get skill test passed: {task_id}")
    
    @pytest.mark.asyncio
    async def test_list_tasks_skill(self, task_agent, sample_task_data):
        """タスク一覧取得スキルテスト"""
        # Arrange - 複数タスクを作成
        for i in range(3):
            task_data = sample_task_data.copy()
            task_data["title"] = f"テストタスク {i+1}"
            create_message = Message(
                content=TextContent(text=json.dumps(task_data)),
                role=MessageRole.USER
            )
            await task_agent.create_task_skill(create_message)
        
        # Act
        list_message = Message(
            content=TextContent(text=json.dumps({})),
            role=MessageRole.USER
        )
        response = await task_agent.list_tasks_skill(list_message)
        
        # Assert
        assert isinstance(response, Message)
        response_data = json.loads(response.content.text)
        assert response_data["success"] is True
        assert "tasks" in response_data["data"]
        assert response_data["data"]["total_count"] >= 3
        
        print(f"✅ Task list skill test passed: {response_data['data']['total_count']} tasks")
    
    @pytest.mark.asyncio
    async def test_estimate_effort_skill(self, task_agent):
        """工数見積もりスキルテスト"""
        # Arrange
        complexity_data = {
            "complexity_factors": {
                "lines_of_code": 2000,
                "complexity": "high",
                "dependencies": ["knowledge-sage", "rag-sage"]
            }
        }
        message = Message(
            content=TextContent(text=json.dumps(complexity_data)),
            role=MessageRole.USER
        )
        
        # Act
        response = await task_agent.estimate_effort_skill(message)
        
        # Assert
        assert isinstance(response, Message)
        response_data = json.loads(response.content.text)
        assert response_data["success"] is True
        assert "estimated_hours" in response_data["data"]
        assert "confidence" in response_data["data"]
        assert "breakdown" in response_data["data"]
        
        estimated_hours = response_data["data"]["estimated_hours"]
        confidence = response_data["data"]["confidence"]
        assert estimated_hours > 0
        assert 0 <= confidence <= 1
        
        print(f"✅ Effort estimation skill test passed: {estimated_hours:.2f}h (confidence: {confidence:.2f})")
    
    @pytest.mark.asyncio
    async def test_get_statistics_skill(self, task_agent):
        """統計情報取得スキルテスト"""
        # Arrange
        message = Message(
            content=TextContent(text=json.dumps({})),
            role=MessageRole.USER
        )
        
        # Act
        response = await task_agent.get_statistics_skill(message)
        
        # Assert
        assert isinstance(response, Message)
        response_data = json.loads(response.content.text)
        assert response_data["success"] is True
        assert "task_statistics" in response_data["data"]
        assert "project_statistics" in response_data["data"]
        assert "time_statistics" in response_data["data"]
        assert "system_health" in response_data["data"]
        
        task_stats = response_data["data"]["task_statistics"]
        assert "total_tasks" in task_stats
        assert "status_breakdown" in task_stats
        
        print(f"✅ Statistics skill test passed: {task_stats['total_tasks']} total tasks")
    
    @pytest.mark.asyncio
    async def test_health_check_skill(self, task_agent):
        """ヘルスチェックスキルテスト"""
        # Arrange
        message = Message(
            content=TextContent(text=json.dumps({})),
            role=MessageRole.USER
        )
        
        # Act
        response = await task_agent.health_check_skill(message)
        
        # Assert
        assert isinstance(response, Message)
        response_data = json.loads(response.content.text)
        assert response_data["status"] == "healthy"
        assert response_data["agent"] == "task-sage"
        assert "timestamp" in response_data
        assert "total_tasks" in response_data
        assert "total_projects" in response_data
        assert response_data["uptime"] == "operational"
        
        print(f"✅ Health check skill test passed: {response_data['status']}")
    
    @pytest.mark.asyncio
    async def test_elder_collaboration_skill(self, task_agent):
        """4賢者協調スキルテスト"""
        # Arrange
        collaboration_data = {
            "type": "task_planning",
            "task_spec": {
                "complexity_factors": {
                    "lines_of_code": 1500,
                    "complexity": "medium"
                }
            }
        }
        message = Message(
            content=TextContent(text=json.dumps(collaboration_data)),
            role=MessageRole.USER
        )
        
        # Act
        response = await task_agent.elder_collaboration_skill(message)
        
        # Assert
        assert isinstance(response, Message)
        response_data = json.loads(response.content.text)
        assert response_data["success"] is True
        assert response_data["collaboration_type"] == "task_planning"
        assert response_data["agent"] == "task-sage"
        assert "result" in response_data
        
        print(f"✅ Elder collaboration skill test passed: {response_data['collaboration_type']}")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, task_agent):
        """エラーハンドリングテスト"""
        # Arrange - 不正なタスクIDでタスク取得
        invalid_message = Message(
            content=TextContent(text=json.dumps({"task_id": "invalid-task-id"})),
            role=MessageRole.USER
        )
        
        # Act
        response = await task_agent.get_task_skill(invalid_message)
        
        # Assert
        assert isinstance(response, Message)
        response_data = json.loads(response.content.text)
        assert response_data["success"] is False
        assert "error" in response_data
        
        print(f"✅ Error handling test passed: {response_data['error']}")


async def main():
    """基本テストスイート実行"""
    print("📋 Task Sage A2A Agent - 基本テストスイート開始")
    print("=" * 60)
    
    # pytest実行（プログラマティック）
    import subprocess
    import sys
    
    test_file = __file__
    result = subprocess.run([
        sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    print("stdout:", result.stdout)
    if result.stderr:
        print("stderr:", result.stderr)
    
    print(f"✅ 基本テストスイート完了: 終了コード {result.returncode}")
    return result.returncode == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("🎉 Task Sage A2A Agent基本テスト全合格！")
    else:
        print("💥 一部テスト失敗 - Elder Loop Phase 4で修正します")