#!/usr/bin/env python3
"""
Celery移行POC - OSS移行プロジェクト
既存のasync_worker_optimization.pyをCelery + Rayで置き換える
"""
from celery import Celery, Task, group, chain, chord
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from kombu import Queue
import redis
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import functools


# Celeryアプリケーション設定
app = Celery('ai_co_workers')
app.config_from_object({
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_track_started': True,
    'task_send_sent_event': True,
    'worker_pool_restarts': True,
    'worker_max_tasks_per_child': 1000,
    'task_time_limit': 300,  # 5分
    'task_soft_time_limit': 270,  # 4.5分
    'task_acks_late': True,
    'worker_prefetch_multiplier': 4,
})

# タスクルーティング設定
app.conf.task_routes = {
    'celery_migration_poc.process_item': {'queue': 'default'},
    'celery_migration_poc.batch_process': {'queue': 'batch'},
    'celery_migration_poc.heavy_computation': {'queue': 'heavy'},
}

# キュー設定
app.conf.task_queues = (
    Queue('default', routing_key='default'),
    Queue('batch', routing_key='batch'),
    Queue('heavy', routing_key='heavy'),
)

# ロガー
logger = get_task_logger(__name__)


# 既存の列挙型を保持（互換性のため）
class LoadLevel(Enum):
    """負荷レベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskItem:
    """タスクアイテム（簡略化版）"""
    id: str
    data: Any
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkerMetrics:
    """ワーカーメトリクス（簡略化版）"""
    tasks_processed: int = 0
    total_processing_time: float = 0.0
    errors_count: int = 0
    last_task_time: Optional[datetime] = None


# Celeryタスク定義
@app.task(bind=True, name='process_item')
def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
    """個別アイテムの処理"""
    try:
        # 処理開始
        start_time = time.time()
        logger.info(f"Processing item: {item.get('id')}")
        
        # 実際の処理（デモ用）
        result = {
            'id': item.get('id'),
            'processed': True,
            'timestamp': datetime.now().isoformat(),
            'worker_id': self.request.id
        }
        
        # 処理時間の記録
        processing_time = time.time() - start_time
        logger.info(f"Item {item.get('id')} processed in {processing_time:.2f}s")
        
        return result
    except Exception as e:
        logger.error(f"Error processing item {item.get('id')}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@app.task(name='batch_process')
def batch_process(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """バッチ処理タスク"""
    logger.info(f"Processing batch of {len(items)} items")
    
    # 各アイテムを個別タスクとして処理
    job = group(process_item.s(item) for item in items)
    result = job.apply_async()
    
    # 結果を収集
    return result.get(timeout=300)


@app.task(name='heavy_computation')
def heavy_computation(data: Dict[str, Any]) -> Dict[str, Any]:
    """重い計算処理タスク"""
    logger.info(f"Starting heavy computation for {data.get('id')}")
    
    # 重い処理のシミュレーション
    import time
    time.sleep(2)
    
    return {
        'id': data.get('id'),
        'result': 'computed',
        'timestamp': datetime.now().isoformat()
    }


class CeleryWorkerOptimizer:
    """Celeryベースのワーカー最適化器"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.metrics = defaultdict(WorkerMetrics)
        
    async def optimize_batch_processing(self, items: List[Any], 
                                      batch_size: int = 10, 
                                      max_concurrent: int = 5) -> List[Any]:
        """バッチ処理の最適化（Celery版）"""
        results = []
        
        # バッチに分割
        batches = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batches.append(batch)
        
        # Celeryのグループタスクとして実行
        job = group(batch_process.s(batch) for batch in batches)
        result = job.apply_async()
        
        # 結果を取得
        batch_results = result.get(timeout=300)
        
        # 結果をフラット化
        for batch_result in batch_results:
            results.extend(batch_result)
        
        return results
    
    def setup_pipeline(self, stages: List[str]) -> 'chain':
        """パイプラインのセットアップ（Celery chain）"""
        # タスク名からCeleryタスクを取得
        tasks = []
        for stage in stages:
            task = app.tasks.get(stage)
            if task:
                tasks.append(task.s())
        
        # Celeryのchainを作成
        return chain(*tasks)
    
    def create_resource_pool(self, name: str, size: int = 10) -> None:
        """リソースプールの作成（Redis使用）"""
        # Redisにリソースプール情報を保存
        pool_key = f"resource_pool:{name}"
        self.redis_client.hset(pool_key, "size", size)
        self.redis_client.hset(pool_key, "available", size)
        self.redis_client.hset(pool_key, "created_at", datetime.now().isoformat())
        
    def get_worker_metrics(self) -> Dict[str, Any]:
        """ワーカーメトリクスの取得"""
        # Celeryの統計情報を取得
        stats = app.control.inspect().stats()
        active = app.control.inspect().active()
        
        metrics = {
            "workers": stats,
            "active_tasks": active,
            "queue_lengths": self._get_queue_lengths(),
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
    
    def _get_queue_lengths(self) -> Dict[str, int]:
        """キューの長さを取得"""
        lengths = {}
        for queue_name in ['default', 'batch', 'heavy']:
            key = f"celery-queue-{queue_name}"
            length = self.redis_client.llen(key)
            lengths[queue_name] = length
        return lengths
    
    def dynamic_load_balancing(self, load_level: LoadLevel) -> Dict[str, Any]:
        """動的負荷分散（Celeryのワーカー制御）"""
        config = {
            LoadLevel.LOW: {"concurrency": 2, "prefetch": 1},
            LoadLevel.MEDIUM: {"concurrency": 4, "prefetch": 2},
            LoadLevel.HIGH: {"concurrency": 8, "prefetch": 4},
            LoadLevel.CRITICAL: {"concurrency": 16, "prefetch": 8}
        }
        
        settings = config.get(load_level, config[LoadLevel.MEDIUM])
        
        # Celeryワーカーの設定を動的に変更
        app.control.pool_grow(n=settings["concurrency"])
        app.conf.worker_prefetch_multiplier = settings["prefetch"]
        
        return {
            "load_level": load_level.value,
            "settings": settings,
            "applied_at": datetime.now().isoformat()
        }


# 既存APIとの互換性レイヤー
class AsyncWorkerOptimizationCompat:
    """既存のasync_worker_optimizationとの互換性レイヤー"""
    
    def __init__(self):
        self.celery_optimizer = CeleryWorkerOptimizer()
        
    async def optimize_batch_processing(self, items: List[Any], task_func: Callable,
                                      batch_size: int = 10, max_concurrent: int = 5) -> List[Any]:
        """既存APIとの互換性メソッド"""
        # task_funcは使用せず、Celeryタスクを使用
        return await self.celery_optimizer.optimize_batch_processing(
            items, batch_size, max_concurrent
        )
    
    def setup_pipeline(self, stages: List[Callable]) -> Any:
        """パイプライン互換性"""
        # Callableからタスク名を推定（デモ用）
        stage_names = ["process_item" for _ in stages]
        return self.celery_optimizer.setup_pipeline(stage_names)
    
    def create_resource_pool(self, name: str, size: int = 10) -> Any:
        """リソースプール互換性"""
        return self.celery_optimizer.create_resource_pool(name, size)


# Celeryビート（定期タスク）設定
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-old-results': {
        'task': 'celery_migration_poc.cleanup_old_results',
        'schedule': crontab(hour=2, minute=0),  # 毎日午前2時
    },
    'collect-metrics': {
        'task': 'celery_migration_poc.collect_metrics',
        'schedule': 60.0,  # 60秒ごと
    },
}


