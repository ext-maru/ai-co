#!/usr/bin/env python3
"""
Elders Guild pytest基底テスト設定
Issue #93: OSS移行プロジェクト - unittest → pytest

pytestフィクスチャベースの基底テスト構造
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ===== 基本フィクスチャ =====

@pytest.fixture
def mock_config():
    """基本テスト設定フィクスチャ"""

@pytest.fixture
def mock_logger():
    """モックロガーフィクスチャ"""
    return Mock()

@pytest.fixture
def test_task_data():
    """テストタスクデータフィクスチャ"""
    return {
        "task_id": "test-123",
        "type": "test_task",
        "data": {"test": True},
        "priority": "medium",
        "metadata": {"created_by": "pytest"}
    }

# ===== ワーカーテスト用フィクスチャ =====

@pytest.fixture
def mock_rabbit():
    """RabbitMQモックフィクスチャ"""
    mock = Mock()
    mock_channel = Mock()
    mock.channel.return_value = mock_channel
    return mock

@pytest.fixture
def mock_channel(mock_rabbit):
    """RabbitMQチャンネルモックフィクスチャ"""
    return mock_rabbit.channel.return_value

@pytest.fixture
def mock_redis():
    """Redisモックフィクスチャ"""
    mock = Mock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    return mock

@pytest.fixture
def mock_db():
    """データベースモックフィクスチャ"""
    mock = Mock()
    mock.execute.return_value = True
    mock.fetch.return_value = []
    return mock

# ===== 非同期ワーカー用フィクスチャ =====

@pytest.fixture
def mock_aio_connection():
    """非同期接続モックフィクスチャ"""
    return Mock()

@pytest.fixture
def mock_aio_channel(mock_aio_connection):
    """非同期チャンネルモックフィクスチャ"""
    mock = Mock()
    mock_aio_connection.channel.return_value = mock
    return mock

# ===== 統合テスト用フィクスチャ =====

@pytest.fixture
def test_environment():
    """テスト環境変数フィクスチャ"""
    original_env = os.environ.copy()
    os.environ["TEST_MODE"] = "true"

    yield os.environ
    
    # クリーンアップ
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture

    """一時作業ディレクトリフィクスチャ"""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    yield tmp_path
    
    os.chdir(original_cwd)

# ===== 共通セットアップフィクスチャ =====

@pytest.fixture
def worker_test_setup(
    mock_config, mock_logger, mock_rabbit, mock_redis, mock_db, test_task_data
):
    """ワーカーテスト用包括的セットアップ"""
    return {
        "config": mock_config,
        "logger": mock_logger,
        "rabbit": mock_rabbit,
        "redis": mock_redis,
        "db": mock_db,
        "task_data": test_task_data
    }

@pytest.fixture
def async_worker_test_setup(
    worker_test_setup, mock_aio_connection, mock_aio_channel
):
    """非同期ワーカーテスト用包括的セットアップ"""
    setup = worker_test_setup.copy()
    setup.update({
        "aio_connection": mock_aio_connection,
        "aio_channel": mock_aio_channel
    })
    return setup

@pytest.fixture

    """統合テスト用包括的セットアップ"""
    return {
        "environment": test_environment,

        "config": mock_config
    }

# ===== エラーテスト用フィクスチャ =====

@pytest.fixture
def mock_failing_connection():
    """接続失敗モックフィクスチャ"""
    mock = Mock()
    mock.connect.side_effect = ConnectionError("Connection failed")
    return mock

@pytest.fixture
def mock_timeout_operation():
    """タイムアウトモックフィクスチャ"""
    mock = Mock()
    mock.execute.side_effect = TimeoutError("Operation timed out")
    return mock

# ===== パフォーマンステスト用フィクスチャ =====

@pytest.fixture
def performance_timer():
    """パフォーマンス測定フィクスチャ"""
    import time
    
    class Timer:
        """Timerクラス"""
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.perf_counter()
            
        def stop(self):
            self.end_time = time.perf_counter()
            
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()

# ===== マーカー定義 =====

# カスタムマーカーの定義
pytest_plugins = []

def pytest_configure(config):
    """pytest設定"""
    # カスタムマーカー登録
    config.addinivalue_line("markers", "worker: mark test as a worker test")
    config.addinivalue_line("markers", "manager: mark test as a manager test")
    config.addinivalue_line("markers", "async_worker: mark test as an async worker test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")

# ===== ヘルパー関数 =====

def assert_task_processed(mock_channel, task_data):
    """タスク処理アサーションヘルパー"""
    assert mock_channel.basic_publish.called
    args, kwargs = mock_channel.basic_publish.call_args
    assert task_data["task_id"] in str(kwargs)

def assert_error_logged(mock_logger, error_message):
    """エラーログアサーションヘルパー"""
    assert mock_logger.error.called
    args, kwargs = mock_logger.error.call_args
    assert error_message in str(args[0])

def create_test_task(task_type="test", priority="medium", **kwargs):
    """テストタスク作成ヘルパー"""
    base_task = {
        "task_id": f"test-{task_type}-{id(kwargs)}",
        "type": task_type,
        "priority": priority,
        "data": {"test": True},
        "metadata": {"created_by": "pytest_helper"}
    }
    base_task.update(kwargs)
    return base_task

# ===== 後方互換性のためのクラスベースアプローチ =====

class PytestWorkerTestBase:
    """pytest版ワーカーテスト基底クラス（後方互換性用）"""
    
    @pytest.fixture(autouse=True)
    def setup_worker_test(self, worker_test_setup):
        """ワーカーテスト自動セットアップ"""
        self.config = worker_test_setup["config"]
        self.logger = worker_test_setup["logger"]
        self.rabbit = worker_test_setup["rabbit"]
        self.redis = worker_test_setup["redis"]
        self.db = worker_test_setup["db"]
        self.task_data = worker_test_setup["task_data"]

class PytestAsyncWorkerTestBase:
    """pytest版非同期ワーカーテスト基底クラス（後方互換性用）"""
    
    @pytest.fixture(autouse=True)
    def setup_async_worker_test(self, async_worker_test_setup):
        """非同期ワーカーテスト自動セットアップ"""
        self.config = async_worker_test_setup["config"]
        self.logger = async_worker_test_setup["logger"]
        self.rabbit = async_worker_test_setup["rabbit"]
        self.redis = async_worker_test_setup["redis"]
        self.db = async_worker_test_setup["db"]
        self.task_data = async_worker_test_setup["task_data"]
        self.aio_connection = async_worker_test_setup["aio_connection"]
        self.aio_channel = async_worker_test_setup["aio_channel"]

class PytestIntegrationTestBase:
    """pytest版統合テスト基底クラス（後方互換性用）"""
    
    @pytest.fixture(autouse=True)
    def setup_integration_test(self, integration_test_setup):
        """統合テスト自動セットアップ"""
        self.environment = integration_test_setup["environment"]
        self.workdir = integration_test_setup["workdir"]
        self.config = integration_test_setup["config"]

# エイリアス定義（unittest版との互換性）
WorkerTestCase = PytestWorkerTestBase
AsyncWorkerTestCase = PytestAsyncWorkerTestBase
IntegrationTestCase = PytestIntegrationTestBase
ManagerTestCase = PytestWorkerTestBase  # 後方互換性
BaseTestCase = PytestWorkerTestBase     # 後方互換性