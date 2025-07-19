#!/bin/bash
# 即座に基本的な状態を確認
cd /home/aicompany/ai_co

echo "=== 診断結果（シンプル版）==="
echo ""

# 1. Workerの状態
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "✅ Slack Polling Worker: 動作中"
    PID=$(pgrep -f "slack_polling_worker")
    echo "   PID: $PID"

    # ログの最終更新
    if [ -f logs/slack_polling_worker.log ]; then
        LAST_MOD=$(stat -c %y logs/slack_polling_worker.log | cut -d'.' -f1)
        echo "   最終ログ更新: $LAST_MOD"

        # 最新のログ内容
        echo ""
        echo "最新ログ（5行）:"
        tail -5 logs/slack_polling_worker.log
    fi
else
    echo "❌ Slack Polling Worker: 停止中"
    echo ""
    echo "起動が必要です:"
    echo "tmux new -s slack_polling -d 'cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py'"
fi

echo ""
echo "【診断結果】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "基本的にはWorkerは動作しています。"
    echo "Slackで新しいメッセージを送ってテストしてください。"
else
    echo "Workerが停止しているため、Slackメッセージを処理できません。"
    echo "上記のコマンドで起動してください。"
fi