@app.task(name='cleanup_old_results')
def cleanup_old_results():
    """古い結果のクリーンアップ"""
    logger.info("Cleaning up old results...")
    # 実装は省略
    return {"cleaned": 0}


@app.task(name='collect_metrics')
def collect_metrics():
    """メトリクスの収集"""
    optimizer = CeleryWorkerOptimizer()
    metrics = optimizer.get_worker_metrics()
    logger.info(f"Collected metrics: {metrics}")
    return metrics


# デモ用ヘルパー関数
def demo_celery_usage():
    """Celeryの使用例"""
    # 単一タスクの実行
    result = process_item.delay({'id': 'test-1', 'data': 'sample'})
    print(f"Task ID: {result.id}")
    print(f"Result: {result.get(timeout=10)}")
    
    # バッチ処理
    items = [{'id': f'item-{i}', 'data': f'data-{i}'} for i in range(10)]
    batch_result = batch_process.delay(items)
    print(f"Batch result: {batch_result.get(timeout=30)}")
    
    # パイプライン（チェーン）
    pipeline = chain(
        process_item.s({'id': 'pipe-1', 'data': 'test'}),
        heavy_computation.s()
    )
    pipeline_result = pipeline.apply_async()
    print(f"Pipeline result: {pipeline_result.get(timeout=30)}")


if __name__ == "__main__":
    # Celeryワーカーの起動コマンド：
    # celery -A celery_migration_poc worker --loglevel=info
    # celery -A celery_migration_poc beat --loglevel=info
    print("Celery migration POC ready")