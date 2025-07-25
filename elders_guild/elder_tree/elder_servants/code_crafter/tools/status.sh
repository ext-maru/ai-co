#!/bin/bash

# ヘルプ表示
show_help() {
    cat << EOF
status.sh - AI Company システム状態確認コマンド

使用方法:
    status.sh [オプション]

説明:
    AI Company システムの状態を確認します。
    以下の情報を表示します:
    - RabbitMQサーバー状態
    - キューの状態
    - Claude CLI可用性
    - 出力ファイル数
    - ワーカープロセス状態

オプション:
    --help, -h          このヘルプを表示
    --watch             リアルタイム監視モード (2秒間隔)
    --brief             簡潔な表示

例:
    status.sh                   # 状態を1回表示
    status.sh --watch           # 2秒間隔で監視
    status.sh --brief           # 簡潔な表示
EOF
}

# 引数チェック
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

if [ "$1" = "--watch" ]; then
    echo "🔄 リアルタイム監視モード (Ctrl+C で終了)"
    watch -n 2 "$0 --brief"
    exit 0
fi

PROJECT_DIR="$HOME/ai_co"

# 簡潔表示フラグ
BRIEF_MODE=false
if [ "$1" = "--brief" ]; then
    BRIEF_MODE=true
fi

if [ "$BRIEF_MODE" = "false" ]; then
    echo "🏢 AI Company Status - $(date +%H:%M:%S)"
    echo "===================================="
else
    echo "🏢 $(date +%H:%M:%S)"
fi

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
