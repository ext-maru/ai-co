#!/usr/bin/env python3
"""
Elders Guild システムヘルス統合ダッシュボード
全システムの監視と障害予防
"""
import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SystemAlert:
    """システムアラート"""

    id: str
    type: str  # warning, error, critical
    component: str  # rabbitmq, worker, config, etc
    message: str
    timestamp: datetime
    resolved: bool = False


class SystemHealthDashboard:
    """システムヘルス統合ダッシュボード"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.project_root = Path("/home/aicompany/ai_co")

        # 各監視システムのインスタンス
        self.rabbitmq_monitor = None
        self.worker_recovery = None
        self.config_validator = None

        # アラート管理
        self.active_alerts: Dict[str, SystemAlert] = {}
        self.alert_history: List[SystemAlert] = []
        self.max_history = 1000

        # 統計情報
        self.system_stats = {
            "uptime_start": datetime.now(),
            "total_alerts": 0,
            "resolved_alerts": 0,
            "critical_alerts": 0,
            "last_incident": None,
            "system_score": 100.0,  # 0-100のヘルススコア
        }

        # 監視ルール
        self.monitoring_rules = {
            "rabbitmq_down_threshold": 3,  # 3回連続失敗で危険
            "worker_failure_threshold": 2,  # 2つのワーカー失敗で警告
            "queue_backlog_threshold": 20,  # 20件以上で警告
            "config_error_threshold": 1,  # 設定エラー1件で警告
        }

        # 自動対応設定
        self.auto_response_enabled = True
        self.preventive_actions_enabled = True

    def initialize_monitoring(self):
        """監視システムの初期化"""
        try:
            # RabbitMQ監視
            from libs.rabbitmq_monitor import RabbitMQMonitor

            self.rabbitmq_monitor = RabbitMQMonitor()
            self.rabbitmq_monitor.add_alert_handler(self._handle_rabbitmq_alert)
            self.rabbitmq_monitor.start_monitoring()

            # ワーカー自動復旧
            from libs.worker_auto_recovery import WorkerAutoRecovery

            self.worker_recovery = WorkerAutoRecovery()
            self.worker_recovery.start_monitoring()

            # 設定検証
            from libs.config_validator import ConfigValidator

            self.config_validator = ConfigValidator()

            self.logger.info("🎯 システムヘルス監視を開始しました")

        except Exception as e:
            self.logger.error(f"監視システム初期化に失敗: {e}")

    def start_health_monitoring(self):
        """ヘルス監視開始"""
        self.initialize_monitoring()

        # 定期ヘルスチェックスレッド
        health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        health_thread.start()

        # 予防的メンテナンススレッド
        maintenance_thread = threading.Thread(
            target=self._preventive_maintenance_loop, daemon=True
        )
        maintenance_thread.start()

        self.logger.info("🩺 システムヘルス監視が開始されました")

    def _health_check_loop(self):
        """定期ヘルスチェック"""
        while True:
            try:
                self._perform_health_check()
                self._calculate_system_score()
                self._save_health_log()
                time.sleep(60)  # 1分間隔

            except Exception as e:
                self.logger.error(f"ヘルスチェックでエラー: {e}")
                time.sleep(60)

    def _preventive_maintenance_loop(self):
        """予防的メンテナンス"""
        while True:
            try:
                if self.preventive_actions_enabled:
                    self._perform_preventive_maintenance()
                time.sleep(300)  # 5分間隔

            except Exception as e:
                self.logger.error(f"予防的メンテナンスでエラー: {e}")
                time.sleep(300)

    def _perform_health_check(self):
        """ヘルスチェック実行"""
        # RabbitMQ状態チェック
        if self.rabbitmq_monitor:
            rabbitmq_status = self.rabbitmq_monitor.get_status_report()
            if not rabbitmq_status["connection_status"]["is_connected"]:
                self._create_alert(
                    "critical", "rabbitmq", "RabbitMQ接続が失われています"
                )

        # ワーカー状態チェック
        if self.worker_recovery:
            worker_status = self.worker_recovery.get_system_status()
            unhealthy_workers = worker_status["health_summary"]["unhealthy"]
            if unhealthy_workers >= self.monitoring_rules["worker_failure_threshold"]:
                self._create_alert(
                    "warning",
                    "worker",
                    f"{unhealthy_workers}個のワーカーが異常状態です",
                )

        # 設定チェック
        if self.config_validator:
            config_result = self.config_validator.validate_env_file()
            if not config_result.is_valid:
                self._create_alert("warning", "config", "設定ファイルに問題があります")

        # ディスク容量チェック
        self._check_disk_usage()

        # メモリ使用量チェック
        self._check_memory_usage()

    def _perform_preventive_maintenance(self):
        """予防的メンテナンス実行"""
        try:
            # 古いログファイルのクリーンアップ
            self._cleanup_old_logs()

            # 設定の自動修正
            if self.config_validator:
                result = self.config_validator.auto_fix_config()
                if result.fixed_issues:
                    self.logger.info(f"設定を予防的に修正: {result.fixed_issues}")

            # 失敗したワーカーの自動再起動
            if self.worker_recovery and self.auto_response_enabled:
                restarted = self.worker_recovery.auto_restart_failed_workers()
                if restarted:
                    self.logger.info(f"ワーカーを予防的に再起動: {restarted}")

            # アラートの自動解決チェック
            self._check_alert_resolution()

        except Exception as e:
            self.logger.error(f"予防的メンテナンスでエラー: {e}")

    def _check_disk_usage(self):
        """ディスク使用量チェック"""
        try:
            import shutil

            total, used, free = shutil.disk_usage(self.project_root)
            usage_percent = (used / total) * 100

            if usage_percent > 90:
                self._create_alert(
                    "critical",
                    "disk",
                    f"ディスク使用量が危険レベル: {usage_percent:.1f}%",
                )
            elif usage_percent > 80:
                self._create_alert(
                    "warning", "disk", f"ディスク使用量が高い: {usage_percent:.1f}%"
                )

        except Exception as e:
            self.logger.error(f"ディスクチェックでエラー: {e}")

    def _check_memory_usage(self):
        """メモリ使用量チェック"""
        try:
            import psutil

            memory = psutil.virtual_memory()

            if memory.percent > 90:
                self._create_alert(
                    "critical", "memory", f"メモリ使用量が危険レベル: {memory.percent}%"
                )
            elif memory.percent > 80:
                self._create_alert(
                    "warning", "memory", f"メモリ使用量が高い: {memory.percent}%"
                )

        except Exception as e:
            self.logger.error(f"メモリチェックでエラー: {e}")

    def _cleanup_old_logs(self):
        """古いログファイルのクリーンアップ"""
        try:
            log_dir = self.project_root / "logs"
            if not log_dir.exists():
                return

            cutoff_date = datetime.now() - timedelta(days=7)
            cleaned_files = 0

            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    # 古いログファイルを圧縮または削除
                    if log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB以上
                        log_file.unlink()
                        cleaned_files += 1

            if cleaned_files > 0:
                self.logger.info(
                    f"古いログファイルをクリーンアップ: {cleaned_files}ファイル"
                )

        except Exception as e:
            self.logger.error(f"ログクリーンアップでエラー: {e}")

    def _create_alert(self, alert_type: str, component: str, message: str):
        """アラート作成"""
        alert_id = f"{component}_{int(time.time())}"

        # 同じアラートが既に存在するかチェック
        existing_alert = None
        for alert in self.active_alerts.values():
            if (
                alert.component == component
                and alert.message == message
                and not alert.resolved
            ):
                existing_alert = alert
                break

        if existing_alert:
            return  # 重複アラートは作成しない

        alert = SystemAlert(
            id=alert_id,
            type=alert_type,
            component=component,
            message=message,
            timestamp=datetime.now(),
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.system_stats["total_alerts"] += 1

        if alert_type == "critical":
            self.system_stats["critical_alerts"] += 1
            self.system_stats["last_incident"] = datetime.now()

        # アラート履歴のサイズ管理
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history :]

        self.logger.warning(f"🚨 アラート作成: [{alert_type}] {component} - {message}")

        # 自動対応の実行
        if self.auto_response_enabled:
            self._auto_respond_to_alert(alert)

    def _auto_respond_to_alert(self, alert: SystemAlert):
        """アラートへの自動対応"""
        try:
            if alert.component == "rabbitmq" and alert.type == "critical":
                # RabbitMQ復旧を試行
                self.logger.info("🔧 RabbitMQ自動復旧を実行中...")

            elif alert.component == "worker" and alert.type == "warning":
                # ワーカー再起動を試行
                if self.worker_recovery:
                    restarted = self.worker_recovery.auto_restart_failed_workers()
                    if restarted:
                        self.logger.info(f"🔧 ワーカー自動復旧完了: {restarted}")

            elif alert.component == "config":
                # 設定の自動修正
                if self.config_validator:
                    result = self.config_validator.auto_fix_config()
                    if result.fixed_issues:
                        self.logger.info("🔧 設定自動修正完了")
                        self._resolve_alert(alert.id)

        except Exception as e:
            self.logger.error(f"自動対応でエラー: {e}")

    def _check_alert_resolution(self):
        """アラートの自動解決チェック"""
        for alert_id, alert in list(self.active_alerts.items()):
            if alert.resolved:
                continue

            # 条件に基づいてアラートを解決
            should_resolve = False

            if alert.component == "rabbitmq":
                if self.rabbitmq_monitor:
                    status = self.rabbitmq_monitor.get_status_report()
                    if status["connection_status"]["is_connected"]:
                        should_resolve = True

            elif alert.component == "worker":
                if self.worker_recovery:
                    status = self.worker_recovery.get_system_status()
                    if status["health_summary"]["unhealthy"] == 0:
                        should_resolve = True

            if should_resolve:
                self._resolve_alert(alert_id)

    def _resolve_alert(self, alert_id: str):
        """アラート解決"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            self.system_stats["resolved_alerts"] += 1
            self.logger.info(f"✅ アラート解決: {alert.component} - {alert.message}")

    def _calculate_system_score(self):
        """システムヘルススコア計算"""
        base_score = 100.0

        # アクティブアラートによる減点
        for alert in self.active_alerts.values():
            if not alert.resolved:
                if alert.type == "critical":
                    base_score -= 20
                elif alert.type == "warning":
                    base_score -= 5

        # 最近のインシデント頻度による減点
        recent_incidents = [
            alert
            for alert in self.alert_history
            if alert.type == "critical"
            and alert.timestamp > datetime.now() - timedelta(hours=24)
        ]
        base_score -= len(recent_incidents) * 5

        # 稼働時間による加点
        uptime_hours = (
            datetime.now() - self.system_stats["uptime_start"]
        ).total_seconds() / 3600
        if uptime_hours > 24:
            base_score += min(5, uptime_hours / 24)

        self.system_stats["system_score"] = max(0, min(100, base_score))

    def _save_health_log(self):
        """ヘルスログ保存"""
        log_file = self.project_root / "logs" / "system_health.log"
        log_file.parent.mkdir(exist_ok=True)

        health_data = {
            "timestamp": datetime.now().isoformat(),
            "system_score": self.system_stats["system_score"],
            "active_alerts": len(
                [a for a in self.active_alerts.values() if not a.resolved]
            ),
            "critical_alerts": len(
                [
                    a
                    for a in self.active_alerts.values()
                    if not a.resolved and a.type == "critical"
                ]
            ),
            "total_alerts": self.system_stats["total_alerts"],
            "resolved_alerts": self.system_stats["resolved_alerts"],
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(health_data) + "\n")

    def _handle_rabbitmq_alert(self, alert_type: str, message: str):
        """RabbitMQ監視からのアラートハンドラー"""
        severity = "warning"
        if alert_type in ["connection_lost"]:
            severity = "critical"
        elif alert_type in ["queue_backlog", "consumer_lost"]:
            severity = "warning"

        self._create_alert(severity, "rabbitmq", message)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """ダッシュボード用データ取得"""
        active_alerts = [
            {
                "id": alert.id,
                "type": alert.type,
                "component": alert.component,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
            }
            for alert in self.active_alerts.values()
            if not alert.resolved
        ]

        return {
            "system_score": self.system_stats["system_score"],
            "uptime": (
                datetime.now() - self.system_stats["uptime_start"]
            ).total_seconds(),
            "active_alerts": active_alerts,
            "alert_summary": {
                "total": self.system_stats["total_alerts"],
                "resolved": self.system_stats["resolved_alerts"],
                "active": len(active_alerts),
                "critical": len([a for a in active_alerts if a["type"] == "critical"]),
            },
            "components": {
                "rabbitmq": (
                    self.rabbitmq_monitor.get_status_report()
                    if self.rabbitmq_monitor
                    else None
                ),
                "workers": (
                    self.worker_recovery.get_system_status()
                    if self.worker_recovery
                    else None
                ),
            },
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    dashboard = SystemHealthDashboard()
    dashboard.start_health_monitoring()

    print("🩺 システムヘルスダッシュボードを開始...")

    try:
        while True:
            time.sleep(30)
            data = dashboard.get_dashboard_data()
            print(
                f"🩺 ヘルススコア: {data['system_score']:.1f}, "
                f"アクティブアラート: {data['alert_summary']['active']}"
            )

    except KeyboardInterrupt:
        print("\n🩺 ダッシュボードを停止します...")
