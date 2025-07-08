#!/bin/bash
# 診断レポート生成（50秒後）
cd /home/aicompany/ai_co
source venv/bin/activate

sleep 50

echo "📋 診断レポート生成"
echo "=================="
python3 generate_diagnosis_report.py
