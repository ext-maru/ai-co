#!/bin/bash
# Slack即時メッセージ処理

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🚀 Slack即時メッセージ処理"
echo "========================"

# Pythonで直接処理
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

if not bot_token or not channel_id:
    print("❌ Slack設定エラー")
    exit(1)

headers = {
    'Authorization': f'Bearer {bot_token}',
    'Content-Type': 'application/json'
}

# Bot ID取得
print("Bot ID取得中...")
auth_resp = requests.get('https://slack.com/api/auth.test', headers=headers)
if auth_resp.status_code == 200:
    auth_data = auth_resp.json()
    if auth_data.get('ok'):
        bot_id = auth_data.get('user_id')
        print(f"✅ Bot ID: {bot_id}")
    else:
        print(f"❌ 認証エラー: {auth_data.get('error')}")
        exit(1)
else:
    print(f"❌ API接続エラー")
    exit(1)

# 最新メッセージ取得（過去5分）
print("\n最新メッセージ取得中...")
oldest = (datetime.now() - timedelta(minutes=5)).timestamp()
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
        print(f"✅ {len(messages)}件のメッセージ取得")

        # メンション付きメッセージを探す
        mention_found = False

        for msg in messages:
            if msg.get('bot_id'):
                continue

            text = msg.get('text', '')
            if bot_id and f'<@{bot_id}>' in text:
                mention_found = True
                print(f"\n📌 メンション検出!")
                print(f"   時刻: {msg.get('ts')}")
                print(f"   内容: {text[:100]}")

                # タスク作成
                clean_text = text.replace(f'<@{bot_id}>', '').strip()

                try:
                    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
                    channel = connection.channel()
                    channel.queue_declare(queue='ai_tasks', durable=True)

                    task = {
                        'task_id': f"slack_immediate_{int(float(msg['ts']) * 1000000)}_code",
                        'type': 'slack_command',
                        'task_type': 'code',
                        'prompt': clean_text,
                        'source': 'slack',
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

                    print(f"   ✅ タスク投入成功: {task['task_id']}")

                    # リアクション追加
                    reaction_data = {
                        'channel': channel_id,
                        'timestamp': msg['ts'],
                        'name': 'eyes'
                    }
                    requests.post('https://slack.com/api/reactions.add',
                                headers=headers, json=reaction_data)

                    channel.close()
                    connection.close()

                    # Slack通知
                    from libs.slack_notifier import SlackNotifier
                    notifier = SlackNotifier()
                    notifier.send_message(f"👀 タスク受信: {clean_text[:50]}...\\n処理を開始します")

                    break  # 最新の1件のみ処理

                except Exception as e:
                    print(f"   ❌ エラー: {str(e)}")

        if not mention_found:
            print("\n📌 メンション付きメッセージが見つかりません")
            print("   Slackで @pm-ai をメンションしてメッセージを送信してください")
    else:
        print(f"❌ メッセージ取得エラー: {msg_data.get('error')}")
else:
    print(f"❌ API接続エラー: {msg_resp.status_code}")

print("\n✅ 処理完了")
EOF

# キュー確認
echo ""
echo "キュー状態:"
sudo rabbitmqctl list_queues name messages | grep ai_tasks || echo "キューなし"
