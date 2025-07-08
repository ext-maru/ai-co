#!/usr/bin/env python3
import sys
sys.path.append("/home/aicompany/ai_co")

import requests
import json
import pika
from datetime import datetime, timedelta
from core import get_config

print("🔥 強制メッセージ処理")
print("=" * 50)

config = get_config()
bot_token = config.get('slack.bot_token', '')
channel_id = config.get('slack.polling_channel_id', '')

headers = {
    'Authorization': f'Bearer {bot_token}',
    'Content-Type': 'application/json'
}

# Bot ID取得
auth_resp = requests.get('https://slack.com/api/auth.test', headers=headers)
auth_data = auth_resp.json()
bot_id = auth_data.get('user_id') if auth_data.get('ok') else None

print(f"Bot ID: {bot_id}")

# 過去30分のメッセージを取得
oldest = (datetime.now() - timedelta(minutes=30)).timestamp()
params = {
    'channel': channel_id,
    'oldest': str(oldest),
    'limit': 50
}

msg_resp = requests.get('https://slack.com/api/conversations.history', 
                      headers=headers, params=params)

if msg_resp.status_code == 200:
    msg_data = msg_resp.json()
    if msg_data.get('ok'):
        messages = msg_data.get('messages', [])
        print(f"取得メッセージ数: {len(messages)}")
        
        # RabbitMQ接続
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='ai_tasks', durable=True)
        
        processed = 0
        for msg in messages:
            if msg.get('bot_id'):
                continue
                
            text = msg.get('text', '')
            if bot_id and f'<@{bot_id}>' in text:
                clean_text = text.replace(f'<@{bot_id}>', '').strip()
                
                # 全てコードタスクとして処理
                task = {
                    'task_id': f"slack_force_{int(float(msg['ts']) * 1000000)}_code",
                    'type': 'slack_command',
                    'task_type': 'code',
                    'prompt': clean_text,
                    'source': 'slack_force',
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'slack_ts': msg['ts'],
                        'slack_user': msg.get('user', 'unknown'),
                        'slack_channel': channel_id,
                        'mentioned': True
                    }
                }
                
                channel.basic_publish(
                    exchange='',
                    routing_key='ai_tasks',
                    body=json.dumps(task),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                
                print(f"✅ 処理: {clean_text[:50]}...")
                processed += 1
        
        channel.close()
        connection.close()
        
        print(f"\n合計 {processed} 件のメッセージを処理しました")
