#!/bin/bash

SESSION="ai_company"
PROJECT_DIR="$HOME/ai_co"

# セッションリセット
tmux kill-session -t $SESSION 2>/dev/null

echo "🏢 AI Company を起動中..."

# セッション作成
tmux new-session -d -s $SESSION -n "dashboard"

# 1. ダッシュボード
tmux send-keys -t $SESSION:dashboard "cd $PROJECT_DIR && clear" C-m
tmux send-keys -t $SESSION:dashboard "watch -n 2 '$PROJECT_DIR/scripts/status.sh'" C-m

# 2. タスクワーカー1
tmux new-window -t $SESSION -n "worker-1"
tmux send-keys -t $SESSION:worker-1 "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:worker-1 "python3 workers/task_worker.py worker-1" C-m

# 3. タスクワーカー2
tmux new-window -t $SESSION -n "worker-2"
tmux send-keys -t $SESSION:worker-2 "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:worker-2 "python3 workers/task_worker.py worker-2" C-m

# 4. 結果ワーカー
tmux new-window -t $SESSION -n "result-worker"
tmux send-keys -t $SESSION:result-worker "cd $PROJECT_DIR && source venv/bin/activate" C-m
tmux send-keys -t $SESSION:result-worker "python3 workers/result_worker.py" C-m

# 5. ログモニター
tmux new-window -t $SESSION -n "logs"
tmux send-keys -t $SESSION:logs "cd $PROJECT_DIR/logs" C-m
tmux send-keys -t $SESSION:logs "tail -f *.log" C-m

echo "✅ AI Company 起動完了！"
echo "接続: tmux attach -t $SESSION"
