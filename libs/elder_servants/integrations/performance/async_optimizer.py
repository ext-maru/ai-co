"""
⚡ Elder Servants非同期実行最適化システム
Phase 3 パフォーマンス最適化：並列処理とリソース最適化

EldersServiceLegacy統合: Iron Will品質基準とエルダー評議会令第27号完全準拠
目標: 175.9%オーバーヘッドを50%以下に削減
"""

import asyncio
import gc
import logging
import threading
import time
import weakref
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Union

import psutil

# EldersLegacy統合インポート
from libs.core.elders_legacy import (
    EldersLegacyDomain,
    EldersServiceLegacy,
    IronWillCriteria,
    enforce_boundary,
)


class OptimizationStrategy(Enum):
    """最適化戦略"""

    SPEED_FIRST = "speed_first"  # 速度優先（メモリ多用）
    MEMORY_FIRST = "memory_first"  # メモリ効率優先
    BALANCED = "balanced"  # バランス型
    ADAPTIVE = "adaptive"  # 適応型（動的調整）


class ExecutionMode(Enum):
    """実行モード"""

    SEQUENTIAL = "sequential"  # 逐次実行
    CONCURRENT = "concurrent"  # 協調的並行
    PARALLEL = "parallel"  # 真の並列
    HYBRID = "hybrid"  # ハイブリッド（動的選択）


class ResourceType(Enum):
    """リソースタイプ"""

    CPU_BOUND = "cpu_bound"  # CPU集約的
    IO_BOUND = "io_bound"  # I/O集約的
    MEMORY_BOUND = "memory_bound"  # メモリ集約的
    NETWORK_BOUND = "network_bound"  # ネットワーク集約的


@dataclass
class TaskMetrics:
    """タスクメトリクス"""

    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time_ms: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    resource_type: ResourceType = ResourceType.IO_BOUND
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class ResourceLimits:
    """リソース制限"""

    max_concurrent_tasks: int = 50
    max_memory_mb: int = 500
    max_cpu_percent: int = 80
    max_execution_time_s: int = 300
    connection_pool_size: int = 20


@dataclass
class OptimizationProfile:
    """最適化プロファイル"""

    strategy: OptimizationStrategy
    mode: ExecutionMode
    limits: ResourceLimits
    adaptive_thresholds: Dict[str, float] = field(default_factory=dict)


class AsyncOptimizationRequest:
    """非同期最適化リクエスト"""

    def __init__(
        """初期化メソッド"""
        self,
        task_id: str,
        coroutine_func: Callable,
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        resource_type: ResourceType = ResourceType.IO_BOUND,
        priority: int = 1,
        timeout_s: int = 60,
    ):
        self.task_id = task_id
        self.coroutine_func = coroutine_func
        self.args = args
        self.kwargs = kwargs or {}
        self.resource_type = resource_type
        self.priority = priority
        self.timeout_s = timeout_s
        self.created_at = datetime.now()


class AsyncOptimizationResponse:
    """非同期最適化レスポンス"""

    def __init__(
        """初期化メソッド"""
        self,
        task_id: str,
        success: bool,
        result: Any = None,
        error_message: Optional[str] = None,
        metrics: Optional[TaskMetrics] = None,
    ):
        self.task_id = task_id
        self.success = success
        self.result = result
        self.error_message = error_message
        self.metrics = metrics
        self.completed_at = datetime.now()


