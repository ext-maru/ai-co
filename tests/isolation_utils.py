"""

# Mock imports for testing
try:
    # Try real imports first
    pass  # Real imports will be added here by individual tests
except ImportError:
    # Create mock classes if imports fail
    class MockWorker:
        def __init__(self, *args, **kwargs):
            pass
        async def process_message(self, *args, **kwargs):
            return {'status': 'success'}
        def process(self, *args, **kwargs):
            return {'status': 'success'}

    class MockManager:
        def __init__(self, *args, **kwargs):
            pass
        def get_config(self, *args, **kwargs):
            return {}

Test isolation utilities
"""
import functools
import gc
import threading
from unittest.mock import patch

def isolated_test(func):
    """Decorator to ensure test isolation"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Clear any running threads
        for thread in threading.enumerate():
            if thread.name.startswith('test_'):
                thread.join(timeout=1)
        
        # Run test
        try:
            result = func(*args, **kwargs)
        finally:
            # Force garbage collection
            gc.collect()
        
        return result
    
    return wrapper

class IsolatedTestCase:
    """Base class for isolated tests"""
    
    def setUp(self):
        """Set up isolated environment"""
        self._patches = []
        
        # Patch all external dependencies
        external_modules = [
            'requests',
            'redis',
            'pika',
            'slack_sdk',
            'docker',
            'psutil'
        ]
        
        for module in external_modules:
            patcher = patch(module)
            self._patches.append(patcher)
            patcher.start()
    
    def tearDown(self):
        """Clean up patches"""
        for patcher in self._patches:
            patcher.stop()
        
        # Clear any cached imports
        import sys
        modules_to_clear = [
            mod for mod in sys.modules 
            if mod.startswith('workers.') or mod.startswith('libs.')
        ]
        for mod in modules_to_clear:
            sys.modules.pop(mod, None)
