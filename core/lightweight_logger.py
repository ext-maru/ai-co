#!/usr/bin/env python3
"""
軽量ロガー実装
structlogの代替として、依存関係を最小限に抑えた構造化ログ機能
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import sys
from pathlib import Path

class LightweightStructuredLogger:
    """
    軽量な構造化ログ実装
    
    Features:
    - JSON形式のログ出力
    - コンテキスト管理
    - 複数出力先対応
    - パフォーマンス重視
    """
    
    def __init__(
        self, 
        name: str = "ai_company",
        level: str = "INFO",
        output_file: Optional[str] = None,
        console_output: bool = True
    ):
        self.name = name
        self.level = getattr(logging, level.upper())
        self.context = {}
        
        # 標準ロガーの設定
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # 既存のハンドラーをクリア
        self.logger.handlers.clear()
        
        # フォーマッター
        formatter = StructuredFormatter()
        
        # コンソール出力
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # ファイル出力
        if output_file:
            file_handler = logging.FileHandler(output_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def bind(self, **kwargs) -> 'LightweightStructuredLogger':
        """コンテキストの追加"""
        new_logger = LightweightStructuredLogger.__new__(LightweightStructuredLogger)
        new_logger.name = self.name
        new_logger.level = self.level
        new_logger.logger = self.logger
        new_logger.context = {**self.context, **kwargs}
        return new_logger
    
    def unbind(self, *keys) -> 'LightweightStructuredLogger':
        """コンテキストの削除"""
        new_logger = LightweightStructuredLogger.__new__(LightweightStructuredLogger)
        new_logger.name = self.name
        new_logger.level = self.level
        new_logger.logger = self.logger
        new_logger.context = {k: v for k, v in self.context.items() if k not in keys}
        return new_logger
    
    def _log(self, level: str, message: str, **kwargs):
        """内部ログ処理"""
        log_level = getattr(logging, level.upper())
        
        if self.logger.isEnabledFor(log_level):
            # ログデータの構築
            log_data = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': level.upper(),
                'logger': self.name,
                'message': message,
                **self.context,
                **kwargs
            }
            
            # ログ出力（StructuredFormatterが処理）
            record = logging.LogRecord(
                name=self.name,
                level=log_level,
                pathname='',
                lineno=0,
                msg=log_data,
                args=(),
                exc_info=None
            )
            
            self.logger.handle(record)
    
    def debug(self, message: str, **kwargs):
        """デバッグログ"""
        self._log('debug', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """情報ログ"""
        self._log('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告ログ"""
        self._log('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """エラーログ"""
        self._log('error', message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """重要ログ"""
        self._log('critical', message, **kwargs)

class StructuredFormatter(logging.Formatter):
    """構造化ログのフォーマッター"""
    
    def format(self, record):
        if isinstance(record.msg, dict):
            # 構造化データの場合
            log_data = record.msg.copy()
            
            # 例外情報の追加
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
        else:
            # 通常のログメッセージの場合
            log_data = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': str(record.msg),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))

# グローバルロガーインスタンス
_global_loggers: Dict[str, LightweightStructuredLogger] = {}

def get_logger(name: str = "ai_company") -> LightweightStructuredLogger:
    """
    軽量構造化ロガーの取得
    structlog.get_logger()の代替
    """
    if name not in _global_loggers:
        # ログディレクトリの確保
        log_dir = Path("/home/aicompany/ai_co/logs")
        log_dir.mkdir(exist_ok=True)
        
        # ログファイルパス
        log_file = log_dir / f"{name}.log"
        
        _global_loggers[name] = LightweightStructuredLogger(
            name=name,
            level="INFO",
            output_file=str(log_file),
            console_output=True
        )
    
    return _global_loggers[name]

# Backward compatibility
def configure_logging(level: str = "INFO", output_dir: str = "/home/aicompany/ai_co/logs"):
    """ログ設定の初期化"""
    # ログディレクトリの作成
    Path(output_dir).mkdir(exist_ok=True)
    
    # ルートロガーの設定
    root_logger = get_logger("ai_company")
    root_logger.info("Logging configured", level=level, output_dir=output_dir)
    
    return root_logger

class LoggingMixin:
    """ロギング機能を追加するMixin"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger_name = getattr(self, 'logger_name', self.__class__.__name__.lower())
        self.logger = get_logger(logger_name)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """パフォーマンスログ"""
        self.logger.info(
            f"Performance: {operation}",
            operation=operation,
            duration=duration,
            **kwargs
        )
    
    def log_error(self, error: Exception, context: str = "", **kwargs):
        """エラーログ"""
        self.logger.error(
            f"Error in {context}: {str(error)}",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            **kwargs
        )

# 使用例とテスト
if __name__ == "__main__":
    # 基本的な使用例
    logger = get_logger("test")
    
    logger.info("System starting", component="test", version="1.0")
    
    # コンテキスト付きログ
    task_logger = logger.bind(task_id="test_001", user_id="admin")
    task_logger.info("Task started", action="processing")
    task_logger.info("Task completed", duration=1.5, status="success")
    
    # エラーログ
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Test error occurred", error=str(e), error_type=type(e).__name__)
    
    print("✅ 軽量ロガーテスト完了")