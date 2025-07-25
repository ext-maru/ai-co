#!/bin/bash
# ナレッジベースファイル監視デーモン

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/tmp/knowledge_monitor.pid"
LOG_FILE="$PROJECT_ROOT/logs/knowledge_monitor.log"

# ログ関数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [MONITOR] $1" | tee -a "$LOG_FILE"
}

# PIDファイルのチェック
if [ -f "$PID_FILE" ]; then
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log "ERROR: 監視プロセスが既に実行中です (PID: $(cat "$PID_FILE"))"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# PIDファイルの作成
echo $$ > "$PID_FILE"

# 監視開始
log "INFO: ナレッジベースファイル監視を開始します"

# シグナルハンドラー
cleanup() {
    log "INFO: 監視プロセスを終了します"
    rm -f "$PID_FILE"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ファイル監視の実行
inotifywait -m -r -e create,modify,delete,move \
    "$PROJECT_ROOT/workers/" \
    "$PROJECT_ROOT/commands/" \
    "$PROJECT_ROOT/libs/" \
    "$PROJECT_ROOT/core/" \
    "$PROJECT_ROOT/config/" \
    --format '%w%f %e' 2>/dev/null | while read file event; do

    # 一時ファイルや無関係なファイルをスキップ
    if [[ "$file" == *".swp" ]] || [[ "$file" == *".tmp" ]] || [[ "$file" == *"__pycache__"* ]]; then
        continue
    fi

    log "INFO: ファイル変更検出: $file ($event)"

    # 変更から少し待ってから処理（連続する変更をまとめる）
    sleep 1

    # 更新トリガーを実行
    "$PROJECT_ROOT/scripts/update_knowledge_trigger.sh" "$file" "$event" &
done
