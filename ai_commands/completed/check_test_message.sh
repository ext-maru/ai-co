#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== 最新のSlackメッセージ確認 ==="
echo "時刻: $(date)"
echo ""

# 1. 最新のSlackメッセージ（過去3分）
echo "【Slack API経由でメッセージ取得】"
python3 << 'EOF'
import requests
import json
from datetime import datetime, timedelta

BOT_TOKEN = "xoxb-9133957021265-9120858383298-GzfwMNHREdN7oU4Amd6rVGHv"
CHANNEL_ID = "C0946R76UU8"

headers = {'Authorization': f'Bearer {BOT_TOKEN}'}
oldest = (datetime.now() - timedelta(minutes=3)).timestamp()

try:
    response = requests.get(
        'https://slack.com/api/conversations.history',
        headers=headers,
        params={'channel': CHANNEL_ID, 'oldest': str(oldest), 'limit': 10}
    )
    data = response.json()
    
    if data.get('ok'):
        messages = data.get('messages', [])
        print(f"✅ 過去3分のメッセージ数: {len(messages)}")
        
        # Bot User ID取得
        auth_resp = requests.get('https://slack.com/api/auth.test', headers=headers)
        bot_id = auth_resp.json().get('user_id', '')
        
        for i, msg in enumerate(messages):
            ts = datetime.fromtimestamp(float(msg['ts']))
            text = msg.get('text', '')
            user = msg.get('user', 'unknown')
            
            # メンション確認
            has_pmai = '@pm-ai' in text.lower()
            has_bot_id = f'<@{bot_id}>' in text if bot_id else False
            
            print(f"
メッセージ {i+1}:")
            print(f"  時刻: {ts}")
            print(f"  ユーザー: {user}")
            print(f"  テキスト: {text[:100]}")
            print(f"  @pm-ai メンション: {'✅' if has_pmai else '❌'}")
            print(f"  Bot IDメンション: {'✅' if has_bot_id else '❌'}")
            
            if has_pmai or has_bot_id:
                print("  ⭐ このメッセージは処理対象です！")
    else:
        print(f"❌ API Error: {data.get('error')}")
except Exception as e:
    print(f"❌ Exception: {str(e)}")
EOF

echo ""
echo "【Slack Polling Workerの状態】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    PID=$(pgrep -f "slack_polling_worker")
    echo "✅ 動作中 (PID: $PID)"
    
    # 最新のログ（特にメッセージ処理部分）
    echo ""
    echo "最新のWorkerログ:"
    if [ -f logs/slack_polling_worker.log ]; then
        tail -30 logs/slack_polling_worker.log | grep -E "新規メッセージ|メンション|タスク化|処理|slack_" || tail -10 logs/slack_polling_worker.log
    fi
else
    echo "❌ 動作していません"
fi

echo ""
echo "【データベース確認】"
if [ -f db/slack_messages.db ]; then
    echo "最新の処理済みメッセージ:"
    sqlite3 db/slack_messages.db << 'SQL'
SELECT 
    datetime(processed_at, 'localtime') as time,
    message_ts,
    substr(text, 1, 80) as text
FROM processed_messages
ORDER BY processed_at DESC
LIMIT 5;
SQL
else
    echo "データベースが存在しません"
fi

echo ""
echo "【RabbitMQキュー確認】"
QUEUE_STATUS=$(sudo rabbitmqctl list_queues name messages 2>/dev/null | grep ai_tasks || echo "取得失敗")
echo "ai_tasks キュー: $QUEUE_STATUS"

echo ""
echo "【問題の診断】"
echo "=================================="

# 診断ロジック
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "✅ Workerは動作している"
    
    # ログに最近のアクティビティがあるか
    if [ -f logs/slack_polling_worker.log ]; then
        LAST_LOG=$(tail -1 logs/slack_polling_worker.log)
        echo "最終ログ: $LAST_LOG"
        
        if grep -q "タスク化" logs/slack_polling_worker.log; then
            echo "✅ タスク化の記録あり"
        else
            echo "⚠️  タスク化の記録なし - メッセージが処理されていない可能性"
        fi
    fi
else
    echo "❌ Workerが動作していない - 起動が必要"
fi

echo "=================================="
