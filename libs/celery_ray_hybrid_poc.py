#!/usr/bin/env python3
"""
Celery + Ray ハイブリッドPOC - OSS移行プロジェクト
Celeryでタスク管理、Rayで並列処理を実現するハイブリッドアプローチ
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import ray
from celery import Celery

# Celeryアプリケーション
app = Celery("hybrid_workers")
app.config_from_object(
    {
        "broker_url": "redis://localhost:6379/1",
        "result_backend": "redis://localhost:6379/1",
    }
)

# Rayの初期化（実際の使用時に初期化）
# ray.init(address='auto')  # Rayクラスターに接続


@dataclass
class OptimizationResult:
    """最適化結果"""

    task_id: str
    processing_time: float
    method: str  # 'celery', 'ray', 'hybrid'
    result: Any
    metrics: Dict[str, Any]


class HybridWorkerOptimizer:
    """Celery + Rayハイブリッド最適化器"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.ray_initialized = False

    def _ensure_ray(self):
        """Rayの初期化を確認"""
        if not self.ray_initialized:
            try:
                ray.init(address="auto", ignore_reinit_error=True)
                self.ray_initialized = True
            except:
                # ローカルモードで初期化
                ray.init(ignore_reinit_error=True)
                self.ray_initialized = True

    async def optimize_with_ray(self, items: List[Any], func) -> List[Any]:
        """Rayを使用した並列処理"""
        self._ensure_ray()

        # Rayリモート関数の定義
        @ray.remote
        def ray_process_item(item):
            return func(item)

        # 並列実行
        futures = [ray_process_item.remote(item) for item in items]
        results = ray.get(futures)

        return results

    def optimize_with_celery(self, items: List[Any], task_name: str) -> List[Any]:
        """Celeryを使用したタスク管理"""
        from celery import group

        # Celeryタスクの取得
        task = app.tasks.get(task_name)
        if not task:
            raise ValueError(f"Task {task_name} not found")

        # グループタスクとして実行
        job = group(task.s(item) for item in items)
        result = job.apply_async()

        return result.get(timeout=300)

    async def hybrid_optimization(
        self, items: List[Any], threshold: int = 100
    ) -> OptimizationResult:
        """ハイブリッド最適化

        小規模タスク: Celery（タスク管理の利点）
        大規模タスク: Ray（高速並列処理）
        """
        start_time = time.time()

        if len(items) < threshold:
            # 小規模: Celeryを使用
            self.logger.info(f"Using Celery for {len(items)} items")
            results = self.optimize_with_celery(items, "process_small_batch")
            method = "celery"
        else:
            # 大規模: Rayを使用
            self.logger.info(f"Using Ray for {len(items)} items")
            results = await self.optimize_with_ray(items, self._process_large_item)
            method = "ray"

        processing_time = time.time() - start_time

        return OptimizationResult(
            task_id=f"hybrid_{int(time.time())}",
            processing_time=processing_time,
            method=method,
            result=results,
            metrics={
                "items_count": len(items),
                "avg_time_per_item": processing_time / len(items),
                "memory_usage": psutil.Process().memory_info().rss / 1024 / 1024,  # MB
            },
        )

    def _process_large_item(self, item):
        """大規模アイテムの処理（Ray用）"""
        # 重い計算のシミュレーション
        import numpy as np

        data = np.random.rand(1000, 1000)
        result = np.sum(data)
        return {"item": item, "result": result}

    def create_adaptive_pipeline(self) -> "AdaptivePipeline":
        """適応的パイプラインの作成"""
        return AdaptivePipeline(self)


class AdaptivePipeline:
    """適応的パイプライン（Celery + Ray）"""

    def __init__(self, optimizer: HybridWorkerOptimizer):
        self.optimizer = optimizer
        self.stages = []

    def add_stage(self, name: str, func, use_ray: bool = False):
        """ステージの追加"""
        self.stages.append({"name": name, "func": func, "use_ray": use_ray})
        return self

    async def execute(self, data: Any) -> Any:
        """パイプラインの実行"""
        result = data

        for stage in self.stages:
            if stage["use_ray"]:
                # Rayで実行
                self.optimizer._ensure_ray()
                remote_func = ray.remote(stage["func"])
                result = await remote_func.remote(result)
            else:
                # 通常実行
                result = stage["func"](result)

        return result


