#!/usr/bin/env python3
"""
ワーカーオートスケーリングマネージャー
負荷に応じて自動的にワーカー数を調整
"""

import json
import logging
import subprocess
import time
from datetime import datetime, timedelta
from threading import Event, Thread
from typing import Dict, List, Optional, Tuple

import pika
import psutil


class AutoScalingManager:
    """ワーカーのオートスケーリング管理"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: スケーリング設定
                - min_workers: 最小ワーカー数
                - max_workers: 最大ワーカー数
                - scale_up_threshold: スケールアップ閾値（キュー長）
                - scale_down_threshold: スケールダウン閾値
                - cooldown_period: クールダウン期間（秒）
        """
        self.config = config or {
            "min_workers": 1,
            "max_workers": 10,
            "scale_up_threshold": 50,
            "scale_down_threshold": 10,
            "cooldown_period": 60,
            "check_interval": 10,
        }

        self.logger = logging.getLogger(__name__)
        self.connection = None
        self.channel = None
        self.stop_event = Event()

        # ワーカー情報
        self.worker_processes: Dict[str, subprocess.Popen] = {}
        self.last_scale_time = datetime.now()

        # メトリクス
        self.metrics = {
            "scale_up_count": 0,
            "scale_down_count": 0,
            "current_workers": 0,
            "queue_length_history": [],
        }

    def connect(self):
        """RabbitMQに接続"""
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost")
        )
        self.channel = self.connection.channel()

    def get_queue_length(self, queue_name: str) -> int:
        """キューの長さを取得"""
        try:
            method = self.channel.queue_declare(queue=queue_name, passive=True)
            return method.method.message_count
        except Exception as e:
            self.logger.error(f"Failed to get queue length: {str(e)}")
            return 0

    def get_system_load(self) -> Dict[str, float]:
        """システム負荷を取得"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "load_average": psutil.getloadavg()[0]
            if hasattr(psutil, "getloadavg")
            else 0,
        }

    def count_running_workers(self, worker_type: str) -> int:
        """実行中のワーカー数をカウント"""
        count = 0
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"]
                if cmdline and worker_type in " ".join(cmdline):
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # 管理中のプロセスも確認
        self.cleanup_dead_processes()
        return len([p for p in self.worker_processes.values() if p.poll() is None])

    def cleanup_dead_processes(self):
        """終了したプロセスをクリーンアップ"""
        dead_workers = []
        for worker_id, proc in self.worker_processes.items():
            if proc.poll() is not None:
                dead_workers.append(worker_id)

        for worker_id in dead_workers:
            del self.worker_processes[worker_id]
            self.logger.info(f"🧹 Cleaned up dead worker: {worker_id}")

    def spawn_worker(self, worker_type: str, worker_script: str) -> Optional[str]:
        """新しいワーカーを起動"""
        try:
            worker_id = f"{worker_type}_{int(time.time())}"

            # ワーカープロセスを起動
            cmd = ["python3", worker_script, "--worker-id", worker_id]

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="/home/aicompany/ai_co",
            )

            self.worker_processes[worker_id] = proc
            self.logger.info(f"🚀 Spawned new worker: {worker_id} (PID: {proc.pid})")

            return worker_id

        except Exception as e:
            self.logger.error(f"Failed to spawn worker: {str(e)}")
            return None

    def terminate_worker(self, worker_id: str) -> bool:
        """ワーカーを終了"""
        try:
            if worker_id in self.worker_processes:
                proc = self.worker_processes[worker_id]

                # 優雅に終了を試みる
                proc.terminate()
                time.sleep(2)

                # まだ生きていれば強制終了
                if proc.poll() is None:
                    proc.kill()

                del self.worker_processes[worker_id]
                self.logger.info(f"🛑 Terminated worker: {worker_id}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to terminate worker: {str(e)}")

        return False

    def should_scale_up(self, queue_length: int, system_load: Dict[str, float]) -> bool:
        """スケールアップすべきか判定"""
        # クールダウン期間中はスケーリングしない
        if datetime.now() - self.last_scale_time < timedelta(
            seconds=self.config["cooldown_period"]
        ):
            return False

        # キュー長が閾値を超えている
        if queue_length > self.config["scale_up_threshold"]:
            # システムリソースに余裕がある
            if system_load["cpu_percent"] < 80 and system_load["memory_percent"] < 80:
                return True

        return False

    def should_scale_down(self, queue_length: int, current_workers: int) -> bool:
        """スケールダウンすべきか判定"""
        # クールダウン期間中はスケーリングしない
        if datetime.now() - self.last_scale_time < timedelta(
            seconds=self.config["cooldown_period"]
        ):
            return False

        # 最小ワーカー数以下にはしない
        if current_workers <= self.config["min_workers"]:
            return False

        # キュー長が閾値未満
        return queue_length < self.config["scale_down_threshold"]

    def scale_workers(self, worker_type: str, worker_script: str, queue_name: str):
        """ワーカー数を調整"""
        queue_length = self.get_queue_length(queue_name)
        system_load = self.get_system_load()
        current_workers = self.count_running_workers(worker_type)

        # メトリクス記録
        self.metrics["queue_length_history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "queue_length": queue_length,
                "workers": current_workers,
            }
        )
        self.metrics["current_workers"] = current_workers

        # スケールアップ判定
        if (
            self.should_scale_up(queue_length, system_load)
            and current_workers < self.config["max_workers"]
        ):
            # 一度に1つずつ増やす
            worker_id = self.spawn_worker(worker_type, worker_script)
            if worker_id:
                self.metrics["scale_up_count"] += 1
                self.last_scale_time = datetime.now()
                self.logger.info(f"📈 Scaled up to {current_workers + 1} workers")

        # スケールダウン判定
        elif self.should_scale_down(queue_length, current_workers):
            # 最も古いワーカーを終了
            if self.worker_processes:
                oldest_worker = list(self.worker_processes.keys())[0]
                if self.terminate_worker(oldest_worker):
                    self.metrics["scale_down_count"] += 1
                    self.last_scale_time = datetime.now()
                    self.logger.info(f"📉 Scaled down to {current_workers - 1} workers")

    def monitor_and_scale(self, worker_configs: List[Dict]):
        """監視とスケーリングのメインループ"""
        self.connect()
        self.logger.info("🎯 AutoScaling Manager started")

        while not self.stop_event.is_set():
            try:
                for config in worker_configs:
                    self.scale_workers(
                        config["worker_type"],
                        config["worker_script"],
                        config["queue_name"],
                    )

                # 指定された間隔で待機
                self.stop_event.wait(self.config["check_interval"])

            except Exception as e:
                self.logger.error(f"Error in scaling loop: {str(e)}")
                time.sleep(10)

    def stop(self):
        """マネージャーを停止"""
        self.logger.info("Stopping AutoScaling Manager...")
        self.stop_event.set()

        # 全ワーカーを終了
        for worker_id in list(self.worker_processes.keys()):
            self.terminate_worker(worker_id)

        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def get_stats(self) -> Dict:
        """統計情報を取得"""
        return {
            "metrics": self.metrics,
            "config": self.config,
            "last_scale_time": self.last_scale_time.isoformat(),
            "active_workers": list(self.worker_processes.keys()),
        }


class AutoScalableWorker:
    """オートスケーリング対応のワーカーミックスイン"""

    def register_with_scaler(self):
        """スケーラーに自身を登録"""
        # ワーカーIDと起動時刻を記録
        self.scaling_metadata = {
            "worker_id": self.worker_id,
            "start_time": datetime.now(),
            "pid": psutil.Process().pid,
        }

        # グレースフルシャットダウンのシグナルハンドラー設定
        import signal

        signal.signal(signal.SIGTERM, self._handle_termination)

    def _handle_termination(self, signum, frame):
        """終了シグナルのハンドリング"""
        self.logger.info(f"Received termination signal, shutting down gracefully...")
        self.stop()
