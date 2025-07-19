#!/bin/bash
echo '🛑 Stopping old Command Executor processes...'
kill 1084 2>/dev/null && echo 'Killed PID 1084' || echo 'PID 1084 already stopped'
kill 1088 2>/dev/null && echo 'Killed PID 1088' || echo 'PID 1088 already stopped'
rm -f /tmp/ai_command_executor.pid
echo ''
echo '🚀 Starting new Command Executor...'
cd /home/aicompany/ai_co
source venv/bin/activate
python3 workers/command_executor_worker.py > logs/command_executor.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > /tmp/ai_command_executor.pid
echo "✓ New Command Executor started (PID: $NEW_PID)"
echo ''
echo '📊 Checking status...'
ps aux | grep command_executor | grep -v grep
echo ''
echo '✅ Restart complete!'
