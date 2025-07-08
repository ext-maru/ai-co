#!/bin/bash
# Result Worker 緊急起動スクリプト

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🚨 Result Worker Emergency Start"
echo "================================"

# 1. 既存プロセス停止
echo -e "\n1️⃣ Stopping existing processes..."
pkill -f "result_worker" || true

# 2. RabbitMQ確認
echo -e "\n2️⃣ Checking RabbitMQ..."
if ! sudo systemctl is-active --quiet rabbitmq-server; then
    echo "Starting RabbitMQ..."
    sudo systemctl start rabbitmq-server
fi
echo "✅ RabbitMQ is active"

# 3. 簡易版で起動
echo -e "\n3️⃣ Starting simplified Result Worker..."
tmux new-session -d -s result_worker_simple "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/result_worker_simple.py"

sleep 2

# 4. 確認
echo -e "\n4️⃣ Verification..."
if pgrep -f "result_worker_simple" > /dev/null; then
    echo "✅ Result Worker (simplified) is running!"
    echo "PID: $(pgrep -f result_worker_simple)"
    
    # ログ確認
    echo -e "\nRecent logs:"
    tail -n 10 logs/result_worker.log
else
    echo "❌ Still failed to start"
    echo "Manual debug: python3 workers/result_worker_simple.py"
fi

echo -e "\n================================"
echo "Monitor: tmux attach -t result_worker_simple"
