#!/usr/bin/env python3
import pika
import json
import sys
from datetime import datetime

def send_task(prompt, task_type="general"):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        channel = connection.channel()
        channel.queue_declare(queue='task_queue', durable=True)
        
        task = {
            "task_id": f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": task_type,
            "prompt": prompt,
            "created_at": datetime.now().isoformat()
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=json.dumps(task),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        print(f"✅ タスク送信成功")
        print(f"   ID: {task['task_id']}")
        print(f"   プロンプト: {prompt[:50]}...")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: send_task.py <prompt> [type]")
        print("例: send_task.py 'Pythonでフィボナッチ数列を生成' code")
        sys.exit(1)
    
    prompt = sys.argv[1]
    task_type = sys.argv[2] if len(sys.argv) > 2 else "general"
    send_task(prompt, task_type)
