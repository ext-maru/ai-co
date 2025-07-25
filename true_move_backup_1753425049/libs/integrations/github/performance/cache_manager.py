#!/usr/bin/env python3
"""
💾 GitHub Integration Cache Manager
Iron Will Compliant - Performance Optimization
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)


class CacheManager:
    """
    💾 高性能キャッシュ管理システム
    
    Features:
    - Multi-level caching (memory + disk)
    - TTL management
    - LRU eviction policy
    - Cache warming
    - Invalidation strategies
    - Performance metrics
    """
    
    def __init__(
        self,
        memory_size: int = 1000,
        disk_cache_dir: Optional[Path] = None,
        default_ttl: int = 3600
    ):
        """
        キャッシュマネージャー初期化
        
        Args:
            memory_size: メモリキャッシュサイズ
            disk_cache_dir: ディスクキャッシュディレクトリ
            default_ttl: デフォルトTTL（秒）
        """
        # メモリキャッシュ（LRU）
        self.memory_cache = OrderedDict()
        self.memory_size = memory_size
        
        # ディスクキャッシュ
        self.disk_cache_dir = disk_cache_dir or Path.home() / ".github_cache"
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # TTL管理
        self.default_ttl = default_ttl
        self.ttl_map = {}
        
        # キャッシュ統計
        self.stats = {
            "memory_hits": 0,
            "memory_misses": 0,
            "disk_hits": 0,
            "disk_misses": 0,
            "total_requests": 0,
            "evictions": 0,
            "invalidations": 0
        }
        
        # キャッシュウォーミング
        self.warming_tasks = {}
        
        logger.info(f"CacheManager initialized: memory_size={memory_size}, disk_cache={self.disk_cache_dir}")
    
    def _generate_cache_key(self, key: Union[str, Dict[str, Any]]) -> str:
        """
        キャッシュキー生成
        
        Args:
            key: キー（文字列または辞書）
            
        Returns:
            ハッシュ化されたキー
        """
        if isinstance(key, dict):
            key_str = json.dumps(key, sort_keys=True)
        else:
            key_str = str(key)
        
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    async def get(
        self,
        key: Union[str, Dict[str, Any]],
        fetch_func: Optional[Callable] = None,
        ttl: Optional[int] = None
    ) -> Optional[Any]:
        """
        キャッシュから値を取得
        
        Args:
            key: キャッシュキー
            fetch_func: キャッシュミス時の取得関数
            ttl: TTL（秒）
            
        Returns:
            キャッシュされた値またはNone
        """
        self.stats["total_requests"] += 1
        cache_key = self._generate_cache_key(key)
        
        # メモリキャッシュチェック
        value = self._get_from_memory(cache_key)
        if value is not None:
            self.stats["memory_hits"] += 1
            logger.debug(f"Memory cache hit: {cache_key[:8]}...")
            return value
        
        self.stats["memory_misses"] += 1
        
        # ディスクキャッシュチェック
        value = await self._get_from_disk(cache_key)
        if value is not None:
            self.stats["disk_hits"] += 1
            logger.debug(f"Disk cache hit: {cache_key[:8]}...")
            # メモリキャッシュに昇格
            self._set_to_memory(cache_key, value, ttl or self.default_ttl)
            return value
        
        self.stats["disk_misses"] += 1
        
        # キャッシュミス - 取得関数実行
        if fetch_func:
            logger.debug(f"Cache miss, fetching: {cache_key[:8]}...")
            try:
                value = await fetch_func() if asyncio.iscoroutinefunction(fetch_func) else fetch_func()
                await self.set(key, value, ttl)
                return value
            except Exception as e:
                logger.error(f"Fetch function failed: {str(e)}")
                return None
        
        return None
    
    async def set(
        self,
        key: Union[str, Dict[str, Any]],
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        キャッシュに値を設定
        
        Args:
            key: キャッシュキー
            value: 保存する値
            ttl: TTL（秒）
        """
        cache_key = self._generate_cache_key(key)
        ttl = ttl or self.default_ttl
        
        # メモリキャッシュに設定
        self._set_to_memory(cache_key, value, ttl)
        
        # ディスクキャッシュに非同期で設定
        asyncio.create_task(self._set_to_disk(cache_key, value, ttl))
        
        logger.debug(f"Cache set: {cache_key[:8]}... (ttl={ttl}s)")
    
    def _get_from_memory(self, cache_key: str) -> Optional[Any]:
        """
        メモリキャッシュから取得
        
        Args:
            cache_key: キャッシュキー
            
        Returns:
            キャッシュされた値またはNone
        """
        if cache_key in self.memory_cache:
            # TTLチェック
            if cache_key in self.ttl_map:
                if time.time() > self.ttl_map[cache_key]:
                    # TTL期限切れ
                    self._remove_from_memory(cache_key)
                    return None
            
            # LRU更新（最後に移動）
            self.memory_cache.move_to_end(cache_key)
            return self.memory_cache[cache_key]
        
        return None
    
    def _set_to_memory(self, cache_key: str, value: Any, ttl: int):
        """
        メモリキャッシュに設定
        
        Args:
            cache_key: キャッシュキー
            value: 値
            ttl: TTL（秒）
        """
        # サイズチェック
        if len(self.memory_cache) >= self.memory_size:
            # 最も古いエントリを削除（LRU）
            oldest_key = next(iter(self.memory_cache))
            self._remove_from_memory(oldest_key)
            self.stats["evictions"] += 1
        
        # キャッシュに追加
        self.memory_cache[cache_key] = value
        self.ttl_map[cache_key] = time.time() + ttl
    
    def _remove_from_memory(self, cache_key: str):
        """メモリキャッシュから削除"""
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        if cache_key in self.ttl_map:
            del self.ttl_map[cache_key]
    
    async def _get_from_disk(self, cache_key: str) -> Optional[Any]:
        """
        ディスクキャッシュから取得
        
        Args:
            cache_key: キャッシュキー
            
        Returns:
            キャッシュされた値またはNone
        """
        cache_file = self.disk_cache_dir / f"{cache_key}.cache"
        
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                
                # TTLチェック
                if time.time() > data["expires_at"]:
                    # TTL期限切れ
                    cache_file.unlink()
                    return None
                
                return data["value"]
                
            except Exception as e:
                logger.error(f"Disk cache read error: {str(e)}")
                # 破損したキャッシュファイルを削除
                cache_file.unlink(missing_ok=True)
        
        return None
    
    async def _set_to_disk(self, cache_key: str, value: Any, ttl: int):
        """
        ディスクキャッシュに設定
        
        Args:
            cache_key: キャッシュキー
            value: 値
            ttl: TTL（秒）
        """
        cache_file = self.disk_cache_dir / f"{cache_key}.cache"
        
        try:
            data = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time()
            }
            
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
                
        except Exception as e:
            logger.error(f"Disk cache write error: {str(e)}")
    
    async def invalidate(self, key: Union[str, Dict[str, Any]]):
        """
        キャッシュを無効化
        
        Args:
            key: キャッシュキー
        """
        cache_key = self._generate_cache_key(key)
        
        # メモリキャッシュから削除
        self._remove_from_memory(cache_key)
        
        # ディスクキャッシュから削除
        cache_file = self.disk_cache_dir / f"{cache_key}.cache"
        cache_file.unlink(missing_ok=True)
        
        self.stats["invalidations"] += 1
        logger.debug(f"Cache invalidated: {cache_key[:8]}...")
    
    async def invalidate_pattern(self, pattern: str):
        """
        パターンマッチでキャッシュを無効化
        
        Args:
            pattern: パターン（例: "user:*"）
        """
        # メモリキャッシュ
        keys_to_remove = []
        for key in self.memory_cache:
            if self._match_pattern(key, pattern):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_from_memory(key)
        
        # ディスクキャッシュ
        for cache_file in self.disk_cache_dir.glob("*.cache"):
            if self._match_pattern(cache_file.stem, pattern):
                cache_file.unlink()
        
        invalidated_count = len(keys_to_remove)
        self.stats["invalidations"] += invalidated_count
        logger.info(f"Invalidated {invalidated_count} cache entries matching pattern: {pattern}")
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """パターンマッチング（簡易実装）"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    async def warm_cache(
        self,
        key: Union[str, Dict[str, Any]],
        fetch_func: Callable,
        ttl: Optional[int] = None,
        interval: Optional[int] = None
    ):
        """
        キャッシュウォーミング（定期的に更新）
        
        Args:
            key: キャッシュキー
            fetch_func: 取得関数
            ttl: TTL（秒）
            interval: 更新間隔（秒）
        """
        cache_key = self._generate_cache_key(key)
        
        async def warming_task():
            """warming_taskメソッド"""
            while True:
                try:
                    value = await fetch_func() if asyncio.iscoroutinefunction(fetch_func) else fetch_func()
                    await self.set(key, value, ttl)
                    logger.debug(f"Cache warmed: {cache_key[:8]}...")
                except Exception as e:
                    logger.error(f"Cache warming failed: {str(e)}")
                
                await asyncio.sleep(interval or (ttl or self.default_ttl) * 0.8)
        
        # 既存のタスクをキャンセル
        if cache_key in self.warming_tasks:
            self.warming_tasks[cache_key].cancel()
        
        # 新しいタスクを開始
        self.warming_tasks[cache_key] = asyncio.create_task(warming_task())
        logger.info(f"Cache warming started: {cache_key[:8]}...")
    
    def stop_warming(self, key: Union[str, Dict[str, Any]]):
        """キャッシュウォーミング停止"""
        cache_key = self._generate_cache_key(key)
        
        if cache_key in self.warming_tasks:
            self.warming_tasks[cache_key].cancel()
            del self.warming_tasks[cache_key]
            logger.info(f"Cache warming stopped: {cache_key[:8]}...")
    
    async def clear_all(self):
        """すべてのキャッシュをクリア"""
        # メモリキャッシュクリア
        self.memory_cache.clear()
        self.ttl_map.clear()
        
        # ディスクキャッシュクリア
        for cache_file in self.disk_cache_dir.glob("*.cache"):
            cache_file.unlink()
        
        # ウォーミングタスク停止
        for task in self.warming_tasks.values():
            task.cancel()
        self.warming_tasks.clear()
        
        logger.info("All cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計取得
        
        Returns:
            統計情報辞書
        """
        total_hits = self.stats["memory_hits"] + self.stats["disk_hits"]
        total_misses = self.stats["memory_misses"] + self.stats["disk_misses"]
        
        hit_rate = (total_hits / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": f"{hit_rate:0.2f}%",
            "memory_usage": f"{len(self.memory_cache)}/{self.memory_size}",
            "disk_files": len(list(self.disk_cache_dir.glob("*.cache"))),
            "warming_tasks": len(self.warming_tasks)
        }


