#!/usr/bin/env python3
"""
"🔍" Search Magic テストスイート
=============================

Search Magic（探索魔法）の包括的なテストスイート。
深層探索、パターン発見、知識検索をテスト。

Author: Claude Elder
Created: 2025-07-23
"""

import pytest
import asyncio
from typing import Dict, Any, List
import json
import tempfile
from pathlib import Path
from datetime import datetime
import ast
import re

# テスト対象をインポート
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ancient_magic.search_magic.search_magic import SearchMagic


class TestSearchMagic:
    """Search Magic テストクラス"""
    
    @pytest.fixture
    def search_magic(self):
        """Search Magic インスタンスを作成"""
        return SearchMagic()
        
    @pytest.fixture
    def sample_codebase_data(self):
        """テスト用コードベースデータ"""
        return {
            "files": [
                {
                    "path": "/project/src/main.py",
                    "content": "def hello_world():\n    print('Hello, World!')\n    return True",
                    "size": 52,
                    "modified": "2025-07-23T10:00:00"
                },
                {
                    "path": "/project/src/utils.py", 
                    "content": "class DataProcessor:\n    def process_data(self, data):\n        return data.upper()",
                    "size": 78,
                    "modified": "2025-07-23T09:30:00"
                },
                {
                    "path": "/project/tests/test_main.py",
                    "content": "import unittest\nfrom src.main import hello_world\n\nclass TestMain(unittest.TestCase):\n    def test_hello_world(self):\n        self.assertTrue(hello_world())",
                    "size": 142,
                    "modified": "2025-07-23T10:15:00"
                }
            ],
            "patterns": ["function_definitions", "class_definitions", "import_statements"],
            "search_targets": ["functions", "classes", "tests", "imports"]
        }
        
    @pytest.fixture
    def sample_knowledge_data(self):
        """テスト用知識データ"""
        return {
            "documents": [
                {
                    "id": "doc_001",
                    "title": "Python Best Practices",
                    "content": "Python coding standards include PEP 8 compliance, proper error handling, and comprehensive testing.",
                    "tags": ["python", "standards", "best-practices"],
                    "category": "development"
                },
                {
                    "id": "doc_002", 
                    "title": "Database Optimization",
                    "content": "Database performance can be improved through indexing, query optimization, and connection pooling.",
                    "tags": ["database", "performance", "optimization"],
                    "category": "performance"
                },
                {
                    "id": "doc_003",
                    "title": "TDD Methodology",
                    "content": "Test-driven development follows Red-Green-Refactor cycle for reliable software development.",
                    "tags": ["testing", "tdd", "methodology"],
                    "category": "methodology"
                }
            ],
            "search_contexts": ["development", "performance", "methodology"]
        }
    
    # Phase 1: 基本的な検索機能（Basic Search）
    async def test_deep_search_codebase(self, search_magic, sample_codebase_data):
        """コードベース深層検索テスト"""
        search_params = {
            "query": "function",
            "search_type": "deep_code_search",
            "targets": sample_codebase_data["files"],
            "patterns": ["function_definitions", "method_calls"]
        }
        
        result = await search_magic.deep_search(search_params)
        
        assert result["success"] is True
        search_results = result["search_results"]
        
        # 検索結果の基本構造確認
        assert "matches" in search_results
        assert "pattern_analysis" in search_results
        assert "relevance_scores" in search_results
        
        # 関数定義が見つかることを確認
        matches = search_results["matches"]
        assert len(matches) > 0
        assert any("hello_world" in match["content"] for match in matches)
        
    async def test_pattern_discovery_ast(self, search_magic, sample_codebase_data):
        """AST パターン発見テスト"""
        discovery_params = {
            "source_code": sample_codebase_data["files"][0]["content"],
            "pattern_types": ["function_definitions", "return_statements", "function_calls"],
            "analysis_depth": "deep"
        }
        
        result = await search_magic.discover_patterns(discovery_params)
        
        assert result["success"] is True
        patterns = result["discovered_patterns"]
        
        # パターン発見の確認
        assert "function_definitions" in patterns
        assert "return_statements" in patterns
        
        # 具体的なパターンの確認
        functions = patterns["function_definitions"]
        assert len(functions) > 0
        assert functions[0]["name"] == "hello_world"
        assert functions[0]["line_number"] == 1
        
    async def test_knowledge_search_whoosh(self, search_magic, sample_knowledge_data):
        """Whoosh 知識検索テスト"""
        search_params = {
            "query": "python testing",
            "documents": sample_knowledge_data["documents"],
            "search_fields": ["title", "content", "tags"],
            "max_results": 10
        }
        
        result = await search_magic.search_knowledge(search_params)
        
        assert result["success"] is True
        search_results = result["search_results"]
        
        # 検索結果の確認
        assert "ranked_results" in search_results
        assert "search_stats" in search_results
        
        ranked_results = search_results["ranked_results"]
        assert len(ranked_results) > 0
        
        # 関連性の高い結果が上位に来ることを確認
        assert ranked_results[0]["relevance_score"] > 0.5
        
    async def test_context_matching(self, search_magic):
        """コンテキストマッチングテスト"""
        context_params = {
            "primary_context": "database optimization",
            "secondary_contexts": ["performance", "indexing", "caching"],
            "similarity_threshold": 0.7
        }
        
        result = await search_magic.match_contexts(context_params)
        
        assert result["success"] is True
        matches = result["context_matches"]
        
        # コンテキストマッチの確認
        assert "primary_matches" in matches
        assert "similarity_scores" in matches
        assert "related_contexts" in matches
        
    # Phase 2: 高度な検索機能（Advanced Search）
    async def test_semantic_search(self, search_magic, sample_knowledge_data):
        """セマンティック検索テスト"""
        semantic_params = {
            "query": "improve code quality",
            "documents": sample_knowledge_data["documents"],
            "semantic_model": "basic_similarity",
            "context_awareness": True
        }
        
        result = await search_magic.semantic_search(semantic_params)
        
        assert result["success"] is True
        semantic_results = result["semantic_results"]
        
        # セマンティック検索結果の確認
        assert "conceptual_matches" in semantic_results
        assert "semantic_scores" in semantic_results
        
        conceptual_matches = semantic_results["conceptual_matches"]
        assert len(conceptual_matches) > 0
        
        # 概念的類似性の確認
        for match in conceptual_matches:
            assert "semantic_relevance" in match
            assert match["semantic_relevance"] >= 0.0
    
    async def test_pattern_clustering(self, search_magic):
        """パターンクラスタリングテスト"""  
        patterns_data = [
            {"pattern": "def test_", "type": "test_function", "frequency": 15},
            {"pattern": "assert ", "type": "assertion", "frequency": 45},
            {"pattern": "import ", "type": "import_statement", "frequency": 23},
            {"pattern": "class Test", "type": "test_class", "frequency": 8},
            {"pattern": "def __init__", "type": "constructor", "frequency": 12}
        ]
        
        clustering_params = {
            "patterns": patterns_data,
            "clustering_method": "frequency_based",
            "min_cluster_size": 2
        }
        
        result = await search_magic.cluster_patterns(clustering_params)
        
        assert result["success"] is True
        clusters = result["pattern_clusters"]
        
        # クラスタリング結果の確認
        assert "clusters" in clusters
        assert "cluster_stats" in clusters
        
        cluster_list = clusters["clusters"]
        assert len(cluster_list) > 0
        
        # テスト関連パターンがクラスター化されることを確認
        test_cluster = next((c for c in cluster_list if "test" in c["cluster_name"].lower()), None)
        assert test_cluster is not None
        
    async def test_cross_reference_search(self, search_magic, sample_codebase_data):
        """クロスリファレンス検索テスト"""
        cross_ref_params = {
            "target_symbol": "hello_world",
            "codebase": sample_codebase_data["files"],
            "reference_types": ["function_calls", "imports", "mentions"]
        }
        
        result = await search_magic.cross_reference_search(cross_ref_params)
        
        assert result["success"] is True
        references = result["cross_references"]
        
        # クロスリファレンス結果の確認
        assert "definitions" in references
        assert "usages" in references
        assert "import_chains" in references
        
        # 定義と使用箇所の確認
        definitions = references["definitions"]
        usages = references["usages"]
        
        assert len(definitions) > 0
        assert len(usages) > 0
    
    # Phase 3: 特殊検索機能（Specialized Search）
    async def test_dependency_graph_search(self, search_magic, sample_codebase_data):
        """依存関係グラフ検索テスト"""
        dependency_params = {
            "files": sample_codebase_data["files"],
            "dependency_types": ["imports", "function_calls", "class_inheritance"],
            "graph_depth": 3
        }
        
        result = await search_magic.build_dependency_graph(dependency_params)
        
        assert result["success"] is True
        dependency_graph = result["dependency_graph"]
        
        # 依存関係グラフの確認
        assert "nodes" in dependency_graph
        assert "edges" in dependency_graph
        assert "cycles" in dependency_graph
        
        nodes = dependency_graph["nodes"]
        edges = dependency_graph["edges"]
        
        assert len(nodes) > 0
        assert len(edges) >= 0  # エッジは0個でも可
        
    async def test_anomaly_detection_search(self, search_magic):
        """異常検知検索テスト"""
        code_metrics = [
            {"file": "main.py", "complexity": 5, "lines": 50, "functions": 3},
            {"file": "utils.py", "complexity": 8, "lines": 120, "functions": 6},
            {"file": "data.py", "complexity": 25, "lines": 300, "functions": 2},  # 異常
            {"file": "tests.py", "complexity": 3, "lines": 80, "functions": 10}
        ]
        
        anomaly_params = {
            "metrics": code_metrics,
            "anomaly_types": ["complexity", "function_count", "line_ratio"],
            "threshold_method": "statistical"
        }
        
        result = await search_magic.detect_anomalies(anomaly_params)
        
        assert result["success"] is True
        anomalies = result["anomalies"]
        
        # 異常検知結果の確認
        assert "detected_anomalies" in anomalies
        assert "anomaly_scores" in anomalies
        
        detected = anomalies["detected_anomalies"]
        assert len(detected) > 0
        
        # data.pyが異常として検出されることを確認
        data_anomaly = next((a for a in detected if a["file"] == "data.py"), None)
        assert data_anomaly is not None
        assert data_anomaly["anomaly_type"] == "complexity"
    
    async def test_temporal_search(self, search_magic):
        """時系列検索テスト"""
        temporal_data = [
            {"timestamp": "2025-07-23T08:00:00", "event": "function_added", "details": {"name": "process_data"}},
            {"timestamp": "2025-07-23T09:00:00", "event": "test_created", "details": {"test_name": "test_process_data"}},
            {"timestamp": "2025-07-23T10:00:00", "event": "bug_fixed", "details": {"issue": "null_pointer"}},
            {"timestamp": "2025-07-23T11:00:00", "event": "refactor", "details": {"scope": "process_data"}}
        ]
        
        temporal_params = {
            "events": temporal_data,
            "time_range": {"start": "2025-07-23T08:30:00", "end": "2025-07-23T10:30:00"},
            "event_types": ["test_created", "bug_fixed"]
        }
        
        result = await search_magic.temporal_search(temporal_params)
        
        assert result["success"] is True
        temporal_results = result["temporal_results"]
        
        # 時系列検索結果の確認
        assert "filtered_events" in temporal_results
        assert "time_patterns" in temporal_results
        
        filtered_events = temporal_results["filtered_events"]
        assert len(filtered_events) == 2  # test_created と bug_fixed
        
    # Phase 4: 統合検索機能（Integrated Search）
    async def test_multi_modal_search(self, search_magic, sample_codebase_data, sample_knowledge_data):
        """マルチモーダル検索テスト"""
        multi_modal_params = {
            "query": "testing best practices",
            "search_modes": [
                {"type": "code_search", "data": sample_codebase_data["files"]},
                {"type": "knowledge_search", "data": sample_knowledge_data["documents"]},
                {"type": "pattern_search", "patterns": ["test_*", "assert_*"]}
            ],
            "fusion_method": "weighted_ranking"
        }
        
        result = await search_magic.multi_modal_search(multi_modal_params)
        
        assert result["success"] is True
        multi_results = result["multi_modal_results"]
        
        # マルチモーダル検索結果の確認
        assert "unified_results" in multi_results
        assert "mode_contributions" in multi_results
        
        unified_results = multi_results["unified_results"]
        assert len(unified_results) > 0
        
        # 各モードからの貢献度確認
        mode_contributions = multi_results["mode_contributions"]
        assert "code_search" in mode_contributions
        assert "knowledge_search" in mode_contributions
        
    async def test_search_optimization(self, search_magic):
        """検索最適化テスト"""
        search_history = [
            {"query": "python function", "results_count": 150, "execution_time": 0.5},
            {"query": "test cases", "results_count": 80, "execution_time": 0.3},
            {"query": "database query", "results_count": 200, "execution_time": 0.8},
            {"query": "python function", "results_count": 150, "execution_time": 0.4}  # 重複クエリ
        ]
        
        optimization_params = {
            "search_history": search_history,
            "optimization_targets": ["execution_time", "cache_hits", "result_relevance"],
            "cache_strategy": "lru"
        }
        
        result = await search_magic.optimize_search_performance(optimization_params)
        
        assert result["success"] is True
        optimization = result["optimization_result"]
        
        # 最適化結果の確認
        assert "cache_recommendations" in optimization
        assert "query_optimization" in optimization
        assert "performance_improvements" in optimization
        
        # キャッシュ推奨事項の確認
        cache_recs = optimization["cache_recommendations"]
        assert "frequent_queries" in cache_recs
        assert len(cache_recs["frequent_queries"]) > 0
    
    # Phase 5: エラーハンドリング・エッジケース
    async def test_search_magic_invalid_intent(self, search_magic):
        """無効な意図での魔法発動テスト"""
        result = await search_magic.cast_magic("invalid_search_intent", {})
        
        assert result["success"] is False
        assert "Unknown search intent" in result["error"]
        
    async def test_empty_search_query(self, search_magic):
        """空の検索クエリテスト"""
        search_params = {
            "query": "",
            "search_type": "basic_search",
            "targets": []
        }
        
        result = await search_magic.deep_search(search_params)
        
        assert result["success"] is False
        assert "empty" in result["error"].lower()
        
    async def test_large_dataset_search(self, search_magic):
        """大規模データセット検索テスト"""
        # 大量のダミーデータを生成
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                "id": f"doc_{i:04d}",
                "content": f"This is document number {i} with various content patterns and keywords.",
                "category": f"category_{i % 10}"
            })
        
        search_params = {
            "query": "document patterns",
            "documents": large_dataset,
            "search_fields": ["content"],
            "max_results": 50
        }
        
        result = await search_magic.search_knowledge(search_params)
        
        assert result["success"] is True
        search_results = result["search_results"]
        
        # 大規模データセットでも動作することを確認
        ranked_results = search_results["ranked_results"]
        assert len(ranked_results) <= 50  # max_results制限
        assert len(ranked_results) > 0    # 結果は見つかる
        
    async def test_concurrent_search(self, search_magic, sample_knowledge_data):
        """並行検索テスト"""
        # 複数の検索を同時実行
        search_tasks = []
        
        for i in range(5):
            search_params = {
                "query": f"test query {i}",
                "documents": sample_knowledge_data["documents"],
                "search_fields": ["title", "content"]
            }
            task = search_magic.search_knowledge(search_params)
            search_tasks.append(task)
        
        # 並行実行
        results = await asyncio.gather(*search_tasks)
        
        # すべての検索が成功することを確認
        assert len(results) == 5
        for result in results:
            assert result["success"] is True
            assert "search_results" in result


