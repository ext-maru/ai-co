"""
Elder Flow Error Handler - エラーハンドリング強化システム
Created: 2025-07-12
Author: Claude Elder
Version: 1.0.0

エルダーフローのエラーハンドリング強化実装
- 専用例外クラス
- リトライメカニズム
- エラーリカバリー戦略
- サーキットブレーカーパターン
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, Union
from datetime import datetime, timedelta
from enum import Enum
import traceback
from functools import wraps
import json

# Type definitions
T = TypeVar("T")
ErrorHandler = Callable[[Exception], Union[T, None]]

# Elder Flow専用例外クラス
class ElderFlowError(Exception):
    """Elder Flow基底例外クラス"""

    def __init__(
        self, message: str, error_code: str = "EF000", details: Optional[Dict] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()

class SageConsultationError(ElderFlowError):
    """賢者相談エラー"""

    def __init__(self, sage_type: str, message: str, details: Optional[Dict] = None):
        """初期化メソッド"""
        super().__init__(
            f"Sage consultation failed: {sage_type} - {message}", "EF001", details
        )
        self.sage_type = sage_type

class QualityGateError(ElderFlowError):
    """品質ゲートエラー"""

    def __init__(self, gate_name: str, message: str, score: float = 0.0):
        """初期化メソッド"""
        super().__init__(
            f"Quality gate failed: {gate_name} - {message}",
            "EF002",
            {"gate_name": gate_name, "score": score},
        )
        self.gate_name = gate_name
        self.score = score

class ServantExecutionError(ElderFlowError):
    """サーバント実行エラー"""

    def __init__(self, servant_type: str, message: str, task_id: Optional[str] = None):
        """初期化メソッド"""
        super().__init__(
            f"Servant execution failed: {servant_type} - {message}",
            "EF003",
            {"servant_type": servant_type, "task_id": task_id},
        )
        self.servant_type = servant_type

class GitAutomationError(ElderFlowError):
    """Git自動化エラー"""

    def __init__(self, operation: str, message: str, repository: Optional[str] = None):
        """初期化メソッド"""
        super().__init__(
            f"Git automation failed: {operation} - {message}",
            "EF004",
            {"operation": operation, "repository": repository},
        )
        self.operation = operation

class CouncilReportError(ElderFlowError):
    """評議会報告エラー"""

    def __init__(self, report_type: str, message: str):
        """初期化メソッド"""
        super().__init__(
            f"Council report failed: {report_type} - {message}",
            "EF005",
            {"report_type": report_type},
        )
        self.report_type = report_type

# リトライ戦略
class RetryStrategy(Enum):
    """リトライ戦略"""

    EXPONENTIAL = "exponential"  # 指数バックオフ
    LINEAR = "linear"  # 線形バックオフ
    FIXED = "fixed"  # 固定間隔

class RetryConfig:
    """リトライ設定"""

    def __init__(
        self,

        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):

        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

        """リトライ遅延時間を計算"""
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = min(

            )
        elif self.strategy == RetryStrategy.LINEAR:

        else:  # FIXED
            delay = self.base_delay

        # ジッター追加（ランダム性）
        if self.jitter:
            import random

            delay *= 0.5 + random.random()

        return delay

# サーキットブレーカー
class CircuitState(Enum):
    """サーキットブレーカー状態"""

    CLOSED = "closed"  # 正常（通電）
    OPEN = "open"  # 異常（遮断）
    HALF_OPEN = "half_open"  # 半開（テスト中）

class CircuitBreaker:
    """サーキットブレーカーパターン実装"""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.logger = logging.getLogger(f"CircuitBreaker.{name}")

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """関数呼び出しをサーキットブレーカー経由で実行"""
        if self.state == CircuitState.OPEN:

                self.state = CircuitState.HALF_OPEN

            else:
                raise ElderFlowError(
                    f"Circuit breaker {self.name} is OPEN",
                    "EF100",
                    {"state": self.state.value, "failures": self.failure_count},
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

        """リセットを試みるべきか判定"""
        return (
            self.last_failure_time
            and datetime.now() - self.last_failure_time
            > timedelta(seconds=self.recovery_timeout)
        )

    def _on_success(self):
        """成功時の処理"""
        if self.state == CircuitState.HALF_OPEN:
            self.logger.info(f"Circuit breaker {self.name} reset to CLOSED")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None

    def _on_failure(self):
        """失敗時の処理"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.logger.warning(f"Circuit breaker {self.name} tripped to OPEN")
            self.state = CircuitState.OPEN

