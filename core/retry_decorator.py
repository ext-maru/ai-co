#!/usr/bin/env python3
"""
リトライ機能デコレータとRetryableWorker基底クラス
"""

import functools
import logging
import time
from typing import Any, Callable, Optional, Union


class RetryError(Exception):
    """リトライ失敗時の例外"""

    pass


def retry(
    max_attempts: int = 3,
    backoff: Union[str, float] = "exponential",
    exceptions: tuple = (Exception,),
    delay: float = 1.0,
) -> Callable:
    """
    関数のリトライデコレータ

    Args:
        max_attempts: 最大リトライ回数
        backoff: リトライ間隔の戦略 ('exponential', 'linear', または固定値)
        exceptions: リトライ対象の例外タプル
        delay: 基本待機時間（秒）
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        """decoratorメソッド"""
        def wrapper(*args, **kwargs) -> Any:
            """wrapperメソッド"""
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # ロギング
                    logger = logging.getLogger(func.__module__)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}"
                    )

                    # 最後の試行の場合は待機しない
                    if attempt < max_attempts - 1:
                        wait_time = calculate_wait_time(attempt, backoff, delay)
                        logger.info(f"Retrying after {wait_time:0.1f} seconds...")
                        time.sleep(wait_time)

            # 全試行失敗
            raise RetryError(
                f"Failed after {max_attempts} attempts: {str(last_exception)}"
            ) from last_exception

        return wrapper

    return decorator


def calculate_wait_time(
    attempt: int, backoff: Union[str, float], base_delay: float
) -> float:
    """待機時間の計算"""
    if isinstance(backoff, (int, float)):
        return float(backoff)

    if backoff == "exponential":
        return base_delay * (2**attempt)
    elif backoff == "linear":
        return base_delay * (attempt + 1)
    else:
        return base_delay


class RetryableWorker:
    """リトライ機能を持つワーカー基底クラス"""

    def __init__(self, retry_config: Optional[dict] = None):
        """
        Args:
            retry_config: リトライ設定
                - max_attempts: 最大リトライ回数
                - backoff: リトライ戦略
                - delay: 基本待機時間
                - exceptions: リトライ対象例外
        """
        self.retry_config = retry_config or {
            "max_attempts": 3,
            "backoff": "exponential",
            "delay": 1.0,
            "exceptions": (Exception,),
        }

    def retryable_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """リトライ可能な操作の実行"""

        @retry(**self.retry_config)
        def wrapped_operation():
            return operation(*args, **kwargs)

        return wrapped_operation()

    def retry_with_config(self, **custom_config) -> Callableconfig = self.retry_config.copy()
    """カスタム設定でのリトライデコレータ"""
        config.update(custom_config)
        return retry(**config)


# よく使う設定のプリセット:
class RetryPresets:
    """リトライ設定のプリセット"""

    QUICK = {"max_attempts": 3, "backoff": "linear", "delay": 0.5}

    STANDARD = {"max_attempts": 3, "backoff": "exponential", "delay": 1.0}

    PERSISTENT = {"max_attempts": 5, "backoff": "exponential", "delay": 2.0}

    NETWORK = {
        "max_attempts": 5,
        "backoff": "exponential",
        "delay": 1.0,
        "exceptions": (ConnectionError, TimeoutError),
    }
