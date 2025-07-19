#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo ""
echo "=== 詳細確認 ==="

# Polling Workerのデバッグ情報
if pgrep -f "slack_polling_worker" > /dev/null; then
    echo "1. Polling Worker内部状態:"

    # Workerが使用している設定を確認
    python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from core import get_config

config = get_config()
print(f"  Bot Token: {'設定あり' if config.get('slack.bot_token') else '設定なし'}")
print(f"  Channel ID: {config.get('slack.polling_channel_id', 'なし')}")
print(f"  ポーリング間隔: {config.get('slack.polling_interval', 20)}秒")
print(f"  メンション必須: {config.get('slack.require_mention', True)}")
EOF

    echo ""
    echo "2. 最近のエラー:"
    grep -i error logs/slack_polling_worker.log | tail -5 || echo "エラーなし"

else
    echo "Workerが動作していないため、手動起動します..."

    # tmuxで起動
    tmux new-session -d -s slack_polling         "cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/slack_polling_worker.py 2>&1 | tee -a logs/slack_polling_worker.log"

    sleep 5

    if tmux has-session -t slack_polling 2>/dev/null; then
        echo "✅ Slack Polling Worker起動成功"
        echo "起動後のログ:"
        tail -10 logs/slack_polling_worker.log
    fi
fi

echo ""
echo "3. タスク投入の確認:"
# タスクワーカーのログも確認
if [ -f logs/task_worker.log ]; then
    echo "TaskWorkerの最新ログ（Slack関連）:"
    grep -i slack logs/task_worker.log | tail -5 || echo "Slack関連のタスクなし"
fi
