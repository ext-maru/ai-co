#!/usr/bin/env python3
"""Setup test environment with proper mocks"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Create mock modules before any imports
class MockPika:
    """Mock pika module"""

    class exceptions:
        AMQPConnectionError = Exception
        AMQPChannelError = Exception
        ConnectionClosed = Exception
        ChannelClosed = Exception
        StreamLostError = Exception

    class BlockingConnection:
        def __init__(self, *args, **kwargs):
            self.is_open = True

        def channel(self):
            return MockChannel()

        def close(self):
            self.is_open = False

    class ConnectionParameters:
        def __init__(self, **kwargs):
            pass

    class PlainCredentials:
        def __init__(self, username, password):
            pass

    class BasicProperties:
        def __init__(self, **kwargs):
            pass


class MockChannel:
    """Mock channel"""

    def __init__(self):
        self.is_open = True

    def queue_declare(self, **kwargs):
        pass

    def basic_consume(self, **kwargs):
        pass

    def basic_qos(self, **kwargs):
        pass

    def basic_ack(self, **kwargs):
        pass

    def basic_nack(self, **kwargs):
        pass

    def basic_publish(self, **kwargs):
        pass

    def start_consuming(self):
        pass

    def stop_consuming(self):
        pass

    def close(self):
        self.is_open = False


# Mock all external dependencies
mock_modules = {
    "pika": MockPika(),
    "redis": type(sys)("redis"),
    "aioredis": type(sys)("aioredis"),
    "slack_sdk": type(sys)("slack_sdk"),
    "prometheus_client": type(sys)("prometheus_client"),
    "selenium": type(sys)("selenium"),
    "playwright": type(sys)("playwright"),
    "docker": type(sys)("docker"),
}

# Inject mocks into sys.modules
for module_name, mock_module in mock_modules.items():
    sys.modules[module_name] = mock_module

# Create sub-modules
sys.modules["pika.exceptions"] = MockPika.exceptions
sys.modules["slack_sdk.web"] = type(sys)("slack_sdk.web")
sys.modules["slack_sdk.web.async_client"] = type(sys)("slack_sdk.web.async_client")
sys.modules["docker.errors"] = type(sys)("docker.errors")

print("Test environment setup complete!")
print(f"Mocked modules: {', '.join(mock_modules.keys())}")

# Run pytest with coverage
if __name__ == "__main__":
    import subprocess

    cmd = [
        "python3",
        "-m",
        "pytest",
        "--cov=libs",
        "--cov=workers",
        "--cov=core",
        "--cov=commands",
        "--cov-report=term",
        "--cov-report=html:htmlcov",
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ]

    subprocess.run(cmd)
