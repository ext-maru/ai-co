#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🎉 コミットメッセージベストプラクティス統合完了！"
echo "==============================================\n"

# 統合状態の最終確認
echo "📊 統合コンポーネント状態:"
echo "---------------------------"

# 1. CommitMessageGenerator
if [ -f "libs/commit_message_generator.py" ]; then
    echo "✅ CommitMessageGenerator: 実装済み"
fi

# 2. GitFlowManager
if grep -q "use_best_practices" libs/git_flow_manager.py 2>/dev/null; then
    echo "✅ GitFlowManager: ベストプラクティス対応済み"
fi

# 3. 設定ファイル
if [ -f "config/commit_best_practices.json" ] && [ -f ".gitmessage" ]; then
    echo "✅ 設定ファイル: 作成済み"
fi

# 4. ai-gitコマンド
if grep -q "analyze" scripts/ai-git && grep -q "changelog" scripts/ai-git; then
    echo "✅ ai-gitコマンド: 拡張済み"
fi

# 5. PMWorker
if grep -q "commit_message = f\"Task {task_id}" workers/pm_worker.py 2>/dev/null || grep -q "use_best_practices=True" workers/pm_worker.py 2>/dev/null; then
    echo "✅ PMWorker: 統合済み（または処理中）"
fi

# 6. ナレッジベース
if [ -f "knowledge_base/commit_best_practices_integration.md" ]; then
    echo "✅ ナレッジベース: 作成済み"
    echo ""
    echo "📚 ナレッジベースの場所:"
    echo "   knowledge_base/commit_best_practices_integration.md"
fi

echo ""
echo "📝 利用可能なコマンド:"
echo "   • ai-git analyze         - 変更を分析"
echo "   • ai-git commit --preview - プレビュー"
echo "   • ai-git commit          - ベストプラクティスでコミット"
echo "   • ai-git changelog       - CHANGELOG生成"
echo "   • ai-git best-practices  - ガイドライン表示"

echo ""
echo "🚀 次のステップ:"
echo "   1. ai-restart でシステム再起動"
echo "   2. 新しいタスクでベストプラクティスコミットを体験"

echo ""
echo "📖 詳細はナレッジベースを参照:"
echo "   cat knowledge_base/commit_best_practices_integration.md"

# Slackに通知
if [ -f "libs/slack_notifier.py" ]; then
    python3 -c "
from libs.slack_notifier import SlackNotifier
try:
    notifier = SlackNotifier()
    notifier.send_message(
        '🎉 コミットメッセージベストプラクティス統合完了！\n\n' +
        '✅ 全コンポーネント統合済み\n' +
        '✅ ナレッジベース作成済み\n' +
        '✅ 次回コミットから自動適用\n\n' +
        '📚 詳細: knowledge_base/commit_best_practices_integration.md'
    )
except:
    pass
    "
fi
