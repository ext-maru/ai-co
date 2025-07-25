"""
Import resolver to prevent circular dependencies
"""
import sys
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Pre-mock problematic imports
sys.modules['aio_pika'] = Mock()
sys.modules['slack_sdk'] = Mock()
sys.modules['redis'] = Mock()
sys.modules['psutil'] = Mock()
sys.modules['prometheus_client'] = Mock()

def safe_import(module_name):
    """Safely import a module with fallback to mock"""
    try:
        return __import__(module_name)
    except ImportError:
        mock_module = Mock()
        sys.modules[module_name] = mock_module
        return mock_module
