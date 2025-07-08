#!/bin/bash
# Slack PM-AI完全状態確認
cd /home/aicompany/ai_co

echo "📊 Slack PM-AI完全状態確認"
echo "=========================="
echo "日時: $(date)"
echo ""

echo "1. プロセス状態"
echo "---------------"
echo -n "Task Worker: "
ps aux | grep task_worker.py | grep -v grep > /dev/null && echo "✅ 稼働中" || echo "❌ 停止"

echo -n "PM Worker: "
ps aux | grep pm_worker.py | grep -v grep > /dev/null && echo "✅ 稼働中" || echo "❌ 停止"

echo -n "Result Worker: "
ps aux | grep result_worker.py | grep -v grep > /dev/null && echo "✅ 稼働中" || echo "❌ 停止"

echo -n "Slack Polling Worker: "
ps aux | grep slack_polling_worker.py | grep -v grep > /dev/null && echo "✅ 稼働中" || echo "❌ 停止"

echo ""
echo "2. TMUXセッション"
echo "-----------------"
tmux list-windows -t ai_company 2>/dev/null || echo "セッションなし"

echo ""
echo "3. キュー状態"
echo "-------------"
sudo rabbitmqctl list_queues name messages 2>/dev/null | grep -E "(ai_tasks|pm_task|result)" || echo "確認失敗"

echo ""
echo "4. 最新ログ (slack_polling_worker.log)"
echo "--------------------------------------"
if [ -f logs/slack_polling_worker.log ]; then
    tail -15 logs/slack_polling_worker.log
else
    echo "ログファイルなし"
fi

echo ""
echo "5. 最新ログ (task_worker.log)"
echo "-----------------------------"
if [ -f logs/task_worker.log ]; then
    tail -10 logs/task_worker.log | grep -E "(Slack|slack|処理)"
else
    echo "ログファイルなし"
fi

echo ""
echo "6. Slack設定"
echo "------------"
grep -E "(SLACK_BOT_TOKEN|SLACK_POLLING_ENABLED|SLACK_POLLING_CHANNEL)" config/slack.conf | grep -v "^#" | head -5

echo ""
echo "✅ 状態確認完了"
