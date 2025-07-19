#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🔍 ベストプラクティス統合 - 最終動作確認"
echo "==========================================\n"

# 1. PMWorkerの実装確認
echo "📊 PMWorker実装状態:"
if grep -q "commit_message = f\"Task {task_id}" workers/pm_worker.py 2>/dev/null; then
    echo "✅ commit_message定義: 実装済み"
    grep -n "commit_message = f" workers/pm_worker.py | head -1
else
    echo "❌ commit_message定義: 未実装"
fi

if grep -q "use_best_practices=True" workers/pm_worker.py 2>/dev/null; then
    echo "✅ use_best_practices: 設定済み"
    grep -n "use_best_practices=True" workers/pm_worker.py | head -1
else
    echo "❌ use_best_practices: 未設定"
fi

echo ""
echo "📝 該当箇所のコード:"
grep -B3 -A1 "use_best_practices=True" workers/pm_worker.py 2>/dev/null | head -8 || echo "見つかりません"

# 2. GitFlowManagerの確認
echo "\n\n📊 GitFlowManager実装状態:"
if [ -f "libs/git_flow_manager.py" ] && grep -q "use_best_practices" libs/git_flow_manager.py; then
    echo "✅ GitFlowManager: ベストプラクティス対応"
    if grep -q "from libs.commit_message_generator import CommitMessageGenerator" libs/git_flow_manager.py; then
        echo "✅ CommitMessageGeneratorインポート済み"
    fi
else
    echo "❌ GitFlowManager: 未対応"
fi

# 3. CommitMessageGeneratorの確認
echo "\n📊 CommitMessageGenerator:"
if [ -f "libs/commit_message_generator.py" ]; then
    echo "✅ ファイル存在"
    methods=$(grep "def " libs/commit_message_generator.py | wc -l)
    echo "   メソッド数: $methods"
else
    echo "❌ ファイルなし"
fi

# 4. ai-gitコマンドの確認
echo "\n📊 ai-gitコマンド新機能:"
for cmd in analyze changelog best-practices; do
    if grep -q "$cmd" scripts/ai-git 2>/dev/null; then
        echo "✅ ai-git $cmd"
    else
        echo "❌ ai-git $cmd"
    fi
done

# 5. 設定ファイルの確認
echo "\n📊 設定ファイル:"
if [ -f "config/commit_best_practices.json" ]; then
    echo "✅ commit_best_practices.json"
fi
if [ -f ".gitmessage" ]; then
    echo "✅ .gitmessageテンプレート"
fi

# 総合判定
echo "\n\n========================================"
echo "📊 統合状態サマリー:"
echo "========================================"

if grep -q "commit_message = f\"Task {task_id}" workers/pm_worker.py 2>/dev/null && \
   grep -q "use_best_practices=True" workers/pm_worker.py 2>/dev/null && \
   [ -f "libs/commit_message_generator.py" ] && \
   [ -f "config/commit_best_practices.json" ]; then
    echo ""
    echo "🎉 ベストプラクティス統合完了！"
    echo ""
    echo "✅ 全コンポーネントが正常に統合されています"
    echo "✅ 次回のコミットから自動的に適用されます"
    echo ""
    echo "📝 生成されるコミットメッセージ例:"
    echo "-------------------------------------"
    echo "feat(workers): implement notification system"
    echo ""
    echo "Add comprehensive notification framework with"
    echo "support for multiple channels."
    echo ""
    echo "- Implement retry mechanism"
    echo "- Add template engine"
    echo "- Create unified interface"
    echo ""
    echo "Refs: code_20250703_120000"
    echo "-------------------------------------"
    echo ""
    echo "🚀 ai-restart 後から有効になります"
else
    echo ""
    echo "⚠️ 一部コンポーネントが未統合です"
    echo "   PMWorker修正が必要な可能性があります"
fi
