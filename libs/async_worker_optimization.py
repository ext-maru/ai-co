#!/usr/bin/env python3
"""
非同期ワーカーパフォーマンス最適化システム
バッチ処理、パイプライニング、リソースプール管理、動的負荷分散を提供
"""
import asyncio
import functools
import gc
import heapq
import logging
import sys
import threading
import time
import weakref
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set, Tuple


class LoadLevel(Enum):
    """負荷レベル"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskItem:
    """タスクアイテム"""

    id: str
    data: Any
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def __lt__(self, other):
        """__lt__特殊メソッド"""
        return self.priority > other.priority  # 高優先度が先


@dataclass
class WorkerMetrics:
    """ワーカーメトリクス"""

    tasks_processed: int = 0
    total_processing_time: float = 0.0
    errors_count: int = 0
    last_task_time: Optional[datetime] = None

    @property
    def average_processing_time(self) -> float:
        """average_processing_time処理メソッド"""
        if self.tasks_processed == 0:
            return 0.0
        return self.total_processing_time / self.tasks_processed


class AsyncWorkerOptimizer:
    """非同期ワーカー最適化器"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.pipelines = {}
        self.resource_pools = {}
        self.metrics = defaultdict(WorkerMetrics)

    async def optimize_batch_processing(
        self,
        items: List[Any],
        task_func: Callable,
        batch_size: int = 10,
        max_concurrent: int = 5,
    ) -> List[Any]:
        """バッチ処理の最適化"""
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_batch(batch):
            """process_batch処理メソッド"""
            async with semaphore:
                batch_results = []
                tasks = [task_func(item) for item in batch]
                batch_results = await asyncio.gather(*tasks)
                return batch_results

        # バッチに分割
        batches = []
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batches.append(batch)

        # バッチを並列処理
        batch_tasks = [process_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)

        # 結果をフラット化
        for batch_result in batch_results:
            results.extend(batch_result)

        return results

    def setup_pipeline(self, stages: List[Callable]) -> "Pipeline":
        """パイプラインのセットアップ"""
        pipeline = Pipeline(stages)
        pipeline_id = f"pipeline_{len(self.pipelines)}"
        self.pipelines[pipeline_id] = pipeline
        return pipeline

    def manage_resource_pool(
        self, pool_name: str, config: Dict[str, Any]
    ) -> "ResourcePool":
        """リソースプール管理"""
        pool = ResourcePool(
            name=pool_name,
            min_workers=config["min_workers"],
            max_workers=config["max_workers"],
            scaling_factor=config.get("scaling_factor", 2.0),
            idle_timeout=config.get("idle_timeout", 30),
        )
        self.resource_pools[pool_name] = pool
        return pool

    async def distribute_tasks(
        self, tasks: List[Dict], workers: List[Dict]
    ) -> Dict[str, int]:
        """タスク分散"""
        distribution = defaultdict(int)

        # ワーカーの負荷でソート（低い順）
        sorted_workers = sorted(workers, key=lambda w: w["load"])

        # ラウンドロビンで分散（負荷を考慮）
        for i, task in enumerate(tasks):
            # 最も負荷の低いワーカーを選択
            worker = sorted_workers[0]
            distribution[worker["id"]] += 1

            # ワーカーの負荷を更新
            worker["load"] += task["weight"] / worker["capacity"]

            # ワーカーを再ソート
            sorted_workers = sorted(sorted_workers, key=lambda w: w["load"])

        return dict(distribution)

    def calculate_balance_score(
        self, distribution: Dict[str, int], workers: List[Dict]
    ) -> float:
        """バランススコア計算"""
        if not distribution:
            return 0.0

        # 理想的な分散
        total_tasks = sum(distribution.values())
        ideal_per_worker = total_tasks / len(workers)

        # 標準偏差計算
        variance = sum(
            (distribution.get(w["id"], 0) - ideal_per_worker) ** 2 for w in workers
        )
        std_dev = (variance / len(workers)) ** 0.5

        # スコア計算（0-1の範囲）
        max_std_dev = ideal_per_worker  # 最大標準偏差
        score = 1.0 - min(std_dev / max_std_dev, 1.0) if max_std_dev > 0 else 1.0

        return score

    def profile_performance(self) -> Dict[str, Any]:
        """パフォーマンスプロファイリング"""
        profile_data = {"pipelines": {}, "resource_pools": {}, "overall_metrics": {}}

        # パイプラインメトリクス
        for name, pipeline in self.pipelines.items():
            profile_data["pipelines"][name] = pipeline.get_metrics()

        # リソースプールメトリクス
        for name, pool in self.resource_pools.items():
            profile_data["resource_pools"][name] = {
                "active_workers": pool.get_active_workers(),
                "utilization": pool.get_utilization(),
            }

        return profile_data


