#!/bin/bash
cd /home/aicompany/ai_co
# バックグラウンドで30秒間ログを監視
timeout 30 python3 monitor_ai_logs.py > ai_monitor_output.log 2>&1
echo "ログ監視結果を ai_monitor_output.log に保存しました"