#!/usr/bin/env python3
"""
PostgreSQL MCP統合実装
テストが成功したので実際のMCP統合を実装する
"""

import os
import sys
import asyncio
import asyncpg
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

class MCPMessageType(Enum):
    """MCP メッセージタイプ"""
    SEARCH = "search"
    STORE = "store"
    UPDATE = "update"
    DELETE = "delete"
    STATS = "stats"
    HEALTH = "health"

@dataclass
class MCPRequest:
    """MCP リクエスト"""
    message_type: MCPMessageType
    query: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict] = None
    limit: Optional[int] = 10
    filters: Optional[Dict] = None

@dataclass
class MCPResponse:
    """MCP レスポンス"""
    success: bool
    message: str
    data: Optional[Any] = None
    metadata: Optional[Dict] = None
    timestamp: Optional[str] = None

class PostgreSQLMCPServer:
    """PostgreSQL MCP サーバー"""

    def __init__(self,
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "elders_knowledge",
                 user: str = "elders_guild",
                 password: str = "elders_2025"):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.is_connected = False

    async def connect(self):
        """データベース接続"""
        try:
            self.conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.is_connected = True
            print(f"✅ PostgreSQL MCP サーバー接続成功: {self.database}")

        except Exception as e:
            self.is_connected = False
            print(f"❌ PostgreSQL MCP サーバー接続失敗: {e}")
            raise

    async def disconnect(self):
        """データベース切断"""
        if self.conn:
            await self.conn.close()
            self.is_connected = False
            print("✅ PostgreSQL MCP サーバー切断完了")

    async def health_check(self) -> MCPResponse:
        """ヘルスチェック"""
        try:
            if not self.is_connected:
                return MCPResponse(
                    success=False,
                    message="Database not connected",
                    timestamp=datetime.now().isoformat()
                )

            # 基本的な接続確認
            result = await self.conn.fetchval("SELECT 1")

            # データベース統計
            stats = await self.conn.fetchrow("""
                SELECT
                    COUNT(*) as total_documents,
                    COUNT(DISTINCT section_type) as unique_types,
                    pg_database_size(current_database()) as db_size
                FROM knowledge_base.core_documents
            """)

            return MCPResponse(
                success=True,
                message="Health check passed",
                data={
                    "connection": "OK",
                    "total_documents": stats['total_documents'],
                    "unique_types": stats['unique_types'],
                    "database_size": stats['db_size']
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return MCPResponse(
                success=False,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )

    async def search_knowledge(self, request: MCPRequest) -> MCPResponse:
        """知識検索"""
        try:
            if not self.is_connected:
                return MCPResponse(
                    success=False,
                    message="Database not connected",
                    timestamp=datetime.now().isoformat()
                )

            query = request.query
            limit = request.limit or 10
            filters = request.filters or {}

            # OpenAI embeddings が必要な場合のフォールバック
            if 'embedding' in filters and filters['embedding']:
                # embedding による検索
                embedding = filters['embedding']

                sql = """
                    SELECT
                        id,
                        section_title,
                        section_content,
                        section_type,
                        file_path,
                        tags,
                        1 - (embedding <=> $1) as similarity,
                        created_at
                    FROM knowledge_base.core_documents
                    ORDER BY embedding <=> $1
                    LIMIT $2
                """

                results = await self.conn.fetch(sql, embedding, limit)

            else:
                # 全文検索
                sql = """
                    SELECT
                        id,
                        section_title,
                        section_content,
                        section_type,
                        file_path,
                        tags,
                        ts_rank(search_vector, plainto_tsquery('english', $1)) as rank,
                        created_at
                    FROM knowledge_base.core_documents
                    WHERE search_vector @@ plainto_tsquery('english', $1)
                    ORDER BY rank DESC
                    LIMIT $2
                """

                results = await self.conn.fetch(sql, query, limit)

            # 結果を整形
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'id': row['id'],
                    'title': row['section_title'],
                    'content': row['section_content'],
                    'type': row['section_type'],
                    'file_path': row['file_path'],
                    'tags': row['tags'],
                    'similarity': float(row.get('similarity', 0.0)) if 'similarity' in row else None,
                    'rank': float(row.get('rank', 0.0)) if 'rank' in row else None,
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })

            return MCPResponse(
                success=True,
                message=f"Search completed, found {len(formatted_results)} results",
                data=formatted_results,
                metadata={
                    'query': query,
                    'limit': limit,
                    'search_type': 'vector' if 'embedding' in filters else 'fulltext'
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return MCPResponse(
                success=False,
                message=f"Search failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )

    async def store_knowledge(self, request: MCPRequest) -> MCPResponse:
        """知識保存"""
        try:
            if not self.is_connected:
                return MCPResponse(
                    success=False,
                    message="Database not connected",
                    timestamp=datetime.now().isoformat()
                )

            content = request.content
            metadata = request.metadata or {}

            # 必須フィールドの確認
            required_fields = ['section_title', 'section_content', 'section_type']
            for field in required_fields:
                if field not in metadata:
                    return MCPResponse(
                        success=False,
                        message=f"Missing required field: {field}",
                        timestamp=datetime.now().isoformat()
                    )

            # データベースに保存
            sql = """
                INSERT INTO knowledge_base.core_documents
                (file_path, section_title, section_content, section_type,
                 priority, tags, search_vector, metadata)
                VALUES ($1, $2, $3, $4, $5, $6,
                        to_tsvector('english', $2 || ' ' || $3), $7)
                RETURNING id
            """

            result = await self.conn.fetchval(
                sql,
                metadata.get('file_path', 'mcp_import'),
                metadata['section_title'],
                metadata['section_content'],
                metadata['section_type'],
                metadata.get('priority', 5),
                metadata.get('tags', []),
                json.dumps(metadata)
            )

            return MCPResponse(
                success=True,
                message=f"Knowledge stored successfully with ID: {result}",
                data={'id': result},
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return MCPResponse(
                success=False,
                message=f"Store failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )

    async def get_statistics(self, request: MCPRequest) -> MCPResponse:
        """統計情報取得"""
        try:
            if not self.is_connected:
                return MCPResponse(
                    success=False,
                    message="Database not connected",
                    timestamp=datetime.now().isoformat()
                )

            # 基本統計
            basic_stats = await self.conn.fetchrow("""
                SELECT
                    COUNT(*) as total_documents,
                    COUNT(DISTINCT section_type) as unique_types,
                    COUNT(DISTINCT file_path) as unique_files,
                    AVG(LENGTH(section_content)) as avg_content_length,
                    MIN(created_at) as oldest_document,
                    MAX(created_at) as newest_document
                FROM knowledge_base.core_documents
            """)

            # タイプ別統計
            type_stats = await self.conn.fetch("""
                SELECT
                    section_type,
                    COUNT(*) as count,
                    AVG(LENGTH(section_content)) as avg_length
                FROM knowledge_base.core_documents
                GROUP BY section_type
                ORDER BY count DESC
            """)

            # タグ統計
            tag_stats = await self.conn.fetch("""
                SELECT
                    unnest(tags) as tag,
                    COUNT(*) as count
                FROM knowledge_base.core_documents
                WHERE tags IS NOT NULL AND array_length(tags, 1) > 0
                GROUP BY tag
                ORDER BY count DESC
                LIMIT 10
            """)

            return MCPResponse(
                success=True,
                message="Statistics retrieved successfully",
                data={
                    'basic_stats': {
                        'total_documents': basic_stats['total_documents'],
                        'unique_types': basic_stats['unique_types'],
                        'unique_files': basic_stats['unique_files'],
                        'avg_content_length': float(basic_stats['avg_content_length'] or 0),
                        'oldest_document': basic_stats['oldest_document'].isoformat() if basic_stats['oldest_document'] else None,
                        'newest_document': basic_stats['newest_document'].isoformat() if basic_stats['newest_document'] else None
                    },
                    'type_stats': [
                        {
                            'type': row['section_type'],
                            'count': row['count'],
                            'avg_length': float(row['avg_length'] or 0)
                        }
                        for row in type_stats
                    ],
                    'tag_stats': [
                        {
                            'tag': row['tag'],
                            'count': row['count']
                        }
                        for row in tag_stats
                    ]
                },
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return MCPResponse(
                success=False,
                message=f"Statistics failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """リクエストハンドラー"""
        try:
            if request.message_type == MCPMessageType.HEALTH:
                return await self.health_check()

            elif request.message_type == MCPMessageType.SEARCH:
                return await self.search_knowledge(request)

            elif request.message_type == MCPMessageType.STORE:
                return await self.store_knowledge(request)

            elif request.message_type == MCPMessageType.STATS:
                return await self.get_statistics(request)

            else:
                return MCPResponse(
                    success=False,
                    message=f"Unsupported message type: {request.message_type}",
                    timestamp=datetime.now().isoformat()
                )

        except Exception as e:
            return MCPResponse(
                success=False,
                message=f"Request handling failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )

class PostgreSQLMCPClient:
    """PostgreSQL MCP クライアント"""

    def __init__(self, server: PostgreSQLMCPServer):
        self.server = server

    async def search(self, query: str, limit: int = 10, filters: Dict = None) -> MCPResponse:
        """検索"""
        request = MCPRequest(
            message_type=MCPMessageType.SEARCH,
            query=query,
            limit=limit,
            filters=filters or {}
        )
        return await self.server.handle_request(request)

    async def store(self, content: str, metadata: Dict) -> MCPResponse:
        """保存"""
        request = MCPRequest(
            message_type=MCPMessageType.STORE,
            content=content,
            metadata=metadata
        )
        return await self.server.handle_request(request)

    async def get_stats(self) -> MCPResponse:
        """統計情報取得"""
        request = MCPRequest(message_type=MCPMessageType.STATS)
        return await self.server.handle_request(request)

    async def health_check(self) -> MCPResponse:
        """ヘルスチェック"""
        request = MCPRequest(message_type=MCPMessageType.HEALTH)
        return await self.server.handle_request(request)

async def demo_mcp_integration():
    """MCP統合デモ"""
    print("🚀 PostgreSQL MCP統合デモ開始")
    print("=" * 60)

    # サーバー起動
    server = PostgreSQLMCPServer()
    await server.connect()

    # クライアント作成
    client = PostgreSQLMCPClient(server)

    try:
        # 1. ヘルスチェック
        print("\n1. ヘルスチェック...")
        health_response = await client.health_check()
        print(f"   結果: {health_response.message}")
        if health_response.success:
            print(f"   データ: {health_response.data}")

        # 2. 検索テスト
        print("\n2. 検索テスト...")
        search_response = await client.search("4賢者について", limit=3)
        print(f"   結果: {search_response.message}")
        if search_response.success:
            for i, result in enumerate(search_response.data[:2]):
                print(f"   #{i+1}: {result['title']}")

        # 3. 統計情報取得
        print("\n3. 統計情報取得...")
        stats_response = await client.get_stats()
        print(f"   結果: {stats_response.message}")
        if stats_response.success:
            basic = stats_response.data['basic_stats']
            print(f"   総文書数: {basic['total_documents']}")
            print(f"   文書タイプ数: {basic['unique_types']}")

        # 4. 新規データ保存テスト
        print("\n4. 新規データ保存テスト...")
        test_metadata = {
            'section_title': 'MCP統合テスト',
            'section_content': 'これはMCP統合のテストデータです。PostgreSQL MCPサーバーが正常に動作していることを確認するためのサンプルです。',
            'section_type': 'test',
            'file_path': 'mcp_test.md',
            'tags': ['MCP', 'テスト', 'PostgreSQL'],
            'priority': 3
        }

        store_response = await client.store("テストコンテンツ", test_metadata)
        print(f"   結果: {store_response.message}")
        if store_response.success:
            print(f"   新規ID: {store_response.data['id']}")

        # 5. 保存したデータの検索確認
        print("\n5. 保存データ検索確認...")
        verify_response = await client.search("MCP統合テスト", limit=1)
        print(f"   結果: {verify_response.message}")
        if verify_response.success and verify_response.data:
            result = verify_response.data[0]
            print(f"   見つかったタイトル: {result['title']}")

        print("\n🎉 PostgreSQL MCP統合デモ完了")

    except Exception as e:
        print(f"\n❌ デモ中にエラーが発生: {e}")

    finally:
        await server.disconnect()

async def create_mcp_integration_service():
    """MCP統合サービス作成"""
    print("🏗️ PostgreSQL MCP統合サービス作成...")

    service_code = '''#!/usr/bin/env python3
"""
PostgreSQL MCP統合サービス
systemdサービスとして起動可能
"""

import asyncio
import signal
import sys
from postgres_mcp_integration_implementation import PostgreSQLMCPServer

class MCPService:
    def __init__(self):
        self.server = None
        self.running = False

    async def start(self):
        """サービス開始"""
        print("🚀 PostgreSQL MCP Service starting...")

        self.server = PostgreSQLMCPServer()
        await self.server.connect()

        self.running = True
        print("✅ PostgreSQL MCP Service started")

        # サービスループ
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """サービス停止"""
        print("⏹️ PostgreSQL MCP Service stopping...")
        self.running = False

        if self.server:
            await self.server.disconnect()

        print("✅ PostgreSQL MCP Service stopped")

async def main():
    service = MCPService()

    # シグナルハンドラー
    def signal_handler(signum, frame):
        print(f"\\nReceived signal {signum}")
        asyncio.create_task(service.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await service.start()
    except KeyboardInterrupt:
        await service.stop()
    except Exception as e:
        print(f"❌ Service error: {e}")
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())
'''

    with open('/home/aicompany/ai_co/scripts/postgres_mcp_service.py', 'w') as f:
        f.write(service_code)

    print("✅ PostgreSQL MCP統合サービス作成完了")
    print("   起動方法: python3 scripts/postgres_mcp_service.py")

if __name__ == "__main__":
    # デモ実行
    asyncio.run(demo_mcp_integration())

    # サービス作成
    asyncio.run(create_mcp_integration_service())

    print("\n🎯 次のステップ:")
    print("1. MCP統合サービスのテスト実行")
    print("2. 4賢者システムとの連携")
    print("3. CLI/Webインターフェースとの統合")
    print("4. 本番環境での段階的導入")