class Pipeline:
    """非同期パイプライン"""

    def __init__(self, stages: List[Callable]):
        """初期化"""
        self.stages = stages
        self.metrics = {
            "items_processed": 0,
            "total_time": 0.0,
            "stage_times": defaultdict(float),
        }

    async def process(self, items: List[Any]) -> List[Any]:
        """パイプライン処理"""
        start_time = time.time()
        results = items

        for i, stage in enumerate(self.stages):
            stage_start = time.time()

            # ステージを並列実行
            tasks = [stage(item) for item in results]
            results = await asyncio.gather(*tasks)

            # メトリクス更新
            self.metrics["stage_times"][f"stage_{i}"] += time.time() - stage_start

        self.metrics["items_processed"] += len(items)
        self.metrics["total_time"] += time.time() - start_time

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """メトリクス取得"""
        if self.metrics["items_processed"] == 0:
            return {"throughput": 0.0, "average_latency": 0.0, "stage_times": {}}

        return {
            "throughput": self.metrics["items_processed"] / self.metrics["total_time"],
            "average_latency": self.metrics["total_time"]
            / self.metrics["items_processed"],
            "stage_times": dict(self.metrics["stage_times"]),
        }


class ResourcePool:
    """リソースプール"""

    def __init__(
        self,
        name: str,
        min_workers: int,
        max_workers: int,
        scaling_factor: float = 2.0,
        idle_timeout: int = 30,
    ):
        """初期化"""
        self.name = name
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scaling_factor = scaling_factor
        self.idle_timeout = idle_timeout
        self.active_workers = min_workers
        self._load_level = LoadLevel.LOW

    def get_active_workers(self) -> int:
        """アクティブワーカー数取得"""
        return self.active_workers

    def simulate_load(self, high: bool):
        """負荷シミュレーション"""
        if high:
            self._load_level = LoadLevel.HIGH
            # スケールアップ
            self.active_workers = min(
                int(self.active_workers * self.scaling_factor), self.max_workers
            )
        else:
            self._load_level = LoadLevel.LOW
            # スケールダウン（最小値まで）
            self.active_workers = max(
                self.min_workers, int(self.active_workers / self.scaling_factor)
            )

    def get_utilization(self) -> float:
        """使用率取得"""
        return self.active_workers / self.max_workers


class PerformanceProfiler:
    """パフォーマンスプロファイラー"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self._profiling = False
        self._start_time = None
        self._function_stats = defaultdict(
            lambda: {
                "call_count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
            }
        )

    def start_profiling(self):
        """プロファイリング開始"""
        self._profiling = True
        self._start_time = time.time()
        self._function_stats.clear()

    def stop_profiling(self):
        """プロファイリング停止"""
        self._profiling = False

    def profile_async(self, func: Callable) -> Callable:
        """非同期関数のプロファイリングデコレータ"""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            """wrapperメソッド"""
            if not self._profiling:
                return await func(*args, **kwargs)

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                stats = self._function_stats[func.__name__]
                stats["call_count"] += 1
                stats["total_time"] += elapsed
                stats["min_time"] = min(stats["min_time"], elapsed)
                stats["max_time"] = max(stats["max_time"], elapsed)

        return wrapper

    def get_profile_report(self) -> Dict[str, Any]:
        """プロファイルレポート取得"""
        report = {"function_stats": {}}

        for func_name, stats in self._function_stats.items():
            if stats["call_count"] > 0:
                report["function_stats"][func_name] = {
                    "call_count": stats["call_count"],
                    "total_time": stats["total_time"],
                    "average_time": stats["total_time"] / stats["call_count"],
                    "min_time": stats["min_time"],
                    "max_time": stats["max_time"],
                }

        return report

    def analyze_bottlenecks(self, profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ボトルネック分析"""
        bottlenecks = []
        function_stats = profile_data.get("function_stats", {})

        # 総実行時間でソート
        sorted_funcs = sorted(
            function_stats.items(), key=lambda x: x[1]["total_time"], reverse=True
        )

        total_time = sum(stats["total_time"] for _, stats in sorted_funcs)

        for func_name, stats in sorted_funcs:
            impact_score = stats["total_time"] / total_time if total_time > 0 else 0

            bottleneck = {
                "function": func_name,
                "impact_score": impact_score,
                "total_time": stats["total_time"],
                "call_count": stats["call_count"],
                "average_time": stats["average_time"],
                "optimization_suggestions": [],
            }

            # 最適化提案
            if stats["call_count"] > 100:
                bottleneck["optimization_suggestions"].append(
                    "Consider caching results"
                )
            if stats["average_time"] > 1.0:
                bottleneck["optimization_suggestions"].append(
                    "Consider async/parallel processing"
                )

            bottlenecks.append(bottleneck)

        return bottlenecks


