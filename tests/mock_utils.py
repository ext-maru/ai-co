"""
包括的モックユーティリティ - エルダー評議会承認
"""
import sys
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# PROJECT_ROOT設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_mock_config():
    """設定モック"""
    config = MagicMock()
    config.get.return_value = "test_value"
    config.RABBITMQ_HOST = "localhost"
    config.REDIS_HOST = "localhost"
    return config

def create_mock_logger():
    """ロガーモック"""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger

def create_mock_connection():
    """接続モック"""
    conn = MagicMock()
    conn.is_open = True
    conn.close = MagicMock()
    return conn

def create_mock_channel():
    """チャンネルモック"""
    channel = MagicMock()
    channel.basic_publish = MagicMock()
    channel.queue_declare = MagicMock()
    return channel

def create_mock_worker():
    """ワーカーモック"""
    worker = MagicMock()
    worker.start = MagicMock()
    worker.stop = MagicMock()
    worker.is_running = True
    return worker

# 基本的なモック辞書
STANDARD_MOCKS = {
    'config': create_mock_config,
    'logger': create_mock_logger,
    'connection': create_mock_connection,
    'channel': create_mock_channel,
    'worker': create_mock_worker
}

def setup_test_environment():
    """テスト環境のセットアップ"""
    os.environ['TESTING'] = 'true'
    os.environ['PROJECT_ROOT'] = str(PROJECT_ROOT)
    os.environ['AI_COMPANY_ENV'] = 'test'
