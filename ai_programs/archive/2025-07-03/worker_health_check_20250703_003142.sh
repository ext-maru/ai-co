#!/bin/bash
echo "=== AI Company Worker Status ==="
echo "Checking at: $(date)"
echo ""

# アクティブなワーカーをチェック
echo "Active Workers:"
ps aux | grep -E "(task_worker|pm_worker|result_worker|command_executor)" | grep -v grep | while read line; do
    PID=$(echo $line | awk '{print $2}')
    CPU=$(echo $line | awk '{print $3}')
    MEM=$(echo $line | awk '{print $4}')
    CMD=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
    echo "  PID: $PID | CPU: $CPU% | MEM: $MEM% | $CMD"
done

echo ""
echo "RabbitMQ Queues:"
sudo rabbitmqctl list_queues name messages 2>/dev/null || echo "  (RabbitMQ access requires sudo)"

echo ""
echo "Recent Logs:"
find /home/aicompany/ai_co/logs -name "*.log" -type f -mmin -60 -exec basename {} \; | head -5
