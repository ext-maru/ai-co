"""
unified_config_manager module
"""

import os

def get_config(key, default=None):
    """config取得メソッド"""
    return os.getenv(key, default)
