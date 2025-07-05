#!/usr/bin/env python3
"""
対話制御PMワーカー
"""
import os
import sys
import json
import pika
import logging
import traceback
from datetime import datetime
from pathlib import Path

sys.path.append('/root/ai_co')
from features.conversation.conversation_manager import ConversationManager
from features.notification.slack_notifier import SlackNotifier

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR / "logs"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [DialogPM] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "dialog_pm_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DialogPM")

class DialogPMWorker:
    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.slack = SlackNotifier()
        
    def connect(self):
        """RabbitMQ接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            
            # キュー宣言
            self.channel.queue_declare(queue='dialog_response_queue', durable=True)
            self.channel.queue_declare(queue='user_input_queue', durable=True)
            self.channel.queue_declare(queue='dialog_task_queue', durable=True)
            
            logger.info("RabbitMQ接続成功")
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続失敗: {e}")
            return False
    
    def process_worker_response(self, ch, method, properties, body):
        """ワーカーからの応答処理"""
        try:
            response = json.loads(body)
            conversation_id = response['conversation_id']
            status = response['status']
            content = response['content']
            
            logger.info(f"📨 ワーカー応答: {conversation_id} - {status}")
            
            if status == 'need_info':
                # ユーザー入力が必要
                question = response.get('question', '詳細を教えてください')
                self.conversation_manager.request_user_input(
                    conversation_id, question
                )
                
                # Slack通知
                self._notify_user_input_needed(conversation_id, question)
                
            elif status == 'progress':
                # 進捗更新
                progress = response.get('progress', 0)
                logger.info(f"進捗: {progress}%")
                
                if progress < 100:
                    # 次の指示を送信
                    self._send_next_instruction(conversation_id)
                    
            elif status == 'completed':
                # 完了
                self.conversation_manager.complete_conversation(
                    conversation_id, content
                )
                self._notify_completion(conversation_id, content)
                
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"応答処理エラー: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def process_user_input(self, ch, method, properties, body):
        """ユーザー入力処理"""
        try:
            input_data = json.loads(body)
            conversation_id = input_data['conversation_id']
            user_response = input_data['response']
            
            logger.info(f"👤 ユーザー入力: {conversation_id}")
            
            # 会話に記録
            self.conversation_manager.add_user_response(
                conversation_id, user_response
            )
            
            # ワーカーに新しい指示送信
            task_data = {
                'conversation_id': conversation_id,
                'instruction': user_response,
                'context': {'from_user': True}
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='dialog_task_queue',
                body=json.dumps(task_data),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"ユーザー入力処理エラー: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _notify_user_input_needed(self, conversation_id, question):
        """ユーザー入力必要通知"""
        message = f"🤔 ユーザー入力が必要です\n\n"
        message += f"会話ID: {conversation_id}\n"
        message += f"質問: {question}\n\n"
        message += f"返答方法: `ai-reply {conversation_id} 回答内容`"
        
        self.slack.send_notification(message)
    
    def _notify_completion(self, conversation_id, result):
        """完了通知"""
        message = f"✅ タスク完了\n\n"
        message += f"会話ID: {conversation_id}\n"
        message += f"結果: {result[:200]}..."
        
        self.slack.send_notification(message)
    
    def _send_next_instruction(self, conversation_id):
        """次の指示送信"""
        # 会話履歴から次のステップを決定
        messages = self.conversation_manager.db.get_messages(conversation_id)
        
        # シンプルな例：段階的な指示
        instruction = "続きの処理を実行してください"
        
        task_data = {
            'conversation_id': conversation_id,
            'instruction': instruction,
            'context': {'step': len(messages)}
        }
        
        self.channel.basic_publish(
            exchange='',
            routing_key='dialog_task_queue',
            body=json.dumps(task_data),
            properties=pika.BasicProperties(delivery_mode=2)
        )
    
    def start(self):
        """PM起動"""
        if not self.connect():
            return
            
        self.channel.basic_qos(prefetch_count=1)
        
        # 応答とユーザー入力を処理
        self.channel.basic_consume(
            queue='dialog_response_queue',
            on_message_callback=self.process_worker_response
        )
        self.channel.basic_consume(
            queue='user_input_queue',
            on_message_callback=self.process_user_input
        )
        
        logger.info("🚀 Dialog PM Worker起動")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("停止中...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker = DialogPMWorker()
    worker.start()
