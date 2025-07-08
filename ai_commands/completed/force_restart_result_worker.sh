#!/bin/bash
# ResultWorker強制再起動（日本語パッチ適用済み）

echo "🔄 ResultWorker強制再起動..."

# 1. 現在のプロセスを強制終了
pkill -9 -f result_worker.py
sleep 2

# 2. 起動
cd /home/aicompany/ai_co
source venv/bin/activate
nohup python3 workers/result_worker.py > logs/result_worker_force.log 2>&1 &

sleep 2

# 3. 確認
ps aux | grep result_worker.py | grep -v grep && echo "✅ ResultWorker起動成功" || echo "❌ 起動失敗"

echo ""
echo "📝 ログ確認: tail -f logs/result_worker_force.log"
