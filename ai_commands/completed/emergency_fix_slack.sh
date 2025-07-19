#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🔧 Slack PM-AI自動修復開始"
echo "=========================="

# RabbitMQ確認・起動
if ! sudo systemctl is-active --quiet rabbitmq-server; then
    echo "RabbitMQ起動中..."
    sudo systemctl start rabbitmq-server
    sleep 3
fi

# TMUXセッション作成
if ! tmux has-session -t ai_company 2>/dev/null; then
    echo "TMUXセッション作成中..."
    tmux new-session -d -s ai_company -n main
fi

# 既存のslack_pollingプロセスを終了
echo "既存プロセス終了中..."
pkill -f slack_polling_worker.py || true
tmux kill-window -t ai_company:slack_polling 2>/dev/null || true
sleep 2

# 基本ワーカー確認
echo "基本ワーカー起動確認..."
if ! tmux list-windows -t ai_company 2>/dev/null | grep -q "task_worker"; then
    tmux new-window -t ai_company -n task_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/task_worker.py"
    sleep 2
fi

# Slack Polling Worker起動
echo "Slack Polling Worker起動..."
tmux new-window -t ai_company -n slack_polling "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py"
sleep 3

# 起動確認
if tmux list-windows -t ai_company 2>/dev/null | grep -q "slack_polling"; then
    echo "✅ Slack Polling Worker起動成功"
else
    echo "❌ 起動失敗"
fi

# 最新メッセージ処理テスト
echo -e "
最新メッセージ処理テスト..."
python3 << 'PYTHON_EOF'
import sys
sys.path.append("/home/aicompany/ai_co")
import requests
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
    if auth_resp.status_code == 200:
        auth_data = auth_resp.json()
        if auth_data.get('ok'):
            bot_id = auth_data.get('user_id')
            print(f"Bot ID: {bot_id}")

            # 最新メッセージ取得
            params = {
                'channel': channel_id,
                'limit': 10
            }
            msg_resp = requests.get('https://slack.com/api/conversations.history',
                                  headers=headers, params=params)

            if msg_resp.status_code == 200:
                msg_data = msg_resp.json()
                if msg_data.get('ok'):
                    messages = msg_data.get('messages', [])

                    # メンション付きメッセージを探す
                    for msg in messages:
                        text = msg.get('text', '')
                        if bot_id and f'<@{bot_id}>' in text:
                            print(f"📌 未処理のメンション検出:")
                            print(f"   時刻: {msg.get('ts')}")
                            print(f"   内容: {text[:100]}...")

                            # 手動でタスク投入
                            import pika
                            import json
                            from datetime import datetime

                            try:
                                connection = pika.BlockingConnection(
                                    pika.ConnectionParameters('localhost'))
                                channel = connection.channel()
                                channel.queue_declare(queue='ai_tasks', durable=True)

                                clean_text = text.replace(f'<@{bot_id}>', '').strip()

                                task = {
                                    'task_id': f"slack_recovery_{int(float(msg['ts']) * 1000000)}_code",
                                    'type': 'slack_command',
                                    'task_type': 'code' if any(kw in clean_text.lower()
                                        for kw in ['コード', 'code', '作成', 'create', 'プログラム'])
                                        else 'general',
                                    'prompt': clean_text,
                                    'source': 'slack_recovery',
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

                                print(f"✅ タスク投入成功: {task['task_id']}")
                                channel.close()
                                connection.close()
                                break

                            except Exception as e:
                                print(f"タスク投入エラー: {e}")
PYTHON_EOF

echo -e "
📊 最終確認"
echo "==========="
ps aux | grep slack_polling_worker | grep -v grep | wc -l | xargs -I {} echo "Slack Polling Workerプロセス: {}個"
echo ""
echo "✅ 修復完了"