@pytest.mark.asyncio
class TestSearchMagicIntegration:
    """Search Magic統合テスト"""
    
    async def test_comprehensive_search_workflow(self):
        """包括的な検索ワークフローテスト"""
        search_magic = SearchMagic()
        
        # Step 1: パターン発見
        code_content = """
def process_user_data(user_data):
    if not user_data:
        return None
    return user_data.strip().lower()

class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, user):
        self.users.append(user)
"""
        
        pattern_params = {
            "source_code": code_content,
            "pattern_types": ["function_definitions", "class_definitions", "conditional_statements"],
            "analysis_depth": "deep"
        }
        
        pattern_result = await search_magic.discover_patterns(pattern_params)
        assert pattern_result["success"] is True
        
        # Step 2: 知識検索
        knowledge_docs = [
            {
                "id": "kb_001",
                "title": "User Data Processing",
                "content": "Best practices for processing user data include validation, sanitization, and error handling.",
                "category": "development"
            }
        ]
        
        knowledge_params = {
            "query": "user data processing",
            "documents": knowledge_docs,
            "search_fields": ["title", "content"]
        }
        
        knowledge_result = await search_magic.search_knowledge(knowledge_params)
        assert knowledge_result["success"] is True
        
        # Step 3: 統合検索
        multi_modal_params = {
            "query": "user data management",
            "search_modes": [
                {"type": "pattern_search", "patterns": pattern_result["discovered_patterns"]},
                {"type": "knowledge_search", "data": knowledge_docs}
            ],
            "fusion_method": "weighted_ranking"
        }
        
        integration_result = await search_magic.multi_modal_search(multi_modal_params)
        assert integration_result["success"] is True
        
        # 統合結果の確認
        unified_results = integration_result["multi_modal_results"]["unified_results"]
        assert len(unified_results) > 0
        

if __name__ == "__main__":
    pytest.main(["-v", __file__])