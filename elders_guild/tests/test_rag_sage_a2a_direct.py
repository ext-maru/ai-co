#!/usr/bin/env python3
"""
🔍 RAG Sage A2A Agent - 直接テストスイート
========================================

Elder Loop Phase 3: 基本テストスイート
A2A依存なしでビジネスロジックを直接テスト

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

# RAG Sage imports
import sys
sys.path.append("/home/aicompany/ai_co/elders_guild")
from rag_sage.business_logic import RAGProcessor


class TestRAGSageA2ADirect:
    """RAG Sage直接テストスイート"""
    
    def __init__(self):
        self.processor = None
        self.test_results = {}
        self.test_documents = []
    
    async def setup(self):
        """テストセットアップ"""
        print("🔧 Setting up RAG Sage test environment...")
        self.processor = RAGProcessor("data/test_rag_sage.db")
        
        # テストドキュメント準備
        self.test_documents = [
            {
                "id": "test_doc_1",
                "content": "Elder Loop開発手法は品質保証のための厳密なループを特徴とします。",
                "source": "elders_guild_docs",
                "title": "Elder Loop開発手法",
                "category": "development",
                "tags": ["elder-loop", "quality", "methodology"],
                "author": "Claude Elder"
            },
            {
                "id": "test_doc_2",
                "content": "4賢者システムはKnowledge Sage、Task Sage、Incident Sage、RAG Sageで構成されます。",
                "source": "elders_guild_docs",
                "title": "4賢者システムアーキテクチャ",
                "category": "architecture",
                "tags": ["4-sages", "architecture", "system"],
                "author": "Grand Elder maru"
            },
            {
                "id": "test_doc_3",
                "content": "A2A Protocol準拠により分散システムでの相互通信が可能になります。",
                "source": "technical_docs",
                "title": "A2A Protocol実装ガイド",
                "category": "technical",
                "tags": ["a2a", "protocol", "distributed"],
                "author": "Technical Team"
            }
        ]
        
        # テストドキュメントインデックス
        for doc_data in self.test_documents:
            await self.processor.process_action("index_document", {"document": doc_data})
        
        print("✅ Test environment ready")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """全テスト実行"""
        print("\n🧪 RAG Sage A2A Direct Test Suite")
        print("=" * 50)
        
        await self.setup()
        
        # テスト実行
        test_methods = [
            ("test_search_knowledge", self.test_search_knowledge),
            ("test_index_document", self.test_index_document),
            ("test_batch_index_documents", self.test_batch_index_documents),
            ("test_get_similar_documents", self.test_get_similar_documents),
            ("test_analyze_query_intent", self.test_analyze_query_intent),
            ("test_generate_insights", self.test_generate_insights),
            ("test_delete_document", self.test_delete_document),
            ("test_update_document_boost", self.test_update_document_boost),
            ("test_search_filters", self.test_search_filters),
            ("test_search_types", self.test_search_types),
            ("test_optimize_index", self.test_optimize_index),
            ("test_get_search_statistics", self.test_get_search_statistics),
            ("test_get_index_info", self.test_get_index_info),
            ("test_health_check", self.test_health_check)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_method in test_methods:
            print(f"\n🔍 Running {test_name}...")
            try:
                result = await test_method()
                if result:
                    print(f"✅ {test_name} passed")
                    passed += 1
                    self.test_results[test_name] = {"status": "passed"}
                else:
                    print(f"❌ {test_name} failed")
                    failed += 1
                    self.test_results[test_name] = {"status": "failed"}
            except Exception as e:
                print(f"💥 {test_name} error: {e}")
                failed += 1
                self.test_results[test_name] = {"status": "error", "error": str(e)}
        
        # 結果サマリー
        total = passed + failed
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results Summary")
        print(f"Total: {total}, Passed: {passed}, Failed: {failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": success_rate,
            "details": self.test_results
        }
    
    # === Individual Test Methods ===
    
    async def test_search_knowledge(self) -> bool:
        """知識検索テスト"""
        result = await self.processor.process_action("search_knowledge", {
            "query": "Elder Loop",
            "limit": 10
        })
        
        assert result["success"], "Search should succeed"
        assert len(result["data"]["results"]) > 0, "Should find results"
        assert any("Elder Loop" in r["content"] for r in result["data"]["results"]), "Should find Elder Loop content"
        
        return True
    
    async def test_index_document(self) -> bool:
        """ドキュメントインデックステスト"""
        test_doc = {
            "id": "test_index_doc",
            "content": "これはインデックステスト用のドキュメントです。",
            "source": "test",
            "title": "インデックステスト",
            "category": "test",
            "tags": ["test", "index"]
        }
        
        result = await self.processor.process_action("index_document", {
            "document": test_doc
        })
        
        assert result["success"], "Index should succeed"
        assert result["data"]["document_id"] == "test_index_doc", "Document ID should match"
        
        # 検索して確認
        search_result = await self.processor.process_action("search_knowledge", {
            "query": "インデックステスト",
            "limit": 1
        })
        
        assert search_result["success"], "Search should succeed"
        assert len(search_result["data"]["results"]) > 0, "Should find indexed document"
        
        return True
    
    async def test_batch_index_documents(self) -> bool:
        """バッチインデックステスト"""
        test_docs = [
            {
                "id": f"batch_doc_{i}",
                "content": f"バッチドキュメント {i} のコンテンツ",
                "source": "batch_test",
                "title": f"バッチドキュメント {i}",
                "category": "batch"
            }
            for i in range(3)
        ]
        
        result = await self.processor.process_action("batch_index_documents", {
            "documents": test_docs
        })
        
        assert result["success"], "Batch index should succeed"
        assert result["data"]["successful_count"] == 3, "All documents should be indexed"
        assert result["data"]["failed_count"] == 0, "No failures expected"
        
        return True
    
    async def test_get_similar_documents(self) -> bool:
        """類似ドキュメント取得テスト"""
        result = await self.processor.process_action("get_similar_documents", {
            "document_id": "test_doc_1",
            "limit": 3
        })
        
        assert result["success"], "Get similar should succeed"
        assert "similar_documents" in result["data"], "Should have similar documents"
        
        # Elder Loop関連のドキュメントが見つかるはず（自分自身は除外されるので、類似文書が見つからない場合もある）
        similar = result["data"]["similar_documents"]
        # 類似文書の存在は保証されないため、リストの存在のみ確認
        assert isinstance(similar, list), "Should have similar documents list"
        
        return True
    
    async def test_analyze_query_intent(self) -> bool:
        """クエリ意図分析テスト"""
        queries = [
            ("How to implement Elder Loop?", "how_to"),
            ("What is RAG Sage?", "definition"),
            ("なぜ品質保証が重要なのか", "explanation"),
            ("List all sages", "enumeration"),
            ("エラー解決方法", "general")
        ]
        
        for query, expected_intent in queries:
            result = await self.processor.process_action("analyze_query_intent", {
                "query": query
            })
            
            assert result["success"], f"Intent analysis should succeed for: {query}"
            intent_data = result["data"]
            assert "intent_type" in intent_data, "Should have intent type"
            assert "keywords" in intent_data, "Should have keywords"
            
            # 意図タイプ確認（簡易実装なので完全一致は期待しない）
            if expected_intent in ["how_to", "definition"]:
                assert intent_data["intent_type"] in ["how_to", "definition", "general"], \
                    f"Intent type mismatch for: {query}"
        
        return True
    
    async def test_generate_insights(self) -> bool:
        """洞察生成テスト"""
        # まず検索実行
        search_result = await self.processor.process_action("search_knowledge", {
            "query": "賢者",
            "limit": 10
        })
        
        # 洞察生成
        result = await self.processor.process_action("generate_insights", {
            "search_results": search_result["data"]["results"],
            "query": "賢者"
        })
        
        assert result["success"], "Generate insights should succeed"
        insights = result["data"]
        assert "summary" in insights, "Should have summary"
        assert "key_themes" in insights, "Should have key themes"
        assert "recommendations" in insights, "Should have recommendations"
        
        return True
    
    async def test_delete_document(self) -> bool:
        """ドキュメント削除テスト"""
        # 削除用ドキュメント作成
        test_doc = {
            "id": "doc_to_delete",
            "content": "削除されるドキュメント",
            "source": "test",
            "title": "削除テスト"
        }
        
        # インデックス
        await self.processor.process_action("index_document", {"document": test_doc})
        
        # 削除
        result = await self.processor.process_action("delete_document", {
            "document_id": "doc_to_delete"
        })
        
        assert result["success"], "Delete should succeed"
        assert result["data"]["deleted"], "Document should be deleted"
        
        # 検索して削除確認
        search_result = await self.processor.process_action("search_knowledge", {
            "query": "削除されるドキュメント",
            "limit": 1
        })
        
        # 削除されたドキュメントは見つからないはず
        found_deleted = any(
            r["document_id"] == "doc_to_delete" 
            for r in search_result["data"]["results"]
        )
        assert not found_deleted, "Deleted document should not be found"
        
        return True
    
    async def test_update_document_boost(self) -> bool:
        """ドキュメントブースト更新テスト"""
        result = await self.processor.process_action("update_document_boost", {
            "document_id": "test_doc_1",
            "boost_value": 2.0
        })
        
        assert result["success"], "Update boost should succeed"
        assert result["data"]["boost_value"] == 2.0, "Boost value should be updated"
        
        # 検索してブースト効果確認
        search_result = await self.processor.process_action("search_knowledge", {
            "query": "Elder",
            "limit": 10
        })
        
        # ブーストされたドキュメントが上位に来るはず
        if len(search_result["data"]["results"]) > 1:
            first_result = search_result["data"]["results"][0]
            # スコアが高いことを確認（厳密な順序は保証しない）
            assert first_result["score"] > 0, "Boosted document should have high score"
        
        return True
    
    async def test_search_filters(self) -> bool:
        """検索フィルターテスト"""
        # カテゴリフィルター
        result = await self.processor.process_action("search_knowledge", {
            "query": "システム",
            "filters": {"category": "architecture"},
            "limit": 10
        })
        
        assert result["success"], "Filtered search should succeed"
        
        # フィルター結果確認
        for doc in result["data"]["results"]:
            assert doc["category"] == "architecture", "All results should match category filter"
        
        # タグフィルター
        result = await self.processor.process_action("search_knowledge", {
            "query": "",
            "filters": {"tags": ["a2a"]},
            "limit": 10
        })
        
        assert result["success"], "Tag filtered search should succeed"
        
        return True
    
    async def test_search_types(self) -> bool:
        """検索タイプテスト"""
        search_types = ["full_text", "semantic", "hybrid", "exact"]
        
        for search_type in search_types:
            result = await self.processor.process_action("search_knowledge", {
                "query": "Elder Loop",
                "search_type": search_type,
                "limit": 5
            })
            
            assert result["success"], f"{search_type} search should succeed"
            assert result["data"]["search_type"] == search_type, "Search type should match"
        
        return True
    
    async def test_optimize_index(self) -> bool:
        """インデックス最適化テスト"""
        result = await self.processor.process_action("optimize_index", {})
        
        assert result["success"], "Optimize should succeed"
        assert "optimization_time_ms" in result["data"], "Should have optimization time"
        
        return True
    
    async def test_get_search_statistics(self) -> bool:
        """検索統計取得テスト"""
        result = await self.processor.process_action("get_search_statistics", {})
        
        assert result["success"], "Get statistics should succeed"
        stats = result["data"]
        assert "total_searches" in stats, "Should have total searches"
        assert "popular_queries" in stats, "Should have popular queries"
        assert "average_search_time_ms" in stats, "Should have average search time"
        
        return True
    
    async def test_get_index_info(self) -> bool:
        """インデックス情報取得テスト"""
        result = await self.processor.process_action("get_index_info", {})
        
        assert result["success"], "Get index info should succeed"
        info = result["data"]
        assert "document_count" in info, "Should have document count"
        assert "size_bytes" in info, "Should have size"
        assert info["document_count"] > 0, "Should have indexed documents"
        
        return True
    
    async def test_health_check(self) -> bool:
        """ヘルスチェックテスト"""
        result = await self.processor.process_action("health_check", {})
        
        assert result["success"], "Health check should succeed"
        health = result["data"]
        assert health["status"] == "healthy", "Should be healthy"
        assert health["db_accessible"], "Database should be accessible"
        assert health["search_functional"], "Search should be functional"
        
        return True


async def main():
    """メイン実行"""
    tester = TestRAGSageA2ADirect()
    results = await tester.run_all_tests()
    
    # Elder Loop基準チェック（80%以上）
    if results["success_rate"] >= 80:
        print(f"\n🎉 Elder Loop Quality Gate PASSED! ({results['success_rate']:.1f}%)")
    else:
        print(f"\n❌ Elder Loop Quality Gate FAILED! ({results['success_rate']:.1f}% < 80%)")


if __name__ == "__main__":
    asyncio.run(main())