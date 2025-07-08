#!/bin/bash
# 毎日深夜2時に自動要約を実行

CRON_CMD="0 2 * * * cd /home/aicompany/ai_co && /home/aicompany/ai_co/venv/bin/python /home/aicompany/ai_co/scripts/auto_summarize.py >> /home/aicompany/ai_co/logs/auto_summarize.log 2>&1"

# 既存のcronジョブを確認
if ! crontab -l 2>/dev/null | grep -q "auto_summarize.py"; then
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ cronジョブ追加完了"
else
    echo "⚠️ cronジョブは既に存在します"
fi

crontab -l | grep auto_summarize
