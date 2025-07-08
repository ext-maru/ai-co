#!/bin/bash
echo '📊 AI Company Health Check by AI'
echo 'Time: '$(date)
echo ''
echo 'Memory Usage:'
free -h | grep -E 'Mem:|Swap:'
echo ''
echo 'Disk Usage:'
df -h | grep -E '^/dev|Filesystem'
echo ''
echo 'Worker Processes:'
ps aux | grep -E '(worker|executor)' | grep -v grep | wc -l
echo ' workers running'
echo ''
echo '✅ Health check complete!'