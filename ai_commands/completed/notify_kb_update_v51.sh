#!/bin/bash
# ナレッジベース更新通知を実行

cd /home/aicompany/ai_co
source venv/bin/activate

echo "📚 ナレッジベース更新通知 v5.1"
echo "=============================="
echo ""

# 通知スクリプト実行
python3 notify_kb_update.py

echo ""
echo "✅ 通知完了！"
echo ""
echo "📋 更新内容:"
echo "  - Command Executorのデフォルト起動"
echo "  - SE-Testerワーカーの統合"
echo "  - ai-start/ai-stopの改善"
echo ""
echo "🔍 詳細確認:"
echo "  ls -la knowledge_base/"
