#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo ""
echo "=== 自動修正 ==="

# Workerが動作していない場合
if ! pgrep -f "slack_polling_worker" > /dev/null; then
    echo "Slack Polling Workerを起動します..."

    # 既存セッションクリーンアップ
    tmux kill-session -t slack_polling 2>/dev/null

    # ログディレクトリ確認
    mkdir -p logs

    # tmuxで起動
    tmux new-session -d -s slack_polling         "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py 2>&1 | tee -a logs/slack_polling_worker.log"

    sleep 5

    if tmux has-session -t slack_polling 2>/dev/null; then
        echo "✅ 起動成功"

        # 起動確認
        if pgrep -f "slack_polling_worker" > /dev/null; then
            PID=$(pgrep -f "slack_polling_worker")
            echo "プロセスID: $PID"

            # 初期ログ
            echo ""
            echo "起動ログ:"
            tail -20 logs/slack_polling_worker.log
        fi
    else
        echo "❌ 起動失敗 - 手動で確認が必要"
        echo ""
        echo "手動起動方法:"
        echo "cd /home/aicompany/ai_co"
        echo "source venv/bin/activate"
        echo "python3 workers/slack_polling_worker.py"
    fi
else
    echo "✅ Workerは既に動作中"

    # ログに問題がないか確認
    if [ -f logs/slack_polling_worker.log ]; then
        echo ""
        echo "最新のエラー（もしあれば）:"
        tail -100 logs/slack_polling_worker.log | grep -i error | tail -5
    fi
fi

echo ""
echo "【次のステップ】"
echo "1. 新しいテストメッセージを送信:"
echo "   @pm-ai Hello World を出力するPythonコードを作成"
echo ""
echo "2. 20秒待ってから確認:"
echo "   tail -f logs/slack_polling_worker.log"
echo ""
echo "3. タスクキュー確認:"
echo "   sudo rabbitmqctl list_queues | grep ai_tasks"
