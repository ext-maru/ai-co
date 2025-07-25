#!/bin/bash
# Elder Council Watchdog Script
# エルダー評議会ウォッチドッグスクリプト

PROJECT_ROOT="/home/aicompany/ai_co"
LOG_DIR="$PROJECT_ROOT/logs"
ELDER_LOG="$LOG_DIR/elder_watchdog.log"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$ELDER_LOG"
}

log "🏛️ エルダー評議会ウォッチドッグ起動"

while true; do
    # 1. ワーカーチェック
    WORKER_COUNT=$(ps aux | grep -E 'enhanced_task_worker|intelligent_pm_worker|async_result_worker' | grep -v grep | wc -l)

    if [ "$WORKER_COUNT" -lt 3 ]; then
        log "⚠️ ワーカー不足検出 (現在: $WORKER_COUNT/3)"
        log "🔧 ワーカー復旧開始..."
        cd "$PROJECT_ROOT"
        python3 check_and_fix_workers.py >> "$ELDER_LOG" 2>&1
    fi

    # 2. エルダー監視チェック
    ELDER_MONITOR=$(ps aux | grep 'start_elder_monitoring.py' | grep -v grep | wc -l)

    if [ "$ELDER_MONITOR" -eq 0 ]; then
        log "⚠️ エルダー監視停止検出"
        log "🔧 エルダー監視再起動..."
        cd "$PROJECT_ROOT"
        nohup python3 start_elder_monitoring.py >> "$LOG_DIR/elder_monitoring.log" 2>&1 &
        log "✅ エルダー監視再起動完了"
    fi

    # 3. RabbitMQチェック
    RABBITMQ_STATUS=$(systemctl is-active rabbitmq-server 2>/dev/null || echo "inactive")

    if [ "$RABBITMQ_STATUS" != "active" ]; then
        log "❌ RabbitMQ停止検出"
        # RabbitMQは手動復旧が必要
    fi

    # 4. システムヘルスレポート
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print int(100 - $1)}')

    if [ "$((RANDOM % 12))" -eq 0 ]; then  # 約1時間ごと
        log "📊 定期レポート - ワーカー: $WORKER_COUNT, メモリ: ${MEMORY_USAGE}%, CPU: ${CPU_USAGE}%"
    fi

    # 5分待機
    sleep 300
done
