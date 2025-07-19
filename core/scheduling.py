#!/usr/bin/env python3
"""
スケジューリング機能
定期実行タスクのサポート
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import Event, Thread
from typing import Any, Callable, Dict, List, Optional


class ScheduleType(Enum):
    """スケジュールタイプ"""

    ONCE = "once"  # 一度だけ実行
    INTERVAL = "interval"  # 一定間隔で実行
    DAILY = "daily"  # 毎日特定時刻に実行
    WEEKLY = "weekly"  # 毎週特定曜日・時刻に実行
    MONTHLY = "monthly"  # 毎月特定日・時刻に実行
    CRON = "cron"  # Cron形式


@dataclass
class Schedule:
    """Basic schedule configuration (for TDD compatibility)"""

    schedule_type: ScheduleType
    cron_expression: Optional[str] = None
    hour: Optional[int] = None
    day_of_week: Optional[int] = None

    def is_valid(self) -> bool:
        """Validate schedule configuration"""
        if self.schedule_type == ScheduleType.CRON:
            return validate_cron_expression(self.cron_expression)
        return True


@dataclass
class ScheduledTask:
    """スケジュールされたタスク"""

    task_id: str
    name: str
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    task_data: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ScheduleParser:
    """スケジュール解析"""

    @staticmethod
    def parse_interval(config: Dict[str, Any]) -> timedelta:
        """インターバル設定を解析"""
        unit = config.get("unit", "minutes")
        value = config.get("value", 1)

        if unit == "seconds":
            return timedelta(seconds=value)
        elif unit == "minutes":
            return timedelta(minutes=value)
        elif unit == "hours":
            return timedelta(hours=value)
        elif unit == "days":
            return timedelta(days=value)
        else:
            raise ValueError(f"Unknown interval unit: {unit}")

    @staticmethod
    def parse_daily(config: Dict[str, Any]) -> datetime:
        """日次スケジュールを解析"""
        time_str = config.get("time", "00:00")
        hour, minute = map(int, time_str.split(":"))

        now = datetime.now()
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # 既に過ぎている場合は翌日
        if scheduled <= now:
            scheduled += timedelta(days=1)

        return scheduled

    @staticmethod
    def parse_weekly(config: Dict[str, Any]) -> datetime:
        """週次スケジュールを解析"""
        day_of_week = config.get("day", 0)  # 0=月曜日, 6=日曜日
        time_str = config.get("time", "00:00")
        hour, minute = map(int, time_str.split(":"))

        now = datetime.now()
        current_dow = now.weekday()
        days_ahead = (day_of_week - current_dow) % 7

        if days_ahead == 0:
            # 今日の場合、時刻をチェック
            scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if scheduled <= now:
                days_ahead = 7

        scheduled = now + timedelta(days=days_ahead)
        scheduled = scheduled.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return scheduled

    @staticmethod
    def calculate_next_run(task: ScheduledTask) -> datetime:
        """次回実行時刻を計算"""
        if task.schedule_type == ScheduleType.ONCE:
            # 一度だけの場合、設定された時刻
            return datetime.fromisoformat(task.schedule_config["datetime"])

        elif task.schedule_type == ScheduleType.INTERVAL:
            # インターバルの場合
            interval = ScheduleParser.parse_interval(task.schedule_config)
            if task.last_run:
                return task.last_run + interval
            else:
                return datetime.now()

        elif task.schedule_type == ScheduleType.DAILY:
            return ScheduleParser.parse_daily(task.schedule_config)

        elif task.schedule_type == ScheduleType.WEEKLY:
            return ScheduleParser.parse_weekly(task.schedule_config)

        elif task.schedule_type == ScheduleType.CRON:
            # Cron式の場合
            cron_expr = task.schedule_config.get("cron_expression")
            if not cron_expr:
                raise ValueError("Cron expression is required for CRON schedule type")
            return calculate_next_cron_run(cron_expr, task.last_run or datetime.now())

        else:
            raise ValueError(f"Unsupported schedule type: {task.schedule_type}")


class ScheduledWorker:
    """スケジューリング機能を持つワーカー基底クラス"""

    def __init__(self):
        self.scheduled_tasks: List[ScheduledTask] = []
        self.scheduler_thread = None
        self.stop_event = Event()
        self.logger = logging.getLogger(__name__)

    def schedule_task(
        self,
        name: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        task_data: Dict[str, Any],
    ) -> ScheduledTask:
        """タスクをスケジュール"""
        task = ScheduledTask(
            task_id=f"scheduled_{int(time.time())}",
            name=name,
            schedule_type=ScheduleType(schedule_type),
            schedule_config=schedule_config,
            task_data=task_data,
        )

        # 次回実行時刻を計算
        task.next_run = ScheduleParser.calculate_next_run(task)

        self.scheduled_tasks.append(task)
        self.logger.info(f"📅 Task scheduled: {name} - Next run: {task.next_run}")

        return task

    def start_scheduler(self):
        """スケジューラーを開始"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return

        self.scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("⏰ Scheduler started")

    def _scheduler_loop(self):
        """スケジューラーのメインループ"""
        while not self.stop_event.is_set():
            now = datetime.now()

            for task in self.scheduled_tasks:
                if not task.enabled:
                    continue

                if task.next_run and task.next_run <= now:
                    # タスクを実行
                    self._execute_scheduled_task(task)

                    # 統計更新
                    task.last_run = now
                    task.run_count += 1

                    # 次回実行時刻を計算
                    if task.schedule_type != ScheduleType.ONCE:
                        task.next_run = ScheduleParser.calculate_next_run(task)
                    else:
                        task.enabled = False  # 一度だけの場合は無効化

            # 1秒待機
            self.stop_event.wait(1)

    def _execute_scheduled_task(self, task: ScheduledTask):
        """スケジュールされたタスクを実行"""
        self.logger.info(f"🎯 Executing scheduled task: {task.name}")

        try:
            # 実装クラスでオーバーライドされるべきメソッド
            self.execute_scheduled_task(task.task_data)
        except Exception as e:
            self.logger.error(f"Error executing scheduled task {task.name}: {str(e)}")

    def execute_scheduled_task(self, task_data: Dict[str, Any]):
        """スケジュールされたタスクの実行（オーバーライド必須）"""
        raise NotImplementedError("Subclass must implement execute_scheduled_task")

    def stop_scheduler(self):
        """スケジューラーを停止"""
        self.stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.logger.info("⏰ Scheduler stopped")


