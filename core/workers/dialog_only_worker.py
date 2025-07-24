#!/usr/bin/env python3
"""
対話専用ワーカー（dialog_task_queueのみ処理）
"""
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import pika

sys.path.append("/root/ai_co")
from features.conversation.conversation_manager import ConversationManager

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR / "logs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DialogOnly] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "dialog_only_worker.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("DialogOnly")


class DialogOnlyWorker:
    def __init__(self, worker_id="dialog-only-1"):
        """初期化メソッド"""
        self.worker_id = worker_id
    """DialogOnlyWorkerワーカークラス"""
        self.conversation_manager = ConversationManager()
        logger.info(f"{worker_id} 初期化")

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
        """connectメソッド"""
                pika.ConnectionParameters("localhost")
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue="dialog_task_queue", durable=True)
            self.channel.queue_declare(queue="dialog_response_queue", durable=True)
            logger.info("RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"接続失敗: {e}")
            return False

    def process_dialog_task(self, ch, method, properties, body):
        try:
        """process_dialog_taskを処理"""
            task_data = json.loads(body)
            conversation_id = task_data.get("conversation_id")
            instruction = task_data.get("instruction")
            context = task_data.get("context", {})

            logger.info(f"📨 対話タスク受信: {conversation_id}")
            logger.info(f"指示: {instruction[:100]}...")

            # 会話履歴取得
            messages = self.conversation_manager.db.get_messages(conversation_id)
            logger.info(f"既存メッセージ数: {len(messages)}")

            # シンプルな応答を生成
            if "webサービス" in instruction.lower() or "アイデア" in instruction.lower():
                response_content = "AIを使った革新的なWebサービスのアイデアをいくつか提案します"
                question = "どのような分野のサービスに興味がありますか？（例：教育、健康、エンターテイメント、ビジネス）"
            else:
                response_content = "詳細を教えてください"
                question = "具体的にどのような機能や要件が必要でしょうか？"

            # PMに応答送信
            response = {
                "conversation_id": conversation_id,
                "worker_id": self.worker_id,
                "status": "need_info",
                "content": response_content,
                "question": question,
            }

            self.channel.basic_publish(
                exchange="",
                routing_key="dialog_response_queue",
                body=json.dumps(response),
                properties=pika.BasicProperties(delivery_mode=2),
            )

            # 会話記録
            self.conversation_manager.add_worker_message(
                conversation_id,
                self.worker_id,
                response["content"],
                metadata={"status": response["status"], "question": question},
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"✅ 対話応答送信: {conversation_id}")

        except Exception as e:
            logger.error(f"❌ 処理エラー: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start(self)if not self.connect():
    """startメソッド"""
            return

        self.channel.basic_qos(prefetch_count=1)

        # dialog_task_queueのみを処理
        self.channel.basic_consume(
            queue="dialog_task_queue", on_message_callback=self.process_dialog_task
        )

        logger.info(f"🚀 {self.worker_id} 起動 - dialog_task_queue専用")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("停止中...")
            self.channel.stop_consuming()
            self.connection.close()


if __name__ == "__main__":
    import sys

    worker_id = sys.argv[1] if len(sys.argv) > 1 else "dialog-only-1"
    worker = DialogOnlyWorker(worker_id)
    worker.start()
