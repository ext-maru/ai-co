#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo '🔧 Applying final PMWorker patch...'

# Simple sed replacement
sed -i 's/if self\.git_flow\.commit_changes(commit_message, new_files):/if self.git_flow.commit_changes(use_best_practices=True):/' workers/pm_worker.py

# Verify
echo ''
echo '📝 Verification:'
grep -n 'use_best_practices' workers/pm_worker.py && echo '✅ PMWorker patch applied successfully!' || echo '❌ Patch may have failed'

# Run status check
echo ''
echo '📊 Running full status check...'
python3 check_implementation_status.py

echo ''
echo '🎉 All done! Check the results above.'