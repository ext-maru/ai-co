#!/bin/bash
# Slack最新メッセージ直接処理
cd /home/aicompany/ai_co
source venv/bin/activate

echo "🔧 Slack最新メッセージ直接処理開始"
echo "===================================="

# 先にワーカー確認
echo "ワーカー状態確認..."
ps aux | grep -E "(task_worker|pm_worker)" | grep -v grep || echo "基本ワーカーが起動していません"

# メッセージ処理
python3 process_slack_direct.py

echo ""
echo "キュー状態:"
sudo rabbitmqctl list_queues name messages | grep -E "(ai_tasks|result)" || echo "キュー確認失敗"

echo ""
echo "✅ 処理完了"
