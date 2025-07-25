#!/bin/bash
# nWo Daily Council 自動実行スクリプト
# 毎日 9:00 AM に実行

cd /home/aicompany/ai_co

# nWo Daily Council 実行
echo "🌌 nWo Daily Council 開始: $(date)" >> logs/nwo/daily_council.log
python3 libs/nwo_daily_council.py >> logs/nwo/daily_council.log 2>&1

# nWo Vision 更新
echo "🔮 nWo Vision 更新: $(date)" >> logs/nwo/daily_vision.log
python3 commands/ai_nwo_vision.py >> logs/nwo/daily_vision.log 2>&1

echo "✅ nWo自動化完了: $(date)" >> logs/nwo/automation.log
