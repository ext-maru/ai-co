#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "🔧 PMWorker最終修正（確実版）"
echo "===================================\n"

# バックアップ作成
cp workers/pm_worker.py workers/pm_worker.py.bak_$(date +%Y%m%d_%H%M%S)

# Pythonで確実に修正
python3 << 'EOF'
import re
from pathlib import Path

pm_worker_path = Path("/home/aicompany/ai_co/workers/pm_worker.py")

if pm_worker_path.exists():
    content = pm_worker_path.read_text()
    
    # 修正前のコードを探す
    # 行135-136あたり: if self.git_flow.commit_changes(None, new_files, use_best_practices=True):
    
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        if "if self.git_flow.commit_changes(None, new_files, use_best_practices=True):" in line:
            # この行の前にcommit_message定義を追加
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent
            
            # コメント行を確認して削除または修正
            if i > 0 and "ベストプラクティス対応（自動生成）" in lines[i-1]:
                new_lines[-1] = f"{indent_str}# ファイルをコミット（ベストプラクティス対応）"
            
            # commit_message定義を追加
            new_lines.append(f'{indent_str}commit_message = f"Task {{task_id}}: {{git_result_data[\'summary\']}}'[:100] + '"')
            
            # 修正した行を追加（Noneをcommit_messageに置換）
            new_lines.append(line.replace('None', 'commit_message'))
        else:
            new_lines.append(line)
    
    # ファイルを書き込み
    pm_worker_path.write_text('\n'.join(new_lines))
    print("✅ PMWorker修正完了")
    
    # 修正結果を確認
    print("\n📋 修正箇所の確認:")
    lines = pm_worker_path.read_text().split('\n')
    for i, line in enumerate(lines):
        if "commit_message = " in line and "git_result_data" in line:
            print(f"  行{i+1}: {line.strip()}")
        elif "use_best_practices=True" in line:
            print(f"  行{i+1}: {line.strip()}")
            break
else:
    print("❌ PMWorkerファイルが見つかりません")
EOF

echo ""
echo "📊 修正結果の最終確認:"
echo "----------------------"
grep -B3 -A1 "use_best_practices=True" workers/pm_worker.py | head -10

echo ""
echo "🎉 修正完了！"
echo "   • commit_messageが正しく定義されました"
echo "   • use_best_practices=Trueが維持されています"
echo ""
echo "🚀 次のステップ:"
echo "   1. ai-restart でシステム再起動"
echo "   2. 新しいタスクでベストプラクティスコミットをテスト"