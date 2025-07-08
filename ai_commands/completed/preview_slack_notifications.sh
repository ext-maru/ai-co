#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo "=== Slack Notification Preview ==="
python3 scripts/preview_slack_notifications.py

echo -e "
=== Preview completed ==="
