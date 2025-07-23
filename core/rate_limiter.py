#!/usr/bin/env python3
"""
レート制限とキャッシング機能
API呼び出しの制限とパフォーマンス向上のためのキャッシュ管理
"""

import asyncio
import hashlib
import json
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import aioredis
import structlog


class RateLimiter:
    """
    トークンバケット方式のレート制限実装

    Features:
    - 時間窓内の呼び出し回数制限
    - バースト対応
    - 非同期待機
    - Redis連携（分散環境対応）
    """

    def __init__(
        self,
        rate: int = 10,
        period: int = 60,
        burst: Optional[int] = None,
        redis_client: Optional[aioredis.Redis] = None,
        key_prefix: str = "rate_limit",
    ):
        """
        Args:
            rate: 期間内の最大呼び出し回数
            period: 期間（秒）
            burst: バースト時の最大呼び出し回数
            redis_client: Redis クライアント（分散環境用）
            key_prefix: Redisキーのプレフィックス
        """
        self.rate = rate
        self.period = period
        self.burst = burst or rate * 2
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self.logger = structlog.get_logger(__name__)

        # ローカルストレージ（Redis未使用時）
        self.calls = deque()

    async def check_rate_limit(self, identifier: str = "default") -> bool:
        """
        レート制限チェック

        Args:
            identifier: 制限を適用する識別子（ユーザーID、APIキーなど）

        Returns:
            制限内ならTrue、超過ならFalse
        """
        if self.redis_client:
            return await self._check_redis(identifier)
        else:
            return await self._check_local()

    async def _check_redis(self, identifier: str) -> bool:
        """Redis使用時のレート制限チェック"""
        key = f"{self.key_prefix}:{identifier}"
        now = time.time()

        # スライディングウィンドウ方式
        pipe = self.redis_client.pipeline()

        # 古いエントリを削除
        pipe.zremrangebyscore(key, 0, now - self.period)

        # 現在のカウントを取得
        pipe.zcard(key)

        # 新しいエントリを追加（仮）
        pipe.zadd(key, {str(now): now})

        # TTLを設定
        pipe.expire(key, self.period + 1)

        results = await pipe.execute()
        current_count = results[1]

        if current_count >= self.rate:
            # 制限超過の場合、仮追加を取り消す
            await self.redis_client.zrem(key, str(now))
            return False

        return True

    async def _check_local(self) -> bool:
        """ローカルストレージ使用時のレート制限チェック"""
        now = time.time()

        # 期限切れの呼び出しを削除
        while self.calls and self.calls[0] <= now - self.period:
            self.calls.popleft()

        if len(self.calls) >= self.rate:
            return False

        self.calls.append(now)
        return True

    async def wait_if_needed(self, identifier: str = "default") -> float:
        """
        必要に応じて待機

        Returns:
            待機時間（秒）
        """
        wait_time = 0
        while not await self.check_rate_limit(identifier):
            # 次の空きスロットまでの時間を計算
            if self.redis_client:
                key = f"{self.key_prefix}:{identifier}"
                oldest = await self.redis_client.zrange(key, 0, 0)
                if oldest:
                    oldest_time = float(oldest[0])
                    wait_time = max(0.1, (oldest_time + self.period) - time.time())
            else:
                if self.calls:
                    wait_time = max(0.1, (self.calls[0] + self.period) - time.time())

            self.logger.debug(
                "Rate limit reached, waiting",
                identifier=identifier,
                wait_time=wait_time,
            )

            await asyncio.sleep(min(wait_time, 1))

        return wait_time

    def get_remaining_calls(self, identifier: str = "default") -> int:
        """残り呼び出し可能回数を取得"""
        if self.redis_client:
            # Redis実装は省略（非同期のため別メソッドが必要）
            return -1
        else:
            return max(0, self.rate - len(self.calls))


