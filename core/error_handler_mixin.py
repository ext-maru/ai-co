#!/usr/bin/env python3
"""
ErrorHandlerMixin - 統一エラーハンドリングMixin

すべてのワーカーで統一されたエラー処理を提供
エラー分類、自動リトライ、エラー通知、インシデント記録を含む
"""

import json
import time
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from functools import wraps

class ErrorCategory:
    """エラーカテゴリー定義"""
    NETWORK = "network"
    API = "api"
    DATA = "data"
    SYSTEM = "system"
    PERMISSION = "permission"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

class ErrorSeverity:
    """エラー深刻度定義"""
    CRITICAL = "critical"  # システム停止級
    HIGH = "high"         # 機能停止級
    MEDIUM = "medium"     # 一部機能影響
    LOW = "low"           # 軽微な影響
    INFO = "info"         # 情報レベル

class ErrorHandlerMixin:
    """統一エラーハンドリングMixin"""
    
    def __init__(self):
        """エラーハンドラー初期化"""
        self.error_count = 0
        self.error_history = []
        self.max_error_history = 100
        self.retry_config = {
            ErrorCategory.NETWORK: {"max_attempts": 3, "delay": 5},
            ErrorCategory.API: {"max_attempts": 2, "delay": 10},
            ErrorCategory.TIMEOUT: {"max_attempts": 2, "delay": 5},
            ErrorCategory.DATA: {"max_attempts": 1, "delay": 0},
        }
        
        # エラーインテリジェンスワーカーへの通知設定
        self.error_intelligence_enabled = True
        
    def handle_error(self, error: Exception, context: Dict[str, Any], 
                    severity: str = ErrorSeverity.MEDIUM,
                    retry_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        統一エラーハンドリング
        
        Args:
            error: 発生したエラー
            context: エラーコンテキスト情報
            severity: エラー深刻度
            retry_callback: リトライ時に実行する関数
            
        Returns:
            エラー処理結果
        """
        # エラー分類
        category = self._categorize_error(error)
        
        # エラー情報構築
        error_info = {
            "error_id": f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.error_count}",
            "timestamp": datetime.now().isoformat(),
            "worker_id": getattr(self, 'worker_id', 'unknown'),
            "worker_type": getattr(self, 'worker_type', 'unknown'),
            "category": category,
            "severity": severity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "stacktrace": traceback.format_exc()
        }
        
        # エラーログ出力（統一フォーマット）
        self._log_error(error_info)
        
        # エラー履歴に追加
        self._add_to_history(error_info)
        
        # エラー通知
        self._notify_error(error_info)
        
        # リトライ判定
        if retry_callback and self._should_retry(category, context):
            return self._execute_retry(retry_callback, error_info, category)
        
        # エラーインテリジェンスワーカーへ送信
        if self.error_intelligence_enabled and severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            self._send_to_error_intelligence(error_info)
        
        self.error_count += 1
        
        return {
            "handled": True,
            "error_id": error_info["error_id"],
            "action_taken": "logged_and_notified",
            "retry_attempted": False
        }
    
    def _categorize_error(self, error: Exception) -> str:
        """エラーを分類"""
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        # ネットワークエラー
        if any(keyword in error_msg for keyword in ['connection', 'network', 'refused', 'timeout']):
            return ErrorCategory.NETWORK
            
        # APIエラー
        if any(keyword in error_msg for keyword in ['api', 'rate limit', 'unauthorized', 'forbidden']):
            return ErrorCategory.API
            
        # データエラー
        if any(keyword in error_msg for keyword in ['json', 'decode', 'parse', 'validation']):
            return ErrorCategory.DATA
            
        # タイムアウト
        if 'timeout' in error_msg:
            return ErrorCategory.TIMEOUT
            
        # パーミッションエラー
        if any(keyword in error_msg for keyword in ['permission', 'denied', 'access']):
            return ErrorCategory.PERMISSION
            
        # システムエラー
        if any(keyword in error_type for keyword in ['OSError', 'SystemError', 'RuntimeError']):
            return ErrorCategory.SYSTEM
            
        return ErrorCategory.UNKNOWN
    
    def _log_error(self, error_info: Dict[str, Any]):
        """統一フォーマットでエラーログ出力"""
        log_level = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.INFO: logging.DEBUG
        }.get(error_info['severity'], logging.ERROR)
        
        # 統一ログフォーマット
        log_message = (
            f"[{error_info['error_id']}] "
            f"{error_info['severity'].upper()} | "
            f"{error_info['category']} | "
            f"{error_info['error_type']}: {error_info['error_message']} | "
            f"Context: {json.dumps(error_info['context'], ensure_ascii=False)}"
        )
        
        if hasattr(self, 'logger'):
            self.logger.log(log_level, log_message)
        else:
            logging.log(log_level, log_message)
        
        # デバッグモードではスタックトレースも出力
        if log_level >= logging.ERROR:
            if hasattr(self, 'logger'):
                self.logger.debug(f"Stacktrace:\n{error_info['stacktrace']}")
    
    def _add_to_history(self, error_info: Dict[str, Any]):
        """エラー履歴に追加"""
        self.error_history.append(error_info)
        
        # 履歴サイズ制限
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history:]
    
    def _notify_error(self, error_info: Dict[str, Any]):
        """エラー通知（Slack等）"""
        if error_info['severity'] in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            try:
                # Slack通知
                if hasattr(self, 'slack_notifier'):
                    message = (
                        f"🚨 {error_info['severity'].upper()} Error\n"
                        f"Worker: {error_info['worker_type']} ({error_info['worker_id']})\n"
                        f"Category: {error_info['category']}\n"
                        f"Error: {error_info['error_type']} - {error_info['error_message']}\n"
                        f"ID: {error_info['error_id']}"
                    )
                    self.slack_notifier.send_error_notification(message)
            except Exception as e:
                # 通知エラーは無視（無限ループ防止）
                if hasattr(self, 'logger'):
                    self.logger.debug(f"Error notification failed: {e}")
    
    def _should_retry(self, category: str, context: Dict[str, Any]) -> bool:
        """リトライすべきか判定"""
        retry_count = context.get('retry_count', 0)
        max_attempts = self.retry_config.get(category, {}).get('max_attempts', 0)
        
        return retry_count < max_attempts
    
    def _execute_retry(self, retry_callback: Callable, error_info: Dict[str, Any], 
                      category: str) -> Dict[str, Any]:
        """リトライ実行"""
        retry_count = error_info['context'].get('retry_count', 0) + 1
        delay = self.retry_config.get(category, {}).get('delay', 5)
        
        if hasattr(self, 'logger'):
            self.logger.info(
                f"🔄 Retrying (attempt {retry_count}) after {delay}s delay... "
                f"[{error_info['error_id']}]"
            )
        
        time.sleep(delay)
        
        try:
            # リトライコンテキストを追加
            retry_context = error_info['context'].copy()
            retry_context['retry_count'] = retry_count
            retry_context['previous_error_id'] = error_info['error_id']
            
            result = retry_callback(retry_context)
            
            if hasattr(self, 'logger'):
                self.logger.info(f"✅ Retry successful [{error_info['error_id']}]")
            
            return {
                "handled": True,
                "error_id": error_info["error_id"],
                "action_taken": "retry_successful",
                "retry_attempted": True,
                "retry_count": retry_count,
                "result": result
            }
            
        except Exception as e:
            # リトライも失敗
            if hasattr(self, 'logger'):
                self.logger.error(f"❌ Retry failed [{error_info['error_id']}]: {e}")
            
            return {
                "handled": True,
                "error_id": error_info["error_id"],
                "action_taken": "retry_failed",
                "retry_attempted": True,
                "retry_count": retry_count,
                "final_error": str(e)
            }
    
    def _send_to_error_intelligence(self, error_info: Dict[str, Any]):
        """エラーインテリジェンスワーカーへ送信"""
        try:
            if hasattr(self, 'channel') and self.channel:
                message = {
                    "type": "error_analysis_request",
                    "error_info": error_info,
                    "request_auto_fix": error_info['severity'] == ErrorSeverity.CRITICAL
                }
                
                self.channel.basic_publish(
                    exchange='',
                    routing_key='ai_error_intelligence',
                    body=json.dumps(message, ensure_ascii=False)
                )
                
                if hasattr(self, 'logger'):
                    self.logger.debug(
                        f"Sent to Error Intelligence Worker [{error_info['error_id']}]"
                    )
        except Exception as e:
            # エラー送信の失敗は無視
            if hasattr(self, 'logger'):
                self.logger.debug(f"Failed to send to Error Intelligence: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計を取得"""
        if not self.error_history:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "recent_errors": []
            }
        
        # カテゴリ別集計
        by_category = {}
        by_severity = {}
        
        for error in self.error_history:
            category = error['category']
            severity = error['severity']
            
            by_category[category] = by_category.get(category, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": self.error_history[-10:]  # 最新10件
        }
    
    def clear_error_history(self):
        """エラー履歴をクリア"""
        self.error_history = []
        self.error_count = 0
        
        if hasattr(self, 'logger'):
            self.logger.info("Error history cleared")


def with_error_handling(severity: str = ErrorSeverity.MEDIUM):
    """
    エラーハンドリングデコレーター
    
    使用例:
    @with_error_handling(severity=ErrorSeverity.HIGH)
    def process_important_task(self, data):
        # 処理
        pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],  # 長すぎる場合は切り詰め
                    "kwargs": str(kwargs)[:200]
                }
                
                if hasattr(self, 'handle_error'):
                    self.handle_error(e, context, severity=severity)
                else:
                    raise
        return wrapper
    return decorator