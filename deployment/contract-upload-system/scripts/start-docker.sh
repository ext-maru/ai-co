#!/bin/bash
# Elder Flow準拠 - Docker起動スクリプト

set -e

echo "🌊 Elder Flow準拠 契約書アップロードシステム起動開始..."

# Docker権限チェック
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker権限エラー - sgコマンドを使用します"
    DOCKER_CMD="sg docker -c"
else
    echo "✅ Docker権限確認済み"
    DOCKER_CMD=""
fi

# 現在のコンテナを停止・削除
echo "🛑 既存コンテナの停止・削除..."
$DOCKER_CMD "docker-compose down --remove-orphans" || true

# イメージのビルド
echo "🔨 Elder Flow準拠イメージビルド中..."
$DOCKER_CMD "docker-compose build --no-cache"

# サービス起動
echo "🚀 Elder Flow準拠サービス起動中..."
$DOCKER_CMD "docker-compose up -d"

# ヘルスチェック待機
echo "🏥 ヘルスチェック待機中..."
sleep 30

# サービス状態確認
echo "📊 サービス状態確認..."
$DOCKER_CMD "docker-compose ps"

# バックエンドヘルスチェック
echo "🔍 バックエンドヘルスチェック..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ バックエンド正常稼働中"
else
    echo "❌ バックエンドヘルスチェック失敗"
    exit 1
fi

# 監視エンドポイント確認
echo "📈 監視エンドポイント確認..."
if curl -f http://localhost:8000/monitoring/readiness >/dev/null 2>&1; then
    echo "✅ 監視システム正常稼働中"
else
    echo "⚠️ 監視システム確認できませんが継続"
fi

echo ""
echo "🎉 Elder Flow準拠システム起動完了！"
echo ""
echo "📍 利用可能なエンドポイント:"
echo "  🌐 バックエンドAPI: http://localhost:8000"
echo "  🖥️ フロントエンド: http://localhost:3000"
echo "  🗄️ PostgreSQL: localhost:5432"
echo "  📊 Prometheus監視: http://localhost:9090"
echo ""
echo "🔍 ヘルスチェック:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/monitoring/readiness"
echo "  curl http://localhost:8000/monitoring/metrics"
echo ""
echo "📋 ログ確認:"
echo "  $DOCKER_CMD \"docker-compose logs -f backend\""
echo "  $DOCKER_CMD \"docker-compose logs -f frontend\""
echo ""
echo "🛑 停止方法:"
echo "  $DOCKER_CMD \"docker-compose down\""
