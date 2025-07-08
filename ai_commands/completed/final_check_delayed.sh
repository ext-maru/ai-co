#!/bin/bash
# 診断結果待機と最終確認（15秒後）

cd /home/aicompany/ai_co

echo "⏳ 診断実行待機中..."
sleep 15

echo ""
echo "📊 診断結果最終確認"
echo "=================="
echo ""

# 重要な診断結果を抽出
echo "1. 致命的な問題:"
echo "---------------"
find ai_commands/logs -name "*check_results*.log" -mmin -5 -exec grep -A 5 "CRITICAL" {} \; | head -10 || echo "致命的問題なし"

echo ""
echo "2. Botチャンネルメンバーシップ:"
echo "-----------------------------"
find ai_commands/logs -name "*direct_log*.log" -mmin -5 -exec grep "Botはチャンネルメンバー" {} \; | tail -1

echo ""
echo "3. メッセージ検出状況:"
echo "--------------------"
find ai_commands/logs -name "*find_messages_detail*.log" -mmin -5 -exec grep -E "検出メッセージ数:|メンション統計:" {} \; | tail -2

echo ""
echo "4. Slack通知テスト結果:"
echo "---------------------"
find ai_commands/logs -name "*comprehensive_slack_fix*.log" -mmin -5 -exec grep -A 3 "Slack通知テスト" {} \; | tail -5

echo ""
echo "5. 修正実行状況:"
echo "--------------"
ls -lt ai_commands/logs/*comprehensive_slack_fix*.log 2>/dev/null | head -1 || echo "修正コマンド未実行"

echo ""
echo "✅ 最終確認完了"
echo ""
echo "【次のアクション】"
echo "1. Botがチャンネルメンバーでない場合:"
echo "   → Slackで /invite @pm-ai を実行"
echo ""
echo "2. メッセージが検出されていない場合:"
echo "   → 正しいチャンネルで @pm-ai test を送信"
echo ""
echo "3. 全て正常な場合:"
echo "   → tmux attach -t ai_company でワーカー確認"
