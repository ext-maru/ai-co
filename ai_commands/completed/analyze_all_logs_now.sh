#!/bin/bash
# 全ログ分析実行
cd /home/aicompany/ai_co
source venv/bin/activate

echo "📋 全ログ分析開始"
echo "=================="
echo ""

# 診断ログ分析
python3 analyze_all_logs.py

echo ""
echo ""

# ワーカーログ詳細
python3 check_worker_logs_detail.py

echo ""
echo "✅ ログ分析完了"
