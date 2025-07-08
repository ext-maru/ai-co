#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

# 現在のResultWorkerを停止
echo "📌 現在のResultWorkerを停止..."
pkill -f result_worker.py
sleep 2

# 新しいResultWorkerを起動
echo "📌 新しいResultWorkerを起動..."
source venv/bin/activate
nohup python3 workers/result_worker.py > logs/result_worker_restart.log 2>&1 &

sleep 3
ps aux | grep result_worker

echo "✅ ResultWorker再起動完了"
