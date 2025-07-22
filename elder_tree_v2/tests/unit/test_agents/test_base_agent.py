"""
Base Agent Unit Tests (TDD)
"""

import pytest
from unittest.mock import Mock, AsyncMock
from python_a2a import Message


class TestElderTreeAgent:
    """エージェント基底クラスのテスト"""
    
    def test_agent_initialization(self):
        """Test: エージェントが正しく初期化される"""
        from elder_tree.agents.base_agent import ElderTreeAgent
        
        # Act
        agent = ElderTreeAgent(
            name="test_agent",
            domain="test",
            port=50999
        )
        
        # Assert
        assert agent.name == "test_agent"
        assert agent.domain == "test"
        assert agent.port == 50999
        assert hasattr(agent, 'logger')
        assert hasattr(agent, 'message_counter')
    
    @pytest.mark.asyncio
    async def test_agent_health_check_handler(self):
        """Test: ヘルスチェックハンドラーが動作"""
        from elder_tree.agents.base_agent import ElderTreeAgent
        
        # Arrange
        agent = ElderTreeAgent(
            name="test_agent",
            domain="test"
        )
        
        # Act
        health_response = await agent.handle_health_check(
            Message(data={})
        )
        
        # Assert
        assert health_response["status"] == "healthy"
        assert health_response["agent"] == "test_agent"
        assert health_response["domain"] == "test"
    
    @pytest.mark.asyncio
    async def test_agent_metrics_tracking(self):
        """Test: メトリクスが正しく記録される"""
        from elder_tree.agents.base_agent import ElderTreeAgent
        
        # Arrange
        agent = ElderTreeAgent(
            name="test_agent",
            domain="test"
        )
        
        # Act
        await agent.process_message(
            Message(
                message_type="test_message",
                data={"test": "data"}
            )
        )
        
        # Assert
        # Prometheusメトリクスの確認
        assert agent.message_counter._value.get() > 0
    
    def test_agent_inherits_from_python_a2a(self):
        """Test: python-a2aのAgentクラスを継承"""
        from elder_tree.agents.base_agent import ElderTreeAgent
        from python_a2a import Agent
        
        # Assert
        assert issubclass(ElderTreeAgent, Agent)
