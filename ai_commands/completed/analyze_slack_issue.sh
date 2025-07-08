#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "問題の切り分け:"
echo ""

# Polling Workerが動作しているか
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "✅ Slack Polling Workerは動作中"
    
    # ログに最新のアクティビティがあるか
    if [ -f logs/slack_polling_worker.log ]; then
        LAST_LOG_TIME=$(tail -1 logs/slack_polling_worker.log | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}' | head -1)
        if [ -n "$LAST_LOG_TIME" ]; then
            echo "  最終ログ時刻: $LAST_LOG_TIME"
        fi
    fi
else
    echo "❌ Slack Polling Workerが動作していません"
    echo ""
    echo "起動方法:"
    echo "  tmux new -s slack_polling"
    echo "  cd /home/aicompany/ai_co && source venv/bin/activate"
    echo "  python3 workers/slack_polling_worker.py"
fi

echo ""
echo "診断推奨:"
echo "1. リアルタイム監視モードで確認:"
echo "   python3 slack_diagnosis_tool.py --monitor"
echo ""
echo "2. Polling Workerを手動で起動してエラー確認:"
echo "   cd /home/aicompany/ai_co && source venv/bin/activate"
echo "   python3 workers/slack_polling_worker.py"