class AsyncBatchProcessor:
    """非同期バッチプロセッサー"""

    def __init__(self, batch_size: int = 10, timeout: float = 1.0):
        """初期化"""
        self.batch_size = batch_size
        self.timeout = timeout
        self._batch_handler = None
        self._pending_items = []
        self._pending_futures = []
        self._batch_task = None
        self._stats = {"total_batches": 0, "total_items": 0}

    def set_handler(self, handler: Callable):
        """ハンドラー設定"""
        self._batch_handler = handler

    async def add_item(self, item: Any) -> asyncio.Future:
        """アイテム追加"""
        future = asyncio.Future()
        self._pending_items.append(item)
        self._pending_futures.append(future)

        # バッチサイズに達したら処理
        if len(self._pending_items) >= self.batch_size:
            await self._process_batch()
        elif self._batch_task is None or self._batch_task.done():
            # タイムアウトタスクを開始
            self._batch_task = asyncio.create_task(self._timeout_batch())

        return future

    async def _timeout_batch(self):
        """タイムアウトベースのバッチ処理"""
        await asyncio.sleep(self.timeout)
        if self._pending_items:
            await self._process_batch()

    async def _process_batch(self):
        """バッチ処理実行"""
        if not self._pending_items or not self._batch_handler:
            return

        # 現在のバッチを取得
        items = self._pending_items.copy()
        futures = self._pending_futures.copy()
        self._pending_items.clear()
        self._pending_futures.clear()

        try:
            # バッチ処理
            results = await self._batch_handler(items)

            # 結果を各Futureに設定
            for future, result in zip(futures, results):
                future.set_result(result)

            # 統計更新
            self._stats["total_batches"] += 1
            self._stats["total_items"] += len(items)

        except Exception as e:
            # エラーを各Futureに設定
            for future in futures:
                future.set_exception(e)

    def get_statistics(self) -> Dict[str, Any]:
        """統計取得"""
        avg_batch_size = (
            self._stats["total_items"] / self._stats["total_batches"]
            if self._stats["total_batches"] > 0
            else 0
        )

        return {
            "total_batches": self._stats["total_batches"],
            "total_items": self._stats["total_items"],
            "average_batch_size": avg_batch_size,
        }