class AsyncWorkerOptimizer(
    EldersServiceLegacy[AsyncOptimizationRequest, AsyncOptimizationResponse]
):
    """
    ⚡ Elder Servants非同期実行最適化システム

    EldersServiceLegacyから継承し、Iron Will品質基準に完全準拠。
    並列処理とリソース最適化により大幅な性能向上を実現。
    """

    def __init__(self, profile: OptimizationProfile = None):
        """初期化メソッド"""
        # EldersServiceLegacy初期化 (EXECUTION域)
        super().__init__("async_worker_optimizer")

        self.profile = profile or OptimizationProfile(
            strategy=OptimizationStrategy.BALANCED,
            mode=ExecutionMode.HYBRID,
            limits=ResourceLimits(),
        )

        self.logger = logging.getLogger("elder_servants.async_optimizer")

        # 実行統計
        self.metrics_history: List[TaskMetrics] = []
        self.active_tasks: Dict[str, TaskMetrics] = {}
        self.resource_monitor = ResourceMonitor()

        # 実行エンジン
        self.semaphore = asyncio.Semaphore(self.profile.limits.max_concurrent_tasks)
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.process_pool = ProcessPoolExecutor(max_workers=2)

        # 接続プール管理
        self.connection_pools: Dict[str, Any] = {}
        self.pool_manager = ConnectionPoolManager(
            self.profile.limits.connection_pool_size
        )

        # 適応システム
        self.adaptive_controller = AdaptiveController(self.profile)

        # Iron Will品質基準
        self.quality_threshold = 95.0

        self.logger.info(
            f"Async Worker Optimizer initialized: {self.profile.strategy.value}"
        )

    @enforce_boundary("async_optimization")
    async def process_request(
        self, request: AsyncOptimizationRequest
    ) -> AsyncOptimizationResponse:
        """
        EldersServiceLegacy統一リクエスト処理

        Args:
            request: AsyncOptimizationRequest形式のリクエスト

        Returns:
            AsyncOptimizationResponse: 最適化実行結果
        """
        start_time = time.time()
        metrics = TaskMetrics(
            task_id=request.task_id,
            start_time=datetime.now(),
            resource_type=request.resource_type,
        )

        try:
            # リソース監視開始
            self.active_tasks[request.task_id] = metrics

            # 実行モード決定
            execution_mode = await self._determine_execution_mode(request)

            # 実行
            result = await self._execute_optimized(request, execution_mode, metrics)

            # メトリクス完成
            metrics.end_time = datetime.now()
            metrics.execution_time_ms = (time.time() - start_time) * 1000
            metrics.success = True

            # 適応学習
            await self.adaptive_controller.learn_from_execution(metrics)

            return AsyncOptimizationResponse(
                task_id=request.task_id, success=True, result=result, metrics=metrics
            )

        except Exception as e:
            # Handle specific exception case
            metrics.end_time = datetime.now()
            metrics.execution_time_ms = (time.time() - start_time) * 1000
            metrics.success = False
            metrics.error_message = str(e)

            self.logger.error(
                f"Async optimization failed for {request.task_id}: {str(e)}"
            )

            return AsyncOptimizationResponse(
                task_id=request.task_id,
                success=False,
                error_message=str(e),
                metrics=metrics,
            )

        finally:
            # クリーンアップ
            if request.task_id in self.active_tasks:
                completed_metrics = self.active_tasks.pop(request.task_id)
                self.metrics_history.append(completed_metrics)

                # 履歴サイズ制限
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]

    async def _determine_execution_mode(
        self, request: AsyncOptimizationRequest
    ) -> ExecutionMode:
        """実行モード決定"""
        if self.profile.mode != ExecutionMode.HYBRID:
            return self.profile.mode

        # 適応的モード選択
        resource_usage = await self.resource_monitor.get_current_usage()

        # CPU集約的タスクでCPU使用率が高い場合は逐次実行
        if (
            request.resource_type == ResourceType.CPU_BOUND
            and resource_usage.cpu_percent > 80
        ):
            return ExecutionMode.SEQUENTIAL

        # メモリ使用量が高い場合は協調的並行
        if resource_usage.memory_percent > 75:
            return ExecutionMode.CONCURRENT

        # I/O集約的タスクは並列実行
        if request.resource_type == ResourceType.IO_BOUND:
            return ExecutionMode.PARALLEL

        return ExecutionMode.CONCURRENT

    async def _execute_optimized(
        self,
        request: AsyncOptimizationRequest,
        mode: ExecutionMode,
        metrics: TaskMetrics,
    ) -> Any:
        """最適化実行"""
        async with self.semaphore:  # 同時実行数制限
            if mode == ExecutionMode.SEQUENTIAL:
                return await self._execute_sequential(request, metrics)
            elif mode == ExecutionMode.CONCURRENT:
                return await self._execute_concurrent(request, metrics)
            elif mode == ExecutionMode.PARALLEL:
                return await self._execute_parallel(request, metrics)
            else:
                return await self._execute_concurrent(request, metrics)

    async def _execute_sequential(
        self, request: AsyncOptimizationRequest, metrics: TaskMetrics
    ) -> Any:
        """逐次実行"""
        coroutine = request.coroutine_func(*request.args, **request.kwargs)

        try:
            result = await asyncio.wait_for(coroutine, timeout=request.timeout_s)
            return result
        except asyncio.TimeoutError:
            # Handle specific exception case
            raise Exception(
                f"Task {request.task_id} timed out after {request.timeout_s}s"
            )

    async def _execute_concurrent(
        self, request: AsyncOptimizationRequest, metrics: TaskMetrics
    ) -> Any:
        """協調的並行実行"""
        # メモリ使用量監視
        memory_before = self.resource_monitor.get_memory_usage()

        try:
            coroutine = request.coroutine_func(*request.args, **request.kwargs)
            result = await asyncio.wait_for(coroutine, timeout=request.timeout_s)

            # メモリ使用量記録
            memory_after = self.resource_monitor.get_memory_usage()
            metrics.memory_peak_mb = max(memory_before, memory_after)

            return result

        except asyncio.TimeoutError:
            # Handle specific exception case
            raise Exception(
                f"Task {request.task_id} timed out after {request.timeout_s}s"
            )

    async def _execute_parallel(
        self, request: AsyncOptimizationRequest, metrics: TaskMetrics
    ) -> Any:
        """真の並列実行（スレッドプール使用）"""
        loop = asyncio.get_event_loop()

        try:
            if request.resource_type == ResourceType.CPU_BOUND:
                # CPU集約的タスクはプロセスプールで実行
                future = self.process_pool.submit(
                    self._execute_in_process,
                    request.coroutine_func,
                    request.args,
                    request.kwargs,
                )
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, future.result), timeout=request.timeout_s
                )
            else:
                # I/O集約的タスクはスレッドプールで実行
                result = await loop.run_in_executor(
                    self.thread_pool,
                    self._execute_in_thread,
                    request.coroutine_func,
                    request.args,
                    request.kwargs,
                )

            return result

        except asyncio.TimeoutError:
            # Handle specific exception case
            raise Exception(
                f"Task {request.task_id} timed out after {request.timeout_s}s"
            )

    def _execute_in_thread(
        self, coroutine_func: Callable, args: tuple, kwargs: Dict[str, Any]
    ) -> Any:
        """スレッドプール内実行"""
        # 新しいイベントループを作成して実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            coroutine = coroutine_func(*args, **kwargs)
            result = loop.run_until_complete(coroutine)
            return result
        finally:
            loop.close()

    def _execute_in_process(
        self, coroutine_func: Callable, args: tuple, kwargs: Dict[str, Any]
    ) -> Any:
        """プロセスプール内実行（プロセス間通信用）"""
        # プロセスプール用の同期実行
        # 注意: coroutine_funcは同期関数である必要がある
        if asyncio.iscoroutinefunction(coroutine_func):
            raise ValueError("Process pool execution requires non-coroutine function")
        return coroutine_func(*args, **kwargs)

    def validate_request(self, request: AsyncOptimizationRequest) -> bool:
        """EldersServiceLegacyリクエスト検証"""
        if not request.task_id:
            return False
        if not callable(request.coroutine_func):
            return False
        if request.timeout_s <= 0:
            return False
        if not isinstance(request.resource_type, ResourceType):
            return False
        return True

    def get_capabilities(self) -> List[str]:
        """EldersServiceLegacy能力取得"""
        return [
            "async_optimization",
            "concurrent_execution",
            "parallel_processing",
            "resource_monitoring",
            "adaptive_optimization",
            "connection_pool_management",
            "performance_profiling",
        ]

    async def batch_execute(
        self, requests: List[AsyncOptimizationRequest]
    ) -> List[AsyncOptimizationResponse]:
        """バッチ実行（高性能並列処理）"""
        if not requests:
            return []

        # 優先度でソート
        sorted_requests = sorted(requests, key=lambda r: r.priority, reverse=True)

        # リソースタイプ別グルーピング
        grouped_requests = self._group_by_resource_type(sorted_requests)

        # 並列実行
        all_tasks = []
        for resource_type, type_requests in grouped_requests.items():
            # リソースタイプ別の最適化
            if resource_type == ResourceType.IO_BOUND:
                # I/O集約的タスクは大量並列実行
                tasks = [self.process_request(req) for req in type_requests]
                all_tasks.extend(tasks)
            elif resource_type == ResourceType.CPU_BOUND:
                # CPU集約的タスクは制限付き実行
                batch_size = min(len(type_requests), psutil.cpu_count())
                for i in range(0, len(type_requests), batch_size):
                    batch = type_requests[i : i + batch_size]
                    tasks = [self.process_request(req) for req in batch]
                    all_tasks.extend(tasks)
            else:
                # その他は標準並列実行
                tasks = [self.process_request(req) for req in type_requests]
                all_tasks.extend(tasks)

        # 全タスク実行
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # 例外を適切なレスポンスに変換
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append(
                    AsyncOptimizationResponse(
                        task_id=f"batch_task_{i}",
                        success=False,
                        error_message=str(result),
                    )
                )
            else:
                responses.append(result)

        return responses

    def _group_by_resource_type(
        self, requests: List[AsyncOptimizationRequest]
    ) -> Dict[ResourceType, List[AsyncOptimizationRequest]]:
        """リソースタイプ別グルーピング"""
        groups = {}
        for request in requests:
            # Process each item in collection
            if request.resource_type not in groups:
                groups[request.resource_type] = []
            groups[request.resource_type].append(request)
        return groups

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクス取得"""
        if not self.metrics_history:
            return {"message": "No metrics available"}

        # 統計計算
        successful_tasks = [m for m in self.metrics_history if m.success]
        total_tasks = len(self.metrics_history)
        success_rate = len(successful_tasks) / total_tasks if total_tasks > 0 else 0

        execution_times = [m.execution_time_ms for m in successful_tasks]
        avg_execution_time = (
            sum(execution_times) / len(execution_times) if execution_times else 0
        )

        memory_peaks = [
            m.memory_peak_mb for m in successful_tasks if m.memory_peak_mb > 0
        ]
        avg_memory_peak = sum(memory_peaks) / len(memory_peaks) if memory_peaks else 0

        # リソースタイプ別統計
        resource_stats = {}
        for resource_type in ResourceType:
            type_metrics = [
                m for m in successful_tasks if m.resource_type == resource_type
            ]
            if type_metrics:
                type_times = [m.execution_time_ms for m in type_metrics]
                resource_stats[resource_type.value] = {
                    "count": len(type_metrics),
                    "avg_execution_time_ms": sum(type_times) / len(type_times),
                    "success_rate": len(type_metrics)
                    / len(
                        [
                            m
                            for m in self.metrics_history
                            if m.resource_type == resource_type
                        ]
                    ),
                }

        # 現在のリソース使用量
        current_usage = await self.resource_monitor.get_current_usage()

        return {
            "total_tasks": total_tasks,
            "success_rate": round(success_rate * 100, 2),
            "average_execution_time_ms": round(avg_execution_time, 2),
            "average_memory_peak_mb": round(avg_memory_peak, 2),
            "active_tasks": len(self.active_tasks),
            "resource_stats": resource_stats,
            "current_resource_usage": {
                "cpu_percent": current_usage.cpu_percent,
                "memory_percent": current_usage.memory_percent,
                "memory_mb": current_usage.memory_mb,
            },
            "optimization_profile": {
                "strategy": self.profile.strategy.value,
                "mode": self.profile.mode.value,
                "limits": {
                    "max_concurrent_tasks": self.profile.limits.max_concurrent_tasks,
                    "max_memory_mb": self.profile.limits.max_memory_mb,
                },
            },
            "iron_will_compliance": success_rate >= 0.95,  # 95%以上の成功率
        }

    async def optimize_profile(self) -> OptimizationProfile:
        """プロファイル最適化（適応学習）"""
        return await self.adaptive_controller.optimize_profile(self.metrics_history)

    async def cleanup_resources(self):
        """リソースクリーンアップ"""
        # アクティブタスクのキャンセル
        for task_id in list(self.active_tasks.keys()):
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

        # 実行プールのシャットダウン
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

        # 接続プールクリーンアップ
        await self.pool_manager.cleanup_all()

        # メモリクリーンアップ
        gc.collect()

        self.logger.info("Async optimizer resources cleaned up")

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # 基本ヘルスチェック
            base_health = await super().health_check()

            # リソース使用量確認
            resource_usage = await self.resource_monitor.get_current_usage()

            # パフォーマンス統計
            if self.metrics_history:
                recent_metrics = self.metrics_history[-100:]  # 最近100件
                success_rate = len([m for m in recent_metrics if m.success]) / len(
                    recent_metrics
                )
                avg_execution_time = sum(
                    m.execution_time_ms for m in recent_metrics if m.success
                ) / max(len([m for m in recent_metrics if m.success]), 1)
            else:
                success_rate = 1.0
                avg_execution_time = 0.0

            # 健全性判定
            resource_healthy = (
                resource_usage.cpu_percent < 90 and resource_usage.memory_percent < 85
            )

            performance_healthy = (
                success_rate >= 0.95 and avg_execution_time < 10000  # 10秒以下
            )

            overall_healthy = resource_healthy and performance_healthy

            return {
                **base_health,
                "optimizer_status": "healthy" if overall_healthy else "degraded",
                "active_tasks": len(self.active_tasks),
                "resource_usage": {
                    "cpu_percent": resource_usage.cpu_percent,
                    "memory_percent": resource_usage.memory_percent,
                    "memory_mb": resource_usage.memory_mb,
                },
                "performance": {
                    "success_rate": round(success_rate * 100, 2),
                    "average_execution_time_ms": round(avg_execution_time, 2),
                },
                "optimization_profile": self.profile.strategy.value,
                "iron_will_compliance": overall_healthy,
            }

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Health check failed: {str(e)}")
            return {"success": False, "status": "error", "error": str(e)}


class ResourceMonitor:
    """リソース監視クラス"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger("elder_servants.resource_monitor")

    @dataclass
    class ResourceUsage:
        # Main class implementation
        cpu_percent: float
        memory_percent: float
        memory_mb: float
        available_memory_mb: float
        timestamp: datetime = field(default_factory=datetime.now)

    async def get_current_usage(self) -> "ResourceMonitor.ResourceUsage":
        """現在のリソース使用量取得"""
        try:
            # CPU使用率（1秒間測定）
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # メモリ使用量
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_mb = memory.used / 1024 / 1024
            available_memory_mb = memory.available / 1024 / 1024

            return self.ResourceUsage(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                available_memory_mb=available_memory_mb,
            )

        except Exception as e:
            # Handle specific exception case
            self.logger.warning(f"Failed to get resource usage: {str(e)}")
            return self.ResourceUsage(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_mb=0.0,
                available_memory_mb=0.0,
            )

    def get_memory_usage(self) -> float:
        """メモリ使用量取得（MB）"""
        try:
            return psutil.virtual_memory().used / 1024 / 1024
        except:
            return 0.0


