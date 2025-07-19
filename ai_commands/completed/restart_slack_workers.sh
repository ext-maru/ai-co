#!/bin/bash
#!/bin/bash
# Slack通知改善のためのワーカー再起動

cd /home/aicompany/ai_co

# ログ記録
echo "[$(date)] Slack通知改善のためワーカー再起動開始" >> logs/command_executor.log

# 既存ワーカーを安全に停止
echo "Stopping workers..."
pkill -f task_worker.py || true
pkill -f result_worker.py || true
sleep 2

# ワーカー再起動（tmux使用）
echo "Restarting workers in tmux..."
tmux kill-session -t task_worker 2>/dev/null || true
tmux kill-session -t result_worker 2>/dev/null || true

sleep 1

# TaskWorker起動
tmux new-session -d -s task_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/task_worker.py"

# ResultWorker起動
tmux new-session -d -s result_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/result_worker.py"

echo "Workers restarted successfully!"

# 動作確認
sleep 3
echo "\nWorker status:"
tmux ls | grep -E "(task_worker|result_worker)" || echo "No workers found in tmux"

echo "\nProcess check:"
ps aux | grep -E "(task_worker|result_worker)" | grep -v grep || echo "No worker processes found"

echo "\n[$(date)] Slack通知改善のためのワーカー再起動完了" >> logs/command_executor.log
