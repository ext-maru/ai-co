#!/bin/bash

SESSION="ai_company"
PROJECT_DIR="$HOME/ai_co"

tmux kill-session -t $SESSION 2>/dev/null

echo "🏢 AI Company を起動中..."

tmux new-session -d -s $SESSION -n "dashboard"
tmux send-keys -t $SESSION:dashboard "cd $PROJECT_DIR && clear" C-m
tmux send-keys -t $SESSION:dashboard "watch -n 2 '$PROJECT_DIR/scripts/status.sh'" C-m

# PMワーカー起動（追加）
tmux new-window -t $SESSION -n "pm-worker"
tmux send-keys -t $SESSION:pm-worker "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:pm-worker "python3 workers/pm_worker.py" C-m

# 既存ワーカー起動
tmux new-window -t $SESSION -n "worker-1"
tmux send-keys -t $SESSION:worker-1 "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:worker-1 "python3 workers/task_worker.py worker-1" C-m

tmux new-window -t $SESSION -n "worker-2"
tmux send-keys -t $SESSION:worker-2 "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:worker-2 "python3 workers/task_worker.py worker-2" C-m

tmux new-window -t $SESSION -n "result-worker"
tmux send-keys -t $SESSION:result-worker "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:result-worker "python3 workers/result_worker.py" C-m

tmux new-window -t $SESSION -n "logs"
tmux send-keys -t $SESSION:logs "cd $PROJECT_DIR/logs" C-m
tmux send-keys -t $SESSION:logs "tail -f *.log" C-m

echo "✅ AI Company 起動完了！"
echo "接続: tmux attach -t $SESSION"

