#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🔧 PMWorker最終修正を実行..."

# sedコマンドで直接修正
sed -i 's/if self.git_flow.commit_changes(commit_message, new_files):/if self.git_flow.commit_changes(commit_message, new_files, use_best_practices=True):/' workers/pm_worker.py

echo "✅ 修正完了"
echo ""
echo "📋 修正結果確認:"
grep -n "use_best_practices=True" workers/pm_worker.py

echo ""
echo "🎉 ベストプラクティス統合完了！"
echo ""
echo "📝 今後の自動コミットは以下の形式になります:"
echo "   feat(workers): implement new feature"
echo "   "
echo "   Detailed description of the changes..."
echo "   "
echo "   - Change 1"
echo "   - Change 2"
echo "   "
echo "   Refs: task_id"
echo ""
echo "🚀 ai-restart でシステムを再起動してください"