class CacheManager:
    """
    高性能キャッシュ管理

    Features:
    - TTL対応
    - LRU削除
    - タグベースの無効化
    - 統計情報
    """

    def __init__(
        self,
        redis_client: Optional[aioredis.Redis] = None,
        default_ttl: int = 3600,
        max_memory_mb: int = 100,
    ):
        """
        Args:
            redis_client: Redisクライアント
            default_ttl: デフォルトTTL（秒）
            max_memory_mb: 最大メモリ使用量（MB）
        """
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.max_memory_mb = max_memory_mb
        self.logger = structlog.get_logger(__name__)

        # ローカルキャッシュ（Redis未使用時）
        self.local_cache: Dict[str, Dict[str, Any]] = {}

        # 統計情報
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    def _generate_key(self, key: str, namespace: str = None) -> str:
        """キー生成"""
        if namespace:
            return f"cache:{namespace}:{key}"
        return f"cache:{key}"

    async def get(
        self, key: str, namespace: str = None, default: Any = None
    ) -> Optional[Any]:
        """
        キャッシュから値を取得

        Args:
            key: キー
            namespace: 名前空間
            default: デフォルト値

        Returns:
            キャッシュされた値、またはdefault
        """
        full_key = self._generate_key(key, namespace)

        try:
            if self.redis_client:
                value = await self.redis_client.get(full_key)
                if value:
                    self.stats["hits"] += 1
                    return json.loads(value)
            else:
                # ローカルキャッシュ
                if full_key in self.local_cache:
                    entry = self.local_cache[full_key]
                    if entry["expires_at"] > time.time():
                        self.stats["hits"] += 1
                        return entry["value"]
                    else:
                        # 期限切れ
                        del self.local_cache[full_key]

            self.stats["misses"] += 1
            return default

        except Exception as e:
            self.logger.error("Cache get error", key=full_key, error=str(e))
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        キャッシュに値を設定

        Args:
            key: キー
            value: 値
            ttl: TTL（秒）
            namespace: 名前空間
            tags: タグ（無効化用）

        Returns:
            成功ならTrue
        """
        full_key = self._generate_key(key, namespace)
        ttl = ttl or self.default_ttl

        try:
            if self.redis_client:
                # Redis使用
                await self.redis_client.setex(full_key, ttl, json.dumps(value))

                # タグの設定
                if tags:
                    for tag in tags:
                        tag_key = f"cache:tag:{tag}"
                        await self.redis_client.sadd(tag_key, full_key)
                        await self.redis_client.expire(tag_key, ttl)
            else:
                # ローカルキャッシュ
                self.local_cache[full_key] = {
                    "value": value,
                    "expires_at": time.time() + ttl,
                    "tags": tags or [],
                }

                # メモリ制限チェック
                await self._check_memory_limit()

            self.stats["sets"] += 1
            return True

        except Exception as e:
            self.logger.error("Cache set error", key=full_key, error=str(e))
            return False

    async def delete(self, key: str, namespace: str = None) -> bool:
        """キャッシュから削除"""
        full_key = self._generate_key(key, namespace)

        try:
            if self.redis_client:
                result = await self.redis_client.delete(full_key)
                return result > 0
            else:
                if full_key in self.local_cache:
                    del self.local_cache[full_key]
                    return True
                return False

        except Exception as e:
            self.logger.error("Cache delete error", key=full_key, error=str(e))
            return False

    async def invalidate_by_tag(self, tag: str) -> int:
        """タグによる一括無効化"""
        count = 0

        try:
            if self.redis_client:
                tag_key = f"cache:tag:{tag}"
                keys = await self.redis_client.smembers(tag_key)

                if keys:
                    count = await self.redis_client.delete(*keys)
                    await self.redis_client.delete(tag_key)
            else:
                # ローカルキャッシュ
                keys_to_delete = []
                for key, entry in self.local_cache.items():
                    if tag in entry.get("tags", []):
                        keys_to_delete.append(key)

                for key in keys_to_delete:
                    del self.local_cache[key]
                    count += 1

            self.logger.info("Invalidated cache by tag", tag=tag, count=count)

        except Exception as e:
            self.logger.error("Cache invalidation error", tag=tag, error=str(e))

        return count

    async def _check_memory_limit(self):
        """メモリ制限チェック（ローカルキャッシュ用）"""
        # 簡易的なサイズ推定
        estimated_size = len(str(self.local_cache)) / (1024 * 1024)

        if estimated_size > self.max_memory_mb:
            # LRU削除
            sorted_keys = sorted(
                self.local_cache.items(), key=lambda x: x[1]["expires_at"]
            )

            # 最も古いエントリから削除
            delete_count = len(self.local_cache) // 4
            for key, _ in sorted_keys[:delete_count]:
                del self.local_cache[key]
                self.stats["evictions"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "cache_size": len(self.local_cache) if not self.redis_client else -1,
        }


class CachedFunction:
    """
    関数のキャッシュデコレータ

    使用例:
        cache = CacheManager()

        @CachedFunction(cache, ttl=300)
        async def expensive_operation(param: str) -> str:
            # 重い処理
            return result
    """

    def __init__(
        """初期化メソッド"""
        self,
        cache_manager: CacheManager,
        ttl: int = 3600,
        key_prefix: str = "func",
        namespace: str = None,
    ):
        self.cache_manager = cache_manager
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.namespace = namespace

    def __call__(self, func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # キャッシュキーの生成
            key_parts = [
                self.key_prefix,
                func.__name__,
                hashlib.md5(f"{args}{kwargs}".encode()).hexdigest()[:8],
            ]
            cache_key = ":".join(key_parts)

            # キャッシュから取得を試行
            cached = await self.cache_manager.get(cache_key, namespace=self.namespace)

            if cached is not None:
                return cached

            # 実関数を実行
            result = await func(*args, **kwargs)

            # 結果をキャッシュ
            await self.cache_manager.set(
                cache_key, result, ttl=self.ttl, namespace=self.namespace
            )

            return result

        return wrapper
