#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

# バックグラウンドで起動
nohup python3 workers/knowledge_scheduler_worker.py > logs/knowledge_scheduler.log 2>&1 &
echo $! > /tmp/knowledge_scheduler.pid

echo "✅ Knowledge scheduler started (PID: $(cat /tmp/knowledge_scheduler.pid))"
