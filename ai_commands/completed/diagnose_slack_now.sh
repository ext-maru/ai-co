#!/bin/bash
# Slack PM-AI診断と自動修復実行
cd /home/aicompany/ai_co
source venv/bin/activate
python3 diagnose_and_fix_slack.py
