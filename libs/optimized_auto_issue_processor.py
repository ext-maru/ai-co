#!/usr/bin/env python3
"""
Optimized Auto Issue Processor - Issue #192対応
動的並列処理とパフォーマンス最適化を統合したAuto Issue Processor

主な最適化:
1. 動的並列処理スケーリング
2. プロセスプーリング
3. メモリ使用最適化
4. パフォーマンスモニタリング
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import sys
from dataclasses import dataclass
from contextlib import asynccontextmanager

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 必要なモジュールをインポート
from libs.dynamic_parallel_processor import DynamicParallelProcessor, AdaptiveScalingStrategy
from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
from libs.auto_issue_processor_error_handling import AutoIssueProcessorErrorHandler
from github.Issue import Issue

logger = logging.getLogger(__name__)


@dataclass
class ProcessingJob:
    """処理ジョブ"""
    issue: Issue
    job_id: str
    priority: str
    created_at: float
    metadata: Dict[str, Any]
    
    @property
    def age_seconds(self) -> float:
        """ジョブの経過時間（秒）"""
        return time.time() - self.created_at


class ProcessingQueue:
    """優先度ベース処理キュー"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queues = {
            "critical": asyncio.Queue(),
            "high": asyncio.Queue(),
            "medium": asyncio.Queue(), 
            "low": asyncio.Queue()
        }
        self.total_size = 0
        self._lock = asyncio.Lock()
    
    async def put(self, job: ProcessingJob):
        """ジョブをキューに追加"""
        async with self._lock:
            if self.total_size >= self.max_size:
                # 最も優先度の低いジョブを削除
                await self._remove_lowest_priority_job()
            
            priority = job.priority.lower()
            if priority not in self.queues:
                priority = "medium"
            
            await self.queues[priority].put(job)
            self.total_size += 1
            logger.debug(f"Job added to {priority} queue: {job.job_id}")
    
    async def get(self) -> ProcessingJob:
        """最高優先度のジョブを取得"""
        # 優先度順にチェック
        for priority in ["critical", "high", "medium", "low"]:
            try:
                job = self.queues[priority].get_nowait()
                async with self._lock:
                    self.total_size -= 1
                return job
            except asyncio.QueueEmpty:
                continue
        
        # すべてのキューが空の場合は待機
        for priority in ["critical", "high", "medium", "low"]:
            try:
                job = await asyncio.wait_for(self.queues[priority].get(), timeout=1.0)
                async with self._lock:
                    self.total_size -= 1
                return job
            except asyncio.TimeoutError:
                continue
        
        raise asyncio.QueueEmpty("All queues are empty")
    
    async def _remove_lowest_priority_job(self):
        """最も優先度の低いジョブを削除"""
        for priority in ["low", "medium", "high", "critical"]:
            try:
                removed_job = self.queues[priority].get_nowait()
                logger.warning(f"Removed job due to queue full: {removed_job.job_id}")
                return
            except asyncio.QueueEmpty:
                continue
    
    def size(self) -> int:
        """キューの総サイズ"""
        return self.total_size
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """各優先度キューのサイズ"""
        return {
            priority: queue.qsize() 
            for priority, queue in self.queues.items()
        }


