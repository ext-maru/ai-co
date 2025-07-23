#!/bin/bash

# Elder Tree Development Environment Setup Script

set -e

echo "🏛️ Elder Tree 開発環境セットアップ開始"
echo "=================================="

# プロジェクトルート
PROJECT_ROOT="/home/aicompany/elders_guild"
cd "$PROJECT_ROOT"

# Python仮想環境の作成
echo "📦 Python仮想環境を作成中..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo "✅ 仮想環境作成完了"
else
    echo "ℹ️  仮想環境は既に存在します"
fi

# 仮想環境の有効化
source venv/bin/activate

# pipのアップグレード
echo "📦 pipをアップグレード中..."
pip install --upgrade pip setuptools wheel

# 依存関係のインストール
echo "📦 依存関係をインストール中..."
pip install -r requirements.txt

# 開発用依存関係の追加インストール
echo "📦 開発ツールをインストール中..."
pip install ipython jupyter notebook

# PostgreSQLの確認
echo "🐘 PostgreSQLの状態を確認中..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQLがインストールされています"
    # Elder Tree用データベースの作成（存在しない場合）
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw elder_tree; then
        echo "ℹ️  elder_treeデータベースは既に存在します"
    else
        echo "📦 elder_treeデータベースを作成中..."
        sudo -u postgres createdb elder_tree
        echo "✅ データベース作成完了"
    fi
else
    echo "⚠️  PostgreSQLがインストールされていません"
    echo "   後でインストールすることをお勧めします: sudo apt install postgresql"
fi

# Redisの確認
echo "🔴 Redisの状態を確認中..."
if command -v redis-cli &> /dev/null; then
    echo "✅ Redisがインストールされています"
    if systemctl is-active --quiet redis; then
        echo "✅ Redisが実行中です"
    else
        echo "⚠️  Redisが停止しています"
        echo "   起動するには: sudo systemctl start redis"
    fi
else
    echo "⚠️  Redisがインストールされていません"
    echo "   後でインストールすることをお勧めします: sudo apt install redis-server"
fi

# 環境変数ファイルの作成
echo "🔧 環境変数ファイルを作成中..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Elder Tree Environment Variables
ELDER_TREE_ENV=development
ELDER_TREE_LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://aicompany:password@localhost/elder_tree
SQLITE_URL=sqlite+aiosqlite:///elder_tree.db

# Redis
REDIS_URL=redis://localhost:6379/0

# A2A Communication
A2A_BROKER_TYPE=local  # local, redis, grpc
A2A_TIMEOUT=30

# Monitoring
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30
EOF
    echo "✅ .envファイル作成完了"
else
    echo "ℹ️  .envファイルは既に存在します"
fi

# PYTHONPATHの設定
echo "🔧 PYTHONPATHを設定中..."
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 設定スクリプトの作成
cat > "$PROJECT_ROOT/scripts/activate_env.sh" << 'EOF'
#!/bin/bash
# Elder Tree環境有効化スクリプト

PROJECT_ROOT="/home/aicompany/elders_guild"
cd "$PROJECT_ROOT"
source venv/bin/activate
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
echo "🏛️ Elder Tree開発環境が有効化されました"
echo "   プロジェクトルート: $PROJECT_ROOT"
echo "   Python: $(which python)"
echo "   PYTHONPATH: $PYTHONPATH"
EOF

chmod +x "$PROJECT_ROOT/scripts/activate_env.sh"

# テスト実行
echo "🧪 インストールのテスト中..."
python -c "
import sys
print(f'Python: {sys.version}')

try:
    import asyncio
    import pydantic
    import sqlalchemy
    import redis
    import grpc
    print('✅ 主要ライブラリのインポート成功')
except ImportError as e:
    print(f'❌ インポートエラー: {e}')

# Elder Tree共有ライブラリのテスト
sys.path.insert(0, '/home/aicompany/elders_guild')
try:
    from shared_libs import BaseSoul, A2AMessage
    print('✅ Elder Tree共有ライブラリのインポート成功')
except ImportError as e:
    print(f'❌ Elder Tree共有ライブラリのインポートエラー: {e}')
"

echo ""
echo "=================================="
echo "🎉 セットアップ完了！"
echo ""
echo "開発環境を有効化するには:"
echo "  source /home/aicompany/elders_guild/scripts/activate_env.sh"
echo ""
echo "または:"
echo "  cd /home/aicompany/elders_guild"
echo "  source venv/bin/activate"
echo "=================================="