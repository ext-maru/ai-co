#!/usr/bin/env python3
"""
タスク送信ヘルパー
各種キューへのタスク送信を簡単に行うためのユーティリティ
"""

import json
import pika
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import logging

# プロジェクトルートをPythonパスに追加
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import get_config


class TaskSender:
    """タスク送信を管理するヘルパークラス"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """RabbitMQに接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            self.channel = self.connection.channel()
            
            # 基本的なキューを宣言（priority付き）
            queues = ['ai_tasks', 'ai_pm', 'ai_results', 'ai_dialog', 'ai_se', 'ai_error_analysis']
            for queue in queues:
                self.channel.queue_declare(
                    queue=queue, 
                    durable=True,
                    arguments={"x-max-priority": 10}
                )
                
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def send_to_queue(self, queue_name: str, message: Dict, priority: Optional[int] = None) -> bool:
        """指定されたキューにメッセージを送信"""
        try:
            # メッセージにタイムスタンプを追加
            if 'timestamp' not in message:
                message['timestamp'] = datetime.now().isoformat()
            
            # プロパティ設定
            properties = pika.BasicProperties(
                delivery_mode=2,  # 永続化
                timestamp=int(datetime.now().timestamp()),
                content_type='application/json'
            )
            
            # 優先度設定
            if priority is not None:
                properties.priority = priority
            
            # メッセージ送信
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message, ensure_ascii=False),
                properties=properties
            )
            
            self.logger.info(f"Message sent to {queue_name}: task_id={message.get('task_id', 'unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {queue_name}: {e}")
            return False
    
    def send_task(self, prompt: str, task_type: str = 'code', 
                  priority: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """新しいタスクを作成して送信"""
        # タスクID生成
        task_id = f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # タスクメッセージ作成
        task = {
            'task_id': task_id,
            'task_type': task_type,
            'prompt': prompt,
            'created_at': datetime.now().isoformat()
        }
        
        # メタデータ追加
        if metadata:
            task['metadata'] = metadata
        
        # 優先度マッピング
        priority_map = {
            'critical': 10,
            'high': 7,
            'normal': 5,
            'low': 3
        }
        
        priority_value = priority_map.get(priority, 5) if priority else 5
        
        # 送信
        success = self.send_to_queue('ai_tasks', task, priority_value)
        
        if success:
            return task_id
        else:
            raise Exception("Failed to send task")
    
    def send_to_pm(self, files_created: list, task_id: str, 
                    git_commit: bool = True, metadata: Optional[Dict] = None) -> bool:
        """PMワーカーにファイル配置タスクを送信"""
        pm_task = {
            'task_id': task_id,
            'files_created': files_created,
            'git_commit': git_commit,
            'created_at': datetime.now().isoformat()
        }
        
        if metadata:
            pm_task['metadata'] = metadata
        
        return self.send_to_queue('ai_pm', pm_task)
    
    def send_to_result(self, task_id: str, result: Any, 
                       success: bool = True, metadata: Optional[Dict] = None) -> bool:
        """結果ワーカーに結果を送信"""
        result_message = {
            'task_id': task_id,
            'result': result,
            'success': success,
            'completed_at': datetime.now().isoformat()
        }
        
        if metadata:
            result_message['metadata'] = metadata
        
        return self.send_to_queue('ai_results', result_message)
    
    def send_dialog_message(self, conversation_id: str, role: str, 
                           content: str, metadata: Optional[Dict] = None) -> bool:
        """対話型タスクワーカーにメッセージを送信"""
        dialog_message = {
            'conversation_id': conversation_id,
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        if metadata:
            dialog_message['metadata'] = metadata
        
        return self.send_to_queue('ai_dialog', dialog_message)
    
    def send_to_se_tester(self, files_to_test: list, task_id: str, 
                          test_type: str = 'unit', metadata: Optional[Dict] = None) -> bool:
        """SE-Testerワーカーにテストタスクを送信"""
        test_task = {
            'task_id': task_id,
            'files_to_test': files_to_test,
            'test_type': test_type,
            'created_at': datetime.now().isoformat()
        }
        
        if metadata:
            test_task['metadata'] = metadata
        
        return self.send_to_queue('ai_se', test_task)
    
    def send_error_analysis_request(self, error_text: str, context: Dict, 
                                   response_queue: Optional[str] = None) -> bool:
        """エラー分析リクエストを送信"""
        analysis_request = {
            'error_text': error_text,
            'context': context,
            'request_id': f"err_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'response_queue': response_queue
        }
        
        return self.send_to_queue('ai_error_analysis', analysis_request)
    
    def close(self):
        """接続をクローズ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
    
    def __enter__(self):
        """with文のサポート"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """with文のクリーンアップ"""
        self.close()


if __name__ == "__main__":
    # テスト実行
    sender = TaskSender()
    
    print("=== TaskSender Test ===")
    
    # 通常タスク送信テスト
    task_id = sender.send_task(
        "Create a Python function to calculate fibonacci numbers",
        task_type="code",
        priority="normal"
    )
    print(f"Task sent: {task_id}")
    
    # PMタスク送信テスト
    success = sender.send_to_pm(
        files_created=["test_fibonacci.py"],
        task_id=task_id,
        git_commit=True
    )
    print(f"PM task sent: {success}")
    
    # エラー分析リクエストテスト
    success = sender.send_error_analysis_request(
        error_text="ModuleNotFoundError: No module named 'numpy'",
        context={'worker_type': 'task', 'task_id': task_id}
    )
    print(f"Error analysis request sent: {success}")
    
    sender.close()
