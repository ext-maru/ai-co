#!/usr/bin/env python3
"""
SearchPerformanceTracker - RAG Sage 検索パフォーマンス追跡システム
Created: 2025-07-18
Author: Claude Elder

A2A統合とUnifiedTrackingDBを使用した検索パフォーマンスの追跡と分析
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import json
import statistics

from pathlib import Path
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.elders_legacy import EldersServiceLegacy, enforce_boundary, DomainBoundary
from libs.tracking.unified_tracking_db import UnifiedTrackingDB
from libs.four_sages.rag.rag_sage import RAGSage
from core.lightweight_logger import get_logger

logger = get_logger("search_performance_tracker")


@dataclass
class SearchPerformanceMetrics:
    """検索パフォーマンスメトリクス"""
    query: str
    search_type: str
    response_time_ms: float
    num_results: int
    avg_relevance_score: float
    cache_hit: bool
    timestamp: datetime
    query_length: int
    result_quality: float = 0.0
    user_satisfaction: Optional[float] = None


@dataclass
class QueryPattern:
    """クエリパターン分析結果"""
    pattern_type: str  # "keyword", "question", "semantic", "hybrid"
    complexity: str    # "simple", "moderate", "complex"
    domain: str       # "technical", "general", "specific"
    frequent_terms: List[str] = field(default_factory=list)
    success_rate: float = 0.0


class QueryPatternAnalyzer:
    """クエリパターン分析器"""
    
    def __init__(self):
        self.pattern_cache = {}
        self.term_frequency = {}
        
    async def analyze(self, query: str, results: List[Dict[str, Any]]) -> QueryPattern:
        """クエリパターンを分析"""
        # パターンタイプの判定
        pattern_type = self._determine_pattern_type(query)
        
        # 複雑度の判定
        complexity = self._determine_complexity(query)
        
        # ドメインの判定
        domain = self._determine_domain(query)
        
        # 頻出語句の抽出
        frequent_terms = self._extract_frequent_terms(query)
        
        # 成功率の計算（結果の関連性から）
        success_rate = self._calculate_success_rate(results)
        
        pattern = QueryPattern(
            pattern_type=pattern_type,
            complexity=complexity,
            domain=domain,
            frequent_terms=frequent_terms,
            success_rate=success_rate
        )
        
        # パターンをキャッシュ
        self.pattern_cache[query] = pattern
        
        return pattern
    
    def _determine_pattern_type(self, query: str) -> str:
        """パターンタイプを判定"""
        query_lower = query.lower()
        
        # 質問形式
        if any(q in query_lower for q in ["what", "how", "why", "when", "where", "?"]):
            return "question"
        
        # セマンティック検索（自然言語的）
        if len(query.split()) > 5:
            return "semantic"
        
        # キーワード検索（短い）
        if len(query.split()) <= 2:
            return "keyword"
        
        return "hybrid"
    
    def _determine_complexity(self, query: str) -> str:
        """クエリの複雑度を判定"""
        words = query.split()
        
        if len(words) <= 3:
            return "simple"
        elif len(words) <= 7:
            return "moderate"
        else:
            return "complex"
    
    def _determine_domain(self, query: str) -> str:
        """クエリのドメインを判定"""
        technical_terms = ["api", "function", "class", "method", "implementation", 
                          "algorithm", "database", "system", "architecture"]
        
        query_lower = query.lower()
        tech_count = sum(1 for term in technical_terms if term in query_lower)
        
        if tech_count >= 2:
            return "technical"
        elif tech_count == 1:
            return "specific"
        else:
            return "general"
    
    def _extract_frequent_terms(self, query: str) -> List[str]:
        """頻出語句を抽出"""
        # 簡易的な実装
        words = query.lower().split()
        
        # ストップワードを除外
        stopwords = {"the", "a", "an", "is", "are", "in", "on", "at", "to", "for", 
                    "of", "with", "by", "from", "as", "and", "or", "but"}
        
        meaningful_words = [w for w in words if w not in stopwords and len(w) > 2]
        
        # 頻度をカウント
        for word in meaningful_words:
            self.term_frequency[word] = self.term_frequency.get(word, 0) + 1
        
        # 上位の語句を返す
        return sorted(meaningful_words, key=lambda x: self.term_frequency.get(x, 0), reverse=True)[:5]
    
    def _calculate_success_rate(self, results: List[Dict[str, Any]]) -> float:
        """結果から成功率を計算"""
        if not results:
            return 0.0
        
        # 関連性スコアの平均を成功率とする
        relevance_scores = [r.get("relevance_score", 0) for r in results]
        return statistics.mean(relevance_scores) if relevance_scores else 0.0


class SearchPerformanceTracker(EldersServiceLegacy):
    """検索パフォーマンス追跡システム"""
    
    def __init__(self, rag_sage: RAGSage, tracking_db: UnifiedTrackingDB):
        super().__init__(name="SearchPerformanceTracker")
        self.rag_sage = rag_sage
        self.tracking_db = tracking_db
        self.query_analyzer = QueryPatternAnalyzer()
        self.performance_history = []
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_queries": 0
        }
        logger.info("🔍 SearchPerformanceTracker initialized")
    
    @enforce_boundary(DomainBoundary.EXECUTION, "track_search")
    async def track_search_operation(self, query: str, search_type: str) -> Dict[str, Any]:
        """検索操作を追跡"""
        start_time = time.time()
        self.cache_stats["total_queries"] += 1
        
        try:
            # キャッシュヒットチェック
            cache_hit = await self._check_cache_hit(query)
            if cache_hit:
                self.cache_stats["hits"] += 1
            else:
                self.cache_stats["misses"] += 1
            
            # 検索実行
            results = await self.rag_sage.search(query, search_type)
            
            # パフォーマンスデータ収集
            response_time_ms = (time.time() - start_time) * 1000
            
            performance_data = SearchPerformanceMetrics(
                query=query,
                search_type=search_type,
                response_time_ms=response_time_ms,
                num_results=len(results),
                avg_relevance_score=self._calculate_avg_relevance(results),
                cache_hit=cache_hit,
                timestamp=datetime.now(),
                query_length=len(query),
                result_quality=self._assess_result_quality(results)
            )
            
            # トラッキングDBに記録
            await self._record_to_tracking_db(performance_data)
            
            # クエリパターン分析
            patterns = await self.query_analyzer.analyze(query, results)
            
            # 履歴に追加
            self.performance_history.append(performance_data)
            if len(self.performance_history) > 1000:  # メモリ管理
                self.performance_history.pop(0)
            
            return {
                "results": results,
                "performance": {
                    "response_time_ms": performance_data.response_time_ms,
                    "num_results": performance_data.num_results,
                    "avg_relevance_score": performance_data.avg_relevance_score,
                    "cache_hit": performance_data.cache_hit,
                    "cache_hit_rate": self._calculate_cache_hit_rate()
                },
                "patterns": {
                    "type": patterns.pattern_type,
                    "complexity": patterns.complexity,
                    "domain": patterns.domain,
                    "success_rate": patterns.success_rate
                }
            }
            
        except Exception as e:
            logger.error(f"検索追跡エラー: {e}")
            raise
    
    async def _check_cache_hit(self, query: str) -> bool:
        """キャッシュヒットをチェック"""
        # RAG Sageのキャッシュ機能と連携
        # 簡易実装として、最近のクエリをチェック
        recent_queries = [m.query for m in self.performance_history[-10:]]
        return query in recent_queries
    
    def _calculate_avg_relevance(self, results: List[Dict[str, Any]]) -> float:
        """平均関連性スコアを計算"""
        if not results:
            return 0.0
        
        scores = [r.get("relevance_score", 0) for r in results]
        return statistics.mean(scores) if scores else 0.0
    
    def _assess_result_quality(self, results: List[Dict[str, Any]]) -> float:
        """結果の品質を評価"""
        if not results:
            return 0.0
        
        # 品質指標
        # 1. 関連性スコアの分散（低いほど良い）
        scores = [r.get("relevance_score", 0) for r in results]
        if len(scores) > 1:
            score_variance = statistics.variance(scores)
            variance_factor = 1.0 / (1.0 + score_variance)
        else:
            variance_factor = 1.0
        
        # 2. 上位結果の関連性
        top_relevance = scores[0] if scores else 0
        
        # 3. 結果数の適切さ
        result_count_factor = min(len(results) / 10, 1.0)  # 10件程度が理想
        
        # 総合品質スコア
        quality = (variance_factor * 0.3 + top_relevance * 0.5 + result_count_factor * 0.2)
        
        return quality
    
    def _calculate_cache_hit_rate(self) -> float:
        """キャッシュヒット率を計算"""
        total = self.cache_stats["total_queries"]
        if total == 0:
            return 0.0
        return self.cache_stats["hits"] / total
    
    async def _record_to_tracking_db(self, metrics: SearchPerformanceMetrics) -> None:
        """トラッキングDBに記録"""
        try:
            # UnifiedTrackingDBのexecution記録フォーマットに変換
            execution_data = {
                "task_id": f"rag_search_{int(time.time()*1000)}",
                "task_type": f"rag_search_{metrics.search_type}",
                "status": "completed",
                "start_time": metrics.timestamp.isoformat(),
                "end_time": metrics.timestamp.isoformat(),
                "execution_time": metrics.response_time_ms / 1000,  # 秒に変換
                "quality_score": metrics.result_quality,
                "metadata": {
                    "query": metrics.query,
                    "num_results": metrics.num_results,
                    "avg_relevance": metrics.avg_relevance_score,
                    "cache_hit": metrics.cache_hit,
                    "query_length": metrics.query_length
                }
            }
            
            await self.tracking_db.record_execution(execution_data)
            
        except Exception as e:
            logger.error(f"トラッキングDB記録エラー: {e}")
    
    async def get_performance_summary(self, time_range_minutes: int = 60) -> Dict[str, Any]:
        """パフォーマンスサマリーを取得"""
        recent_metrics = [
            m for m in self.performance_history 
            if (datetime.now() - m.timestamp).seconds < time_range_minutes * 60
        ]
        
        if not recent_metrics:
            return {"error": "No recent data available"}
        
        response_times = [m.response_time_ms for m in recent_metrics]
        relevance_scores = [m.avg_relevance_score for m in recent_metrics]
        
        return {
            "time_range_minutes": time_range_minutes,
            "total_queries": len(recent_metrics),
            "performance": {
                "avg_response_time_ms": statistics.mean(response_times),
                "p50_response_time_ms": statistics.median(response_times),
                "p90_response_time_ms": self._calculate_percentile(response_times, 90),
                "p99_response_time_ms": self._calculate_percentile(response_times, 99),
            },
            "quality": {
                "avg_relevance_score": statistics.mean(relevance_scores),
                "avg_result_count": statistics.mean([m.num_results for m in recent_metrics]),
            },
            "cache": {
                "hit_rate": self._calculate_cache_hit_rate(),
                "total_hits": self.cache_stats["hits"],
                "total_misses": self.cache_stats["misses"]
            },
            "patterns": self._analyze_query_patterns(recent_metrics)
        }
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """パーセンタイルを計算"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        
        if index >= len(sorted_data):
            return sorted_data[-1]
        
        return sorted_data[index]
    
    def _analyze_query_patterns(self, metrics: List[SearchPerformanceMetrics]) -> Dict[str, Any]:
        """クエリパターンを分析"""
        if not metrics:
            return {}
        
        # 検索タイプ別の分析
        search_types = {}
        for m in metrics:
            if m.search_type not in search_types:
                search_types[m.search_type] = {
                    "count": 0,
                    "avg_response_time": 0,
                    "avg_relevance": 0
                }
            
            search_types[m.search_type]["count"] += 1
        
        # 平均値の計算
        for search_type in search_types:
            type_metrics = [m for m in metrics if m.search_type == search_type]
            search_types[search_type]["avg_response_time"] = statistics.mean(
                [m.response_time_ms for m in type_metrics]
            )
            search_types[search_type]["avg_relevance"] = statistics.mean(
                [m.avg_relevance_score for m in type_metrics]
            )
        
        return {
            "by_search_type": search_types,
            "query_complexity": {
                "avg_length": statistics.mean([m.query_length for m in metrics]),
                "max_length": max([m.query_length for m in metrics]),
                "min_length": min([m.query_length for m in metrics])
            }
        }
    
    async def get_capabilities(self) -> List[str]:
        """能力一覧を取得"""
        return [
            "track_search_operation",
            "get_performance_summary",
            "analyze_query_patterns",
            "calculate_cache_hit_rate",
            "assess_result_quality"
        ]
    
    def validate_request(self, request: Dict[str, Any]) -> bool:
        """リクエストを検証"""
        required_fields = ["query", "search_type"]
        return all(field in request for field in required_fields)
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """リクエストを処理"""
        request_type = request.get("type", "track_search")
        
        if request_type == "track_search":
            return await self.track_search_operation(
                query=request["query"],
                search_type=request["search_type"]
            )
        elif request_type == "get_summary":
            time_range = request.get("time_range_minutes", 60)
            return await self.get_performance_summary(time_range)
        else:
            return {"error": f"Unknown request type: {request_type}"}