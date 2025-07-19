#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== Slack PM-AI連携 最終診断結果 ==="
echo "時刻: $(date)"
echo ""

# 1. 現在の状態サマリー
echo "【現在の状態】"
echo "=================="

# Polling Worker
if pgrep -f "slack_polling_worker" > /dev/null; then
    PID=$(pgrep -f "slack_polling_worker")
    echo "✅ Slack Polling Worker: 動作中 (PID: $PID)"
else
    echo "❌ Slack Polling Worker: 停止"
fi

# 最新のメッセージ取得状況
echo ""
echo "【最新のSlackメッセージ】"
echo "=================="
python3 << 'EOF'
import requests
import json
from datetime import datetime, timedelta

BOT_TOKEN = "xoxb-9133957021265-9120858383298-GzfwMNHREdN7oU4Amd6rVGHv"
CHANNEL_ID = "C0946R76UU8"

headers = {'Authorization': f'Bearer {BOT_TOKEN}'}
oldest = (datetime.now() - timedelta(minutes=30)).timestamp()

try:
    response = requests.get(
        'https://slack.com/api/conversations.history',
        headers=headers,
        params={'channel': CHANNEL_ID, 'oldest': str(oldest), 'limit': 10}
    )
    data = response.json()

    if data.get('ok'):
        messages = [m for m in data.get('messages', []) if '@pm-ai' in m.get('text', '').lower()]
        print(f"過去30分のPM-AIメンション数: {len(messages)}")

        for msg in messages[:3]:
            ts = datetime.fromtimestamp(float(msg['ts']))
            text = msg.get('text', '')[:100]
            print(f"  - {ts}: {text}")
    else:
        print(f"❌ API Error: {data.get('error')}")
except Exception as e:
    print(f"❌ Exception: {str(e)}")
EOF

# データベースの状態
echo ""
echo "【処理済みメッセージ】"
echo "=================="
if [ -f db/slack_messages.db ]; then
    sqlite3 db/slack_messages.db << 'SQL'
SELECT 'PM-AI関連メッセージ数:', COUNT(*)
FROM processed_messages
WHERE text LIKE '%pm-ai%' OR text LIKE '%PM-AI%';

SELECT '';
SELECT '最新3件:';
SELECT datetime(processed_at, 'localtime') as time, substr(text, 1, 60) as text
FROM processed_messages
WHERE text LIKE '%pm-ai%'
ORDER BY processed_at DESC
LIMIT 3;
SQL
else
    echo "データベースなし"
fi

# RabbitMQキュー
echo ""
echo "【RabbitMQキュー状態】"
echo "=================="
sudo rabbitmqctl list_queues name messages | grep ai_tasks || echo "キュー情報取得失敗"

# エラーログ
echo ""
echo "【最新のエラー】"
echo "=================="
if [ -f logs/slack_polling_worker.log ]; then
    grep -E "Error|error|Exception|Failed" logs/slack_polling_worker.log | tail -5 || echo "エラーなし"
else
    echo "ログファイルなし"
fi

echo ""
echo "【診断結果】"
echo "=================="

# 診断ロジック
WORKER_OK=false
MESSAGE_OK=false
DB_OK=false

if pgrep -f "slack_polling_worker" > /dev/null; then
    WORKER_OK=true
fi

# この部分は前のPythonスクリプトの結果に基づく
# 実際にはもっと詳細なチェックが必要

if [ "$WORKER_OK" = true ]; then
    echo "✅ ワーカーは正常に動作しています"
else
    echo "❌ ワーカーが動作していません"
    echo "   対処法: tmux new -s slack_polling -d 'cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py'"
fi

echo ""
echo "【推奨アクション】"
echo "=================="
echo "1. 新しいテストメッセージを送信:"
echo "   Slackで: @pm-ai test$(date +%s)"
echo ""
echo "2. ログ監視:"
echo "   tail -f logs/slack_polling_worker.log"
echo ""
echo "3. 手動でワーカー起動（必要な場合）:"
echo "   cd /home/aicompany/ai_co && source venv/bin/activate"
echo "   python3 workers/slack_polling_worker.py"