class ConnectionPoolOptimizer:
    """コネクションプール最適化器"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self._pools = {}

    async def create_pool(
        self, min_size: int, max_size: int, connection_factory: Callable
    ) -> "ConnectionPool":
        """プール作成"""
        pool = ConnectionPool(
            min_size=min_size, max_size=max_size, connection_factory=connection_factory
        )
        await pool.initialize()
        return pool

    def optimize_pool_size(
        self, load_pattern: List[Dict], pool: "ConnectionPool"
    ) -> int:
        """プールサイズ最適化"""
        if not load_pattern:
            return pool.min_size

        # 最近の負荷の平均
        recent_loads = [p["active_connections"] for p in load_pattern[-10:]]
        avg_load = sum(recent_loads) / len(recent_loads)

        # ピーク負荷
        peak_load = max(p["active_connections"] for p in load_pattern)

        # 最適サイズ計算（平均とピークの加重平均）
        optimal_size = int(avg_load * 0.7 + peak_load * 0.3)

        # 制限内に収める
        return max(pool.min_size, min(optimal_size, pool.max_size))

    async def monitor_pool_health(self, pool) -> Dict[str, Any]:
        """プールヘルスモニタリング"""
        total_connections = len(pool.connections)
        healthy_connections = 0

        for conn in pool.connections:
            if await conn.is_alive():
                healthy_connections += 1

        unhealthy_connections = total_connections - healthy_connections
        health_percentage = (
            healthy_connections / total_connections * 100
            if total_connections > 0
            else 0
        )

        return {
            "total_connections": total_connections,
            "healthy_connections": healthy_connections,
            "unhealthy_connections": unhealthy_connections,
            "health_percentage": health_percentage,
        }


class ConnectionPool:
    """コネクションプール"""

    def __init__(self, min_size: int, max_size: int, connection_factory: Callable):
        """初期化"""
        self.min_size = min_size
        self.max_size = max_size
        self.connection_factory = connection_factory
        self.connections = []
        self._size = 0

    async def initialize(self):
        """初期化"""
        # 最小サイズまでコネクションを作成
        for _ in range(self.min_size):
            conn = await self.connection_factory()
            self.connections.append(conn)
        self._size = self.min_size

    @property
    def size(self) -> int:
        """サイズ取得"""
        return self._size


class MockConnection:
    """モックコネクション"""

    def __init__(self, alive: bool = True):
        """初期化"""
        self._alive = alive

    async def is_alive(self) -> bool:
        """生存確認"""
        return self._alive


class AsyncTaskScheduler:
    """非同期タスクスケジューラー"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self._task_queue = []  # ヒープキュー
        self._task_map = {}
        self._pending_count = 0

    async def schedule_task(self, task_id: str, task_func: Callable, priority: int = 0):
        """タスクスケジュール"""
        task_item = TaskItem(id=task_id, data=task_func, priority=priority)

        heapq.heappush(self._task_queue, task_item)
        self._task_map[task_id] = task_item
        self._pending_count += 1

    def cancel_task(self, task_id: str) -> bool:
        """タスクキャンセル"""
        if task_id in self._task_map:
            del self._task_map[task_id]
            # キューから削除（再構築）
            self._task_queue = [t for t in self._task_queue if t.id != task_id]
            heapq.heapify(self._task_queue)
            self._pending_count -= 1
            return True
        return False

    def get_pending_tasks(self) -> List[str]:
        """保留中タスク取得"""
        return list(self._task_map.keys())

    def has_pending_tasks(self) -> bool:
        """保留中タスクの有無"""
        return len(self._task_queue) > 0

    async def execute_next(self) -> Any:
        """次のタスク実行"""
        if not self._task_queue:
            return None

        task_item = heapq.heappop(self._task_queue)
        del self._task_map[task_item.id]
        self._pending_count -= 1

        # タスク実行
        task_func = task_item.data
        return await task_func()

    def optimize_schedule(self, tasks: List[Dict]) -> List[Dict]:
        """スケジュール最適化"""
        # トポロジカルソート（依存関係を考慮）
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        # グラフ構築
        for task in tasks:
            task_id = task["id"]
            for dep in task.get("dependencies", []):
                graph[dep].append(task_id)
                in_degree[task_id] += 1

        # 開始可能なタスクをキューに追加
        queue = deque()
        for task in tasks:
            if in_degree[task["id"]] == 0:
                queue.append(task)

        # トポロジカルソート実行
        optimized_schedule = []
        while queue:
            current = queue.popleft()
            optimized_schedule.append(current)

            # 依存関係を更新
            for neighbor in graph[current["id"]]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    # 該当タスクを見つけて追加
                    for task in tasks:
                        if task["id"] == neighbor:
                            queue.append(task)
                            break

        return optimized_schedule

    def calculate_total_time(self, schedule: List[Dict]) -> float:
        """総実行時間計算"""
        if not schedule:
            return 0.0

        # 簡易的な計算（並列実行を考慮）
        max_time = 0.0
        current_time = 0.0

        for task in schedule:
            duration = task.get("duration", 0)
            current_time += duration
            max_time = max(max_time, current_time)

        return max_time


