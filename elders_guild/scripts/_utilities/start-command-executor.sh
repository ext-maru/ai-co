#!/bin/bash
# AI Command Executor 起動スクリプト

set -e

echo "🚀 Starting AI Command Executor Worker..."

cd /home/aicompany/ai_co
source venv/bin/activate

# ログディレクトリ確認
mkdir -p logs

# バックグラウンドで起動
python3 workers/command_executor_worker.py > logs/command_executor.log 2>&1 &
PID=$!

echo "✓ Command Executor Worker started (PID: $PID)"
echo "📁 Commands directory: /home/aicompany/ai_co/ai_commands/"
echo "📝 Logs directory: /home/aicompany/ai_co/ai_commands/logs/"

# PIDファイルに保存
echo $PID > /tmp/ai_command_executor.pid

echo ""
echo "To stop: kill $(cat /tmp/ai_command_executor.pid)"
echo "To check logs: tail -f logs/command_executor.log"
