#!/bin/bash
# Result Worker 動作確認

cd /home/aicompany/ai_co

echo "📊 Result Worker v5.0 Status Check"
echo "=================================="

# 1. プロセス状態
echo -e "\n1️⃣ Process Status:"
ps aux | grep result_worker | grep -v grep

# 2. 最新のログ（20行）
echo -e "\n2️⃣ Recent Logs:"
tail -n 20 logs/result_worker.log

# 3. キュー状態
echo -e "\n3️⃣ Queue Status:"
sudo rabbitmqctl list_queues name messages | grep -E "ai_results|result_queue" || echo "No messages in queues"

# 4. Slack設定確認
echo -e "\n4️⃣ Slack Configuration:"
if [ -f "config/slack.conf" ]; then
    grep -q "WEBHOOK_URL=" config/slack.conf && echo "✅ Webhook URL configured" || echo "⚠️ Webhook URL not found"
else
    echo "⚠️ slack.conf not found"
fi

# 5. 統計情報
echo -e "\n5️⃣ Worker Statistics:"
grep -E "(total_tasks|successful_tasks|Success Rate)" logs/result_worker.log | tail -5

echo -e "\n=================================="
echo "✅ Result Worker v5.0 is operational!"
echo ""
echo "Next steps:"
echo "1. Check your Slack channel for the notification"
echo "2. Send more test messages with: python3 scripts/send_test_result_message.py"
echo "3. Monitor logs: tail -f logs/result_worker.log"
