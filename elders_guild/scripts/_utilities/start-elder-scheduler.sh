#!/bin/bash
#
# Elder Scheduled Tasks Service Starter
# エルダーズギルドAPScheduler統合スケジューラー起動
#

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 環境変数を読み込み
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi

# ログディレクトリ
LOG_DIR="$PROJECT_ROOT/logs/elder_scheduler"
mkdir -p "$LOG_DIR"

# PIDファイル
PID_FILE="$PROJECT_ROOT/logs/elder_scheduler.pid"

# ログファイル
LOG_FILE="$LOG_DIR/$(date +%Y%m%d_%H%M%S).log"

# タイムスタンプ付きロギング関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 既存プロセス確認
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    log "⚠️ エルダースケジューラーが既に起動しています (PID: $(cat "$PID_FILE"))"
    exit 1
fi

log "🚀 エルダーズギルドスケジューラー起動開始"
log "📁 プロジェクトルート: $PROJECT_ROOT"
log "📝 ログファイル: $LOG_FILE"

# Python環境に移動
cd "$PROJECT_ROOT"

# バックグラウンドで実行
nohup python3 -u libs/elder_scheduled_tasks.py >> "$LOG_FILE" 2>&1 &

# PID保存
echo $! > "$PID_FILE"
SCHEDULER_PID=$!

log "✅ エルダースケジューラー起動完了 (PID: $SCHEDULER_PID)"
log "🔍 スケジューラー状態確認: kill -0 $SCHEDULER_PID"
log "🛑 スケジューラー停止: $PROJECT_ROOT/scripts/stop-elder-scheduler.sh"

# 起動確認
sleep 3
if kill -0 $SCHEDULER_PID 2>/dev/null; then
    log "✅ スケジューラー正常起動確認"
else
    log "❌ スケジューラー起動失敗"
    rm -f "$PID_FILE"
    exit 1
fi

log "🏁 起動スクリプト完了"