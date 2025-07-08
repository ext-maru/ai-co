#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🔧 PMWorkerのベストプラクティス修正..."

# PMWorkerのcommit_changes呼び出しを修正
python3 << 'EOF'
import re
from pathlib import Path

pm_worker_path = Path("/home/aicompany/ai_co/workers/pm_worker.py")

if pm_worker_path.exists():
    content = pm_worker_path.read_text()
    
    # 修正前のパターン
    old_pattern = r'(commit_message = f"Task {task_id}: {git_result_data\[\'summary\'\]}")\s*\n(\s*if self\.git_flow\.commit_changes\(commit_message, new_files\):)'
    
    # 修正後のパターン
    new_pattern = r'\1\n\2[:-1], use_best_practices=True):'
    
    # 置換実行
    new_content = re.sub(old_pattern, new_pattern, content)
    
    if new_content != content:
        pm_worker_path.write_text(new_content)
        print("✅ PMWorker修正完了")
        print("   commit_changesにuse_best_practices=Trueを追加しました")
    else:
        print("ℹ️  既に修正済みまたはパターンが見つかりませんでした")
        # 直接文字列置換を試みる
        if "if self.git_flow.commit_changes(commit_message, new_files):" in content:
            new_content = content.replace(
                "if self.git_flow.commit_changes(commit_message, new_files):",
                "if self.git_flow.commit_changes(commit_message, new_files, use_best_practices=True):"
            )
            pm_worker_path.write_text(new_content)
            print("✅ 直接置換で修正完了")
        else:
            print("❌ 修正対象が見つかりませんでした")
else:
    print("❌ PMWorkerファイルが見つかりません")
EOF

echo ""
echo "📋 修正結果を確認..."
grep -n "commit_changes" /home/aicompany/ai_co/workers/pm_worker.py | head -5

echo ""
echo "🚀 PMWorkerを再起動してください: ai-restart"
echo "✅ 修正完了"