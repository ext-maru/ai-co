"""
pytest configuration
共通フィクスチャとテスト設定
"""

import pytest
import asyncio
from typing import AsyncGenerator
from python_a2a import agent, A2AClient, A2AServer, Message


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
    agent = Agent(name="test_agent", port=59999)
    await agent.start()
    yield agent
    await agent.stop()


@pytest.fixture
def mock_message():
    """モックメッセージフィクスチャ"""
    from python_a2a import Message
    
    def _create_message(**kwargs):
        """_create_messageを作成"""
        defaults = {
            "message_type": "test",
            "data": {"test": "data"}
        }
        defaults.update(kwargs)
        return Message(**defaults)
    
    return _create_message
