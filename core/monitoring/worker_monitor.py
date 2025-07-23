#!/usr/bin/env python3
"""
Worker Monitor - ワーカーとシステムの監視
"""
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

import pika
import psutil

logger = logging.getLogger("WorkerMonitor")


class WorkerMonitor:
    def __init__(self, config_file=None):
        """ワーカー監視システムの初期化"""
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "scaling.conf"
        self.config = self._load_config(config_file)
        self.rabbitmq_host = "localhost"

    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        config = {}
        try:
            with open(config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        # 数値として解析を試みる
                        try:
                            config[key] = int(value)
                        except ValueError:
                            config[key] = value
            logger.info(f"設定読み込み完了: {config}")
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
        return config

    def get_queue_length(self, queue_name="task_queue"):
        """RabbitMQキューの長さを取得"""
        try:
            # rabbitmqctlを使用してキュー情報取得
            cmd = [
                "sudo",
                "rabbitmqctl",
                "list_queues",
                "name",
                "messages",
                "--formatter",
                "json",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                queues = json.loads(result.stdout)
                for queue in queues:
                    if queue["name"] == queue_name:
                        return queue["messages"]
            return 0
        except Exception as e:
            logger.error(f"キュー長取得エラー: {e}")
            return 0

    def get_active_workers(self):
        """稼働中のTaskWorkerプロセス情報を取得"""
        workers = []
        try:
            # psを使って task_worker.py プロセスを探す
            cmd = ["ps", "aux"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            # 繰り返し処理
            for line in result.stdout.split("\n"):
                if "task_worker.py" in line and "worker-" in line:
                    parts = line.split()
                    if len(parts) > 10:
                        # worker IDを抽出
                        worker_id = None
                        for part in parts:
                            if part.startswith("worker-"):
                                worker_id = part
                                break

                        if worker_id:
                            workers.append(
                                {
                                    "pid": int(parts[1]),
                                    "cpu": float(parts[2]),
                                    "mem": float(parts[3]),
                                    "worker_id": worker_id,
                                    "start_time": " ".join(parts[8:10]),
                                }
                            )
        except Exception as e:
            logger.error(f"ワーカー情報取得エラー: {e}")

        return workers

    def get_system_metrics(self):
        """システムメトリクス（CPU、メモリ使用率）を取得"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "load_average": psutil.getloadavg()[0],  # 1分間の負荷平均
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"システムメトリクス取得エラー: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "load_average": 0,
                "timestamp": datetime.now().isoformat(),
            }

    def get_worker_health(self, worker_id):
        """特定ワーカーの健康状態を確認"""
        workers = self.get_active_workers()
        for worker in workers:
            if worker["worker_id"] == worker_id:
                # CPU使用率が異常に高い、またはメモリ使用率が高い場合は不健康
                is_healthy = worker["cpu"] < 90 and worker["mem"] < 90
                return {
                    "worker_id": worker_id,
                    "pid": worker["pid"],
                    "healthy": is_healthy,
                    "cpu": worker["cpu"],
                    "mem": worker["mem"],
                }
        return None

    def get_all_metrics(self):
        """全ての監視メトリクスを統合して返す"""
        workers = self.get_active_workers()
        return {
            "queue_length": self.get_queue_length(),
            "active_workers": len(workers),
            "worker_details": workers,
            "system": self.get_system_metrics(),
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    monitor = WorkerMonitor()

    print("=== Worker Monitor Test ===")
    metrics = monitor.get_all_metrics()
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