class ConnectionPoolManager:
    """接続プール管理"""

    def __init__(self, default_pool_size: int = 20):
        """初期化メソッド"""
        self.default_pool_size = default_pool_size
        self.pools: Dict[str, Any] = {}
        self.logger = logging.getLogger("elder_servants.connection_pool")

    async def get_pool(self, pool_name: str, pool_type: str = "generic") -> Any:
        """プール取得（遅延作成）"""
        if pool_name not in self.pools:
            # プールタイプに応じて適切なプールを作成
            # 実装は具体的なプールタイプに依存
            self.pools[pool_name] = await self._create_pool(pool_name, pool_type)

        return self.pools[pool_name]

    async def _create_pool(self, pool_name: str, pool_type: str) -> Any:
        """プール作成"""
        # プレースホルダー実装
        # 実際の実装では具体的なプールクラスを使用
        self.logger.info(f"Created connection pool: {pool_name} ({pool_type})")
        return {
            "pool_name": pool_name,
            "pool_type": pool_type,
            "size": self.default_pool_size,
        }

    async def cleanup_all(self):
        """全プールクリーンアップ"""
        for pool_name, pool in self.pools.items():
            try:
                # プール固有のクリーンアップ処理
                if hasattr(pool, "close"):
                    await pool.close()
                self.logger.info(f"Cleaned up connection pool: {pool_name}")
            except Exception as e:
                # Handle specific exception case
                self.logger.warning(f"Failed to cleanup pool {pool_name}: {str(e)}")

        self.pools.clear()


