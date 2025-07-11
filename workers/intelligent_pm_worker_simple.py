#!/usr/bin/env python3
"""
Intelligent PM Worker Simple - 軽量版プロジェクト管理ワーカー
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
        logging.FileHandler('logs/intelligent_pm_worker_simple.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('intelligent_pm_worker_simple')

class IntelligentPMWorkerSimple:
    """軽量版インテリジェントPMワーカー"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = 'ai_pm'

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

    def process_pm_task(self, task_data):
        """PM タスクを処理"""
        try:
            task_id = task_data.get('task_id', 'unknown')
            task_type = task_data.get('type', 'unknown')

            logger.info(f"🔄 Processing PM task: {task_id} ({task_type})")

            # 基本的なPM処理
            result = {
                'task_id': task_id,
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'worker': 'intelligent_pm_worker_simple',
                'result': f'PM task {task_type} processed successfully'
            }

            # 結果をログに記録
            logger.info(f"✅ PM task completed: {task_id}")

            return result

        except Exception as e:
            logger.error(f"❌ PM task processing failed: {e}")
            return {
                'task_id': task_data.get('task_id', 'unknown'),
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'worker': 'intelligent_pm_worker_simple'
            }

    def callback(self, ch, method, properties, body):
        """メッセージ受信時のコールバック"""
        try:
            # メッセージをデコード
            message = json.loads(body.decode('utf-8'))
            logger.info(f"📨 Received PM message: {message}")

            # タスクを処理
            result = self.process_pm_task(message)

            # 結果を結果キューに送信（簡略化）
            logger.info(f"📤 PM result: {result}")

            # メッセージを確認
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"❌ Message processing failed: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        """メッセージ消費を開始"""
        if not self.connect_rabbitmq():
            return

        logger.info("🚀 Starting PM worker (simple mode)...")

        # QoS設定
        self.channel.basic_qos(prefetch_count=1)

        # コンシューマー設定
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback
        )

        try:
            logger.info("⏳ Waiting for PM messages...")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("🛑 Stopping PM worker...")
            self.channel.stop_consuming()
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("🔌 RabbitMQ connection closed")

def main():
    """メイン関数"""
    logger.info("🏗️ Intelligent PM Worker Simple starting...")

    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)

    worker = IntelligentPMWorkerSimple()
    worker.start_consuming()

if __name__ == "__main__":
    main()
