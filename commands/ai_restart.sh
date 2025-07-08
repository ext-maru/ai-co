#!/bin/bash
echo "=================================================="
echo "🚀 AI Company システム再起動 - $(date '+%H:%M:%S')"
echo "=================================================="

# システム停止
echo -e "\n--- システム停止 ---"
echo "ℹ️  現在のシステムを停止しています..."
tmux kill-session -t ai_company 2>/dev/null && echo "✅ tmuxセッション停止完了" || echo "ℹ️  tmuxセッションは既に停止しています"
pkill -f "worker.py" 2>/dev/null
pkill -f "task_worker" 2>/dev/null
pkill -f "pm_worker" 2>/dev/null
pkill -f "result_worker" 2>/dev/null
rm -f /tmp/ai_command_executor.pid 2>/dev/null
echo "✅ プロセス停止完了"

# 3秒待機
echo -e "\nℹ️  3秒待機中..."
sleep 3

# システム起動
echo -e "\n--- システム起動 ---"
echo "ℹ️  システムを起動しています..."
cd /home/aicompany/ai_co
bash scripts/start_company.sh

echo -e "\n--- 再起動完了 ---"
echo "✅ システム再起動が完了しました！"
