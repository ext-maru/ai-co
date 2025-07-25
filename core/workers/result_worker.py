#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pika

PROJECT_DIR = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_DIR / "logs"
sys.path.append(str(PROJECT_DIR))

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ResultWorker] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "result_worker.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("ResultWorker")

from features.notification.slack_notifier import SlackNotifier

# Slack通知をインポート
from features.notification.slack_notifier_v2 import SlackNotifierV2


class ResultWorker:
    def __init__(self):
        """初期化メソッド"""
        # Slack通知の初期化
        self.slack_notifier = SlackNotifierV2()
        self.slack_notifier_v1 = SlackNotifier()  # フォールバック用
        logger.info(f"Slack通知: {'有効' if self.slack_notifier.enabled else '無効'}")

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters("localhost")
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue="result_queue", durable=True)
            logger.info("RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False

    def send_slack_notification(self, result):
        """拡張版タスク完了通知をSlackに送信"""
        if not self.slack_notifier.enabled:
            return

        try:
            # 結果データの検証
            if not result or not isinstance(result, dict):
                logger.error("Slack通知送信エラー: 無効な結果データ")
                return

            # 結果データから拡張情報を収集
            task_data = {
                "task_id": result.get("task_id", "N/A"),
                "task_type": result.get("task_type", "general"),
                "status": result.get("status", "unknown"),
                "worker": result.get("worker", "unknown"),
                "priority": result.get("priority", 2),
                # タイミング情報
                "start_time": result.get("start_time"),
                "end_time": result.get("timestamp", datetime.now()),
                "execution_time": result.get("execution_time", 0),
                "queue_time": result.get("queue_time", 0),
                # AI処理情報
                "rag_applied": result.get("rag_applied", False),
                "rag_reference_count": result.get("rag_reference_count", 0),
                "evolution_applied": bool(
                    result.get("evolution_result", {}).get("success")
                )
                if result.get("evolution_result")
                else False,
                "evolution_files": result.get("evolution_result", {}).get(
                    "evolved_files", []
                )
                if result.get("evolution_result")
                else [],
                "model": result.get("model", "default"),
                # コンテンツ
                "prompt": result.get("prompt", ""),
                "response": result.get("response", ""),
                "error": result.get("error"),
                # ファイル情報
                "output_file": result.get("output_file"),
            }

            # 出力ファイルから応答を読み取る（必要な場合）
            if not task_data["response"] and task_data["output_file"]:
                try:
                    with open(task_data["output_file"], "r", encoding="utf-8") as f:
                        content = f.read(1000)  # 最初の1000文字
                        task_data["response"] = content
                except Exception:
                    task_data["response"] = f"ファイル出力: {task_data['output_file']}"

            # 拡張版通知を送信
            success = self.slack_notifier.send_enhanced_task_notification(task_data)

            if success:
                logger.info(f"拡張版Slack通知送信成功: タスク {task_data['task_id']}")
            else:
                logger.warning(f"拡張版Slack通知送信失敗: タスク {task_data['task_id']}")

                # V2失敗時にV1フォールバックを実行
                if self.slack_notifier_v1.enabled:
                    logger.info("V1フォールバック通知を試行中...")
                    fallback_message = (
                        f"タスク {task_data['task_id']} が完了しました\n"
                        f"ワーカー: {task_data['worker']}\n"
                        f"ステータス: {task_data['status']}"
                    )

                    if self.slack_notifier_v1.send_notification(fallback_message):
                        logger.info("V1フォールバック通知送信成功")
                    else:
                        logger.error("V1フォールバック通知も失敗")

        except Exception as e:
            logger.error(f"Slack通知送信エラー: {e}")
            import traceback

            traceback.print_exc()

    def process_result(self, ch, method, properties, body):
        """process_resultを処理"""
        try:
            result = json.loads(body)
            logger.info(f"結果受信: {result['task_id']} - {result['status']}")

            # 結果をログに記録
            logger.info(f"出力ファイル: {result.get('output_file', 'N/A')}")

            # Slack通知を送信
            self.send_slack_notification(result)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"結果処理エラー: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self):
        """startメソッド"""
        if not self.connect():
            return

        self.channel.basic_consume(
            queue="result_queue", on_message_callback=self.process_result
        )

        logger.info("ResultWorker起動 - 結果待機中...")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("シャットダウン中...")
            self.channel.stop_consuming()
            self.connection.close()


if __name__ == "__main__":
    worker = ResultWorker()
    worker.start()
