#!/bin/bash
# 監視システム起動スクリプト

echo "🚀 AI-CO Prometheus + Grafana監視システムを起動します..."

# 設定ファイル存在チェック
if [ ! -f "config/prometheus.yml" ]; then
    echo "❌ Prometheus設定ファイルが見つかりません"
    exit 1
fi

# Docker Composeで起動
echo "📊 監視コンテナを起動中..."
docker-compose -f docker-compose.monitoring.yml up -d

# 起動待機
echo "⏳ サービスの起動を待機中..."
sleep 10

# 起動確認
echo "✅ サービス起動状態:"
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo "🎯 アクセスURL:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/eldersguild)"
echo "  - AlertManager: http://localhost:9093"
echo ""
echo "📊 次のステップ:"
echo "  1. Grafanaにログイン"
echo "  2. ダッシュボードを確認"
echo "  3. アラートルールを設定"
echo ""
echo "停止する場合: docker-compose -f docker-compose.monitoring.yml down"
