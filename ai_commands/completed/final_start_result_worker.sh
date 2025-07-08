#!/bin/bash
# Result Worker 最終起動スクリプト

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🔄 Result Worker Final Start"
echo "============================"

# 1. プロセス停止
echo -e "\n1️⃣ Cleaning up..."
pkill -f "result_worker" || true
sleep 1

# 2. どちらのバージョンを使うか選択
echo -e "\n2️⃣ Selecting version..."

# フル機能版のテスト
if python3 -c "from core import BaseWorker; print('Core OK')" 2>/dev/null; then
    echo "✅ Using full version (with Core support)"
    WORKER_FILE="workers/result_worker.py"
else
    echo "⚠️ Using simplified version (Core not available)"
    WORKER_FILE="workers/result_worker_simple.py"
fi

# 3. 起動
echo -e "\n3️⃣ Starting $WORKER_FILE..."
tmux new-session -d -s result_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 $WORKER_FILE"

sleep 3

# 4. 確認
echo -e "\n4️⃣ Status check..."
if pgrep -f "result_worker" > /dev/null; then
    echo "✅ Result Worker is running!"
    echo "PID: $(pgrep -f result_worker)"
    echo ""
    echo "Recent logs:"
    tail -n 15 logs/result_worker.log
else
    echo "❌ Failed to start"
    echo "Debug with: python3 $WORKER_FILE"
fi

echo -e "\n============================"
echo "Commands:"
echo "- Monitor: tmux attach -t result_worker"
echo "- Logs: tail -f logs/result_worker.log"
echo "- Test: bash ai_commands/pending/test_all_result_worker.sh"
