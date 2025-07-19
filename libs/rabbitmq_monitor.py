#!/usr/bin/env python3
"""
Elders Guild RabbitMQ 常時監視システム
接続状態の監視と自動復旧
"""
import asyncio
import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional

import pika


@dataclass
class ConnectionStatus:
    """接続状態"""

    is_connected: bool
    last_check: datetime
    error_message: Optional[str]
    consecutive_failures: int
    last_success: Optional[datetime]


@dataclass
class QueueInfo:
    """キュー情報"""

    name: str
    message_count: int
    consumer_count: int
    last_updated: datetime


class RabbitMQMonitor:
    """RabbitMQ 監視システム"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_root = Path("/home/aicompany/ai_co")

        # 監視設定
        self.check_interval = 5  # 5秒間隔
        self.failure_threshold = 3  # 3回連続失敗で警告
        self.auto_recovery_enabled = True

        # 状態管理
        self.connection_status = ConnectionStatus(
            is_connected=False,
            last_check=datetime.now(),
            error_message=None,
            consecutive_failures=0,
            last_success=None,
        )

        self.queue_info: Dict[str, QueueInfo] = {}
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # 重要キューのリスト
        self.critical_queues = [
            "ai_tasks",
            "ai_pm",
            "ai_results",
            "dialog_task_queue",
            "user_input_queue",
        ]

        # アラートハンドラー
        self.alert_handlers: List[Callable] = []

        # 統計情報
        self.stats = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "last_downtime": None,
            "total_downtime": timedelta(0),
        }

    def start_monitoring(self):
        """監視開始"""
        if self.monitoring:
            self.logger.warning("監視は既に開始されています")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("🔍 RabbitMQ監視を開始しました")

    def stop_monitoring(self):
        """監視停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        self.logger.info("🔍 RabbitMQ監視を停止しました")

    def _monitor_loop(self):
        """監視ループ"""
        while self.monitoring:
            try:
                self._check_connection()
                self._check_queues()
                self._update_stats()

                # 異常検知時の処理
                if (
                    self.connection_status.consecutive_failures
                    >= self.failure_threshold
                ):
                    self._handle_connection_failure()

                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"監視ループでエラー: {e}")
                time.sleep(self.check_interval)

    def _check_connection(self):
        """接続チェック"""
        self.stats["total_checks"] += 1

        try:
            # 環境変数から接続情報を取得
            connection_params = self._get_connection_params()
            connection = pika.BlockingConnection(connection_params)
            connection.close()

            # 成功時の処理
            was_down = not self.connection_status.is_connected
            self.connection_status.is_connected = True
            self.connection_status.last_check = datetime.now()
            self.connection_status.error_message = None
            self.connection_status.consecutive_failures = 0
            self.connection_status.last_success = datetime.now()

            self.stats["successful_checks"] += 1

            if was_down:
                self.logger.info("✅ RabbitMQ接続復旧")
                self._trigger_alerts("recovery", "RabbitMQ接続が復旧しました")

        except Exception as e:
            # 失敗時の処理
            was_up = self.connection_status.is_connected
            self.connection_status.is_connected = False
            self.connection_status.last_check = datetime.now()
            self.connection_status.error_message = str(e)
            self.connection_status.consecutive_failures += 1

            self.stats["failed_checks"] += 1

            if was_up:
                self.stats["last_downtime"] = datetime.now()
                self.logger.error(f"❌ RabbitMQ接続失敗: {e}")
                self._trigger_alerts("connection_lost", f"RabbitMQ接続失敗: {e}")

    def _check_queues(self):
        """キュー状態チェック"""
        if not self.connection_status.is_connected:
            return

        try:
            connection_params = self._get_connection_params()
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()

            for queue_name in self.critical_queues:
                try:
                    method = channel.queue_declare(queue=queue_name, passive=True)
                    queue_info = QueueInfo(
                        name=queue_name,
                        message_count=method.method.message_count,
                        consumer_count=method.method.consumer_count,
                        last_updated=datetime.now(),
                    )

                    # 前回の情報と比較
                    if queue_name in self.queue_info:
                        prev_info = self.queue_info[queue_name]

                        # メッセージ蓄積の警告
                        if (
                            queue_info.message_count > 10
                            and queue_info.consumer_count == 0
                        ):
                            self._trigger_alerts(
                                "queue_backlog",
                                f"キュー{queue_name}にメッセージが蓄積中: {queue_info.message_count}件",
                            )

                        # コンシューマー減少の警告
                        if queue_info.consumer_count < prev_info.consumer_count:
                            self._trigger_alerts(
                                "consumer_lost",
                                f"キュー{queue_name}のコンシューマーが減少: {queue_info.consumer_count}",
                            )

                    self.queue_info[queue_name] = queue_info

                except Exception as e:
                    self.logger.warning(f"キュー{queue_name}のチェックに失敗: {e}")

            connection.close()

        except Exception as e:
            self.logger.error(f"キューチェックでエラー: {e}")

    def _handle_connection_failure(self):
        """接続失敗時の処理"""
        if not self.auto_recovery_enabled:
            return

        self.logger.warning("🔧 自動復旧を試行します")

        try:
            # 設定検証
            from libs.config_validator import ConfigValidator

            validator = ConfigValidator()
            result = validator.auto_fix_config()

            if result.fixed_issues:
                self.logger.info("設定の自動修正を実行しました")
                self._trigger_alerts("auto_fix", f"設定を自動修正: {result.fixed_issues}")

            # RabbitMQサービス再起動（権限があれば）
            self._restart_rabbitmq_service()

        except Exception as e:
            self.logger.error(f"自動復旧に失敗: {e}")

    def _restart_rabbitmq_service(self):
        """RabbitMQサービス再起動"""
        try:
            import subprocess

            result = subprocess.run(
                ["sudo", "systemctl", "restart", "rabbitmq-server"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self.logger.info("RabbitMQサービスを再起動しました")
                self._trigger_alerts("service_restart", "RabbitMQサービスを再起動しました")
            else:
                self.logger.error(f"RabbitMQ再起動に失敗: {result.stderr}")
        except Exception as e:
            self.logger.error(f"RabbitMQ再起動でエラー: {e}")

    def _get_connection_params(self):
        """接続パラメータ取得"""
        # 環境変数から取得
        import os

        host = os.getenv("RABBITMQ_HOST", "localhost")
        port = int(os.getenv("RABBITMQ_PORT", "5672"))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASS", "guest")

        return pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=pika.PlainCredentials(user, password),
            heartbeat=600,
            blocked_connection_timeout=300,
        )

    def _update_stats(self):
        """統計情報更新"""
        if self.stats["last_downtime"] and not self.connection_status.is_connected:
            # ダウンタイム計算
            downtime = datetime.now() - self.stats["last_downtime"]
            self.stats["total_downtime"] += downtime
            self.stats["last_downtime"] = datetime.now()

    def _trigger_alerts(self, alert_type: str, message: str):
        """アラート発火"""
        for handler in self.alert_handlers:
            try:
                handler(alert_type, message)
            except Exception as e:
                self.logger.error(f"アラートハンドラーでエラー: {e}")

    def add_alert_handler(self, handler: Callable):
        """アラートハンドラー追加"""
        self.alert_handlers.append(handler)

    def get_status_report(self) -> Dict:
        """状態レポート取得"""
        return {
            "connection_status": {
                "is_connected": self.connection_status.is_connected,
                "last_check": self.connection_status.last_check.isoformat(),
                "consecutive_failures": self.connection_status.consecutive_failures,
                "error_message": self.connection_status.error_message,
            },
            "queue_info": {
                name: {
                    "message_count": info.message_count,
                    "consumer_count": info.consumer_count,
                    "last_updated": info.last_updated.isoformat(),
                }
                for name, info in self.queue_info.items()
            },
            "statistics": {
                "total_checks": self.stats["total_checks"],
                "success_rate": (
                    self.stats["successful_checks"] / max(1, self.stats["total_checks"])
                )
                * 100,
                "total_downtime_seconds": self.stats["total_downtime"].total_seconds(),
            },
        }

    def save_status_log(self):
        """状態ログ保存"""
        log_file = self.project_root / "logs" / "rabbitmq_monitor.log"
        log_file.parent.mkdir(exist_ok=True)

        status = self.get_status_report()

        with open(log_file, "a") as f:
            log_entry = {"timestamp": datetime.now().isoformat(), "status": status}
            f.write(json.dumps(log_entry) + "\n")


def create_slack_alert_handler():
    """Slack通知ハンドラー作成"""

    def slack_handler(alert_type: str, message: str):
        try:
            from libs.slack_notifier import SlackNotifier

            notifier = SlackNotifier()

            emoji_map = {
                "connection_lost": "🚨",
                "recovery": "✅",
                "queue_backlog": "⚠️",
                "consumer_lost": "📉",
                "auto_fix": "🔧",
                "service_restart": "🔄",
            }

            emoji = emoji_map.get(alert_type, "ℹ️")
            notifier.send_message(f"{emoji} RabbitMQ監視: {message}")

        except Exception as e:
            logging.getLogger(__name__).error(f"Slack通知に失敗: {e}")

    return slack_handler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    monitor = RabbitMQMonitor()

    # Slack通知を追加
    monitor.add_alert_handler(create_slack_alert_handler())

    print("🔍 RabbitMQ監視を開始...")
    monitor.start_monitoring()

    try:
        while True:
            # 定期的にレポート表示
            time.sleep(30)
            status = monitor.get_status_report()
            print(
                f"🔍 監視状況: 接続={status['connection_status']['is_connected']}, "
                f"成功率={status['statistics']['success_rate']:.1f}%"
            )

            # ログ保存
            monitor.save_status_log()

    except KeyboardInterrupt:
        print("\n🔍 監視を停止します...")
        monitor.stop_monitoring()
