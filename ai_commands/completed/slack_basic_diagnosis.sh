#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co

# 診断ツール実行
echo "Slack診断を実行中..."
python3 slack_diagnosis_tool.py

echo ""
echo "診断ログ:"
cat slack_diagnosis.log
