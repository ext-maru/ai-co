#!/bin/bash
# Result Worker 診断と修正

cd /home/aicompany/ai_co

echo "🔍 Result Worker Diagnostic & Fix"
echo "================================="

# 1. tmuxセッション確認
echo -e "\n1️⃣ Checking tmux sessions..."
tmux ls 2>/dev/null || echo "No tmux sessions found"

# 既存セッションを削除
tmux kill-session -t result_worker 2>/dev/null
tmux kill-session -t result_worker_simple 2>/dev/null

# 2. プロセス確認と削除
echo -e "\n2️⃣ Checking processes..."
ps aux | grep -E "result_worker|python" | grep -v grep || echo "No processes found"
pkill -f "result_worker" 2>/dev/null || true

# 3. Python環境確認
echo -e "\n3️⃣ Testing Python environment..."
source venv/bin/activate
python3 --version

# 4. インポートテスト
echo -e "\n4️⃣ Testing imports..."
python3 << EOF
import sys
sys.path.insert(0, '/home/aicompany/ai_co')

try:
    import pika
    print("✅ pika: OK")
except Exception as e:
    print(f"❌ pika: {e}")

try:
    from workers.result_worker_simple import ResultWorker
    print("✅ result_worker_simple: OK")
except Exception as e:
    print(f"❌ result_worker_simple: {e}")
EOF

# 5. RabbitMQ確認
echo -e "\n5️⃣ Checking RabbitMQ..."
if systemctl is-active --quiet rabbitmq-server; then
    echo "✅ RabbitMQ is running"
    sudo rabbitmqctl list_queues | grep -E "ai_results|result_queue" || echo "Queues not found"
else
    echo "❌ RabbitMQ is not running"
    echo "Starting RabbitMQ..."
    sudo systemctl start rabbitmq-server
fi

# 6. 簡易版で直接起動テスト
echo -e "\n6️⃣ Direct start test..."
timeout 5 python3 workers/result_worker_simple.py 2>&1 | head -20 || true

echo -e "\n================================="
echo "Diagnostic complete"
