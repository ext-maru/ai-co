#!/bin/bash
"""
🎯 Practical PR Automation Setup
実用的なPR自動化設定スクリプト
"""

echo "🎯 実用的なPR自動化設定"
echo "分析結果: 週間71コミットの高活動リポジトリ"
echo ""

echo "📋 推奨設定オプション:"
echo ""

echo "1. 🛡️ 安全重視 (深夜2:00 日次)"
echo "   Cron: 0 2 * * *"
echo "   リスク: 最低"
echo "   処理数: 1-2 Issue/日"
echo ""

echo "2. ⚡ バランス重視 (6時間毎)"
echo "   Cron: 0 */6 * * *"
echo "   リスク: 中"
echo "   処理数: 4 Issue/日"
echo ""

echo "3. 🚀 積極処理 (2時間毎、営業時間外)"
echo "   Cron: 0 */2 * * * (22:00-6:00のみ)"
echo "   リスク: 中高"
echo "   処理数: 8-12 Issue/日"
echo ""

echo "🤔 どの設定を選択しますか？"
echo "1) 安全重視"
echo "2) バランス重視 (推奨)"
echo "3) 積極処理"
echo ""

read -p "選択 (1-3): " choice

case $choice in
  1)
    CRON_SETTING="0 2 * * *"
    DESCRIPTION="安全重視 - 深夜2:00日次処理"
    ;;
  2)
    CRON_SETTING="0 */6 * * *"
    DESCRIPTION="バランス重視 - 6時間毎処理"
    ;;
  3)
    CRON_SETTING="0 22,0,2,4 * * *"
    DESCRIPTION="積極処理 - 営業時間外2時間毎"
    ;;
  *)
    echo "デフォルト: バランス重視を選択"
    CRON_SETTING="0 */6 * * *"
    DESCRIPTION="バランス重視 - 6時間毎処理"
    ;;
esac

echo ""
echo "✅ 選択された設定:"
echo "Cron: $CRON_SETTING"
echo "説明: $DESCRIPTION"
echo ""

echo "🔧 Cron設定手順:"
echo "1. crontab -e"
echo "2. 以下の行を追加:"
echo ""
echo "$CRON_SETTING /home/aicompany/ai_co/scripts/enhanced_auto_pr_cron.sh"
echo ""

echo "📊 予想効果:"
case $choice in
  1)
    echo "- 1-2 Issue/日の安定処理"
    echo "- コンフリクトリスク: 5%未満"
    ;;
  2)
    echo "- 4 Issue/日の効率的処理"
    echo "- コンフリクトリスク: 10-15%"
    ;;
  3)
    echo "- 8-12 Issue/日の高速処理"
    echo "- コンフリクトリスク: 20-25%"
    ;;
esac

echo ""
echo "💡 Tips:"
echo "- 処理ログ: /home/aicompany/ai_co/logs/enhanced_auto_pr/"
echo "- 停止方法: crontab -e で該当行削除"
echo "- 監視方法: tail -f logs/enhanced_auto_pr/*.log"
echo ""

echo "🎉 PR自動化設定完了準備OK!"
