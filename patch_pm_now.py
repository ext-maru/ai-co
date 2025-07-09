#!/usr/bin/env python3
"""
PMWorkerにコミットメッセージベストプラクティスを適用
"""

import sys
from pathlib import Path
sys.path.append(str(Path("/home/aicompany/ai_co")))

from libs.ai_command_helper import AICommandHelper

helper = AICommandHelper()

# PMWorkerパッチコマンド
patch_command = r"""#!/bin/bash
cd /home/aicompany/ai_co

echo "🔧 Patching PMWorker for commit best practices..."

# バックアップ作成
cp workers/pm_worker.py workers/pm_worker_backup_$(date +%Y%m%d_%H%M%S).py

# Pythonでパッチ適用
python3 << 'EOF'
import re
from pathlib import Path

pm_worker_path = Path("workers/pm_worker.py")
content = pm_worker_path.read_text()

# 1. commit_changesの呼び出しを修正
# 旧: if self.git_flow.commit_changes(commit_message, new_files):
# 新: if self.git_flow.commit_changes(use_best_practices=True):

old_pattern = r'commit_message = f"Task \{task_id\}: \{result_data\[\'summary\'\]\}"\s*\n\s*if self\.git_flow\.commit_changes\(commit_message, new_files\):'
new_code = '''# ベストプラクティスモードでコミット（メッセージ自動生成）
                    if self.git_flow.commit_changes(use_best_practices=True):'''

content = re.sub(old_pattern, new_code, content)

# 念のため、別のパターンも試す
if 'use_best_practices=True' not in content:
    # 単純な置換
    content = content.replace(
        'if self.git_flow.commit_changes(commit_message, new_files):',
        'if self.git_flow.commit_changes(use_best_practices=True):'
    )

# ベストプラクティスマーカー追加
if "# COMMIT_BEST_PRACTICES_ENABLED" not in content:
    content = "# COMMIT_BEST_PRACTICES_ENABLED\\n" + content

pm_worker_path.write_text(content)
print("✅ PMWorker patched successfully")
EOF

# 確認
echo ""
echo "📝 Checking patch..."
grep -n "use_best_practices" workers/pm_worker.py && echo "✅ Patch applied" || echo "❌ Patch failed"

# PMWorker再起動が必要
echo ""
echo "⚠️ PMWorkerの再起動が必要です:"
echo "  1. 現在のPMWorkerを停止: Ctrl+C"
echo "  2. 再起動: python3 workers/pm_worker.py"
echo ""
echo "または ai-restart を実行してください"
"""

result = helper.create_bash_command(patch_command, "patch_pm_worker_best_practices")
print(f"✅ PMWorker patch command created: patch_pm_worker_best_practices")
print("⏰ Executing in 6 seconds...")
print("")
print("📋 After patching, PMWorker will:")
print("• Use CommitMessageGenerator to analyze changes")
print("• Generate Conventional Commits format messages")
print("• Include proper type, scope, and detailed body")
print("• Follow 50/72 character rules")
print("• Auto-detect breaking changes")
