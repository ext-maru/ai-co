#!/usr/bin/env python3
"""
Celery統合非同期ワーカーフレームワーク - OSS移行版
既存のasync_worker_optimization.pyをCeleryで置き換え
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable

from celery import Celery, Task
from celery.result import AsyncResult
from celery.signals import task_prerun, task_postrun, task_failure
from kombu import Queue
import redis


class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class WorkerStatus(Enum):
    """ワーカーステータス"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class TaskResult:
    """タスク結果"""
    task_id: str
    status: TaskStatus
    result: Any = None
    traceback: Optional[str] = None
    execution_time: float = 0.0
    worker_name: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


@dataclass
class WorkerMetrics:
    """ワーカーメトリクス"""
    worker_name: str
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_execution_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)


class CeleryIntegrationFramework:
    """Celery統合フレームワーク"""
    
    def __init__(self, 
                 app_name: str = "elder_workers",
                 broker_url: str = "redis://localhost:6379/0",
                 result_backend: str = "redis://localhost:6379/0"):
        
        self.app_name = app_name
        self.broker_url = broker_url
        self.result_backend = result_backend
        self.logger = logging.getLogger(f"celery_framework.{app_name}")
        
        # Celeryアプリ初期化
        self.celery_app = Celery(
            app_name,
            broker=broker_url,
            backend=result_backend
        )
        
        # 設定
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='Asia/Tokyo',
            enable_utc=True,
            task_routes={
                'elder_workers.high_priority': {'queue': 'high_priority'},
                'elder_workers.normal': {'queue': 'normal'},
                'elder_workers.low_priority': {'queue': 'low_priority'},
            },
            task_default_queue='normal',
            task_queues=[
                Queue('high_priority', routing_key='high_priority'),
                Queue('normal', routing_key='normal'),
                Queue('low_priority', routing_key='low_priority'),
            ],
            worker_prefetch_multiplier=4,
            task_acks_late=True,
            worker_disable_rate_limits=False,
            task_compression='gzip',
            result_compression='gzip',
        )
        
        # メトリクス記録
        self.task_results = {}
        self.worker_metrics = {}
        self.performance_stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_execution_time': 0.0
        }
        
        # シグナルハンドラー設定
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Celeryシグナルハンドラー設定"""
        
        @task_prerun.connect
        def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
            self.logger.info(f"Task {task_id} starting: {task.name}")
            self.task_results[task_id] = TaskResult(
                task_id=task_id,
                status=TaskStatus.STARTED
            )
        
        @task_postrun.connect
        def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kw):
            if task_id in self.task_results:
                self.task_results[task_id].status = TaskStatus(state)
                self.task_results[task_id].result = retval
                self.task_results[task_id].completed_at = time.time()
                
                # 実行時間計算
                if self.task_results[task_id].created_at:
                    execution_time = self.task_results[task_id].completed_at - self.task_results[task_id].created_at
                    self.task_results[task_id].execution_time = execution_time
                
                self.logger.info(f"Task {task_id} completed: {state}")
                
                # 統計更新
                self._update_performance_stats(task_id, state)
        
        @task_failure.connect
        def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kw):
            if task_id in self.task_results:
                self.task_results[task_id].status = TaskStatus.FAILURE
                self.task_results[task_id].traceback = str(traceback)
                self.task_results[task_id].completed_at = time.time()
                
            self.logger.error(f"Task {task_id} failed: {exception}")
    
    def _update_performance_stats(self, task_id: str, state: str):
        """パフォーマンス統計更新"""
        self.performance_stats['total_tasks'] += 1
        
        if state == 'SUCCESS':
            self.performance_stats['successful_tasks'] += 1
        elif state == 'FAILURE':
            self.performance_stats['failed_tasks'] += 1
        
        # 平均実行時間更新
        if task_id in self.task_results:
            execution_time = self.task_results[task_id].execution_time
            current_avg = self.performance_stats['average_execution_time']
            total_tasks = self.performance_stats['total_tasks']
            
            new_avg = ((current_avg * (total_tasks - 1)) + execution_time) / total_tasks
            self.performance_stats['average_execution_time'] = new_avg
    
    def create_task(self, 
                   func: Callable,
                   name: Optional[str] = None,
                   queue: str = 'normal',
                   priority: int = 5,
                   retry_limit: int = 3) -> Task:
        """Celeryタスク作成"""
        
        task_name = name or f"{func.__module__}.{func.__name__}"
        
        @self.celery_app.task(
            name=task_name,
            bind=True,
            max_retries=retry_limit,
            default_retry_delay=60,
            queue=queue
        )
        def celery_task(self, *args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                self.logger.error(f"Task {self.request.id} error: {exc}")
                # リトライ機能
                if self.request.retries < retry_limit:
                    raise self.retry(countdown=60 * (2 ** self.request.retries))
                raise exc
        
        return celery_task
    
    def submit_task(self, 
                   task: Union[Task, str],
                   args: tuple = (),
                   kwargs: dict = None,
                   queue: str = 'normal',
                   countdown: int = 0,
                   eta: Optional[float] = None) -> str:
        """タスク投入"""
        if kwargs is None:
            kwargs = {}
        
        if isinstance(task, str):
            # タスク名で投入
            result = self.celery_app.send_task(
                task,
                args=args,
                kwargs=kwargs,
                queue=queue,
                countdown=countdown,
                eta=eta
            )
        else:
            # Taskオブジェクトで投入
            result = task.apply_async(
                args=args,
                kwargs=kwargs,
                queue=queue,
                countdown=countdown,
                eta=eta
            )
        
        self.logger.info(f"Submitted task {result.id} to queue {queue}")
        return result.id
    
    def get_task_result(self, task_id: str) -> TaskResult:
        """タスク結果取得"""
        if task_id in self.task_results:
            return self.task_results[task_id]
        
        # Celeryから結果取得
        async_result = AsyncResult(task_id, app=self.celery_app)
        
        return TaskResult(
            task_id=task_id,
            status=TaskStatus(async_result.status),
            result=async_result.result if async_result.successful() else None,
            traceback=str(async_result.traceback) if async_result.failed() else None
        )
    
    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """タスク完了待機"""
        async_result = AsyncResult(task_id, app=self.celery_app)
        
        try:
            result = async_result.get(timeout=timeout)
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.SUCCESS,
                result=result
            )
        except Exception as e:
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILURE,
                traceback=str(e)
            )
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """ワーカー統計取得"""
        # Celeryワーカー情報取得
        inspect = self.celery_app.control.inspect()
        
        stats = {
            'active_workers': 0,
            'total_tasks': self.performance_stats['total_tasks'],
            'successful_tasks': self.performance_stats['successful_tasks'],
            'failed_tasks': self.performance_stats['failed_tasks'],
            'success_rate': 0.0,
            'average_execution_time': self.performance_stats['average_execution_time'],
            'workers': {}
        }
        
        # 成功率計算
        if self.performance_stats['total_tasks'] > 0:
            stats['success_rate'] = (
                self.performance_stats['successful_tasks'] / 
                self.performance_stats['total_tasks'] * 100
            )
        
        # ワーカー情報
        if inspect:
            try:
                active_workers = inspect.active()
                if active_workers:
                    stats['active_workers'] = len(active_workers)
                    stats['workers'] = active_workers
            except Exception as e:
                self.logger.warning(f"Failed to get worker info: {e}")
        
        return stats
    
    def create_batch_processor(self, 
                              batch_size: int = 10,
                              max_parallel: int = 5) -> 'CeleryBatchProcessor':
        """バッチプロセッサー作成"""
        return CeleryBatchProcessor(self, batch_size, max_parallel)
    
    def shutdown(self):
        """フレームワークシャットダウン"""
        self.logger.info("Shutting down Celery framework")
        # ワーカー停止（必要に応じて）
        # self.celery_app.control.shutdown()


class CeleryBatchProcessor:
    """Celeryバッチプロセッサー"""
    
    def __init__(self, framework: CeleryIntegrationFramework, 
                 batch_size: int = 10, max_parallel: int = 5):
        self.framework = framework
        self.batch_size = batch_size
        self.max_parallel = max_parallel
        self.logger = logging.getLogger("celery_batch_processor")
    
    def process_batch(self, 
                     task: Task,
                     items: List[Any],
                     queue: str = 'normal') -> List[str]:
        """バッチ処理実行"""
        task_ids = []
        
        # バッチ分割
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # バッチタスク投入
            task_id = self.framework.submit_task(
                task,
                args=(batch,),
                queue=queue
            )
            task_ids.append(task_id)
            
            self.logger.info(f"Submitted batch {i//self.batch_size + 1} with {len(batch)} items")
        
        return task_ids
    
    def wait_for_batch(self, task_ids: List[str], 
                      timeout: Optional[float] = None) -> List[TaskResult]:
        """バッチ完了待機"""
        results = []
        
        for task_id in task_ids:
            result = self.framework.wait_for_task(task_id, timeout)
            results.append(result)
        
        return results


# サンプルタスク定義
def create_sample_tasks(framework: CeleryIntegrationFramework):
    """サンプルタスク作成"""
    
    @framework.celery_app.task(name='elder_workers.data_processing')
    def data_processing_task(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """データ処理タスク"""
        processed_count = 0
        errors = []
        
        for item in data:
            try:
                # データ処理ロジック（例）
                time.sleep(0.1)  # 処理時間シミュレート
                processed_count += 1
            except Exception as e:
                errors.append(str(e))
        
        return {
            'processed_count': processed_count,
            'errors': errors,
            'total_items': len(data)
        }
    
    @framework.celery_app.task(name='elder_workers.report_generation')
    def report_generation_task(report_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """レポート生成タスク"""
        # レポート生成ロジック（例）
        time.sleep(2)  # 重い処理をシミュレート
        
        return {
            'report_type': report_type,
            'generated_at': time.time(),
            'status': 'completed',
            'file_path': f'/tmp/report_{report_type}_{int(time.time())}.pdf'
        }
    
    return {
        'data_processing': data_processing_task,
        'report_generation': report_generation_task
    }


# Celery起動用関数
def create_celery_app(config: Optional[Dict[str, Any]] = None) -> Celery:
    """Celeryアプリ作成"""
    framework = CeleryIntegrationFramework()
    
    if config:
        framework.celery_app.conf.update(config)
    
    # サンプルタスク登録
    create_sample_tasks(framework)
    
    return framework.celery_app


if __name__ == "__main__":
    # 設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # フレームワーク初期化
    framework = CeleryIntegrationFramework()
    
    # サンプルタスク作成
    tasks = create_sample_tasks(framework)
    
    # テスト実行例
    print("Celery Integration Framework initialized")
    print(f"Available tasks: {list(tasks.keys())}")
    print("Start workers with: celery -A libs.celery_integration_framework worker --loglevel=info")
