#!/bin/bash
# ナレッジベース更新の最終確認

cd /home/aicompany/ai_co
source venv/bin/activate

echo "🔍 ナレッジベース更新の最終確認"
echo "================================"
echo ""

# 確認スクリプト実行
python3 check_kb_update.py

echo ""
echo "📌 次のステップ:"
echo "  1. ai-stop --force && ai-start でシステム再起動"
echo "  2. ai-status で新機能の動作確認"
echo "  3. ai-start --se-tester でテスト自動化を試す"
echo ""
echo "🎉 AI Company v5.1へのアップグレード完了！"
