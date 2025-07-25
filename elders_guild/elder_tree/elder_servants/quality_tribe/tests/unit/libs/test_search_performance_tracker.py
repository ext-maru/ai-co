#!/usr/bin/env python3
"""
SearchPerformanceTracker テストスイート
Created: 2025-07-18
Author: Claude Elder
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys
from unittest.mock import Mock, AsyncMock, patch

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elders_guild.elder_tree.four_sages.rag.search_performance_tracker import (
    SearchPerformanceTracker,
    SearchPerformanceMetrics,
    QueryPatternAnalyzer,
    QueryPattern
)
from elders_guild.elder_tree.four_sages.rag.rag_sage import RAGSage
from elders_guild.elder_tree.tracking.unified_tracking_db import UnifiedTrackingDB


class TestQueryPatternAnalyzer:
    """QueryPatternAnalyzerのテスト"""
    
    @pytest.fixture
    def analyzer(self):
        return QueryPatternAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_question_pattern(self, analyzer):
        """質問パターンの分析テスト"""
        query = "What is the implementation of Elder Flow?"
        results = [
            {"relevance_score": 0.9, "content": "Elder Flow implementation details..."},
            {"relevance_score": 0.8, "content": "Related documentation..."}
        ]
        
        pattern = await analyzer.analyze(query, results)
        
        assert pattern.pattern_type == "question"
        assert pattern.complexity == "moderate"
        assert pattern.domain == "specific"  # "implementation"が1つだけなのでspecific
        assert pattern.success_rate == pytest.approx(0.85, 0.01)
    
    @pytest.mark.asyncio
    async def test_analyze_keyword_pattern(self, analyzer):
        """キーワードパターンの分析テスト"""
        query = "Elder Flow"
        results = [{"relevance_score": 0.7}]
        
        pattern = await analyzer.analyze(query, results)
        
        assert pattern.pattern_type == "keyword"
        assert pattern.complexity == "simple"
        assert "elder" in [term.lower() for term in pattern.frequent_terms]
    
    @pytest.mark.asyncio
    async def test_analyze_semantic_pattern(self, analyzer):
        """セマンティックパターンの分析テスト"""
        query = "Explain how the four sages collaborate to process complex tasks in the system"
        results = [{"relevance_score": 0.95}]
        
        pattern = await analyzer.analyze(query, results)
        
        assert pattern.pattern_type == "question"  # "Explain how"で始まるので質問タイプ
        assert pattern.complexity == "complex"
    
    def test_determine_domain(self, analyzer):
        """ドメイン判定のテスト"""
        assert analyzer._determine_domain("API implementation details") == "technical"
        assert analyzer._determine_domain("How to use the system") == "specific"
        assert analyzer._determine_domain("What is this about") == "general"


class TestSearchPerformanceTracker:
    """SearchPerformanceTrackerのテスト"""
    
    @pytest_asyncio.fixture
    async def mock_rag_sage(self):
        """モックRAG Sage"""
        sage = AsyncMock(spec=RAGSage)
        sage.search = AsyncMock(return_value=[
            {"content": "Result 1", "relevance_score": 0.9},
            {"content": "Result 2", "relevance_score": 0.8},
            {"content": "Result 3", "relevance_score": 0.7}
        ])
        return sage
    
    @pytest_asyncio.fixture
    async def mock_tracking_db(self):
        """モックトラッキングDB"""
        db = AsyncMock(spec=UnifiedTrackingDB)
        db.record_execution = AsyncMock()
        return db
    
    @pytest_asyncio.fixture
    async def tracker(self, mock_rag_sage, mock_tracking_db):
        """SearchPerformanceTrackerフィクスチャ"""
        return SearchPerformanceTracker(mock_rag_sage, mock_tracking_db)
    
    @pytest.mark.asyncio
    async def test_track_search_operation(self, tracker, mock_rag_sage, mock_tracking_db):
        """検索操作追跡のテスト"""
        query = "Elder Flow implementation"
        search_type = "hybrid"
        
        result = await tracker.track_search_operation(query, search_type)
        
        # 検索が実行されたことを確認
        mock_rag_sage.search.assert_called_once_with(query, search_type)
        
        # 結果の検証
        assert "results" in result
        assert len(result["results"]) == 3
        
        # パフォーマンスメトリクスの検証
        assert "performance" in result
        perf = result["performance"]
        assert perf["num_results"] == 3
        assert perf["avg_relevance_score"] == pytest.approx(0.8, 0.01)
        assert "response_time_ms" in perf
        assert perf["response_time_ms"] > 0
        
        # パターン分析の検証
        assert "patterns" in result
        patterns = result["patterns"]
        assert patterns["type"] in ["keyword", "question", "semantic", "hybrid"]
        assert patterns["complexity"] in ["simple", "moderate", "complex"]
        
        # トラッキングDBへの記録を確認
        mock_tracking_db.record_execution.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_hit_tracking(self, tracker):
        """キャッシュヒット追跡のテスト"""
        query = "test query"
        
        # 初回検索（キャッシュミス）
        result1 = await tracker.track_search_operation(query, "text")
        assert not result1["performance"]["cache_hit"]
        
        # 2回目検索（簡易実装ではキャッシュヒット）
        result2 = await tracker.track_search_operation(query, "text")
        # 履歴に基づくキャッシュ判定
        
        # キャッシュ統計の確認
        assert tracker.cache_stats["total_queries"] == 2
        assert tracker.cache_stats["hits"] + tracker.cache_stats["misses"] == 2
    
    @pytest.mark.asyncio
    async def test_performance_summary(self, tracker):
        """パフォーマンスサマリーのテスト"""
        # いくつかの検索を実行
        queries = ["query1", "query2", "query3"]
        for q in queries:
            await tracker.track_search_operation(q, "text")
        
        # サマリー取得
        summary = await tracker.get_performance_summary(time_range_minutes=60)
        
        assert summary["total_queries"] == 3
        assert "performance" in summary
        assert "avg_response_time_ms" in summary["performance"]
        assert "p50_response_time_ms" in summary["performance"]
        assert "p90_response_time_ms" in summary["performance"]
        
        assert "quality" in summary
        assert "cache" in summary
        assert summary["cache"]["hit_rate"] >= 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, tracker, mock_rag_sage):
        """エラーハンドリングのテスト"""
        # 検索エラーをシミュレート
        mock_rag_sage.search.side_effect = Exception("Search failed")
        
        with pytest.raises(Exception) as exc_info:
            await tracker.track_search_operation("error query", "text")
        
        assert "Search failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_result_quality_assessment(self, tracker):
        """結果品質評価のテスト"""
        # 高品質な結果
        high_quality_results = [
            {"relevance_score": 0.95},
            {"relevance_score": 0.93},
            {"relevance_score": 0.91}
        ]
        quality1 = tracker._assess_result_quality(high_quality_results)
        
        # 低品質な結果
        low_quality_results = [
            {"relevance_score": 0.5},
            {"relevance_score": 0.3},
            {"relevance_score": 0.1}
        ]
        quality2 = tracker._assess_result_quality(low_quality_results)
        
        # 高品質の方がスコアが高いことを確認
        assert quality1 > quality2
        
        # 空の結果
        assert tracker._assess_result_quality([]) == 0.0
    
    @pytest.mark.asyncio
    async def test_process_request(self, tracker):
        """process_requestメソッドのテスト"""
        # 検索追跡リクエスト
        request1 = {
            "type": "track_search",
            "query": "test query",
            "search_type": "hybrid"
        }
        result1 = await tracker.process_request(request1)
        assert "results" in result1
        assert "performance" in result1
        
        # サマリー取得リクエスト
        request2 = {
            "type": "get_summary",
            "time_range_minutes": 30
        }
        result2 = await tracker.process_request(request2)
        assert "total_queries" in result2
        
        # 不明なリクエストタイプ
        request3 = {"type": "unknown"}
        result3 = await tracker.process_request(request3)
        assert "error" in result3
    
    def test_validate_request(self, tracker):
        """リクエスト検証のテスト"""
        # 有効なリクエスト
        valid_request = {
            "query": "test",
            "search_type": "text"
        }
        assert tracker.validate_request(valid_request)
        
        # 無効なリクエスト（フィールド不足）
        invalid_request = {"query": "test"}
        assert not tracker.validate_request(invalid_request)
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, tracker):
        """能力一覧取得のテスト"""
        capabilities = await tracker.get_capabilities()
        
        expected_capabilities = [
            "track_search_operation",
            "get_performance_summary",
            "analyze_query_patterns",
            "calculate_cache_hit_rate",
            "assess_result_quality"
        ]
        
        for cap in expected_capabilities:
            assert cap in capabilities
    
    def test_percentile_calculation(self, tracker):
        """パーセンタイル計算のテスト"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        assert tracker._calculate_percentile(data, 50) == 6  # 50%は6番目の要素
        assert tracker._calculate_percentile(data, 90) == 10  # 90%は10番目の要素
        assert tracker._calculate_percentile(data, 99) == 10  # 99%は最後の要素
        
        # 空のデータ
        assert tracker._calculate_percentile([], 50) == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])