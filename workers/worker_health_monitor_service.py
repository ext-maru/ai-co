#!/usr/bin/env python3
"""
🌳 Elder Tree Integrated Worker Health Monitor Service
ワーカーヘルス監視サービス - Elders Guild統合版

Elders Guild Integration:
- 🌟 Grand Elder maru oversight
- 🤖 Claude Elder execution guidance
- 🧙‍♂️ Four Sages wisdom consultation
- 🏛️ Elder Council decision support
- ⚔️ Elder Servants coordination

Part of the Elder Tree Hierarchy for comprehensive system monitoring
"""
import signal
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import EMOJI, setup_logging
from libs.slack_notifier import SlackNotifier
from libs.worker_health_monitor import (
    WorkerAutoScaler,
    WorkerHealthMonitor,
    WorkerPerformanceAnalyzer,
)

# Elder Tree Integration imports
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import ElderMessage, ElderRank, get_elder_tree
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_TREE_AVAILABLE = True
except ImportError as e:
    # Handle specific exception case
    import logging

    logging.warning(f"Elder Tree integration not available: {e}")
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None
    ElderMessage = None
    ElderRank = None
    ELDER_TREE_AVAILABLE = False


class WorkerHealthMonitorService:
    """ワーカーヘルス監視サービス"""

    def __init__(self):
        """🌳 Elder Tree統合版サービスの初期化"""
        self.logger = setup_logging(
            name="WorkerHealthMonitorService",
            log_file=PROJECT_ROOT / "logs" / "worker_health_monitor.log",
        )

        # コンポーネント初期化
        self.health_monitor = WorkerHealthMonitor()
        self.performance_analyzer = WorkerPerformanceAnalyzer()
        self.auto_scaler = WorkerAutoScaler()
        self.slack = SlackNotifier()

        # Elder Tree Integration
        self.elder_tree = None
        self.four_sages = None
        self.elder_council_summoner = None
        self.elder_integration_enabled = False

        # Initialize Elder systems with error handling
        self._initialize_elder_systems()

        # 設定
        self.running = True
        self.check_interval = 30  # 30秒間隔
        self.performance_check_interval = 300  # 5分間隔
        self.scaling_check_interval = 600  # 10分間隔

        # 最後のチェック時刻
        self.last_performance_check = datetime.now()
        self.last_scaling_check = datetime.now()

        # メトリクス履歴
        self.metrics_history = []
        self.max_history_length = 1000

    def _initialize_elder_systems(self):
        """Elder Tree システムの初期化（エラー処理付き）"""
        try:
            # Elder Tree Hierarchy initialization
            if get_elder_tree:
                self.elder_tree = get_elder_tree()
                self.logger.info("🌳 Elder Tree Hierarchy connected")

            # Four Sages Integration
            if FourSagesIntegration:
                self.four_sages = FourSagesIntegration()
                self.logger.info("🧙‍♂️ Four Sages Integration activated")

            # Elder Council Summoner
            if ElderCouncilSummoner:
                self.elder_council_summoner = ElderCouncilSummoner()
                self.logger.info("🏛️ Elder Council Summoner initialized")

            # Enable integration if all systems are available
            if all([self.elder_tree, self.four_sages, self.elder_council_summoner]):
                self.elder_integration_enabled = True
                self.logger.info(
                    "✅ Full Elder Tree Integration enabled for health monitoring"
                )
            else:
                self.logger.warning(
                    "⚠️ Partial Elder Tree Integration - some systems unavailable"
                )

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Elder Tree initialization failed: {e}")
            self.elder_integration_enabled = False

    def run(self):
        """🌳 Elder Tree統合版メインサービスループ"""
        self.logger.info(
            f"{EMOJI['start']} Elder Tree Integrated Worker Health Monitor Service started"
        )

        # Report initial Elder integration status
        if self.elder_integration_enabled:
            self._report_elder_status_to_incident_sage(
                {
                    "type": "service_startup",
                    "service": "worker_health_monitor",
                    "elder_integration": True,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # シグナルハンドラ設定
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        try:
            while self.running:
                self._perform_health_checks()

                # パフォーマンスチェック
                if self._should_perform_performance_check():
                    self._perform_performance_analysis()
                    self.last_performance_check = datetime.now()

                # スケーリングチェック
                if self._should_perform_scaling_check():
                    self._perform_scaling_analysis()
                    self.last_scaling_check = datetime.now()

                time.sleep(self.check_interval)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} Service error: {str(e)}")
            self._send_critical_alert("Service error", str(e))
        finally:
            self.logger.info(f"{EMOJI['stop']} Worker Health Monitor Service stopped")

    def _handle_signal(self, signum, frame):
        """シグナルハンドラ"""
        self.logger.info(f"{EMOJI['stop']} Received signal {signum}, shutting down...")
        self.running = False

    def _perform_health_checks(self):
        """ヘルスチェック実行"""
        try:
            # 包括的メトリクス収集
            metrics = self.health_monitor.collect_comprehensive_metrics()

            # メトリクス履歴に追加
            self._add_to_history(metrics)

            # 健全性評価
            overall_healthy = metrics["system_health"]["overall_healthy"]

            if not overall_healthy:
                self.logger.warning(f"{EMOJI['warning']} System health degraded")
                self._handle_unhealthy_system(metrics)
            else:
                self.logger.debug(f"{EMOJI['success']} System health OK")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} Health check failed: {str(e)}")

    def _perform_performance_analysis(self):
        """パフォーマンス分析実行"""
        try:
            self.logger.info(f"{EMOJI['monitor']} Performing performance analysis")

            # 最近のメトリクスを取得
            recent_metrics = self._get_recent_metrics(minutes=30)

            if not recent_metrics:
                return

            # ボトルネック検出
            worker_metrics = self._extract_worker_metrics(recent_metrics)
            bottlenecks = self.performance_analyzer.detect_bottlenecks(worker_metrics)

            if bottlenecks:
                self.logger.warning(
                    f"{EMOJI['warning']} Performance bottlenecks detected: {list(bottlenecks.keys())}"
                )
                self._handle_performance_issues(bottlenecks)

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} Performance analysis failed: {str(e)}")

    def _perform_scaling_analysis(self):
        """スケーリング分析実行（エラー耐性強化）"""
        try:
            self.logger.info(f"{EMOJI['scaling']} Performing scaling analysis")

            # WorkerHealthMonitor が不完全な場合の対策
            if not hasattr(self.health_monitor, "collect_comprehensive_metrics"):
                self.logger.warning(
                    "Scaling analysis skipped - collect_comprehensive_metrics not implemented"
                )
                return

            if not hasattr(self.health_monitor, "get_scaling_recommendations"):
                self.logger.warning(
                    "Scaling analysis skipped - get_scaling_recommendations not implemented"
                )
                return

            # 現在のシステムメトリクス
            current_metrics = self.health_monitor.collect_comprehensive_metrics()

            # スケーリング推奨取得
            system_metrics = {
                "queue_lengths": {"task_queue": 50, "pm_queue": 10},  # 実際にはキューから取得
                "worker_counts": {"task_worker": 2, "pm_worker": 1},
                "avg_processing_times": {"task_worker": 2000, "pm_worker": 1500},
                "system_load": 0.6,
            }

            recommendations = self.health_monitor.get_scaling_recommendations(
                system_metrics
            )

            if recommendations:
                self.logger.info(
                    f"{EMOJI['scaling']} Scaling recommendations: {recommendations}"
                )
                self._handle_scaling_recommendations(recommendations)

        except AttributeError as e:
            # Handle specific exception case
            self.logger.warning(
                f"{EMOJI['warning']} Scaling feature not available: {e}"
            )
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"{EMOJI['error']} Scaling analysis failed: {str(e)}")

    def _handle_unhealthy_system(self, metrics: Dict[str, Any]):
        """🌳 Elder Tree統合版不健全システムの対処"""
        unhealthy_workers = []

        for worker_name, worker_metrics in metrics.get("workers", {}).items():
            # Process each item in collection
            if worker_metrics.get("status") != "running":
                unhealthy_workers.append(worker_name)

        if unhealthy_workers:
            self.logger.warning(
                f"{EMOJI['warning']} Unhealthy workers: {unhealthy_workers}"
            )

            # Report to Incident Sage before taking action
            if self.elder_integration_enabled:
                self._report_elder_status_to_incident_sage(
                    {
                        "type": "unhealthy_workers_detected",
                        "unhealthy_workers": unhealthy_workers,
                        "total_unhealthy": len(unhealthy_workers),
                        "metrics": metrics,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # 自動再起動試行
            restart_results = self.health_monitor.restart_unhealthy_workers()

            # 結果をログ出力
            for result in restart_results:
                if result.get("success"):
                    self.logger.info(
                        f"{EMOJI['success']} Worker restarted successfully"
                    )

                    # Report successful restart to Knowledge Sage
                    if self.elder_integration_enabled:
                        self._report_to_knowledge_sage(
                            {
                                "type": "worker_restart_success",
                                "restart_result": result,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                else:
                    self.logger.error(
                        f"{EMOJI['error']} Worker restart failed: {result.get('error')}"
                    )

                    # Escalate critical failure to Incident Sage
                    if self.elder_integration_enabled:
                        self._escalate_to_incident_sage(
                            {
                                "type": "worker_restart_failure",
                                "error": result.get("error"),
                                "worker_data": result,
                                "severity": "critical",
                            }
                        )

                    # クリティカルアラート送信
                    self._send_critical_alert(
                        f"Worker restart failed", f"Failed to restart worker: {result}"
                    )

    def _handle_performance_issues(self, bottlenecks: Dict[str, Any]):
        """パフォーマンス問題の対処"""
        for worker_name, issue in bottlenecks.items():
            # Process each item in collection
            issue_type = issue.get("type")

            if issue_type == "queue_overload":
                self._send_performance_alert(worker_name, "Queue overload detected")
            elif issue_type == "slow_processing":
                self._send_performance_alert(worker_name, "Slow processing detected")
            elif issue_type == "high_error_rate":
                self._send_critical_alert(worker_name, "High error rate detected")

    def _handle_scaling_recommendations(self, recommendations: Dict[str, Any]):
        """スケーリング推奨の対処"""
        for worker_name, rec in recommendations.items():
            # Process each item in collection
            action = rec.get("action")
            current_count = rec.get("current_count", 1)
            recommended_count = rec.get("recommended_count", 1)

            if action == "scale_up":
                self.logger.info(
                    f"{EMOJI['scaling']} Recommending scale up for {worker_name}: {current_count} → {recommended_count}"
                )
                self._send_scaling_alert(
                    worker_name,
                    f"Scale up recommended: {current_count} → {recommended_count}",
                )
            elif action == "scale_down":
                self.logger.info(
                    (
                        f"f"{EMOJI['scaling']} Recommending scale down for {worker_name}: {current_count} → "
                        f"{recommended_count}""
                    )
                )

    def _should_perform_performance_check(self) -> bool:
        """パフォーマンスチェック実行タイミング判定"""
        return (
            datetime.now() - self.last_performance_check
        ).total_seconds() >= self.performance_check_interval

    def _should_perform_scaling_check(self) -> bool:
        """スケーリングチェック実行タイミング判定"""
        return (
            datetime.now() - self.last_scaling_check
        ).total_seconds() >= self.scaling_check_interval

    def _add_to_history(self, metrics: Dict[str, Any]):
        """メトリクス履歴に追加"""
        self.metrics_history.append(metrics)

        # 履歴サイズ制限
        if len(self.metrics_history) > self.max_history_length:
            self.metrics_history = self.metrics_history[-self.max_history_length :]

    def _get_recent_metrics(self, minutes: int = 30) -> list:
        """最近のメトリクス取得"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        recent_metrics = []
        for metric in reversed(self.metrics_history):
            # Process each item in collection
            timestamp_str = metric.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp >= cutoff_time:
                        recent_metrics.append(metric)
                except ValueError:
                    # Handle specific exception case
                    continue

        return recent_metrics

    def _extract_worker_metrics(self, metrics_list: list) -> Dict[str, Any]:
        """ワーカーメトリクス抽出"""
        worker_metrics = {}

        for metrics in metrics_list:
            # Process each item in collection
            workers = metrics.get("workers", {})
            for worker_name, worker_data in workers.items():
                # Process each item in collection
                if worker_name not in worker_metrics:
                    worker_metrics[worker_name] = {
                        "queue_length": 50,  # 実際にはキューから取得
                        "processing_time": 2000,  # 実際には計測
                        "error_rate": 0.05,  # 実際にはログから計算
                    }

        return worker_metrics

    def _send_critical_alert(self, title: str, message: str):
        """クリティカルアラート送信"""
        try:
            alert_message = f"🚨 CRITICAL: {title}\n{message}\nTimestamp: {datetime.now().isoformat()}" \
                "🚨 CRITICAL: {title}\n{message}\nTimestamp: {datetime.now().isoformat()}" \
                "🚨 CRITICAL: {title}\n{message}\nTimestamp: {datetime.now().isoformat()}"
            self.slack.send_message(alert_message)
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to send critical alert: {e}")

    def _send_performance_alert(self, worker_name: str, message: str):
        """パフォーマンスアラート送信"""
        try:
            alert_message = f"⚠️ PERFORMANCE: {worker_name}\n{message}\nTimestamp: {datetime.now()." \
                "⚠️ PERFORMANCE: {worker_name}\n{message}\nTimestamp: {datetime.now()." \
                "isoformat()}"
            self.slack.send_message(alert_message)
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to send performance alert: {e}")

    def _send_scaling_alert(self, worker_name: str, message: str):
        """スケーリングアラート送信"""
        try:
            alert_message = f"📈 SCALING: {worker_name}\n{message}\nTimestamp: {datetime.now().isoformat()}" \
                "📈 SCALING: {worker_name}\n{message}\nTimestamp: {datetime.now().isoformat()}" \
                "📈 SCALING: {worker_name}\n{message}\nTimestamp: {datetime.now().isoformat()}"
            self.slack.send_message(alert_message)
        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Failed to send scaling alert: {e}")

    def _report_elder_status_to_incident_sage(self, status_data: Dict[str, Any]):
        """Incident Sageにステータス報告"""
        if not self.elder_integration_enabled or not self.four_sages:
            # Complex condition - consider breaking down
            return

        try:
            incident_report = {
                "type": "health_monitor_status",
                "service_id": "worker_health_monitor_service",
                "status_data": status_data,
                "timestamp": datetime.now().isoformat(),
                "severity": "medium",
            }

            # Use asyncio to handle async call
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                loop.create_task(
                    self.four_sages.escalate_to_incident_sage(incident_report)
                )
            except RuntimeError:
                # If no event loop, create a new one for this task
                asyncio.run(self.four_sages.escalate_to_incident_sage(incident_report))

            self.logger.info("📊 Health status reported to Incident Sage")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Incident Sage status reporting failed: {e}")

    def _report_to_knowledge_sage(self, report_data: Dict[str, Any]):
        """Knowledge Sageに知識報告"""
        if not self.elder_integration_enabled or not self.four_sages:
            # Complex condition - consider breaking down
            return

        try:
            knowledge_report = {
                "type": "health_monitor_knowledge",
                "service_id": "worker_health_monitor_service",
                "knowledge_data": report_data,
                "timestamp": datetime.now().isoformat(),
            }

            # Use asyncio to handle async call
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                loop.create_task(
                    self.four_sages.report_to_knowledge_sage(knowledge_report)
                )
            except RuntimeError:
                # Handle specific exception case
                asyncio.run(self.four_sages.report_to_knowledge_sage(knowledge_report))

            self.logger.info("📚 Knowledge reported to Knowledge Sage")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Knowledge Sage reporting failed: {e}")

    def _escalate_to_incident_sage(self, incident_data: Dict[str, Any]):
        """Incident Sageに重大問題をエスカレーション"""
        if not self.elder_integration_enabled or not self.four_sages:
            # Complex condition - consider breaking down
            return

        try:
            incident_report = {
                "type": "critical_health_incident",
                "service_id": "worker_health_monitor_service",
                "incident_data": incident_data,
                "timestamp": datetime.now().isoformat(),
                "severity": incident_data.get("severity", "high"),
            }

            # Use asyncio to handle async call
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                loop.create_task(
                    self.four_sages.escalate_to_incident_sage(incident_report)
                )
            except RuntimeError:
                # Handle specific exception case
                asyncio.run(self.four_sages.escalate_to_incident_sage(incident_report))

            self.logger.warning("🚨 Critical incident escalated to Incident Sage")

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Incident Sage escalation failed: {e}")


if __name__ == "__main__":
    service = WorkerHealthMonitorService()
    service.run()
