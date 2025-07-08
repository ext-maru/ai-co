#!/bin/bash
# 即時状態確認

cd /home/aicompany/ai_co

echo "🔍 Slack PM-AI即時状態確認"
echo "=========================="
echo "時刻: $(date)"
echo ""

# 1. プロセス確認
echo "1. Slack Polling Workerプロセス:"
ps aux | grep slack_polling_worker.py | grep -v grep || echo "❌ プロセスなし"

# 2. 最新ログ確認（エラーのみ）
echo ""
echo "2. 最新エラー (slack_polling_worker.log):"
grep -i "error" logs/slack_polling_worker.log | tail -5 || echo "エラーなし"

# 3. Slack設定確認
echo ""
echo "3. Slack設定:"
grep "SLACK_BOT_TOKEN" config/slack.conf | head -1
grep "SLACK_POLLING_CHANNEL_ID" config/slack.conf | head -1
grep "SLACK_POLLING_ENABLED" config/slack.conf | head -1

# 4. キュー確認
echo ""
echo "4. ai_tasksキュー:"
sudo rabbitmqctl list_queues name messages | grep ai_tasks || echo "確認失敗"

# 5. 最新のメンション処理ログ
echo ""
echo "5. 最新メンション処理:"
grep -E "(メンション|mention|<@U)" logs/slack_polling_worker.log | tail -3 || echo "メンションログなし"

echo ""
echo "✅ 即時確認完了"
