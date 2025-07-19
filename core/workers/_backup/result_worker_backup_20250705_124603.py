#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pika

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR / "logs"

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


class ResultWorker:
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

    def process_result(self, ch, method, properties, body):
        try:
            result = json.loads(body)
            logger.info(f"結果受信: {result['task_id']} - {result['status']}")

            # 結果をログに記録（将来的にはDB保存など）
            logger.info(f"出力ファイル: {result.get('output_file', 'N/A')}")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"結果処理エラー: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self):
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
