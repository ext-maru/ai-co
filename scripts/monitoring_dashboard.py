#!/usr/bin/env python3
"""
Elders Guild 監視ダッシュボード
リアルタイムメトリクス表示と アラート機能
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import psutil

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.lightweight_logger import get_logger


class MonitoringDashboard:
    """監視ダッシュボードクラス"""

    def __init__(self):
        self.logger = get_logger("monitoring_dashboard")
        self.project_root = PROJECT_ROOT

        # アラート設定
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "queue_length": 1000,
            "error_rate": 5.0,  # %
            "response_time": 30.0,  # seconds
        }

        # メトリクス履歴
        self.metrics_history = {
            "timestamps": [],
            "cpu": [],
            "memory": [],
            "disk": [],
            "worker_counts": [],
            "queue_sizes": [],
        }

        # アラート履歴
        self.alerts = []

        # 最大履歴件数
        self.max_history = 1000

    def collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # ネットワーク統計
            network = psutil.net_io_counters()

            # プロセス統計
            process_count = len(psutil.pids())

            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                },
                "processes": {"total": process_count},
            }

            return metrics

        except Exception as e:
            self.logger.error("Failed to collect system metrics", error=str(e))
            return {}

    def collect_worker_metrics(self) -> Dict[str, Any]:
        """ワーカーメトリクス収集"""
        try:
            # ワーカープロセスの検出
            worker_processes = {}

            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "cpu_percent", "memory_info"]
            ):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])

                    # Elders Guildワーカーの検出
                    if "worker" in cmdline and "python" in cmdline:
                        worker_name = "unknown"

                        if not ("task_worker" in cmdline):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if "task_worker" in cmdline:
                            worker_name = "task_worker"
                        elif "pm_worker" in cmdline:
                            worker_name = "pm_worker"
                        elif "result_worker" in cmdline:
                            worker_name = "result_worker"
                        elif "async" in cmdline:
                            if not ("task" in cmdline):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if "task" in cmdline:
                                worker_name = "async_task_worker"
                            elif "result" in cmdline:
                                worker_name = "async_result_worker"
                            elif "pm" in cmdline:
                                worker_name = "async_pm_worker"

                        if not (worker_name not in worker_processes):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if worker_name not in worker_processes:
                            worker_processes[worker_name] = []

                        worker_processes[worker_name].append(
                            {
                                "pid": proc.info["pid"],
                                "cpu_percent": proc.info["cpu_percent"],
                                "memory_mb": proc.info["memory_info"].rss / 1024 / 1024,
                            }
                        )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # ワーカー統計の計算
            worker_stats = {}
            for worker_name, processes in worker_processes.items():
                worker_stats[worker_name] = {
                    "process_count": len(processes),
                    "total_cpu_percent": sum(p["cpu_percent"] for p in processes),
                    "total_memory_mb": sum(p["memory_mb"] for p in processes),
                    "avg_cpu_percent": (
                        sum(p["cpu_percent"] for p in processes) / len(processes)
                        if processes
                        else 0
                    ),
                    "avg_memory_mb": (
                        sum(p["memory_mb"] for p in processes) / len(processes)
                        if processes
                        else 0
                    ),
                    "processes": processes,
                }

            return worker_stats

        except Exception as e:
            self.logger.error("Failed to collect worker metrics", error=str(e))
            return {}

    def collect_queue_metrics(self) -> Dict[str, Any]:
        """キューメトリクス収集（シミュレーション）"""
        # 実際の実装では RabbitMQ Management API を使用
        try:
            # シミュレーション用のダミーデータ
            import random

            queues = ["ai_tasks", "ai_pm", "ai_results", "worker_tasks", "dialog_tasks"]
            queue_stats = {}

            for queue in queues:
                # ランダムなキューサイズ（実際の実装では API 呼び出し）
                size = random.randint(0, 50)
                rate = random.uniform(0, 10)

                queue_stats[queue] = {
                    "messages": size,
                    "consumers": random.randint(0, 3),
                    "message_rate": rate,
                    "publish_rate": rate * 1.1,
                    "consume_rate": rate * 0.9,
                }

            return queue_stats

        except Exception as e:
            self.logger.error("Failed to collect queue metrics", error=str(e))
            return {}

    def check_alerts(
        self, system_metrics: Dict, worker_metrics: Dict, queue_metrics: Dict
    ):
        """アラートチェック"""
        current_time = datetime.utcnow()
        new_alerts = []

        # CPU使用率チェック
        if (
            system_metrics.get("cpu", {}).get("percent", 0)
            > self.alert_thresholds["cpu_percent"]
        ):
            new_alerts.append(
                {
                    "type": "cpu_high",
                    "severity": "warning",
                    "message": f"High CPU usage: {system_metrics['cpu']['percent']:.1f}%",
                    "value": system_metrics["cpu"]["percent"],
                    "threshold": self.alert_thresholds["cpu_percent"],
                    "timestamp": current_time.isoformat(),
                }
            )

        # メモリ使用率チェック
        if (
            system_metrics.get("memory", {}).get("percent", 0)
            > self.alert_thresholds["memory_percent"]
        ):
            new_alerts.append(
                {
                    "type": "memory_high",
                    "severity": "warning",
                    "message": f"High memory usage: {system_metrics['memory']['percent']:.1f}%",
                    "value": system_metrics["memory"]["percent"],
                    "threshold": self.alert_thresholds["memory_percent"],
                    "timestamp": current_time.isoformat(),
                }
            )

        # ディスク使用率チェック
        if (
            system_metrics.get("disk", {}).get("percent", 0)
            > self.alert_thresholds["disk_percent"]
        ):
            new_alerts.append(
                {
                    "type": "disk_high",
                    "severity": "critical",
                    "message": f"High disk usage: {system_metrics['disk']['percent']:.1f}%",
                    "value": system_metrics["disk"]["percent"],
                    "threshold": self.alert_thresholds["disk_percent"],
                    "timestamp": current_time.isoformat(),
                }
            )

        # ワーカー停止チェック
        expected_workers = ["task_worker", "pm_worker", "result_worker"]
        for worker in expected_workers:
            if (
                worker not in worker_metrics
                or worker_metrics[worker]["process_count"] == 0
            ):
                new_alerts.append(
                    {
                        "type": "worker_down",
                        "severity": "critical",
                        "message": f"Worker {worker} is not running",
                        "worker": worker,
                        "timestamp": current_time.isoformat(),
                    }
                )

        # キュー長チェック
        for queue_name, stats in queue_metrics.items():
            if stats.get("messages", 0) > self.alert_thresholds["queue_length"]:
                new_alerts.append(
                    {
                        "type": "queue_backlog",
                        "severity": "warning",
                        "message": f"Queue {queue_name} has {stats['messages']} messages",
                        "queue": queue_name,
                        "value": stats["messages"],
                        "threshold": self.alert_thresholds["queue_length"],
                        "timestamp": current_time.isoformat(),
                    }
                )

        # 新しいアラートを履歴に追加
        self.alerts.extend(new_alerts)

        # 古いアラートを削除（24時間以上前）
        cutoff_time = current_time - timedelta(hours=24)
        self.alerts = [
            alert
            for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]

        # アラートログ
        for alert in new_alerts:
            alert_data = alert.copy()
            alert_message = alert_data.pop("message", "Alert triggered")
            self.logger.warning(alert_message, **alert_data)

        return new_alerts

    def update_metrics_history(self, system_metrics: Dict, worker_metrics: Dict):
        """メトリクス履歴の更新"""
        current_time = datetime.utcnow()

        # タイムスタンプ追加
        self.metrics_history["timestamps"].append(current_time.isoformat())

        # システムメトリクス追加
        self.metrics_history["cpu"].append(
            system_metrics.get("cpu", {}).get("percent", 0)
        )
        self.metrics_history["memory"].append(
            system_metrics.get("memory", {}).get("percent", 0)
        )
        self.metrics_history["disk"].append(
            system_metrics.get("disk", {}).get("percent", 0)
        )

        # ワーカー数追加
        total_workers = sum(
            stats.get("process_count", 0) for stats in worker_metrics.values()
        )
        self.metrics_history["worker_counts"].append(total_workers)

        # 履歴サイズの制限
        for key in self.metrics_history:
            if len(self.metrics_history[key]) > self.max_history:
                self.metrics_history[key] = self.metrics_history[key][
                    -self.max_history :
                ]

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """ダッシュボード用データ生成"""
        system_metrics = self.collect_system_metrics()
        worker_metrics = self.collect_worker_metrics()
        queue_metrics = self.collect_queue_metrics()

        # アラートチェック
        new_alerts = self.check_alerts(system_metrics, worker_metrics, queue_metrics)

        # 履歴更新
        self.update_metrics_history(system_metrics, worker_metrics)

        # ダッシュボードデータ
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics,
            "workers": worker_metrics,
            "queues": queue_metrics,
            "alerts": {
                "active": [
                    a
                    for a in self.alerts
                    if a["timestamp"]
                    > (datetime.utcnow() - timedelta(hours=1)).isoformat()
                ],
                "recent": new_alerts,
                "total_count": len(self.alerts),
            },
            "history": {
                "last_24h": {
                    "timestamps": self.metrics_history["timestamps"][
                        -144:
                    ],  # 10分間隔で24時間
                    "cpu": self.metrics_history["cpu"][-144:],
                    "memory": self.metrics_history["memory"][-144:],
                    "worker_counts": self.metrics_history["worker_counts"][-144:],
                }
            },
            "summary": {
                "total_workers": sum(
                    stats.get("process_count", 0) for stats in worker_metrics.values()
                ),
                "active_alerts": len(
                    [
                        a
                        for a in self.alerts
                        if a["timestamp"]
                        > (datetime.utcnow() - timedelta(hours=1)).isoformat()
                    ]
                ),
                "system_health": (
                    "healthy"
                    if not new_alerts
                    else (
                        "warning"
                        if any(a["severity"] == "warning" for a in new_alerts)
                        else "critical"
                    )
                ),
            },
        }

        return dashboard_data

    def print_dashboard(self, data: Dict[str, Any]):
        """コンソールダッシュボード表示"""
        print("\n" + "=" * 80)
        print("🖥️  Elders Guild Monitoring Dashboard")
        print("=" * 80)
        print(f"📅 Time: {data['timestamp']}")
        print(f"🏥 Health: {data['summary']['system_health'].upper()}")

        # システム状態
        print(f"\n📊 System Metrics:")
        if "system" in data:
            sys_data = data["system"]
            print(f"  💻 CPU: {sys_data.get('cpu', {}).get('percent', 0):.1f}%")
            print(f"  🧠 Memory: {sys_data.get('memory', {}).get('percent', 0):.1f}%")
            print(f"  💾 Disk: {sys_data.get('disk', {}).get('percent', 0):.1f}%")

        # ワーカー状態
        print(f"\n👷 Workers ({data['summary']['total_workers']} total):")
        for worker_name, stats in data.get("workers", {}).items():
            status = "🟢" if stats["process_count"] > 0 else "🔴"
            print(
                f"  {status} {worker_name}: {stats['process_count']} processes, "
                f"CPU {stats['avg_cpu_percent']:.1f}%, "
                f"Memory {stats['avg_memory_mb']:.1f}MB"
            )

        # キュー状態
        print(f"\n📬 Queues:")
        for queue_name, stats in data.get("queues", {}).items():
            status = "⚠️" if stats["messages"] > 100 else "✅"
            print(
                f"  {status} {queue_name}: {stats['messages']} messages, "
                f"{stats['consumers']} consumers"
            )

        # アラート
        active_alerts = data.get("alerts", {}).get("active", [])
        if active_alerts:
            print(f"\n🚨 Active Alerts ({len(active_alerts)}):")
            for alert in active_alerts[-5:]:  # 最新5件
                severity_icon = {"critical": "🔴", "warning": "⚠️", "info": "ℹ️"}.get(
                    alert["severity"], "❓"
                )
                print(f"  {severity_icon} {alert['message']}")
        else:
            print(f"\n✅ No active alerts")

        print("=" * 80)

    async def run_monitoring_loop(self, interval: int = 60):
        """監視ループの実行"""
        self.logger.info("Starting monitoring loop", interval=interval)

        try:
            while True:
                dashboard_data = self.generate_dashboard_data()
                self.print_dashboard(dashboard_data)

                # データの保存
                data_file = self.project_root / "data" / "monitoring_data.json"
                data_file.parent.mkdir(exist_ok=True)

                with open(data_file, "w") as f:
                    json.dump(dashboard_data, f, indent=2)

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error("Monitoring loop error", error=str(e))


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Elders Guild Monitoring Dashboard")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds (default: 60)",
    )
    parser.add_argument("--once", action="store_true", help="Run once and exit")

    args = parser.parse_args()

    dashboard = MonitoringDashboard()

    if args.once:
        # 一回だけ実行
        data = dashboard.generate_dashboard_data()
        dashboard.print_dashboard(data)

        # データファイルの保存
        data_file = Path(__file__).parent.parent / "data" / "monitoring_data.json"
        data_file.parent.mkdir(exist_ok=True)

        with open(data_file, "w") as f:
            import json

            json.dump(data, f, indent=2)
    else:
        # 継続監視
        try:
            asyncio.run(dashboard.run_monitoring_loop(args.interval))
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")


if __name__ == "__main__":
    main()
