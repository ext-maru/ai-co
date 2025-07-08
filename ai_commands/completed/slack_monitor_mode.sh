#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

echo "=== Slack継続監視モード ==="
echo "Slackで @pm-ai にメンションを送ってテストしてください"
echo "Ctrl+Cで停止"
echo ""

# 監視モード実行
python3 slack_diagnosis_tool.py --monitor
