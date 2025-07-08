#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== 現在の状態（即時確認）==="
echo "時刻: $(date)"
echo ""

# 1. Worker状態
echo "【Slack Polling Worker】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    PID=$(pgrep -f "slack_polling_worker")
    echo "✅ 動作中 (PID: $PID)"
    
    # tmuxセッション
    if tmux has-session -t slack_polling 2>/dev/null; then
        echo "   tmuxセッション: あり"
    fi
    
    # 最新ログ（最後の10行）
    echo ""
    echo "最新ログ:"
    tail -10 logs/slack_polling_worker.log 2>/dev/null | grep -v "^$"
else
    echo "❌ 停止中"
fi

echo ""
echo "【最近のタスク処理】"
# タスク化の記録を探す
if [ -f logs/slack_polling_worker.log ]; then
    TASK_RECORDS=$(grep -c "タスク化" logs/slack_polling_worker.log 2>/dev/null || echo "0")
    echo "タスク化の記録数: $TASK_RECORDS"
    
    # 最新のタスク化記録
    if [ "$TASK_RECORDS" -gt 0 ]; then
        echo "最新のタスク化:"
        grep "タスク化" logs/slack_polling_worker.log | tail -3
    fi
fi

echo ""
echo "【診断ログの存在確認】"
ls -la ai_commands/logs/*slack*.log 2>/dev/null | tail -5 || echo "診断ログなし"

echo ""
echo "【結論】"
if pgrep -f "slack_polling_worker" > /dev/null; then
    if [ -f logs/slack_polling_worker.log ] && [ $(stat -c%s logs/slack_polling_worker.log) -gt 0 ]; then
        # ログファイルのサイズが0より大きい
        LAST_MOD=$(stat -c %Y logs/slack_polling_worker.log)
        CURRENT=$(date +%s)
        DIFF=$((CURRENT - LAST_MOD))
        
        if [ $DIFF -lt 300 ]; then  # 5分以内に更新
            echo "✅ Workerは正常に動作している可能性が高い"
        else
            echo "⚠️  Workerは動作中だが活動していない可能性"
        fi
    else
        echo "⚠️  Workerは動作中だがログがない"
    fi
else
    echo "❌ Workerが動作していない - 起動が必要"
fi

echo ""
echo "手動確認コマンド:"
echo "  tmux attach -t slack_polling    # tmuxセッションに接続"
echo "  tail -f logs/slack_polling_worker.log    # ログ監視"
