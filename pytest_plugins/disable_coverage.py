"""
Disable coverage plugin that's causing issues
"""
import sys
from unittest.mock import Mock

# Mock coverage module before pytest-cov can import it
coverage_mock = Mock()
coverage_mock.exceptions = Mock()
coverage_mock.exceptions.CoverageWarning = type('CoverageWarning', (Warning,), {})
sys.modules['coverage'] = coverage_mock
sys.modules['coverage.exceptions'] = coverage_mock.exceptions

def pytest_configure(config):
    """Disable pytest-cov plugin"""
    try:
        config.pluginmanager.unregister(name="pytest_cov")
    except:
        pass