#!/bin/bash
# PostgreSQLとpgvectorをインストールするスクリプト

echo "🚀 PostgreSQLインストールスクリプト"
echo "================================"

# 現在のユーザー確認
echo "現在のユーザー: $(whoami)"

# sudoが使えるかチェック
if ! command -v sudo &> /dev/null; then
    echo "❌ sudoコマンドが見つかりません"
    echo "管理者に以下のコマンドを実行してもらってください:"
    echo ""
    echo "# PostgreSQLのインストール"
    echo "apt-get update"
    echo "apt-get install -y postgresql postgresql-contrib"
    echo ""
    echo "# pgvectorのインストール"
    echo "apt-get install -y postgresql-14-pgvector"
    echo ""
    echo "# PostgreSQLサービスの起動"
    echo "systemctl start postgresql"
    echo "systemctl enable postgresql"
    echo ""
    echo "# データベースとユーザーの作成"
    echo "sudo -u postgres psql << EOF"
    echo "CREATE DATABASE ai_company;"
    echo "CREATE DATABASE ai_company_grimoire;"
    echo "CREATE USER ai_company_user WITH PASSWORD 'ai_company_pass';"
    echo "GRANT ALL PRIVILEGES ON DATABASE ai_company TO ai_company_user;"
    echo "GRANT ALL PRIVILEGES ON DATABASE ai_company_grimoire TO ai_company_user;"
    echo "\\c ai_company_grimoire"
    echo "CREATE EXTENSION IF NOT EXISTS vector;"
    echo "EOF"
    exit 1
fi

# PostgreSQLがインストール済みかチェック
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQLは既にインストールされています"
    psql --version
else
    echo "📦 PostgreSQLをインストールします..."
    echo "sudo権限が必要です。パスワードを入力してください:"

    # PostgreSQLのインストール
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib

    # pgvectorのインストール
    sudo apt-get install -y postgresql-14-pgvector || sudo apt-get install -y postgresql-15-pgvector || sudo apt-get install -y postgresql-16-pgvector
fi

# PostgreSQLサービスの状態確認
echo ""
echo "🔍 PostgreSQLサービスの状態確認..."
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQLサービスは稼働中です"
else
    echo "🚀 PostgreSQLサービスを起動します..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# データベースの作成
echo ""
echo "🗄️ データベースを作成します..."
echo "PostgreSQLのpostgresユーザーで実行します"

sudo -u postgres psql << EOF
-- AI Companyデータベースの作成
CREATE DATABASE ai_company;
CREATE DATABASE ai_company_grimoire;

-- ユーザーの作成（既に存在する場合はスキップ）
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'ai_company_user') THEN
        CREATE USER ai_company_user WITH PASSWORD 'ai_company_pass';
    END IF;
END\$\$;

-- 権限の付与
GRANT ALL PRIVILEGES ON DATABASE ai_company TO ai_company_user;
GRANT ALL PRIVILEGES ON DATABASE ai_company_grimoire TO ai_company_user;

-- pgvector拡張の有効化
\c ai_company_grimoire
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 接続テスト用
\c ai_company
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOF

echo ""
echo "✨ PostgreSQLのセットアップが完了しました！"
echo ""
echo "📊 接続情報:"
echo "  - ホスト: localhost"
echo "  - ポート: 5432"
echo "  - データベース: ai_company, ai_company_grimoire"
echo "  - ユーザー: ai_company_user"
echo "  - パスワード: ai_company_pass"
echo ""
echo "🔧 環境変数はすでに.envファイルに設定されています:"
echo "  - DATABASE_URL"
echo "  - GRIMOIRE_DATABASE_URL"
