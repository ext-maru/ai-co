#!/usr/bin/env python3
"""
PostgreSQL MCP統合テストスイート
現行システムに影響を与えないよう徹底的にテストを実施
"""

import os
import sys
import asyncio
import asyncpg
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import unittest
from unittest.mock import Mock, patch

# OpenAI設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY が設定されていません")
    sys.exit(1)

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)


class PostgreSQLMCPIntegrationTest:
    """PostgreSQL MCP統合テストクラス"""

    def __init__(self):
        self.conn = None
        self.test_db = "elders_knowledge_test"
        self.test_results = []
        self.fallback_results = []

    async def setup_test_environment(self)print("🔧 テスト環境セットアップ開始...")
    """テスト環境セットアップ"""

        # 管理者権限でテストDB作成
        admin_conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="postgres",
        )

        try:
            # テストDB削除・作成
            await admin_conn.execute(f"DROP DATABASE IF EXISTS {self.test_db}")
            await admin_conn.execute(f"CREATE DATABASE {self.test_db}")

            # テストユーザー作成
            try:
                await admin_conn.execute(
                    """
                    CREATE USER elders_test_user WITH PASSWORD 'test_2025'
                """
                )
            except:
                pass  # ユーザーが既に存在する場合

            await admin_conn.execute(
                f"""
                GRANT ALL PRIVILEGES ON DATABASE {self.test_db} TO elders_test_user
            """
            )

        finally:
            await admin_conn.close()

        # テストDB接続
        self.conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database=self.test_db,
            user="elders_test_user",
            password="test_2025",
        )

        # pgvector拡張
        await self.conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # テストスキーマ作成
        await self.conn.execute("CREATE SCHEMA IF NOT EXISTS knowledge_base")
        await self.conn.execute("CREATE SCHEMA IF NOT EXISTS task_management")
        await self.conn.execute("CREATE SCHEMA IF NOT EXISTS incident_tracking")
        await self.conn.execute("CREATE SCHEMA IF NOT EXISTS search_analytics")

        print("✅ テスト環境セットアップ完了")

    async def test_basic_connectivity(self):
        """基本接続テスト"""
        test_name = "基本接続テスト"
        print(f"\n🔍 {test_name}...")

        try:
            # 接続確認
            result = await self.conn.fetchval("SELECT 1")
            assert result == 1, "基本接続失敗"

            # pgvector確認
            result = await self.conn.fetchval(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            )
            assert result == 1, "pgvector拡張が見つからない"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": "接続とpgvector拡張正常",
                }
            )
            print(f"✅ {test_name} - 成功")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def test_vector_search_performance(self):
        """ベクトル検索パフォーマンステスト"""
        test_name = "ベクトル検索パフォーマンステスト"
        print(f"\n🔍 {test_name}...")

        try:
            # テストテーブル作成
            await self.conn.execute(
                """
                CREATE TABLE knowledge_base.perf_test (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """
            )

            # インデックス作成
            await self.conn.execute(
                """
                CREATE INDEX idx_perf_embedding
                ON knowledge_base.perf_test
                USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)
            """
            )

            # テストデータ挿入
            test_data = [
                "エルダーズギルドの4賢者システムについて説明します",
                "ナレッジ賢者は知識管理を担当する重要な役割です",
                "タスク賢者はプロジェクト管理の専門家です",
                "インシデント賢者は緊急事態対応のスペシャリストです",
                "RAG賢者は情報検索と理解のエキスパートです",
            ]

            for content in test_data:
                response = client.embeddings.create(
                    model="text-embedding-ada-002", input=content
                )
                embedding = response.data[0].embedding

                await self.conn.execute(
                    """
                    INSERT INTO knowledge_base.perf_test (content, embedding)
                    VALUES ($1, $2::vector)
                """,
                    content,
                    str(embedding),
                )

            # 検索パフォーマンステスト
            query = "4賢者について教えてください"
            response = client.embeddings.create(
                model="text-embedding-ada-002", input=query
            )
            query_embedding = response.data[0].embedding

            start_time = time.time()
            results = await self.conn.fetch(
                """
                SELECT
                    content,
                    1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base.perf_test
                ORDER BY embedding <=> $1::vector
                LIMIT 3
            """,
                str(query_embedding),
            )
            end_time = time.time()

            search_time = (end_time - start_time) * 1000  # ミリ秒

            assert len(results) > 0, "検索結果が空"
            assert search_time < 100, f"検索時間が遅い: {search_time}ms"

            best_similarity = results[0]["similarity"]
            assert best_similarity > 0.5, f"類似度が低い: {best_similarity}"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f"検索時間: {search_time:0.2f}ms, 最高類似度: {best_similarity:0.3f}",
                }
            )
            print(f"✅ {test_name} - 成功 (時間: {search_time:0.2f}ms)")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def test_mcp_integration_simulation(self):
        """MCP統合シミュレーションテスト"""
        test_name = "MCP統合シミュレーションテスト"
        print(f"\n🔍 {test_name}...")

        try:
            # MCPインターフェース模擬
            class MockMCPInterface:
                def __init__(self, conn):
                    self.conn = conn

                async def search_knowledge(
                    self, query: str, limit: int = 5
                """MockMCPInterfaceクラス"""
                ) -> List[Dict]:
                    """知識検索"""
                    response = client.embeddings.create(
                        model="text-embedding-ada-002", input=query
                    )
                    query_embedding = response.data[0].embedding

                    results = await self.conn.fetch(
                        """
                        SELECT
                            content,
                            1 - (embedding <=> $1::vector) as similarity
                        FROM knowledge_base.perf_test
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                    """,
                        str(query_embedding),
                        limit,
                    )

                    return [
                        {
                            "content": r["content"],
                            "similarity": float(r["similarity"]),
                            "source": "postgres_mcp",
                        }
                        for r in results
                    ]

                async def store_knowledge(
                    self, content: str, metadata: Dict = None
                ) -> bool:
                    """知識保存"""
                    response = client.embeddings.create(
                        model="text-embedding-ada-002", input=content
                    )
                    embedding = response.data[0].embedding

                    await self.conn.execute(
                        """
                        INSERT INTO knowledge_base.perf_test (content, embedding)
                        VALUES ($1, $2::vector)
                    """,
                        content,
                        str(embedding),
                    )

                    return True

            # MCP統合テスト
            mcp = MockMCPInterface(self.conn)

            # 知識保存テスト
            test_content = "これはMCP統合テストのための新しい知識です"
            store_result = await mcp.store_knowledge(test_content)
            assert store_result, "知識保存失敗"

            # 検索テスト
            search_results = await mcp.search_knowledge("MCP統合テスト", 3)
            assert len(search_results) > 0, "検索結果が空"

            # 類似度確認
            best_match = search_results[0]
            assert (
                best_match["similarity"] > 0.7
            ), f"類似度不足: {best_match['similarity']}"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f'MCP統合正常 - 類似度: {best_match["similarity"]:0.3f}',
                }
            )
            print(f"✅ {test_name} - 成功")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def test_fallback_mechanism(self):
        """フォールバック機構テスト"""
        test_name = "フォールバック機構テスト"
        print(f"\n🔍 {test_name}...")

        try:
            # 既存ファイルベースシステムのシミュレート
            class FallbackKnowledgeSystem:
                def __init__(self):
                    self.knowledge_base = {
                        "4賢者": "ナレッジ賢者、タスク賢者、インシデント賢者、RAG賢者",
                        "エルダーズギルド": "4賢者システムを中心とした開発組織",
                """FallbackKnowledgeSystemクラス"""
                        "TDD": "テスト駆動開発",
                    }

                def search(self, query: str) -> List[Dict]:
                    results = []
                    for key, value in self.knowledge_base.items():
                        if key.lower() in query.lower():
                    """searchメソッド"""
                            results.append(
                                {
                                    "content": f"{key}: {value}",
                                    "similarity": 0.85,
                                    "source": "fallback_system",
                                }
                            )
                    return results

            # 統合検索システム
            class HybridSearchSystem:
                def __init__(self, mcp_conn, fallback_system):
                    self.mcp_conn = mcp_conn
                """HybridSearchSystemクラス"""
                    self.fallback = fallback_system

                async def search(self, query: str) -> List[Dict]:
                    results = []
                    """searchメソッド"""

                    # まずMCPで検索
                    try:
                        response = client.embeddings.create(
                            model="text-embedding-ada-002", input=query
                        )
                        query_embedding = response.data[0].embedding

                        mcp_results = await self.mcp_conn.fetch(
                            """
                            SELECT
                                content,
                                1 - (embedding <=> $1::vector) as similarity
                            FROM knowledge_base.perf_test
                            ORDER BY embedding <=> $1::vector
                            LIMIT 3
                        """,
                            str(query_embedding),
                        )

                        for r in mcp_results:
                            results.append(
                                {
                                    "content": r["content"],
                                    "similarity": float(r["similarity"]),
                                    "source": "mcp_postgres",
                                }
                            )

                        # 結果が不十分な場合はフォールバック
                        if not results or max(r["similarity"] for r in results) < 0.5:
                            fallback_results = self.fallback.search(query)
                            results.extend(fallback_results)

                    except Exception as e:
                        # MCP失敗時はフォールバックのみ
                        results = self.fallback.search(query)

                    return results

            # フォールバックテスト
            fallback_system = FallbackKnowledgeSystem()
            hybrid_system = HybridSearchSystem(self.conn, fallback_system)

            # 正常検索
            results = await hybrid_system.search("4賢者について")
            assert len(results) > 0, "検索結果が空"

            # MCP接続切断をシミュレート
            with patch.object(
                self.conn, "fetch", side_effect=Exception("Connection lost")
            ):
                fallback_results = await hybrid_system.search("4賢者について")
                assert len(fallback_results) > 0, "フォールバック失敗"
                assert any(
                    r["source"] == "fallback_system" for r in fallback_results
                ), "フォールバック結果が含まれていない"

            self.fallback_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": "フォールバック機構正常動作",
                }
            )
            print(f"✅ {test_name} - 成功")

        except Exception as e:
            self.fallback_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def test_concurrent_access(self):
        """同時アクセステスト"""
        test_name = "同時アクセステスト"
        print(f"\n🔍 {test_name}...")

        try:
            # 複数の同時検索をシミュレート
            async def search_task(query_id):
                """search_taskメソッド"""
                query = f"テストクエリ {query_id}"
                response = client.embeddings.create(
                    model="text-embedding-ada-002", input=query
                )
                query_embedding = response.data[0].embedding

                results = await self.conn.fetch(
                    """
                    SELECT
                        content,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM knowledge_base.perf_test
                    ORDER BY embedding <=> $1::vector
                    LIMIT 1
                """,
                    str(query_embedding),
                )

                return len(results) > 0

            # 10個の同時検索
            start_time = time.time()
            tasks = [search_task(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            total_time = (end_time - start_time) * 1000
            success_count = sum(results)

            assert success_count == 10, f"同時検索失敗: {success_count}/10"
            assert total_time < 5000, f"同時検索時間過大: {total_time}ms"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f"同時検索成功: {success_count}/10, 時間: {total_time:0.2f}ms",
                }
            )
            print(f"✅ {test_name} - 成功")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def test_memory_usage(self):
        """メモリ使用量テスト"""
        test_name = "メモリ使用量テスト"
        print(f"\n🔍 {test_name}...")

        try:
            import psutil

            # プロセス監視開始
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 大量データ処理シミュレート
            for i in range(100):
                content = f"大量データテスト {i} " * 100
                response = client.embeddings.create(
                    model="text-embedding-ada-002", input=content
                )
                embedding = response.data[0].embedding

                await self.conn.execute(
                    """
                    INSERT INTO knowledge_base.perf_test (content, embedding)
                    VALUES ($1, $2::vector)
                """,
                    content,
                    str(embedding),
                )

            # メモリ使用量確認
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            assert memory_increase < 500, f"メモリ使用量過大: {memory_increase}MB"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f"メモリ増加: {memory_increase:0.2f}MB",
                }
            )
            print(f"✅ {test_name} - 成功")

        except ImportError:
            self.test_results.append(
                {
                    "test": test_name,
                    "status": "SKIP",
                    "message": "psutilが利用できません",
                }
            )
            print(f"⚠️ {test_name} - スキップ")
        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def cleanup_test_environment(self)print("\n🧹 テスト環境クリーンアップ...")
    """テスト環境クリーンアップ"""

        if self.conn:
            await self.conn.close()

        # テストDB削除
        admin_conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="postgres",
        )

        try:
            await admin_conn.execute(f"DROP DATABASE IF EXISTS {self.test_db}")
            await admin_conn.execute("DROP USER IF EXISTS elders_test_user")
        finally:
            await admin_conn.close()

        print("✅ テスト環境クリーンアップ完了")

    def generate_test_report(self)print("\n" + "=" * 80)
    """テストレポート生成"""
        print("📊 PostgreSQL MCP統合テストレポート")
        print("=" * 80)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed_tests = sum(1 for r in self.test_results if r["status"] == "FAIL")
        skipped_tests = sum(1 for r in self.test_results if r["status"] == "SKIP")

        print(f"総テスト数: {total_tests}")
        print(f"成功: {passed_tests}")
        print(f"失敗: {failed_tests}")
        print(f"スキップ: {skipped_tests}")
        print(f"成功率: {passed_tests/total_tests*100:0.1f}%")

        print("\n🔍 テスト詳細:")
        for result in self.test_results:
            status_emoji = (
                "✅"
                if result["status"] == "PASS"
                else "❌" if result["status"] == "FAIL" else "⚠️"
            )
            print(f"  {status_emoji} {result['test']}: {result['message']}")

        # フォールバック結果
        if self.fallback_results:
            print("\n🔄 フォールバック機構テスト:")
            for result in self.fallback_results:
                status_emoji = "✅" if result["status"] == "PASS" else "❌"
                print(f"  {status_emoji} {result['test']}: {result['message']}")

        # 推奨事項
        print("\n📋 推奨事項:")
        if failed_tests == 0:
            print(
                "  🎉 すべてのテストが成功しました。PostgreSQL MCP統合を安全に進められます。"
            )
        else:
            print(
                "  ⚠️ 一部のテストが失敗しました。問題を修正してから統合を進めてください。"
            )

        print("  🔧 本番環境での段階的導入を推奨します。")
        print("  📊 継続的な監視とフォールバック機構の維持が重要です。")

        return failed_tests == 0


async def main()print("🚀 PostgreSQL MCP統合テストスイート開始")
"""メイン実行関数"""
    print("=" * 80)

    tester = PostgreSQLMCPIntegrationTest()

    try:
        # テスト実行
        await tester.setup_test_environment()
        await tester.test_basic_connectivity()
        await tester.test_vector_search_performance()
        await tester.test_mcp_integration_simulation()
        await tester.test_fallback_mechanism()
        await tester.test_concurrent_access()
        await tester.test_memory_usage()

        # レポート生成
        success = tester.generate_test_report()

        if success:
            print("\n🎉 すべてのテストが成功しました！")
            print("PostgreSQL MCP統合を安全に進められます。")
        else:
            print("\n⚠️ 一部のテストが失敗しました。")
            print("問題を修正してから統合を進めてください。")

        return success

    except Exception as e:
        print(f"\n❌ テスト実行中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await tester.cleanup_test_environment()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