# Celeryタスク定義
@app.task(name="process_small_batch")
def process_small_batch(item: Dict[str, Any]) -> Dict[str, Any]:
    """小規模バッチ処理（Celery）"""
    # 軽い処理
    return {"id": item.get("id"), "processed_by": "celery", "timestamp": time.time()}


@app.task(name="orchestrate_hybrid_job")
def orchestrate_hybrid_job(job_config: Dict[str, Any]) -> Dict[str, Any]:
    """ハイブリッドジョブのオーケストレーション"""
    optimizer = HybridWorkerOptimizer()

    # 非同期処理を同期的に実行
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    items = job_config.get("items", [])
    threshold = job_config.get("threshold", 100)

    result = loop.run_until_complete(optimizer.hybrid_optimization(items, threshold))

    return {
        "job_id": result.task_id,
        "method": result.method,
        "processing_time": result.processing_time,
        "metrics": result.metrics,
    }


# Ray アクター（ステートフルな処理用）
@ray.remote
class RayWorkerPool:
    """Rayワーカープール"""

    def __init__(self, size: int = 4):
        self.size = size
        self.tasks_processed = 0

    def process_batch(self, items: List[Any]) -> List[Any]:
        """バッチ処理"""
        results = []
        for item in items:
            # 処理ロジック
            result = {"item": item, "processed": True}
            results.append(result)
            self.tasks_processed += 1
        return results

    def get_stats(self) -> Dict[str, Any]:
        """統計情報の取得"""
        return {"pool_size": self.size, "tasks_processed": self.tasks_processed}


class PerformanceComparator:
    """パフォーマンス比較ツール"""

    def __init__(self):
        self.results = []

    async def compare_methods(self, items: List[Any], iterations: int = 3):
        """Celery vs Ray vs Hybrid の比較"""
        methods = ["celery", "ray", "hybrid"]

        for method in methods:
            times = []
            for i in range(iterations):
                start = time.time()

                if method == "celery":
                    # Celeryのみ
                    optimizer = HybridWorkerOptimizer()
                    result = optimizer.optimize_with_celery(
                        items, "process_small_batch"
                    )
                elif method == "ray":
                    # Rayのみ
                    optimizer = HybridWorkerOptimizer()
                    result = await optimizer.optimize_with_ray(
                        items, lambda x: {"processed": x}
                    )
                else:
                    # ハイブリッド
                    optimizer = HybridWorkerOptimizer()
                    result = await optimizer.hybrid_optimization(items)

                elapsed = time.time() - start
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            self.results.append(
                {
                    "method": method,
                    "avg_time": avg_time,
                    "items_count": len(items),
                    "throughput": len(items) / avg_time,
                }
            )

        return self.results

    def print_comparison(self):
        """比較結果の表示"""
        print("\n" + "=" * 60)
        print("Performance Comparison: Celery vs Ray vs Hybrid")
        print("=" * 60)

        for result in self.results:
            print(f"\nMethod: {result['method']}")
            print(f"  Average Time: {result['avg_time']:.3f}s")
            print(f"  Throughput: {result['throughput']:.1f} items/s")


# デモ用関数
async def demo_hybrid_optimization():
    """ハイブリッド最適化のデモ"""
    print("🚀 Hybrid Worker Optimization Demo")

    # テストデータ
    small_batch = [{"id": i, "data": f"item-{i}"} for i in range(50)]
    large_batch = [{"id": i, "data": f"item-{i}"} for i in range(500)]

    optimizer = HybridWorkerOptimizer()

    # 小規模バッチ（Celery使用）
    print("\n📦 Small batch optimization...")
    small_result = await optimizer.hybrid_optimization(small_batch, threshold=100)
    print(f"Method: {small_result.method}")
    print(f"Time: {small_result.processing_time:.3f}s")

    # 大規模バッチ（Ray使用）
    print("\n📦 Large batch optimization...")
    large_result = await optimizer.hybrid_optimization(large_batch, threshold=100)
    print(f"Method: {large_result.method}")
    print(f"Time: {large_result.processing_time:.3f}s")

    # パフォーマンス比較
    print("\n📊 Performance comparison...")
    comparator = PerformanceComparator()
    await comparator.compare_methods(small_batch)
    comparator.print_comparison()


if __name__ == "__main__":
    # デモ実行
    import asyncio

    asyncio.run(demo_hybrid_optimization())
