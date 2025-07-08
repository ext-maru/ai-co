#!/bin/bash
cd /home/aicompany/ai_co
echo "📊 AI Git コミットベストプラクティス - 最終確認"
echo ""

# Pythonレポートを実行
python3 final_best_practices_report.py

# 手動でPMWorkerのパッチ状態も確認
echo ""
echo "🔍 PMWorkerの詳細確認:"
echo "================================================"
echo ""

# 現在の実装を表示
echo "現在のcommit_changes呼び出し:"
grep -C2 "commit_changes" workers/pm_worker.py | head -10

echo ""
echo "================================================"
echo ""

# パッチ適用の提案
if ! grep -q "use_best_practices=True" workers/pm_worker.py; then
    echo "⚠️  PMWorkerはまだ旧形式です"
    echo ""
    echo "💡 修正方法:"
    echo "   1. apply_pm_patch_direct.sh を実行"
    echo "   2. または手動で以下を変更:"
    echo ""
    echo "   変更前:"
    echo '   commit_message = f"Task {task_id}: {git_result_data['"'"'summary'"'"']}"'
    echo '   if self.git_flow.commit_changes(commit_message, new_files):'
    echo ""
    echo "   変更後:"
    echo '   if self.git_flow.commit_changes(None, new_files, use_best_practices=True):'
else
    echo "✅ PMWorkerは既にベストプラクティス対応済みです！"
fi
