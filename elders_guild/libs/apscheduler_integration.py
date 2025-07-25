#!/usr/bin/env python3
"""
APScheduler統合システム - エルダーズギルド
高度なスケジューリング機能とエルダーズギルドシステムの統合
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.job import Job

# from .env_manager import EnvManager  # osを直接使用


class ElderSchedulerConfig:
    """エルダーズギルド用スケジューラー設定"""
    
    def __init__(self):        
        """初期化メソッド"""
        # 基本設定
        self.timezone = os.getenv('SCHEDULER_TIMEZONE', 'Asia/Tokyo')
        self.max_workers = int(os.getenv('SCHEDULER_MAX_WORKERS', '20'))
        
        # Redis設定（オプション）
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB', '1'))
        
        # PostgreSQL設定（オプション）
        self.postgres_url = os.getenv('DATABASE_URL', 
            'postgresql://postgres:password@localhost:5432/ai_company')
        
        # ジョブストア設定
        self.use_redis = os.getenv('SCHEDULER_USE_REDIS', 'false').lower() == 'true'
        self.use_postgres = os.getenv(
            'SCHEDULER_USE_POSTGRES',
            'false').lower(
        ) == 'true'  # デフォルトはメモリ使用
        
        # ログ設定
        self.log_level = os.getenv('SCHEDULER_LOG_LEVEL', 'INFO')
        
    def get_jobstores(self) -> Dict[str, Any]:
        """ジョブストア設定を取得"""
        jobstores = {}
        
        # デフォルトはメモリジョブストア（MemoryJobStoreインスタンス）
        from apscheduler.jobstores.memory import MemoryJobStore
        jobstores['default'] = MemoryJobStore()
        
        if self.use_redis:
            try:
                jobstores['redis'] = RedisJobStore(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db
                )
            except Exception as e:
                logging.warning(f"Redis jobstore setup failed: {e}")
            
        if self.use_postgres:
            try:
                jobstores['postgres'] = SQLAlchemyJobStore(
                    url=self.postgres_url,
                    tablename='apscheduler_jobs'
                )
            except Exception as e:
                logging.warning(f"PostgreSQL jobstore setup failed: {e}")
        
        return jobstores
        
    def get_executors(self) -> Dict[str, Any]:
        """エグゼキューター設定を取得"""
        return {
            'default': ThreadPoolExecutor(max_workers=self.max_workers),
            'asyncio': AsyncIOExecutor(),
        }
        
    def get_job_defaults(self) -> Dict[str, Any]:
        """ジョブデフォルト設定を取得"""
        return {
            'coalesce': True,  # 同一ジョブの重複実行を防ぐ
            'max_instances': 3,  # 最大同時実行数
            'misfire_grace_time': 30,  # 実行遅延許容時間（秒）
        }


class ElderScheduler:
    """エルダーズギルド統合スケジューラー"""
    
    def __init__(self, scheduler_type: str = 'asyncio'):
        """
        Args:
            scheduler_type: 'asyncio', 'background', 'blocking'のいずれか
        """
        self.config = ElderSchedulerConfig()
        self.logger = logging.getLogger(__name__)
        
        # スケジューラー初期化
        self.scheduler = self._create_scheduler(scheduler_type)
        
        # イベントリスナー設定
        self._setup_event_listeners()
        
        # 4賢者システム統合用
        self.sage_callbacks: Dict[str, Callable] = {}
        
        # 統計情報
        self.job_stats = {
            'total_executed': 0,
            'total_errors': 0,
            'last_execution': None,
            'active_jobs': 0
        }
        
    def _create_scheduler(self, scheduler_type: str):
        """スケジューラーインスタンス作成"""
        config = {
            'jobstores': self.config.get_jobstores(),
            'executors': self.config.get_executors(),
            'job_defaults': self.config.get_job_defaults(),
            'timezone': self.config.timezone
        }
        
        if scheduler_type == 'asyncio':
            return AsyncIOScheduler(**config)
        elif scheduler_type == 'background':
            return BackgroundScheduler(**config)
        elif scheduler_type == 'blocking':
            return BlockingScheduler(**config)
        else:
            raise ValueError(f"Unsupported scheduler type: {scheduler_type}")
            
    def _setup_event_listeners(self):
        """イベントリスナー設定"""
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        
    def _job_executed(self, event):
        """ジョブ実行完了イベント"""
        self.job_stats['total_executed'] += 1
        self.job_stats['last_execution'] = datetime.now()
        self.logger.info(f"✅ Job executed: {event.job_id}")
        
        # 4賢者への通知
        if 'task_sage' in self.sage_callbacks:
            self.sage_callbacks['task_sage'](event)
            
    def _job_error(self, event):
        """ジョブエラーイベント"""
        self.job_stats['total_errors'] += 1
        self.logger.error(f"❌ Job error: {event.job_id} - {event.exception}")
        
        # インシデント賢者への通知
        if 'incident_sage' in self.sage_callbacks:
            self.sage_callbacks['incident_sage'](event)
            
    def start(self):
        """スケジューラー開始"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("🚀 Elder Scheduler started")
            
    def shutdown(self, wait: bool = True):
        """スケジューラー停止"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            self.logger.info("🛑 Elder Scheduler stopped")
            
    def add_job(self, 
                func: Callable,
                trigger: str,
                id: Optional[str] = None,
                name: Optional[str] = None,
                jobstore: str = 'default',
                executor: str = 'default',
                **trigger_args) -> Job:
        """ジョブ追加"""
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=id,
            name=name,
            jobstore=jobstore,
            executor=executor,
            **trigger_args
        )
        
        self.job_stats['active_jobs'] = len(self.scheduler.get_jobs())
        self.logger.info(f"📋 Job added: {job.id} ({name or 'Unnamed'})")
        
        return job
        
    def remove_job(self, job_id: str, jobstore: str = 'default'):
        """ジョブ削除"""
        self.scheduler.remove_job(job_id, jobstore)
        self.job_stats['active_jobs'] = len(self.scheduler.get_jobs())
        self.logger.info(f"🗑️ Job removed: {job_id}")
        
    def get_job(self, job_id: str, jobstore: str = 'default') -> Optional[Job]:
        """ジョブ取得"""
        return self.scheduler.get_job(job_id, jobstore)
        
    def get_jobs(self, jobstore: str = None) -> List[Job]:
        """全ジョブ取得"""
        return self.scheduler.get_jobs(jobstore)
        
    def pause_job(self, job_id: str, jobstore: str = 'default'):
        """ジョブ一時停止"""
        self.scheduler.pause_job(job_id, jobstore)
        self.logger.info(f"⏸️ Job paused: {job_id}")
        
    def resume_job(self, job_id: str, jobstore: str = 'default'):
        """ジョブ再開"""
        self.scheduler.resume_job(job_id, jobstore)
        self.logger.info(f"▶️ Job resumed: {job_id}")
        
    def modify_job(self, job_id: str, jobstore: str = 'default', **changes):
        """ジョブ変更"""
        job = self.scheduler.modify_job(job_id, jobstore, **changes)
        self.logger.info(f"✏️ Job modified: {job_id}")
        return job
        
    def reschedule_job(self, job_id: str, jobstore: str = 'default', 
                      trigger: str = None, **trigger_args):
        """ジョブ再スケジュール"""
        job = self.scheduler.reschedule_job(job_id, jobstore, trigger, **trigger_args)
        self.logger.info(f"🔄 Job rescheduled: {job_id}")
        return job


class ElderScheduleBuilder:
    """エルダーズギルド用スケジュール構築ヘルパー"""
    
    def __init__(self, scheduler: ElderScheduler):
        """初期化メソッド"""
        self.scheduler = scheduler
        
    def every(self, interval: int):
        """間隔スケジュール"""
        return IntervalBuilder(self.scheduler, interval)
        
    def daily_at(self, hour: int, minute: int = 0):
        """日次スケジュール"""
        return self.scheduler.add_job(
            trigger='cron',
            hour=hour,
            minute=minute
        )
        
    def weekly_on(self, day_of_week: int, hour: int, minute: int = 0):
        """週次スケジュール"""
        return self.scheduler.add_job(
            trigger='cron',
            day_of_week=day_of_week,
            hour=hour,
            minute=minute
        )
        
    def cron(self, expression: str):
        """Cron式スケジュール"""
        # Cron式を解析してAPSchedulerのcronトリガーに変換
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError("Invalid cron expression")
            
        minute, hour, day, month, day_of_week = parts
        
        return CronBuilder(self.scheduler, {
            'minute': minute,
            'hour': hour,
            'day': day,
            'month': month,
            'day_of_week': day_of_week
        })
        
    def at(self, run_date: Union[str, datetime]):
        """一回限りのスケジュール"""
        return self.scheduler.add_job(
            trigger='date',
            run_date=run_date
        )


class IntervalBuilder:
    """間隔スケジュールビルダー"""
    
    def __init__(self, scheduler: ElderScheduler, interval: int):
        """初期化メソッド"""
        self.scheduler = scheduler
        self.interval = interval
        
    def seconds(self):
        """secondsメソッド"""
        return IntervalJobBuilder(self.scheduler, 'interval', seconds=self.interval)
        
    def minutes(self):
        """minutesメソッド"""
        return IntervalJobBuilder(self.scheduler, 'interval', minutes=self.interval)
        
    def hours(self):
        """hoursメソッド"""
        return IntervalJobBuilder(self.scheduler, 'interval', hours=self.interval)
        
    def days(self):
        """daysメソッド"""
        return IntervalJobBuilder(self.scheduler, 'interval', days=self.interval)


class CronBuilder:
    """Cronスケジュールビルダー"""
    
    def __init__(self, scheduler: ElderScheduler, cron_params: Dict[str, str]):
        """初期化メソッド"""
        self.scheduler = scheduler
        self.cron_params = cron_params
        
    def do(self, func: Callable, *args, **kwargs):
        """ジョブ実行関数設定"""
        return self.scheduler.add_job(
            func=func,
            trigger='cron',
            args=args,
            kwargs=kwargs,
            **self.cron_params
        )


class IntervalJobBuilder:
    """間隔ジョブビルダー"""
    
    def __init__(self, scheduler: ElderScheduler, trigger: str, **trigger_args):
        """初期化メソッド"""

        self.scheduler = scheduler
        self.trigger = trigger
        self.trigger_args = trigger_args
        
    def do(self, func: Callable, *args, **kwargs):
        """ジョブ実行関数設定"""
        return self.scheduler.add_job(
            func=func,
            trigger=self.trigger,
            args=args,
            kwargs=kwargs,
            **self.trigger_args
        )


class ElderScheduleDecorators:
    """エルダーズギルド用デコレータ"""
    
    def __init__(self, scheduler: ElderScheduler):
        """初期化メソッド"""
        self.scheduler = scheduler
        
    def scheduled(self, trigger: str, **trigger_args):
        """スケジュール済みジョブデコレータ"""
        def decorator(func: Callable):
            """decoratorメソッド"""
            # Check if function is async
            import inspect
            if inspect.iscoroutinefunction(func):
                # Use asyncio executor for async functions
                self.scheduler.add_job(
                    func=func,
                    trigger=trigger,
                    id=f"{func.__module__}.{func.__name__}",
                    name=func.__name__,
                    executor='asyncio',
                    **trigger_args
                )
            else:
                # Use default executor for sync functions
                self.scheduler.add_job(
                    func=func,
                    trigger=trigger,
                    id=f"{func.__module__}.{func.__name__}",
                    name=func.__name__,
                    **trigger_args
                )
            return func
        return decorator
        
    def daily(self, hour: int, minute: int = 0):
        """日次実行デコレータ"""
        return self.scheduled('cron', hour=hour, minute=minute)
        
    def hourly(self, minute: int = 0):
        """時次実行デコレータ"""
        return self.scheduled('cron', minute=minute)
        
    def weekly(self, day_of_week: int, hour: int, minute: int = 0):
        """週次実行デコレータ"""
        return self.scheduled('cron', day_of_week=day_of_week, hour=hour, minute=minute)


# エルダーズギルド統合用のグローバルスケジューラー
_global_scheduler: Optional[ElderScheduler] = None


def get_elder_scheduler() -> ElderScheduler:
    """グローバルエルダースケジューラー取得"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = ElderScheduler()
    return _global_scheduler


