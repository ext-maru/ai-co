#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# 既存プロセスチェック
if pgrep -f "error_intelligence_worker.py" > /dev/null; then
    echo "⚠️ Error Intelligence Worker is already running"
else
    # tmuxセッション作成
    tmux new-session -d -s error_intelligence
    tmux send-keys -t error_intelligence "cd /home/aicompany/ai_co" C-m
    tmux send-keys -t error_intelligence "source venv/bin/activate" C-m
    tmux send-keys -t error_intelligence "python3 workers/error_intelligence_worker.py" C-m
    echo "✅ Error Intelligence Worker started in tmux session"
    echo "To view: tmux attach -t error_intelligence"
fi
