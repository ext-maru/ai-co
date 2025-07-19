#!/bin/bash
echo '🔍 Checking Command Executor Worker...'
ps aux | grep command_executor | grep -v grep
echo ''
echo '📝 Worker log tail:'
tail -20 /home/aicompany/ai_co/logs/command_executor.log 2>/dev/null || echo 'Log file not found yet'
echo ''
echo '📊 Directory status:'
echo 'Pending: '$(ls /home/aicompany/ai_co/ai_commands/pending/ 2>/dev/null)
echo 'Running: '$(ls /home/aicompany/ai_co/ai_commands/running/ 2>/dev/null)
echo 'Completed: '$(ls /home/aicompany/ai_co/ai_commands/completed/ 2>/dev/null)
