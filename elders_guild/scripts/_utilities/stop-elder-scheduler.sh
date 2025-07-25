#!/bin/bash
#
# Elder Scheduled Tasks Service Stopper
# エルダーズギルドAPSchedulerスケジューラー停止
#

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# PIDファイル
PID_FILE="$PROJECT_ROOT/logs/elder_scheduler.pid"

# ログディレクトリ
LOG_DIR="$PROJECT_ROOT/logs/elder_scheduler"

# タイムスタンプ付きロギング関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

if [ ! -f "$PID_FILE" ]; then
    log "⚠️ PIDファイルが見つかりません。スケジューラーは起動していない可能性があります。"
    exit 1
fi

SCHEDULER_PID=$(cat "$PID_FILE")

if ! kill -0 "$SCHEDULER_PID" 2>/dev/null; then
    log "⚠️ PID $SCHEDULER_PID のプロセスが見つかりません。"
    rm -f "$PID_FILE"
    exit 1
fi

log "🛑 エルダースケジューラー停止開始 (PID: $SCHEDULER_PID)"

# 優雅な停止を試行
kill -TERM "$SCHEDULER_PID"

# 停止確認
for i in {1..10}; do
    if ! kill -0 "$SCHEDULER_PID" 2>/dev/null; then
        log "✅ スケジューラー正常停止完了"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 強制停止
log "⚠️ 優雅な停止に失敗、強制停止実行"
kill -KILL "$SCHEDULER_PID" 2>/dev/null

# 最終確認
if kill -0 "$SCHEDULER_PID" 2>/dev/null; then
    log "❌ スケジューラー停止失敗"
    exit 1
else
    log "✅ スケジューラー強制停止完了"
    rm -f "$PID_FILE"
fi

log "🏁 停止スクリプト完了"