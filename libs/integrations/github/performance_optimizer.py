#!/usr/bin/env python3
"""
⚡ Auto Issue Processor A2A Performance Optimizer
並列処理性能最適化・スケーラビリティ向上システム

Issue #192対応: 動的並列処理スケーリング・Claude CLI実行プール最適化
"""

import asyncio
import json
import logging
import multiprocessing
import os
import psutil
import resource
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional, Set, Tuple
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import weakref

logger = logging.getLogger("PerformanceOptimizer")


class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    CLAUDE_CLI = "claude_cli"


class OptimizationStrategy(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    LOAD_BALANCE = "load_balance"
    CACHE_OPTIMIZE = "cache_optimize"
    MEMORY_OPTIMIZE = "memory_optimize"


@dataclass
class ResourceMetrics:
    """リソースメトリクス"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read: float
    disk_io_write: float
    network_io_sent: float
    network_io_recv: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceTarget:
    """パフォーマンス目標"""
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 85.0
    max_response_time: float = 30.0
    min_throughput: float = 2.0  # issues/second
    max_queue_size: int = 100


@dataclass
class OptimizationResult:
    """最適化結果"""
    strategy: OptimizationStrategy
    old_value: Any
    new_value: Any
    improvement_percent: float
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourceMonitor:
    """リソース監視システム"""
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: Deque[ResourceMetrics] = deque(maxlen=1000)
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # システム情報
        self.cpu_count = multiprocessing.cpu_count()
        self.total_memory = psutil.virtual_memory().total / (1024 * 1024)  # MB
    
    async def start_monitoring(self):
        """監視開始"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """監視停止"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """監視ループ"""
        try:
            while self.is_monitoring:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                await asyncio.sleep(self.monitoring_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Monitoring loop error: {str(e)}")
    
    def _collect_metrics(self) -> ResourceMetrics:
        """メトリクス収集"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # メモリ使用状況
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        
        # ディスクI/O
        disk_io = psutil.disk_io_counters()
        disk_io_read = disk_io.read_bytes / (1024 * 1024) if disk_io else 0  # MB
        disk_io_write = disk_io.write_bytes / (1024 * 1024) if disk_io else 0  # MB
        
        # ネットワークI/O
        network_io = psutil.net_io_counters()
        network_io_sent = network_io.bytes_sent / (1024 * 1024) if network_io else 0  # MB
        network_io_recv = network_io.bytes_recv / (1024 * 1024) if network_io else 0  # MB
        
        return ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            network_io_sent=network_io_sent,
            network_io_recv=network_io_recv
        )
    
    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """現在のメトリクス取得"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_average_metrics(self, duration_minutes: int = 5) -> Optional[ResourceMetrics]:
        """平均メトリクス取得"""
        if not self.metrics_history:
            return None
        
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return None
        
        count = len(recent_metrics)
        return ResourceMetrics(
            cpu_percent=sum(m.cpu_percent for m in recent_metrics) / count,
            memory_percent=sum(m.memory_percent for m in recent_metrics) / count,
            memory_used_mb=sum(m.memory_used_mb for m in recent_metrics) / count,
            disk_io_read=sum(m.disk_io_read for m in recent_metrics) / count,
            disk_io_write=sum(m.disk_io_write for m in recent_metrics) / count,
            network_io_sent=sum(m.network_io_sent for m in recent_metrics) / count,
            network_io_recv=sum(m.network_io_recv for m in recent_metrics) / count
        )


class ClaudeCLIExecutionPool:
    """Claude CLI実行プール"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(8, multiprocessing.cpu_count())
        self.current_workers = 2  # 初期値
        
        # プール管理
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.process_pool: Optional[ProcessPoolExecutor] = None
        
        # 実行キュー
        self.execution_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.active_executions: Set[str] = set()
        
        # 統計情報
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "queue_wait_time": 0.0
        }
        
        # キャッシュ
        self.result_cache: Dict[str, Any] = {}
        self.cache_max_size = 100
        self.cache_ttl = timedelta(hours=1)
        
        self._setup_pools()
    
    def _setup_pools(self):
        """プールセットアップ"""
        try:
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.current_workers,
                thread_name_prefix="claude_cli"
            )
            
            # プロセスプールは必要に応じて作成
            # self.process_pool = ProcessPoolExecutor(max_workers=2)
            
            logger.info(f"Claude CLI execution pool initialized with {self.current_workers} workers")
            
        except Exception as e:
            logger.error(f"Failed to setup execution pools: {str(e)}")
    
    async def execute_claude_cli(
        self, 
        prompt: str, 
        model: str = "claude-sonnet-4-20250514",
        cache_key: Optional[str] = None,
        priority: int = 1
    ) -> str:
        """Claude CLI実行（プール管理付き）"""
        execution_id = f"exec_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            # キャッシュチェック
            if cache_key and cache_key in self.result_cache:
                cache_entry = self.result_cache[cache_key]
                if datetime.now() - cache_entry["timestamp"] < self.cache_ttl:
                    logger.info(f"Cache hit for key: {cache_key}")
                    return cache_entry["result"]
            
            # 実行キューに追加
            queue_start = time.time()
            await self.execution_queue.put((execution_id, prompt, model, priority))
            queue_wait_time = time.time() - queue_start
            
            # 実行処理
            self.active_executions.add(execution_id)
            
            try:
                # スレッドプールで実行
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_pool,
                    self._execute_claude_cli_sync,
                    prompt,
                    model
                )
                
                # 統計更新
                execution_time = time.time() - start_time
                self._update_execution_stats(execution_time, queue_wait_time, True)
                
                # キャッシュ保存
                if cache_key:
                    self._cache_result(cache_key, result)
                
                return result
                
            finally:
                self.active_executions.discard(execution_id)
        
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_execution_stats(execution_time, 0, False)
            logger.error(f"Claude CLI execution failed: {str(e)}")
            raise
    
    def _execute_claude_cli_sync(self, prompt: str, model: str) -> str:
        """Claude CLI同期実行"""
        try:
            from libs.claude_cli_executor import ClaudeCLIExecutor
            
            executor = ClaudeCLIExecutor()
            result = executor.execute(
                prompt=prompt,
                model=model,
                working_dir=str(Path.cwd())
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Claude CLI sync execution error: {str(e)}")
            raise
    
    def _update_execution_stats(self, execution_time: float, queue_wait_time: float, success: bool):
        """実行統計更新"""
        self.execution_stats["total_executions"] += 1
        
        if success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1
        
        # 移動平均で平均実行時間を更新
        total = self.execution_stats["total_executions"]
        old_avg = self.execution_stats["average_execution_time"]
        self.execution_stats["average_execution_time"] = (old_avg * (total - 1) + execution_time) / total
        
        # キュー待機時間も更新
        old_queue_avg = self.execution_stats["queue_wait_time"]
        self.execution_stats["queue_wait_time"] = (old_queue_avg * (total - 1) + queue_wait_time) / total
    
    def _cache_result(self, cache_key: str, result: str):
        """結果キャッシュ"""
        # キャッシュサイズ制限
        if len(self.result_cache) >= self.cache_max_size:
            # 古いエントリを削除
            oldest_key = min(
                self.result_cache.keys(),
                key=lambda k: self.result_cache[k]["timestamp"]
            )
            del self.result_cache[oldest_key]
        
        self.result_cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now()
        }
    
    async def scale_workers(self, new_worker_count: int) -> bool:
        """ワーカー数スケーリング"""
        try:
            if new_worker_count == self.current_workers:
                return True
            
            old_count = self.current_workers
            
            # 既存プールをシャットダウン
            if self.thread_pool:
                self.thread_pool.shutdown(wait=False)
            
            # 新しいプールを作成
            self.current_workers = min(new_worker_count, self.max_workers)
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.current_workers,
                thread_name_prefix="claude_cli"
            )
            
            logger.info(f"Scaled Claude CLI workers: {old_count} -> {self.current_workers}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to scale workers: {str(e)}")
            return False
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """プール統計取得"""
        return {
            "current_workers": self.current_workers,
            "max_workers": self.max_workers,
            "active_executions": len(self.active_executions),
            "queue_size": self.execution_queue.qsize(),
            "cache_size": len(self.result_cache),
            "execution_stats": self.execution_stats.copy()
        }
    
    async def cleanup(self):
        """クリーンアップ"""
        try:
            if self.thread_pool:
                self.thread_pool.shutdown(wait=True)
            if self.process_pool:
                self.process_pool.shutdown(wait=True)
            
            logger.info("Claude CLI execution pool cleaned up")
            
        except Exception as e:
            logger.error(f"Pool cleanup error: {str(e)}")


