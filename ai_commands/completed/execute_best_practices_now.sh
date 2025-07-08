#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
echo '🚀 Executing Commit Best Practices Setup NOW'

# Run the main implementation
if [ -f implement_commit_best_practices.py ]; then
    python3 implement_commit_best_practices.py
else
    echo '❌ Implementation file not found'
fi

# Patch PMWorker
if [ -f patch_pm_now.py ]; then
    python3 patch_pm_now.py
else
    echo '❌ Patch file not found'
fi

echo '✅ Commands submitted to AI Command Executor'