#!/usr/bin/env python3
"""
対話型タスクワーカー
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
from libs.conversation_manager import ConversationManager
from libs.rag_manager import RAGManager
from workers.task_worker import TaskWorker

PROJECT_DIR = Path(__file__).parent.parent
LOG_DIR = PROJECT_DIR / "logs"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [DialogTaskWorker] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "dialog_task_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DialogTaskWorker")

class DialogTaskWorker(TaskWorker):
    def __init__(self, worker_id="dialog-worker-1"):
        super().__init__(worker_id)
        self.conversation_manager = ConversationManager()
        
    def connect(self):
        """拡張接続（対話キューも含む）"""
        super().connect()
        self.channel.queue_declare(queue='dialog_task_queue', durable=True)
        self.channel.queue_declare(queue='dialog_response_queue', durable=True)
        logger.info(f"{self.worker_id} - 対話キュー接続成功")
        return True
        
    def process_dialog_task(self, ch, method, properties, body):
        """対話型タスク処理"""
        try:
            task_data = json.loads(body)
            conversation_id = task_data.get('conversation_id')
            instruction = task_data.get('instruction')
            context = task_data.get('context', {})
            
            logger.info(f"📨 対話タスク受信: {conversation_id}")
            logger.info(f"指示: {instruction[:100]}")
            
            # 会話履歴取得
            messages = self.conversation_manager.db.get_messages(conversation_id)
            conversation_context = self._build_conversation_context(messages)
            
            # RAG適用（会話履歴も含む）
            enhanced_prompt = f"{conversation_context}\n\n新しい指示: {instruction}"
            enhanced_prompt = self.rag.build_context_prompt(enhanced_prompt)
            
            # 処理実行（シミュレーション）
            if "詳細" in instruction or "？" in instruction:
                # 追加情報が必要
                response = {
                    'conversation_id': conversation_id,
                    'worker_id': self.worker_id,
                    'status': 'need_info',
                    'content': '追加情報が必要です',
                    'question': self._generate_clarification_question(instruction)
                }
            else:
                # 処理実行
                response = {
                    'conversation_id': conversation_id,
                    'worker_id': self.worker_id,
                    'status': 'progress',
                    'content': f'{instruction}を処理中です',
                    'progress': 50
                }
            
            # PMに応答送信
            self.channel.basic_publish(
                exchange='',
                routing_key='dialog_response_queue',
                body=json.dumps(response),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            # 会話記録
            self.conversation_manager.add_worker_message(
                conversation_id,
                self.worker_id,
                response['content'],
                metadata={'status': response['status']}
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"✅ 対話応答送信: {conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ 対話タスク処理エラー: {e}")
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _build_conversation_context(self, messages):
        """会話コンテキスト構築"""
        context = "【会話履歴】\n"
        for msg in messages[-10:]:  # 最新10件
            sender = msg['sender']
            content = msg['content'][:100]  # 要約
            context += f"{sender}: {content}\n"
        return context
    
    def _generate_clarification_question(self, instruction):
        """明確化質問生成"""
        if "Webアプリ" in instruction:
            return "どのような機能が必要ですか？（ユーザー認証、データベース、API等）"
        elif "データ" in instruction:
            return "どのような形式のデータですか？（CSV、JSON、データベース等）"
        else:
            return "もう少し詳しく要件を教えてください"
    
    def start(self):
        """対話型ワーカー起動"""
        if not self.connect():
            return
            
        self.channel.basic_qos(prefetch_count=1)
        
        # 通常タスクと対話タスクの両方を処理
        self.channel.basic_consume(queue='task_queue', 
                                 on_message_callback=self.process_task)
        self.channel.basic_consume(queue='dialog_task_queue',
                                 on_message_callback=self.process_dialog_task)
        
        logger.info(f"🚀 {self.worker_id} 対話型モード起動")
        
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("停止中...")
            self.channel.stop_consuming()
            self.connection.close()

if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "dialog-worker-1"
    worker = DialogTaskWorker(worker_id)
    worker.start()
