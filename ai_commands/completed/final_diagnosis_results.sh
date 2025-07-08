#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== 診断結果サマリー ==="
echo ""

# 1. 最新の診断ログから結果を抽出
echo "【最新の診断結果】"
for log in ai_commands/logs/*slack*.log; do
    if [ -f "$log" ]; then
        filename=$(basename "$log")
        # 重要な結果のみ抽出
        if grep -q "✅ 過去3分のメッセージ数:" "$log" 2>/dev/null; then
            echo ""
            echo "ファイル: $filename"
            grep -E "(✅ 過去3分のメッセージ数:|⭐ このメッセージは処理対象|@pm-ai|テスト)" "$log" | head -10
        fi
        
        if grep -q "Slack Polling Worker" "$log" 2>/dev/null; then
            grep -E "(✅ 動作中|❌ 動作していません|✅ タスク化の記録|⚠️  タスク化の記録なし)" "$log" | head -5
        fi
    fi
done | tail -30

echo ""
echo "【現在の状態】"
# Workerプロセス
if pgrep -f "slack_polling_worker" > /dev/null; then
    PID=$(pgrep -f "slack_polling_worker")
    echo "✅ Slack Polling Worker: 動作中 (PID: $PID)"
    
    # 最新のログ確認
    if [ -f logs/slack_polling_worker.log ]; then
        echo ""
        echo "最新のWorkerログ（重要部分）:"
        tail -50 logs/slack_polling_worker.log | grep -E "(新規メッセージ|タスク化|メンション|Error|処理)" | tail -10
        
        # タスク投入の記録を探す
        if tail -100 logs/slack_polling_worker.log | grep -q "タスク化"; then
            echo "✅ 最近タスク化の記録あり"
        else
            echo "⚠️  最近タスク化の記録なし"
        fi
    fi
else
    echo "❌ Slack Polling Worker: 停止中"
fi

echo ""
echo "【データベース状態】"
if [ -f db/slack_messages.db ]; then
    echo "処理済みメッセージ（最新5件）:"
    sqlite3 db/slack_messages.db << 'SQL' 2>/dev/null || echo "DB読み取りエラー"
SELECT 
    datetime(processed_at, 'localtime') as time,
    substr(text, 1, 60) as text
FROM processed_messages
WHERE text LIKE '%pm-ai%' OR text LIKE '%テスト%'
ORDER BY processed_at DESC
LIMIT 5;
SQL
fi

echo ""
echo "【問題の特定】"
echo "================================"

# 問題診断ロジック
WORKER_OK=false
MESSAGE_RECEIVED=false
TASK_CREATED=false

if pgrep -f "slack_polling_worker" > /dev/null; then
    WORKER_OK=true
fi

# メッセージ受信確認（簡易チェック）
if [ -f ai_commands/logs/check_test_message*.log ]; then
    if grep -q "✅ 過去3分のメッセージ数: [1-9]" ai_commands/logs/check_test_message*.log 2>/dev/null; then
        MESSAGE_RECEIVED=true
    fi
fi

# タスク作成確認
if [ -f logs/slack_polling_worker.log ]; then
    if tail -200 logs/slack_polling_worker.log | grep -q "タスク化"; then
        TASK_CREATED=true
    fi
fi

# 診断結果
if [ "$WORKER_OK" = false ]; then
    echo "❌ 主要問題: Slack Polling Workerが動作していません"
    echo "   対処: ワーカーを起動する必要があります"
elif [ "$MESSAGE_RECEIVED" = false ]; then
    echo "❌ 主要問題: Slackメッセージが取得できていません"
    echo "   対処: Bot Token/チャンネル権限を確認"
elif [ "$TASK_CREATED" = false ]; then
    echo "⚠️  主要問題: メッセージは受信しているがタスク化されていません"
    echo "   対処: ワーカーの内部処理を確認"
else
    echo "✅ システムは正常に動作しているようです"
fi

echo "================================"
