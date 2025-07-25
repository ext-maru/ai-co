#!/usr/bin/env python3
"""
Elders Guild 強化エラーハンドリング＆リトライシステム
失敗タスクの自動リトライとインテリジェントエラー処理
"""

import json
import logging
import sqlite3
import time
import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class RetryStrategy:
    """リトライ戦略定義"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """次のリトライまでの待機時間を計算"""
        delay = min(
            self.initial_delay * (self.exponential_base**attempt), self.max_delay
        )

        if self.jitter:
            # ジッターを追加して同時リトライを回避
            import random

            delay = delay * (0.5 + random.random())

        return delay


class ErrorClassifier:
    """エラー分類システム"""

    # エラータイプ定義
    ERROR_TYPES = {
        "TIMEOUT": {
            "patterns": ["timeout", "timed out", "deadline exceeded"],
            "retryable": True,
            "strategy": RetryStrategy(max_attempts=2, initial_delay=5.0),
        },
        "PERMISSION": {
            "patterns": ["permission denied", "access denied", "unauthorized", "sudo"],
            "retryable": False,
            "strategy": None,
        },
        "NETWORK": {
            "patterns": ["connection refused", "network error", "dns failure"],
            "retryable": True,
            "strategy": RetryStrategy(max_attempts=5, initial_delay=2.0),
        },
        "RATE_LIMIT": {
            "patterns": ["rate limit", "too many requests", "429"],
            "retryable": True,
            "strategy": RetryStrategy(max_attempts=3, initial_delay=30.0),
        },
        "RESOURCE": {
            "patterns": ["out of memory", "disk full", "no space left"],
            "retryable": False,
            "strategy": None,
        },
        "SYNTAX": {
            "patterns": ["syntaxerror", "invalid syntax", "parsing error"],
            "retryable": False,
            "strategy": None,
        },
        "IMPORT": {
            "patterns": ["importerror", "modulenotfounderror", "no module named"],
            "retryable": False,
            "strategy": None,
        },
        "TEMPORARY": {
            "patterns": ["temporary failure", "service unavailable", "503"],
            "retryable": True,
            "strategy": RetryStrategy(max_attempts=3, initial_delay=10.0),
        },
    }

    @classmethod
    def classify(cls, error: Exception) -> tuple[str, bool, Optional[RetryStrategy]]:
        """エラーを分類してリトライ可能性を判断"""
        error_str = str(error).lower()
        error_type_str = type(error).__name__.lower()
        for error_type, config in cls.ERROR_TYPES.items():
            for pattern in config["patterns"]:
                if pattern in error_str or pattern in error_type_str:
                    return error_type, config["retryable"], config["strategy"]

        # デフォルト: 不明なエラーは1回だけリトライ
        return "UNKNOWN", True, RetryStrategy(max_attempts=1, initial_delay=1.0)


class ErrorHistory:
    """エラー履歴管理"""

    def __init__(self, db_path: Optional[Path] = None):
        """初期化メソッド"""
        if db_path is None:
            db_path = Path.home() / ".elders_guild" / "error_history.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS error_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    function_name TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT,
                    traceback TEXT,
                    retry_count INTEGER DEFAULT 0,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_method TEXT
                )
            """
            )
            conn.commit()

    def record_error(
        self,
        function_name: str,
        error: Exception,
        error_type: str,
        retry_count: int = 0,
    ):
        """エラーを記録"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO error_history
                (timestamp, function_name, error_type, error_message, traceback, retry_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    function_name,
                    error_type,
                    str(error),
                    traceback.format_exc(),
                    retry_count,
                ),
            )
            conn.commit()

    def mark_resolved(self, function_name: str, resolution_method: str):
        """エラー解決を記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE error_history
                SET resolved = TRUE, resolution_method = ?
                WHERE function_name = ? AND resolved = FALSE
                ORDER BY timestamp DESC
                LIMIT 1
            """,
                (resolution_method, function_name),
            )
            conn.commit()

    def get_error_patterns(self, days: int = 7) -> Dict[str, int]:
        """最近のエラーパターンを取得"""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT error_type, COUNT(*) as count
                FROM error_history
                WHERE timestamp > ?
                GROUP BY error_type
                ORDER BY count DESC
            """,
                (since,),
            )

            return dict(cursor.fetchall())


