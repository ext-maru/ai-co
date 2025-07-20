"""
unified_config_manager module
"""

import os

def get_config(key, default=None):
    return os.getenv(key, default)
