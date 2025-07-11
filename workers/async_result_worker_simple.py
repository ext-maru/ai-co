#!/usr/bin/env python3
"""
Async Result Worker Simple - 軽量版結果処理ワーカー
Missing worker file recovery - 不足ワーカーファイル復旧
"""

import asyncio
import json
import logging
import pika
import sys
from datetime import datetime
from pathlib import Path

# パス設定
sys.path.append(str(Path(__file__).parent.parent))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/async_result_worker_simple.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('async_result_worker_simple')

class AsyncResultWorkerSimple:
    """軽量版非同期結果ワーカー"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = 'ai_results'

    def connect_rabbitmq(self):
        """RabbitMQに接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={'x-max-priority': 10}
            )
            logger.info(f"✅ RabbitMQ connected: {self.queue_name}")
            return True
        except Exception as e:
            logger.error(f"❌ RabbitMQ connection failed: {e}")
            return False

    def process_result(self, result_data):
        """結果データを処理"""
        try:
            task_id = result_data.get('task_id', 'unknown')
            status = result_data.get('status', 'unknown')

            logger.info(f"🔄 Processing result: {task_id} ({status})")

            # 基本的な結果処理
            processed_result = {
                'task_id': task_id,
                'original_status': status,
                'processed_at': datetime.now().isoformat(),
                'worker': 'async_result_worker_simple',
                'processing_status': 'completed'
            }

            # 結果に応じた処理分岐
            if status == 'completed':
                processed_result['action'] = 'stored_successfully'
            elif status == 'failed':
                processed_result['action'] = 'logged_error'
            else:
                processed_result['action'] = 'processed_unknown_status'

            # 結果をログに記録
            logger.info(f"✅ Result processed: {task_id} -> {processed_result['action']}")

            return processed_result

        except Exception as e:
            logger.error(f"❌ Result processing failed: {e}")
            return {
                'task_id': result_data.get('task_id', 'unknown'),
                'processing_status': 'failed',
                'error': str(e),
                'processed_at': datetime.now().isoformat(),
                'worker': 'async_result_worker_simple'
            }

    def callback(self, ch, method, properties, body):
        """メッセージ受信時のコールバック"""
        try:
            # メッセージをデコード
            message = json.loads(body.decode('utf-8'))
            logger.info(f"📨 Received result message: {message}")

            # 結果を処理
            processed = self.process_result(message)

            # 処理済み結果をログ出力（簡略化）
            logger.info(f"📊 Processed result: {processed}")

            # メッセージを確認
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"❌ Message processing failed: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        """メッセージ消費を開始"""
        if not self.connect_rabbitmq():
            return

        logger.info("🚀 Starting result worker (simple mode)...")

        # QoS設定
        self.channel.basic_qos(prefetch_count=1)

        # コンシューマー設定
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback
        )

        try:
            logger.info("⏳ Waiting for result messages...")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("🛑 Stopping result worker...")
            self.channel.stop_consuming()
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("🔌 RabbitMQ connection closed")

def main():
    """メイン関数"""
    logger.info("📊 Async Result Worker Simple starting...")

    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)

    worker = AsyncResultWorkerSimple()
    worker.start_consuming()

if __name__ == "__main__":
    main()