class ScheduleManager:
    """全体のスケジュール管理"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("/home/aicompany/ai_co/db/schedules.db")
        self.logger = logging.getLogger(__name__)
        self._init_db()

    def _init_db(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedules (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    schedule_type TEXT NOT NULL,
                    schedule_config TEXT NOT NULL,
                    task_data TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    run_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedule_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success INTEGER DEFAULT 1,
                    error_message TEXT,
                    FOREIGN KEY (task_id) REFERENCES schedules(task_id)
                )
            """
            )

    def save_schedule(self, task: ScheduledTask):
        """スケジュールを保存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO schedules
                (task_id, name, schedule_type, schedule_config, task_data,
                 enabled, last_run, next_run, run_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    task.task_id,
                    task.name,
                    task.schedule_type.value,
                    json.dumps(task.schedule_config),
                    json.dumps(task.task_data),
                    1 if task.enabled else 0,
                    task.last_run.isoformat() if task.last_run else None,
                    task.next_run.isoformat() if task.next_run else None,
                    task.run_count,
                ),
            )

    def load_schedules(self) -> List[ScheduledTask]:
        """スケジュールを読み込む"""
        schedules = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT task_id, name, schedule_type, schedule_config, task_data,
                       enabled, last_run, next_run, run_count, created_at
                FROM schedules
                WHERE enabled = 1
            """
            )

            for row in cursor.fetchall():
                task = ScheduledTask(
                    task_id=row[0],
                    name=row[1],
                    schedule_type=ScheduleType(row[2]),
                    schedule_config=json.loads(row[3]),
                    task_data=json.loads(row[4]),
                    enabled=bool(row[5]),
                    last_run=datetime.fromisoformat(row[6]) if row[6] else None,
                    next_run=datetime.fromisoformat(row[7]) if row[7] else None,
                    run_count=row[8],
                    created_at=datetime.fromisoformat(row[9]),
                )
                schedules.append(task)

        return schedules

    def record_execution(
        self, task_id: str, success: bool, error_message: Optional[str] = None
    ):
        """実行履歴を記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO schedule_history (task_id, success, error_message)
                VALUES (?, ?, ?)
            """,
                (task_id, 1 if success else 0, error_message),
            )

    def get_schedule_stats(self) -> Dict[str, Any]:
        """スケジュール統計を取得"""
        with sqlite3.connect(self.db_path) as conn:
            # アクティブなスケジュール数
            active_count = conn.execute(
                "SELECT COUNT(*) FROM schedules WHERE enabled = 1"
            ).fetchone()[0]

            # 実行履歴統計
            stats = conn.execute(
                """
                SELECT
                    COUNT(*) as total_executions,
                    SUM(success) as successful_executions,
                    COUNT(*) - SUM(success) as failed_executions
                FROM schedule_history
                WHERE executed_at > datetime('now', '-7 days')
            """
            ).fetchone()

            return {
                "active_schedules": active_count,
                "total_executions_7days": stats[0],
                "successful_executions_7days": stats[1],
                "failed_executions_7days": stats[2],
            }


