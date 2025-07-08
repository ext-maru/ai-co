#!/bin/bash
# 診断結果表示（40秒後）
cd /home/aicompany/ai_co
source venv/bin/activate

echo "⏳ 診断完了待機中..."
sleep 40

echo ""
echo "📊 診断結果表示"
echo "=============="
python3 show_diagnosis_results.py
