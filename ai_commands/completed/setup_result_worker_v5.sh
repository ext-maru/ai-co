#!/bin/bash
# Result Worker v5.0 完全セットアップ

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🚀 AI Company Result Worker v5.0 Setup"
echo "====================================="

# 1. 実行権限設定
echo -e "\n1️⃣ Setting permissions..."
chmod +x scripts/preview_slack_notifications.py
chmod +x scripts/create_result_worker_tests.py
chmod +x scripts/restart_result_worker.sh
chmod +x scripts/setup_result_worker_v5.py

# 2. テストコマンド生成
echo -e "\n2️⃣ Generating test commands..."
python3 scripts/create_result_worker_tests.py

# 3. Result Worker再起動
echo -e "\n3️⃣ Restarting Result Worker..."
pkill -f "result_worker.py" || true
sleep 1
tmux new-session -d -s result_worker "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/result_worker.py"

# 4. 動作確認
echo -e "\n4️⃣ Verification..."
sleep 2
if pgrep -f "result_worker.py" > /dev/null; then
    echo "✅ Result Worker v5.0 is running!"
    echo "PID: $(pgrep -f result_worker.py)"
else
    echo "❌ Failed to start"
fi

echo -e "\n✅ Setup complete!"
echo "Monitor: tmux attach -t result_worker"
