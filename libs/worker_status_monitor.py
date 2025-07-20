#!/usr/bin/env python3
"""
Worker Status Monitor - Worker専用ステータス監視システム
EldersGuildのWorker達の状態をリアルタイムで監視・管理
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import logging
import sqlite3
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil

try:
    import pika

    PIKA_AVAILABLE = True
except ImportError:
    PIKA_AVAILABLE = False

logger = logging.getLogger(__name__)


class WorkerStatusMonitor:
    """Worker ステータス監視システム"""

    def __init__(self):
        """WorkerStatusMonitor 初期化"""
        self.workers_status = {}
        self.monitoring_thread = None
        self.is_monitoring = False
        self.monitoring_interval = 1.0
        self.performance_history = defaultdict(list)
        self.error_history = defaultdict(deque)
        self.task_metrics = defaultdict(dict)
        self.queue_status_cache = {}
        self._last_system_metrics_time = 0
        self._system_metrics_cache = None
        self._system_metrics_cache_duration = 10  # システムメトリクスのキャッシュ期間（秒）
        self.db_path = PROJECT_ROOT / "data" / "worker_status.db"

        # データベース初期化
        self._init_database()

        logger.info("WorkerStatusMonitor initialized")

    def _init_database(self):
        """ワーカーステータス用データベース初期化"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # ワーカーステータステーブル
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS worker_status (
                worker_id TEXT PRIMARY KEY,
                worker_type TEXT,
                pid INTEGER,
                status TEXT,
                current_task TEXT,
                started_at TIMESTAMP,
                last_updated TIMESTAMP,
                performance_data TEXT
            )
            """
            )

            # タスクメトリクステーブル
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS task_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id TEXT,
                task_id TEXT,
                processing_time REAL,
                memory_used REAL,
                cpu_percent REAL,
                status TEXT,
                timestamp TIMESTAMP
            )
            """
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    def register_worker(self, worker_info: Dict) -> bool:
        """Worker を登録"""
        try:
            worker_id = worker_info["worker_id"]

            # ワーカー情報を保存
            self.workers_status[worker_id] = {
                "worker_id": worker_id,
                "worker_type": worker_info["worker_type"],
                "pid": worker_info["pid"],
                "status": "idle",
                "current_task": None,
                "started_at": worker_info.get("started_at", datetime.now()),
                "last_updated": datetime.now(),
                "tasks_completed": 0,
                "tasks_failed": 0,
                "total_processing_time": 0.0,
                "performance_metrics": {
                    "avg_processing_time": 0.0,
                    "success_rate": 1.0,
                    "current_load": {"memory_mb": 0.0, "cpu_percent": 0.0},
                },
            }

            # データベースに保存
            self._save_worker_to_db(worker_id)

            logger.info(f"Worker registered: {worker_id}")
            return True

        except Exception as e:
            logger.error(f"Worker registration error: {e}")
            return False

    def _save_worker_to_db(self, worker_id: str):
        """ワーカー情報をデータベースに保存"""
        try:
            worker = self.workers_status[worker_id]
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
            INSERT OR REPLACE INTO worker_status
            (worker_id, worker_type, pid, status, current_task, started_at, last_updated, performance_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    worker_id,
                    worker["worker_type"],
                    worker["pid"],
                    worker["status"],
                    json.dumps(worker.get("current_task")),
                    worker["started_at"].isoformat(),
                    worker["last_updated"].isoformat(),
                    json.dumps(worker["performance_metrics"]),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Database save error: {e}")

    def get_worker_status(self, worker_id: str) -> Optional[Dict]:
        """Worker のステータスを取得"""
        return self.workers_status.get(worker_id)

    def update_worker_task_status(
        self, worker_id: str, status: str, task_info: Dict = None
    ):
        """Worker のタスク処理状況を更新"""
        if worker_id not in self.workers_status:
            logger.warning(f"Worker not found: {worker_id}")
            return

        worker = self.workers_status[worker_id]
        worker["status"] = status
        worker["last_updated"] = datetime.now()

        if task_info:
            worker["current_task"] = task_info

        # データベース更新
        self._save_worker_to_db(worker_id)

        logger.debug(f"Worker task status updated: {worker_id} -> {status}")

    def update_task_metrics(self, worker_id: str, task_metrics: Dict):
        """タスクメトリクスを更新"""
        if worker_id not in self.workers_status:
            logger.warning(f"Worker not found: {worker_id}")
            return

        worker = self.workers_status[worker_id]

        # パフォーマンス統計更新
        processing_time = task_metrics.get("processing_time", 0)
        if processing_time > 0:
            worker["total_processing_time"] += processing_time

            if task_metrics.get("status") == "completed":
                worker["tasks_completed"] += 1
            elif task_metrics.get("status") == "failed":
                worker["tasks_failed"] += 1

            # 平均処理時間計算
            total_tasks = worker["tasks_completed"] + worker["tasks_failed"]
            if total_tasks > 0:
                worker["performance_metrics"]["avg_processing_time"] = (
                    worker["total_processing_time"] / total_tasks
                )
                worker["performance_metrics"]["success_rate"] = (
                    worker["tasks_completed"] / total_tasks
                )

        # 現在の負荷情報
        worker["performance_metrics"]["current_load"] = {
            "memory_mb": task_metrics.get("memory_used", 0),
            "cpu_percent": task_metrics.get("cpu_percent", 0),
        }

        # データベースに保存
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
            INSERT INTO task_metrics
            (worker_id, task_id, processing_time, memory_used, cpu_percent, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    worker_id,
                    task_metrics.get("task_id"),
                    processing_time,
                    task_metrics.get("memory_used", 0),
                    task_metrics.get("cpu_percent", 0),
                    task_metrics.get("status"),
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Task metrics save error: {e}")

        # データベース更新
        self._save_worker_to_db(worker_id)

    def get_worker_performance(self, worker_id: str) -> Dict:
        """Worker のパフォーマンス統計を取得"""
        if worker_id not in self.workers_status:
            return {}

        worker = self.workers_status[worker_id]
        total_tasks = worker["tasks_completed"] + worker["tasks_failed"]

        return {
            "avg_processing_time": worker["performance_metrics"]["avg_processing_time"],
            "total_tasks_completed": worker["tasks_completed"],
            "success_rate": worker["performance_metrics"]["success_rate"],
            "current_load": worker["performance_metrics"]["current_load"],
        }

    def get_queue_status(self) -> Dict:
        """RabbitMQ キューの状態を取得"""
        if not PIKA_AVAILABLE:
            return {"ai_tasks": 0, "ai_pm": 0, "ai_results": 0}

        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()

            queue_status = {}
            queues = ["ai_tasks", "ai_pm", "ai_results"]

            for queue_name in queues:
                method = channel.queue_declare(queue=queue_name, passive=True)
                queue_status[queue_name] = method.method.message_count

            connection.close()
            return queue_status

        except Exception as e:
            logger.error(f"Queue status error: {e}")
            return {"ai_tasks": 0, "ai_pm": 0, "ai_results": 0}

    def check_worker_health(self, worker_id: str) -> Dict:
        """Worker のヘルスチェックを実行"""
        if worker_id not in self.workers_status:
            return {"is_alive": False, "health_score": 0}

        worker = self.workers_status[worker_id]
        pid = worker["pid"]

        try:
            process = psutil.Process(pid)

            is_alive = process.is_running()
            # CPU使用率取得（インターバルなしで高速化）
            cpu_percent = process.cpu_percent(interval=None)
            memory_mb = process.memory_info().rss / 1024 / 1024

            # ヘルススコア計算 (簡易版)
            health_score = 100
            if cpu_percent > 80:
                health_score -= 30
            if memory_mb > 512:  # 512MB以上
                health_score -= 20
            if not is_alive:
                health_score = 0

            return {
                "is_alive": is_alive,
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "health_score": max(0, health_score),
            }

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Health check error for {worker_id}: {e}")
            return {
                "is_alive": False,
                "cpu_percent": 0,
                "memory_mb": 0,
                "health_score": 0,
            }

    def record_worker_error(self, worker_id: str, error_info: Dict):
        """Worker のエラーを記録"""
        if worker_id not in self.workers_status:
            return

        # エラー履歴に追加（最大100件保持）
        error_queue = self.error_history[worker_id]
        error_queue.append(error_info)

        if len(error_queue) > 100:
            error_queue.popleft()

        # Worker のエラーカウント更新
        worker = self.workers_status[worker_id]
        worker["tasks_failed"] += 1

        # 成功率再計算
        total_tasks = worker["tasks_completed"] + worker["tasks_failed"]
        if total_tasks > 0:
            worker["performance_metrics"]["success_rate"] = (
                worker["tasks_completed"] / total_tasks
            )

        self._save_worker_to_db(worker_id)

        logger.warning(
            f"Error recorded for {worker_id}: {error_info.get('error_type')}"
        )

    def get_worker_error_stats(self, worker_id: str) -> Dict:
        """Worker のエラー統計を取得"""
        if worker_id not in self.workers_status:
            return {"total_errors": 0, "error_rate": 0, "recent_errors": []}

        worker = self.workers_status[worker_id]
        error_queue = self.error_history[worker_id]

        total_tasks = worker["tasks_completed"] + worker["tasks_failed"]
        error_rate = worker["tasks_failed"] / total_tasks if total_tasks > 0 else 0

        return {
            "total_errors": worker["tasks_failed"],
            "error_rate": error_rate,
            "recent_errors": list(error_queue),
        }

    def start_monitoring(self, interval: float = 1.0):
        """リアルタイム監視を開始"""
        self.monitoring_interval = interval
        self.is_monitoring = True

        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        logger.info("Worker monitoring started")

    def stop_monitoring(self):
        """リアルタイム監視を停止"""
        self.is_monitoring = False

        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)

        logger.info("Worker monitoring stopped")

    def _monitoring_loop(self):
        """監視ループ"""
        while self.is_monitoring:
            try:
                # すべてのWorkerのヘルスチェック
                for worker_id in list(self.workers_status.keys()):
                    health = self.check_worker_health(worker_id)
                    self.workers_status[worker_id]["health"] = health

                # キューステータス更新
                self.queue_status_cache = self.get_queue_status()

                # 動的インターバル調整
                worker_count = len(self.workers_status)
                if worker_count > 50:
                    self.monitoring_interval = min(10, self.monitoring_interval + 0.5)
                elif worker_count < 10:
                    self.monitoring_interval = max(1, self.monitoring_interval - 0.5)

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.monitoring_interval)

    def get_monitoring_data(self) -> Dict:
        """監視データを取得"""
        return {
            "timestamp": datetime.now().isoformat(),
            "workers": dict(self.workers_status),
            "queues": self.queue_status_cache,
            "system_metrics": self._get_system_metrics(),
        }

    def _get_system_metrics(self) -> Dict:
        """システムメトリクスを取得（キャッシュ付き）"""
        current_time = time.time()

        # キャッシュが有効ならそれを返す
        if (
            self._system_metrics_cache is not None
            and current_time - self._last_system_metrics_time
            < self._system_metrics_cache_duration
        ):
            return self._system_metrics_cache

        try:
            # メトリクス取得（インターバル付きでCPU負荷軽減）
            self._system_metrics_cache = {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "load_average": (
                    psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0
                ),
            }
            self._last_system_metrics_time = current_time
            return self._system_metrics_cache
        except Exception as e:
            logger.error(f"System metrics error: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "load_average": 0,
            }

    def generate_dashboard_data(self) -> Dict:
        """ダッシュボード用データを生成"""
        workers_by_type = defaultdict(list)

        for worker_id, worker in self.workers_status.items():
            workers_by_type[worker["worker_type"]].append(worker)

        # Worker サマリー
        workers_summary = {
            "total_workers": len(self.workers_status),
            "by_type": {
                wtype: len(workers) for wtype, workers in workers_by_type.items()
            },
        }

        # パフォーマンスメトリクス
        performance_metrics = {}
        for worker_type, workers in workers_by_type.items():
            if workers:
                avg_processing_time = sum(
                    w["performance_metrics"]["avg_processing_time"] for w in workers
                ) / len(workers)
                avg_success_rate = sum(
                    w["performance_metrics"]["success_rate"] for w in workers
                ) / len(workers)

                performance_metrics[worker_type] = {
                    "avg_processing_time": avg_processing_time,
                    "avg_success_rate": avg_success_rate,
                    "worker_count": len(workers),
                }

        return {
            "workers_summary": workers_summary,
            "queue_status": self.queue_status_cache,
            "system_health": self._get_system_metrics(),
            "performance_metrics": performance_metrics,
        }

    def auto_register_worker(self, worker_instance):
        """BaseWorker インスタンスを自動登録"""
        try:
            worker_info = {
                "worker_id": getattr(
                    worker_instance, "worker_id", f"worker_{int(time.time())}"
                ),
                "worker_type": getattr(worker_instance, "worker_type", "unknown"),
                "pid": getattr(worker_instance, "pid", 0),
                "started_at": datetime.now(),
            }

            return self.register_worker(worker_info)

        except Exception as e:
            logger.error(f"Auto registration error: {e}")
            return False

    def get_worker_queue_mapping(self) -> Dict:
        """Worker とキューの関連付けを取得"""
        return {
            "task_worker": "ai_tasks",
            "pm_worker": "ai_pm",
            "result_worker": "ai_results",
            "todo_worker": "ai_todo",
        }


if __name__ == "__main__":
    # テスト実行
    monitor = WorkerStatusMonitor()

    # テスト用Worker登録
    test_worker = {
        "worker_id": "test_worker_001",
        "worker_type": "task_worker",
        "pid": 12345,
    }

    monitor.register_worker(test_worker)
    print("Worker registered successfully")

    # ステータス確認
    status = monitor.get_worker_status("test_worker_001")
    print(f"Worker status: {status}")
