#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

# PMWorkerの修正
python3 << 'EOF'
import re
from pathlib import Path

pm_path = Path('workers/pm_worker.py')
content = pm_path.read_text()

# commit_changesの呼び出しを修正
old_pattern = r'commit_message = f"Task {task_id}: {git_result_data\[\'summary\'\]}"\s*\n\s*if self\.git_flow\.commit_changes\(commit_message, new_files\):'
new_code = 'if self.git_flow.commit_changes(use_best_practices=True):'

content = re.sub(old_pattern, new_code, content)

# 念のため別のパターンも
if 'commit_changes(commit_message, new_files)' in content:
    content = content.replace(
        'if self.git_flow.commit_changes(commit_message, new_files):',
        'if self.git_flow.commit_changes(use_best_practices=True):'
    )

pm_path.write_text(content)
print('✅ PMWorker patched successfully')
EOF

# 確認
echo ''
echo '📝 Verification:'
grep -n 'use_best_practices' workers/pm_worker.py && echo '✅ PMWorker now uses best practices!' || echo '❌ Patch may have failed'

echo ''
echo '🎉 Complete! All components now use Conventional Commits!'
