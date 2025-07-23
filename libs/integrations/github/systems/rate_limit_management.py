#!/usr/bin/env python3
"""
GitHub APIレート制限管理システム
Iron Will基準準拠・ヘッダー解析・スロットリング・キューイング実装
"""

import asyncio
import json
import logging
import queue
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """レート制限情報"""

    limit: int
    remaining: int
    reset: int  # Unix timestamp
    used: int = field(init=False)

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        self.used = self.limit - self.remaining

    @property
    def reset_datetime(self) -> datetime:
        """リセット時刻をdatetimeで取得"""
        return datetime.fromtimestamp(self.reset)

    @property
    def time_until_reset(self) -> float:
        """リセットまでの秒数"""
        return max(0, self.reset - time.time())

    @property
    def is_exhausted(self) -> bool:
        """レート制限に達したか"""
        return self.remaining == 0

    @property
    def usage_percentage(self) -> float:
        """使用率（パーセント）"""
        return (self.used / self.limit * 100) if self.limit > 0 else 0


@dataclass
class APIEndpointLimit:
    """APIエンドポイント別のレート制限"""

    endpoint: str
    rate_limit: RateLimitInfo
    last_checked: datetime = field(default_factory=datetime.now)


class RateLimitManager:
    """GitHub APIレート制限管理クラス"""

    # GitHub APIのレート制限
    DEFAULT_LIMITS = {
        "core": 5000,  # 認証済みの場合
        "search": 30,  # 検索APIは別枠
        "graphql": 5000,
        "integration_manifest": 5000,
        "code_scanning_upload": 1000,
    }

    # レート制限の閾値（警告レベル）
    WARNING_THRESHOLD = 0.2  # 残り20%で警告
    CRITICAL_THRESHOLD = 0.1  # 残り10%でクリティカル

    def __init__(self, token: Optional[str] = None):
        """
        初期化

        Args:
            token: GitHub Personal Access Token
        """
        self.token = token
        self.authenticated = bool(token)

        # レート制限情報の保存
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.endpoint_limits: Dict[str, APIEndpointLimit] = {}

        # リクエストキュー
        self.request_queue = queue.PriorityQueue()
        self.processing = False

        # スロットリング設定
        self.throttle_enabled = True
        self.min_request_interval = 0.1  # 最小リクエスト間隔（秒）
        self.last_request_time = 0

        # 統計情報
        self.statistics = {
            "total_requests": 0,
            "throttled_requests": 0,
            "queued_requests": 0,
            "rate_limit_hits": 0,
            "wait_time_total": 0,
        }

        # スレッドセーフティ
        self._lock = threading.Lock()
        self._queue_processor_thread = None

        # 初期レート制限チェック
        if self.authenticated:
            self._check_initial_limits()

    def _check_initial_limits(self) -> None:
        """初期レート制限をチェック"""
        try:
            import requests

            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {self.token}",
            }

            response = requests.get(
                "https://api.github.com/rate_limit", headers=headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self._update_rate_limits_from_response(data)
                logger.info("Initial rate limits loaded successfully")
            else:
                logger.warning(
                    f"Failed to load initial rate limits: {response.status_code}"
                )

        except Exception as e:
            logger.warning(f"Could not check initial rate limits: {e}")

    def update_from_headers(
        self, headers: Dict[str, str], endpoint: str = "core"
    ) -> None:
        """
        レスポンスヘッダーからレート制限情報を更新

        Args:
            headers: HTTPレスポンスヘッダー
            endpoint: APIエンドポイントカテゴリ
        """
        with self._lock:
            # レート制限ヘッダーを解析
            limit = int(headers.get("X-RateLimit-Limit", 0))
            remaining = int(headers.get("X-RateLimit-Remaining", 0))
            reset = int(headers.get("X-RateLimit-Reset", 0))

            if limit > 0:
                rate_limit_info = RateLimitInfo(
                    limit=limit, remaining=remaining, reset=reset
                )

                self.rate_limits[endpoint] = rate_limit_info

                # エンドポイント別の情報も更新
                if endpoint not in self.endpoint_limits:
                    self.endpoint_limits[endpoint] = APIEndpointLimit(
                        endpoint=endpoint, rate_limit=rate_limit_info
                    )
                else:
                    self.endpoint_limits[endpoint].rate_limit = rate_limit_info
                    self.endpoint_limits[endpoint].last_checked = datetime.now()

                # 警告チェック
                self._check_limit_warnings(endpoint, rate_limit_info)

                # 統計更新
                self.statistics["total_requests"] += 1

    def _update_rate_limits_from_response(self, data: Dict[str, Any]) -> None:
        """レート制限APIレスポンスから情報を更新"""
        resources = data.get("resources", {})

        for category, limits in resources.items():
            rate_limit_info = RateLimitInfo(
                limit=limits.get("limit", 0),
                remaining=limits.get("remaining", 0),
                reset=limits.get("reset", 0),
            )

            self.rate_limits[category] = rate_limit_info

            # 警告チェック
            self._check_limit_warnings(category, rate_limit_info)

    def _check_limit_warnings(self, endpoint: str, limit_info: RateLimitInfo) -> None:
        """レート制限の警告をチェック"""
        if limit_info.limit == 0:
            return

        usage_ratio = limit_info.remaining / limit_info.limit

        if usage_ratio <= self.CRITICAL_THRESHOLD:
            logger.critical(
                f"CRITICAL: Rate limit for {endpoint} at {limit_info.usage_percentage:.1f}% "
                f"({limit_info.remaining}/{limit_info.limit} remaining)"
            )
        elif usage_ratio <= self.WARNING_THRESHOLD:
            logger.warning(
                f"WARNING: Rate limit for {endpoint} at {limit_info.usage_percentage:.1f}% "
                f"({limit_info.remaining}/{limit_info.limit} remaining)"
            )

    def should_throttle(self, endpoint: str = "core") -> Tuple[bool, float]:
        """
        スロットリングが必要か判定

        Args:
            endpoint: APIエンドポイントカテゴリ

        Returns:
            Tuple[bool, float]: (スロットリング必要か, 待機時間)
        """
        if not self.throttle_enabled:
            return False, 0

        with self._lock:
            # レート制限チェック
            if endpoint in self.rate_limits:
                limit_info = self.rate_limits[endpoint]

                # レート制限に達している場合
                if limit_info.is_exhausted:
                    wait_time = limit_info.time_until_reset
                    logger.warning(
                        f"Rate limit exhausted for {endpoint}. Wait {wait_time:.0f}s"
                    )
                    self.statistics["rate_limit_hits"] += 1
                    return True, wait_time

                # 残りが少ない場合は速度を落とす
                if limit_info.remaining < 100:
                    # 残り時間を残りリクエスト数で割って間隔を計算
                    interval = limit_info.time_until_reset / max(
                        limit_info.remaining, 1
                    )
                    return True, max(interval, self.min_request_interval)

            # 最小リクエスト間隔のチェック
            current_time = time.time()
            time_since_last = current_time - self.last_request_time

            if time_since_last < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last
                return True, wait_time

            return False, 0

    def wait_if_needed(self, endpoint: str = "core") -> float:
        """
        必要に応じて待機

        Args:
            endpoint: APIエンドポイントカテゴリ

        Returns:
            float: 待機した秒数
        """
        should_wait, wait_time = self.should_throttle(endpoint)

        if should_wait and wait_time > 0:
            logger.info(f"Throttling request: waiting {wait_time:.2f}s")
            time.sleep(wait_time)

            with self._lock:
                self.statistics["throttled_requests"] += 1
                self.statistics["wait_time_total"] += wait_time

            return wait_time

        # リクエスト時刻を更新
        with self._lock:
            self.last_request_time = time.time()

        return 0

    def queue_request(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 5,
        endpoint: str = "core",
    ) -> Any:
        """
        リクエストをキューに追加

        Args:
            func: 実行する関数
            args: 関数の引数
            kwargs: 関数のキーワード引数
            priority: 優先度（低い値ほど高優先度）
            endpoint: APIエンドポイントカテゴリ

        Returns:
            実行結果を待つFuture
        """
        if kwargs is None:
            kwargs = {}

        # 結果を受け取るためのFuture
        future = threading.Event()
        result_container = {"result": None, "error": None}

        # キューに追加
        request_item = {
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "endpoint": endpoint,
            "future": future,
            "result_container": result_container,
            "timestamp": time.time(),
        }

        self.request_queue.put((priority, request_item))

        with self._lock:
            self.statistics["queued_requests"] += 1

        # キュー処理スレッドを開始
        self._ensure_queue_processor()

        # 結果を待つ
        future.wait()

        if result_container["error"]:
            raise result_container["error"]

        return result_container["result"]

    def _ensure_queue_processor(self) -> None:
        """キュー処理スレッドを確保"""
        with self._lock:
            if not self.processing:
                self.processing = True
                self._queue_processor_thread = threading.Thread(
                    target=self._process_queue, daemon=True
                )
                self._queue_processor_thread.start()

    def _process_queue(self) -> None:
        """キューを処理"""
        logger.info("Queue processor started")

        try:
            while self.processing:
                try:
                    # キューからアイテムを取得（タイムアウト付き）
                    priority, request_item = self.request_queue.get(timeout=1.0)

                    # スロットリング
                    self.wait_if_needed(request_item["endpoint"])

                    # リクエスト実行
                    try:
                        result = request_item["func"](
                            *request_item["args"], **request_item["kwargs"]
                        )
                        request_item["result_container"]["result"] = result

                    except Exception as e:
                        request_item["result_container"]["error"] = e
                        logger.error(f"Error processing queued request: {e}")

                    finally:
                        # 完了を通知
                        request_item["future"].set()

                except queue.Empty:
                    # キューが空の場合は続行
                    continue

                except Exception as e:
                    logger.error(f"Queue processor error: {e}")

        finally:
            with self._lock:
                self.processing = False
            logger.info("Queue processor stopped")

    def get_limit_info(self, endpoint: str = "core") -> Optional[RateLimitInfo]:
        """
        特定エンドポイントのレート制限情報を取得

        Args:
            endpoint: APIエンドポイントカテゴリ

        Returns:
            RateLimitInfo or None
        """
        with self._lock:
            return self.rate_limits.get(endpoint)

    def get_all_limits(self) -> Dict[str, RateLimitInfo]:
        """すべてのレート制限情報を取得"""
        with self._lock:
            return self.rate_limits.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self._lock:
            stats = self.statistics.copy()

            # 現在のレート制限状態を追加
            limit_status = {}
            for endpoint, limit_info in self.rate_limits.items():
                limit_status[endpoint] = {
                    "limit": limit_info.limit,
                    "remaining": limit_info.remaining,
                    "used": limit_info.used,
                    "usage_percentage": limit_info.usage_percentage,
                    "reset_time": limit_info.reset_datetime.isoformat(),
                    "time_until_reset": limit_info.time_until_reset,
                }

            stats["current_limits"] = limit_status
            stats["queue_size"] = self.request_queue.qsize()

            return stats

    def reset_statistics(self) -> None:
        """統計情報をリセット"""
        with self._lock:
            self.statistics = {
                "total_requests": 0,
                "throttled_requests": 0,
                "queued_requests": 0,
                "rate_limit_hits": 0,
                "wait_time_total": 0,
            }

    def stop_processing(self) -> None:
        """キュー処理を停止"""
        self.processing = False
        if self._queue_processor_thread:
            self._queue_processor_thread.join(timeout=5.0)


class RateLimitDecorator:
    """レート制限デコレータ"""

    def __init__(self, manager: RateLimitManager, endpoint: str = "core"):
        """
        初期化

        Args:
            manager: RateLimitManager インスタンス
            endpoint: APIエンドポイントカテゴリ
        """
        self.manager = manager
        self.endpoint = endpoint

    def __call__(self, func: Callable) -> Callable:
        """デコレータ実装"""

        def wrapper(*args, **kwargs):
            """wrapperメソッド"""
            # スロットリング
            self.manager.wait_if_needed(self.endpoint)

            # 関数実行
            result = func(*args, **kwargs)

            # ヘッダーからレート制限情報を更新（もしあれば）
            if isinstance(result, dict) and "headers" in result:
                self.manager.update_from_headers(result["headers"], self.endpoint)

            return result

        return wrapper


def rate_limited(endpoint: str = "core"):
    """
    レート制限デコレータ（関数用）

    Args:
        endpoint: APIエンドポイントカテゴリ
    """

    def decorator(func):
        """decoratorメソッド"""
        def wrapper(*args, **kwargs):
            """wrapperメソッド"""
            # グローバルマネージャーを使用（必要に応じて設定可能）
            manager = getattr(wrapper, "_rate_limit_manager", None)
            if not manager:
                manager = RateLimitManager()
                wrapper._rate_limit_manager = manager

            # スロットリング
            manager.wait_if_needed(endpoint)

            return func(*args, **kwargs)

        return wrapper

    return decorator
