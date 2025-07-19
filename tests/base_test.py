#!/usr/bin/env python3
"""
Base test class for all Elders Guild tests
Restored by Elder Council Emergency Response
"""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest


class WorkerTestCase(unittest.TestCase):
    """ワーカークラスのテスト用基底クラス"""

    def setUp(self):
        """テストセットアップ"""
        self.mock_config = {"test_mode": True, "log_level": "DEBUG"}


class ManagerTestCase(unittest.TestCase):
    """マネージャークラスのテスト用基底クラス"""

    def setUp(self):
        """テストセットアップ"""
        self.mock_config = {"test_mode": True, "timeout": 30}

    def tearDown(self):
        """テストクリーンアップ"""
        pass

    """Base test class for all worker tests"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()

        # Mock RabbitMQ connection
        self.mock_rabbit = Mock()
        self.mock_channel = Mock()
        self.mock_rabbit.channel.return_value = self.mock_channel

        # Mock logger
        self.mock_logger = Mock()

        # Mock common dependencies
        self.mock_redis = Mock()
        self.mock_db = Mock()

        # Common test data
        self.test_task_data = {
            "task_id": "test-123",
            "type": "test_task",
            "data": {"test": True},
        }

    def tearDown(self):
        """Clean up after tests"""
        super().tearDown()
        # Reset all mocks
        self.mock_rabbit.reset_mock()
        self.mock_logger.reset_mock()


class AsyncWorkerTestCase(WorkerTestCase):
    """Base test class for async workers"""

    def setUp(self):
        super().setUp()
        # Additional async-specific setup
        self.mock_aio_channel = Mock()
        self.mock_aio_connection = Mock()


class IntegrationTestCase(unittest.TestCase):
    """Base test class for integration tests"""

    def setUp(self):
        super().setUp()
        self.test_env = os.environ.copy()
        os.environ["TEST_MODE"] = "true"

    def tearDown(self):
        super().tearDown()
        os.environ.clear()
        os.environ.update(self.test_env)


# Alias for backward compatibility
BaseTestCase = ManagerTestCase
