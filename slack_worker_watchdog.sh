#!/bin/bash
# SlackWorker自動復旧監視スクリプト
# エルダーズ会議決定事項の実装

WORKER_NAME="slack_polling_worker"
WORKER_PATH="/home/aicompany/ai_co/workers/slack_polling_worker.py"
LOG_FILE="/home/aicompany/ai_co/logs/slack_worker_watchdog.log"
SLACK_WEBHOOK_URL="${SLACK_BOT_TOKEN:-}"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SlackWatchdog] $1" | tee -a "$LOG_FILE"
}

send_slack_alert() {
    local message="$1"
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        # Slack通知（webhook使用）
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 **SlackWorker Alert** 🚨\n$message\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
}

check_and_restart_worker() {
    # SlackPollingWorkerプロセス確認
    if pgrep -f "$WORKER_NAME.py" > /dev/null; then
        log_message "✅ SlackWorker正常稼働中"
        return 0
    fi
    
    log_message "❌ SlackWorker停止検知 - 自動復旧開始"
    send_slack_alert "SlackWorker停止検知。自動復旧を開始します..."
    
    # ワーカー再起動
    cd /home/aicompany/ai_co
    nohup python3 "$WORKER_PATH" > /dev/null 2>&1 &
    local worker_pid=$!
    
    # 起動確認（最大30秒待機）
    local retry_count=0
    while [ $retry_count -lt 30 ]; do
        if pgrep -f "$WORKER_NAME.py" > /dev/null; then
            log_message "✅ SlackWorker自動復旧成功 (PID: $worker_pid)"
            send_slack_alert "✅ SlackWorker自動復旧完了！対話機能が回復しました。"
            return 0
        fi
        sleep 1
        retry_count=$((retry_count + 1))
    done
    
    log_message "❌ SlackWorker自動復旧失敗 - 手動介入が必要"
    send_slack_alert "❌ SlackWorker自動復旧失敗。手動での確認が必要です。"
    return 1
}

# メイン監視ループ
log_message "🔍 SlackWorker監視開始（30秒間隔）"
send_slack_alert "🔍 SlackWorker自動監視システム開始"

while true; do
    check_and_restart_worker
    sleep 30
done