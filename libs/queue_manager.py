#!/usr/bin/env python3
"""
AI Company - RabbitMQキュー管理
"""

import pika
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)

class QueueManager:
    """RabbitMQキュー管理クラス"""
    
    def __init__(self, host='localhost', port=5672):
        self.host = host
        self.port = port
        self.connection = None
        self.channel = None
        
    def connect(self):
        """RabbitMQに接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host, port=self.port)
            )
            self.channel = self.connection.channel()
            return True
        except Exception as e:
            logger.error(f"RabbitMQ接続エラー: {e}")
            return False
    
    def disconnect(self):
        """接続を閉じる"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
    
    def get_queue_info(self) -> Dict[str, Dict[str, Any]]:
        """全キューの情報を取得"""
        queue_info = {}
        
        try:
            # rabbitmqctl を使用してキュー情報を取得
            result = subprocess.run(
                ['sudo', 'rabbitmqctl', 'list_queues', 'name', 'messages', 'consumers'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # ヘッダーをスキップ
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            queue_name = parts[0]
                            try:
                                messages = int(parts[1])
                                consumers = int(parts[2])
                                queue_info[queue_name] = {
                                    'messages': messages,
                                    'consumers': consumers
                                }
                            except ValueError:
                                continue
            else:
                # rabbitmqctl が失敗した場合、デフォルトのキューリストを返す
                default_queues = [
                    'ai_tasks',
                    'ai_pm',
                    'ai_results',
                    'dialog_task_queue',
                    'dialog_response_queue',
                    'user_input_queue'
                ]
                
                for queue in default_queues:
                    queue_info[queue] = {
                        'messages': 0,
                        'consumers': 0
                    }
                    
        except Exception as e:
            logger.error(f"キュー情報取得エラー: {e}")
            # エラー時はデフォルト値を返す
            queue_info = {
                'ai_tasks': {'messages': 0, 'consumers': 0},
                'ai_pm': {'messages': 0, 'consumers': 0},
                'ai_results': {'messages': 0, 'consumers': 0},
                'dialog_task_queue': {'messages': 0, 'consumers': 0},
                'dialog_response_queue': {'messages': 0, 'consumers': 0},
                'user_input_queue': {'messages': 0, 'consumers': 0}
            }
        
        return queue_info
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """キューを宣言"""
        if not self.channel:
            self.connect()
        
        if self.channel:
            try:
                self.channel.queue_declare(queue=queue_name, durable=durable)
                return True
            except Exception as e:
                logger.error(f"キュー宣言エラー ({queue_name}): {e}")
                return False
        return False
    
    def purge_queue(self, queue_name: str) -> Optional[int]:
        """キューをパージ（全メッセージ削除）"""
        try:
            result = subprocess.run(
                ['sudo', 'rabbitmqctl', 'purge_queue', queue_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # パージされたメッセージ数を抽出
                import re
                match = re.search(r'(\d+) messages', result.stdout)
                if match:
                    return int(match.group(1))
                return 0
            else:
                logger.error(f"キューパージエラー: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"キューパージエラー ({queue_name}): {e}")
            return None
    
    def get_queue_message_count(self, queue_name: str) -> Optional[int]:
        """特定のキューのメッセージ数を取得"""
        queue_info = self.get_queue_info()
        if queue_name in queue_info:
            return queue_info[queue_name].get('messages', 0)
        return None
    
    def __enter__(self):
        """コンテキストマネージャー用"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー用"""
        self.disconnect()
