#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate

echo ""
echo "========================================="
echo "2. Slack API詳細テスト"
echo "========================================="
python3 slack_api_detailed_test.py
