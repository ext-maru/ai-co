#!/usr/bin/env python3
"""
GitHub統合用包括的エラーハンドリングシステム
Iron Will基準準拠・リトライ機構・指数バックオフ・サーキットブレーカー実装
"""

import json
import logging
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorSeverity(Enum):
    """エラー重要度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CircuitState(Enum):
    """サーキットブレーカー状態"""

    CLOSED = "closed"  # 正常
    OPEN = "open"  # 障害（リクエストをブロック）
    HALF_OPEN = "half_open"  # 回復試行中


class GitHubErrorHandler:
    """GitHub APIエラーハンドリングクラス"""

    # エラータイプとリトライ可否のマッピング
    RETRYABLE_ERRORS = {
        "ConnectionError": True,
        "Timeout": True,
        "HTTPError": lambda status: status >= 500,  # 5xxエラーはリトライ
        "RateLimitError": True,
        "TemporaryError": True,
    }

    # エラーメッセージパターンと対応
    ERROR_PATTERNS = {
        "rate limit": ErrorSeverity.HIGH,
        "not found": ErrorSeverity.LOW,
        "permission denied": ErrorSeverity.MEDIUM,
        "validation failed": ErrorSeverity.LOW,
        "server error": ErrorSeverity.HIGH,
        "bad gateway": ErrorSeverity.HIGH,
        "service unavailable": ErrorSeverity.CRITICAL,
    }

    def __init__(self):
        """初期化"""
        self.error_history = deque(maxlen=1000)  # エラー履歴
        self.retry_config = {
            "max_retries": 3,
            "initial_delay": 1.0,
            "backoff_factor": 2.0,
            "max_delay": 60.0,
        }

        # サーキットブレーカー設定
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, expected_exception=Exception
        )

        # エラー統計
        self.error_stats = {
            "total_errors": 0,
            "retried_errors": 0,
            "permanent_failures": 0,
            "by_type": {},
            "by_severity": {severity.value: 0 for severity in ErrorSeverity},
        }

        self._lock = threading.Lock()

    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        エラーハンドリングのメインエントリポイント

        Args:
            error: 発生したエラー
            context: エラーコンテキスト情報

        Returns:
            Dict containing:
                - handled: エラーが処理されたか
                - should_retry: リトライすべきか
                - severity: エラー重要度
                - recovery_action: 推奨リカバリアクション
        """
        error_info = self._analyze_error(error, context)

        with self._lock:
            # エラー履歴に追加
            self.error_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "error_type": error_info["type"],
                    "message": str(error),
                    "context": context,
                    "severity": error_info["severity"],
                }
            )

            # 統計更新
            self._update_statistics(error_info)

        # リトライ判定
        should_retry = self._should_retry(error_info)

        # リカバリアクション決定
        recovery_action = self._determine_recovery_action(error_info, context)

        # ログ出力
        self._log_error(error, error_info, context)

        return {
            "handled": True,
            "should_retry": should_retry,
            "severity": error_info["severity"],
            "recovery_action": recovery_action,
            "error_info": error_info,
        }

    def _analyze_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """エラーを分析"""
        error_type = type(error).__name__
        error_message = str(error).lower()

        # 重要度判定
        severity = ErrorSeverity.MEDIUM
        for pattern, sev in self.ERROR_PATTERNS.items():
            if pattern in error_message:
                severity = sev
                break

        # HTTPステータスコードがある場合
        status_code = (
            getattr(error, "response", {}).get("status_code")
            if hasattr(error, "response")
            else None
        )
        if status_code:
            if status_code >= 500:
                severity = ErrorSeverity.HIGH
            elif status_code == 429:  # Rate limit
                severity = ErrorSeverity.HIGH
            elif status_code >= 400:
                severity = ErrorSeverity.LOW

        return {
            "type": error_type,
            "message": str(error),
            "severity": severity.value,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat(),
            "context": context,
        }

    def _should_retry(self, error_info: Dict[str, Any]) -> bool:
        """リトライすべきか判定"""
        error_type = error_info["type"]

        # 既知のリトライ可能エラー
        if error_type in self.RETRYABLE_ERRORS:
            retry_check = self.RETRYABLE_ERRORS[error_type]
            if callable(retry_check):
                return retry_check(error_info.get("status_code", 0))
            return retry_check

        # HTTPステータスコードによる判定
        status_code = error_info.get("status_code")
        if status_code:
            if status_code >= 500:  # サーバーエラー
                return True
            elif status_code == 429:  # レート制限
                return True
            elif status_code == 408:  # タイムアウト
                return True

        # エラーメッセージによる判定
        error_message = error_info["message"].lower()
        retryable_patterns = ["timeout", "connection", "temporary", "try again"]
        return any(pattern in error_message for pattern in retryable_patterns)

    def _determine_recovery_action(
        self, error_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """リカバリアクションを決定"""
        severity = error_info["severity"]
        error_type = error_info["type"]

        # レート制限エラー
        if "rate limit" in error_info["message"].lower():
            reset_time = context.get("rate_limit_reset")
            wait_time = max(0, reset_time - time.time()) if reset_time else 3600

            return {
                "action": "wait_and_retry",
                "wait_time": wait_time,
                "message": f"Rate limit hit. Wait {wait_time:.0f} seconds",
            }

        # 認証エラー
        if error_info.get("status_code") == 401:
            return {
                "action": "check_credentials",
                "message": "Authentication failed. Check GitHub token",
            }

        # 権限エラー
        if (
            error_info.get("status_code") == 403
            and "permission" in error_info["message"].lower()
        ):
            return {
                "action": "check_permissions",
                "message": "Permission denied. Ensure token has required scopes",
            }

        # サーバーエラー
        if error_info.get("status_code", 0) >= 500:
            return {
                "action": "exponential_backoff",
                "initial_delay": self.retry_config["initial_delay"],
                "message": "Server error. Retry with exponential backoff",
            }

        # デフォルト
        return {
            "action": "log_and_continue",
            "message": "Error logged. Continue with fallback behavior",
        }

    def _update_statistics(self, error_info: Dict[str, Any]) -> None:
        """エラー統計を更新"""
        self.error_stats["total_errors"] += 1

        # エラータイプ別カウント
        error_type = error_info["type"]
        if error_type not in self.error_stats["by_type"]:
            self.error_stats["by_type"][error_type] = 0
        self.error_stats["by_type"][error_type] += 1

        # 重要度別カウント
        severity = error_info["severity"]
        self.error_stats["by_severity"][severity] += 1

    def _log_error(
        self, error: Exception, error_info: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """エラーをログ出力"""
        severity = error_info["severity"]

        log_message = (
            f"GitHub API Error: {error_info['type']} - {error_info['message']}"
        )

        if context:
            log_message += f" | Context: {json.dumps(context, default=str)}"

        if severity == ErrorSeverity.CRITICAL.value:
            logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH.value:
            logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM.value:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def retry_with_backoff(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        指数バックオフでリトライ実行

        Args:
            func: 実行する関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数

        Returns:
            関数の戻り値

        Raises:
            最後の試行で発生したエラー
        """
        last_error = None
        delay = self.retry_config["initial_delay"]

        for attempt in range(self.retry_config["max_retries"]):
            try:
                # サーキットブレーカーチェック
                with self.circuit_breaker:
                    result = func(*args, **kwargs)

                    # 成功したらリセット
                    if attempt > 0:
                        logger.info(f"Retry successful after {attempt} attempts")
                        with self._lock:
                            self.error_stats["retried_errors"] += 1

                    return result

            except Exception as e:
                last_error = e

                # エラーハンドリング
                error_result = self.handle_error(
                    e,
                    {
                        "function": func.__name__,
                        "attempt": attempt + 1,
                        "args": str(args)[:100],  # 長すぎる場合は切り詰め
                        "kwargs": str(kwargs)[:100],
                    },
                )

                # リトライ不可の場合は即座に例外を再発生
                if not error_result["should_retry"]:
                    with self._lock:
                        self.error_stats["permanent_failures"] += 1
                    raise

                # 最後の試行の場合
                if attempt == self.retry_config["max_retries"] - 1:
                    with self._lock:
                        self.error_stats["permanent_failures"] += 1
                    raise

                # リカバリアクションに基づく待機
                recovery = error_result["recovery_action"]
                if recovery["action"] == "wait_and_retry":
                    wait_time = recovery["wait_time"]
                else:
                    wait_time = min(delay, self.retry_config["max_delay"])

                logger.info(
                    f"Retrying in {wait_time:.1f} seconds (attempt {attempt + 1}/{self.retry_config['max_retries']})"
                )
                time.sleep(wait_time)

                # 指数バックオフ
                delay *= self.retry_config["backoff_factor"]

        # すべてのリトライが失敗
        raise last_error

    def get_error_report(self) -> Dict[str, Any]:
        """エラーレポートを取得"""
        with self._lock:
            recent_errors = list(self.error_history)[-10:]  # 最新10件

            return {
                "statistics": self.error_stats.copy(),
                "recent_errors": recent_errors,
                "circuit_breaker_state": self.circuit_breaker.state.value,
                "report_generated": datetime.now().isoformat(),
            }

    def clear_error_history(self) -> None:
        """エラー履歴をクリア"""
        with self._lock:
            self.error_history.clear()
            self.error_stats = {
                "total_errors": 0,
                "retried_errors": 0,
                "permanent_failures": 0,
                "by_type": {},
                "by_severity": {severity.value: 0 for severity in ErrorSeverity},
            }


class CircuitBreaker:
    """サーキットブレーカー実装"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """
        初期化

        Args:
            failure_threshold: 障害とみなす失敗回数
            recovery_timeout: 回復待機時間（秒）
            expected_exception: 監視する例外タイプ
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = threading.Lock()

    def __enter__(self):
        """コンテキストマネージャー開始"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                # タイムアウトチェック
                if (
                    self.last_failure_time
                    and datetime.now() - self.last_failure_time
                    > timedelta(seconds=self.recovery_timeout)
                ):
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker: OPEN -> HALF_OPEN")
                else:
                    raise Exception("Circuit breaker is OPEN")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        with self._lock:
            if exc_type is None:
                # 成功
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info("Circuit breaker: HALF_OPEN -> CLOSED")
            else:
                # 失敗
                if isinstance(exc_val, self.expected_exception):
                    self.failure_count += 1
                    self.last_failure_time = datetime.now()

                    if self.failure_count >= self.failure_threshold:
                        self.state = CircuitState.OPEN
                        logger.error(
                            f"Circuit breaker: -> OPEN (failures: {self.failure_count})"
                        )
                    elif self.state == CircuitState.HALF_OPEN:
                        self.state = CircuitState.OPEN
                        logger.error("Circuit breaker: HALF_OPEN -> OPEN")

        return False  # 例外を再発生させる

    def reset(self):
        """手動リセット"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            logger.info("Circuit breaker manually reset")


def with_error_handling(
    max_retries: int = 3, backoff_factor: float = 2.0, handle_errors: List[type] = None
):
    """
    エラーハンドリングデコレータ

    Args:
        max_retries: 最大リトライ回数
        backoff_factor: バックオフ係数
        handle_errors: ハンドリングする例外タイプのリスト
    """
    if handle_errors is None:
        handle_errors = [Exception]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = GitHubErrorHandler()
            handler.retry_config["max_retries"] = max_retries
            handler.retry_config["backoff_factor"] = backoff_factor

            try:
                return handler.retry_with_backoff(func, *args, **kwargs)
            except tuple(handle_errors) as e:
                # ハンドリング対象のエラー
                error_result = handler.handle_error(
                    e, {"function": func.__name__, "final_attempt": True}
                )

                # エラーレポートをログ
                logger.error(
                    f"Final error report: {json.dumps(handler.get_error_report(), indent=2)}"
                )
                raise

        return wrapper

    return decorator


# グローバルエラーハンドラインスタンス
global_error_handler = GitHubErrorHandler()
