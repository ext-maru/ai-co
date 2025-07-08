#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# 既存プロセスを停止
if pgrep -f "error_intelligence_worker.py" > /dev/null; then
    echo "既存のワーカーを停止..."
    pkill -f "error_intelligence_worker.py"
    sleep 2
fi

# tmuxセッションで再起動
tmux kill-session -t error_intelligence 2>/dev/null || true
tmux new-session -d -s error_intelligence
tmux send-keys -t error_intelligence "cd /home/aicompany/ai_co" C-m
tmux send-keys -t error_intelligence "source venv/bin/activate" C-m
tmux send-keys -t error_intelligence "python3 workers/error_intelligence_worker.py" C-m

echo "✅ Error Intelligence Worker (Phase 2対応) 起動完了"
echo "To view: tmux attach -t error_intelligence"
