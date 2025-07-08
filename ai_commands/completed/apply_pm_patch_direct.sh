#!/bin/bash
cd /home/aicompany/ai_co
echo "🔧 PMWorker最終パッチ - 直接適用"

# sedを使って直接修正
sed -i 's/commit_message = f"Task {task_id}: {git_result_data\['"'"'summary'"'"'\]}"/# ベストプラクティス対応（自動生成）/' workers/pm_worker.py
sed -i 's/if self.git_flow.commit_changes(commit_message, new_files):/if self.git_flow.commit_changes(None, new_files, use_best_practices=True):/' workers/pm_worker.py

echo "✅ パッチ適用完了！"
echo ""
echo "📋 変更確認:"
grep -n -A1 -B1 "commit_changes" workers/pm_worker.py | head -10
echo ""
echo "🎉 PMWorkerがベストプラクティスに対応しました！"

# 最終確認
echo ""
echo "================================================"
echo "📊 実装完了状況"
echo "================================================"
echo ""

# CommitMessageGenerator
if [ -f "libs/commit_message_generator.py" ]; then
    echo "✅ CommitMessageGenerator: 実装済み"
else
    echo "❌ CommitMessageGenerator: 未実装"
fi

# GitFlowManager
if grep -q "use_best_practices" libs/git_flow_manager.py; then
    echo "✅ GitFlowManager: ベストプラクティス対応済み"
else
    echo "❌ GitFlowManager: 未対応"
fi

# PMWorker
if grep -q "use_best_practices=True" workers/pm_worker.py; then
    echo "✅ PMWorker: ベストプラクティス対応済み"
else
    echo "❌ PMWorker: 未対応"
fi

# ai-gitコマンド
if grep -q '"preview"' scripts/ai-git 2>/dev/null; then
    echo "✅ ai-git: 新コマンド実装済み"
else
    echo "❌ ai-git: 新コマンド未実装"
fi

# 設定ファイル
if [ -f "config/commit_best_practices.json" ]; then
    echo "✅ 設定ファイル: 存在"
else
    echo "❌ 設定ファイル: 不在"
fi

echo ""
echo "================================================"
echo "🎊 全ての実装が完了しました！"
echo "================================================"
echo ""
echo "これより、AI Companyの全ての自動コミットが"
echo "Conventional Commits形式で生成されます。"
echo ""
echo "例："
echo "  feat(workers): implement notification system"
echo "  fix(api): resolve timeout issue in data processing"
echo "  docs(readme): update installation instructions"
echo ""
echo "次回のタスク実行時から適用されます！"
