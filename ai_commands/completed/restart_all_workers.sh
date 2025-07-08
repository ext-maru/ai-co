#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🔄 全ワーカー再起動"
echo "=================="

# 全プロセス終了
echo "既存プロセス終了中..."
pkill -f "worker.*.py" || true
sleep 3

# TMUXセッション再作成
tmux kill-session -t ai_company 2>/dev/null || true
sleep 1
tmux new-session -d -s ai_company -n main

# 基本ワーカー起動
echo "基本ワーカー起動..."
tmux new-window -t ai_company -n task_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/task_worker.py"
sleep 2

tmux new-window -t ai_company -n pm_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/pm_worker.py"
sleep 2

tmux new-window -t ai_company -n result_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/result_worker.py"
sleep 2

# Slack Polling Worker起動
echo "Slack Polling Worker起動..."
tmux new-window -t ai_company -n slack_polling "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py"
sleep 3

echo "✅ 全ワーカー再起動完了"
tmux list-windows -t ai_company
