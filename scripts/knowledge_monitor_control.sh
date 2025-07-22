#!/bin/bash
# ナレッジベース監視制御スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/tmp/knowledge_monitor.pid"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "ERROR: 監視プロセスが既に実行中です (PID: $(cat "$PID_FILE"))"
            exit 1
        fi
        echo "INFO: ナレッジベース監視を開始します"
        nohup "$PROJECT_ROOT/scripts/knowledge_file_monitor.sh" > /dev/null 2>&1 &
        echo "INFO: 監視プロセスを開始しました (PID: $!)"
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                rm -f "$PID_FILE"
                echo "INFO: 監視プロセスを停止しました (PID: $PID)"
            else
                echo "WARN: PIDファイルは存在しますが、プロセスが見つかりません"
                rm -f "$PID_FILE"
            fi
        else
            echo "INFO: 監視プロセスは実行されていません"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "INFO: 監視プロセスが実行中です (PID: $(cat "$PID_FILE"))"
        else
            echo "INFO: 監視プロセスは停止しています"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "使用方法: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