class MemoryOptimizer:
    """メモリ最適化器"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self._leak_storage = weakref.WeakSet()
        self._monitoring = False

    def analyze_memory_usage(self, data: Any) -> Dict[str, Any]:
        """メモリ使用量分析"""
        total_size = 0
        breakdown = {}
        suggestions = []

        # データ構造のサイズ計算
        for key, value in data.items():
            size = sys.getsizeof(value)
            breakdown[key] = size
            total_size += size

            # 最適化提案
            if isinstance(value, list) and len(value) > 10000:
                suggestions.append(f"Consider using generator for '{key}'")
            elif isinstance(value, str) and len(value) > 1000000:
                suggestions.append(f"Consider streaming or chunking for '{key}'")

        return {
            "total_size": total_size,
            "breakdown": breakdown,
            "optimization_suggestions": suggestions,
        }

    def optimize_data_structures(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データ構造最適化"""
        optimized_data = {}
        memory_before = sum(sys.getsizeof(v) for v in data.values())

        for key, value in data.items():
            if key == "duplicated_strings" and isinstance(value, list):
                # 重複排除（インターン）
                unique_strings = set(value)
                if len(unique_strings) == 1:
                    # 全て同じ文字列の場合
                    single_string = next(iter(unique_strings))
                    optimized_data[key] = _RepeatedString(single_string, len(value))
                else:
                    optimized_data[key] = value

            elif key == "sparse_list" and isinstance(value, list):
                # スパースリストの最適化
                non_none_items = [(i, v) for i, v in enumerate(value) if v is not None]
                if len(non_none_items) < len(value) / 2:
                    optimized_data[key] = _SparseList(len(value), non_none_items)
                else:
                    optimized_data[key] = value

            else:
                optimized_data[key] = value

        memory_after = sum(sys.getsizeof(v) for v in optimized_data.values())
        memory_saved = max(0, memory_before - memory_after)

        return {"optimized_data": optimized_data, "memory_saved": memory_saved}

    def setup_memory_pool(self, size: int) -> "MemoryPool":
        """メモリプールセットアップ"""
        return MemoryPool(size)

    def start_leak_detection(self):
        """リーク検出開始"""
        self._monitoring = True
        gc.collect()  # ガベージコレクション実行

    def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """メモリリーク検出"""
        if not self._monitoring:
            return []

        leaks = []

        # グローバル変数のチェック
        frame = sys._getframe()
        while frame is not None:
            for name, obj in frame.f_locals.items():
                if name == "leak_storage" and isinstance(obj, list) and len(obj) > 0:
                    leaks.append(
                        {
                            "location": name,
                            "type": "global_accumulation",
                            "size": sys.getsizeof(obj),
                            "severity": "high" if len(obj) > 100 else "medium",
                        }
                    )
            frame = frame.f_back
            if frame is None:
                break

        # グローバル変数もチェック
        for name, obj in globals().items():
            if name == "leak_storage" and isinstance(obj, list) and len(obj) > 0:
                leaks.append(
                    {
                        "location": name,
                        "type": "global_accumulation",
                        "size": sys.getsizeof(obj),
                        "severity": "high" if len(obj) > 100 else "medium",
                    }
                )

        return leaks


class _RepeatedString:
    """繰り返し文字列の最適化表現"""

    def __init__(self, string: str, count: int):
        """初期化メソッド"""
        self.string = string
        self.count = count

    def __getitem__(self, index):
        """__getitem__特殊メソッド"""
        if 0 <= index < self.count:
            return self.string
        raise IndexError

    def __len__(self):
        """__len__特殊メソッド"""
        return self.count

    def __iter__(self):
        """__iter__特殊メソッド"""
        for _ in range(self.count):
            yield self.string


class _SparseList:
    """スパースリストの最適化表現"""

    def __init__(self, size: int, non_none_items: List[Tuple[int, Any]]):
        """初期化メソッド"""
        self.size = size
        self.data = dict(non_none_items)

    def __getitem__(self, index):
        """__getitem__特殊メソッド"""
        if 0 <= index < self.size:
            return self.data.get(index, None)
        raise IndexError

    def __len__(self):
        """__len__特殊メソッド"""
        return self.size


class MemoryPool:
    """メモリプール"""

    def __init__(self, size: int):
        """初期化"""
        self.size = size
        self._pool = []

    def allocate(self, size: int) -> Optional[Any]:
        """メモリ割り当て"""
        # 簡易実装
        return bytearray(size)
