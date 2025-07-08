#!/bin/bash
cd /home/aicompany/ai_co
echo "🔧 PMWorker最終パッチ適用"

# バックアップ作成
cp workers/pm_worker.py workers/pm_worker.py.backup_$(date +%Y%m%d_%H%M%S)

# パッチ適用
python3 << 'EOF'
import re

# pm_worker.pyを読み込み
with open('workers/pm_worker.py', 'r', encoding='utf-8') as f:
    content = f.read()

# コミットメッセージ部分を修正
old_text = 'commit_message = f"Task {task_id}: {git_result_data[\'summary\']}"\n                        if self.git_flow.commit_changes(commit_message, new_files):'
new_text = 'if self.git_flow.commit_changes(None, new_files, use_best_practices=True):'

content = content.replace(old_text, new_text)

# ファイルを書き戻し
with open('workers/pm_worker.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ パッチ適用完了")
EOF

# 確認
echo ""
echo "📋 変更確認:"
grep -A1 -B1 "commit_changes" workers/pm_worker.py | head -10
echo ""
echo "✅ PMWorkerがベストプラクティス対応になりました！"
echo ""
echo "🎉 これで全ての自動コミットがConventional Commits形式になります！"
