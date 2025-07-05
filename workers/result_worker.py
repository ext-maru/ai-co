#!/usr/bin/env python3
import os
import sys
import json
import pika
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR / "logs"
sys.path.append(str(PROJECT_DIR))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ResultWorker] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "result_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ResultWorker")

# Slack通知をインポート
from libs.slack_notifier import SlackNotifier

class ResultWorker:
    def __init__(self):
        # Slack通知の初期化
        self.slack_notifier = SlackNotifier()
        logger.info(f"Slack通知: {'有効' if self.slack_notifier.enabled else '無効'}")
        
    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='result_queue', durable=True)
            logger.info("RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False
    
    def send_slack_notification(self, result):
        """タスク完了時のSlack通知を送信"""
        if not self.slack_notifier.enabled:
            return
            
        try:
            # タスクの詳細情報を取得
            task_id = result.get('task_id', 'N/A')
            status = result.get('status', 'unknown')
            worker = result.get('worker', 'unknown')
            task_type = result.get('task_type', 'general')
            
            # プロンプトと応答を取得（短縮版）
            prompt = result.get('prompt', '')
            if len(prompt) > 100:
                prompt = prompt[:100] + '...'
            
            response = result.get('response', '')
            if not response and result.get('output_file'):
                response = f"出力ファイル: {result.get('output_file')}"
            if len(response) > 150:
                response = response[:150] + '...'
            
            # RAG適用の有無（将来の拡張用）
            rag_applied = result.get('rag_applied', False)
            
            # Slack通知を送信
            success = self.slack_notifier.send_task_completion_simple(
                task_id=task_id,
                worker=worker,
                prompt=prompt,
                response=response,
                status=status,
                task_type=task_type,
                rag_applied=rag_applied
            )
            
            if success:
                logger.info(f"Slack通知送信成功: タスク {task_id}")
            else:
                logger.warning(f"Slack通知送信失敗: タスク {task_id}")
                
        except Exception as e:
            logger.error(f"Slack通知送信エラー: {e}")
    
    def process_result(self, ch, method, properties, body):
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
        if not self.connect():
            return
            
        self.channel.basic_consume(
            queue='result_queue',
            on_message_callback=self.process_result
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