# エラーハンドラークラス
class ElderFlowErrorHandler:
    """Elder Flowエラーハンドラー"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger("ElderFlowErrorHandler")
        self.error_history = []
        self.recovery_strategies = {}
        self.circuit_breakers = {}

    def retry_async(self, config: Optional[RetryConfig] = None):
        """非同期関数用リトライデコレータ"""
        if config is None:
            config = RetryConfig()

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            """decoratorメソッド"""
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                """wrapperメソッド"""
                last_exception = None

                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        self.logger.warning(

                        )

                            self.logger.info(f"Retrying in {delay:0.2f} seconds...")
                            await asyncio.sleep(delay)
                        else:
                            self.logger.error(

                            )

                raise last_exception

            return wrapper

        return decorator

    def register_recovery_strategy(self, error_type: type, strategy: ErrorHandler):
        """エラーリカバリー戦略を登録"""
        self.recovery_strategies[error_type] = strategy
        self.logger.info(f"Registered recovery strategy for {error_type.__name__}")

    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """サーキットブレーカーを取得（なければ作成）"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, **kwargs)
        return self.circuit_breakers[name]

    async def handle_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Optional[Any]:
        """エラーハンドリング実行"""
        # エラー履歴に記録
        self.error_history.append(
            {
                "timestamp": datetime.now(),
                "error_type": type(error).__name__,
                "message": str(error),
                "context": context,
                "traceback": traceback.format_exc(),
            }
        )

        # リカバリー戦略を検索
        for error_type, strategy in self.recovery_strategies.items():
            if isinstance(error, error_type):
                self.logger.info(
                    f"Applying recovery strategy for {error_type.__name__}"
                )
                try:
                    return (
                        await strategy(error)
                        if asyncio.iscoroutinefunction(strategy)
                        else strategy(error)
                    )
                except Exception as recovery_error:
                    self.logger.error(f"Recovery strategy failed: {recovery_error}")

        # デフォルトエラーハンドリング
        if isinstance(error, ElderFlowError):
            self.logger.error(
                f"Elder Flow Error [{error.error_code}]: {error}",
                extra={"details": error.details},
            )
        else:
            self.logger.error(f"Unhandled error: {error}")

        return None

    def get_error_summary(self) -> Dict[str, Any]:
        """エラーサマリーを取得"""
        if not self.error_history:
            return {"total_errors": 0, "error_types": {}}

        error_types = {}
        for error in self.error_history:
            error_type = error["error_type"]
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1

        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "last_error": self.error_history[-1] if self.error_history else None,
            "circuit_breakers": {
                name: cb.state.value for name, cb in self.circuit_breakers.items()
            },
        }

# グローバルエラーハンドラーインスタンス
error_handler = ElderFlowErrorHandler()

# 便利なデコレータ
def with_error_handling(func: Callable[..., T]) -> Callable[..., T]:
    """エラーハンドリング付きデコレータ"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        """wrapperメソッド"""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            context = {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs),
            }
            result = await error_handler.handle_error(e, context)
            if result is not None:
                return result
            raise

    return wrapper

# エクスポート
__all__ = [
    "ElderFlowError",
    "SageConsultationError",
    "QualityGateError",
    "ServantExecutionError",
    "GitAutomationError",
    "CouncilReportError",
    "RetryStrategy",
    "RetryConfig",
    "CircuitBreaker",
    "ElderFlowErrorHandler",
    "error_handler",
    "with_error_handling",
]
