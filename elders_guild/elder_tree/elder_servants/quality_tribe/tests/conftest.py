"""
pytest configuration
共通フィクスチャとテスト設定
"""

import pytest
import asyncio
from typing import AsyncGenerator
# A2A imports removed - using mock implementation


@pytest.fixture(scope="session")
def event_loop():
    """イベントループフィクスチャ"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_agent():
    """テスト用エージェントフィクスチャ"""
    # Mock agent for testing
    class MockAgent:
        def __init__(self):
            self.name = "test_agent"
            self.port = 59999
            
        async def start(self):
            pass
            
        async def stop(self):
            pass
            
    agent = MockAgent()
    await agent.start()
    yield agent
    await agent.stop()


@pytest.fixture
def mock_message():
    """モックメッセージフィクスチャ"""
    class MockMessage:
        def __init__(self, **kwargs):
            self.message_type = kwargs.get("message_type", "test")
            self.data = kwargs.get("data", {"test": "data"})
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def _create_message(**kwargs):
        """_create_messageを作成"""
        defaults = {
            "message_type": "test",
            "data": {"test": "data"}
        }
        defaults.update(kwargs)
        return MockMessage(**defaults)
    
    return _create_message
