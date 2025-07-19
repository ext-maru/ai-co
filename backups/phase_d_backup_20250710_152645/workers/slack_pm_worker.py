#!/usr/bin/env python3
"""
🌳 Elder Tree Integrated SlackPMWorker
Elders Guild Slack PM Worker - Elders Guild統合版

Elders Guild Integration:
- 🌟 Grand Elder maru oversight
- 🤖 Claude Elder execution guidance
- 🧙‍♂️ Four Sages wisdom consultation
- 🏛️ Elder Council decision support
- ⚔️ Elder Servants coordination

Part of the Elder Tree Hierarchy for Slack PM processing
"""

import json
import re
import sys
import threading
import time
from datetime import datetime

# Core dependencies - dynamic path resolution
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# Slack PM integration
from knowledge_base.slack_integration.slack_pm_manager import SlackPMManager

from core.enhanced_base_worker import EnhancedBaseWorker

# Task processing
from libs.async_worker_optimization import ProcessorOptimizer
from libs.common_utils import setup_logger
from libs.queue_manager import QueueManager
from workers.pm_worker import PMWorker

logger = setup_logger(__name__)


class SlackPMWorker(EnhancedBaseWorker):
    """Slack統合プロジェクトマネージャーワーカー"""

    def __init__(self, worker_id: str = "slack-pm-1"):
        super().__init__(worker_id)

        # Slack PM管理
        self.slack_pm = SlackPMManager()

        # キュープロセッサー
        self.queue_processor = QueueManager()

        # Claude APIクライアント
        from libs.claude_client_with_rotation import ClaudeClientWithRotation

        self.claude_client = ClaudeClientWithRotation()

        # タスク管理
        self.active_tasks: Dict[str, Dict] = {}
        self.task_results: Dict[str, Dict] = {}

        # ワーカー状態
        self.running = False
        self.progress_thread: Optional[threading.Thread] = None

        # Elder Tree Integration
        self.elder_tree = None
        self.four_sages = None
        self.elder_council_summoner = None
        self.elder_integration_enabled = False

        # Slack PM metrics for Elder Tree reporting
        self.slack_pm_metrics = {
            "total_slack_tasks_processed": 0,
            "successful_slack_tasks": 0,
            "failed_slack_tasks": 0,
            "task_sage_consultations": 0,
            "knowledge_sage_learnings": 0,
            "claude_elder_escalations": 0,
            "critical_issues_escalated": 0,
        }

        # Slack PMコールバック設定
        self.slack_pm.set_task_creation_callback(self._handle_task_creation)
        self.slack_pm.set_approval_callback(self._handle_approval_request)
        self.slack_pm.set_completion_callback(self._handle_task_completion)

        self._initialize_elder_systems()

        logger.info(f"📋 {self.worker_id} 初期化完了")

    def start(self):
        """ワーカー開始"""
        logger.info(f"🚀 {self.worker_id} 開始")

        # RabbitMQ接続
        try:
            import pika

            connection_params = pika.ConnectionParameters(host="localhost")
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()

            # キュー宣言
            self.channel.queue_declare(queue="slack_pm_tasks", durable=True)
            logger.info("📡 RabbitMQ接続成功")
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return

        # Slack PM開始
        try:
            # RTMは別スレッドで開始
            rtm_thread = threading.Thread(target=self.slack_pm.start_rtm, daemon=True)
            rtm_thread.start()
            logger.info("📱 Slack RTM開始")
        except Exception as e:
            logger.error(f"Slack RTM開始失敗: {e}")

        # 進捗監視スレッド開始
        self.running = True
        self.progress_thread = threading.Thread(
            target=self._progress_monitor, daemon=True
        )
        self.progress_thread.start()

        # メインループ
        try:
            logger.info(f"📋 {self.worker_id} 待機中 - Slack対話型PM有効")

            # キュー消費設定
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue="slack_pm_tasks", on_message_callback=self._process_slack_task
            )

            # メッセージ消費開始
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("🛑 ワーカー停止中...")
            self.stop()

    def stop(self):
        """ワーカー停止"""
        self.running = False

        # Slack PM停止
        try:
            self.slack_pm.stop_rtm()
        except Exception as e:
            logger.error(f"Slack PM停止エラー: {e}")

        # キュープロセッサー停止
        try:
            self.queue_processor.stop_processing()
        except Exception as e:
            logger.error(f"Queue Processor停止エラー: {e}")

        # RabbitMQ停止
        try:
            if self.channel:
                self.channel.stop_consuming()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.error(f"RabbitMQ停止エラー: {e}")

        # スレッド終了待機
        if self.progress_thread:
            self.progress_thread.join(timeout=5)

        logger.info("👋 Slack PM Worker 終了")

    def _initialize_elder_systems(self):
        """Elder Tree システムの初期化（エラー処理付き）"""
        try:
            if FourSagesIntegration:
                self.four_sages = FourSagesIntegration()
                logger.info("🧙‍♂️ Four Sages Integration activated")

            if ElderCouncilSummoner:
                self.elder_council_summoner = ElderCouncilSummoner()
                logger.info("🏛️ Elder Council Summoner initialized")

            if get_elder_tree:
                self.elder_tree = get_elder_tree()
                logger.info("🌳 Elder Tree Hierarchy connected")

            if all([self.elder_tree, self.four_sages, self.elder_council_summoner]):
                self.elder_integration_enabled = True
                logger.info("✅ Full Elder Tree Integration enabled")
            else:
                logger.warning(
                    "⚠️ Partial Elder Tree Integration - some systems unavailable"
                )

        except Exception as e:
            logger.error(f"Elder Tree initialization failed: {e}")
            self.elder_integration_enabled = False

    def _handle_task_creation(self, task_data: Dict[str, Any]):
        """タスク作成コールバック - Elder Tree統合版"""
        self.slack_pm_metrics["total_slack_tasks_processed"] += 1

        try:
            # Report task creation to Task Sage
            if self.elder_integration_enabled:
                self._report_slack_task_to_task_sage(task_data, "created")

            # 既存のタスク作成ロジック
            task_id = task_data.get("task_id")
            if task_id:
                self.active_tasks[task_id] = task_data
                logger.info(f"📋 Slack task created: {task_id}")

        except Exception as e:
            logger.error(f"Task creation failed: {e}")
            if self.elder_integration_enabled:
                self._report_slack_error_to_task_sage(task_data, e)

    def _handle_approval_request(self, approval_data: Dict[str, Any]):
        """承認リクエストコールバック - Elder Tree統合版"""
        try:
            # Report approval request to Task Sage
            if self.elder_integration_enabled:
                self._report_slack_approval_to_task_sage(approval_data)

            # 既存の承認ロジック
            approval_id = approval_data.get("approval_id")
            logger.info(f"📋 Slack approval request: {approval_id}")

        except Exception as e:
            logger.error(f"Approval request failed: {e}")
            if self.elder_integration_enabled:
                self._report_slack_error_to_task_sage(approval_data, e)

    def _handle_task_completion(self, completion_data: Dict[str, Any]):
        """タスク完了コールバック - Elder Tree統合版"""
        try:
            # Report task completion to Task Sage
            if self.elder_integration_enabled:
                self._report_slack_task_to_task_sage(completion_data, "completed")

            # 既存のタスク完了ロジック
            task_id = completion_data.get("task_id")
            if task_id and task_id in self.active_tasks:
                self.task_results[task_id] = completion_data
                del self.active_tasks[task_id]
                self.slack_pm_metrics["successful_slack_tasks"] += 1
                logger.info(f"✅ Slack task completed: {task_id}")

            # Store successful patterns in Knowledge Sage
            if self.elder_integration_enabled:
                self._store_slack_patterns_in_knowledge_sage(completion_data)

        except Exception as e:
            logger.error(f"Task completion failed: {e}")
            self.slack_pm_metrics["failed_slack_tasks"] += 1
            if self.elder_integration_enabled:
                self._report_slack_error_to_task_sage(completion_data, e)

    def _report_slack_task_to_task_sage(self, task_data: Dict[str, Any], action: str):
        """Report Slack task to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": f"slack_task_{action}",
                "worker": "slack_pm_worker",
                "task_id": task_data.get("task_id"),
                "action": action,
                "slack_channel": task_data.get("slack_channel"),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)
            self.slack_pm_metrics["task_sage_consultations"] += 1

        except Exception as e:
            logger.error(f"Failed to report Slack task to Task Sage: {e}")

    def _report_slack_approval_to_task_sage(self, approval_data: Dict[str, Any]):
        """Report Slack approval to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": "slack_approval_request",
                "worker": "slack_pm_worker",
                "approval_id": approval_data.get("approval_id"),
                "approver": approval_data.get("approver"),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)

        except Exception as e:
            logger.error(f"Failed to report Slack approval to Task Sage: {e}")

    def _report_slack_error_to_task_sage(
        self, task_data: Dict[str, Any], error: Exception
    ):
        """Report Slack error to Task Sage"""
        if not self.four_sages:
            return

        try:
            incident_data = {
                "type": "slack_pm_error",
                "worker": "slack_pm_worker",
                "task_id": task_data.get("task_id", "unknown"),
                "error": str(error),
                "error_type": type(error).__name__,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.consult_incident_sage(incident_data)

        except Exception as e:
            logger.error(f"Failed to report Slack error to Task Sage: {e}")

    def _store_slack_patterns_in_knowledge_sage(self, completion_data: Dict[str, Any]):
        """Store Slack PM patterns in Knowledge Sage"""
        if not self.four_sages:
            return

        try:
            pattern_data = {
                "type": "slack_pm_pattern",
                "task_id": completion_data.get("task_id"),
                "completion_data": completion_data,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.store_knowledge("slack_pm_patterns", pattern_data)
            self.slack_pm_metrics["knowledge_sage_learnings"] += 1

        except Exception as e:
            logger.error(f"Failed to store Slack patterns in Knowledge Sage: {e}")

    def get_elder_slack_pm_status(self) -> Dict[str, Any]:
        """Get comprehensive Elder Tree Slack PM status"""
        return {
            "worker_type": "slack_pm_worker",
            "elder_role": "Slack PM Coordinator",
            "reporting_to": "Task Sage",
            "elder_systems": {
                "integration_enabled": self.elder_integration_enabled,
                "four_sages_active": self.four_sages is not None,
                "council_summoner_active": self.elder_council_summoner is not None,
                "elder_tree_connected": self.elder_tree is not None,
            },
            "slack_pm_metrics": self.slack_pm_metrics.copy(),
            "active_tasks_count": len(self.active_tasks),
            "completed_tasks_count": len(self.task_results),
            "status": "healthy" if self.elder_integration_enabled else "degraded",
        }

    def get_status(self) -> dict:
        """ワーカーステータス取得"""
        return {
            "worker_id": self.worker_id,
            "running": self.running,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.task_results),
            "slack_sessions": len(getattr(self.slack_pm, "active_sessions", {})),
            "elder_integration_enabled": self.elder_integration_enabled,
            "elder_slack_pm_status": self.get_elder_slack_pm_status(),
        }


if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "slack-pm-1"
    worker = SlackPMWorker(worker_id)

    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("キーボード割り込み受信")
    finally:
        worker.stop()
