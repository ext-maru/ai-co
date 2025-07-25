#!/bin/bash
#
# Elder Scheduler再起動スクリプト
# Enhanced Auto Issue Processorへの移行用
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔄 Elder Scheduler再起動中..."

# 既存のプロセスを停止
echo "🛑 既存のElder Schedulerプロセスを停止..."
pkill -f "elder_scheduled_tasks.py" || true
sleep 2

# 念のため強制終了
if pgrep -f "elder_scheduled_tasks.py" > /dev/null; then
    echo "⚠️ 強制終了を実行..."
    pkill -9 -f "elder_scheduled_tasks.py"
    sleep 1
fi

# ログディレクトリ確認
mkdir -p "$PROJECT_ROOT/logs"

# 新しいプロセスを起動
echo "🚀 新しいElder Schedulerを起動..."
cd "$PROJECT_ROOT"
nohup python3 -m libs.elder_scheduled_tasks > logs/elder_scheduler.log 2>&1 &

NEW_PID=$!
echo "✅ Elder Scheduler起動完了 (PID: $NEW_PID)"

# 起動確認
sleep 3
if ps -p $NEW_PID > /dev/null; then
    echo "✅ プロセスが正常に動作しています"
    echo ""
    echo "📋 変更内容:"
    echo "  - Auto Issue Processor → Enhanced Auto Issue Processor"
    echo "  - 5分ごと: 1件ずつ処理（全優先度）"
    echo "  - 深夜1時: 10件バッチ処理（中・低優先度）"
    echo "  - 再オープン検知機能有効"
    echo ""
    echo "📊 ログ確認:"
    echo "  tail -f logs/elder_scheduler.log"
else
    echo "❌ プロセスの起動に失敗しました"
    echo "ログを確認してください: logs/elder_scheduler.log"
    exit 1
fi