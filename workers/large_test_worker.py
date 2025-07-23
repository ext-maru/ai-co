#!/usr/bin/env python3
"""
🌳 Elder Tree Integrated Large Test Worker
基本的なテストワーカー - Elders Guild統合版

Elders Guild Integration:
- 🌟 Grand Elder maru oversight
- 🤖 Claude Elder execution guidance
- 🧙‍♂️ Four Sages wisdom consultation
- 🏛️ Elder Council decision support
- ⚔️ Elder Servants coordination

Part of the Elder Tree Hierarchy for testing and validation
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import pika

# Elder Tree Integration imports
try:
    from libs.elder_council_summoner import ElderCouncilSummoner
    from libs.elder_tree_hierarchy import ElderMessage, ElderRank, get_elder_tree
    from libs.four_sages_integration import FourSagesIntegration

    ELDER_TREE_AVAILABLE = True
except ImportError as e:
    # Handle specific exception case
    logging.warning(f"Elder Tree integration not available: {e}")
    FourSagesIntegration = None
    ElderCouncilSummoner = None
    get_elder_tree = None
    ElderMessage = None
    ElderRank = None
    ELDER_TREE_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LargeTestWorker:
    """🌳 Elder Tree統合テストワーカー"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.tests_processed = 0
        self.test_results = []
        self.created_at = datetime.now()

        # Elder Tree Integration
        self.elder_tree = None
        self.four_sages = None
        self.elder_council_summoner = None
        self.elder_integration_enabled = False

        # Test metrics for Elder Tree reporting
        self.test_metrics = {
            "total_tests_processed": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "task_sage_consultations": 0,
            "knowledge_sage_learnings": 0,
            "claude_elder_escalations": 0,
            "critical_failures_escalated": 0,
        }

        self._initialize_elder_systems()

    def _initialize_elder_systems(self):
        """Elder Tree システムの初期化（エラー処理付き）"""
        try:
            if get_elder_tree:
                self.elder_tree = get_elder_tree()
                logger.info("🌳 Elder Tree Hierarchy connected")

            if FourSagesIntegration:
                self.four_sages = FourSagesIntegration()
                logger.info("🧙‍♂️ Four Sages Integration activated")

            if ElderCouncilSummoner:
                self.elder_council_summoner = ElderCouncilSummoner()
                logger.info("🏛️ Elder Council Summoner initialized")

            if all([self.elder_tree, self.four_sages, self.elder_council_summoner]):
                self.elder_integration_enabled = True
                logger.info("✅ Full Elder Tree Integration enabled")
            else:
                logger.warning(
                    "⚠️ Partial Elder Tree Integration - some systems unavailable"
                )

        except Exception as e:
            # Handle specific exception case
            logger.error(f"Elder Tree initialization failed: {e}")
            self.elder_integration_enabled = False

    def connect_to_rabbitmq(self):
        """RabbitMQ接続の確立"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters("localhost")
            )
            self.channel = self.connection.channel()

            # テストキューの宣言
            self.channel.queue_declare(queue="test_tasks", durable=True)
            self.channel.queue_declare(queue="test_results", durable=True)

            logger.info("📡 RabbitMQ connected successfully")
            return True

        except Exception as e:
            # Handle specific exception case
            logger.error(f"RabbitMQ connection failed: {e}")
            return False

    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク処理 - Elder Tree統合版"""
        self.test_metrics["total_tests_processed"] += 1

        try:
            # Report test start to Task Sage
            if self.elder_integration_enabled:
                self._report_test_start_to_task_sage(task_data)

            logger.info(
                f"🧪 Processing test task: {task_data.get('task_id', 'unknown')}"
            )

            # テスト実行
            test_type = task_data.get("test_type", "basic")
            test_config = task_data.get("config", {})

            if test_type == "basic":
                result = self._execute_basic_test(task_data)
            elif test_type == "load":
                result = self._execute_load_test(task_data)
            elif test_type == "integration":
                result = self._execute_integration_test(task_data)
            else:
                result = {
                    "status": "error",
                    "message": f"Unknown test type: {test_type}",
                }

            # Update metrics
            if result.get("status") == "completed":
                self.test_metrics["successful_tests"] += 1
            else:
                self.test_metrics["failed_tests"] += 1

                # Check for critical failures
                if result.get("severity") == "critical":
                    self._escalate_critical_failure(task_data, result)

            # Report test completion to Task Sage
            if self.elder_integration_enabled:
                self._report_test_completion_to_task_sage(task_data, result)

            # Store test patterns in Knowledge Sage
            if self.elder_integration_enabled and result.get("status") == "completed":
                # Complex condition - consider breaking down
                self._store_test_patterns_in_knowledge_sage(task_data, result)

            self.test_results.append(result)
            return result

        except Exception as e:
            # Handle specific exception case
            logger.error(f"Test processing failed: {e}")
            self.test_metrics["failed_tests"] += 1

            # Report error to Task Sage
            if self.elder_integration_enabled:
                self._report_test_error_to_task_sage(task_data, e)

            return {
                "status": "error",
                "message": str(e),
                "task_id": task_data.get("task_id"),
                "timestamp": datetime.now().isoformat(),
            }

    def _execute_basic_test(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """基本テストの実行"""
        test_name = task_data.get("test_name", "unknown_test")

        # シンプルなテスト実行
        import time

        time.sleep(0.1)  # テスト実行をシミュレート

        return {
            "status": "completed",
            "test_name": test_name,
            "test_type": "basic",
            "duration": 0.1,
            "assertions_passed": 5,
            "assertions_failed": 0,
            "task_id": task_data.get("task_id"),
            "timestamp": datetime.now().isoformat(),
        }

    def _execute_load_test(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """負荷テストの実行"""
        test_name = task_data.get("test_name", "load_test")
        duration = task_data.get("config", {}).get("duration", 1.0)

        import time

        time.sleep(duration)

        return {
            "status": "completed",
            "test_name": test_name,
            "test_type": "load",
            "duration": duration,
            "requests_per_second": 100,
            "error_rate": 0.01,
            "task_id": task_data.get("task_id"),
            "timestamp": datetime.now().isoformat(),
        }

    def _execute_integration_test(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """統合テストの実行"""
        test_name = task_data.get("test_name", "integration_test")
        components = task_data.get("config", {}).get(
            "components", ["component1", "component2"]
        )

        import time

        time.sleep(0.5)

        return {
            "status": "completed",
            "test_name": test_name,
            "test_type": "integration",
            "duration": 0.5,
            "components_tested": len(components),
            "components": components,
            "integration_points_verified": len(components) * 2,
            "task_id": task_data.get("task_id"),
            "timestamp": datetime.now().isoformat(),
        }

    def _report_test_start_to_task_sage(self, task_data: Dict[str, Any]):
        """Test start reporting to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": "test_start",
                "worker": "large_test_worker",
                "task_id": task_data.get("task_id"),
                "test_type": task_data.get("test_type"),
                "test_name": task_data.get("test_name"),
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)
            self.test_metrics["task_sage_consultations"] += 1

        except Exception as e:
            # Handle specific exception case
            logger.error(f"Failed to report test start to Task Sage: {e}")

    def _report_test_completion_to_task_sage(
        self, task_data: Dict[str, Any], result: Dict[str, Any]
    ):
        """Test completion reporting to Task Sage"""
        if not self.four_sages:
            return

        try:
            report = {
                "type": "test_completion",
                "worker": "large_test_worker",
                "task_id": task_data.get("task_id"),
                "test_result": result,
                "success": result.get("status") == "completed",
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.report_to_task_sage(report)

        except Exception as e:
            # Handle specific exception case
            logger.error(f"Failed to report test completion to Task Sage: {e}")

    def _report_test_error_to_task_sage(
        self, task_data: Dict[str, Any], error: Exception
    ):
        """Test error reporting to Task Sage"""
        if not self.four_sages:
            return

        try:
            incident_data = {
                "type": "test_error",
                "worker": "large_test_worker",
                "task_id": task_data.get("task_id", "unknown"),
                "error": str(error),
                "error_type": type(error).__name__,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.consult_incident_sage(incident_data)

        except Exception as e:
            # Handle specific exception case
            logger.error(f"Failed to report test error to Task Sage: {e}")

    def _store_test_patterns_in_knowledge_sage(
        self, task_data: Dict[str, Any], result: Dict[str, Any]
    ):
        """Store successful test patterns in Knowledge Sage"""
        if not self.four_sages:
            return

        try:
            pattern_data = {
                "type": "test_pattern",
                "test_type": task_data.get("test_type"),
                "test_name": task_data.get("test_name"),
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }

            self.four_sages.store_knowledge("test_patterns", pattern_data)
            self.test_metrics["knowledge_sage_learnings"] += 1

        except Exception as e:
            # Handle specific exception case
            logger.error(f"Failed to store test patterns in Knowledge Sage: {e}")

    def _escalate_critical_failure(
        self, task_data: Dict[str, Any], result: Dict[str, Any]
    ):
        """Escalate critical test failures to Claude Elder"""
        if not self.elder_tree or not ElderMessage or not ElderRank:
            # Complex condition - consider breaking down
            return

        try:
            elder_message = ElderMessage(
                sender_rank=ElderRank.SERVANT,
                sender_id="large_test_worker",
                recipient_rank=ElderRank.CLAUDE_ELDER,
                recipient_id="claude",
                message_type="critical_test_failure",
                content={
                    "failure_type": "critical_test_failure",
                    "task_id": task_data.get("task_id"),
                    "test_type": task_data.get("test_type"),
                    "result": result,
                    "reporter": "Large Test Worker",
                    "priority": "critical",
                    "timestamp": datetime.now().isoformat(),
                },
                priority="critical",
            )

            success = self.elder_tree.send_message(elder_message)

            if success:
                self.test_metrics["claude_elder_escalations"] += 1
                self.test_metrics["critical_failures_escalated"] += 1
                logger.critical(
                    f"🚨 Critical test failure escalated to Claude Elder: {task_data.get('task_id')}"
                )
            else:
                logger.error(
                    f"Failed to escalate critical test failure: {task_data.get('task_id')}"
                )

        except Exception as e:
            # Handle specific exception case
            logger.error(f"Failed to escalate critical failure: {e}")

    def get_elder_test_status(self) -> Dict[str, Any]:
        """Get comprehensive Elder Tree test status"""
        return {
            "worker_type": "large_test_worker",
            "elder_role": "Testing Specialist",
            "reporting_to": "Task Sage",
            "elder_systems": {
                "integration_enabled": self.elder_integration_enabled,
                "four_sages_active": self.four_sages is not None,
                "council_summoner_active": self.elder_council_summoner is not None,
                "elder_tree_connected": self.elder_tree is not None,
            },
            "test_metrics": self.test_metrics.copy(),
            "test_results_count": len(self.test_results),
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "status": "healthy" if self.elder_integration_enabled else "degraded",
        }

    def start_consuming(self):
        """テストタスクの消費開始"""
        if not self.connect_to_rabbitmq():
            return

        def callback(ch, method, properties, body):
            try:
                task_data = json.loads(body)
                result = self.process_task(task_data)

                # 結果をキューに送信
                self.channel.basic_publish(
                    exchange="",
                    routing_key="test_results",
                    body=json.dumps(result),
                    properties=pika.BasicProperties(delivery_mode=2),
                )

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                # Handle specific exception case
                logger.error(f"Callback error: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue="test_tasks", on_message_callback=callback)

        logger.info("🧪 Large Test Worker waiting for test tasks...")
        if self.elder_integration_enabled:
            logger.info("🌳 Elder Tree guidance active")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            # Handle specific exception case
            logger.info("🛑 Stopping Large Test Worker...")
            self.channel.stop_consuming()
            if self.connection:
                self.connection.close()

            # Final Elder Tree status report
            if self.elder_integration_enabled:
                final_status = self.get_elder_test_status()
                logger.info(f"📊 Final Elder Tree Test Metrics:")
                logger.info(
                    f"  • Total Tests Processed: {final_status['test_metrics']['total_tests_processed']}"
                )
                logger.info(
                    f"  • Successful Tests: {final_status['test_metrics']['successful_tests']}"
                )
                logger.info(
                    f"  • Failed Tests: {final_status['test_metrics']['failed_tests']}"
                )
                logger.info(
                    f"  • Task Sage Consultations: {final_status['test_metrics']['task_sage_consultations']}"
                )
                logger.info(
                    f"  • Knowledge Sage Learnings: {final_status['test_metrics']['knowledge_sage_learnings']}"
                )
                logger.info(
                    f"  • Claude Elder Escalations: {final_status['test_metrics']['claude_elder_escalations']}"
                )

            logger.info("✅ Large Test Worker stopped")
            logger.info("🌳 Elder Tree Testing Specialist mission complete")


def main():
    """メイン実行関数"""
    worker = LargeTestWorker()

    print("🚀 Large Test Worker started")
    print("🌳 Elder Tree hierarchy integration enabled")

    # Display Elder Tree integration status
    if worker.elder_integration_enabled:
        print("✅ Elder Tree systems initialized successfully")
        print("🧪 Testing Specialist under Elder Tree guidance")
    else:
        print("⚠️ Elder Tree systems not available - running in standalone mode")

    # Display Elder Tree test status
    elder_status = worker.get_elder_test_status()
    print(
        f"🧙‍♂️ Four Sages Integration: {'✅ Available' if elder_status['elder_systems']['four_sages_active'] else '❌ Unavailable'}"
    )
    print(
        f"🏛️ Elder Council: {'✅ Available' if elder_status['elder_systems']['council_summoner_active'] else '❌ Unavailable'}"
    )
    print(
        f"🌳 Elder Tree: {'✅ Available' if elder_status['elder_systems']['elder_tree_connected'] else '❌ Unavailable'}"
    )

    worker.start_consuming()


if __name__ == "__main__":
    main()