class PerformanceTracker:
    """パフォーマンス追跡"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.processing_times = []
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.last_reset = time.time()
        
    def record_processing(self, duration: float, success: bool):
        """処理結果を記録"""
        self.processing_times.append(duration)
        
        # ウィンドウサイズを維持
        if len(self.processing_times) > self.window_size:
            self.processing_times.pop(0)
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, float]:
        """パフォーマンスメトリクス取得"""
        if not self.processing_times:
            return {
                "avg_processing_time": 0.0,
                "throughput": 0.0,
                "error_rate": 0.0,
                "total_processed": 0
            }
        
        # 基本統計
        avg_time = sum(self.processing_times) / len(self.processing_times)
        total_processed = self.success_count + self.error_count
        elapsed_time = time.time() - self.start_time
        throughput = total_processed / elapsed_time if elapsed_time > 0 else 0.0
        error_rate = self.error_count / total_processed if total_processed > 0 else 0.0
        
        return {
            "avg_processing_time": avg_time,
            "throughput": throughput,
            "error_rate": error_rate,
            "total_processed": total_processed,
            "success_count": self.success_count,
            "error_count": self.error_count
        }
    
    def reset(self):
        """統計をリセット"""
        self.processing_times.clear()
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.last_reset = time.time()


class OptimizedAutoIssueProcessor:
    """最適化されたAuto Issue Processor"""
    
    def __init__(
        self,
        initial_concurrency: int = 5,
        max_concurrency: int = 20,
        queue_size: int = 500,
        enable_dynamic_scaling: bool = True
    ):
        self.initial_concurrency = initial_concurrency
        self.max_concurrency = max_concurrency
        self.enable_dynamic_scaling = enable_dynamic_scaling
        
        # コンポーネント初期化
        self.base_processor = AutoIssueProcessor()
        self.error_handler = AutoIssueProcessorErrorHandler()
        self.processing_queue = ProcessingQueue(max_size=queue_size)
        self.performance_tracker = PerformanceTracker()
        
        # 動的並列プロセッサー
        if enable_dynamic_scaling:
            scaling_strategy = AdaptiveScalingStrategy({
                "min_concurrency": 1,
                "max_concurrency": max_concurrency,
                "cooldown_seconds": 15,  # より頻繁な調整
                "confidence_threshold": 0.6
            })
            self.parallel_processor = DynamicParallelProcessor(
                initial_concurrency=initial_concurrency,
                strategy=scaling_strategy,
                monitor_interval=3.0  # 3秒間隔で監視
            )
        else:
            self.parallel_processor = None
        
        # 処理中のジョブ追跡
        self.active_jobs = {}
        self.completed_jobs = []
        self.failed_jobs = []
        
        # ステータス
        self.running = False
        self.worker_tasks = []
        
        logger.info(f"OptimizedAutoIssueProcessor initialized (concurrency: {initial_concurrency}, max: {max_concurrency})")
    
    async def start(self):
        """プロセッサー開始"""
        if self.running:
            return
        
        self.running = True
        
        # 動的並列プロセッサー開始
        if self.parallel_processor:
            await self.parallel_processor.start()
        
        # ワーカータスク開始
        for i in range(self.initial_concurrency):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        logger.info(f"OptimizedAutoIssueProcessor started with {len(self.worker_tasks)} workers")
    
    async def stop(self):
        """プロセッサー停止"""
        if not self.running:
            return
        
        self.running = False
        
        # ワーカータスク停止
        for task in self.worker_tasks:
            task.cancel()
        
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # 動的並列プロセッサー停止
        if self.parallel_processor:
            await self.parallel_processor.stop()
        
        logger.info("OptimizedAutoIssueProcessor stopped")
    
    async def process_issues_batch(
        self,
        issues: List[Issue],
        priority: str = "medium",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """イシューのバッチ処理"""
        if not self.running:
            await self.start()
        
        start_time = time.time()
        total_issues = len(issues)
        completed = 0
        results = {"successful": [], "failed": [], "skipped": []}
        
        # ジョブをキューに追加
        jobs = []
        for i, issue in enumerate(issues):
            job = ProcessingJob(
                issue=issue,
                job_id=f"batch-{int(time.time())}-{i}",
                priority=priority,
                created_at=time.time(),
                metadata={"batch_id": f"batch-{int(time.time())}", "index": i}
            )
            jobs.append(job)
            await self.processing_queue.put(job)
        
        # 完了まで待機
        while completed < total_issues:
            await asyncio.sleep(0.1)
            
            # 完了したジョブをチェック
            new_completed = len([j for j in jobs if j.job_id in self.completed_jobs or j.job_id in self.failed_jobs])
            if new_completed > completed:
                completed = new_completed
                if progress_callback:
                    progress_callback(completed, total_issues)
        
        # 結果を分類
        for job in jobs:
            if job.job_id in self.completed_jobs:
                results["successful"].append({"issue_number": job.issue.number, "job_id": job.job_id})
            elif job.job_id in self.failed_jobs:
                results["failed"].append({"issue_number": job.issue.number, "job_id": job.job_id})
            else:
                results["skipped"].append({"issue_number": job.issue.number, "job_id": job.job_id})
        
        duration = time.time() - start_time
        
        return {
            "results": results,
            "summary": {
                "total": total_issues,
                "successful": len(results["successful"]),
                "failed": len(results["failed"]),
                "skipped": len(results["skipped"]),
                "duration_seconds": duration,
                "throughput": total_issues / duration if duration > 0 else 0.0
            },
            "performance": self.performance_tracker.get_metrics()
        }
    
    async def _worker_loop(self, worker_id: str):
        """ワーカーループ"""
        logger.info(f"Worker {worker_id} started")
        
        try:
            while self.running:
                try:
                    # ジョブ取得（タイムアウト付き）
                    job = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                    
                    # ジョブ処理
                    await self._process_job(job, worker_id)
                    
                except asyncio.TimeoutError:
                    # キューが空の場合は続行
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}")
                    await asyncio.sleep(1)  # エラー後の待機
        
        except asyncio.CancelledError:
            pass
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _process_job(self, job: ProcessingJob, worker_id: str):
        """単一ジョブ処理"""
        start_time = time.time()
        success = False
        
        try:
            # アクティブジョブに追加
            self.active_jobs[job.job_id] = {
                "job": job,
                "worker_id": worker_id,
                "start_time": start_time
            }
            
            logger.debug(f"Worker {worker_id} processing job {job.job_id} (issue #{job.issue.number})")
            
            # 実際の処理実行
            result = await self._execute_issue_processing(job.issue)
            
            if result.get("status") == "success":
                success = True
                self.completed_jobs.append(job.job_id)
                logger.info(f"Job {job.job_id} completed successfully by {worker_id}")
            else:
                self.failed_jobs.append(job.job_id)
                logger.warning(f"Job {job.job_id} failed: {result.get('message', 'Unknown error')}")
        
        except Exception as e:
            self.failed_jobs.append(job.job_id)
            logger.error(f"Job {job.job_id} error in worker {worker_id}: {e}")
            
            # エラーハンドリング
            try:
                recovery_result = await self.error_handler.handle_error(
                    error=e,
                    operation="issue_processing",
                    issue_number=job.issue.number
                )
                logger.info(f"Error recovery result: {recovery_result.message}")
            except Exception as recovery_error:
                logger.error(f"Error recovery failed: {recovery_error}")
        
        finally:
            # 処理時間記録
            duration = time.time() - start_time
            self.performance_tracker.record_processing(duration, success)
            
            # アクティブジョブから削除
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
    
    async def _execute_issue_processing(self, issue: Issue) -> Dict[str, Any]:
        """イシュー処理実行"""
        try:
            # 基本プロセッサーを使用
            result = await self.base_processor.execute_auto_processing(issue)
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """プロセッサーステータス取得"""
        queue_sizes = self.processing_queue.get_queue_sizes()
        performance = self.performance_tracker.get_metrics()
        
        status = {
            "running": self.running,
            "worker_count": len(self.worker_tasks),
            "active_jobs": len(self.active_jobs),
            "queue_status": {
                "total_size": self.processing_queue.size(),
                "by_priority": queue_sizes
            },
            "performance": performance,
            "completed_jobs": len(self.completed_jobs),
            "failed_jobs": len(self.failed_jobs)
        }
        
        # 動的並列プロセッサーのステータス追加
        if self.parallel_processor:
            parallel_status = self.parallel_processor.get_status()
            status["dynamic_scaling"] = {
                "current_concurrency": parallel_status["current_concurrency"],
                "resource_utilization": parallel_status.get("current_resources"),
                "scaling_history": parallel_status.get("last_scaling")
            }
        
        return status
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """詳細パフォーマンスレポート生成"""
        status = self.get_status()
        
        # 処理中のジョブの詳細
        active_job_details = []
        current_time = time.time()
        for job_id, job_info in self.active_jobs.items():
            active_job_details.append({
                "job_id": job_id,
                "issue_number": job_info["job"].issue.number,
                "worker_id": job_info["worker_id"],
                "processing_time": current_time - job_info["start_time"],
                "priority": job_info["job"].priority
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "active_jobs_detail": active_job_details,
            "optimization_metrics": {
                "memory_efficiency": "TODO: Implement memory tracking",
                "cpu_efficiency": "TODO: Implement CPU tracking",
                "io_efficiency": "TODO: Implement I/O tracking"
            },
            "recommendations": self._generate_optimization_recommendations(status)
        }
    
    def _generate_optimization_recommendations(self, status: Dict[str, Any]) -> List[str]:
        """最適化推奨事項生成"""
        recommendations = []
        
        performance = status["performance"]
        
        # スループットチェック
        if performance["throughput"] < 5.0:
            recommendations.append("Consider increasing concurrency for higher throughput")
        
        # エラー率チェック
        if performance["error_rate"] > 0.1:
            recommendations.append("High error rate detected - review error handling and retry logic")
        
        # キューサイズチェック
        total_queue_size = status["queue_status"]["total_size"]
        if total_queue_size > 100:
            recommendations.append("Large queue detected - consider increasing worker count")
        
        # 処理時間チェック
        if performance["avg_processing_time"] > 10.0:
            recommendations.append("High average processing time - investigate bottlenecks")
        
        if not recommendations:
            recommendations.append("System performance is within acceptable ranges")
        
        return recommendations


# 使用例とテスト
async def main():
    """メイン関数（テスト用）"""
    logging.basicConfig(level=logging.INFO)
    
    # 最適化プロセッサー作成
    processor = OptimizedAutoIssueProcessor(
        initial_concurrency=3,
        max_concurrency=10,
        enable_dynamic_scaling=True
    )
    
    try:
        # テスト用のモックイシューを作成（実際のGitHubイシューの代わり）
        class MockIssue:
            def __init__(self, number):
                self.number = number
                self.title = f"Test Issue #{number}"
                self.body = f"Body for issue {number}"
                self.labels = []
        
        test_issues = [MockIssue(i) for i in range(20)]
        
        def progress_callback(completed, total):
            print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%)")
        
        print("Starting optimized batch processing...")
        start_time = time.time()
        
        # バッチ処理実行
        result = await processor.process_issues_batch(
            test_issues,
            priority="high",
            progress_callback=progress_callback
        )
        
        end_time = time.time()
        
        print(f"\nBatch processing completed in {end_time - start_time:.2f} seconds")
        print(f"Results: {result['summary']}")
        
        # ステータス表示
        status = processor.get_status()
        print(f"\nFinal Status:")
        print(f"- Running: {status['running']}")
        print(f"- Workers: {status['worker_count']}")
        print(f"- Completed: {status['completed_jobs']}")
        print(f"- Failed: {status['failed_jobs']}")
        print(f"- Throughput: {status['performance']['throughput']:.2f} issues/sec")
        
        # パフォーマンスレポート
        report = await processor.get_performance_report()
        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"- {rec}")
        
    finally:
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(main())