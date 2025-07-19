#!/bin/bash
# ナレッジベース一覧表示

cd /home/aicompany/ai_co

echo "📚 AI Company ナレッジベース一覧 (v5.1)"
echo "========================================"
echo ""

# ナレッジベースディレクトリの内容
echo "📁 knowledge_base/"
ls -la knowledge_base/ 2>/dev/null || echo "  (ディレクトリが見つかりません)"

echo ""
echo "📊 統計情報:"
echo "  総ファイル数: $(find knowledge_base -name "*.md" 2>/dev/null | wc -l)"
echo "  総サイズ: $(du -sh knowledge_base 2>/dev/null | cut -f1)"

echo ""
echo "📋 主要ドキュメント:"
echo "  • Core Knowledge v5.1 - システム全体の概要"
echo "  • Command Executor v1.1 - 自動実行システム"
echo "  • New Features Guide v5.1 - 新機能活用ガイド"
echo "  • UPDATE NOTES v5.1 - 更新内容の要約"

echo ""
echo "🔍 内容確認方法:"
echo "  cat knowledge_base/AI_Company_Core_Knowledge_v5.1.md"
echo "  less knowledge_base/UPDATE_NOTES_v5.1.md"

echo ""
echo "✨ v5.1の特徴:"
echo "  - ai-startでCommand Executor自動起動"
echo "  - --se-testerオプションでテスト自動化"
echo "  - 統合されたワーカー管理"
