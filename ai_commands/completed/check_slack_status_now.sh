#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "1. 現在のSlack Polling Worker状態"
echo "===================================="

# プロセス確認
SLACK_PROCESS=$(ps aux | grep -E "slack_polling_worker\.py" | grep -v grep)
if [ -z "$SLACK_PROCESS" ]; then
    echo "❌ Slack Polling Workerが動作していません"
else
    echo "✅ Slack Polling Workerが動作中:"
    echo "$SLACK_PROCESS"
fi

# tmuxセッション確認
echo ""
echo "tmuxセッション:"
tmux ls 2>/dev/null | grep slack || echo "Slack関連のtmuxセッションなし"

# 最新ログ確認
echo ""
echo "最新ログ（存在する場合）:"
if [ -f "logs/slack_polling_worker.log" ]; then
    tail -5 logs/slack_polling_worker.log
else
    echo "ログファイルなし"
fi
