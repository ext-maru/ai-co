#!/bin/bash
# 診断ログの直接確認

cd /home/aicompany/ai_co

echo "📋 診断ログ直接確認"
echo "=================="
echo ""

# 最新の重要ログを直接表示
echo "1. Botチャンネルメンバー確認:"
echo "------------------------------"
find ai_commands/logs -name "*check_channel_bot*.log" -mmin -30 -exec grep -h "Botはチャンネルメンバー" {} \; | tail -1 || echo "情報なし"

echo ""
echo "2. メッセージ・メンション数:"
echo "---------------------------"
find ai_commands/logs -name "*find_user_messages*.log" -mmin -30 -exec grep -h "件のメッセージ取得\|PM-AIへのメンション:" {} \; | tail -2 || echo "情報なし"

echo ""
echo "3. Bot ID情報:"
echo "-------------"
find ai_commands/logs -name "*check_channel_bot*.log" -mmin -30 -exec grep -h "Bot ID:\|Bot名:" {} \; | tail -2 || echo "情報なし"

echo ""
echo "4. Slack Polling Worker状態:"
echo "---------------------------"
ps aux | grep slack_polling_worker.py | grep -v grep && echo "✅ 稼働中" || echo "❌ 停止"

echo ""
echo "5. エラー情報（最新5件）:"
echo "------------------------"
grep -i "error\|failed" logs/slack_polling_worker.log | tail -5 || echo "エラーなし"

echo ""
echo "6. 最新のメッセージサンプル:"
echo "--------------------------"
find ai_commands/logs -name "*find_user_messages*.log" -mmin -30 -exec grep -B1 -A1 "Text:" {} \; | tail -10 || echo "メッセージなし"

echo ""
echo "7. Slack設定状態:"
echo "----------------"
grep -E "(SLACK_BOT_TOKEN|SLACK_WEBHOOK_URL|ENABLE_SLACK)" config/slack.conf | grep -v "^#" | head -5

echo ""
echo "8. 最新のタスク処理:"
echo "------------------"
grep "slack" logs/task_worker.log | tail -5 || echo "Slack関連タスクなし"

echo ""
echo "✅ 直接確認完了"
