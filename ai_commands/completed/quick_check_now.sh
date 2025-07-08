#!/bin/bash
cd /home/aicompany/ai_co

echo "=== 即時状態確認 ==="
echo ""

# 1. テストメッセージが見えているか
echo "【最新のSlackメッセージ（簡易確認）】"
python3 -c "
import requests
from datetime import datetime, timedelta

token = 'xoxb-9133957021265-9120858383298-GzfwMNHREdN7oU4Amd6rVGHv'
channel = 'C0946R76UU8'
headers = {'Authorization': f'Bearer {token}'}

try:
    response = requests.get(
        'https://slack.com/api/conversations.history',
        headers=headers,
        params={'channel': channel, 'oldest': str((datetime.now() - timedelta(minutes=5)).timestamp()), 'limit': 5}
    )
    data = response.json()
    if data.get('ok'):
        for msg in data.get('messages', []):
            if '@pm-ai' in msg.get('text', '').lower():
                print(f'✅ メンション検出: {msg.get(\"text\", \"\")[:80]}')
                print(f'   時刻: {datetime.fromtimestamp(float(msg[\"ts\"]))}')
except Exception as e:
    print(f'❌ エラー: {str(e)}')
"

echo ""
echo "【Slack Polling Worker】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "✅ 動作中"
    echo "最新ログ（最後の5行）:"
    tail -5 logs/slack_polling_worker.log 2>/dev/null || echo "ログなし"
else
    echo "❌ 停止中"
fi

echo ""
echo "【結論】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    if tail -10 logs/slack_polling_worker.log 2>/dev/null | grep -q "タスク化"; then
        echo "✅ メッセージは正常に処理されています"
    else
        echo "⚠️  Workerは動作中だがメッセージが処理されていない可能性"
    fi
else
    echo "❌ Slack Polling Workerを起動する必要があります"
fi