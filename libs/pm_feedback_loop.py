#!/usr/bin/env python3
"""
PM フィードバックループ - PMが納得するまで繰り返すメカニズム
"""

import json
import logging

# プロジェクトルートをPythonパスに追加
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pika

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager
from libs.pm_quality_evaluator import PMQualityEvaluator
from libs.slack_notifier import SlackNotifier

logger = logging.getLogger(__name__)


class PMFeedbackLoop(BaseManager):
    """PM満足度ベースのフィードバックループ管理"""

    def __init__(self):
        super().__init__("PMFeedbackLoop")
        self.quality_evaluator = PMQualityEvaluator()

        # RabbitMQ接続
        self.connection = None
        self.channel = None

        # フィードバックキュー
        self.feedback_queue = "pm_feedback_queue"
        self.retry_queue = "pm_retry_queue"

        # 設定
        self.max_concurrent_retries = 3
        self.retry_delay = 60  # 秒
        self.feedback_timeout = 300  # 5分

        # 実行中のタスク管理
        self.active_tasks = {}
        self.retry_tasks = {}

        # 通知
        try:
            self.slack = SlackNotifier()
        except:
            self.slack = None

        self.initialize()

    def initialize(self) -> bool:
        """初期化処理"""
        try:
            self._connect_rabbitmq()
            self._setup_queues()
            return True
        except Exception as e:
            self.handle_error(e, "初期化")
            return False

    def _connect_rabbitmq(self):
        """RabbitMQ接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host="localhost", heartbeat=600, blocked_connection_timeout=300
                )
            )
            self.channel = self.connection.channel()
            logger.info("✅ RabbitMQ接続成功")
        except Exception as e:
            logger.error(f"❌ RabbitMQ接続失敗: {e}")
            raise

    def _setup_queues(self):
        """キューのセットアップ"""
        if self.channel:
            # フィードバックキュー
            self.channel.queue_declare(
                queue=self.feedback_queue,
                durable=True,
                arguments={"x-max-priority": 10},
            )

            # 再試行キュー
            self.channel.queue_declare(
                queue=self.retry_queue, durable=True, arguments={"x-max-priority": 10}
            )

            # 遅延キュー（再試行用）
            self.channel.queue_declare(
                queue=f"{self.retry_queue}_delayed",
                durable=True,
                arguments={
                    "x-message-ttl": self.retry_delay * 1000,  # ミリ秒
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": self.retry_queue,
                },
            )

            logger.info("✅ キューセットアップ完了")

    def process_task_result(
        self, task_id: str, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """タスク結果を処理してPM評価を実行"""
        try:
            logger.info(f"🎯 PMフィードバック処理開始: {task_id}")

            # 品質評価実行
            evaluation_result = self.quality_evaluator.evaluate_task_quality(
                task_id, task_data
            )

            # 結果をアクティブタスクに記録
            self.active_tasks[task_id] = {
                "task_data": task_data,
                "evaluation_result": evaluation_result,
                "timestamp": datetime.now(),
                "attempt_count": task_data.get("attempt_count", 1),
            }

            # PM承認判定
            pm_approved = evaluation_result.get("pm_approved", False)
            retry_required = evaluation_result.get("retry_required", False)

            if pm_approved:
                logger.info(f"✅ PM承認: {task_id}")
                self._handle_approved_task(task_id, evaluation_result)
            elif retry_required:
                logger.info(f"🔄 再試行要請: {task_id}")
                self._handle_retry_required_task(task_id, task_data, evaluation_result)
            else:
                logger.info(f"❌ PM却下（最終）: {task_id}")
                self._handle_rejected_task(task_id, evaluation_result)

            # 結果を返す
            return {
                "task_id": task_id,
                "pm_approved": pm_approved,
                "retry_required": retry_required,
                "evaluation_result": evaluation_result,
            }

        except Exception as e:
            logger.error(f"フィードバック処理エラー: {e}")
            return {
                "task_id": task_id,
                "pm_approved": False,
                "retry_required": False,
                "error": str(e),
            }

    def _handle_approved_task(self, task_id: str, evaluation_result: Dict[str, Any]):
        """承認されたタスクの処理"""
        try:
            # アクティブタスクから削除
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            # 成功通知
            if self.slack:
                self._send_approval_notification(task_id, evaluation_result)

            logger.info(f"✅ タスク承認完了: {task_id}")

        except Exception as e:
            logger.error(f"承認処理エラー: {e}")

    def _handle_retry_required_task(
        self, task_id: str, task_data: Dict[str, Any], evaluation_result: Dict[str, Any]
    ):
        """再試行が必要なタスクの処理"""
        try:
            attempt_count = task_data.get("attempt_count", 1)

            # 再試行タスクとして登録
            self.retry_tasks[task_id] = {
                "task_data": task_data,
                "evaluation_result": evaluation_result,
                "attempt_count": attempt_count,
                "retry_timestamp": datetime.now(),
            }

            # 改善提案を生成
            improvement_suggestions = self._generate_improvement_suggestions(
                evaluation_result
            )

            # 再試行用タスクデータを準備
            retry_task_data = task_data.copy()
            retry_task_data["attempt_count"] = attempt_count + 1
            retry_task_data["pm_feedback"] = evaluation_result.get(
                "feedback_message", ""
            )
            retry_task_data["improvement_suggestions"] = improvement_suggestions
            retry_task_data["original_task_id"] = task_id
            retry_task_data["retry_reason"] = "pm_quality_improvement"

            # 遅延キューに送信（即座に再試行しない）
            self._send_to_retry_queue(task_id, retry_task_data)

            # 再試行通知
            if self.slack:
                self._send_retry_notification(
                    task_id, evaluation_result, improvement_suggestions
                )

            logger.info(f"🔄 再試行キュー送信: {task_id} (試行回数: {attempt_count + 1})")

        except Exception as e:
            logger.error(f"再試行処理エラー: {e}")

    def _handle_rejected_task(self, task_id: str, evaluation_result: Dict[str, Any]):
        """最終的に却下されたタスクの処理"""
        try:
            # アクティブタスクから削除
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            # 却下通知
            if self.slack:
                self._send_rejection_notification(task_id, evaluation_result)

            logger.info(f"❌ タスク最終却下: {task_id}")

        except Exception as e:
            logger.error(f"却下処理エラー: {e}")

    def _generate_improvement_suggestions(
        self, evaluation_result: Dict[str, Any]
    ) -> List[str]:
        """改善提案を生成"""
        suggestions = []

        # 各評価項目に基づく提案
        test_success_rate = evaluation_result.get("test_success_rate", 0.0)
        if test_success_rate < 95.0:
            suggestions.append(f"テストカバレッジを改善してください (現在: {test_success_rate:.1f}%)")

        code_quality_score = evaluation_result.get("code_quality_score", 0.0)
        if code_quality_score < 80.0:
            suggestions.append(f"コード品質を向上させてください (現在: {code_quality_score:.1f}%)")

        requirement_compliance = evaluation_result.get("requirement_compliance", 0.0)
        if requirement_compliance < 90.0:
            suggestions.append(f"要件適合度を向上させてください (現在: {requirement_compliance:.1f}%)")

        error_rate = evaluation_result.get("error_rate", 0.0)
        if error_rate < 95.0:  # エラー率は逆転
            suggestions.append(f"エラーハンドリングを改善してください (エラー率: {100-error_rate:.1f}%)")

        performance_score = evaluation_result.get("performance_score", 0.0)
        if performance_score < 75.0:
            suggestions.append(f"パフォーマンスを最適化してください (現在: {performance_score:.1f}%)")

        security_score = evaluation_result.get("security_score", 0.0)
        if security_score < 85.0:
            suggestions.append(f"セキュリティを強化してください (現在: {security_score:.1f}%)")

        return suggestions

    def _send_to_retry_queue(self, task_id: str, retry_task_data: Dict[str, Any]):
        """再試行キューに送信"""
        try:
            if self.channel:
                # 遅延キューに送信
                self.channel.basic_publish(
                    exchange="",
                    routing_key=f"{self.retry_queue}_delayed",
                    body=json.dumps(retry_task_data, ensure_ascii=False),
                    properties=pika.BasicProperties(delivery_mode=2, priority=5),  # 永続化
                )
                logger.info(f"📤 再試行キュー送信: {task_id}")
        except Exception as e:
            logger.error(f"再試行キュー送信エラー: {e}")

    def _send_approval_notification(
        self, task_id: str, evaluation_result: Dict[str, Any]
    ):
        """承認通知"""
        try:
            if not self.slack:
                return

            overall_score = evaluation_result.get("overall_score", 0.0)
            message = f"✅ PM承認完了\n"
            message += f"タスク: {task_id}\n"
            message += f"総合スコア: {overall_score:.1f}%\n"
            message += f"評価: {evaluation_result.get('feedback_message', '')}"

            self.slack.send_task_completion_simple(
                task_id=f"pm_approval_{task_id}",
                worker="pm_feedback_loop",
                prompt="PM品質評価",
                response=message,
            )
        except Exception as e:
            logger.error(f"承認通知エラー: {e}")

    def _send_retry_notification(
        self, task_id: str, evaluation_result: Dict[str, Any], suggestions: List[str]
    ):
        """再試行通知"""
        try:
            if not self.slack:
                return

            overall_score = evaluation_result.get("overall_score", 0.0)
            message = f"🔄 PM再試行要請\n"
            message += f"タスク: {task_id}\n"
            message += f"総合スコア: {overall_score:.1f}%\n"
            message += f"改善提案:\n"

            for suggestion in suggestions[:3]:  # 最大3つ
                message += f"  - {suggestion}\n"

            self.slack.send_task_completion_simple(
                task_id=f"pm_retry_{task_id}",
                worker="pm_feedback_loop",
                prompt="PM品質再評価",
                response=message,
            )
        except Exception as e:
            logger.error(f"再試行通知エラー: {e}")

    def _send_rejection_notification(
        self, task_id: str, evaluation_result: Dict[str, Any]
    ):
        """却下通知"""
        try:
            if not self.slack:
                return

            overall_score = evaluation_result.get("overall_score", 0.0)
            message = f"❌ PM最終却下\n"
            message += f"タスク: {task_id}\n"
            message += f"総合スコア: {overall_score:.1f}%\n"
            message += f"理由: {evaluation_result.get('feedback_message', '')}"

            self.slack.send_task_completion_simple(
                task_id=f"pm_rejection_{task_id}",
                worker="pm_feedback_loop",
                prompt="PM品質評価",
                response=message,
            )
        except Exception as e:
            logger.error(f"却下通知エラー: {e}")

    def start_feedback_monitor(self):
        """フィードバック監視を開始"""
        try:
            if not self.channel:
                self._connect_rabbitmq()

            # QoS設定
            self.channel.basic_qos(prefetch_count=1)

            # フィードバックキューの消費
            self.channel.basic_consume(
                queue=self.feedback_queue,
                on_message_callback=self._handle_feedback_message,
            )

            logger.info(f"👂 PMフィードバック監視開始: {self.feedback_queue}")

            # 消費開始
            self.channel.start_consuming()

        except Exception as e:
            logger.error(f"フィードバック監視エラー: {e}")

    def _handle_feedback_message(self, ch, method, properties, body):
        """フィードバックメッセージ処理"""
        try:
            task_data = json.loads(body)
            task_id = task_data.get("task_id", "unknown")

            logger.info(f"📨 フィードバックメッセージ受信: {task_id}")

            # フィードバック処理
            result = self.process_task_result(task_id, task_data)

            # ACK
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"フィードバックメッセージ処理エラー: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """フィードバック統計情報"""
        return {
            "active_tasks": len(self.active_tasks),
            "retry_tasks": len(self.retry_tasks),
            "quality_stats": self.quality_evaluator.get_quality_statistics(),
        }

    def stop(self):
        """フィードバックループ停止"""
        try:
            if self.channel:
                self.channel.stop_consuming()
                self.channel.close()

            if self.connection:
                self.connection.close()

            logger.info("🛑 PMフィードバックループ停止")

        except Exception as e:
            logger.error(f"停止エラー: {e}")


if __name__ == "__main__":
    # テスト実行
    feedback_loop = PMFeedbackLoop()

    # テストデータ
    test_task_data = {
        "task_id": "test_feedback_001",
        "status": "completed",
        "files_created": ["workers/test_worker.py"],
        "duration": 45.0,
        "prompt": "Create a test worker with proper error handling",
        "response": "Created TestWorker with basic functionality",
        "error_trace": "",
        "attempt_count": 1,
    }

    print("=== PM Feedback Loop Test ===")
    result = feedback_loop.process_task_result("test_feedback_001", test_task_data)

    print(f"Task ID: {result['task_id']}")
    print(f"PM Approved: {result['pm_approved']}")
    print(f"Retry Required: {result['retry_required']}")

    if "evaluation_result" in result:
        eval_result = result["evaluation_result"]
        print(f"Overall Score: {eval_result.get('overall_score', 0.0):.1f}%")
        print(f"Feedback: {eval_result.get('feedback_message', '')}")

    print("\n=== Feedback Statistics ===")
    stats = feedback_loop.get_feedback_statistics()
    print(f"Active Tasks: {stats['active_tasks']}")
    print(f"Retry Tasks: {stats['retry_tasks']}")
    print(f"Quality Stats: {stats['quality_stats']}")
