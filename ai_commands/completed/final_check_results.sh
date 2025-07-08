#!/bin/bash
# 診断結果の最終確認

cd /home/aicompany/ai_co

echo "=== Slack PM-AI 診断結果 ==="
echo "時刻: $(date)"
echo ""

# 1. Worker状態
echo "【Slack Polling Worker】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    PID=$(pgrep -f "slack_polling_worker")
    echo "✅ 動作中 (PID: $PID)"
    
    # ログ確認
    if [ -f logs/slack_polling_worker.log ]; then
        echo ""
        echo "最新ログ（10行）:"
        tail -10 logs/slack_polling_worker.log
        
        # エラー確認
        ERROR_COUNT=$(tail -50 logs/slack_polling_worker.log | grep -ci error || echo "0")
        echo ""
        echo "エラー数（最新50行）: $ERROR_COUNT"
    fi
else
    echo "❌ 停止中"
    echo ""
    echo "起動方法:"
    echo "tmux new -s slack_polling -d 'cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py'"
fi

echo ""
echo "【診断ログ確認】"
# 最新の診断ログ
LATEST_LOG=$(ls -t ai_commands/logs/*slack*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "最新の診断ログ: $(basename $LATEST_LOG)"
    grep -E "(✅|❌|結論|診断)" "$LATEST_LOG" | tail -10
fi

echo ""
echo "【結論】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "Slack Polling Workerは動作しています。"
    echo "新しいメッセージでテスト: @pm-ai hello test"
else
    echo "Workerが停止しています。上記コマンドで起動してください。"
fi