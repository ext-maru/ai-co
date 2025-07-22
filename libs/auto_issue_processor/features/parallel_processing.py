#!/usr/bin/env python3
"""
並列処理機能
複数のIssueを効率的に並列処理
"""

import asyncio
import logging
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
import psutil
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from github.Issue import Issue

from ..core.config import ProcessorConfig

logger = logging.getLogger(__name__)


class WorkerPool:
    """ワーカープール管理"""
    
    def __init__(self, max_workers: int, name: str = "worker"):
        self.max_workers = max_workers
        self.name = name
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[str] = []
        self._lock = asyncio.Lock()
    
    async def submit(self, task_id: str, coro):
        """タスクを送信"""
        async with self._lock:
            if len(self.active_tasks) >= self.max_workers:
                # 完了したタスクをクリーンアップ
                await self._cleanup_completed()
                
                # まだ満杯の場合は待機
                while len(self.active_tasks) >= self.max_workers:
                    await asyncio.sleep(0.1)
                    await self._cleanup_completed()
            
            # タスクを作成
            task = asyncio.create_task(coro)
            self.active_tasks[task_id] = task
            logger.debug(f"{self.name} pool: submitted task {task_id}")
    
    async def wait_all(self) -> List[Any]:
        """すべてのタスクの完了を待つ"""
        if not self.active_tasks:
            return []
        
        tasks = list(self.active_tasks.values())
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        async with self._lock:
            self.active_tasks.clear()
        
        return results
    
    async def _cleanup_completed(self):
        """完了したタスクをクリーンアップ"""
        completed = []
        for task_id, task in self.active_tasks.items():
            if task.done():
                completed.append(task_id)
        
        for task_id in completed:
            del self.active_tasks[task_id]
            self.completed_tasks.append(task_id)
    
    def get_status(self) -> Dict[str, Any]:
        """ステータスを取得"""
        return {
            "active": len(self.active_tasks),
            "completed": len(self.completed_tasks),
            "max_workers": self.max_workers
        }


