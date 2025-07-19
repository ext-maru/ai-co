#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== 現在の状態確認 ==="
echo ""

# 1. Slack Polling Worker
echo "【Slack Polling Worker】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    PID=$(pgrep -f "slack_polling_worker")
    echo "✅ 動作中 (PID: $PID)"

    # プロセス詳細
    ps aux | grep $PID | grep -v grep

    # 最新ログ（エラーとタスク化に注目）
    echo ""
    echo "最新のログ（重要部分）:"
    if [ -f logs/slack_polling_worker.log ]; then
        # エラーチェック
        ERROR_COUNT=$(tail -100 logs/slack_polling_worker.log | grep -c -i error || echo "0")
        echo "エラー数（最新100行）: $ERROR_COUNT"

        # タスク化チェック
        TASK_COUNT=$(tail -100 logs/slack_polling_worker.log | grep -c "タスク化" || echo "0")
        echo "タスク化数（最新100行）: $TASK_COUNT"

        echo ""
        echo "最新20行:"
        tail -20 logs/slack_polling_worker.log
    fi
else
    echo "❌ 停止中"

    # tmuxセッション確認
    if tmux has-session -t slack_polling 2>/dev/null; then
        echo "⚠️  tmuxセッションは存在するがプロセスがない"
    fi
fi

echo ""
echo "【最新の診断ログファイル】"
# 最新の診断結果ファイルを探す
LATEST_DIAG=$(ls -t ai_commands/logs/*final_diagnosis_results*.log 2>/dev/null | head -1)
if [ -n "$LATEST_DIAG" ]; then
    echo "ファイル: $(basename $LATEST_DIAG)"
    echo "診断結果部分:"
    grep -A 10 "問題の特定" "$LATEST_DIAG" 2>/dev/null | tail -15
fi

echo ""
echo "【RabbitMQキュー】"
sudo rabbitmqctl list_queues name messages | grep -E "ai_tasks|ai_slack" || echo "キュー情報取得失敗"

echo ""
echo "【結論】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    if [ -f logs/slack_polling_worker.log ]; then
        # 最後の更新時刻チェック
        LAST_MOD=$(stat -c %Y logs/slack_polling_worker.log 2>/dev/null || echo "0")
        CURRENT=$(date +%s)
        DIFF=$((CURRENT - LAST_MOD))

        if [ $DIFF -lt 60 ]; then
            echo "✅ Workerは活発に動作中（1分以内にログ更新）"
        elif [ $DIFF -lt 300 ]; then
            echo "⚠️  Workerは動作中だが活動が少ない（${DIFF}秒前に最終更新）"
        else
            echo "❌ Workerは動作中だが活動していない（${DIFF}秒前に最終更新）"
        fi
    fi
else
    echo "❌ Workerが動作していない"
fi
