#!/bin/bash
# Elders Guild Project Web Portal - Docker Startup Script
# RAGエルダー推奨統合起動スクリプト

set -e

# スクリプトディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🎊 Elders Guild Project Web Portal - Docker起動"
echo "=" * 60

# プロジェクトルートに移動
cd "$PROJECT_ROOT"

# 環境変数ファイル確認
echo "📋 環境設定確認..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  .envファイルが見つかりません。.env.exampleをコピーしています..."
        cp .env.example .env
        echo "✅ .envファイルを作成しました"
        echo "🔧 必要に応じて.envファイルを編集してください（特にOPENAI_API_KEY）"
    else
        echo "❌ .env.exampleファイルが見つかりません"
        exit 1
    fi
else
    echo "✅ .envファイル確認完了"
fi

# Docker設定確認
echo "🐳 Docker設定確認..."

# Docker Composeファイル確認
required_files=(
    "docker-compose.yml"
    "Dockerfile.backend"
    "frontend/Dockerfile"
    "nginx/nginx.conf"
    "scripts/init_db.sql"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file が見つかりません"
        exit 1
    fi
done

# Dockerサービス確認
echo "🔧 Dockerサービス確認..."
if ! docker --version >/dev/null 2>&1; then
    echo "❌ Dockerがインストールされていません"
    exit 1
fi

if ! docker-compose --version >/dev/null 2>&1; then
    echo "❌ Docker Composeがインストールされていません"
    exit 1
fi

echo "✅ Docker環境確認完了"

# 既存のコンテナ停止（オプション）
echo "🛑 既存のコンテナ確認・停止..."
if docker-compose ps -q | grep -q .; then
    echo "📦 既存のコンテナを停止しています..."
    docker-compose down
    echo "✅ 停止完了"
else
    echo "✅ 稼働中のコンテナはありません"
fi

# ネットワーク・ボリューム準備
echo "🌐 Dockerネットワーク・ボリューム準備..."
docker-compose create

# データベース初期化（初回のみ）
echo "🗄️  データベース初期化準備..."
echo "   PostgreSQL + pgvector の準備を行います"

# サービス起動
echo "🚀 サービス起動開始..."

# 段階的起動でヘルスチェック
echo "1️⃣ データベースサービス起動（PostgreSQL + Redis）..."
docker-compose up -d postgres redis

echo "⏳ データベース起動待機..."
sleep 10

# データベース接続確認
echo "🔍 データベース接続確認..."
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker-compose exec -T postgres pg_isready -U elder_admin -d elders_guild >/dev/null 2>&1; then
        echo "✅ PostgreSQL接続確認完了"
        break
    fi
    echo "⏳ PostgreSQL起動待機中... ($elapsed/$timeout秒)"
    sleep 5
    elapsed=$((elapsed + 5))
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ PostgreSQL起動タイムアウト"
    docker-compose logs postgres
    exit 1
fi

echo "2️⃣ バックエンドサービス起動（FastAPI）..."
docker-compose up -d backend

echo "⏳ バックエンド起動待機..."
sleep 15

# バックエンド接続確認
echo "🔍 バックエンド接続確認..."
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        echo "✅ FastAPIバックエンド接続確認完了"
        break
    fi
    echo "⏳ FastAPI起動待機中... ($elapsed/$timeout秒)"
    sleep 5
    elapsed=$((elapsed + 5))
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ FastAPI起動タイムアウト"
    docker-compose logs backend
    exit 1
fi

echo "3️⃣ フロントエンドサービス起動（Next.js）..."
docker-compose up -d frontend

echo "⏳ フロントエンド起動待機..."
sleep 20

# フロントエンド接続確認
echo "🔍 フロントエンド接続確認..."
timeout=90
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -f http://localhost:8002 >/dev/null 2>&1; then
        echo "✅ Next.jsフロントエンド接続確認完了"
        break
    fi
    echo "⏳ Next.js起動待機中... ($elapsed/$timeout秒)"
    sleep 5
    elapsed=$((elapsed + 5))
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ Next.js起動タイムアウト"
    docker-compose logs frontend
    exit 1
fi

echo "4️⃣ リバースプロキシ起動（Nginx）..."
docker-compose up -d nginx

echo "⏳ Nginx起動待機..."
sleep 5

# Nginx接続確認
echo "🔍 Nginx接続確認..."
if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ Nginx接続確認完了"
else
    echo "⚠️  Nginx接続確認に失敗（サービスは動作している可能性があります）"
fi

# 最終サービス状態確認
echo "📊 最終サービス状態確認..."
docker-compose ps

# 起動完了メッセージ
echo ""
echo "🎉 Elders Guild Project Web Portal 起動完了！"
echo "=" * 60
echo ""
echo "🌐 アクセスURL:"
echo "   メインアプリケーション: http://localhost:8080"
echo "   Next.js（直接）:     http://localhost:8002"
echo "   FastAPI（直接）:     http://localhost:8001"
echo "   API ドキュメント:     http://localhost:8001/docs"
echo ""
echo "🗄️  データベース:"
echo "   PostgreSQL:         localhost:8003"
echo "   Redis:              localhost:8004"
echo ""
echo "📋 有用なコマンド:"
echo "   ログ確認:            docker-compose logs -f [service]"
echo "   サービス停止:         docker-compose down"
echo "   サービス再起動:       docker-compose restart [service]"
echo "   データベース接続:     docker-compose exec postgres psql -U elder_admin -d elders_guild"
echo ""
echo "🔧 初期設定:"
echo "   1. http://localhost:8080 にアクセス"
echo "   2. プロジェクトスキャンを実行"
echo "   3. 自動資料生成をテスト"
echo ""
echo "✨ RAGエルダー推奨システムをお楽しみください！"
