#!/usr/bin/env python3
"""
Claude Elder Error Wrapper v1.0
クロードエルダーのエラー処理を自動化するラッパーシステム

使用方法:
1. @incident_aware デコレータでエラー自動処理
2. with claude_error_context(): でコンテキスト管理
3. manual_error_report() で手動報告
"""

import asyncio
import contextlib
from typing import Any, Dict, Optional, Callable
from functools import wraps
import logging

# インシデント統合システムをインポート
try:
    from .claude_elder_incident_integration import (
        get_incident_integration,
        claude_error_handler,
        incident_aware_decorator
    )
except ImportError:
    # 直接実行時のフォールバック
    from claude_elder_incident_integration import (
        get_incident_integration,
        claude_error_handler,
        incident_aware_decorator
    )

logger = logging.getLogger(__name__)

class ClaudeElderErrorWrapper:
    """クロードエルダーエラーラッパー"""
    
    def __init__(self):
        self.incident_integration = get_incident_integration()
        self.auto_report_enabled = True
        self.context_stack = []
    
    def enable_auto_report(self):
        """自動報告を有効化"""
        self.auto_report_enabled = True
        logger.info("🔄 Claude Elder auto error reporting enabled")
    
    def disable_auto_report(self):
        """自動報告を無効化"""
        self.auto_report_enabled = False
        logger.info("🔄 Claude Elder auto error reporting disabled")
    
    @contextlib.contextmanager
    def error_context(self, context: Dict[str, Any]):
        """エラーコンテキスト管理"""
        self.context_stack.append(context)
        try:
            yield
        except Exception as e:
            if self.auto_report_enabled:
                # 現在のコンテキストを統合
                merged_context = {}
                for ctx in self.context_stack:
                    merged_context.update(ctx)
                
                # 非同期処理として実行
                asyncio.create_task(self._handle_error(e, merged_context))
            raise
        finally:
            self.context_stack.pop()
    
    async def _handle_error(self, error: Exception, context: Dict[str, Any]):
        """エラー処理（内部使用）"""
        try:
            await claude_error_handler(error, context)
        except Exception as handler_error:
            logger.error(f"Error handler failed: {handler_error}")
    
    def manual_report(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """手動エラー報告"""
        if context is None:
            context = {}
        
        # 現在のコンテキストスタックを追加
        for ctx in self.context_stack:
            context.update(ctx)
        
        # 非同期処理として実行
        asyncio.create_task(self._handle_error(error, context))
        logger.info(f"🚨 Manual error report submitted: {error}")

# グローバルインスタンス
_error_wrapper = ClaudeElderErrorWrapper()

def get_error_wrapper() -> ClaudeElderErrorWrapper:
    """グローバルエラーラッパー取得"""
    return _error_wrapper

# 便利関数とデコレータ
def claude_error_context(context: Dict[str, Any]):
    """エラーコンテキスト（便利関数）"""
    return _error_wrapper.error_context(context)

def incident_aware(func: Callable):
    """インシデント対応デコレータ（改良版）"""
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        context = {
            "function": func.__name__,
            "module": func.__module__,
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()),
            "type": "sync_function"
        }
        
        with claude_error_context(context):
            return func(*args, **kwargs)
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        context = {
            "function": func.__name__,
            "module": func.__module__,
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()),
            "type": "async_function"
        }
        
        with claude_error_context(context):
            return await func(*args, **kwargs)
    
    # 関数が非同期かどうかで適切なラッパーを返す
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def manual_error_report(error: Exception, context: Optional[Dict[str, Any]] = None):
    """手動エラー報告（便利関数）"""
    _error_wrapper.manual_report(error, context)

def enable_auto_error_reporting():
    """自動エラー報告を有効化"""
    _error_wrapper.enable_auto_report()

def disable_auto_error_reporting():
    """自動エラー報告を無効化"""
    _error_wrapper.disable_auto_report()

# 使用例
if __name__ == "__main__":
    import time
    
    # 使用例1: デコレータ
    @incident_aware
    def example_function():
        print("実行中...")
        raise ValueError("デモエラー")
    
    # 使用例2: コンテキストマネージャー
    def example_with_context():
        with claude_error_context({"task": "demo", "important": True}):
            print("コンテキスト内で実行中...")
            raise ImportError("デモインポートエラー")
    
    # 使用例3: 手動報告
    def example_manual_report():
        try:
            raise RuntimeError("手動報告用エラー")
        except Exception as e:
            manual_error_report(e, {"manually_reported": True})
            print("手動報告完了")
    
    print("🚨 Claude Elder Error Wrapper Demo")
    print("=" * 40)
    
    # デモ実行
    try:
        example_function()
    except ValueError:
        print("✅ デコレータテスト完了")
    
    time.sleep(1)
    
    try:
        example_with_context()
    except ImportError:
        print("✅ コンテキストテスト完了")
    
    time.sleep(1)
    
    example_manual_report()
    print("✅ 手動報告テスト完了")
    
    print("\n📊 実際のプロジェクトでは以下のように使用:")
    print("""
    # 1. 関数デコレータ
    @incident_aware
    def my_function():
        # エラーが発生すると自動的にインシデント報告
        pass
    
    # 2. コンテキストマネージャー
    with claude_error_context({"task": "important_task"}):
        # この中でのエラーはコンテキスト付きで報告
        pass
    
    # 3. 手動報告
    try:
        risky_operation()
    except Exception as e:
        manual_error_report(e, {"additional_info": "value"})
    """)