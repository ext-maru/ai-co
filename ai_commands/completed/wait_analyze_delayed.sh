#!/bin/bash
# ログ分析結果待機と問題特定（20秒後）
cd /home/aicompany/ai_co
source venv/bin/activate
python3 wait_and_analyze_logs.py
