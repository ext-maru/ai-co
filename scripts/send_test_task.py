#!/usr/bin/env python3
import pika
import json
import sys
from datetime import datetime

def send_test_task():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='task_queue', durable=True)

        task_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = {
            "task_id": task_id,
            "prompt": "これはテスト送信用のプロンプトです。",
            "type": "test",
            "created_at": datetime.now().isoformat()
        }

        channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=json.dumps(task),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        print(f"✅ テストタスク送信成功: {task_id}")

        connection.close()
    except Exception as e:
        print(f"❌ タスク送信エラー: {e}")

if __name__ == "__main__":
    send_test_task()

