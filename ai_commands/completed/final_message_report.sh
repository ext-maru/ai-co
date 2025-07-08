#!/bin/bash
# 診断完了待機と最終レポート（30秒後）
cd /home/aicompany/ai_co

echo "⏳ 診断完了待機中..."
sleep 30

echo ""
echo "📊 Slackメッセージ診断最終レポート"
echo "==================================="
echo "実行時刻: $(date)"
echo ""

# 最新の診断ログから重要な情報を抽出
echo "1. メッセージ検出結果:"
echo "-----------------------"
find ai_commands/logs -name "*find_user_messages*.log" -mmin -5 -exec grep -h "PM-AIへのメンション:" {} \; | tail -1
find ai_commands/logs -name "*find_user_messages*.log" -mmin -5 -exec grep -h "件のメッセージ取得" {} \; | tail -1

echo ""
echo "2. Bot設定:"
echo "-----------"
find ai_commands/logs -name "*check_channel_bot*.log" -mmin -5 -exec grep -h "Bot ID:" {} \; | tail -1
find ai_commands/logs -name "*check_channel_bot*.log" -mmin -5 -exec grep -h "Botはチャンネルメンバー" {} \; | tail -1

echo ""
echo "3. ユーザー情報:"
echo "---------------"
find ai_commands/logs -name "*find_specific_user*.log" -mmin -5 -exec grep -h "アクティブユーザー数:" {} \; | tail -1

echo ""
echo "✅ 診断完了"
echo ""
echo "詳細なログ確認:"
echo "tail -f /home/aicompany/ai_co/ai_commands/logs/*.log"
