#!/bin/bash
cd /home/aicompany/ai_co

echo "🎯 AI Git コミットベストプラクティス - 統合確認"
echo "================================================"
echo ""

# 15秒待機（他のコマンドの実行を待つ）
echo "⏰ 実行待機中..."
for i in {15..1}; do
    echo -ne "  $i秒...  \r"
    sleep 1
done
echo ""

# Pythonバリデーターを実行
echo "🔍 詳細検証を開始..."
python3 validate_best_practices.py

# 実際のコミット例を表示
echo ""
echo "📝 実装後のコミットメッセージ例"
echo "================================================"
echo ""
echo "Before（現在）:"
echo "  Task code_20250703_123456: 新しいワーカーを作成しました"
echo ""
echo "After（ベストプラクティス適用後）:"
echo "  feat(workers): implement advanced notification worker"
echo "  "
echo "  Add comprehensive notification system with support for"
echo "  multiple channels including email, Slack, and SMS."
echo "  "
echo "  - Implement retry mechanism with exponential backoff"
echo "  - Add template engine for message formatting"
echo "  - Create unified notification interface"
echo "  - Support priority-based queue processing"
echo "  "
echo "  The worker handles all notification types through a"
echo "  single interface, reducing code duplication and"
echo "  improving maintainability."
echo "  "
echo "  Refs: code_20250703_123456"
echo ""
echo "================================================"

# 使用方法ガイド
echo ""
echo "📚 使用方法ガイド"
echo "================================================"
echo ""
echo "1. 変更をプレビュー:"
echo "   ai-git commit --preview"
echo ""
echo "2. 現在の変更を分析:"
echo "   ai-git analyze"
echo ""
echo "3. ベストプラクティスを確認:"
echo "   ai-git best-practices"
echo ""
echo "4. CHANGELOGを生成:"
echo "   ai-git changelog"
echo ""
echo "================================================"
echo "✅ 確認完了"
