#!/usr/bin/env python3
import os
import sys
import json
import pika
import logging
from datetime import datetime
from pathlib import Path

sys.path.append('/root/ai_co')
from features.conversation.conversation_manager import ConversationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SimpleDialog] %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDialogWorker:
    def __init__(self):
        self.conversation_manager = ConversationManager()
        logger.info("SimpleDialogWorker初期化")
        
    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='dialog_task_queue', durable=True)
            self.channel.queue_declare(queue='dialog_response_queue', durable=True)
            logger.info("RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"接続失敗: {e}")
            return False
    
    def process_dialog_task(self, ch, method, properties, body):
        try:
            task_data = json.loads(body)
            conversation_id = task_data.get('conversation_id')
            instruction = task_data.get('instruction')
            
            logger.info(f"タスク受信: {conversation_id}")
            
            # 単純な応答を返す
            response = {
                'conversation_id': conversation_id,
                'worker_id': 'simple-dialog',
                'status': 'need_info',
                'content': '詳細を教えてください',
                'question': 'どのような機能が必要ですか？'
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='dialog_response_queue',
                body=json.dumps(response),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"応答送信: {conversation_id}")
            
        except Exception as e:
            logger.error(f"エラー: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start(self):
        if not self.connect():
            return
        
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue='dialog_task_queue',
            on_message_callback=self.process_dialog_task
        )
        
        logger.info("SimpleDialogWorker起動")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker = SimpleDialogWorker()
    worker.start()
