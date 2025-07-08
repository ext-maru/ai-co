#!/bin/bash
# 修復結果確認（45秒後に実行）
sleep 45
cd /home/aicompany/ai_co
source venv/bin/activate
python3 check_repair_results.py
