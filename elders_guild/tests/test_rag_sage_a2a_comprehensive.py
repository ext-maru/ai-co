#!/usr/bin/env python3
"""
"🔍" RAG Sage A2A Agent - 包括的テストスイート
========================================

Elder Loop Phase 4: 厳密検証ループ
パフォーマンス・並行性・エラーハンドリング・統合テスト

Author: Claude Elder
Created: 2025-07-23
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import threading
import random
import gc
import pytest
import tempfile
import os

# 環境変数を使用してパスを設定
import sys
import os
# shared_libs.configからELDERS_GUILD_HOMEを取得
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_libs.config import config
sys.path.insert(0, config.ELDERS_GUILD_HOME)
from rag_sage.business_logic import RAGProcessor


class TestRAGSageA2AComprehensive:
    """RAG Sage A2A Agent包括的テスト"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テスト用セットアップ"""
        self.performance_metrics = {}
        self.logger = logging.getLogger("rag_sage_comprehensive_test")
        yield
        # クリーンアップ処理（必要に応じて）
    
    @pytest.mark.asyncio
    async def test_performance(self):
        """パフォーマンステスト"""
        processor = RAGProcessor()
        
        # 大量文書の処理性能テスト
        test_documents = []
        for i in range(100):
            document = {
                "title": f"Test Document {i}",
                "content": f"This is test content for document {i}. It contains information about topic {i % 10}.",
                "category": ["engineering", "science", "business"][i % 3],
                "source": f"test_source_{i}",
                "vector_id": f"vec_{i}"
            }
            test_documents.append(document)
        
        # 文書インデックス作成時間測定
        start_time = time.time()
        
        for doc in test_documents:
            result = await processor.process_action("add_document", {"document": doc})
            assert result.get("success"), f"文書追加失敗: {doc['title']}"
        
        index_time = time.time() - start_time
        
        # 検索パフォーマンステスト
        search_queries = [
            "engineering topic",
            "science information", 
            "business document",
            "test content",
            "topic 5"
        ]
        
        search_start = time.time()
        search_results = []
        
        for query in search_queries:
            result = await processor.process_action("search", {"query": query})
            search_results.append(result)
        
        search_time = time.time() - search_start
        
        # パフォーマンスメトリクス計算
        avg_index_time = index_time / len(test_documents)
        avg_search_time = search_time / len(search_queries)
        
        self.performance_metrics["indexing"] = {
            "total_documents": len(test_documents),
            "total_time": index_time,
            "avg_time_per_doc": avg_index_time,
            "docs_per_second": len(test_documents) / index_time
        }
        
        self.performance_metrics["searching"] = {
            "total_queries": len(search_queries),
            "total_time": search_time,
            "avg_time_per_query": avg_search_time,
            "queries_per_second": len(search_queries) / search_time
        }
        
        # パフォーマンス基準確認
        assert avg_index_time < 0.1, f"インデックス時間が長い: {avg_index_time:.3f}s/doc"
        assert avg_search_time < 0.5, f"検索時間が長い: {avg_search_time:.3f}s/query"
        
        print(f"✅ パフォーマンステスト成功: {len(test_documents)/index_time:.1f} docs/sec, {len(search_queries)/search_time:.1f} queries/sec")
    
    @pytest.mark.asyncio
    async def test_concurrency(self):
        """並行性テスト"""
        processor = RAGProcessor()
        
        # 並行検索タスク定義
        async def concurrent_search(query_id):
            query = f"concurrent test query {query_id % 5}"
            return await processor.process_action("search", {"query": query})
        
        # 並行文書追加タスク
        async def concurrent_add_document(doc_id):
            document = {
                "title": f"Concurrent Document {doc_id}",
                "content": f"Concurrent content for testing parallel processing {doc_id}",
                "category": "concurrent_test",
                "source": f"concurrent_source_{doc_id}"
            }
            return await processor.process_action("add_document", {"document": document})
        
        # 並行実行
        start_time = time.time()
        
        # 文書追加と検索を同時実行
        add_tasks = [concurrent_add_document(i) for i in range(20)]
        search_tasks = [concurrent_search(i) for i in range(30)]
        
        all_tasks = add_tasks + search_tasks
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        end_time = time.time()
        
        # 結果分析
        add_results = results[:20]
        search_results = results[20:]
        
        successful_adds = [r for r in add_results if not isinstance(r, Exception) and r.get("success")]
        successful_searches = [r for r in search_results if not isinstance(r, Exception) and r.get("success")]
        
        concurrent_time = end_time - start_time
        
        self.performance_metrics["concurrency"] = {
            "total_operations": len(all_tasks),
            "successful_adds": len(successful_adds),
            "successful_searches": len(successful_searches),
            "execution_time": concurrent_time,
            "operations_per_second": len(all_tasks) / concurrent_time
        }
        
        # 並行性基準確認
        assert len(successful_adds) >= 18, f"並行文書追加失敗が多い: {20 - len(successful_adds)} 失敗"
        assert len(successful_searches) >= 25, f"並行検索失敗が多い: {30 - len(successful_searches)} 失敗"
        assert concurrent_time < 10.0, f"並行実行時間が長い: {concurrent_time:.3f}s"
        
        print(f"✅ 並行性テスト成功: {len(successful_adds)+len(successful_searches)}/{len(all_tasks)} 成功, {concurrent_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """エラーハンドリングテスト"""
        processor = RAGProcessor()
        
        # エラーテストケース
        error_test_cases = [
            {
                "name": "空データ文書追加",
                "action": "add_document",
                "data": {"document": {}}
            },
            {
                "name": "無効な検索パラメータ",
                "action": "search",
                "data": {"query": "", "max_results": -1}
            },
            {
                "name": "存在しない文書更新",
                "action": "update_document",
                "data": {"document_id": "non_existent_id", "updates": {"title": "New Title"}}
            },
            {
                "name": "無効なベクトル検索",
                "action": "vector_search",
                "data": {"vector": "not_a_vector", "k": "not_a_number"}
            },
            {
                "name": "巨大クエリ",
                "action": "search",
                "data": {"query": "x" * 10000}
            },
            {
                "name": "無効なフィルタ条件",
                "action": "search_with_filters",
                "data": {"query": "test", "filters": {"invalid_field": None}}
            },
            {
                "name": "重複文書追加",
                "action": "add_document",
                "data": {"document": {"document_id": "duplicate_id", "title": "Duplicate", "content": "Test"}}
            }
        ]
        
        # 重複テスト用に文書を事前追加
        await processor.process_action("add_document", {
            "document": {"document_id": "duplicate_id", "title": "Original", "content": "Original content"}
        })
        
        error_handling_results = []
        
        for test_case in error_test_cases:
            try:
                result = await processor.process_action(test_case["action"], test_case["data"])
                
                if result.get("success"):
                    error_handling_results.append({
                        "case": test_case["name"],
                        "status": "unexpected_success",
                        "result": result
                    })
                else:
                    if "error" in result and isinstance(result["error"], str):
                        error_handling_results.append({
                            "case": test_case["name"],
                            "status": "properly_handled",
                            "error": result["error"]
                        })
                    else:
                        error_handling_results.append({
                            "case": test_case["name"],
                            "status": "improper_error_format",
                            "result": result
                        })
            
            except Exception as e:
                error_handling_results.append({
                    "case": test_case["name"],
                    "status": "unhandled_exception",
                    "exception": str(e)
                })
        
        # エラーハンドリング評価
        properly_handled = len([r for r in error_handling_results if r["status"] == "properly_handled"])
        total_cases = len(error_test_cases)
        
        assert properly_handled >= total_cases * 0.8, f"エラーハンドリング不十分: {properly_handled}/{total_cases}"
        
        print(f"✅ エラーハンドリング成功: {properly_handled}/{total_cases} 適切処理")
    
    @pytest.mark.asyncio
    async def test_data_integrity(self):
        """データ整合性テスト"""
        processor = RAGProcessor()
        
        # テスト用文書データ
        original_document = {
            "document_id": "integrity_test_doc",
            "title": "Data Integrity Test Document",
            "content": "This is a test document for verifying data integrity in RAG system.",
            "metadata": {
                "author": "Test Author",
                "created_at": "2025-07-23",
                "tags": ["test", "integrity", "rag"],
                "version": 1.0
            },
            "category": "testing",
            "source": "test_suite"
        }
        
        # 1. 文書追加
        add_result = await processor.process_action("add_document", {"document": original_document})
        assert add_result.get("success"), "文書追加失敗"
        
        doc_id = add_result["data"]["document_id"]
        
        # 2. 文書取得して整合性確認
        get_result = await processor.process_action("get_document", {"document_id": doc_id})
        assert get_result.get("success"), "文書取得失敗"
        
        retrieved_doc = get_result["data"]["document"]
        
        # データ整合性チェック
        assert retrieved_doc["title"] == original_document["title"], "タイトル不整合"
        assert retrieved_doc["content"] == original_document["content"], "コンテンツ不整合"
        assert retrieved_doc["category"] == original_document["category"], "カテゴリ不整合"
        assert retrieved_doc["metadata"]["tags"] == original_document["metadata"]["tags"], "タグ不整合"
        
        # 3. 文書更新
        updates = {
            "title": "Updated Title",
            "metadata": {
                "version": 2.0,
                "updated_at": "2025-07-23"
            }
        }
        
        update_result = await processor.process_action("update_document", {
            "document_id": doc_id,
            "updates": updates
        })
        assert update_result.get("success"), "文書更新失敗"
        
        # 4. 更新後の整合性確認
        get_updated_result = await processor.process_action("get_document", {"document_id": doc_id})
        assert get_updated_result.get("success"), "更新後文書取得失敗"
        
        updated_doc = get_updated_result["data"]["document"]
        
        assert updated_doc["title"] == updates["title"], "更新後タイトル不整合"
        assert updated_doc["metadata"]["version"] == 2.0, "バージョン不整合"
        assert updated_doc["content"] == original_document["content"], "未更新フィールド変更"
        
        # 5. 検索での整合性確認
        search_result = await processor.process_action("search", {"query": "Updated Title"})
        assert search_result.get("success"), "検索失敗"
        
        search_docs = search_result["data"]["documents"]
        found_doc = next((d for d in search_docs if d["document_id"] == doc_id), None)
        assert found_doc is not None, "更新後文書が検索結果に含まれない"
        
        print("✅ データ整合性テスト成功: 追加・取得・更新・検索の整合性確認完了")
    
    @pytest.mark.asyncio
    async def test_complex_queries(self):
        """複雑クエリテスト"""
        processor = RAGProcessor()
        
        # テスト用の多様な文書を準備
        test_corpus = [
            {
                "title": "Machine Learning Fundamentals",
                "content": "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
                "category": "technology",
                "tags": ["ml", "ai", "fundamentals"]
            },
            {
                "title": "Deep Learning Advanced Techniques",
                "content": "Deep learning uses neural networks with multiple layers to process complex patterns in data.",
                "category": "technology",
                "tags": ["dl", "neural-networks", "advanced"]
            },
            {
                "title": "Natural Language Processing",
                "content": "NLP enables computers to understand, interpret, and generate human language.",
                "category": "technology",
                "tags": ["nlp", "language", "ai"]
            },
            {
                "title": "Business Applications of AI",
                "content": "AI transforms business operations through automation, prediction, and optimization.",
                "category": "business",
                "tags": ["business", "ai", "applications"]
            },
            {
                "title": "Healthcare AI Solutions",
                "content": "AI in healthcare improves diagnosis, treatment planning, and patient care.",
                "category": "healthcare",
                "tags": ["healthcare", "ai", "medical"]
            }
        ]
        
        # 文書をインデックスに追加
        for doc in test_corpus:
            await processor.process_action("add_document", {"document": doc})
        
        # 複雑なクエリテストケース
        complex_queries = [
            {
                "name": "マルチワード検索",
                "query": "machine learning neural networks",
                "expected_min_results": 2
            },
            {
                "name": "フレーズ検索",
                "query": '"artificial intelligence"',
                "expected_min_results": 1
            },
            {
                "name": "カテゴリフィルタ付き検索",
                "action": "search_with_filters",
                "query": "AI",
                "filters": {"category": "technology"},
                "expected_min_results": 2
            },
            {
                "name": "タグベース検索",
                "action": "search_with_filters",
                "query": "learning",
                "filters": {"tags": ["ai"]},
                "expected_min_results": 1
            },
            {
                "name": "セマンティック検索",
                "query": "intelligent systems that learn",
                "expected_min_results": 2
            }
        ]
        
        query_results = []
        
        for test_case in complex_queries:
            action = test_case.get("action", "search")
            
            if action == "search":
                result = await processor.process_action(action, {"query": test_case["query"]})
            else:
                result = await processor.process_action(action, {
                    "query": test_case["query"],
                    "filters": test_case.get("filters", {})
                })
            
            if result.get("success"):
                docs_found = len(result["data"]["documents"])
                query_results.append({
                    "name": test_case["name"],
                    "docs_found": docs_found,
                    "meets_expectation": docs_found >= test_case["expected_min_results"]
                })
        
        # 結果評価
        successful_queries = [r for r in query_results if r["meets_expectation"]]
        success_rate = len(successful_queries) / len(query_results) * 100
        
        assert success_rate >= 80, f"複雑クエリ成功率が低い: {success_rate:.1f}%"
        
        print(f"✅ 複雑クエリテスト成功: {len(successful_queries)}/{len(query_results)} クエリ成功")
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """メモリ効率性テスト"""
        try:
            import psutil
            
            # 初期メモリ使用量
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            processor = RAGProcessor()
            
            # 大量文書処理
            batch_size = 100
            num_batches = 5
            
            for batch in range(num_batches):
                batch_docs = []
                for i in range(batch_size):
                    doc_id = batch * batch_size + i
                    document = {
                        "title": f"Memory Test Document {doc_id}",
                        "content": f"This is content for memory efficiency testing. " * 50,  # 長めのコンテンツ
                        "metadata": {
                            "batch": batch,
                            "index": i,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    batch_docs.append(document)
                
                # バッチ処理
                for doc in batch_docs:
                    await processor.process_action("add_document", {"document": doc})
                
                # ガベージコレクション促進
                if batch % 2 == 0:
                    gc.collect()
            
            # 最終メモリ使用量
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            total_docs = batch_size * num_batches
            memory_per_doc = memory_increase / total_docs * 1024  # KB per document
            
            self.performance_metrics["memory_efficiency"] = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "total_documents": total_docs,
                "memory_per_doc_kb": memory_per_doc
            }
            
            # メモリ効率性基準
            assert memory_increase < 200, f"メモリ使用量増加が大きい: {memory_increase:.1f}MB"
            assert memory_per_doc < 50, f"文書あたりメモリ使用量が大きい: {memory_per_doc:.1f}KB/doc"
            
            print(f"✅ メモリ効率性テスト成功: +{memory_increase:.1f}MB, {memory_per_doc:.1f}KB/doc")
            
        except ImportError:
            pytest.skip("psutil未利用可能、メモリテストスキップ")
    
    @pytest.mark.asyncio
    async def test_search_accuracy(self):
        """検索精度テスト"""
        processor = RAGProcessor()
        
        # 精度テスト用の文書セット
        test_documents = [
            {
                "document_id": "doc1",
                "title": "Python Programming Guide",
                "content": "Python is a high-level programming language known for its simplicity and readability.",
                "category": "programming"
            },
            {
                "document_id": "doc2",
                "title": "Java Development Best Practices",
                "content": "Java is an object-oriented programming language widely used for enterprise applications.",
                "category": "programming"
            },
            {
                "document_id": "doc3",
                "title": "Machine Learning with Python",
                "content": "Python provides excellent libraries for machine learning such as scikit-learn and TensorFlow.",
                "category": "ml"
            },
            {
                "document_id": "doc4",
                "title": "Data Science Fundamentals",
                "content": "Data science combines statistics, programming, and domain knowledge to extract insights.",
                "category": "data-science"
            },
            {
                "document_id": "doc5",
                "title": "Web Development with JavaScript",
                "content": "JavaScript is essential for modern web development, both frontend and backend.",
                "category": "web"
            }
        ]
        
        # 文書を追加
        for doc in test_documents:
            await processor.process_action("add_document", {"document": doc})
        
        # 検索精度テストケース
        accuracy_tests = [
            {
                "query": "Python programming",
                "expected_docs": ["doc1", "doc3"],
                "must_include": ["doc1"]
            },
            {
                "query": "machine learning libraries",
                "expected_docs": ["doc3"],
                "must_include": ["doc3"]
            },
            {
                "query": "programming language",
                "expected_docs": ["doc1", "doc2", "doc5"],
                "must_include": ["doc1", "doc2"]
            },
            {
                "query": "data analysis",
                "expected_docs": ["doc4", "doc3"],
                "must_include": ["doc4"]
            }
        ]
        
        accuracy_results = []
        
        for test in accuracy_tests:
            result = await processor.process_action("search", {
                "query": test["query"],
                "max_results": 5
            })
            
            if result.get("success"):
                found_ids = [doc["document_id"] for doc in result["data"]["documents"]]
                
                # 必須文書が含まれているか確認
                must_include_found = all(doc_id in found_ids for doc_id in test["must_include"])
                
                # 期待される文書との重複率
                expected_set = set(test["expected_docs"])
                found_set = set(found_ids[:len(test["expected_docs"])])  # 上位N件で評価
                overlap = len(expected_set & found_set) / len(expected_set) if expected_set else 0
                
                accuracy_results.append({
                    "query": test["query"],
                    "must_include_found": must_include_found,
                    "overlap_ratio": overlap,
                    "found_docs": found_ids
                })
        
        # 精度評価
        must_include_success = sum(1 for r in accuracy_results if r["must_include_found"])
        avg_overlap = sum(r["overlap_ratio"] for r in accuracy_results) / len(accuracy_results)
        
        self.performance_metrics["search_accuracy"] = {
            "total_tests": len(accuracy_tests),
            "must_include_success": must_include_success,
            "average_overlap_ratio": avg_overlap
        }
        
        assert must_include_success == len(accuracy_tests), f"必須文書の検索漏れ: {must_include_success}/{len(accuracy_tests)}"
        assert avg_overlap >= 0.7, f"検索精度が低い: {avg_overlap:.2f}"
        
        print(f"✅ 検索精度テスト成功: 必須文書 {must_include_success}/{len(accuracy_tests)}, 平均重複率 {avg_overlap:.2f}")
    
    @pytest.mark.asyncio
    async def test_vector_operations(self):
        """ベクトル操作テスト"""
        processor = RAGProcessor()
        
        # ベクトル検索用の文書準備
        vector_docs = [
            {
                "document_id": "vec1",
                "title": "Artificial Intelligence Overview",
                "content": "AI encompasses machine learning, deep learning, and other computational intelligence techniques.",
                "vector": [0.1, 0.2, 0.3, 0.4, 0.5]  # 簡略化されたベクトル
            },
            {
                "document_id": "vec2",
                "title": "Machine Learning Applications",
                "content": "ML is applied in various domains including computer vision, NLP, and recommendation systems.",
                "vector": [0.2, 0.3, 0.4, 0.5, 0.6]
            },
            {
                "document_id": "vec3",
                "title": "Deep Learning Neural Networks",
                "content": "Deep neural networks have revolutionized pattern recognition and data analysis.",
                "vector": [0.3, 0.4, 0.5, 0.6, 0.7]
            }
        ]
        
        # ベクトル付き文書を追加
        for doc in vector_docs:
            result = await processor.process_action("add_document_with_vector", {"document": doc})
            assert result.get("success"), f"ベクトル文書追加失敗: {doc['document_id']}"
        
        # ベクトル検索テスト
        query_vector = [0.25, 0.35, 0.45, 0.55, 0.65]
        
        vector_search_result = await processor.process_action("vector_search", {
            "vector": query_vector,
            "k": 2
        })
        
        assert vector_search_result.get("success"), "ベクトル検索失敗"
        
        results = vector_search_result["data"]["documents"]
        assert len(results) == 2, f"期待される結果数と異なる: {len(results)}"
        
        # 最も近い文書が正しく取得されているか確認
        # vec2とvec3が最も近いはず
        found_ids = [doc["document_id"] for doc in results]
        assert "vec2" in found_ids or "vec3" in found_ids, "期待される近傍文書が見つからない"
        
        # ハイブリッド検索テスト（テキスト + ベクトル）
        hybrid_result = await processor.process_action("hybrid_search", {
            "query": "neural networks",
            "vector": query_vector,
            "text_weight": 0.5,
            "vector_weight": 0.5
        })
        
        assert hybrid_result.get("success"), "ハイブリッド検索失敗"
        
        print("✅ ベクトル操作テスト成功: ベクトル検索・ハイブリッド検索正常動作")
    
    @pytest.mark.asyncio
    async def test_batch_operations(self):
        """バッチ操作テスト"""
        processor = RAGProcessor()
        
        # バッチ追加テスト
        batch_documents = []
        for i in range(50):
            batch_documents.append({
                "title": f"Batch Document {i}",
                "content": f"Content for batch processing test document {i}",
                "category": f"batch_{i % 5}"
            })
        
        # バッチ追加実行
        batch_add_result = await processor.process_action("batch_add_documents", {
            "documents": batch_documents
        })
        
        assert batch_add_result.get("success"), "バッチ追加失敗"
        
        batch_data = batch_add_result["data"]
        assert batch_data["total_processed"] == len(batch_documents), "処理数が一致しない"
        assert batch_data["successful"] >= len(batch_documents) * 0.95, "成功率が低い"
        
        # バッチ更新テスト
        batch_updates = []
        for i in range(10):
            if i < len(batch_data.get("document_ids", [])):
                batch_updates.append({
                    "document_id": batch_data["document_ids"][i],
                    "updates": {"title": f"Updated Batch Document {i}"}
                })
        
        if batch_updates:
            batch_update_result = await processor.process_action("batch_update_documents", {
                "updates": batch_updates
            })
            
            assert batch_update_result.get("success"), "バッチ更新失敗"
        
        # バッチ削除テスト
        delete_ids = batch_data.get("document_ids", [])[:5] if "document_ids" in batch_data else []
        
        if delete_ids:
            batch_delete_result = await processor.process_action("batch_delete_documents", {
                "document_ids": delete_ids
            })
            
            assert batch_delete_result.get("success"), "バッチ削除失敗"
            assert batch_delete_result["data"]["deleted_count"] == len(delete_ids), "削除数が一致しない"
        
        print("✅ バッチ操作テスト成功: 追加・更新・削除のバッチ処理確認")
    
    @pytest.mark.asyncio
    async def test_caching_performance(self):
        """キャッシング性能テスト"""
        processor = RAGProcessor()
        
        # テスト用文書を追加
        test_doc = {
            "document_id": "cache_test",
            "title": "Caching Test Document",
            "content": "This document is used to test the caching performance of the RAG system."
        }
        
        await processor.process_action("add_document", {"document": test_doc})
        
        # 同じクエリを複数回実行してキャッシュ効果を測定
        test_query = "caching performance test"
        
        # 初回検索（キャッシュなし）
        start_time = time.time()
        first_result = await processor.process_action("search", {"query": test_query})
        first_search_time = time.time() - start_time
        
        assert first_result.get("success"), "初回検索失敗"
        
        # 2回目検索（キャッシュあり）
        start_time = time.time()
        second_result = await processor.process_action("search", {"query": test_query})
        second_search_time = time.time() - start_time
        
        assert second_result.get("success"), "2回目検索失敗"
        
        # 結果が同じであることを確認
        first_docs = first_result["data"]["documents"]
        second_docs = second_result["data"]["documents"]
        
        assert len(first_docs) == len(second_docs), "キャッシュ結果が異なる"
        
        # キャッシュによる高速化を確認
        speedup = first_search_time / second_search_time if second_search_time > 0 else float('inf')
        
        self.performance_metrics["caching"] = {
            "first_search_time": first_search_time,
            "cached_search_time": second_search_time,
            "speedup_factor": speedup
        }
        
        # キャッシュ効果の基準（少なくとも2倍以上高速化）
        assert speedup >= 2.0, f"キャッシュ効果が不十分: {speedup:.1f}倍"
        
        # キャッシュ無効化テスト
        await processor.process_action("clear_cache", {})
        
        # キャッシュクリア後の検索
        start_time = time.time()
        third_result = await processor.process_action("search", {"query": test_query})
        third_search_time = time.time() - start_time
        
        # キャッシュクリア後は初回と同程度の時間がかかるはず
        assert third_search_time > second_search_time * 1.5, "キャッシュクリアが効いていない"
        
        print(f"✅ キャッシング性能テスト成功: {speedup:.1f}倍高速化")
    
    @pytest.mark.asyncio
    async def test_advanced_filtering(self):
        """高度なフィルタリングテスト"""
        processor = RAGProcessor()
        
        # フィルタリングテスト用の文書セット
        filter_test_docs = [
            {
                "title": "Document A",
                "content": "Advanced filtering test document",
                "metadata": {
                    "date": "2025-07-20",
                    "author": "Alice",
                    "priority": 5,
                    "tags": ["important", "technical"]
                }
            },
            {
                "title": "Document B",
                "content": "Another test document for filtering",
                "metadata": {
                    "date": "2025-07-21",
                    "author": "Bob",
                    "priority": 3,
                    "tags": ["review", "draft"]
                }
            },
            {
                "title": "Document C",
                "content": "Third document with different attributes",
                "metadata": {
                    "date": "2025-07-22",
                    "author": "Alice",
                    "priority": 8,
                    "tags": ["important", "urgent"]
                }
            },
            {
                "title": "Document D",
                "content": "Final test document",
                "metadata": {
                    "date": "2025-07-23",
                    "author": "Charlie",
                    "priority": 2,
                    "tags": ["draft"]
                }
            }
        ]
        
        # 文書を追加
        for doc in filter_test_docs:
            await processor.process_action("add_document", {"document": doc})
        
        # 複雑なフィルタリングテストケース
        filter_tests = [
            {
                "name": "著者フィルタ",
                "filters": {"metadata.author": "Alice"},
                "expected_count": 2
            },
            {
                "name": "優先度範囲フィルタ",
                "filters": {"metadata.priority": {"$gte": 5}},
                "expected_count": 2
            },
            {
                "name": "タグ含有フィルタ",
                "filters": {"metadata.tags": {"$contains": "important"}},
                "expected_count": 2
            },
            {
                "name": "日付範囲フィルタ",
                "filters": {
                    "metadata.date": {
                        "$gte": "2025-07-21",
                        "$lte": "2025-07-22"
                    }
                },
                "expected_count": 2
            },
            {
                "name": "複合条件フィルタ",
                "filters": {
                    "$and": [
                        {"metadata.author": "Alice"},
                        {"metadata.priority": {"$gte": 5}}
                    ]
                },
                "expected_count": 2
            }
        ]
        
        filter_results = []
        
        for test in filter_tests:
            result = await processor.process_action("search_with_filters", {
                "query": "document",
                "filters": test["filters"]
            })
            
            if result.get("success"):
                found_count = len(result["data"]["documents"])
                filter_results.append({
                    "name": test["name"],
                    "found": found_count,
                    "expected": test["expected_count"],
                    "correct": found_count == test["expected_count"]
                })
        
        # フィルタリング精度評価
        correct_filters = sum(1 for r in filter_results if r["correct"])
        filter_accuracy = correct_filters / len(filter_results) * 100
        
        assert filter_accuracy >= 80, f"フィルタリング精度が低い: {filter_accuracy:.1f}%"
        
        print(f"✅ 高度なフィルタリングテスト成功: {correct_filters}/{len(filter_results)} フィルタ正確")
    
    @pytest.mark.asyncio
    async def test_document_lifecycle(self):
        """文書ライフサイクルテスト"""
        processor = RAGProcessor()
        
        # ライフサイクル全体のテスト
        lifecycle_doc = {
            "document_id": "lifecycle_test",
            "title": "Document Lifecycle Test",
            "content": "This document will go through the complete lifecycle.",
            "metadata": {
                "version": 1,
                "status": "draft"
            }
        }
        
        # 1. 作成
        create_result = await processor.process_action("add_document", {"document": lifecycle_doc})
        assert create_result.get("success"), "文書作成失敗"
        
        doc_id = create_result["data"]["document_id"]
        
        # 2. 読み取り
        read_result = await processor.process_action("get_document", {"document_id": doc_id})
        assert read_result.get("success"), "文書読み取り失敗"
        assert read_result["data"]["document"]["title"] == lifecycle_doc["title"], "読み取りデータ不一致"
        
        # 3. 更新（複数回）
        updates_sequence = [
            {"metadata": {"version": 2, "status": "review"}},
            {"title": "Updated Document Lifecycle Test"},
            {"metadata": {"version": 3, "status": "published"}}
        ]
        
        for update in updates_sequence:
            update_result = await processor.process_action("update_document", {
                "document_id": doc_id,
                "updates": update
            })
            assert update_result.get("success"), "文書更新失敗"
        
        # 4. 更新履歴確認
        history_result = await processor.process_action("get_document_history", {"document_id": doc_id})
        if history_result.get("success"):
            history = history_result["data"]["history"]
            assert len(history) >= len(updates_sequence), "更新履歴が不完全"
        
        # 5. 検索確認
        search_result = await processor.process_action("search", {"query": "Updated Document Lifecycle"})
        assert search_result.get("success"), "更新後検索失敗"
        
        found = any(doc["document_id"] == doc_id for doc in search_result["data"]["documents"])
        assert found, "更新後文書が検索されない"
        
        # 6. 削除
        delete_result = await processor.process_action("delete_document", {"document_id": doc_id})
        assert delete_result.get("success"), "文書削除失敗"
        
        # 7. 削除後確認
        get_deleted_result = await processor.process_action("get_document", {"document_id": doc_id})
        assert not get_deleted_result.get("success"), "削除後も文書が取得できる"
        
        print("✅ 文書ライフサイクルテスト成功: 作成→読取→更新→削除の完全サイクル確認")
    
    @pytest.mark.asyncio
    async def test_stress_load(self):
        """ストレス負荷テスト"""
        processor = RAGProcessor()
        
        # ストレステスト設定
        stress_config = {
            "num_documents": 200,
            "num_searches": 300,
            "num_updates": 100,
            "batch_size": 20
        }
        
        start_time = time.time()
        
        # 1. 大量文書追加
        stress_docs = []
        for i in range(stress_config["num_documents"]):
            stress_docs.append({
                "title": f"Stress Test Document {i}",
                "content": f"Content for stress testing with index {i} and random data {random.random()}",
                "category": f"stress_cat_{i % 10}",
                "metadata": {
                    "index": i,
                    "batch": i // stress_config["batch_size"]
                }
            })
        
        # バッチで追加
        for batch_start in range(0, len(stress_docs), stress_config["batch_size"]):
            batch_end = min(batch_start + stress_config["batch_size"], len(stress_docs))
            batch = stress_docs[batch_start:batch_end]
            
            result = await processor.process_action("batch_add_documents", {"documents": batch})
            assert result.get("success"), f"バッチ追加失敗: バッチ {batch_start // stress_config['batch_size']}"
        
        add_time = time.time() - start_time
        
        # 2. 大量検索
        search_start = time.time()
        search_tasks = []
        
        for i in range(stress_config["num_searches"]):
            query = f"stress test {i % 50}"
            task = processor.process_action("search", {"query": query})
            search_tasks.append(task)
            
            # 並行実行数を制限
            if len(search_tasks) >= 10:
                await asyncio.gather(*search_tasks)
                search_tasks = []
        
        if search_tasks:
            await asyncio.gather(*search_tasks)
        
        search_time = time.time() - search_start
        
        # 3. ランダム更新
        update_start = time.time()
        
        for i in range(stress_config["num_updates"]):
            # ランダムな文書を更新
            random_index = random.randint(0, stress_config["num_documents"] - 1)
            update_data = {
                "document_id": f"stress_doc_{random_index}",  # 仮定のID形式
                "updates": {
                    "metadata": {
                        "updated": True,
                        "update_count": i
                    }
                }
            }
            
            # エラーを無視して続行
            await processor.process_action("update_document", update_data)
        
        update_time = time.time() - update_start
        
        total_time = time.time() - start_time
        
        # パフォーマンスメトリクス
        self.performance_metrics["stress_test"] = {
            "total_operations": stress_config["num_documents"] + stress_config["num_searches"] + stress_config["num_updates"],
            "total_time": total_time,
            "add_time": add_time,
            "search_time": search_time,
            "update_time": update_time,
            "docs_per_second": stress_config["num_documents"] / add_time,
            "searches_per_second": stress_config["num_searches"] / search_time,
            "updates_per_second": stress_config["num_updates"] / update_time
        }
        
        # ストレステスト基準
        assert total_time < 60, f"ストレステスト時間が長すぎる: {total_time:.1f}秒"
        assert self.performance_metrics["stress_test"]["docs_per_second"] > 50, "文書追加速度が遅い"
        assert self.performance_metrics["stress_test"]["searches_per_second"] > 100, "検索速度が遅い"
        
        print(f"✅ ストレス負荷テスト成功: {total_time:.1f}秒で{self.performance_metrics['stress_test']['total_operations']}操作完了")
    
    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """エッジケーステスト"""
        processor = RAGProcessor()
        
        edge_cases = [
            {
                "name": "空文字列検索",
                "action": "search",
                "data": {"query": ""},
                "should_succeed": True
            },
            {
                "name": "超長文書",
                "action": "add_document",
                "data": {
                    "document": {
                        "title": "Very Long Document",
                        "content": "x" * 10000  # 10,000文字
                    }
                },
                "should_succeed": True
            },
            {
                "name": "特殊文字を含む検索",
                "action": "search",
                "data": {"query": "test @#$%^&*() <script>alert('xss')</script>"},
                "should_succeed": True
            },
            {
                "name": "Unicode文字",
                "action": "add_document",
                "data": {
                    "document": {
                        "title": "Unicode Test 日本語 한국어 中文",
                        "content": "多言語対応テスト 🌍🔍📚"
                    }
                },
                "should_succeed": True
            },
            {
                "name": "重複ID",
                "action": "add_document",
                "data": {
                    "document": {
                        "document_id": "duplicate_edge_test",
                        "title": "First Document",
                        "content": "Original"
                    }
                },
                "should_succeed": True
            },
            {
                "name": "重複ID（2回目）",
                "action": "add_document",
                "data": {
                    "document": {
                        "document_id": "duplicate_edge_test",
                        "title": "Second Document",
                        "content": "Duplicate"
                    }
                },
                "should_succeed": False
            },
            {
                "name": "ゼロ結果クエリ",
                "action": "search",
                "data": {"query": "completely_nonexistent_term_xyz123"},
                "should_succeed": True
            },
            {
                "name": "無効なベクトル次元",
                "action": "vector_search",
                "data": {
                    "vector": [0.1, 0.2],  # 次元が小さすぎる
                    "k": 5
                },
                "should_succeed": False
            }
        ]
        
        edge_results = []
        
        for test_case in edge_cases:
            try:
                result = await processor.process_action(test_case["action"], test_case["data"])
                
                success = result.get("success", False)
                expected = test_case["should_succeed"]
                
                edge_results.append({
                    "case": test_case["name"],
                    "expected_success": expected,
                    "actual_success": success,
                    "correct": success == expected
                })
                
            except Exception as e:
                edge_results.append({
                    "case": test_case["name"],
                    "expected_success": test_case["should_succeed"],
                    "actual_success": False,
                    "correct": not test_case["should_succeed"],
                    "exception": str(e)
                })
        
        # エッジケース評価
        correct_cases = [r for r in edge_results if r["correct"]]
        edge_success_rate = len(correct_cases) / len(edge_results) * 100
        
        assert edge_success_rate >= 80, f"エッジケース処理率が低い: {edge_success_rate:.1f}%"
        
        # 失敗ケースの詳細
        for result in edge_results:
            if not result["correct"]:
                print(f"  ⚠️ {result['case']}: 期待={result['expected_success']}, 実際={result['actual_success']}")
        
        print(f"✅ エッジケーステスト成功: {len(correct_cases)}/{len(edge_results)} ケース正常処理")