# 便利なデコレータ
class schedule:
    """スケジュールデコレータ（使いやすいAPI）"""

    @staticmethod
    def every(interval: int):
        """インターバルスケジュール"""

        class IntervalSchedule:
            def __init__(self, interval):
                self.interval = interval

            def seconds(self):
                return {"unit": "seconds", "value": self.interval}

            def minutes(self):
                return {"unit": "minutes", "value": self.interval}

            def hours(self):
                return {"unit": "hours", "value": self.interval}

            def days(self):
                return {"unit": "days", "value": self.interval}

        return IntervalSchedule(interval)

    @staticmethod
    def daily_at(time_str: str):
        """毎日特定時刻"""
        return {"time": time_str}

    @staticmethod
    def weekly_on(day: int, time_str: str):
        """毎週特定曜日・時刻"""
        return {"day": day, "time": time_str}


# Cron Expression Support Functions


def validate_cron_expression(cron_expr: str) -> bool:
    """Validate cron expression format"""
    if not cron_expr or not isinstance(cron_expr, str):
        return False

    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return False

    # Validate each field
    field_ranges = [
        (0, 59),  # minute
        (0, 23),  # hour
        (1, 31),  # day
        (1, 12),  # month
        (0, 7),  # weekday (0 and 7 = Sunday)
    ]

    field_names = ["minute", "hour", "day", "month", "weekday"]

    for i, (part, (min_val, max_val), field_name) in enumerate(
        zip(parts, field_ranges, field_names)
    ):
        try:
            parse_cron_field(part, field_name)
        except (ValueError, TypeError):
            return False

    return True


def parse_cron_field(field_value: str, field_type: str) -> set:
    """Parse individual cron field and return set of valid values"""
    if field_value == "*":
        return _get_field_range(field_type)

    values = set()

    # Handle comma-separated values
    for part in field_value.split(","):
        part = part.strip()

        # Handle step values (e.g., */5, 1-10/2)
        if "/" in part:
            range_part, step = part.split("/", 1)
            step = int(step)

            if range_part == "*":
                base_values = _get_field_range(field_type)
            elif "-" in range_part:
                start, end = map(int, range_part.split("-", 1))
                base_values = set(range(start, end + 1))
            else:
                start = int(range_part)
                base_values = {start}

            # Apply step
            values.update(
                {v for v in base_values if v % step == (min(base_values) % step)}
            )

        # Handle ranges (e.g., 1-5)
        elif "-" in part:
            start, end = part.split("-", 1)
            start = _parse_field_value(start, field_type)
            end = _parse_field_value(end, field_type)
            values.update(range(start, end + 1))

        # Handle single values
        else:
            values.add(_parse_field_value(part, field_type))

    # Validate all values are in range
    valid_range = _get_field_range(field_type)
    if not values.issubset(valid_range):
        invalid = values - valid_range
        raise ValueError(f"Invalid values for {field_type}: {invalid}")

    return values


