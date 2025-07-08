#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🎯 コミットベストプラクティス統合 - 最終確認"
echo "================================================\n"

echo "📊 統合コンポーネント状態:"
echo "---------------------------"

# 1. CommitMessageGenerator
if [ -f "libs/commit_message_generator.py" ]; then
    echo "✅ CommitMessageGenerator: 実装済み"
    methods=$(grep "def " libs/commit_message_generator.py | wc -l)
    echo "   └─ メソッド数: $methods"
else
    echo "❌ CommitMessageGenerator: 未実装"
fi

# 2. GitFlowManager
if grep -q "use_best_practices" libs/git_flow_manager.py 2>/dev/null; then
    echo "✅ GitFlowManager: ベストプラクティス対応"
    if grep -q "from libs.commit_message_generator import CommitMessageGenerator" libs/git_flow_manager.py; then
        echo "   └─ CommitMessageGeneratorインポート済み"
    fi
else
    echo "❌ GitFlowManager: 未対応"
fi

# 3. PMWorker
echo ""
echo "🔧 PMWorker統合状態:"
if grep -q "use_best_practices=True" workers/pm_worker.py 2>/dev/null; then
    echo "✅ use_best_practices=True 設定済み"
    
    # commit_messageが正しく設定されているか確認
    if grep -B2 "use_best_practices=True" workers/pm_worker.py | grep -q "commit_message = "; then
        echo "✅ commit_message 正しく定義"
        echo ""
        echo "📍 実装箇所:"
        grep -B2 -A1 "use_best_practices=True" workers/pm_worker.py | head -5
    else
        echo "❌ commit_message が未定義（Noneになっている）"
    fi
else
    echo "❌ use_best_practices未設定"
fi

# 4. ai-gitコマンド
echo ""
echo "📝 ai-gitコマンド新機能:"
for cmd in "analyze" "changelog" "best-practices"; do
    if grep -q "$cmd" scripts/ai-git 2>/dev/null; then
        echo "   ✅ ai-git $cmd"
    else
        echo "   ❌ ai-git $cmd"
    fi
done

# 5. 設定ファイル
echo ""
echo "⚙️ 設定ファイル:"
if [ -f "config/commit_best_practices.json" ]; then
    echo "   ✅ commit_best_practices.json"
    types=$(jq -r '.types | length' config/commit_best_practices.json 2>/dev/null || echo "0")
    echo "      └─ 定義済みタイプ: $types"
fi

if [ -f ".gitmessage" ]; then
    echo "   ✅ .gitmessageテンプレート"
fi

echo ""
echo "================================================"
echo "📊 総合評価:"

# すべてが正しく統合されているかチェック
if grep -q "use_best_practices=True" workers/pm_worker.py 2>/dev/null && \
   grep -B2 "use_best_practices=True" workers/pm_worker.py | grep -q "commit_message = " && \
   [ -f "libs/commit_message_generator.py" ] && \
   [ -f "config/commit_best_practices.json" ]; then
    echo ""
    echo "🎉 ベストプラクティス統合完了！"
    echo ""
    echo "📝 生成されるコミットメッセージ例:"
    echo "   feat(workers): implement notification system"
    echo "   "
    echo "   Add comprehensive notification framework with support for"
    echo "   multiple channels including email, Slack, and SMS."
    echo "   "
    echo "   - Implement retry mechanism with exponential backoff"
    echo "   - Add template engine for message formatting"
    echo "   - Create unified notification interface"
    echo "   "
    echo "   Refs: code_20250703_120000"
    echo ""
    echo "🚀 次のステップ: ai-restart でシステム再起動"
else
    echo ""
    echo "⚠️  まだ一部のコンポーネントが未対応です"
    echo "   → final_pm_fix_completeコマンドを実行してください"
fi

echo ""
echo "================================================"