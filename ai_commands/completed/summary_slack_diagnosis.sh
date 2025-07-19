#!/bin/bash
# 全ての診断が完了するまで待つ（約2分）
echo "診断実行中... (約2分かかります)"
sleep 120

cd /home/aicompany/ai_co

echo "=== Slack PM-AI連携 診断結果まとめ ==="
echo "実行時刻: $(date)"
echo ""

# 1. 最終診断結果の確認
echo "【最終診断結果】"
if [ -f ai_commands/logs/final_slack_diagnosis*.log ]; then
    LATEST=$(ls -t ai_commands/logs/final_slack_diagnosis*.log | head -1)
    grep -A 20 "診断結果" "$LATEST" | head -30
else
    echo "最終診断ログが見つかりません"
fi

echo ""
echo "【実行されたコマンド一覧】"
ls -lt ai_commands/logs/*slack*.log | head -10

echo ""
echo "【現在のワーカー状態】"
ps aux | grep -E "(slack_polling_worker|task_worker|pm_worker)" | grep -v grep

echo ""
echo "【推奨される次のステップ】"
echo "1. Slackで新しいメッセージを送信: @pm-ai hello test"
echo "2. ログ監視: tail -f logs/slack_polling_worker.log"
echo "3. 結果確認: cat ai_monitor_output.log"
