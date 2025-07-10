#!/usr/bin/env python3
"""
タスク送信ユーティリティ
ai-sendコマンドと同じ機能を提供
"""

import json
import pika
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# プロジェクトルートをPythonパスに追加
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.common_utils import generate_task_id, EMOJI


def send_task(prompt: str, task_type: str = "code", priority: str = "normal") -> Optional[str]:
    """
    タスクをキューに送信
    
    Args:
        prompt: タスクのプロンプト
        task_type: タスクタイプ（code/general）
        priority: 優先度（critical/high/normal/low）
        
    Returns:
        task_id: 成功時はタスクID、失敗時はNone
    """
    logger = logging.getLogger(__name__)
    
    try:
        # タスクID生成
        task_id = generate_task_id(task_type)
        
        # タスクデータ作成
        task_data = {
            "task_id": task_id,
            "type": task_type,
            "prompt": prompt,
            "priority": priority,
            "created_at": datetime.now().isoformat()
        }
        
        # RabbitMQ接続
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        channel = connection.channel()
        
        # キュー宣言
        queue_name = 'ai_tasks'
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={'x-max-priority': 10}
        )
        
        # 優先度マッピング
        priority_map = {
            'critical': 10,
            'high': 7,
            'normal': 5,
            'low': 3
        }
        
        # メッセージ送信
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(task_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # 永続化
                priority=priority_map.get(priority, 5)
            )
        )
        
        connection.close()
        
        logger.info(f"{EMOJI['send']} Task sent: {task_id}")
        return task_id
        
    except Exception as e:
        logger.error(f"{EMOJI['error']} Failed to send task: {str(e)}")
        return None


def send_dialog_task(initial_prompt: str, priority: str = "normal") -> Optional[str]:
    """
    対話型タスクをキューに送信
    
    Args:
        initial_prompt: 初期プロンプト
        priority: 優先度
        
    Returns:
        conversation_id: 成功時は会話ID、失敗時はNone
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 会話ID生成
        conversation_id = generate_task_id("conv_dialog")
        
        # タスクデータ作成
        task_data = {
            "conversation_id": conversation_id,
            "initial_prompt": initial_prompt,
            "priority": priority,
            "created_at": datetime.now().isoformat()
        }
        
        # RabbitMQ接続
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        channel = connection.channel()
        
        # キュー宣言
        queue_name = 'ai_dialog'
        channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={'x-max-priority': 10}
        )
        
        # 優先度マッピング
        priority_map = {
            'critical': 10,
            'high': 7,
            'normal': 5,
            'low': 3
        }
        
        # メッセージ送信
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(task_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # 永続化
                priority=priority_map.get(priority, 5)
            )
        )
        
        connection.close()
        
        logger.info(f"{EMOJI['send']} Dialog task sent: {conversation_id}")
        return conversation_id
        
    except Exception as e:
        logger.error(f"{EMOJI['error']} Failed to send dialog task: {str(e)}")
        return None


def send_reply(conversation_id: str, reply: str) -> bool:
    """
    対話への返信を送信
    
    Args:
        conversation_id: 会話ID
        reply: 返信内容
        
    Returns:
        成功かどうか
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 返信データ作成
        reply_data = {
            "conversation_id": conversation_id,
            "reply": reply,
            "created_at": datetime.now().isoformat()
        }
        
        # RabbitMQ接続
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        channel = connection.channel()
        
        # キュー宣言
        queue_name = 'ai_dialog'
        channel.queue_declare(queue=queue_name, durable=True)
        
        # メッセージ送信
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(reply_data),
            properties=pika.BasicProperties(
                delivery_mode=2  # 永続化
            )
        )
        
        connection.close()
        
        logger.info(f"{EMOJI['send']} Reply sent for: {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"{EMOJI['error']} Failed to send reply: {str(e)}")
        return False


if __name__ == "__main__":
    # テスト実行
    import argparse
    
    parser = argparse.ArgumentParser(description='Send task to Elders Guild')
    parser.add_argument('prompt', help='Task prompt')
    parser.add_argument('type', choices=['code', 'general'], help='Task type')
    parser.add_argument('--priority', choices=['critical', 'high', 'normal', 'low'],
                       default='normal', help='Task priority')
    
    args = parser.parse_args()
    
    task_id = send_task(args.prompt, args.type, args.priority)
    if task_id:
        print(f"Task sent successfully: {task_id}")
    else:
        print("Failed to send task")
