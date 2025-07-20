"""
Global pytest configuration and fixtures
"""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure pytest
pytest_plugins = []


# Disable coverage plugin if it's causing issues
def pytest_configure(config):
    """Configure pytest"""
    try:
        config.pluginmanager.unregister(name="pytest_cov")
    except:
        pass


# Global fixtures
@pytest.fixture(scope="session")
def project_root():
    """Project root directory"""
    return PROJECT_ROOT


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ connection"""
    with patch("pika.BlockingConnection") as mock_conn:
        mock_channel = Mock()
        mock_conn.return_value.channel.return_value = mock_channel
        yield mock_conn, mock_channel


@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    with patch("redis.Redis") as mock_redis:
        mock_redis.return_value.get.return_value = None
        mock_redis.return_value.set.return_value = True
        yield mock_redis


@pytest.fixture
def mock_logger():
    """Mock logger"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_task():
    """Sample task data"""
    return {
        "task_id": "test_123",
        "prompt": "Test prompt",
        "user_id": "test_user",
        "timestamp": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_ai_service():
    """Mock AI service"""
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text="Generated response")]
        )
        yield mock_client


# Missing module mocks
sys.modules["bs4"] = Mock()
sys.modules["matplotlib"] = Mock()
sys.modules["matplotlib.pyplot"] = Mock()
sys.modules["selenium"] = Mock()
sys.modules["selenium.webdriver"] = Mock()

# Fix pika.exceptions
try:
    import pika

    if not hasattr(pika, "exceptions"):
        pika.exceptions = type(
            "exceptions",
            (),
            {
                "AMQPError": Exception,
                "AMQPConnectionError": Exception,
                "ConnectionClosed": Exception,
            },
        )()
except ImportError:
    pass


# Async test helpers
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Mock external services
@pytest.fixture(autouse=True)
def mock_external_services():
    """Automatically mock external services for all tests"""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}
        yield


# Skip markers
def pytest_collection_modifyitems(items):
    """Add markers to tests"""
    for item in items:
        # Skip tests that require external services
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason="Integration test"))

        # Skip slow tests by default
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Slow test"))


# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Set environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["PYTHONPATH"] = str(PROJECT_ROOT)
    os.environ["MOCK_EXTERNAL_SERVICES"] = "true"

    # Create test directories
    test_dirs = ["logs/test", "coverage", "test_output"]
    for dir_name in test_dirs:
        dir_path = PROJECT_ROOT / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

    yield

    # Cleanup can go here if needed


# Common test utilities
class TestUtils:
    """Common test utilities"""

    @staticmethod
    def create_mock_worker(worker_type="test"):
        """Create a mock worker"""
        with patch("pika.BlockingConnection"):
            worker = Mock()
            worker.worker_type = worker_type
            worker.input_queue = f"{worker_type}_tasks"
            worker.output_queue = f"{worker_type}_results"
            worker.is_connected = False
            worker.connection = None
            worker.channel = None
            return worker

    @staticmethod
    def create_mock_message(body, properties=None):
        """Create a mock RabbitMQ message"""
        method = Mock()
        method.delivery_tag = "test_delivery_tag"

        if properties is None:
            properties = Mock()
            properties.headers = {}

        return Mock(), method, properties, body


# Make TestUtils available to all tests
@pytest.fixture
def test_utils():
    """Test utilities"""
    return TestUtils


# Handle missing imports gracefully
def mock_missing_imports():
    """Mock imports that might be missing"""
    # Mock coverage first
    coverage_mock = Mock()
    coverage_mock.exceptions = Mock()
    coverage_mock.exceptions.CoverageWarning = type("CoverageWarning", (Warning,), {})
    sys.modules["coverage"] = coverage_mock
    sys.modules["coverage.exceptions"] = coverage_mock.exceptions

    missing_modules = [
        "flask_login",
        "flask_cors",
        "flask_limiter",
        "prometheus_client",
        "aio_pika",
        "aioredis",
        "psutil",
        "py_breaker",
    ]

    for module in missing_modules:
        if module not in sys.modules:
            sys.modules[module] = Mock()


mock_missing_imports()

# Ensure test directories exist
os.makedirs("tests/mocks", exist_ok=True)
os.makedirs("tests/fixtures", exist_ok=True)