def smart_retry(
    strategy: Optional[RetryStrategy] = None,
    error_history: Optional[ErrorHistory] = None,
):
    """スマートリトライデコレーター"""
    if strategy is None:
        strategy = RetryStrategy()

    if error_history is None:
        error_history = ErrorHistory()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            attempt = 0

            while attempt < strategy.max_attempts:
                try:
                    # 実行試行
                    result = func(*args, **kwargs)

                    # 成功したら履歴に記録
                    if attempt > 0:
                        error_history.mark_resolved(
                            func.__name__, f"Succeeded after {attempt} retries"
                        )

                    return result

                except Exception as e:
                    last_error = e

                    # エラー分類
                    error_type, retryable, custom_strategy = ErrorClassifier.classify(e)

                    # エラー履歴記録
                    error_history.record_error(func.__name__, e, error_type, attempt)

                    # リトライ不可能なエラーの場合は即座に再raise
                    if not retryable:
                        logger.error(
                            f"Non-retryable error in {func.__name__}: {error_type} - {e}"
                        )
                        raise

                    # カスタム戦略がある場合は使用
                    current_strategy = custom_strategy or strategy

                    attempt += 1

                    if attempt >= current_strategy.max_attempts:
                        logger.error(
                            f"Max retries ({current_strategy.max_attempts}) exceeded for " \
                                "{func.__name__}"
                        )
                        raise

                    # 待機時間計算
                    delay = current_strategy.get_delay(attempt - 1)
                    logger.warning(
                        f"Error in {func.__name__} (attempt {attempt}/{current_strategy.max_attempts}): "
                        f"{error_type} - {e}. Retrying in {delay:0.1f}s..."
                    )

                    time.sleep(delay)

            # すべてのリトライが失敗した場合
            raise last_error

        return wrapper

    return decorator


class CircuitBreaker:
    """サーキットブレーカーパターン実装"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable) -> Callable:
        """__call__特殊メソッド"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self._state == "OPEN":
                # 回復タイムアウトをチェック
                if (
                    datetime.now() - self._last_failure_time
                ).total_seconds() > self.recovery_timeout:
                    self._state = "HALF_OPEN"
                    logger.info(f"Circuit breaker for {func.__name__} is HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker is OPEN for {func.__name__}")

            try:
                result = func(*args, **kwargs)

                # 成功したらカウンターリセット
                if self._state == "HALF_OPEN":
                    self._state = "CLOSED"
                    logger.info(f"Circuit breaker for {func.__name__} is CLOSED")

                self._failure_count = 0
                return result

            except self.expected_exception as e:
                self._failure_count += 1
                self._last_failure_time = datetime.now()

                if self._failure_count >= self.failure_threshold:
                    self._state = "OPEN"
                    logger.error(
                        f"Circuit breaker for {func.__name__} is OPEN after {self._failure_count} failures"
                    )

                raise

        return wrapper


# 使用例
@smart_retry(strategy=RetryStrategy(max_attempts=3, initial_delay=1.0))
@CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
def example_function_with_retry():
    """リトライとサーキットブレーカーを持つ関数の例"""
    # 何か失敗する可能性のある処理
    pass


# タスク実行用の強化版関数
class EnhancedTaskExecutor:
    """強化版タスク実行エンジン"""

    def __init__(self):
        self.circuit_breakers = {}

    def execute_with_resilience(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """レジリエンス機能付きでタスクを実行"""
        if kwargs is None:
            kwargs = {}

        start_time = time.time()

        # サーキットブレーカーを取得または作成
        if func.__name__ not in self.circuit_breakers:
            self.circuit_breakers[func.__name__] = CircuitBreaker()

        circuit_breaker = self.circuit_breakers[func.__name__]

        try:
            # スマートリトライとサーキットブレーカーを適用
            @smart_retry(error_history=self.error_history)
            @circuit_breaker
            def wrapped_func():
                return func(*args, **kwargs)

            result = wrapped_func()

            return {
                "status": "success",
                "result": result,
                "execution_time": time.time() - start_time,
                "task_id": task_id,
            }

        except Exception as e:
            error_type, _, _ = ErrorClassifier.classify(e)

            return {
                "status": "failed",
                "error": str(e),
                "error_type": error_type,
                "execution_time": time.time() - start_time,
                "task_id": task_id,
                "traceback": traceback.format_exc(),
            }

    def get_health_report(self) -> Dict[str, Any]:
        """システムヘルスレポートを生成"""
        error_patterns = self.error_history.get_error_patterns(days=1)
        circuit_states = {name: cb._state for name, cb in self.circuit_breakers.items()}

        return {
            "timestamp": datetime.now().isoformat(),
            "error_patterns_24h": error_patterns,
            "circuit_breaker_states": circuit_states,
            "recommendations": self._generate_recommendations(error_patterns),
        }

    def _generate_recommendations(self, error_patterns: Dict[str, int]) -> List[str]:
        """エラーパターンに基づく推奨事項を生成"""
        recommendations = []

        if error_patterns.get("TIMEOUT", 0) > 10:
            recommendations.append(
                "タイムアウトエラーが多発しています。処理時間の最適化を検討してください。"
            )

        if error_patterns.get("NETWORK", 0) > 5:
            recommendations.append(
                "ネットワークエラーが発生しています。接続の安定性を確認してください。"
            )

        if error_patterns.get("RATE_LIMIT", 0) > 0:
            recommendations.append(
                "レート制限に達しています。リクエスト頻度を調整してください。"
            )

        return recommendations


# グローバルインスタンス
task_executor = EnhancedTaskExecutor()

if __name__ == "__main__":
    # テスト
    logger.info("Enhanced error handling system initialized")

    # ヘルスレポート表示
    health_report = task_executor.get_health_report()
    print(json.dumps(health_report, indent=2, ensure_ascii=False))
