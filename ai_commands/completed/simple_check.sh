#!/bin/bash
cd /home/aicompany/ai_co

echo "=== Slack PM-AI 現状確認（シンプル版）==="
echo ""

# 1. Workerプロセス
echo "【Workerプロセス】"
WORKER_RUNNING=false
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "✅ Slack Polling Worker動作中"
    WORKER_RUNNING=true
else
    echo "❌ Slack Polling Worker停止中"
fi

# 2. 最新ログ
echo ""
echo "【最新ログ（5行）】"
if [ -f logs/slack_polling_worker.log ]; then
    tail -5 logs/slack_polling_worker.log
else
    echo "ログファイルなし"
fi

# 3. 診断結果
echo ""
echo "【診断】"
if [ "$WORKER_RUNNING" = true ]; then
    echo "✅ 基本的には動作しています"
    echo "   新しいメッセージでテスト: @pm-ai test message"
else
    echo "❌ Workerを起動する必要があります"
    echo "   起動コマンド: tmux new -s slack_polling 'cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py'"
fi