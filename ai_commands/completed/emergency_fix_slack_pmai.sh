#!/bin/bash
# Slack PM-AI緊急修復（よくある問題対応）

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🚨 Slack PM-AI緊急修復"
echo "======================"

# 1. プロセス強制終了と再起動
echo "1. プロセスクリーンアップ..."
pkill -f slack_polling_worker.py || true
sleep 2

# 2. TMUXウィンドウ再作成
echo "2. TMUXウィンドウ再作成..."
tmux kill-window -t ai_company:slack_polling 2>/dev/null || true
tmux new-window -t ai_company -n slack_polling "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py"
sleep 3

# 3. DB初期化（過去のメッセージスキップ）
echo "3. Slack DB初期化..."
python3 << 'EOF'
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

db_path = Path("/home/aicompany/ai_co/db/slack_messages.db")
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(db_path)
conn.execute('''
    CREATE TABLE processed_messages (
        message_ts TEXT PRIMARY KEY,
        channel_id TEXT NOT NULL,
        user_id TEXT,
        text TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# 1時間前のタイムスタンプを初期値として設定
old_ts = (datetime.now() - timedelta(hours=1)).timestamp()
conn.execute(
    "INSERT INTO processed_messages (message_ts, channel_id, user_id, text) VALUES (?, ?, ?, ?)",
    (str(old_ts), 'init', 'system', 'initialization')
)
conn.commit()
conn.close()
print("✅ DB初期化完了")
EOF

# 4. 最新メッセージ強制処理
echo -e "\n4. 最新メッセージ強制処理..."
python3 << 'EOF'
import sys
sys.path.append("/home/aicompany/ai_co")

import requests
import json
import pika
from datetime import datetime, timedelta
from core import get_config

config = get_config()
bot_token = config.get('slack.bot_token', '')
channel_id = config.get('slack.polling_channel_id', '')

if bot_token and channel_id:
    headers = {
        'Authorization': f'Bearer {bot_token}',
        'Content-Type': 'application/json'
    }
    
    # Bot ID取得
    auth_resp = requests.get('https://slack.com/api/auth.test', headers=headers)
    bot_id = None
    if auth_resp.status_code == 200:
        auth_data = auth_resp.json()
        if auth_data.get('ok'):
            bot_id = auth_data.get('user_id')
            print(f"Bot ID: {bot_id}")
    
    # 最新メッセージ取得（過去30分）
    oldest = (datetime.now() - timedelta(minutes=30)).timestamp()
    params = {
        'channel': channel_id,
        'oldest': str(oldest),
        'limit': 20
    }
    
    msg_resp = requests.get('https://slack.com/api/conversations.history', 
                          headers=headers, params=params)
    
    if msg_resp.status_code == 200:
        msg_data = msg_resp.json()
        if msg_data.get('ok'):
            messages = msg_data.get('messages', [])
            print(f"メッセージ数: {len(messages)}")
            
            # メンション付きメッセージを処理
            processed = 0
            
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
                channel = connection.channel()
                channel.queue_declare(queue='ai_tasks', durable=True)
                
                for msg in messages:
                    if msg.get('bot_id'):
                        continue
                    
                    text = msg.get('text', '')
                    if bot_id and f'<@{bot_id}>' in text:
                        clean_text = text.replace(f'<@{bot_id}>', '').strip()
                        
                        task = {
                            'task_id': f"slack_emergency_{int(float(msg['ts']) * 1000000)}_code",
                            'type': 'slack_command',
                            'task_type': 'code',
                            'prompt': clean_text,
                            'source': 'slack_emergency',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        channel.basic_publish(
                            exchange='',
                            routing_key='ai_tasks',
                            body=json.dumps(task),
                            properties=pika.BasicProperties(delivery_mode=2)
                        )
                        
                        print(f"✅ 処理: {clean_text[:50]}...")
                        processed += 1
                        
                        # リアクション追加
                        reaction_data = {
                            'channel': channel_id,
                            'timestamp': msg['ts'],
                            'name': 'robot_face'
                        }
                        requests.post('https://slack.com/api/reactions.add', 
                                    headers=headers, json=reaction_data)
                        
                        if processed >= 3:  # 最大3件まで
                            break
                
                channel.close()
                connection.close()
                
            except Exception as e:
                print(f"エラー: {str(e)}")
            
            print(f"処理数: {processed}件")
else:
    print("Slack設定エラー")
EOF

# 5. 確認
echo -e "\n5. 動作確認..."
ps aux | grep slack_polling_worker.py | grep -v grep && echo "✅ プロセス稼働中" || echo "❌ プロセスなし"
tmux list-windows -t ai_company | grep slack_polling && echo "✅ TMUXウィンドウ存在" || echo "❌ ウィンドウなし"

# 6. Slack通知
python3 << 'EOF'
import sys
sys.path.append("/home/aicompany/ai_co")
from libs.slack_notifier import SlackNotifier

try:
    notifier = SlackNotifier()
    notifier.send_message(
        "🚨 緊急修復完了\n"
        "Slack Polling Worker再起動\n"
        "DB初期化済み\n"
        "最新メッセージ処理済み\n\n"
        "@pm-ai でメンションしてください"
    )
except:
    pass
EOF

echo -e "\n✅ 緊急修復完了"
echo "Slackで @pm-ai をメンションしてテストしてください"
