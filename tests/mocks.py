"""Comprehensive mock infrastructure for testing"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock


# RabbitMQ Mocks
class MockChannel:
    def __init__(self):
        self.queue_declare = Mock()
        self.basic_consume = Mock()
        self.basic_ack = Mock()
        self.basic_publish = Mock()
        self.start_consuming = Mock()
        self.stop_consuming = Mock()
        self.close = Mock()


class MockConnection:
    def __init__(self):
        self.channel = Mock(return_value=MockChannel())
        self.close = Mock()
        self.is_open = True


def create_mock_pika():
    """Create mock pika module"""
    mock_pika = Mock()
    mock_pika.BlockingConnection = Mock(return_value=MockConnection())
    mock_pika.ConnectionParameters = Mock()
    return mock_pika


# Slack Mocks
class MockSlackClient:
    def __init__(self):
        self.conversations_list = AsyncMock(return_value={"ok": True, "channels": []})
        self.conversations_history = AsyncMock(
            return_value={"ok": True, "messages": []}
        )
        self.chat_postMessage = AsyncMock(return_value={"ok": True, "ts": "123"})
        self.users_list = AsyncMock(return_value={"ok": True, "members": []})


def create_mock_slack():
    """Create mock slack_sdk module"""
    mock_slack = Mock()
    mock_slack.web.async_client.AsyncWebClient = Mock(return_value=MockSlackClient())
    return mock_slack


# Redis Mocks
class MockRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self.data[key] = value
        return True

    def delete(self, key):
        if key in self.data:
            del self.data[key]
            return 1
        return 0


def create_mock_redis():
    """Create mock redis module"""
    mock_redis = Mock()
    mock_redis.Redis = Mock(return_value=MockRedis())
    return mock_redis


# Database Mocks
class MockCursor:
    def __init__(self):
        self.execute = Mock()
        self.fetchone = Mock(return_value=None)
        self.fetchall = Mock(return_value=[])
        self.close = Mock()


class MockConnection:
    def __init__(self):
        self.cursor = Mock(return_value=MockCursor())
        self.commit = Mock()
        self.rollback = Mock()
        self.close = Mock()


def create_mock_sqlite():
    """Create mock sqlite3 module"""
    mock_sqlite = Mock()
    mock_sqlite.connect = Mock(return_value=MockConnection())
    return mock_sqlite


# Generic Worker Mock
class MockWorker:
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get("config", {})
        self.is_running = False

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    async def process_message(self, message):
        return {"status": "success", "result": "processed"}
