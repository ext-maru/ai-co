#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo ""
echo "2. Slack Polling Workerの起動"
echo "=============================="

# 既存プロセスを停止
echo "既存プロセスを停止..."
pkill -f "slack_polling_worker\.py" 2>/dev/null
tmux kill-session -t slack_polling 2>/dev/null
sleep 2

# ログディレクトリ作成
mkdir -p logs

# tmuxで起動
echo "新規起動中..."
tmux new-session -d -s slack_polling     "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py 2>&1 | tee -a logs/slack_polling_worker.log"

sleep 3

# 起動確認
if tmux has-session -t slack_polling 2>/dev/null; then
    echo "✅ tmuxセッション作成成功"

    # プロセス確認
    POLLING_PID=$(pgrep -f "slack_polling_worker\.py")
    if [ -n "$POLLING_PID" ]; then
        echo "✅ プロセス起動確認 (PID: $POLLING_PID)"
    else
        echo "⚠️  プロセスが見つかりません"
    fi
else
    echo "❌ tmuxセッション作成失敗"
fi

# ログ確認
echo ""
echo "起動ログ（最新10行）:"
sleep 2
tail -10 logs/slack_polling_worker.log 2>/dev/null || echo "ログファイルが生成されていません"