# デコレーター for easy caching
def cached(ttl: int = 3600, key_func: Optional[Callable] = None):
    """
    キャッシュデコレーター
    
    Args:
        ttl: TTL（秒）
        key_func: カスタムキー生成関数
    """
    def decorator(func):
        """decoratorメソッド"""
        cache_manager = CacheManager()
        
        async def async_wrapper(*args, **kwargs):
            """async_wrapperメソッド"""
            # キー生成
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # キャッシュから取得または実行
            return await cache_manager.get(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl
            )
        
        def sync_wrapper(*args, **kwargs):
            """sync_wrapperメソッド"""
            # 同期関数用（簡易実装）
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            result = cache_manager._get_from_memory(cache_manager._generate_cache_key(cache_key))
            if result is None:
                result = func(*args, **kwargs)
                cache_manager._set_to_memory(
                    cache_manager._generate_cache_key(cache_key),
                    result,
                    ttl
                )
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# 使用例
async def example_usage():
    """使用例"""
    cache = CacheManager(memory_size=100)
    
    # 基本的な使用
    async def fetch_user_data(user_id: int):
        """fetch_user_dataメソッド"""
        # 実際のAPI呼び出しをシミュレート
        await asyncio.sleep(1)
        return {"id": user_id, "name": f"User {user_id}"}
    
    # キャッシュ経由で取得
    user_data = await cache.get(
        {"type": "user", "id": 123},
        lambda: fetch_user_data(123),
        ttl=300
    )
    print(f"User data: {user_data}")
    
    # 統計表示
    print(f"Cache stats: {cache.get_stats()}")
    
    # キャッシュウォーミング
    await cache.warm_cache(
        {"type": "popular_repos"},
        lambda: ["repo1", "repo2", "repo3"],
        ttl=600,
        interval=300
    )
    
    # クリーンアップ
    await cache.clear_all()


if __name__ == "__main__":
    asyncio.run(example_usage())