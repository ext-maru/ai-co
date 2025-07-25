#!/bin/bash
# PostgreSQL MCP インストールスクリプト
# エルダーズギルド CorePostgres計画 Phase 0

set -e

echo "🐘 PostgreSQL MCP インストール開始"
echo "=================================="

# 1. Node.jsの確認
echo "📦 Node.js確認中..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js: $NODE_VERSION"
else
    echo "❌ Node.jsがインストールされていません"
    echo "   以下のコマンドでインストールしてください:"
    echo "   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
    echo "   sudo apt-get install -y nodejs"
    exit 1
fi

# 2. npmの確認
echo "📦 npm確認中..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm: $NPM_VERSION"
else
    echo "❌ npmがインストールされていません"
    exit 1
fi

# 3. PostgreSQL接続情報の設定
echo ""
echo "🔧 PostgreSQL接続設定"
echo "===================="
echo "以下の形式で接続文字列を設定します:"
echo "postgresql://username:password@hostname:port/database"
echo ""

# デフォルト値の設定（ローカル開発用）
DEFAULT_USER="elders_guild"
DEFAULT_PASS="elders_2025"
DEFAULT_HOST="localhost"
DEFAULT_PORT="5432"
DEFAULT_DB="elders_knowledge"

read -p "PostgreSQL ユーザー名 [$DEFAULT_USER]: " PG_USER
PG_USER=${PG_USER:-$DEFAULT_USER}

read -s -p "PostgreSQL パスワード [$DEFAULT_PASS]: " PG_PASS
PG_PASS=${PG_PASS:-$DEFAULT_PASS}
echo ""

read -p "PostgreSQL ホスト [$DEFAULT_HOST]: " PG_HOST
PG_HOST=${PG_HOST:-$DEFAULT_HOST}

read -p "PostgreSQL ポート [$DEFAULT_PORT]: " PG_PORT
PG_PORT=${PG_PORT:-$DEFAULT_PORT}

read -p "データベース名 [$DEFAULT_DB]: " PG_DB
PG_DB=${PG_DB:-$DEFAULT_DB}

# 接続文字列の構築
POSTGRES_CONNECTION_STRING="postgresql://${PG_USER}:${PG_PASS}@${PG_HOST}:${PG_PORT}/${PG_DB}"

# 4. PostgreSQL MCPのインストール
echo ""
echo "📥 PostgreSQL MCP Server インストール中..."
npm install -g @modelcontextprotocol/server-postgres

# 5. 設定ファイルの作成
echo ""
echo "📝 設定ファイル作成中..."
MCP_CONFIG_DIR="$HOME/.config/mcp"
mkdir -p "$MCP_CONFIG_DIR"

cat > "$MCP_CONFIG_DIR/postgres_config.json" << EOF
{
  "mcpServers": {
    "postgresql": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "${POSTGRES_CONNECTION_STRING}"
      }
    }
  }
}
EOF

# 6. 環境変数の設定
echo ""
echo "🔧 環境変数設定中..."
echo "export POSTGRES_CONNECTION_STRING='${POSTGRES_CONNECTION_STRING}'" >> ~/.bashrc

# 7. テスト接続スクリプトの作成
cat > test_postgres_mcp.js << 'EOF'
// PostgreSQL MCP テスト接続
const { spawn } = require('child_process');

console.log('🧪 PostgreSQL MCP接続テスト開始...');

const mcp = spawn('npx', [
  '-y',
  '@modelcontextprotocol/server-postgres'
], {
  env: {
    ...process.env,
    POSTGRES_CONNECTION_STRING: process.env.POSTGRES_CONNECTION_STRING
  }
});

mcp.stdout.on('data', (data) => {
  console.log(`✅ MCP出力: ${data}`);
});

mcp.stderr.on('data', (data) => {
  console.error(`❌ MCPエラー: ${data}`);
});

mcp.on('close', (code) => {
  console.log(`MCPプロセス終了 (コード: ${code})`);
});

// 5秒後に終了
setTimeout(() => {
  mcp.kill();
  console.log('テスト完了');
}, 5000);
EOF

echo ""
echo "✅ インストール完了！"
echo ""
echo "📋 次のステップ:"
echo "1. 新しいターミナルを開くか、以下を実行:"
echo "   source ~/.bashrc"
echo ""
echo "2. PostgreSQL MCPの接続テスト:"
echo "   node test_postgres_mcp.js"
echo ""
echo "3. 直接実行テスト:"
echo "   npx -y @modelcontextprotocol/server-postgres"
echo ""
echo "🔐 接続情報:"
echo "   ホスト: $PG_HOST:$PG_PORT"
echo "   データベース: $PG_DB"
echo "   ユーザー: $PG_USER"
echo ""
echo "🐘 PostgreSQL MCP インストール完了！"
