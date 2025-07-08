#!/bin/bash
# Result Worker 安全起動スクリプト

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🛡️ Result Worker Safe Start"
echo "==========================="

# 1. クリーンアップ
echo "1️⃣ Cleanup..."
tmux kill-session -t result_worker 2>/dev/null || true
pkill -f "result_worker" 2>/dev/null || true
sleep 1

# 2. RabbitMQ確認
echo -e "\n2️⃣ RabbitMQ check..."
if ! systemctl is-active --quiet rabbitmq-server; then
    echo "Starting RabbitMQ..."
    sudo systemctl start rabbitmq-server
    sleep 2
fi

# キュー作成
python3 << EOF
import pika
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='ai_results', durable=True)
    channel.queue_declare(queue='result_queue', durable=True)
    print("✅ Queues ready")
    connection.close()
except Exception as e:
    print(f"⚠️ Queue setup: {e}")
EOF

# 3. 簡易版で起動
echo -e "\n3️⃣ Starting simplified version..."
nohup python3 workers/result_worker_simple.py > logs/result_worker_startup.log 2>&1 &
WORKER_PID=$!
echo "Started with PID: $WORKER_PID"

# 4. 起動確認（5秒待機）
echo -e "\n4️⃣ Waiting for startup..."
for i in {1..5}; do
    echo -n "."
    sleep 1
done
echo

# 5. 状態確認
if kill -0 $WORKER_PID 2>/dev/null; then
    echo "✅ Result Worker is running (PID: $WORKER_PID)"
    echo ""
    echo "Startup log:"
    tail -n 20 logs/result_worker_startup.log
    echo ""
    echo "Recent worker log:"
    tail -n 10 logs/result_worker.log
else
    echo "❌ Worker stopped unexpectedly"
    echo "Check logs:"
    echo "- logs/result_worker_startup.log"
    echo "- logs/result_worker.log"
fi

echo -e "\n==========================="
echo "Monitor with:"
echo "- tail -f logs/result_worker.log"
echo "- ps aux | grep result_worker"
