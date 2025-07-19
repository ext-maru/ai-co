#!/usr/bin/env python3
"""
パフォーマンス監視プラグイン
タスクの実行時間やリソース使用量を記録
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

from core.plugin_system import WorkerPlugin


class PerformanceMonitorPlugin(WorkerPlugin):
    """パフォーマンス監視プラグイン"""

    @property
    def name(self) -> str:
        return "performance_monitor"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Monitor and record task performance metrics"

    def initialize(self, config: Dict[str, Any]) -> bool:
        """プラグイン初期化"""
        self.db_path = Path(
            config.get("db_path", "/home/aicompany/ai_co/db/performance.db")
        )
        self.record_interval = config.get("record_interval", 1.0)  # 秒
        self.enable_resource_monitoring = config.get("enable_resource_monitoring", True)

        # 進行中のタスク
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

        # データベース初期化
        self._init_db()

        return True

    def _init_db(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    task_type TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds REAL,
                    cpu_percent_avg REAL,
                    memory_mb_avg REAL,
                    memory_mb_peak REAL,
                    status TEXT,
                    error_type TEXT,
                    metadata TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_task_id ON performance_metrics(task_id);
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_task_type ON performance_metrics(task_type);
            """
            )

    def on_task_start(self, task: Dict[str, Any]):
        """タスク開始時の処理"""
        task_id = task.get("task_id", "unknown")

        # タスク情報を記録
        self.active_tasks[task_id] = {
            "task_id": task_id,
            "task_type": task.get("task_type", "general"),
            "start_time": time.time(),
            "cpu_samples": [],
            "memory_samples": [],
            "process": psutil.Process() if self.enable_resource_monitoring else None,
        }

    def on_task_complete(self, task: Dict[str, Any], result: Any):
        """タスク完了時の処理"""
        task_id = task.get("task_id", "unknown")

        if task_id in self.active_tasks:
            task_info = self.active_tasks[task_id]
            end_time = time.time()
            duration = end_time - task_info["start_time"]

            # リソース使用量の集計
            cpu_avg = (
                sum(task_info["cpu_samples"]) / len(task_info["cpu_samples"])
                if task_info["cpu_samples"]
                else 0
            )
            memory_avg = (
                sum(task_info["memory_samples"]) / len(task_info["memory_samples"])
                if task_info["memory_samples"]
                else 0
            )
            memory_peak = (
                max(task_info["memory_samples"]) if task_info["memory_samples"] else 0
            )

            # データベースに記録
            self._record_metrics(
                task_id=task_id,
                task_type=task_info["task_type"],
                start_time=datetime.fromtimestamp(task_info["start_time"]),
                end_time=datetime.fromtimestamp(end_time),
                duration=duration,
                cpu_avg=cpu_avg,
                memory_avg=memory_avg,
                memory_peak=memory_peak,
                status="completed",
                metadata=json.dumps(
                    {
                        "files_created": len(result.get("files_created", []))
                        if isinstance(result, dict)
                        else 0
                    }
                ),
            )

            # クリーンアップ
            del self.active_tasks[task_id]

    def on_task_error(self, task: Dict[str, Any], error: Exception):
        """タスクエラー時の処理"""
        task_id = task.get("task_id", "unknown")

        if task_id in self.active_tasks:
            task_info = self.active_tasks[task_id]
            end_time = time.time()
            duration = end_time - task_info["start_time"]

            # エラー情報を記録
            self._record_metrics(
                task_id=task_id,
                task_type=task_info["task_type"],
                start_time=datetime.fromtimestamp(task_info["start_time"]),
                end_time=datetime.fromtimestamp(end_time),
                duration=duration,
                cpu_avg=0,
                memory_avg=0,
                memory_peak=0,
                status="failed",
                error_type=type(error).__name__,
            )

            # クリーンアップ
            del self.active_tasks[task_id]

    def _record_metrics(self, **kwargs):
        """メトリクスをデータベースに記録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO performance_metrics
                (task_id, task_type, start_time, end_time, duration_seconds,
                 cpu_percent_avg, memory_mb_avg, memory_mb_peak, status,
                 error_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    kwargs.get("task_id"),
                    kwargs.get("task_type"),
                    kwargs.get("start_time"),
                    kwargs.get("end_time"),
                    kwargs.get("duration"),
                    kwargs.get("cpu_avg"),
                    kwargs.get("memory_avg"),
                    kwargs.get("memory_peak"),
                    kwargs.get("status"),
                    kwargs.get("error_type"),
                    kwargs.get("metadata", "{}"),
                ),
            )

    def cleanup(self):
        """クリーンアップ処理"""
        # アクティブなタスクの記録を完了
        for task_id in list(self.active_tasks.keys()):
            task_info = self.active_tasks[task_id]
            self._record_metrics(
                task_id=task_id,
                task_type=task_info["task_type"],
                start_time=datetime.fromtimestamp(task_info["start_time"]),
                end_time=datetime.now(),
                duration=time.time() - task_info["start_time"],
                status="interrupted",
            )


# 統計情報取得用のヘルパークラス
class PerformanceStats:
    """パフォーマンス統計"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """統計サマリーを取得"""
        with sqlite3.connect(self.db_path) as conn:
            # 基本統計
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_tasks,
                    AVG(duration_seconds) as avg_duration,
                    MAX(duration_seconds) as max_duration,
                    MIN(duration_seconds) as min_duration,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
                FROM performance_metrics
                WHERE recorded_at > datetime('now', '-{} days')
            """.format(
                    days
                )
            )

            row = cursor.fetchone()

            return {
                "total_tasks": row[0],
                "avg_duration": row[1],
                "max_duration": row[2],
                "min_duration": row[3],
                "completed_count": row[4],
                "failed_count": row[5],
                "success_rate": row[4] / row[0] if row[0] > 0 else 0,
            }

    def get_task_type_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """タスクタイプ別の統計"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    task_type,
                    COUNT(*) as count,
                    AVG(duration_seconds) as avg_duration,
                    AVG(cpu_percent_avg) as avg_cpu,
                    AVG(memory_mb_avg) as avg_memory
                FROM performance_metrics
                GROUP BY task_type
            """
            )

            breakdown = {}
            for row in cursor.fetchall():
                breakdown[row[0]] = {
                    "count": row[1],
                    "avg_duration": row[2],
                    "avg_cpu": row[3],
                    "avg_memory": row[4],
                }

            return breakdown
