"""
Elder Tree User Story Acceptance Tests
TDD: これらのテストから開始（最初は全て失敗）
"""

import pytest
from python_a2a import Agent, Message, Protocol
import asyncio


class TestElderTreeUserStories:
    """ユーザーストーリーベースの受け入れテスト"""
    
    @pytest.mark.acceptance
    async def test_4_sages_can_communicate(self):
        """
        ユーザーストーリー #1: 4賢者が相互通信できる
        
        Given: 4つの賢者エージェントが起動している
        When: Knowledge SageがTask Sageにタスク見積もりを依頼
        Then: Task Sageが見積もり結果を返す
        """
        # Arrange
        from elder_tree.agents import KnowledgeSage, TaskSage
        
        knowledge_sage = KnowledgeSage()
        task_sage = TaskSage()
        
        # Act
        await knowledge_sage.start()
        await task_sage.start()
        
        response = await knowledge_sage.send_message(
            target="task_sage",
            message_type="estimate_task",
            data={
                "task_description": "OAuth2.0認証システム実装",
                "complexity": "high"
            }
        )
        
        # Assert
        assert response is not None
        assert response.status == "success"
        assert "estimation" in response.data
        assert response.data["estimation"]["hours"] > 0
        
        # Cleanup
        await knowledge_sage.stop()
        await task_sage.stop()
    
    @pytest.mark.acceptance
    async def test_elder_flow_complete_execution(self):
        """
        ユーザーストーリー #2: Elder Flowが5段階を完全実行
        
        Given: Elder Flowシステムが利用可能
        When: 新機能実装タスクを投入
        Then: 5段階（相談→実行→品質→報告→Git）が完了
        """
        from elder_tree.workflows import ElderFlow
        
        # Arrange
        elder_flow = ElderFlow()
        
        # Act
        result = await elder_flow.execute(
            task_type="feature_implementation",
            requirements=[
                "ユーザー認証機能",
                "JWT トークン使用",
                "リフレッシュトークン対応"
            ],
            priority="high"
        )
        
        # Assert
        assert result.status == "completed"
        assert len(result.stages) == 5
        assert all(stage.completed for stage in result.stages)
        assert result.stages[0].name == "sage_consultation"
        assert result.stages[1].name == "servant_execution"
        assert result.stages[2].name == "quality_gate"
        assert result.stages[3].name == "council_report"
        assert result.stages[4].name == "git_automation"
    
    @pytest.mark.acceptance
    async def test_servant_with_4_sages_collaboration(self):
        """
        ユーザーストーリー #3: サーバントが4賢者と協調
        
        Given: Code Crafterサーバントが起動
        When: コード生成タスクを受信
        Then: 4賢者と協調して高品質コードを生成
        """
        from elder_tree.agents.servants import CodeCrafter
        
        # Arrange
        code_crafter = CodeCrafter()
        await code_crafter.start()
        
        # Act
        result = await code_crafter.generate_code(
            specification={
                "function_name": "authenticate_user",
                "parameters": ["username", "password"],
                "returns": "JWT token",
                "requirements": ["セキュア", "非同期対応"]
            }
        )
        
        # Assert
        assert result.status == "success"
        assert "test_code" in result.data
        assert "implementation_code" in result.data
        assert result.quality_score >= 85  # Iron Will基準
        
        # 4賢者協調の検証
        assert result.collaboration_log["knowledge_sage"]["consulted"] is True
        assert result.collaboration_log["task_sage"]["consulted"] is True
        assert result.collaboration_log["incident_sage"]["consulted"] is True
        assert result.collaboration_log["rag_sage"]["consulted"] is True