class AdaptiveController:
    """適応制御システム"""

    def __init__(self, profile: OptimizationProfile):
        """初期化メソッド"""
        self.profile = profile
        self.learning_history: List[TaskMetrics] = []
        self.logger = logging.getLogger("elder_servants.adaptive_controller")

    async def learn_from_execution(self, metrics: TaskMetrics):
        """実行結果からの学習"""
        self.learning_history.append(metrics)

        # 履歴サイズ制限
        if len(self.learning_history) > 500:
            self.learning_history = self.learning_history[-500:]

        # 適応的調整（簡易版）
        if len(self.learning_history) >= 10:
            await self._adjust_parameters()

    async def _adjust_parameters(self):
        """パラメータ自動調整"""
        recent_metrics = self.learning_history[-10:]

        # 成功率計算
        success_rate = len([m for m in recent_metrics if m.success]) / len(
            recent_metrics
        )

        # 平均実行時間
        successful_metrics = [m for m in recent_metrics if m.success]
        if successful_metrics:
            avg_execution_time = sum(
                m.execution_time_ms for m in successful_metrics
            ) / len(successful_metrics)

            # 実行時間が長い場合は並列度を上げる
            if avg_execution_time > 5000:  # 5秒以上
                current_limit = self.profile.limits.max_concurrent_tasks
                new_limit = min(current_limit + 5, 100)
                self.profile.limits.max_concurrent_tasks = new_limit
                self.logger.info(f"Increased concurrent task limit to {new_limit}")

        # 成功率が低い場合は保守的に調整
        if success_rate < 0.9:
            current_limit = self.profile.limits.max_concurrent_tasks
            new_limit = max(current_limit - 5, 10)
            self.profile.limits.max_concurrent_tasks = new_limit
            self.logger.info(
                f"Decreased concurrent task limit to {new_limit} due to low success rate"
            )

    async def optimize_profile(
        self, all_metrics: List[TaskMetrics]
    ) -> OptimizationProfile:
        """プロファイル最適化"""
        if not all_metrics:
            return self.profile

        # メトリクス分析
        successful_metrics = [m for m in all_metrics if m.success]

        if not successful_metrics:
            return self.profile

        # リソースタイプ別分析
        io_bound_metrics = [
            m for m in successful_metrics if m.resource_type == ResourceType.IO_BOUND
        ]
        cpu_bound_metrics = [
            m for m in successful_metrics if m.resource_type == ResourceType.CPU_BOUND
        ]

        # 最適化戦略決定
        if len(io_bound_metrics) > len(cpu_bound_metrics) * 2:
            # I/O集約的タスクが多い場合
            optimized_strategy = OptimizationStrategy.SPEED_FIRST
            optimized_mode = ExecutionMode.PARALLEL
        elif len(cpu_bound_metrics) > len(io_bound_metrics):
            # CPU集約的タスクが多い場合
            optimized_strategy = OptimizationStrategy.MEMORY_FIRST
            optimized_mode = ExecutionMode.CONCURRENT
        else:
            # バランス型
            optimized_strategy = OptimizationStrategy.BALANCED
            optimized_mode = ExecutionMode.HYBRID

        # 最適化されたプロファイル作成
        optimized_profile = OptimizationProfile(
            strategy=optimized_strategy,
            mode=optimized_mode,
            limits=self.profile.limits,  # 制限は現在の値を維持
        )

        self.logger.info(
            f"Optimized profile: {optimized_strategy.value}, {optimized_mode.value}"
        )
        return optimized_profile