def _get_field_range(field_type: str) -> set:
    """Get valid range for field type"""
    ranges = {
        "minute": set(range(0, 60)),
        "hour": set(range(0, 24)),
        "day": set(range(1, 32)),
        "month": set(range(1, 13)),
        "weekday": set(range(0, 8)),  # 0 and 7 both represent Sunday
    }
    return ranges[field_type]


def _parse_field_value(value: str, field_type: str) -> int:
    """Parse individual field value (handling named values)"""
    # Handle weekday names
    if field_type == "weekday":
        weekday_names = {
            "SUN": 0,
            "MON": 1,
            "TUE": 2,
            "WED": 3,
            "THU": 4,
            "FRI": 5,
            "SAT": 6,
        }
        if value.upper() in weekday_names:
            return weekday_names[value.upper()]

    # Handle month names (future enhancement)
    if field_type == "month":
        month_names = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }
        if value.upper() in month_names:
            return month_names[value.upper()]

    return int(value)


def calculate_next_cron_run(cron_expr: str, current_time: datetime) -> datetime:
    """Calculate next run time for cron expression"""
    if not validate_cron_expression(cron_expr):
        raise ValueError(f"Invalid cron expression: {cron_expr}")

    parts = cron_expr.split()

    minutes = parse_cron_field(parts[0], "minute")
    hours = parse_cron_field(parts[1], "hour")
    days = parse_cron_field(parts[2], "day")
    months = parse_cron_field(parts[3], "month")
    weekdays = parse_cron_field(parts[4], "weekday")

    # Start from the next minute
    next_time = current_time.replace(second=0, microsecond=0) + timedelta(minutes=1)

    # Find next valid time (simple approach, can be optimized)
    max_iterations = 366 * 24 * 60  # Max 1 year worth of minutes
    iterations = 0

    while iterations < max_iterations:
        # Convert Python weekday (0=Monday) to cron weekday (0=Sunday, 1=Monday)
        cron_weekday = (next_time.weekday() + 1) % 7

        if (
            next_time.minute in minutes
            and next_time.hour in hours
            and next_time.day in days
            and next_time.month in months
            and cron_weekday in weekdays
        ):
            return next_time

        next_time += timedelta(minutes=1)
        iterations += 1

    raise ValueError("Could not find next run time within reasonable range")


def calculate_next_run(schedule: Schedule, current_time: datetime) -> datetime:
    """Calculate next run for Schedule object (TDD compatibility)"""
    if schedule.schedule_type == ScheduleType.CRON:
        return calculate_next_cron_run(schedule.cron_expression, current_time)
    elif schedule.schedule_type == ScheduleType.DAILY:
        # Simple daily implementation
        next_run = current_time.replace(
            hour=schedule.hour or 0, minute=0, second=0, microsecond=0
        )
        if next_run <= current_time:
            next_run += timedelta(days=1)
        return next_run
    elif schedule.schedule_type == ScheduleType.WEEKLY:
        # Simple weekly implementation
        target_weekday = schedule.day_of_week or 0
        days_ahead = (target_weekday - current_time.weekday()) % 7
        if days_ahead == 0 and current_time.hour >= (schedule.hour or 0):
            days_ahead = 7
        next_run = current_time + timedelta(days=days_ahead)
        return next_run.replace(
            hour=schedule.hour or 0, minute=0, second=0, microsecond=0
        )
    elif schedule.schedule_type == ScheduleType.ONCE:
        return current_time  # For ONCE, return current time
    else:
        raise ValueError(f"Unsupported schedule type: {schedule.schedule_type}")
