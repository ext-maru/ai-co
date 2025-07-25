#!/usr/bin/env python3
"""
対話型タスク処理用キュー設定
"""
import logging

import pika

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_dialog_queues():
    """対話用キューを設定"""
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()

    # 対話型タスクキュー
    queues = [
        "dialog_task_queue",  # PM→Worker: タスク指示
        "dialog_response_queue",  # Worker→PM: 応答・質問
        "user_input_queue",  # UI→PM: ユーザー入力
        "notification_queue",  # PM→UI: 通知
    ]

    for queue in queues:
        channel.queue_declare(queue=queue, durable=True)
        logger.info(f"キュー作成: {queue}")

    connection.close()
    logger.info("対話型キュー設定完了")


if __name__ == "__main__":
    setup_dialog_queues()
