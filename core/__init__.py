"""
AI Company Core - 共通基盤モジュール

このパッケージはAI Companyシステムの共通基盤を提供します。
"""

from .base_worker_ja import BaseWorker
from .base_manager import BaseManager
from .common_utils import setup_logging, get_project_paths, EMOJI, generate_task_id, format_filesize, truncate_text
from .config import AICompanyConfig, get_config, reload_config
from .prompt_template_mixin import PromptTemplateMixin
from .messages import messages, msg
from .error_handler_mixin import ErrorSeverity, ErrorCategory, with_error_handling

__all__ = [
    'BaseWorker',
    'BaseManager',
    'setup_logging',
    'get_project_paths',
    'AICompanyConfig',
    'get_config',
    'reload_config',
    'EMOJI',
    'generate_task_id',
    'format_filesize',
    'truncate_text',
    'PromptTemplateMixin',
    'messages',
    'msg',
    'ErrorSeverity',
    'ErrorCategory',
    'with_error_handling'
]

__version__ = '1.0.0'