def schedule_with_elder(trigger: str, **trigger_args):
    """エルダースケジューラーでスケジュール（デコレータ）"""
    scheduler = get_elder_scheduler()
    decorators = ElderScheduleDecorators(scheduler)
    return decorators.scheduled(trigger, **trigger_args)


def start_elder_scheduler():
    """エルダースケジューラー開始"""
    scheduler = get_elder_scheduler()
    scheduler.start()


def stop_elder_scheduler():
    """エルダースケジューラー停止"""
    scheduler = get_elder_scheduler()
    scheduler.shutdown()


# 4賢者統合用関数
def register_sage_callback(sage_type: str, callback: Callable):
    """4賢者コールバック登録"""
    scheduler = get_elder_scheduler()
    scheduler.sage_callbacks[sage_type] = callback


def get_scheduler_stats() -> Dict[str, Any]:
    """スケジューラー統計取得"""
    scheduler = get_elder_scheduler()
    return scheduler.job_stats.copy()


if __name__ == "__main__":
    # テスト例
    import time
    
    def test_job():
        """test_jobテストメソッド"""
        print(f"🎯 Test job executed at {datetime.now()}")
        
    # スケジューラー作成・開始
    scheduler = ElderScheduler('background')
    scheduler.start()
    
    # ジョブ追加（5秒間隔）
    scheduler.add_job(
        func=test_job,
        trigger='interval',
        seconds=5,
        id='test_job'
    )
    
    try:
        time.sleep(30)  # 30秒間実行
    finally:
        scheduler.shutdown()