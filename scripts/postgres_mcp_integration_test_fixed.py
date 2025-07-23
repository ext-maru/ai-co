#!/usr/bin/env python3
"""
PostgreSQL MCP統合テストスイート (修正版)
既存のデータベースを使用して現行システムに影響を与えないテストを実施
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
    """PostgreSQL MCP統合テストクラス（既存DB使用版）"""

    def __init__(self):
        self.conn = None
        self.test_results = []
        self.fallback_results = []

    async def setup_test_environment(self):
        """テスト環境セットアップ（既存DB使用）"""
        print("🔧 テスト環境セットアップ開始...")

        # 既存のelders_knowledge DBに接続
        self.conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="elders_knowledge",
            user="elders_guild",
            password="elders_2025",
        )

        # テスト用テーブルを一時的に作成
        await self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_base.mcp_test_temp (
                id SERIAL PRIMARY KEY,
                content TEXT,
                embedding vector(1536),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """
        )

        # テスト用インデックス
        await self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_mcp_test_embedding
            ON knowledge_base.mcp_test_temp
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)
        """
        )

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

            # 既存のcore_documentsテーブル確認
            result = await self.conn.fetchval(
                """
                SELECT COUNT(*) FROM knowledge_base.core_documents
            """
            )

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f"接続OK、既存データ: {result}件",
                }
            )
            print(f"✅ {test_name} - 成功")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def test_existing_vector_search(self):
        """既存ベクトル検索テスト"""
        test_name = "既存ベクトル検索テスト"
        print(f"\n🔍 {test_name}...")

        try:
            # 既存データを使った検索テスト
            query = "4賢者について教えてください"
            response = client.embeddings.create(
                model="text-embedding-ada-002", input=query
            )
            query_embedding = response.data[0].embedding

            start_time = time.time()
            results = await self.conn.fetch(
                """
                SELECT
                    section_title,
                    section_content,
                    1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base.core_documents
                ORDER BY embedding <=> $1::vector
                LIMIT 5
            """,
                str(query_embedding),
            )
            end_time = time.time()

            search_time = (end_time - start_time) * 1000  # ミリ秒

            assert len(results) > 0, "検索結果が空"
            assert search_time < 200, f"検索時間が遅い: {search_time}ms"

            best_similarity = results[0]["similarity"]
            assert best_similarity > 0.3, f"類似度が低い: {best_similarity}"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f"検索時間: {search_time:.2f}ms, 最高類似度: {best_similarity:.3f}",
                }
            )
            print(f"✅ {test_name} - 成功 (時間: {search_time:.2f}ms)")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def test_mcp_interface_simulation(self):
        """MCP インターフェース シミュレーション"""
        test_name = "MCP インターフェース シミュレーション"
        print(f"\n🔍 {test_name}...")

        try:
            # MCP風インターフェース作成
            class PostgreSQLMCPInterface:
                def __init__(self, conn):
                    self.conn = conn

                async def search_knowledge(
                    self, query: str, limit: int = 5
                ) -> List[Dict]:
                    """知識検索 (MCP風)"""
                    response = client.embeddings.create(
                        model="text-embedding-ada-002", input=query
                    )
                    query_embedding = response.data[0].embedding

                    results = await self.conn.fetch(
                        """
                        SELECT
                            section_title,
                            section_content,
                            section_type,
                            1 - (embedding <=> $1::vector) as similarity
                        FROM knowledge_base.core_documents
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                    """,
                        str(query_embedding),
                        limit,
                    )

                    return [
                        {
                            "title": r["section_title"],
                            "content": (
                                r["section_content"][:200] + "..."
                                if len(r["section_content"]) > 200
                                else r["section_content"]
                            ),
                            "type": r["section_type"],
                            "similarity": float(r["similarity"]),
                            "source": "postgres_mcp",
                        }
                        for r in results
                    ]

                async def search_with_context(
                    self, query: str, context: str = None
                ) -> List[Dict]:
                    """コンテキスト付き検索"""
                    enhanced_query = f"{context} {query}" if context else query
                    return await self.search_knowledge(enhanced_query)

                async def get_statistics(self) -> Dict:
                    """統計情報取得"""
                    stats = await self.conn.fetchrow(
                        """
                        SELECT
                            COUNT(*) as total_documents,
                            COUNT(DISTINCT section_type) as unique_types,
                            AVG(LENGTH(section_content)) as avg_content_length
                        FROM knowledge_base.core_documents
                    """
                    )

                    return {
                        "total_documents": stats["total_documents"],
                        "unique_types": stats["unique_types"],
                        "avg_content_length": float(stats["avg_content_length"]),
                    }

            # MCP インターフェーステスト
            mcp = PostgreSQLMCPInterface(self.conn)

            # 基本検索テスト
            search_results = await mcp.search_knowledge("エルダーズギルド", 3)
            assert len(search_results) > 0, "検索結果が空"

            # コンテキスト付き検索テスト
            context_results = await mcp.search_with_context("賢者", "エルダーズギルド")
            assert len(context_results) > 0, "コンテキスト検索失敗"

            # 統計情報テスト
            stats = await mcp.get_statistics()
            assert stats["total_documents"] > 0, "統計情報取得失敗"

            # 類似度確認
            best_match = search_results[0]
            assert (
                best_match["similarity"] > 0.1
            ), f"類似度不足: {best_match['similarity']}"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f'MCP統合OK - 文書数: {stats["total_documents"]}, 類似度: {best_match["similarity"]:.3f}',
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
            # ファイルベースフォールバック
            class FileBasedFallback:
                def __init__(self):
                    self.knowledge_db = {
                        "4賢者システム": {
                            "content": "ナレッジ賢者、タスク賢者、インシデント賢者、RAG賢者で構成される",
                            "similarity": 0.85,
                        },
                        "エルダーズギルド": {
                            "content": "4賢者システムを中心とした自律的な開発組織",
                            "similarity": 0.80,
                        },
                        "PostgreSQL": {
                            "content": "オープンソースのリレーショナルデータベース管理システム",
                            "similarity": 0.75,
                        },
                    }

                def search(self, query: str) -> List[Dict]:
                    results = []
                    for key, data in self.knowledge_db.items():
                        if any(word in key.lower() for word in query.lower().split()):
                            results.append(
                                {
                                    "title": key,
                                    "content": data["content"],
                                    "similarity": data["similarity"],
                                    "source": "file_fallback",
                                }
                            )
                    return sorted(results, key=lambda x: x["similarity"], reverse=True)

            # ハイブリッド検索システム
            class HybridSearchSystem:
                def __init__(self, mcp_conn, fallback_system):
                    self.mcp_conn = mcp_conn
                    self.fallback = fallback_system

                async def search(self, query: str, use_fallback=False) -> List[Dict]:
                    results = []

                    if not use_fallback:
                        try:
                            # まずPostgreSQLで検索
                            response = client.embeddings.create(
                                model="text-embedding-ada-002", input=query
                            )
                            query_embedding = response.data[0].embedding

                            postgres_results = await self.mcp_conn.fetch(
                                """
                                SELECT
                                    section_title,
                                    section_content,
                                    1 - (embedding <=> $1::vector) as similarity
                                FROM knowledge_base.core_documents
                                ORDER BY embedding <=> $1::vector
                                LIMIT 3
                            """,
                                str(query_embedding),
                            )

                            for r in postgres_results:
                                results.append(
                                    {
                                        "title": r["section_title"],
                                        "content": r["section_content"][:100] + "...",
                                        "similarity": float(r["similarity"]),
                                        "source": "postgres_mcp",
                                    }
                                )

                            # 結果が不十分な場合はフォールバック
                            if (
                                not results
                                or max(r["similarity"] for r in results) < 0.3
                            ):
                                fallback_results = self.fallback.search(query)
                                results.extend(fallback_results)

                        except Exception as e:
                            # PostgreSQL障害時はフォールバック
                            print(f"PostgreSQL障害検出: {e}")
                            results = self.fallback.search(query)
                    else:
                        # フォールバック強制実行
                        results = self.fallback.search(query)

                    return results

            # フォールバックテスト
            fallback_system = FileBasedFallback()
            hybrid_system = HybridSearchSystem(self.conn, fallback_system)

            # 正常検索テスト
            normal_results = await hybrid_system.search("4賢者について")
            assert len(normal_results) > 0, "正常検索失敗"

            # フォールバック強制テスト
            fallback_results = await hybrid_system.search(
                "4賢者について", use_fallback=True
            )
            assert len(fallback_results) > 0, "フォールバック失敗"
            assert any(
                r["source"] == "file_fallback" for r in fallback_results
            ), "フォールバック結果が含まれていない"

            self.fallback_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f"フォールバック正常動作 - 通常: {len(normal_results)}件, フォールバック: {len(fallback_results)}件",
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
            # 同時検索タスク
            async def search_task(query_id):
                query = f"エルダーズギルド {query_id}"
                response = client.embeddings.create(
                    model="text-embedding-ada-002", input=query
                )
                query_embedding = response.data[0].embedding

                results = await self.conn.fetch(
                    """
                    SELECT
                        section_title,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM knowledge_base.core_documents
                    ORDER BY embedding <=> $1::vector
                    LIMIT 1
                """,
                    str(query_embedding),
                )

                return len(results) > 0

            # 5個の同時検索テスト
            start_time = time.time()
            tasks = [search_task(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            total_time = (end_time - start_time) * 1000
            success_count = sum(results)

            assert success_count == 5, f"同時検索失敗: {success_count}/5"
            assert total_time < 10000, f"同時検索時間過大: {total_time}ms"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f"同時検索成功: {success_count}/5, 時間: {total_time:.2f}ms",
                }
            )
            print(f"✅ {test_name} - 成功")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def test_data_integrity(self):
        """データ整合性テスト"""
        test_name = "データ整合性テスト"
        print(f"\n🔍 {test_name}...")

        try:
            # 既存データの整合性確認
            integrity_check = await self.conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_count,
                    COUNT(embedding) as embedding_count,
                    COUNT(DISTINCT section_type) as type_count
                FROM knowledge_base.core_documents
            """
            )

            assert integrity_check["total_count"] > 0, "データが存在しない"
            assert (
                integrity_check["embedding_count"] == integrity_check["total_count"]
            ), "embeddings欠損"
            assert integrity_check["type_count"] > 0, "カテゴリが存在しない"

            # データ品質確認
            quality_check = await self.conn.fetchrow(
                """
                SELECT
                    AVG(LENGTH(section_content)) as avg_length,
                    MIN(LENGTH(section_content)) as min_length,
                    MAX(LENGTH(section_content)) as max_length
                FROM knowledge_base.core_documents
            """
            )

            assert quality_check["avg_length"] > 10, "コンテンツが短すぎる"
            assert quality_check["min_length"] > 0, "空のコンテンツが存在"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f'データ整合性OK - 総件数: {
                        integrity_check["total_count"]},
                        平均長: {quality_check["avg_length"]:.0f
                    }',
                }
            )
            print(f"✅ {test_name} - 成功")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def test_performance_benchmark(self):
        """パフォーマンス ベンチマーク"""
        test_name = "パフォーマンス ベンチマーク"
        print(f"\n🔍 {test_name}...")

        try:
            # 複数の検索パターンをテスト
            queries = [
                "4賢者について",
                "エルダーズギルド",
                "TDD開発",
                "PostgreSQL",
                "ナレッジ賢者",
            ]

            total_time = 0
            all_results = []

            for query in queries:
                response = client.embeddings.create(
                    model="text-embedding-ada-002", input=query
                )
                query_embedding = response.data[0].embedding

                start_time = time.time()
                results = await self.conn.fetch(
                    """
                    SELECT
                        section_title,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM knowledge_base.core_documents
                    ORDER BY embedding <=> $1::vector
                    LIMIT 5
                """,
                    str(query_embedding),
                )
                end_time = time.time()

                search_time = (end_time - start_time) * 1000
                total_time += search_time
                all_results.extend(results)

            avg_time = total_time / len(queries)
            avg_similarity = sum(float(r["similarity"]) for r in all_results) / len(
                all_results
            )

            assert avg_time < 100, f"平均検索時間が遅い: {avg_time}ms"
            assert avg_similarity > 0.1, f"平均類似度が低い: {avg_similarity}"

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "message": f"平均検索時間: {avg_time:.2f}ms, 平均類似度: {avg_similarity:.3f}",
                }
            )
            print(f"✅ {test_name} - 成功")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAIL", "message": str(e)}
            )
            print(f"❌ {test_name} - 失敗: {e}")

    async def cleanup_test_environment(self):
        """テスト環境クリーンアップ"""
        print("\n🧹 テスト環境クリーンアップ...")

        if self.conn:
            # テスト用一時テーブル削除
            await self.conn.execute("DROP TABLE IF EXISTS knowledge_base.mcp_test_temp")
            await self.conn.close()

        print("✅ テスト環境クリーンアップ完了")

    def generate_test_report(self):
        """テストレポート生成"""
        print("\n" + "=" * 80)
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

        if total_tests > 0:
            print(f"成功率: {passed_tests/total_tests*100:.1f}%")

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
            print("  🎉 すべてのテストが成功しました。")
            print("  ✅ PostgreSQL MCP統合を安全に進められます。")
            print("  🔧 段階的な導入スケジュールを作成しましょう。")
        else:
            print("  ⚠️ 一部のテストが失敗しました。")
            print("  🔧 問題を修正してから統合を進めてください。")

        print("  📊 継続的な監視体制の構築が重要です。")
        print("  🔄 フォールバック機構の保持を推奨します。")
        print("  🚀 本番環境での段階的ロールアウトを実施してください。")

        return failed_tests == 0


async def main():
    """メイン実行関数"""
    print("🚀 PostgreSQL MCP統合テストスイート開始")
    print("=" * 80)

    tester = PostgreSQLMCPIntegrationTest()

    try:
        # テスト実行
        await tester.setup_test_environment()
        await tester.test_basic_connectivity()
        await tester.test_existing_vector_search()
        await tester.test_mcp_interface_simulation()
        await tester.test_fallback_mechanism()
        await tester.test_concurrent_access()
        await tester.test_data_integrity()
        await tester.test_performance_benchmark()

        # レポート生成
        success = tester.generate_test_report()

        if success:
            print("\n🎉 すべてのテストが成功しました！")
            print("PostgreSQL MCP統合の準備が整いました。")
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