# 便利関数群
async def execute_async_optimized(
    coroutine_func: Callable,
    *args,
    resource_type: ResourceType = ResourceType.IO_BOUND,
    timeout_s: int = 60,
    **kwargs,
) -> Any:
    """非同期最適化実行（便利関数）"""
    optimizer = AsyncWorkerOptimizer()

    request = AsyncOptimizationRequest(
        task_id=f"quick_task_{int(time.time())}",
        coroutine_func=coroutine_func,
        args=args,
        kwargs=kwargs,
        resource_type=resource_type,
        timeout_s=timeout_s,
    )

    try:
        response = await optimizer.process_request(request)
        if response.success:
            return response.result
        else:
            raise Exception(response.error_message)
    finally:
        await optimizer.cleanup_resources()


def async_optimized(
    resource_type: ResourceType = ResourceType.IO_BOUND, timeout_s: int = 60
):
    """非同期最適化デコレータ"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await execute_async_optimized(
                func, *args, resource_type=resource_type, timeout_s=timeout_s, **kwargs
            )

        return wrapper

    return decorator


# グローバル最適化インスタンス
_global_optimizer: Optional[AsyncWorkerOptimizer] = None


async def get_global_optimizer() -> AsyncWorkerOptimizer:
    """グローバル最適化インスタンス取得"""
    global _global_optimizer

    if _global_optimizer is None:
        _global_optimizer = AsyncWorkerOptimizer()

    return _global_optimizer
