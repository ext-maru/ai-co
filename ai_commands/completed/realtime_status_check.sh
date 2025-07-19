#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "【現在の状態】"
echo "確認時刻: $(date)"
echo ""

# 1. プロセス確認
echo "Slack Polling Worker:"
if pgrep -f "slack_polling_worker" > /dev/null; then
    PID=$(pgrep -f "slack_polling_worker")
    echo "✅ 動作中 (PID: $PID)"

    # プロセスの詳細
    ps aux | grep $PID | grep -v grep | awk '{print "  CPU: "$3"%, MEM: "$4"%, 起動時刻: "$9}'
else
    echo "❌ 停止中"
fi

# 2. ログファイルの状態
echo ""
echo "ログファイル:"
if [ -f logs/slack_polling_worker.log ]; then
    SIZE=$(stat -c%s logs/slack_polling_worker.log)
    LAST_MOD=$(stat -c %y logs/slack_polling_worker.log | cut -d'.' -f1)
    echo "  サイズ: $SIZE bytes"
    echo "  最終更新: $LAST_MOD"

    # 最新10行
    echo ""
    echo "最新ログ（10行）:"
    tail -10 logs/slack_polling_worker.log
else
    echo "  ログファイルが存在しません"
fi

# 3. エラーチェック
echo ""
echo "エラーチェック:"
if [ -f logs/slack_polling_worker.log ]; then
    ERROR_COUNT=$(tail -100 logs/slack_polling_worker.log | grep -ci error || echo "0")
    echo "  最新100行のエラー数: $ERROR_COUNT"

    if [ $ERROR_COUNT -gt 0 ]; then
        echo "  最新のエラー:"
        tail -100 logs/slack_polling_worker.log | grep -i error | tail -3
    fi
fi

# 4. タスク処理確認
echo ""
echo "タスク処理:"
TASK_COUNT=$(grep -c "タスク化" logs/slack_polling_worker.log 2>/dev/null || echo "0")
echo "  総タスク化数: $TASK_COUNT"

if [ $TASK_COUNT -gt 0 ]; then
    echo "  最新のタスク化:"
    grep "タスク化" logs/slack_polling_worker.log | tail -2
fi
