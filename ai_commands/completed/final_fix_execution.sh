#!/bin/bash
# 最終的な修正実行スクリプト

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🚀 AI Start/Stop修正プロセス開始"
echo "================================"
echo ""

# 1. execute_fix_via_helper.pyを実行
echo "📝 ステップ1: AI Command Helper経由で修正実行"
python3 execute_fix_via_helper.py

echo ""
echo "✅ 全プロセス完了！"
echo ""
echo "📋 次のステップ:"
echo "  1. しばらく待ってから結果を確認"
echo "  2. ai-status で現在の状態を確認"
echo "  3. ai-stop --force && ai-start でテスト"
