#!/bin/bash
# pgvector インストールスクリプト（ソースからビルド）
# CorePostgres計画 - ベクトル検索基盤

set -e

echo "🔧 pgvector インストール開始"
echo "================================"

# 作業ディレクトリ
WORK_DIR="/tmp/pgvector_install"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 1. 必要なパッケージの確認
echo "📦 必要なパッケージ確認中..."
if ! command -v make &> /dev/null; then
    echo "❌ makeがインストールされていません"
    echo "   sudo apt install make gcc を実行してください"
    exit 1
fi

if ! command -v gcc &> /dev/null; then
    echo "❌ gccがインストールされていません"
    echo "   sudo apt install gcc を実行してください"
    exit 1
fi

# PostgreSQL開発ヘッダーの確認
if [ ! -d "/usr/include/postgresql/16/server" ]; then
    echo "❌ PostgreSQL 16 開発ヘッダーがありません"
    echo "   sudo apt install postgresql-server-dev-16 を実行してください"
    exit 1
fi

# 2. pgvectorのダウンロード
echo "📥 pgvector ダウンロード中..."
if [ -d "pgvector" ]; then
    rm -rf pgvector
fi

git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
cd pgvector

# 3. ビルド
echo "🔨 pgvector ビルド中..."
make

# 4. インストール準備
echo "📋 インストール準備..."
echo ""
echo "⚠️  次のコマンドをsudo権限で実行してください:"
echo ""
echo "cd $WORK_DIR/pgvector"
echo "sudo make install"
echo ""
echo "✅ インストール後、PostgreSQLで以下を実行:"
echo ""
echo "PGPASSWORD=elders_2025 psql -h localhost -U elders_guild -d elders_knowledge"
echo "CREATE EXTENSION vector;"
echo ""
echo "🎯 pgvectorのビルドが完了しました！"
