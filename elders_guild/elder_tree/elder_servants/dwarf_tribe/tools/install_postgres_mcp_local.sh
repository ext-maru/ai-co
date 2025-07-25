#!/bin/bash
# PostgreSQL MCP ローカルインストールスクリプト（sudoなし）
# エルダーズギルド CorePostgres計画 Phase 0

set -e

echo "🐘 PostgreSQL MCP ローカルインストール開始"
echo "=========================================="

PROJECT_ROOT="/home/aicompany/ai_co"
MCP_DIR="$PROJECT_ROOT/mcp"

# プロジェクトディレクトリに移動
cd "$PROJECT_ROOT"

# 1. MCPディレクトリの作成
echo "📁 MCPディレクトリ作成中..."
mkdir -p "$MCP_DIR"
cd "$MCP_DIR"

# 2. package.jsonの作成
echo "📝 package.json作成中..."
cat > package.json << 'EOF'
{
  "name": "elders-guild-mcp",
  "version": "1.0.0",
  "description": "PostgreSQL MCP for Elders Guild Knowledge Base",
  "private": true,
  "dependencies": {
    "@modelcontextprotocol/server-postgres": "latest",
    "asyncpg": "latest"
  }
}
EOF

# 3. npmインストール（ローカル）
echo "📥 PostgreSQL MCP Server インストール中..."
npm install

# 4. 接続設定ファイルの作成
echo "🔧 接続設定ファイル作成中..."
cat > postgres_config.json << 'EOF'
{
  "connection": {
    "host": "localhost",
    "port": 5432,
    "database": "elders_knowledge",
    "user": "elders_guild",
    "password": "elders_2025"
  },
  "options": {
    "ssl": false,
    "pool_size": 10,
    "statement_timeout": 30000
  }
}
EOF

# 5. 実行スクリプトの作成
echo "📝 実行スクリプト作成中..."
cat > run_mcp.sh << 'EOF'
#!/bin/bash
# PostgreSQL MCP 実行スクリプト

PROJECT_ROOT="/home/aicompany/ai_co"
MCP_DIR="$PROJECT_ROOT/mcp"

export POSTGRES_CONNECTION_STRING="postgresql://elders_guild:elders_2025@localhost:5432/elders_knowledge"

cd "$MCP_DIR"
npx @modelcontextprotocol/server-postgres
EOF

chmod +x run_mcp.sh

# 6. Pythonラッパーの作成
echo "🐍 Pythonラッパー作成中..."
cat > "$PROJECT_ROOT/libs/postgres_mcp_client.py" << 'EOF'
"""
PostgreSQL MCP Client for Elders Guild
エルダーズギルド用PostgreSQL MCPクライアント
"""
import os
import json
import asyncio
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

class PostgresMCPClient:
    """PostgreSQL MCPクライアント"""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv(
            'POSTGRES_CONNECTION_STRING',
            'postgresql://elders_guild:elders_2025@localhost:5432/elders_knowledge'
        )
        self.mcp_dir = Path(__file__).parent.parent / 'mcp'

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """クエリを実行して結果を返す"""
        # MCPを通じてクエリを実行
        cmd = [
            'npx', '@modelcontextprotocol/server-postgres',
            '--query', query
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.mcp_dir),
            env={**os.environ, 'POSTGRES_CONNECTION_STRING': self.connection_string}
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"MCP Error: {stderr.decode()}")

        return json.loads(stdout.decode())

    async def list_schemas(self) -> List[str]:
        """スキーマ一覧を取得"""
        query = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schema_name;
        """
        results = await self.execute_query(query)
        return [row['schema_name'] for row in results]

    async def describe_table(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """テーブル構造を取得"""
        query = f"""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = '{schema}'
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;
        """
        return await self.execute_query(query)

# テスト用関数
async def test_connection():
    """接続テスト"""
    client = PostgresMCPClient()
    try:
        schemas = await client.list_schemas()
        print("✅ PostgreSQL MCP接続成功！")
        print(f"📋 利用可能なスキーマ: {schemas}")
    except Exception as e:
        print(f"❌ 接続エラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
EOF

# 7. セットアップ完了メッセージ
echo ""
echo "✅ PostgreSQL MCPローカルインストール完了！"
echo ""
echo "📋 インストール内容:"
echo "   • MCPディレクトリ: $MCP_DIR"
echo "   • 実行スクリプト: $MCP_DIR/run_mcp.sh"
echo "   • Pythonクライアント: $PROJECT_ROOT/libs/postgres_mcp_client.py"
echo ""
echo "🧪 接続テスト方法:"
echo "   cd $PROJECT_ROOT"
echo "   python3 libs/postgres_mcp_client.py"
echo ""
echo "🚀 MCP実行方法:"
echo "   cd $MCP_DIR"
echo "   ./run_mcp.sh"
echo ""
echo "🐘 PostgreSQL MCPセットアップ完了！"
