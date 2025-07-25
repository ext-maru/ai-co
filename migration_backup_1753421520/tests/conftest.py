#!/usr/bin/env python3
"""
Comprehensive test configuration
Created by Test Import Manager
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set test environment
os.environ["TESTING"] = "true"
os.environ["TEST_MODE"] = "true"


@pytest.fixture
def mock_config():
    """Mock configuration object"""
    config = Mock()
    config.get.return_value = "test_value"
    config.RABBITMQ_HOST = "localhost"
    config.REDIS_HOST = "localhost"
    config.SLACK_TOKEN = "test_token"
    return config


@pytest.fixture
def mock_logger():
    """Mock logger object"""
    logger = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ connection and channel"""
    connection = Mock()
    channel = Mock()
    connection.channel.return_value = channel

    # Setup channel methods
    channel.queue_declare = Mock()
    channel.basic_publish = Mock()
    channel.basic_consume = Mock()
    channel.start_consuming = Mock()
    channel.stop_consuming = Mock()
    channel.basic_ack = Mock()
    channel.basic_nack = Mock()
    channel.close = Mock()

    return connection, channel


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_client = Mock()
    redis_client.get = Mock(return_value=None)
    redis_client.set = Mock(return_value=True)
    redis_client.delete = Mock(return_value=1)
    redis_client.exists = Mock(return_value=False)
    redis_client.expire = Mock(return_value=True)
    redis_client.hget = Mock(return_value=None)
    redis_client.hset = Mock(return_value=1)
    redis_client.hdel = Mock(return_value=1)
    redis_client.hgetall = Mock(return_value={})
    redis_client.pipeline = Mock(return_value=redis_client)
    redis_client.execute = Mock(return_value=[])
    return redis_client


@pytest.fixture
def mock_slack():
    """Mock Slack client"""
    slack_client = Mock()
    slack_client.chat_postMessage = Mock(
        return_value={"ok": True, "ts": "1234567890.123456"}
    )
    slack_client.conversations_list = Mock(return_value={"ok": True, "channels": []})
    slack_client.users_list = Mock(return_value={"ok": True, "members": []})
    slack_client.conversations_history = Mock(return_value={"ok": True, "messages": []})
    return slack_client


@pytest.fixture
def temp_file():
    """Temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_dir():
    """Temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def test_task_data():
    """Standard test task data"""
    return {
        "task_id": "test-123",
        "type": "test_task",
        "data": {"test": True},
        "created_at": "2025-01-01T00:00:00Z",
        "priority": "normal",
        "retry_count": 0,
        "max_retries": 3,
        "status": "pending",
    }


@pytest.fixture
def mock_claude_cli():
    """Mock Claude CLI subprocess calls"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Test response"
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_slack_notifier():
    """Mock Slack notifier"""
    with patch("libs.slack_notifier.SlackNotifier") as mock_slack:
        mock_instance = Mock()
        mock_slack.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def valid_task():
    """Valid task data for testing"""
    return {
        "id": "test-123",
        "type": "code",
        "prompt": "Create a fibonacci function",
        "priority": "normal",
        "created_at": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def worker():
    """Test worker instance"""
    with patch("libs.task_history_db.TaskHistoryDB"):
        with patch("libs.slack_notifier.SlackNotifier"):
            from workers.task_worker import TaskWorker

            worker = TaskWorker(worker_id="test-worker-1")
            worker.task_history_db = Mock()
            worker.task_history_db.save_task = Mock()
            worker.task_history_db.add_task = Mock()
            worker.task_history_db.update_task = Mock()
            worker.channel = Mock()
            worker.channel.basic_publish = Mock()
            yield worker


# Auto-use fixtures for common mocks
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically setup test environment"""
    # Mock external dependencies
    with patch("pika.BlockingConnection") as mock_pika:
        with patch("redis.Redis") as mock_redis:
            with patch("slack_sdk.WebClient") as mock_slack:
                yield


"""Reusable test fixtures"""
import sys
from unittest.mock import Mock, patch

import pytest

# Mock all external dependencies
sys.modules["pika"] = Mock()
sys.modules["redis"] = Mock()
sys.modules["slack_sdk"] = Mock()
sys.modules["aioredis"] = Mock()
sys.modules["prometheus_client"] = Mock()


@pytest.fixture
def mock_config():
    """Standard test configuration"""
    return {
        "rabbitmq": {
            "host": "localhost",
            "port": 5672,
            "username": "test",
            "password": "test",
        },
        "redis": {"host": "localhost", "port": 6379},
        "slack": {"bot_token": "test-token", "channel": "test-channel"},
    }


@pytest.fixture
def mock_task():
    """Standard test task"""
    return {
        "task_id": "test-123",
        "type": "test_task",
        "data": {"key": "value"},
        "metadata": {},
    }


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ connection"""
    with patch("pika.BlockingConnection") as mock:
        from tests.mocks import MockConnection

        mock.return_value = MockConnection()
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    with patch("redis.Redis") as mock:
        from tests.mocks import MockRedis

        mock.return_value = MockRedis()
        yield mock


@pytest.fixture
def mock_slack():
    """Mock Slack client"""
    with patch("slack_sdk.web.async_client.AsyncWebClient") as mock:
        from tests.mocks import MockSlackClient

        mock.return_value = MockSlackClient()
        yield mock


# OSS移行POC用追加設定
def pytest_configure(config):
    """pytest設定 - OSS移行POC"""
    # カスタムマーカーの登録
    config.addinivalue_line("markers", "integration: 統合テスト用マーカー")
    config.addinivalue_line("markers", "database: データベーステスト用マーカー")
    config.addinivalue_line("markers", "api: APIテスト用マーカー")
    config.addinivalue_line("markers", "benchmark: ベンチマークテスト用マーカー")


# pytest-asyncio設定
pytest_plugins = ["pytest_asyncio"]
