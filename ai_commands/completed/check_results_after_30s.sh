#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "⏳ 30秒待機してから結果を確認します..."
sleep 30

echo ""
echo "=== 実行結果確認 ==="
echo "時刻: $(date)"
echo ""

echo "1. 実行済みコマンド（最新10件）:"
ls -lt ai_commands/completed/*.json 2>/dev/null | head -10

echo ""
echo "2. Slack通知テストの結果:"
if [ -f ai_commands/logs/test_slack_again_result.json ]; then
    cat ai_commands/logs/test_slack_again_result.json
    echo ""
    # ログの最後の部分を表示
    log_file=$(grep -o 'test_slack_again.*\.log' ai_commands/logs/test_slack_again_result.json | head -1)
    if [ -n "$log_file" ]; then
        echo "ログ内容:"
        tail -20 "ai_commands/logs/$log_file"
    fi
fi

echo ""
echo "3. ai-send拡張の実装結果:"
if [ -f config/task_types.json ]; then
    echo "✅ task_types.json が作成されました"
    echo "内容（最初の5行）:"
    head -5 config/task_types.json
    echo "..."
else
    echo "❌ task_types.json がまだありません"
fi

echo ""
echo "4. 最新のSlack関連ログ:"
grep -i "slack" ai_commands/logs/*.log 2>/dev/null | tail -10

echo ""
echo "5. Command Executorの状態:"
if ps aux | grep -E 'command_executor' | grep -v grep > /dev/null; then
    echo "✅ Command Executorは実行中です"
else
    echo "❌ Command Executorが停止しています"
fi