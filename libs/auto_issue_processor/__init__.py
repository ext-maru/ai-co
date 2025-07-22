"""
統一Auto Issue Processor
5つの既存実装を1つに統合した、一貫性のある自動Issue処理システム
"""

from .core.processor import AutoIssueProcessor
from .core.config import ProcessorConfig, get_default_config
from .utils.locking import ProcessLock

__version__ = "1.0.0"
__all__ = [
    "AutoIssueProcessor",
    "ProcessorConfig", 
    "get_default_config",
    "ProcessLock"
]