class ResourceMonitor:
    """リソース監視"""
    
    def __init__(self):
        self.cpu_threshold = 80.0  # CPU使用率の閾値
        self.memory_threshold = 80.0  # メモリ使用率の閾値
        self.check_interval = 1.0  # チェック間隔（秒）
    
    async def get_resource_usage(self) -> Dict[str, float]:
        """現在のリソース使用状況を取得"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "available_memory_gb": psutil.virtual_memory().available / (1024**3)
        }
    
    async def is_resource_available(self) -> bool:
        """リソースが利用可能かチェック"""
        usage = await self.get_resource_usage()
        
        if usage["cpu_percent"] > self.cpu_threshold:
            logger.warning(f"CPU usage high: {usage['cpu_percent']:.1f}%")
            return False
        
        if usage["memory_percent"] > self.memory_threshold:
            logger.warning(f"Memory usage high: {usage['memory_percent']:.1f}%")
            return False
        
        return True
    
    async def wait_for_resources(self):
        """リソースが利用可能になるまで待機"""
        while not await self.is_resource_available():
            logger.info("Waiting for resources to become available...")
            await asyncio.sleep(self.check_interval)


class ParallelProcessor:
    """並列処理エンジン"""
    
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.max_workers = config.processing.max_parallel_workers
        self.batch_size = config.processing.parallel_batch_size
        
        # ワーカープール
        self.worker_pool = WorkerPool(self.max_workers, "issue_processor")
        
        # リソースモニター
        self.resource_monitor = ResourceMonitor()
        
        # 処理統計
        self.stats = {
            "total_processed": 0,
            "batch_count": 0,
            "average_time_per_issue": 0.0,
            "peak_memory_usage": 0.0
        }
    
    async def process_batch(
        self,
        issues: List[Issue],
        process_func: Callable[[Issue], Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Issueのバッチを並列処理"""
        logger.info(f"Starting parallel processing of {len(issues)} issues")
        start_time = datetime.now()
        
        # リソースチェック
        await self.resource_monitor.wait_for_resources()
        
        # バッチに分割
        batches = self._create_batches(issues)
        all_results = []
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} issues)")
            
            # バッチ内の並列処理
            batch_results = await self._process_batch_parallel(batch, process_func)
            all_results.extend(batch_results)
            
            # バッチ間でリソースチェック
            if batch_idx < len(batches) - 1:
                await self.resource_monitor.wait_for_resources()
        
        # 統計更新
        elapsed = (datetime.now() - start_time).total_seconds()
        self.stats["total_processed"] += len(issues)
        self.stats["batch_count"] += len(batches)
        self.stats["average_time_per_issue"] = elapsed / len(issues) if issues else 0
        
        # リソース使用状況
        usage = await self.resource_monitor.get_resource_usage()
        self.stats["peak_memory_usage"] = max(
            self.stats["peak_memory_usage"],
            usage["memory_percent"]
        )
        
        logger.info(f"Parallel processing completed in {elapsed:.1f}s "
                   f"(avg: {self.stats['average_time_per_issue']:.1f}s per issue)")
        
        return all_results
    
    def _create_batches(self, issues: List[Issue]) -> List[List[Issue]]:
        """Issueをバッチに分割"""
        batches = []
        for i in range(0, len(issues), self.batch_size):
            batches.append(issues[i:i + self.batch_size])
        return batches
    
    async def _process_batch_parallel(
        self,
        batch: List[Issue],
        process_func: Callable[[Issue], Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """単一バッチを並列処理"""
        # 各Issueの処理タスクを作成
        for issue in batch:
            task_id = f"issue_{issue.number}"
            await self.worker_pool.submit(
                task_id,
                self._process_with_monitoring(issue, process_func)
            )
        
        # すべてのタスクの完了を待つ
        results = await self.worker_pool.wait_all()
        
        # エラーハンドリング
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing issue in batch: {result}")
                processed_results.append({
                    "issue_number": batch[i].number if i < len(batch) else None,
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _process_with_monitoring(
        self,
        issue: Issue,
        process_func: Callable[[Issue], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """リソース監視付きでIssueを処理"""
        start_time = datetime.now()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # 処理実行
            result = await process_func(issue)
            
            # メトリクス追加
            elapsed = (datetime.now() - start_time).total_seconds()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            result["_metrics"] = {
                "processing_time": elapsed,
                "memory_delta_mb": end_memory - start_memory,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing Issue #{issue.number}: {e}")
            raise
    
    async def optimize_worker_count(self) -> int:
        """最適なワーカー数を動的に決定"""
        cpu_count = multiprocessing.cpu_count()
        usage = await self.resource_monitor.get_resource_usage()
        
        # CPU使用率に基づいて調整
        if usage["cpu_percent"] > 70:
            optimal = max(1, self.max_workers - 1)
        elif usage["cpu_percent"] < 30:
            optimal = min(cpu_count, self.max_workers + 1)
        else:
            optimal = self.max_workers
        
        # メモリ制約も考慮
        if usage["memory_percent"] > 70:
            optimal = max(1, optimal - 1)
        
        logger.info(f"Optimal worker count: {optimal} (CPU: {usage['cpu_percent']:.1f}%, "
                   f"Memory: {usage['memory_percent']:.1f}%)")
        
        return optimal
    
    def get_statistics(self) -> Dict[str, Any]:
        """処理統計を取得"""
        return {
            **self.stats,
            "worker_pool_status": self.worker_pool.get_status(),
            "config": {
                "max_workers": self.max_workers,
                "batch_size": self.batch_size
            }
        }


class DependencyResolver:
    """Issue間の依存関係を解決"""
    
    def __init__(self):
        self.dependency_graph: Dict[int, List[int]] = {}
    
    def add_dependency(self, issue_num: int, depends_on: int):
        """依存関係を追加"""
        if issue_num not in self.dependency_graph:
            self.dependency_graph[issue_num] = []
        self.dependency_graph[issue_num].append(depends_on)
    
    def get_processing_order(self, issues: List[Issue]) -> List[List[Issue]]:
        """依存関係を考慮した処理順序を取得"""
        issue_map = {issue.number: issue for issue in issues}
        issue_numbers = set(issue.number for issue in issues)
        
        # 依存関係のないIssueを見つける
        independent = []
        dependent = []
        
        for issue in issues:
            deps = self.dependency_graph.get(issue.number, [])
            # 処理対象内の依存関係のみ考慮
            active_deps = [d for d in deps if d in issue_numbers]
            
            if not active_deps:
                independent.append(issue)
            else:
                dependent.append((issue, active_deps))
        
        # 処理順序を決定
        levels = [independent]
        processed = set(issue.number for issue in independent)
        
        # 依存関係を解決しながらレベル分け
        while dependent:
            next_level = []
            remaining = []
            
            for issue, deps in dependent:
                if all(d in processed for d in deps):
                    next_level.append(issue)
                else:
                    remaining.append((issue, deps))
            
            if not next_level:
                # 循環依存の可能性
                logger.warning("Circular dependency detected")
                next_level = [issue for issue, _ in remaining]
                remaining = []
            
            levels.append(next_level)
            processed.update(issue.number for issue in next_level)
            dependent = remaining
        
        return levels
    
    def detect_circular_dependencies(self) -> List[List[int]]:
        """循環依存を検出"""
        # TODO: 実装
        return []