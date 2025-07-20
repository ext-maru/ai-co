#!/usr/bin/env python3
"""
System Performance Enhancer - システムパフォーマンス向上
エルダーズギルドシステム全体の高速化と最適化

主要機能:
- メモリプール管理
- 非同期処理最適化
- キャッシング戦略
- リソース管理
- パフォーマンス監視
- 自動チューニング
"""

import asyncio
import concurrent.futures
import gc
import logging
import os
import resource
import threading
import time
import weakref
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


class MemoryPool:
    """メモリプール管理"""

    def __init__(self, max_size_mb: int = 500):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.pools = defaultdict(list)
        self.allocated = 0
        self.lock = threading.Lock()
        self.stats = {"allocations": 0, "deallocations": 0, "reuses": 0}

    def allocate(self, size: int, pool_name: str = "default") -> bytearray:
        """メモリ割り当て"""
        with self.lock:
            # プールから再利用
            if self.pools[pool_name]:
                for i, (pooled_size, buffer) in enumerate(self.pools[pool_name]):
                    if pooled_size >= size:
                        self.pools[pool_name].pop(i)
                        self.stats["reuses"] += 1
                        return buffer[:size]

            # 新規割り当て
            if self.allocated + size <= self.max_size_bytes:
                buffer = bytearray(size)
                self.allocated += size
                self.stats["allocations"] += 1
                return buffer

            # メモリ不足
            raise MemoryError(
                f"Memory pool exhausted: {self.allocated}/{self.max_size_bytes}"
            )

    def deallocate(self, buffer: bytearray, pool_name: str = "default"):
        """メモリ解放"""
        with self.lock:
            size = len(buffer)
            self.pools[pool_name].append((size, buffer))
            self.stats["deallocations"] += 1

            # プールサイズ制限
            while len(self.pools[pool_name]) > 100:
                old_size, _ = self.pools[pool_name].pop(0)
                self.allocated -= old_size


class AsyncTaskPool:
    """非同期タスクプール"""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        self.active_tasks = weakref.WeakSet()
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_time": 0.0,
        }

    async def submit(self, coro: Callable, *args, **kwargs) -> Any:
        """タスク送信"""
        async with self.semaphore:
            start_time = time.time()
            self.stats["total_tasks"] += 1

            task = asyncio.create_task(coro(*args, **kwargs))
            self.active_tasks.add(task)

            try:
                result = await task
                self.stats["completed_tasks"] += 1

                # 平均時間更新
                elapsed = time.time() - start_time
                self._update_average_time(elapsed)

                return result

            except Exception as e:
                self.stats["failed_tasks"] += 1
                raise

    def _update_average_time(self, elapsed: float):
        """平均実行時間更新"""
        count = self.stats["completed_tasks"]
        current_avg = self.stats["average_time"]
        self.stats["average_time"] = (current_avg * (count - 1) + elapsed) / count

    async def map(self, coro: Callable, items: List[Any]) -> List[Any]:
        """並列マップ処理"""
        tasks = []
        for item in items:
            task = self.submit(coro, item)
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)


class SmartCache:
    """スマートキャッシュ"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.access_counts = defaultdict(int)
        self.lock = threading.RLock()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, key: str) -> Optional[Any]:
        """キャッシュ取得"""
        with self.lock:
            if key in self.cache:
                # 有効期限チェック
                if time.time() - self.access_times[key] < self.ttl_seconds:
                    self.stats["hits"] += 1
                    self.access_counts[key] += 1
                    self.access_times[key] = time.time()
                    return self.cache[key]
                else:
                    # 期限切れ
                    self._evict(key)

            self.stats["misses"] += 1
            return None

    def set(self, key: str, value: Any):
        """キャッシュ設定"""
        with self.lock:
            # サイズ制限チェック
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()

            self.cache[key] = value
            self.access_times[key] = time.time()
            self.access_counts[key] = 1

    def _evict(self, key: str):
        """キー削除"""
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
            del self.access_counts[key]
            self.stats["evictions"] += 1

    def _evict_lru(self):
        """LRU削除"""
        # アクセス頻度と時間を考慮したスコア計算
        scores = {}
        current_time = time.time()

        for key in self.cache:
            age = current_time - self.access_times[key]
            frequency = self.access_counts[key]
            # スコア = 頻度 / (年齢 + 1)
            scores[key] = frequency / (age + 1)

        # 最もスコアの低いキーを削除
        if scores:
            victim = min(scores, key=scores.get)
            self._evict(victim)


class ResourceMonitor:
    """リソース監視"""

    def __init__(self):
        self.process = psutil.Process()
        self.history = {
            "cpu": deque(maxlen=100),
            "memory": deque(maxlen=100),
            "io": deque(maxlen=100),
        }
        self.thresholds = {"cpu_percent": 80, "memory_percent": 85, "io_wait": 50}
        self.alerts = []

    def check_resources(self) -> Dict[str, Any]:
        """リソースチェック"""
        # CPU使用率
        cpu_percent = self.process.cpu_percent(interval=0.1)
        self.history["cpu"].append(cpu_percent)

        # メモリ使用率
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        self.history["memory"].append(memory_percent)

        # I/O統計
        io_counters = self.process.io_counters()
        io_bytes = io_counters.read_bytes + io_counters.write_bytes
        self.history["io"].append(io_bytes)

        # アラートチェック
        alerts = []
        if cpu_percent > self.thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {cpu_percent:.1f}%")

        if memory_percent > self.thresholds["memory_percent"]:
            alerts.append(f"High memory usage: {memory_percent:.1f}%")

        self.alerts.extend(alerts)

        return {
            "cpu_percent": cpu_percent,
            "memory_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": memory_percent,
            "io_bytes": io_bytes,
            "alerts": alerts,
        }

    def get_trends(self) -> Dict[str, Any]:
        """トレンド分析"""
        trends = {}

        for metric, history in self.history.items():
            if len(history) >= 10:
                recent = list(history)[-10:]
                older = list(history)[-20:-10] if len(history) >= 20 else recent

                recent_avg = sum(recent) / len(recent)
                older_avg = sum(older) / len(older)

                if older_avg > 0:
                    change_percent = ((recent_avg - older_avg) / older_avg) * 100
                    trends[metric] = {
                        "current": recent_avg,
                        "change_percent": change_percent,
                        "trend": "increasing"
                        if change_percent > 5
                        else "decreasing"
                        if change_percent < -5
                        else "stable",
                    }

        return trends


class PerformanceOptimizer:
    """パフォーマンス最適化"""

    def __init__(self):
        self.memory_pool = MemoryPool()
        self.task_pool = AsyncTaskPool()
        self.cache = SmartCache()
        self.monitor = ResourceMonitor()

        # 最適化設定
        self.settings = {
            "gc_threshold": 0.8,
            "cache_size": 1000,
            "max_workers": 10,
            "auto_tune": True,
        }

        # パフォーマンスメトリクス
        self.metrics = {
            "optimizations_performed": 0,
            "gc_collections": 0,
            "cache_resizes": 0,
        }

        # 自動チューニング開始
        if self.settings["auto_tune"]:
            self._start_auto_tuning()

    def _start_auto_tuning(self):
        """自動チューニング開始"""

        def tune_loop():
            while self.settings["auto_tune"]:
                try:
                    self._perform_tuning()
                    time.sleep(60)  # 1分ごと
                except Exception as e:
                    logger.error(f"Auto-tuning error: {e}")

        thread = threading.Thread(target=tune_loop, daemon=True)
        thread.start()

    def _perform_tuning(self):
        """チューニング実行"""
        resources = self.monitor.check_resources()
        trends = self.monitor.get_trends()

        # メモリ圧力が高い場合
        if resources["memory_percent"] > self.settings["gc_threshold"] * 100:
            self._optimize_memory()

        # CPUトレンドに基づくワーカー数調整
        if "cpu" in trends:
            cpu_trend = trends["cpu"]
            if cpu_trend["trend"] == "increasing" and cpu_trend["current"] > 70:
                # ワーカー数削減
                self.task_pool.max_workers = max(2, self.task_pool.max_workers - 1)
                self.task_pool.semaphore = asyncio.Semaphore(self.task_pool.max_workers)
            elif cpu_trend["trend"] == "decreasing" and cpu_trend["current"] < 30:
                # ワーカー数増加
                self.task_pool.max_workers = min(20, self.task_pool.max_workers + 1)
                self.task_pool.semaphore = asyncio.Semaphore(self.task_pool.max_workers)

        # キャッシュサイズ調整
        cache_hit_rate = self._get_cache_hit_rate()
        if cache_hit_rate < 0.5 and resources["memory_percent"] < 60:
            # キャッシュサイズ増加
            self.cache.max_size = min(5000, int(self.cache.max_size * 1.2))
            self.metrics["cache_resizes"] += 1

        self.metrics["optimizations_performed"] += 1

    def _optimize_memory(self):
        """メモリ最適化"""
        # ガベージコレクション強制実行
        gc.collect()
        self.metrics["gc_collections"] += 1

        # メモリプールクリーンアップ
        with self.memory_pool.lock:
            for pool_name, pool in self.memory_pool.pools.items():
                # 古いバッファを削除
                if len(pool) > 10:
                    removed = len(pool) - 10
                    for _ in range(removed):
                        size, _ = pool.pop(0)
                        self.memory_pool.allocated -= size

    def _get_cache_hit_rate(self) -> float:
        """キャッシュヒット率"""
        total = self.cache.stats["hits"] + self.cache.stats["misses"]
        if total == 0:
            return 0.0
        return self.cache.stats["hits"] / total

    def cached(self, ttl: int = 3600):
        """キャッシュデコレータ"""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # キャッシュキー生成
                key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

                # キャッシュチェック
                result = self.cache.get(key)
                if result is not None:
                    return result

                # 関数実行
                result = await func(*args, **kwargs)

                # キャッシュ保存
                self.cache.set(key, result)

                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # キャッシュキー生成
                key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

                # キャッシュチェック
                result = self.cache.get(key)
                if result is not None:
                    return result

                # 関数実行
                result = func(*args, **kwargs)

                # キャッシュ保存
                self.cache.set(key, result)

                return result

            # 非同期/同期判定
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    async def optimize_async_operation(
        self, operation: Callable, *args, **kwargs
    ) -> Any:
        """非同期操作最適化"""
        # タスクプール経由で実行
        return await self.task_pool.submit(operation, *args, **kwargs)

    def get_performance_report(self) -> Dict[str, Any]:
        """パフォーマンスレポート"""
        resources = self.monitor.check_resources()
        trends = self.monitor.get_trends()

        return {
            "system_resources": resources,
            "resource_trends": trends,
            "memory_pool": {
                "allocated_mb": self.memory_pool.allocated / 1024 / 1024,
                "stats": self.memory_pool.stats,
            },
            "task_pool": {
                "max_workers": self.task_pool.max_workers,
                "stats": self.task_pool.stats,
            },
            "cache": {
                "size": len(self.cache.cache),
                "max_size": self.cache.max_size,
                "hit_rate": self._get_cache_hit_rate(),
                "stats": self.cache.stats,
            },
            "optimizations": self.metrics,
            "alerts": self.monitor.alerts[-10:],  # 最新10件
        }

    def set_resource_limits(self):
        """リソース制限設定"""
        try:
            # メモリ制限（1GB）
            resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, -1))

            # ファイルディスクリプタ制限
            resource.setrlimit(resource.RLIMIT_NOFILE, (4096, 4096))

            # CPU時間制限なし
            resource.setrlimit(resource.RLIMIT_CPU, (-1, -1))

            logger.info("Resource limits set successfully")

        except Exception as e:
            logger.warning(f"Failed to set resource limits: {e}")


class SystemPerformanceEnhancer:
    """システムパフォーマンス強化統合"""

    def __init__(self):
        self.optimizer = PerformanceOptimizer()
        self.start_time = time.time()

        # パフォーマンス強化設定
        self._apply_system_optimizations()

        logger.info("SystemPerformanceEnhancer initialized")

    def _apply_system_optimizations(self):
        """システム最適化適用"""
        # ガベージコレクション調整
        gc.set_threshold(700, 10, 10)

        # プロセス優先度設定
        try:
            os.nice(-5)  # 優先度を少し上げる
        except:
            pass

        # リソース制限設定
        self.optimizer.set_resource_limits()

    def enhance_function(self, func: Callable) -> Callable:
        """関数強化"""

        # キャッシュとパフォーマンス監視を追加
        @wraps(func)
        async def async_enhanced(*args, **kwargs):
            start_time = time.time()

            try:
                # 最適化実行
                result = await self.optimizer.optimize_async_operation(
                    func, *args, **kwargs
                )

                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")

                return result

            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise

        @wraps(func)
        def sync_enhanced(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")

                return result

            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_enhanced
        else:
            return sync_enhanced

    def get_system_health(self) -> Dict[str, Any]:
        """システム健康状態"""
        uptime = time.time() - self.start_time

        return {
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "performance_report": self.optimizer.get_performance_report(),
            "gc_stats": gc.get_stats(),
            "thread_count": threading.active_count(),
        }

    async def optimize_batch_operation(
        self, operations: List[Callable], max_concurrent: int = 5
    ) -> List[Any]:
        """バッチ操作最適化"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(op):
            async with semaphore:
                if asyncio.iscoroutinefunction(op):
                    return await op()
                else:
                    return await asyncio.to_thread(op)

        tasks = [run_with_semaphore(op) for op in operations]
        return await asyncio.gather(*tasks, return_exceptions=True)


# グローバルインスタンス
_enhancer = None


def get_performance_enhancer() -> SystemPerformanceEnhancer:
    """パフォーマンスエンハンサー取得"""
    global _enhancer
    if _enhancer is None:
        _enhancer = SystemPerformanceEnhancer()
    return _enhancer


def performance_enhanced(func: Callable) -> Callable:
    """パフォーマンス強化デコレータ"""
    enhancer = get_performance_enhancer()
    return enhancer.enhance_function(func)


if __name__ == "__main__":
    # テスト実行
    async def test():
        enhancer = get_performance_enhancer()

        # キャッシュテスト
        @enhancer.optimizer.cached(ttl=60)
        async def expensive_operation(n):
            await asyncio.sleep(0.1)
            return n * n

        # 1回目（キャッシュミス）
        start = time.time()
        result1 = await expensive_operation(10)
        time1 = time.time() - start

        # 2回目（キャッシュヒット）
        start = time.time()
        result2 = await expensive_operation(10)
        time2 = time.time() - start

        print(f"First call: {time1:.3f}s, Second call: {time2:.3f}s")
        print(f"Cache speedup: {time1/time2:.1f}x")

        # システム健康状態
        health = enhancer.get_system_health()
        print(f"System health: {health}")

    asyncio.run(test())
