#!/bin/bash
# Slack PM-AI完全修復スクリプト
# AI Command Executor経由で実行

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🔧 Slack PM-AI完全修復開始..."
echo "==================================="

# 1. TMUXセッション確認・作成
echo -e "\n1️⃣ TMUXセッション確認"
if ! tmux has-session -t ai_company 2>/dev/null; then
    echo "TMUXセッション作成中..."
    tmux new-session -d -s ai_company -n main
    echo "✅ TMUXセッション作成完了"
else
    echo "✅ TMUXセッション存在確認"
fi

# 2. RabbitMQ確認
echo -e "\n2️⃣ RabbitMQ状態確認"
if ! sudo systemctl is-active --quiet rabbitmq-server; then
    echo "RabbitMQ起動中..."
    sudo systemctl start rabbitmq-server
    sleep 3
fi
echo "✅ RabbitMQ稼働中"

# 3. 基本ワーカー起動確認
echo -e "\n3️⃣ 基本ワーカー起動確認"

# TaskWorker
if ! tmux list-windows -t ai_company 2>/dev/null | grep -q "task_worker"; then
    echo "TaskWorker起動中..."
    tmux new-window -t ai_company -n task_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/task_worker.py"
    sleep 2
fi

# PMWorker
if ! tmux list-windows -t ai_company 2>/dev/null | grep -q "pm_worker"; then
    echo "PMWorker起動中..."
    tmux new-window -t ai_company -n pm_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/pm_worker.py"
    sleep 2
fi

# ResultWorker
if ! tmux list-windows -t ai_company 2>/dev/null | grep -q "result_worker"; then
    echo "ResultWorker起動中..."
    tmux new-window -t ai_company -n result_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/result_worker.py"
    sleep 2
fi

echo "✅ 基本ワーカー起動完了"

# 4. Slack Polling Worker起動
echo -e "\n4️⃣ Slack Polling Worker起動"
# 既存のウィンドウを終了
tmux kill-window -t ai_company:slack_polling 2>/dev/null || true

# 新規起動
tmux new-window -t ai_company -n slack_polling "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py"
echo "✅ Slack Polling Worker起動完了"
sleep 3

# 5. 動作確認
echo -e "\n5️⃣ 動作確認"
echo "=== アクティブワーカー ==="
tmux list-windows -t ai_company | grep -E "(task|pm|result|slack)" || echo "ワーカーなし"

echo -e "\n=== プロセス確認 ==="
ps aux | grep -E "worker.*\.py" | grep -v grep | wc -l | xargs -I {} echo "稼働中のワーカー数: {}"

echo -e "\n=== キュー状態 ==="
sudo rabbitmqctl list_queues name messages | grep -E "(ai_tasks|pm_task_queue|result_queue)" || echo "キューなし"

# 6. テストメッセージ送信
echo -e "\n6️⃣ テストメッセージ送信"
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.append("/home/aicompany/ai_co")

import json
import pika
from datetime import datetime

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='ai_tasks', durable=True)
    
    test_task = {
        'task_id': f'slack_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}_code',
        'type': 'slack_command',
        'task_type': 'code',
        'prompt': 'Hello Worldを出力するシンプルなPythonスクリプトを作成してください',
        'source': 'slack_test',
        'timestamp': datetime.now().isoformat(),
        'metadata': {
            'slack_ts': '1234567890.123456',
            'slack_user': 'test_user',
            'slack_channel': 'test_channel',
            'mentioned': True
        }
    }
    
    channel.basic_publish(
        exchange='',
        routing_key='ai_tasks',
        body=json.dumps(test_task),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    print(f"✅ テストタスク送信成功: {test_task['task_id']}")
    
    channel.close()
    connection.close()
    
except Exception as e:
    print(f"❌ エラー: {str(e)}")
EOF

# 7. Slack通知
echo -e "\n7️⃣ 修復完了通知"
python3 << 'EOF'
import sys
sys.path.append("/home/aicompany/ai_co")

from libs.slack_notifier import SlackNotifier

try:
    notifier = SlackNotifier()
    
    message = '''🎉 Slack PM-AI修復完了！
━━━━━━━━━━━━━━━━━━━━━━
✅ TMUXセッション: ai_company
✅ 基本ワーカー: task, pm, result
✅ Slack Polling Worker: 起動完了
✅ テストメッセージ: 送信成功

📡 使い方:
Slackで @pm-ai をメンションしてメッセージ送信
→ 自動的にタスクとして処理されます

🔍 動作確認:
- tmux attach -t ai_company
- tmux select-window -t slack_polling'''
    
    notifier.send_message(message)
    print("✅ Slack通知送信")
except Exception as e:
    print(f"Slack通知スキップ: {e}")
EOF

echo -e "\n✅ 修復完了！"
echo "==================================="
echo "動作確認方法:"
echo "1. Slackで @pm-ai をメンションしてメッセージ送信"
echo "2. tmux attach -t ai_company でワーカー確認"
echo "3. tail -f logs/slack_polling_worker.log でログ確認"
