#!/bin/bash
# 重要情報の即時抽出

cd /home/aicompany/ai_co

echo "🔍 重要情報即時抽出"
echo "==================="
echo ""

# 最新の診断結果から重要情報を抽出
echo "1. Bot情報:"
echo "-----------"
find ai_commands/logs -name "*check_channel_bot*.log" -mmin -10 -exec grep -h "Bot ID:\|Bot名:\|Botはチャンネルメンバー" {} \; | head -5

echo ""
echo "2. メッセージ情報:"
echo "-----------------"
find ai_commands/logs -name "*find_user_messages*.log" -mmin -10 -exec grep -h "件のメッセージ取得\|PM-AIへのメンション:" {} \; | head -5

echo ""
echo "3. エラー情報:"
echo "-------------"
grep -i "error\|failed\|失敗" logs/slack_polling_worker.log | tail -5 || echo "エラーなし"

echo ""
echo "4. Slack Polling Worker最新状態:"
echo "-------------------------------"
tail -10 logs/slack_polling_worker.log | grep -E "(開始|Bot ID|メンション|タスク|ERROR)" || echo "関連ログなし"

echo ""
echo "5. キュー状態:"
echo "-------------"
sudo rabbitmqctl list_queues name messages | grep -E "(ai_tasks|pm_task|result)" || echo "キュー確認失敗"

echo ""
echo "6. プロセス状態:"
echo "---------------"
ps aux | grep slack_polling_worker.py | grep -v grep && echo "✅ Slack Polling Worker稼働中" || echo "❌ Slack Polling Worker停止"

echo ""
echo "✅ 即時確認完了"
