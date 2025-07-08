#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

# 現在のResultWorkerを停止
echo "📌 現在のResultWorkerを停止..."
pkill -f result_worker.py
sleep 2

# ResultWorkerを起動（tmux使用）
echo "📌 ResultWorkerを起動..."
tmux new-session -d -s result_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/result_worker.py"

sleep 3

# 確認
echo "📌 プロセス確認:"
ps aux | grep result_worker | grep -v grep

# ログ確認
echo "\n📌 最新ログ:"
tail -n 10 logs/result_worker.log

echo "\n✅ ResultWorker再起動完了"