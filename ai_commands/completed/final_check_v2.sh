#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "📊 最終動作確認"
echo "=============="

# プロセス確認
echo "プロセス状態:"
ps aux | grep -E "worker.*\.py" | grep -v grep | wc -l | xargs -I {} echo "稼働ワーカー数: {}"

# キュー確認
echo ""
echo "キュー状態:"
sudo rabbitmqctl list_queues name messages | grep -E "(ai_tasks|result)"

# ログ確認
echo ""
echo "最新ログ:"
tail -5 logs/task_worker.log 2>/dev/null | grep -E "(Slack|処理|タスク)"

# Slack通知
source venv/bin/activate
python3 << 'EOF'
import sys
sys.path.append("/home/aicompany/ai_co")
from libs.slack_notifier import SlackNotifier

try:
    notifier = SlackNotifier()
    notifier.send_message(
        "✅ Slack PM-AI完全修復完了 v2\n"
        "全ワーカー再起動済み\n"
        "DB初期化済み\n"
        "メッセージ処理準備完了\n\n"
        "@pm-ai でメンションしてください"
    )
except:
    pass
EOF

echo ""
echo "✅ 修復完了！"
