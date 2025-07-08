#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== AI Company システム診断 ==="
echo "時刻: $(date)"
echo ""

echo "1. Command Executorプロセス:"
ps aux | grep -E 'command_executor|CommandExecutor' | grep -v grep || echo "  ❌ Command Executorが起動していません"

echo ""
echo "2. ワーカープロセス:"
ps aux | grep -E 'worker.py|Worker' | grep -v grep | wc -l

echo ""
echo "3. Pendingコマンド:"
ls -la /home/aicompany/ai_co/ai_commands/pending/ | grep -E '\.(json|sh|py)$' | wc -l

echo ""
echo "4. 最新の実行ログ:"
ls -la /home/aicompany/ai_co/ai_commands/logs/ | tail -5

echo ""
echo "5. Slack設定確認:"
if [ -f /home/aicompany/ai_co/config/slack.conf ]; then
    grep -E 'webhook_url|channel' /home/aicompany/ai_co/config/slack.conf | head -2
    echo "  ✅ Slack設定ファイルあり"
else
    echo "  ❌ Slack設定ファイルなし"
fi

echo ""
echo "6. 環境変数:"
echo "  SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL:+設定済み}"
echo "  PYTHONPATH: $PYTHONPATH"

echo ""
echo "7. 実行済みファイル:"
ls -la /home/aicompany/ai_co/ai_commands/completed/*.json 2>/dev/null | tail -5 || echo "  実行済みファイルなし"