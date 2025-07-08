#!/bin/bash
# SlackWorker診断スクリプト
# 緊急時の問題診断用

echo "🔍 SlackWorker診断スクリプト - $(date)"
echo "============================================="

# 1. プロセス状態確認
echo "📋 1. プロセス状態確認"
SLACK_PID=$(pgrep -f "slack_polling_worker.py")
if [ -n "$SLACK_PID" ]; then
    echo "✅ SlackWorker実行中 (PID: $SLACK_PID)"
    echo "   プロセス状態: $(ps -o stat= -p $SLACK_PID)"
    echo "   開始時刻: $(ps -o lstart= -p $SLACK_PID)"
    echo "   CPU使用率: $(ps -o %cpu= -p $SLACK_PID)%"
    echo "   メモリ使用量: $(ps -o %mem= -p $SLACK_PID)%"
else
    echo "❌ SlackWorkerが実行されていません"
fi

# 2. ログ確認
echo -e "\n📝 2. 最新ログ確認 (直近10行)"
if [ -f "/home/aicompany/ai_co/logs/slack_polling_worker.log" ]; then
    tail -10 "/home/aicompany/ai_co/logs/slack_polling_worker.log"
else
    echo "❌ ログファイルが見つかりません"
fi

# 3. Slack API接続テスト
echo -e "\n🌐 3. Slack API接続テスト"
if [ -f "/home/aicompany/ai_co/.env" ]; then
    source /home/aicompany/ai_co/.env
    if [ -n "$SLACK_BOT_TOKEN" ]; then
        SLACK_TEST=$(curl -s -X GET "https://slack.com/api/auth.test" \
            -H "Authorization: Bearer $SLACK_BOT_TOKEN" | jq -r '.ok')
        if [ "$SLACK_TEST" = "true" ]; then
            echo "✅ Slack API接続正常"
        else
            echo "❌ Slack API接続エラー"
        fi
    else
        echo "❌ SLACK_BOT_TOKEN未設定"
    fi
else
    echo "❌ .envファイルが見つかりません"
fi

# 4. RabbitMQ接続確認
echo -e "\n🐰 4. RabbitMQ接続確認"
if ss -tuln | grep -q ":5672"; then
    echo "✅ RabbitMQポート開放中"
else
    echo "❌ RabbitMQポート未開放"
fi

# 5. ネットワーク接続確認
echo -e "\n🔗 5. SlackWorkerネットワーク接続"
if [ -n "$SLACK_PID" ]; then
    echo "アクティブな接続:"
    lsof -p $SLACK_PID 2>/dev/null | grep -E "(TCP|UDP)" || echo "接続情報取得失敗"
else
    echo "プロセスが存在しないため、接続確認不可"
fi

# 6. 推奨アクション
echo -e "\n💡 6. 推奨アクション"
if [ -z "$SLACK_PID" ]; then
    echo "❌ SlackWorkerが停止しています"
    echo "   → 自動復旧: watchdogが30秒以内に再起動予定"
    echo "   → 手動復旧: cd /home/aicompany/ai_co && python3 workers/slack_polling_worker.py"
elif [ -n "$SLACK_PID" ]; then
    LAST_LOG_TIME=$(stat -c %Y "/home/aicompany/ai_co/logs/slack_polling_worker.log" 2>/dev/null || echo 0)
    CURRENT_TIME=$(date +%s)
    TIME_DIFF=$((CURRENT_TIME - LAST_LOG_TIME))
    
    if [ $TIME_DIFF -gt 300 ]; then
        echo "⚠️ ログ更新が5分以上停止しています"
        echo "   → 可能性: ワーカーが応答なし状態"
        echo "   → 対処法: kill -TERM $SLACK_PID (watchdogが自動再起動)"
    else
        echo "✅ 正常稼働中と思われます"
    fi
fi

echo -e "\n============================================="
echo "診断完了 - $(date)"