#!/bin/bash
# ワーカーの安定性を改善するスクリプト

echo "🔧 ワーカーの安定性改善を開始..."

# 1. RabbitMQの設定を確認
echo "1. RabbitMQ接続設定を確認..."
sudo rabbitmqctl eval 'application:get_env(rabbit, heartbeat).'

# 2. ハートビート設定を追加（60秒に設定）
echo "2. ハートビート設定を更新..."
sudo rabbitmqctl eval 'application:set_env(rabbit, heartbeat, 60).'

# 3. RabbitMQを再起動
echo "3. RabbitMQを再起動..."
sudo systemctl restart rabbitmq-server
sleep 5

# 4. 古いキューをクリア
echo "4. キューの状態を確認..."
sudo rabbitmqctl list_queues name messages consumers

# 5. AI Companyを再起動
echo "5. AI Companyを再起動..."
cd /root/ai_co
pkill -f "python3.*worker" || true
sleep 2
bash utils/scripts/start_company.sh

echo "✅ 安定性改善完了！"
echo ""
echo "📊 推奨事項:"
echo "- 定期的な監視: python3 core/monitoring/monitor_workers.py"
echo "- ログ確認: tail -f logs/*.log | grep -E '(ERROR|Exception)'"
echo "- TaskWorkerの二重Slack通知を無効化することを検討"
