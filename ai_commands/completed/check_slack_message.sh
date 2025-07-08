#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== Slackメッセージ確認 ==="
echo "実行時刻: $(date)"
echo ""

# シンプルなAPIテストで最新メッセージ確認
echo "1. 最新のSlackメッセージ（過去5分）:"
echo "----------------------------------------"
python3 test_slack_api_simple.py

echo ""
echo "2. Slack Polling Workerの状態:"
echo "----------------------------------------"
ps aux | grep slack_polling_worker | grep -v grep || echo "❌ Slack Polling Workerが動作していません"

echo ""
echo "3. 最新のPolling Workerログ（存在する場合）:"
echo "----------------------------------------"
if [ -f logs/slack_polling_worker.log ]; then
    echo "最後の20行:"
    tail -20 logs/slack_polling_worker.log
else
    echo "ログファイルが存在しません"
fi

echo ""
echo "4. データベースの最新エントリ:"
echo "----------------------------------------"
if [ -f db/slack_messages.db ]; then
    sqlite3 db/slack_messages.db << 'SQL'
SELECT 'Total messages:', COUNT(*) FROM processed_messages;
SELECT '';
SELECT 'Latest 5 messages:';
SELECT datetime(processed_at, 'localtime') as time, 
       message_ts, 
       substr(text, 1, 80) as text_preview
FROM processed_messages
ORDER BY processed_at DESC
LIMIT 5;
SQL
else
    echo "データベースが存在しません"
fi

echo ""
echo "5. RabbitMQキューの状態:"
echo "----------------------------------------"
sudo rabbitmqctl list_queues name messages | grep -E "ai_tasks|ai_" | head -10 || echo "キュー情報取得失敗"

echo ""
echo "6. 診断ログの最新部分:"
echo "----------------------------------------"
if [ -f slack_diagnosis.log ]; then
    echo "最後の30行:"
    tail -30 slack_diagnosis.log
else
    echo "診断ログが存在しません - 診断ツールを実行してください"
fi
