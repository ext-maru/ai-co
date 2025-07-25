"""
🧪 Knowledge Sage A2A Agent - 簡単テスト (API確認用)
実際のpython-a2a APIに合わせた基本テスト
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock

from python_a2a import Message, TextContent, MessageRole, A2AError

# テスト対象インポート
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from knowledge_sage.a2a_agent import KnowledgeSageAgent
from knowledge_sage.business_logic import KnowledgeProcessor


class TestKnowledgeSageBasic:
    """基本的なKnowledge Sage A2A Agent テスト"""
    
    @pytest.fixture
    async def agent(self):
        """テスト用エージェント作成"""
        agent = KnowledgeSageAgent(host="localhost", port=8901)
        
        # モックプロセッサーに置き換え
        agent.knowledge_processor = AsyncMock(spec=KnowledgeProcessor)
        agent.knowledge_processor.process_action.return_value = {
            "success": True,
            "data": {"test": "response"}
        }
        
        yield agent
        
        # クリーンアップ
        try:
            await agent.shutdown()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """エージェント初期化テスト"""
        result = await agent.initialize()
        assert result is True
        assert agent.agent_name == "knowledge-sage"
        assert agent.port == 8901
    
    @pytest.mark.asyncio
    async def test_search_knowledge_skill_simple_text(self, agent):
        """知識検索スキル - 簡単なテキスト"""
        # テストメッセージ作成
        message = Message(
            content=TextContent(text="python programming"),
            role=MessageRole.USER
        )
        
        # スキル実行
        response = await agent.search_knowledge_skill(message)
        
        # 基本検証
        assert isinstance(response, Message)
        assert isinstance(response.content, TextContent)
        assert response.role == MessageRole.AGENT
        
        # JSON応答をパース
        response_data = json.loads(response.content.text)
        assert response_data["success"] is True
        
        # プロセッサー呼び出し確認
        agent.knowledge_processor.process_action.assert_called_once_with(
            "search_knowledge",
            {"query": "python programming"}
        )
    
    @pytest.mark.asyncio
    async def test_search_knowledge_skill_json_input(self, agent):
        """知識検索スキル - JSON入力"""
        # JSON形式のテストデータ
        input_data = {"query": "machine learning", "limit": 5}
        message = Message(
            content=TextContent(text=json.dumps(input_data)),
            role=MessageRole.USER
        )
        
        # スキル実行
        response = await agent.search_knowledge_skill(message)
        
        # 検証
        assert isinstance(response, Message)
        response_data = json.loads(response.content.text)
        assert response_data["success"] is True
        
        # プロセッサー呼び出し確認
        agent.knowledge_processor.process_action.assert_called_once_with(
            "search_knowledge",
            input_data
        )
    
    @pytest.mark.asyncio 
    async def test_search_knowledge_skill_error(self, agent):
        """知識検索スキル - エラーハンドリング"""
        # プロセッサーエラーをシミュレート
        agent.knowledge_processor.process_action.side_effect = Exception("Test error")
        
        message = Message(
            content=TextContent(text="test query"),
            role=MessageRole.USER
        )
        
        # スキル実行
        response = await agent.search_knowledge_skill(message)
        
        # エラー応答確認
        response_data = json.loads(response.content.text)
        assert response_data["success"] is False
        assert "Test error" in response_data["error"]
    
    @pytest.mark.asyncio
    async def test_agent_can_be_created(self):
        """エージェント作成可能確認"""
        agent = KnowledgeSageAgent()
        assert agent.agent_name == "knowledge-sage"
        assert agent.port == 8001  # デフォルトポート