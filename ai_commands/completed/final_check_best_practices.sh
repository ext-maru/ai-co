#!/bin/bash
cd /home/aicompany/ai_co

echo "🔍 AI Git コミットベストプラクティス - 最終確認"
echo "================================================"
echo ""

# 1. PMWorkerの確認
echo "1️⃣ PMWorker の現在の実装状態:"
echo "   現在のcommit_changes呼び出し:"
grep -n "commit_changes" workers/pm_worker.py | head -5
echo ""
if grep -q "use_best_practices=True" workers/pm_worker.py; then
    echo "   ✅ ベストプラクティス対応済み"
else
    echo "   ❌ 旧形式のまま（パッチ未適用）"
fi
echo ""

# 2. CommitMessageGeneratorの確認
echo "2️⃣ CommitMessageGenerator:"
if [ -f "libs/commit_message_generator.py" ]; then
    echo "   ✅ ファイル存在"
    lines=$(wc -l < libs/commit_message_generator.py)
    echo "   📏 ファイルサイズ: ${lines}行"
else
    echo "   ❌ ファイルなし"
fi
echo ""

# 3. GitFlowManagerの確認
echo "3️⃣ GitFlowManager:"
if grep -q "use_best_practices" libs/git_flow_manager.py; then
    echo "   ✅ use_best_practicesパラメータ実装済み"
    if grep -q "CommitMessageGenerator" libs/git_flow_manager.py; then
        echo "   ✅ CommitMessageGenerator統合済み"
    fi
else
    echo "   ❌ ベストプラクティス未対応"
fi
echo ""

# 4. 設定ファイル
echo "4️⃣ 設定ファイル:"
if [ -f "config/commit_best_practices.json" ]; then
    echo "   ✅ commit_best_practices.json 存在"
    types=$(jq -r '.types | keys[]' config/commit_best_practices.json 2>/dev/null | wc -l)
    echo "   📊 定義されたタイプ数: $types"
fi
echo ""

# 5. ai-gitコマンド
echo "5️⃣ ai-gitコマンドの新機能:"
for cmd in "preview" "analyze" "best-practices" "changelog"; do
    if grep -q "\"$cmd\"" scripts/ai-git 2>/dev/null; then
        echo "   ✅ $cmd コマンド実装済み"
    else
        echo "   ❌ $cmd コマンド未実装"
    fi
done
echo ""

# 6. AI Command Executorの状態
echo "6️⃣ AI Command Executor:"
if pgrep -f "command_executor_worker" > /dev/null; then
    echo "   ✅ 実行中"
    echo "   📁 pending内のファイル数: $(ls ai_commands/pending/*.sh 2>/dev/null | wc -l)"
else
    echo "   ❌ 停止中"
fi
echo ""

echo "================================================"
echo "📊 サマリー"
echo "================================================"

if grep -q "use_best_practices=True" workers/pm_worker.py; then
    echo "✅ PMWorkerはベストプラクティス対応済みです！"
    echo "🎉 全ての自動コミットがConventional Commits形式になります"
else
    echo "⚠️  PMWorkerはまだ旧形式です"
    echo "💡 apply_final_pm_patch.sh の実行を待っています..."
fi
