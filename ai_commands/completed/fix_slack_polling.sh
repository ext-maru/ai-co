#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== 問題の自動修正 ==="
echo ""

# Polling Workerが動作していない場合は起動
if ! pgrep -f "slack_polling_worker" > /dev/null; then
    echo "Slack Polling Workerを起動します..."

    # 既存のセッションをクリーンアップ
    tmux kill-session -t slack_polling 2>/dev/null

    # 新規起動
    tmux new-session -d -s slack_polling         "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py 2>&1 | tee -a logs/slack_polling_worker.log"

    sleep 3

    if tmux has-session -t slack_polling 2>/dev/null; then
        echo "✅ Slack Polling Worker起動成功"

        # 最初のログ確認
        sleep 2
        echo ""
        echo "起動ログ:"
        tail -10 logs/slack_polling_worker.log
    else
        echo "❌ 起動失敗"
    fi
else
    echo "✅ Slack Polling Workerは既に動作中"

    # ログの最新部分を確認
    echo ""
    echo "最新のログ（問題の手がかり）:"
    tail -20 logs/slack_polling_worker.log | grep -E "Error|error|Exception|Failed|❌|✅"
fi

echo ""
echo "次のテスト:"
echo "1. Slackで新しいメッセージを送信: @pm-ai テスト$(date +%H%M%S)"
echo "2. 20秒待つ"
echo "3. tail -f logs/slack_polling_worker.log でログ確認"
