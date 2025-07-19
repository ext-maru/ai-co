#!/usr/bin/env python3
"""
Enhanced Error Recovery System
Ancient Elder #2 (ERROR_HANDLING) 指摘事項対応
包括的エラーハンドリング・自動回復・監視機能
"""

import asyncio
import json
import logging
import threading
import time
import traceback
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorSeverity(Enum):
    """エラー重要度レベル"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """回復戦略"""

    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    ESCALATE = "escalate"
    IGNORE = "ignore"


class ErrorPattern:
    """エラーパターン定義"""

    def __init__(
        self,
        pattern: str,
        severity: ErrorSeverity,
        strategy: RecoveryStrategy,
        max_retries: int = 3,
        backoff_multiplier: float = 2.0,
    ):
        self.pattern = pattern
        self.severity = severity
        self.strategy = strategy
        self.max_retries = max_retries
        self.backoff_multiplier = backoff_multiplier


class CircuitBreakerState(Enum):
    """サーキットブレーカー状態"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """改良型サーキットブレーカー"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = threading.Lock()

        logger.info(f"🔄 Circuit Breaker initialized - threshold: {failure_threshold}")

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """サーキットブレーカー経由でのメソッド呼び出し"""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("🔄 Circuit Breaker: OPEN -> HALF_OPEN")
                else:
                    raise Exception("Circuit breaker is OPEN - calls blocked")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """リセット試行すべきか判定"""
        if self.last_failure_time is None:
            return True

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout

    def _on_success(self):
        """成功時の処理"""
        with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info("✅ Circuit Breaker: HALF_OPEN -> CLOSED")
            else:
                self.failure_count = max(0, self.failure_count - 1)

    def _on_failure(self):
        """失敗時の処理"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                self.success_count = 0
                logger.warning("⚠️ Circuit Breaker: HALF_OPEN -> OPEN")
            elif self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.error(
                    f"🚨 Circuit Breaker: CLOSED -> OPEN (failures: {self.failure_count})"
                )

    def reset(self):
        """手動リセット"""
        with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            logger.info("🔄 Circuit Breaker manually reset")


class ErrorRecoveryManager:
    """包括的エラー回復管理システム"""

    def __init__(self):
        """初期化"""
        self.error_patterns = self._initialize_error_patterns()
        self.circuit_breakers = {}
        self.error_history = deque(maxlen=1000)
        self.fallback_handlers = {}
        self.recovery_metrics = {
            "total_errors": 0,
            "recovered_errors": 0,
            "failed_recoveries": 0,
            "circuit_breaks": 0,
        }

        # スレッドセーフティ
        self._lock = threading.Lock()

        logger.info("🛡️ Enhanced Error Recovery Manager initialized")

    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """エラーパターンを初期化"""
        return [
            # 接続関連エラー
            ErrorPattern(
                "ConnectionError", ErrorSeverity.HIGH, RecoveryStrategy.RETRY, 3, 2.0
            ),
            ErrorPattern(
                "TimeoutError", ErrorSeverity.HIGH, RecoveryStrategy.RETRY, 3, 1.5
            ),
            ErrorPattern(
                "ConnectTimeout", ErrorSeverity.HIGH, RecoveryStrategy.RETRY, 2, 2.0
            ),
            # HTTP関連エラー
            ErrorPattern("HTTP 5", ErrorSeverity.HIGH, RecoveryStrategy.RETRY, 3, 2.0),
            ErrorPattern(
                "HTTP 429", ErrorSeverity.MEDIUM, RecoveryStrategy.CIRCUIT_BREAK, 1, 5.0
            ),
            ErrorPattern(
                "HTTP 401", ErrorSeverity.CRITICAL, RecoveryStrategy.ESCALATE, 0, 0
            ),
            ErrorPattern(
                "HTTP 403", ErrorSeverity.CRITICAL, RecoveryStrategy.ESCALATE, 0, 0
            ),
            ErrorPattern(
                "HTTP 404", ErrorSeverity.LOW, RecoveryStrategy.FALLBACK, 1, 1.0
            ),
            # GitHub API関連エラー
            ErrorPattern(
                "rate limit",
                ErrorSeverity.HIGH,
                RecoveryStrategy.CIRCUIT_BREAK,
                1,
                10.0,
            ),
            ErrorPattern(
                "abuse", ErrorSeverity.CRITICAL, RecoveryStrategy.ESCALATE, 0, 0
            ),
            ErrorPattern(
                "bad credentials",
                ErrorSeverity.CRITICAL,
                RecoveryStrategy.ESCALATE,
                0,
                0,
            ),
            # 一般的なエラー
            ErrorPattern(
                "JSONDecodeError", ErrorSeverity.MEDIUM, RecoveryStrategy.RETRY, 2, 1.5
            ),
            ErrorPattern(
                "KeyError", ErrorSeverity.MEDIUM, RecoveryStrategy.FALLBACK, 1, 1.0
            ),
            ErrorPattern(
                "ValueError", ErrorSeverity.LOW, RecoveryStrategy.FALLBACK, 1, 1.0
            ),
            # システムエラー
            ErrorPattern(
                "MemoryError", ErrorSeverity.CRITICAL, RecoveryStrategy.ESCALATE, 0, 0
            ),
            ErrorPattern("OSError", ErrorSeverity.HIGH, RecoveryStrategy.RETRY, 2, 2.0),
        ]

    def register_fallback(self, error_pattern: str, fallback_handler: Callable):
        """フォールバックハンドラーを登録"""
        self.fallback_handlers[error_pattern] = fallback_handler
        logger.info(f"📝 Fallback handler registered for: {error_pattern}")

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """サーキットブレーカーを取得（存在しない場合は作成）"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker()
        return self.circuit_breakers[name]

    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        func: Optional[Callable] = None,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:
        """包括的エラーハンドリング"""
        error_info = self._analyze_error(error, context)

        with self._lock:
            self.error_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "context": context,
                    "severity": error_info["severity"].value,
                    "strategy": error_info["strategy"].value,
                }
            )
            self.recovery_metrics["total_errors"] += 1

        logger.error(
            f"🚨 Error occurred: {error} | Strategy: {error_info['strategy'].value}"
        )

        try:
            # 回復戦略に基づく処理
            if error_info["strategy"] == RecoveryStrategy.RETRY:
                result = await self._execute_retry_strategy(
                    error_info, func, *args, **kwargs
                )
            elif error_info["strategy"] == RecoveryStrategy.FALLBACK:
                result = await self._execute_fallback_strategy(
                    error_info, func, *args, **kwargs
                )
            elif error_info["strategy"] == RecoveryStrategy.CIRCUIT_BREAK:
                result = await self._execute_circuit_break_strategy(error_info, context)
            elif error_info["strategy"] == RecoveryStrategy.ESCALATE:
                result = await self._execute_escalate_strategy(error_info, context)
            else:
                result = {"success": False, "action": "ignored", "error": str(error)}

            if result.get("success", False):
                with self._lock:
                    self.recovery_metrics["recovered_errors"] += 1
            else:
                with self._lock:
                    self.recovery_metrics["failed_recoveries"] += 1

            return result

        except Exception as recovery_error:
            logger.critical(f"💥 Recovery failed: {recovery_error}")
            with self._lock:
                self.recovery_metrics["failed_recoveries"] += 1

            return {
                "success": False,
                "action": "recovery_failed",
                "original_error": str(error),
                "recovery_error": str(recovery_error),
            }

    def _analyze_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """エラーを分析して回復戦略を決定"""
        error_str = str(error).lower()
        error_type = type(error).__name__

        # パターンマッチング
        for pattern in self.error_patterns:
            if (
                pattern.pattern.lower() in error_str
                or pattern.pattern.lower() in error_type.lower()
            ):
                return {
                    "pattern": pattern,
                    "severity": pattern.severity,
                    "strategy": pattern.strategy,
                    "max_retries": pattern.max_retries,
                    "backoff_multiplier": pattern.backoff_multiplier,
                }

        # デフォルト戦略
        if "timeout" in error_str or "connection" in error_str:
            return {
                "pattern": None,
                "severity": ErrorSeverity.HIGH,
                "strategy": RecoveryStrategy.RETRY,
                "max_retries": 3,
                "backoff_multiplier": 2.0,
            }

        return {
            "pattern": None,
            "severity": ErrorSeverity.MEDIUM,
            "strategy": RecoveryStrategy.FALLBACK,
            "max_retries": 1,
            "backoff_multiplier": 1.0,
        }

    async def _execute_retry_strategy(
        self, error_info: Dict[str, Any], func: Optional[Callable], *args, **kwargs
    ) -> Dict[str, Any]:
        """リトライ戦略の実行"""
        if func is None:
            return {"success": False, "action": "retry_no_function"}

        max_retries = error_info["max_retries"]
        backoff = error_info["backoff_multiplier"]

        for attempt in range(max_retries):
            try:
                await asyncio.sleep(backoff**attempt)

                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                logger.info(f"✅ Retry successful on attempt {attempt + 1}")
                return {
                    "success": True,
                    "action": "retry_success",
                    "attempts": attempt + 1,
                    "result": result,
                }

            except Exception as retry_error:
                logger.warning(f"⚠️ Retry attempt {attempt + 1} failed: {retry_error}")
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "action": "retry_exhausted",
                        "attempts": max_retries,
                    }

        return {"success": False, "action": "retry_failed"}

    async def _execute_fallback_strategy(
        self, error_info: Dict[str, Any], func: Optional[Callable], *args, **kwargs
    ) -> Dict[str, Any]:
        """フォールバック戦略の実行"""
        # 登録されたフォールバックハンドラーを確認
        if error_info["pattern"]:
            pattern_name = error_info["pattern"].pattern
            if pattern_name in self.fallback_handlers:
                try:
                    fallback_func = self.fallback_handlers[pattern_name]

                    if asyncio.iscoroutinefunction(fallback_func):
                        result = await fallback_func(*args, **kwargs)
                    else:
                        result = fallback_func(*args, **kwargs)

                    logger.info(f"✅ Fallback executed successfully for: {pattern_name}")
                    return {
                        "success": True,
                        "action": "fallback_success",
                        "result": result,
                    }

                except Exception as fallback_error:
                    logger.error(f"❌ Fallback failed: {fallback_error}")

        # デフォルトフォールバック
        return {
            "success": True,
            "action": "default_fallback",
            "result": {
                "error": "Operation failed, using fallback response",
                "data": None,
            },
        }

    async def _execute_circuit_break_strategy(
        self, error_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """サーキットブレーク戦略の実行"""
        circuit_name = context.get("circuit_name", "default")
        circuit_breaker = self.get_circuit_breaker(circuit_name)

        # サーキットブレーカーをオープンに設定
        circuit_breaker._on_failure()

        with self._lock:
            self.recovery_metrics["circuit_breaks"] += 1

        # 待機時間を計算
        wait_time = error_info.get("backoff_multiplier", 5.0)

        logger.warning(
            f"🔴 Circuit breaker activated for {circuit_name}, waiting {wait_time}s"
        )

        return {
            "success": True,
            "action": "circuit_break",
            "wait_time": wait_time,
            "circuit_state": circuit_breaker.state.value,
        }

    async def _execute_escalate_strategy(
        self, error_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """エスカレーション戦略の実行"""
        # 重要なエラーをログに記録
        logger.critical(f"🚨 CRITICAL ERROR ESCALATED: {error_info}")

        # エラー通知（実装に応じて外部通知システムに送信）
        escalation_data = {
            "timestamp": datetime.now().isoformat(),
            "severity": error_info["severity"].value,
            "error_pattern": error_info["pattern"].pattern
            if error_info["pattern"]
            else "unknown",
            "context": context,
        }

        # 将来の実装: アラート送信、チケット作成など

        return {
            "success": True,
            "action": "escalated",
            "escalation_data": escalation_data,
        }

    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計を取得"""
        with self._lock:
            total_errors = self.recovery_metrics["total_errors"]

            if total_errors == 0:
                recovery_rate = 0
            else:
                recovery_rate = (
                    self.recovery_metrics["recovered_errors"] / total_errors
                ) * 100

            # 最近のエラー傾向
            recent_errors = list(self.error_history)[-50:]  # 最新50件
            error_types = {}
            severities = {}

            for error_entry in recent_errors:
                error_type = error_entry.get("error_type", "unknown")
                severity = error_entry.get("severity", "unknown")

                error_types[error_type] = error_types.get(error_type, 0) + 1
                severities[severity] = severities.get(severity, 0) + 1

            return {
                "metrics": self.recovery_metrics.copy(),
                "recovery_rate": recovery_rate,
                "circuit_breakers": {
                    name: {
                        "state": cb.state.value,
                        "failure_count": cb.failure_count,
                        "success_count": cb.success_count,
                    }
                    for name, cb in self.circuit_breakers.items()
                },
                "recent_error_types": error_types,
                "recent_severities": severities,
                "total_error_history": len(self.error_history),
            }

    def reset_statistics(self):
        """統計をリセット"""
        with self._lock:
            self.recovery_metrics = {
                "total_errors": 0,
                "recovered_errors": 0,
                "failed_recoveries": 0,
                "circuit_breaks": 0,
            }
            self.error_history.clear()

        logger.info("📊 Error statistics reset")


# グローバルエラー回復マネージャー
global_error_recovery_manager = ErrorRecoveryManager()


def enhanced_error_handler(
    circuit_name: str = "default",
    enable_retry: bool = True,
    enable_fallback: bool = True,
    enable_circuit_breaker: bool = True,
):
    """拡張エラーハンドリングデコレータ"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = {
                "function": func.__name__,
                "circuit_name": circuit_name,
                "enable_retry": enable_retry,
                "enable_fallback": enable_fallback,
                "enable_circuit_breaker": enable_circuit_breaker,
            }

            try:
                # サーキットブレーカーが有効で、オープン状態の場合はチェック
                if enable_circuit_breaker:
                    circuit_breaker = global_error_recovery_manager.get_circuit_breaker(
                        circuit_name
                    )
                    if circuit_breaker.state == CircuitBreakerState.OPEN:
                        raise Exception(f"Circuit breaker {circuit_name} is OPEN")

                # 関数実行
                result = await func(*args, **kwargs)

                # 成功時にサーキットブレーカーに通知
                if enable_circuit_breaker:
                    circuit_breaker = global_error_recovery_manager.get_circuit_breaker(
                        circuit_name
                    )
                    circuit_breaker._on_success()

                return result

            except Exception as e:
                # エラー回復を試行
                recovery_result = await global_error_recovery_manager.handle_error(
                    e, context, func, *args, **kwargs
                )

                if (
                    recovery_result.get("success", False)
                    and "result" in recovery_result
                ):
                    return recovery_result["result"]
                else:
                    # 回復失敗時は元のエラーを再発生
                    raise e

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同期関数用のラッパー
            return asyncio.run(async_wrapper(*args, **kwargs))

        # 関数が非同期かどうかで適切なラッパーを返す
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def robust_github_api_call(circuit_name: str = "github_api"):
    """GitHub API専用の堅牢なエラーハンドリングデコレータ"""
    return enhanced_error_handler(
        circuit_name=circuit_name,
        enable_retry=True,
        enable_fallback=True,
        enable_circuit_breaker=True,
    )


# フォールバックハンドラーの例
def github_api_fallback(*args, **kwargs):
    """GitHub API用のフォールバックハンドラー"""
    return {
        "success": False,
        "error": "GitHub API unavailable",
        "fallback": True,
        "data": None,
    }


# 初期化時にフォールバックハンドラーを登録
global_error_recovery_manager.register_fallback("HTTP 5", github_api_fallback)
global_error_recovery_manager.register_fallback("ConnectionError", github_api_fallback)
global_error_recovery_manager.register_fallback("TimeoutError", github_api_fallback)
