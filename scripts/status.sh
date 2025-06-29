#!/bin/bash

PROJECT_DIR="$HOME/ai_co"

echo "🏢 AI Company Status - $(date +%H:%M:%S)"
echo "===================================="

# RabbitMQ
echo "[RabbitMQ]"
if systemctl is-active --quiet rabbitmq-server; then
    echo "  状態: ✅ 稼働中"
    sudo rabbitmqctl list_queues name messages 2>/dev/null | grep -E "task_queue|result_queue" | awk '{printf "  %-15s: %s messages\n", $1, $2}'
else
    echo "  状態: ❌ 停止"
fi

# Claude CLI
echo ""
echo "[Claude CLI]"
if command -v claude &> /dev/null; then
    echo "  状態: ✅ 利用可能"
else
    echo "  状態: ⚠️  シミュレーションモード"
fi

# 出力ファイル
echo ""
echo "[出力ファイル]"
OUTPUT_COUNT=$(ls -1 "$PROJECT_DIR/output" 2>/dev/null | wc -l)
echo "  ファイル数: $OUTPUT_COUNT"
if [ $OUTPUT_COUNT -gt 0 ]; then
    echo "  最新: $(ls -t "$PROJECT_DIR/output" | head -1)"
fi

# ワーカー
echo ""
echo "[ワーカー状態]"
ps aux | grep -E "task_worker|result_worker" | grep -v grep | awk '{print "  " $NF}'
