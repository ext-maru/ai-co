#!/usr/bin/env python3
"""
BaseWorker日本語拡張
既存のBaseWorkerに日本語メッセージ機能を追加
"""

import os
from .base_worker import BaseWorker as OriginalBaseWorker
from .messages import msg
from .config import get_config

class BaseWorker(OriginalBaseWorker):
    """日本語対応BaseWorker"""
    
    def __init__(self, worker_type: str, worker_id: str = None):
        super().__init__(worker_type, worker_id)
        
        # 起動メッセージを日本語化
        self.logger.info(msg('worker_started', 
                           worker_type=self.worker_type,
                           pid=os.getpid()))
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        """エラーハンドリング（日本語化）"""
        error_msg = msg('worker_error', error=str(error))
        self.logger.error(f"{context}: {error_msg}" if context else error_msg)
        
        # 元の処理も実行
        super().handle_error(error, context)
    
    def log_task_start(self, task_id: str, task_type: str = None):
        """タスク開始ログ（日本語）"""
        self.logger.info(msg('task_started',
                           task_id=task_id,
                           task_type=task_type or self.worker_type))
    
    def log_task_complete(self, task_id: str, duration: float = 0, files: int = 0):
        """タスク完了ログ（日本語）"""
        self.logger.info(msg('task_completed',
                           task_id=task_id,
                           duration=duration,
                           files=files))
    
    def log_task_failed(self, task_id: str, error: Exception):
        """タスク失敗ログ（日本語）"""
        self.logger.error(msg('task_failed',
                            task_id=task_id,
                            error_type=error.__class__.__name__,
                            error_msg=str(error)))
    
    def _shutdown(self):
        """シャットダウン処理（日本語化）"""
        self.logger.info(msg('worker_stopped', worker_type=self.worker_type))
        super()._shutdown()
