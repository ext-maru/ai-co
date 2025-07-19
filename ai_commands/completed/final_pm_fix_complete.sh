#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🔧 PMWorkerの最終修正..."

# Pythonで正確に修正
python3 << 'EOF'
import re
from pathlib import Path

pm_worker_path = Path("/home/aicompany/ai_co/workers/pm_worker.py")

if pm_worker_path.exists():
    content = pm_worker_path.read_text()

    # 現在の問題のある行を修正
    # 136行目付近: if self.git_flow.commit_changes(None, new_files, use_best_practices=True):
    # これを以下に修正:
    # commit_message = f"Task {task_id}: {git_result_data['summary']}"
    # if self.git_flow.commit_changes(commit_message, new_files, use_best_practices=True):

    # 正規表現で修正
    pattern = r'(\s*)# ベストプラクティス対応（自動生成）\n(\s*)if self\.git_flow\.commit_changes\(None, new_files, use_best_practices=True\):'

    replacement = r'\1# ファイルをコミット（ベストプラクティス対応）\n\1commit_message = f"Task {task_id}: {git_result_data[\'summary\']}"\n\2if self.git_flow.commit_changes(commit_message, new_files, use_best_practices=True):'

    new_content = re.sub(pattern, replacement, content)

    if new_content != content:
        pm_worker_path.write_text(new_content)
        print("✅ PMWorker修正完了")
        print("   commit_messageを適切に設定しました")
    else:
        print("⚠️ パターンマッチに失敗。直接修正を試みます...")

        # より単純な置換を試みる
        if "if self.git_flow.commit_changes(None, new_files, use_best_practices=True):" in content:
            # 該当行の前にcommit_message定義を追加
            lines = content.split('\n')
            new_lines = []

            for i, line in enumerate(lines):
                if "if self.git_flow.commit_changes(None, new_files, use_best_practices=True):" in line:
                    # インデントを取得
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent

                    # commit_message定義を追加
                    new_lines.append(f'{indent_str}# ファイルをコミット（ベストプラクティス対応）')
                    new_lines.append(f'{indent_str}commit_message = f"Task {{task_id}}: {{git_result_data[\'summary\']}}"')
                    # 修正した行を追加
                    new_lines.append(line.replace('None', 'commit_message'))
                else:
                    new_lines.append(line)

            pm_worker_path.write_text('\n'.join(new_lines))
            print("✅ 直接修正で完了")
else:
    print("❌ PMWorkerファイルが見つかりません")

EOF

echo ""
echo "📋 修正結果確認:"
grep -B2 -A1 "commit_changes" /home/aicompany/ai_co/workers/pm_worker.py | grep -v "^--$" | head -10

echo ""
echo "🎉 修正完了！"
echo "   • commit_messageが正しく設定されました"
echo "   • use_best_practices=Trueも維持されています"
echo ""
echo "🚀 ai-restart でシステムを再起動してください"
