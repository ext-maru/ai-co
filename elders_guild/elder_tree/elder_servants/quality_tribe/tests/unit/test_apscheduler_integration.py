#!/usr/bin/env python3
"""
APScheduler統合システムのテスト
TDD実装
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from elders_guild.elder_tree.apscheduler_integration import (
    ElderScheduler,
    ElderSchedulerConfig,
    ElderScheduleBuilder,
    ElderScheduleDecorators,
    get_elder_scheduler,
    get_scheduler_stats,
    start_elder_scheduler,
    stop_elder_scheduler
)


class TestElderSchedulerConfig:
    """エルダーズギルド スケジューラー設定テスト"""
    
    def test_config_initialization(self):
        """設定初期化テスト"""
        config = ElderSchedulerConfig()
        
        assert config.timezone == 'Asia/Tokyo'
        assert config.max_workers == 20
        assert config.redis_host == 'localhost'
        assert config.redis_port == 6379
        assert config.redis_db == 1
        assert not config.use_redis  # デフォルトはFalse
        assert config.use_postgres   # デフォルトはTrue
        
    def test_get_jobstores_postgres_only(self):
        """PostgreSQLのみのジョブストア設定"""
        config = ElderSchedulerConfig()
        config.use_redis = False
        config.use_postgres = True
        
        jobstores = config.get_jobstores()
        
        assert 'postgres' in jobstores
        assert 'redis' not in jobstores
        assert jobstores['default'] == 'memory'
        
    def test_get_jobstores_redis_only(self):
        """Redisのみのジョブストア設定"""
        config = ElderSchedulerConfig()
        config.use_redis = True
        config.use_postgres = False
        
        jobstores = config.get_jobstores()
        
        assert 'redis' in jobstores
        assert 'postgres' not in jobstores
        assert jobstores['default'] == 'memory'
        
    def test_get_executors(self):
        """エグゼキューター設定テスト"""
        config = ElderSchedulerConfig()
        executors = config.get_executors()
        
        assert 'default' in executors
        assert 'asyncio' in executors
        
    def test_get_job_defaults(self):
        """ジョブデフォルト設定テスト"""
        config = ElderSchedulerConfig()
        defaults = config.get_job_defaults()
        
        assert defaults['coalesce'] is True
        assert defaults['max_instances'] == 3
        assert defaults['misfire_grace_time'] == 30


class TestElderScheduler:
    """エルダーズギルド スケジューラーテスト"""
    
    @pytest.fixture
    def scheduler(self):
        """テスト用スケジューラー"""
        scheduler = ElderScheduler('background')
        yield scheduler
        if scheduler.scheduler.running:
            scheduler.shutdown(wait=False)
            
    def test_scheduler_initialization(self, scheduler):
        """スケジューラー初期化テスト"""
        assert scheduler is not None
        assert not scheduler.scheduler.running
        assert scheduler.job_stats['total_executed'] == 0
        assert scheduler.job_stats['total_errors'] == 0
        
    def test_scheduler_start_stop(self, scheduler):
        """スケジューラー開始・停止テスト"""
        # 開始
        scheduler.start()
        assert scheduler.scheduler.running
        
        # 停止
        scheduler.shutdown()
        assert not scheduler.scheduler.running
        
    def test_add_job_interval(self, scheduler):
        """間隔ジョブ追加テスト"""
        def test_job():
            pass
            
        job = scheduler.add_job(
            func=test_job,
            trigger='interval',
            seconds=5,
            id='test_interval_job',
            name='Test Interval Job'
        )
        
        assert job.id == 'test_interval_job'
        assert job.name == 'Test Interval Job'
        assert scheduler.job_stats['active_jobs'] == 1
        
    def test_add_job_cron(self, scheduler):
        """Cronジョブ追加テスト"""
        def test_job():
            pass
            
        job = scheduler.add_job(
            func=test_job,
            trigger='cron',
            minute='*/5',  # 5分間隔
            id='test_cron_job',
            name='Test Cron Job'
        )
        
        assert job.id == 'test_cron_job'
        assert job.name == 'Test Cron Job'
        
    def test_remove_job(self, scheduler):
        """ジョブ削除テスト"""
        def test_job():
            pass
            
        job = scheduler.add_job(
            func=test_job,
            trigger='interval',
            seconds=10,
            id='test_remove_job'
        )
        
        assert scheduler.get_job('test_remove_job') is not None
        
        scheduler.remove_job('test_remove_job')
        assert scheduler.get_job('test_remove_job') is None
        
    def test_pause_resume_job(self, scheduler):
        """ジョブ一時停止・再開テスト"""
        def test_job():
            pass
            
        job = scheduler.add_job(
            func=test_job,
            trigger='interval',
            seconds=10,
            id='test_pause_job'
        )
        
        # 一時停止
        scheduler.pause_job('test_pause_job')
        paused_job = scheduler.get_job('test_pause_job')
        assert paused_job.next_run_time is None
        
        # 再開
        scheduler.resume_job('test_pause_job')
        resumed_job = scheduler.get_job('test_pause_job')
        assert resumed_job.next_run_time is not None
        
    def test_modify_job(self, scheduler):
        """ジョブ変更テスト"""
        def test_job():
            pass
            
        job = scheduler.add_job(
            func=test_job,
            trigger='interval',
            seconds=10,
            id='test_modify_job',
            name='Original Name'
        )
        
        # ジョブ変更
        modified_job = scheduler.modify_job(
            'test_modify_job',
            name='Modified Name'
        )
        
        assert modified_job.name == 'Modified Name'
        
    def test_get_jobs(self, scheduler):
        """ジョブ一覧取得テスト"""
        def test_job():
            pass
            
        # 複数ジョブ追加
        scheduler.add_job(func=test_job, trigger='interval', seconds=5, id='job1')
        scheduler.add_job(func=test_job, trigger='interval', seconds=10, id='job2')
        scheduler.add_job(func=test_job, trigger='interval', seconds=15, id='job3')
        
        jobs = scheduler.get_jobs()
        assert len(jobs) == 3
        
        job_ids = [job.id for job in jobs]
        assert 'job1' in job_ids
        assert 'job2' in job_ids
        assert 'job3' in job_ids


class TestElderScheduleBuilder:
    """エルダーズギルド スケジュールビルダーテスト"""
    
    @pytest.fixture
    def scheduler(self):
        """テスト用スケジューラー"""
        scheduler = ElderScheduler('background')
        yield scheduler
        if scheduler.scheduler.running:
            scheduler.shutdown(wait=False)
            
    @pytest.fixture
    def builder(self, scheduler):
        """テスト用ビルダー"""
        return ElderScheduleBuilder(scheduler)
        
    def test_interval_builder_seconds(self, builder):
        """秒間隔ビルダーテスト"""
        def test_job():
            pass
            
        interval_builder = builder.every(30)
        job_builder = interval_builder.seconds()
        job = job_builder.do(test_job)
        
        assert job is not None
        assert job.trigger.interval.total_seconds() == 30
        
    def test_interval_builder_minutes(self, builder):
        """分間隔ビルダーテスト"""
        def test_job():
            pass
            
        interval_builder = builder.every(5)
        job_builder = interval_builder.minutes()
        job = job_builder.do(test_job)
        
        assert job is not None
        assert job.trigger.interval.total_seconds() == 300  # 5分 = 300秒
        
    def test_interval_builder_hours(self, builder):
        """時間隔ビルダーテスト"""
        def test_job():
            pass
            
        interval_builder = builder.every(2)
        job_builder = interval_builder.hours()
        job = job_builder.do(test_job)
        
        assert job is not None
        assert job.trigger.interval.total_seconds() == 7200  # 2時間 = 7200秒
        
    def test_cron_builder(self, builder):
        """Cronビルダーテスト"""
        def test_job():
            pass
            
        cron_builder = builder.cron("0 */2 * * *")  # 2時間間隔
        job = cron_builder.do(test_job)
        
        assert job is not None
        assert str(job.trigger).startswith('cron')


class TestElderScheduleDecorators:
    """エルダーズギルド スケジュールデコレータテスト"""
    
    @pytest.fixture
    def scheduler(self):
        """テスト用スケジューラー"""
        scheduler = ElderScheduler('background')
        yield scheduler
        if scheduler.scheduler.running:
            scheduler.shutdown(wait=False)
            
    @pytest.fixture
    def decorators(self, scheduler):
        """テスト用デコレータ"""
        return ElderScheduleDecorators(scheduler)
        
    def test_scheduled_decorator(self, decorators, scheduler):
        """スケジュールデコレータテスト"""
        @decorators.scheduled('interval', seconds=10)
        def test_function():
            return "test"
            
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].func == test_function
        
    def test_daily_decorator(self, decorators, scheduler):
        """日次デコレータテスト"""
        @decorators.daily(hour=9, minute=30)
        def daily_task():
            return "daily"
            
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert str(jobs[0].trigger).startswith('cron')
        
    def test_hourly_decorator(self, decorators, scheduler):
        """時次デコレータテスト"""
        @decorators.hourly(minute=15)
        def hourly_task():
            return "hourly"
            
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert str(jobs[0].trigger).startswith('cron')
        
    def test_weekly_decorator(self, decorators, scheduler):
        """週次デコレータテスト"""
        @decorators.weekly(day_of_week=1, hour=10, minute=0)  # 月曜日10:00
        def weekly_task():
            return "weekly"
            
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert str(jobs[0].trigger).startswith('cron')


class TestElderSchedulerGlobalFunctions:
    """グローバル関数テスト"""
    
    def test_get_elder_scheduler(self):
        """グローバルスケジューラー取得テスト"""
        scheduler1 = get_elder_scheduler()
        scheduler2 = get_elder_scheduler()
        
        # シングルトンパターンの確認
        assert scheduler1 is scheduler2
        
    def test_get_scheduler_stats(self):
        """スケジューラー統計取得テスト"""
        stats = get_scheduler_stats()
        
        assert 'total_executed' in stats
        assert 'total_errors' in stats
        assert 'last_execution' in stats
        assert 'active_jobs' in stats
        
    def test_start_stop_elder_scheduler(self):
        """グローバルスケジューラー開始・停止テスト"""
        # 停止状態から開始
        start_elder_scheduler()
        scheduler = get_elder_scheduler()
        assert scheduler.scheduler.running
        
        # 停止
        stop_elder_scheduler()
        assert not scheduler.scheduler.running


class TestElderSchedulerIntegration:
    """統合テスト"""
    
    @pytest.fixture
    def scheduler(self):
        """テスト用スケジューラー"""
        scheduler = ElderScheduler('background')
        scheduler.start()
        yield scheduler
        scheduler.shutdown()
        
    def test_job_execution_tracking(self, scheduler):
        """ジョブ実行追跡テスト"""
        execution_count = 0
        
        def counting_job():
            nonlocal execution_count
            execution_count += 1
            
        # 短い間隔でジョブを追加
        scheduler.add_job(
            func=counting_job,
            trigger='interval',
            seconds=1,
            id='counting_job'
        )
        
        # 3秒待機（2-3回実行されるはず）
        time.sleep(3.5)
        
        assert execution_count >= 2
        assert scheduler.job_stats['total_executed'] >= 2
        
    def test_job_error_handling(self, scheduler):
        """ジョブエラー処理テスト"""
        def error_job():
            raise ValueError("Test error")
            
        scheduler.add_job(
            func=error_job,
            trigger='interval',
            seconds=1,
            id='error_job'
        )
        
        # エラーが発生するまで待機
        time.sleep(2)
        
        assert scheduler.job_stats['total_errors'] >= 1
        
    def test_sage_callback_integration(self, scheduler):
        """4賢者コールバック統合テスト"""
        task_sage_called = False
        incident_sage_called = False
        
        def task_sage_callback(event):
            nonlocal task_sage_called
            task_sage_called = True
            
        def incident_sage_callback(event):
            nonlocal incident_sage_called
            incident_sage_called = True
            
        # コールバック登録
        scheduler.sage_callbacks['task_sage'] = task_sage_callback
        scheduler.sage_callbacks['incident_sage'] = incident_sage_callback
        
        # 成功ジョブ
        def success_job():
            pass
            
        # エラージョブ
        def error_job():
            raise Exception("Test error")
            
        scheduler.add_job(func=success_job, trigger='date', run_date=datetime.now() + timedelta(seconds=1))
        scheduler.add_job(func=error_job, trigger='date', run_date=datetime.now() + timedelta(seconds=2))
        
        # 実行を待機
        time.sleep(3)
        
        assert task_sage_called
        assert incident_sage_called


class TestErrorCases:
    """エラーケーステスト"""
    
    def test_invalid_scheduler_type(self):
        """無効なスケジューラータイプ"""
        with pytest.raises(ValueError):
            ElderScheduler('invalid_type')
            
    def test_remove_nonexistent_job(self):
        """存在しないジョブの削除"""
        scheduler = ElderScheduler('background')
        
        with pytest.raises(Exception):
            scheduler.remove_job('nonexistent_job')
            
    def test_pause_nonexistent_job(self):
        """存在しないジョブの一時停止"""
        scheduler = ElderScheduler('background')
        
        with pytest.raises(Exception):
            scheduler.pause_job('nonexistent_job')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])