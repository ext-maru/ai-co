#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== Slack連携の詳細分析 ==="
echo "実行時刻: $(date)"
echo ""

# 1. 最新のログファイルを確認
echo "1. 最新のコマンド実行ログ:"
echo "----------------------------------------"
for log in ai_commands/logs/*slack*.log; do
    if [ -f "$log" ]; then
        echo "ファイル: $(basename $log)"
        echo "更新時刻: $(stat -c %y "$log" | cut -d' ' -f1,2)"
        echo "サイズ: $(stat -c %s "$log") bytes"
        echo ""
    fi
done | tail -20

# 2. Slack API応答の詳細確認
echo "2. test_slack_api_simple.pyを再実行:"
echo "----------------------------------------"
python3 test_slack_api_simple.py 2>&1 | tail -50

# 3. Polling Workerの詳細状態
echo ""
echo "3. Polling Worker詳細:"
echo "----------------------------------------"
POLLING_PID=$(pgrep -f "slack_polling_worker")
if [ -n "$POLLING_PID" ]; then
    echo "✅ プロセス発見 (PID: $POLLING_PID)"
    echo "メモリ使用:"
    ps aux | grep -E "PID|$POLLING_PID" | grep -v grep
else
    echo "❌ Polling Workerが動作していません"
fi

# 4. 最新のslack_diagnosis.logを解析
echo ""
echo "4. 診断ログ解析:"
echo "----------------------------------------"
if [ -f slack_diagnosis.log ]; then
    echo "メンション検出箇所:"
    grep -n -E "@pm-ai|メンション検出|<@U" slack_diagnosis.log | tail -10
    
    echo ""
    echo "エラー箇所:"
    grep -n -E "❌|エラー|Error|error" slack_diagnosis.log | tail -10
else
    echo "診断ログが存在しません"
fi

# 5. データベースの詳細
echo ""
echo "5. データベース詳細:"
echo "----------------------------------------"
if [ -f db/slack_messages.db ]; then
    sqlite3 db/slack_messages.db << 'SQL'
.headers on
.mode column
SELECT 
    datetime(processed_at, 'localtime') as processed_time,
    message_ts,
    substr(text, 1, 50) || '...' as text_preview
FROM processed_messages
WHERE text LIKE '%pm-ai%' OR text LIKE '%PM-AI%'
ORDER BY processed_at DESC
LIMIT 10;
SQL
else
    echo "データベースなし"
fi

# 6. 問題の特定
echo ""
echo "6. 問題の特定:"
echo "=========================================="

# メッセージが取得できているか
if grep -q "@pm-ai" slack_diagnosis.log 2>/dev/null || grep -q "メンション検出" slack_diagnosis.log 2>/dev/null; then
    echo "✅ Slackメッセージは取得できています"
    
    # Polling Workerが動作しているか
    if [ -n "$POLLING_PID" ]; then
        echo "✅ Polling Workerも動作中"
        echo ""
        echo "⚠️  問題: メッセージは取得できているがタスク化されていない"
        echo "原因候補:"
        echo "  - Polling Workerがメッセージを既に処理済みと判断"
        echo "  - RabbitMQ接続の問題"
        echo "  - タスク送信時のエラー"
    else
        echo "❌ Polling Workerが動作していません"
        echo ""
        echo "解決策: Polling Workerを起動"
    fi
else
    echo "❌ Slackメッセージが取得できていません"
    echo "原因候補:"
    echo "  - Bot Token無効"
    echo "  - チャンネルアクセス権限なし"
    echo "  - ネットワーク問題"
fi

echo ""
echo "=========================================="
