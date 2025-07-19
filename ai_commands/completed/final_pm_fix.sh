#!/bin/bash
cd /home/aicompany/ai_co
echo "🔧 PMWorker ベストプラクティス修正 - 最終適用"
echo "================================================"

# バックアップ作成
cp workers/pm_worker.py workers/pm_worker.py.backup_$(date +%Y%m%d_%H%M%S)

# 修正前の確認
echo "📋 修正前の状態:"
grep -n -A1 -B1 "commit_message = " workers/pm_worker.py | head -10

# sedで修正
echo ""
echo "🔧 修正を適用中..."

# 複数行のパターンをsedで置換
sed -i '/# ファイルをコミット/{N;N;s/# ファイルをコミット\n.*commit_message = f"Task {task_id}: {git_result_data\['"'"'summary'"'"'\]}"\n.*if self.git_flow.commit_changes(commit_message, new_files):/# ファイルをコミット（ベストプラクティス適用）\n                        if self.git_flow.commit_changes(None, new_files, use_best_practices=True):/}' workers/pm_worker.py

# 修正後の確認
echo ""
echo "📋 修正後の状態:"
grep -n -A1 -B1 "commit_changes" workers/pm_worker.py | head -10

# 最終確認
echo ""
echo "================================================"
echo "🎉 実装完了状況"
echo "================================================"
echo ""

# 各コンポーネントの確認
components=(
    "CommitMessageGenerator:libs/commit_message_generator.py"
    "GitFlowManager:libs/git_flow_manager.py:use_best_practices"
    "PMWorker:workers/pm_worker.py:use_best_practices=True"
    "ai-git preview:scripts/ai-git:preview"
    "ai-git analyze:scripts/ai-git:analyze"
    "設定ファイル:config/commit_best_practices.json"
    ".gitmessage:.gitmessage"
)

success_count=0
total_count=${#components[@]}

for component in "${components[@]}"; do
    IFS=':' read -r name file pattern <<< "$component"

    if [ -z "$pattern" ]; then
        # ファイル存在チェック
        if [ -f "$file" ]; then
            echo "✅ $name"
            ((success_count++))
        else
            echo "❌ $name"
        fi
    else
        # パターン検索
        if grep -q "$pattern" "$file" 2>/dev/null; then
            echo "✅ $name"
            ((success_count++))
        else
            echo "❌ $name"
        fi
    fi
done

echo ""
echo "================================================"
echo "実装率: $success_count/$total_count ($(( success_count * 100 / total_count ))%)"
echo "================================================"

if [ $success_count -eq $total_count ]; then
    echo ""
    echo "🎊 全ての実装が完了しました！"
    echo ""
    echo "📝 今後のコミットメッセージ例："
    echo ""
    echo "  feat(workers): implement advanced notification system"
    echo "  fix(api): resolve timeout issue in data processing"
    echo "  docs(readme): update installation instructions"
    echo "  refactor(core): simplify base worker initialization"
    echo "  test(unit): add coverage for new features"
    echo ""
    echo "✨ AI Companyは完全にConventional Commits対応になりました！"
else
    echo ""
    echo "⚠️  一部の実装が未完了です"
fi
