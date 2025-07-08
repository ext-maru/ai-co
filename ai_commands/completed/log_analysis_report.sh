#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo ""
echo "========================================="
echo "4. ログ分析レポート"
echo "========================================="

echo "最新のAI Command Executorログ:"
echo "--------------------------------"
ls -lt ai_commands/logs/*.log | head -5

echo ""
echo "Slackメッセージ関連のログ抽出:"
echo "--------------------------------"
grep -i "slack" logs/task_worker.log | tail -10 || echo "Slack関連ログなし"

echo ""
echo "エラーログ抽出:"
echo "--------------------------------"
grep -i "error" logs/*.log | tail -10 || echo "エラーなし"

echo ""
echo "メンション処理確認:"
echo "--------------------------------"
grep -E "(mention|<@U)" logs/slack_polling_worker.log | tail -10 || echo "メンション処理ログなし"
