#!/bin/bash
# Slack最新状態の簡易確認
cd /home/aicompany/ai_co

echo "📊 Slack PM-AI最新状態"
echo "====================="

# プロセス
echo -n "Slack Polling Worker: "
ps aux | grep slack_polling_worker.py | grep -v grep > /dev/null && echo "✅ 稼働中" || echo "❌ 停止"

# 最新ログ（最後の1行）
echo ""
echo "最新ログ:"
tail -1 logs/slack_polling_worker.log 2>/dev/null || echo "ログなし"

# キュー
echo ""
echo -n "ai_tasksキュー: "
sudo rabbitmqctl list_queues name messages 2>/dev/null | grep ai_tasks | awk '{print $2 " 件"}' || echo "確認失敗"

echo ""
echo "詳細は診断結果を確認してください"