class DynamicScaler:
    """動的スケーリングシステム"""
    
    def __init__(self, resource_monitor: ResourceMonitor, execution_pool: ClaudeCLIExecutionPool):
        self.resource_monitor = resource_monitor
        self.execution_pool = execution_pool
        self.performance_target = PerformanceTarget()
        
        # スケーリング履歴
        self.scaling_history: List[OptimizationResult] = []
        self.last_scale_time = datetime.now()
        self.scale_cooldown = timedelta(minutes=2)  # スケーリング間隔
    
    async def auto_scale(self) -> List[OptimizationResult]:
        """自動スケーリング実行"""
        optimizations = []
        
        # クールダウン期間チェック
        if datetime.now() - self.last_scale_time < self.scale_cooldown:
            return optimizations
        
        try:
            # 現在のメトリクス取得
            current_metrics = self.resource_monitor.get_current_metrics()
            if not current_metrics:
                return optimizations
            
            # 平均メトリクス取得
            avg_metrics = self.resource_monitor.get_average_metrics(5)
            if not avg_metrics:
                avg_metrics = current_metrics
            
            # プール統計取得
            pool_stats = self.execution_pool.get_pool_stats()
            
            # スケーリング判定
            scale_decision = self._analyze_scaling_need(avg_metrics, pool_stats)
            
            if scale_decision["action"] != "no_action":
                optimization = await self._execute_scaling(scale_decision)
                if optimization:
                    optimizations.append(optimization)
                    self.scaling_history.append(optimization)
                    self.last_scale_time = datetime.now()
            
            # メモリ最適化
            memory_optimization = await self._optimize_memory_usage(avg_metrics)
            if memory_optimization:
                optimizations.append(memory_optimization)
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Auto-scaling error: {str(e)}")
            return optimizations
    
    def _analyze_scaling_need(self, metrics: ResourceMetrics, pool_stats: Dict[str, Any]) -> Dict[str, Any]:
        """スケーリング必要性分析"""
        decision = {
            "action": "no_action",
            "reason": "metrics within target range",
            "target_workers": pool_stats["current_workers"]
        }
        
        current_workers = pool_stats["current_workers"]
        max_workers = pool_stats["max_workers"]
        queue_size = pool_stats["queue_size"]
        avg_execution_time = pool_stats["execution_stats"]["average_execution_time"]
        
        # スケールアップ条件
        scale_up_conditions = [
            metrics.cpu_percent < 60 and queue_size > 10,  # CPU余裕ありかつキュー蓄積
            avg_execution_time > self.performance_target.max_response_time,  # 応答時間超過
            queue_size > 20,  # キュー過多
        ]
        
        # スケールダウン条件
        scale_down_conditions = [
            metrics.cpu_percent < 30 and queue_size == 0,  # CPU低使用率かつキューなし
            pool_stats["active_executions"] == 0 and current_workers > 2,  # アイドル状態
        ]
        
        if any(scale_up_conditions) and current_workers < max_workers:
            new_workers = min(current_workers + 2, max_workers)
            decision.update({
                "action": "scale_up",
                "reason": "performance bottleneck detected",
                "target_workers": new_workers
            })
        
        elif all(scale_down_conditions) and current_workers > 2:
            new_workers = max(current_workers - 1, 2)
            decision.update({
                "action": "scale_down",
                "reason": "low utilization detected",
                "target_workers": new_workers
            })
        
        return decision
    
    async def _execute_scaling(self, decision: Dict[str, Any]) -> Optional[OptimizationResult]:
        """スケーリング実行"""
        try:
            start_time = time.time()
            old_workers = self.execution_pool.current_workers
            new_workers = decision["target_workers"]
            
            success = await self.execution_pool.scale_workers(new_workers)
            
            if success:
                execution_time = time.time() - start_time
                improvement = ((new_workers - old_workers) / old_workers) * 100
                
                strategy = OptimizationStrategy.SCALE_UP if new_workers > old_workers else OptimizationStrategy.SCALE_DOWN
                
                return OptimizationResult(
                    strategy=strategy,
                    old_value=old_workers,
                    new_value=new_workers,
                    improvement_percent=abs(improvement),
                    execution_time=execution_time,
                    metadata={
                        "reason": decision["reason"],
                        "action": decision["action"]
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Scaling execution failed: {str(e)}")
            return None
    
    async def _optimize_memory_usage(self, metrics: ResourceMetrics) -> Optional[OptimizationResult]:
        """メモリ使用量最適化"""
        try:
            if metrics.memory_percent > self.performance_target.max_memory_percent:
                start_time = time.time()
                old_cache_size = len(self.execution_pool.result_cache)
                
                # キャッシュクリア
                old_cache = self.execution_pool.result_cache.copy()
                self.execution_pool.result_cache.clear()
                
                # ガベージコレクション強制実行
                import gc
                gc.collect()
                
                execution_time = time.time() - start_time
                new_cache_size = len(self.execution_pool.result_cache)
                
                improvement = ((old_cache_size - new_cache_size) / old_cache_size) * 100 if old_cache_size > 0 else 0
                
                return OptimizationResult(
                    strategy=OptimizationStrategy.MEMORY_OPTIMIZE,
                    old_value=old_cache_size,
                    new_value=new_cache_size,
                    improvement_percent=improvement,
                    execution_time=execution_time,
                    metadata={
                        "memory_percent": metrics.memory_percent,
                        "cache_cleared": True
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {str(e)}")
            return None


class PerformanceOptimizer:
    """包括的パフォーマンス最適化システム"""
    
    def __init__(self):
        self.resource_monitor = ResourceMonitor()
        self.execution_pool = ClaudeCLIExecutionPool()
        self.dynamic_scaler = DynamicScaler(self.resource_monitor, self.execution_pool)
        
        # 最適化履歴
        self.optimization_history: List[OptimizationResult] = []
        
        # 自動最適化設定
        self.auto_optimization_enabled = True
        self.optimization_interval = 30.0  # 30秒間隔
        self.optimization_task: Optional[asyncio.Task] = None
        
        # パフォーマンス統計
        self.performance_stats = {
            "start_time": datetime.now(),
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "total_improvement_percent": 0.0
        }
    
    async def start_optimization(self):
        """最適化開始"""
        try:
            await self.resource_monitor.start_monitoring()
            
            if self.auto_optimization_enabled:
                self.optimization_task = asyncio.create_task(self._optimization_loop())
            
            logger.info("Performance optimization started")
            
        except Exception as e:
            logger.error(f"Failed to start optimization: {str(e)}")
    
    async def stop_optimization(self):
        """最適化停止"""
        try:
            await self.resource_monitor.stop_monitoring()
            
            if self.optimization_task:
                self.optimization_task.cancel()
                try:
                    await self.optimization_task
                except asyncio.CancelledError:
                    pass
            
            await self.execution_pool.cleanup()
            
            logger.info("Performance optimization stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop optimization: {str(e)}")
    
    async def _optimization_loop(self):
        """最適化ループ"""
        try:
            while self.auto_optimization_enabled:
                optimizations = await self.dynamic_scaler.auto_scale()
                
                for optimization in optimizations:
                    self.optimization_history.append(optimization)
                    self._update_performance_stats(optimization)
                    
                    logger.info(f"Optimization applied: {optimization.strategy.value} "
                              f"({optimization.improvement_percent:.1f}% improvement)")
                
                await asyncio.sleep(self.optimization_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Optimization loop error: {str(e)}")
    
    def _update_performance_stats(self, optimization: OptimizationResult):
        """パフォーマンス統計更新"""
        self.performance_stats["total_optimizations"] += 1
        
        if optimization.improvement_percent > 0:
            self.performance_stats["successful_optimizations"] += 1
            self.performance_stats["total_improvement_percent"] += optimization.improvement_percent
    
    async def execute_claude_cli_optimized(
        self, 
        prompt: str, 
        model: str = "claude-sonnet-4-20250514",
        cache_key: Optional[str] = None,
        priority: int = 1
    ) -> str:
        """最適化されたClaude CLI実行"""
        return await self.execution_pool.execute_claude_cli(prompt, model, cache_key, priority)
    
    async def process_issues_batch_optimized(self, issues: List[Any]) -> List[Dict[str, Any]]:
        """最適化されたバッチ処理"""
        try:
            # 動的並列度調整
            current_metrics = self.resource_monitor.get_current_metrics()
            if current_metrics:
                # CPU使用率に基づいて並列度を調整
                if current_metrics.cpu_percent < 50:
                    max_concurrent = min(len(issues), self.execution_pool.current_workers * 2)
                elif current_metrics.cpu_percent < 70:
                    max_concurrent = self.execution_pool.current_workers
                else:
                    max_concurrent = max(1, self.execution_pool.current_workers // 2)
            else:
                max_concurrent = self.execution_pool.current_workers
            
            # セマフォで並列度制御
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_single_issue(issue):
                async with semaphore:
                    # Issue処理の実装（モック）
                    await asyncio.sleep(0.1)  # 処理時間シミュレート
                    return {
                        "issue_number": getattr(issue, 'number', 0),
                        "status": "processed",
                        "processing_time": 0.1
                    }
            
            # バッチ実行
            tasks = [asyncio.create_task(process_single_issue(issue)) for issue in issues]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 例外を結果に変換
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "issue_number": getattr(issues[i], 'number', i),
                        "status": "error",
                        "error": str(result)
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            return []
    
    def get_performance_report(self) -> Dict[str, Any]:
        """パフォーマンスレポート取得"""
        current_metrics = self.resource_monitor.get_current_metrics()
        avg_metrics = self.resource_monitor.get_average_metrics(10)
        pool_stats = self.execution_pool.get_pool_stats()
        
        uptime = datetime.now() - self.performance_stats["start_time"]
        
        report = {
            "uptime_seconds": uptime.total_seconds(),
            "current_metrics": current_metrics.__dict__ if current_metrics else None,
            "average_metrics": avg_metrics.__dict__ if avg_metrics else None,
            "execution_pool_stats": pool_stats,
            "optimization_stats": self.performance_stats.copy(),
            "recent_optimizations": [
                {
                    "strategy": opt.strategy.value,
                    "improvement_percent": opt.improvement_percent,
                    "execution_time": opt.execution_time
                }
                for opt in self.optimization_history[-10:]  # 最近10件
            ]
        }
        
        # 成功率計算
        total_opts = self.performance_stats["total_optimizations"]
        if total_opts > 0:
            report["optimization_success_rate"] = (
                self.performance_stats["successful_optimizations"] / total_opts
            )
            report["average_improvement_percent"] = (
                self.performance_stats["total_improvement_percent"] / 
                self.performance_stats["successful_optimizations"]
                if self.performance_stats["successful_optimizations"] > 0 else 0
            )
        
        return report
    
    async def manual_optimization(self, strategy: OptimizationStrategy) -> OptimizationResult:
        """手動最適化実行"""
        try:
            start_time = time.time()
            
            if strategy == OptimizationStrategy.SCALE_UP:
                old_workers = self.execution_pool.current_workers
                new_workers = min(old_workers + 1, self.execution_pool.max_workers)
                success = await self.execution_pool.scale_workers(new_workers)
                
                if success:
                    return OptimizationResult(
                        strategy=strategy,
                        old_value=old_workers,
                        new_value=new_workers,
                        improvement_percent=((new_workers - old_workers) / old_workers) * 100,
                        execution_time=time.time() - start_time,
                        metadata={"manual": True}
                    )
            
            elif strategy == OptimizationStrategy.CACHE_OPTIMIZE:
                old_cache_size = len(self.execution_pool.result_cache)
                self.execution_pool.result_cache.clear()
                
                return OptimizationResult(
                    strategy=strategy,
                    old_value=old_cache_size,
                    new_value=0,
                    improvement_percent=100.0 if old_cache_size > 0 else 0.0,
                    execution_time=time.time() - start_time,
                    metadata={"manual": True}
                )
            
            # その他の戦略...
            raise NotImplementedError(f"Manual optimization for {strategy.value} not implemented")
            
        except Exception as e:
            logger.error(f"Manual optimization failed: {str(e)}")
            raise


# シングルトンインスタンス
_performance_optimizer = None

def get_performance_optimizer() -> PerformanceOptimizer:
    """パフォーマンス最適化システムシングルトン取得"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer