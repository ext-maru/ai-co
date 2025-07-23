#!/usr/bin/env python3
"""
Cache Optimization Engine - キャッシュ最適化エンジン
Created: 2025-07-19
Author: Claude Elder
"""

import asyncio
import hashlib
import json
import logging
import pickle
import sys
import threading
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.elders_legacy import DomainBoundary, EldersServiceLegacy, enforce_boundary
from core.lightweight_logger import get_logger
from libs.tracking.unified_tracking_db import UnifiedTrackingDB

logger = get_logger("cache_optimization_engine")


@dataclass
class CacheEntry:
    """キャッシュエントリ"""

    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    hit_count: int = 0
    size_bytes: int = 0
    ttl: Optional[int] = None
    priority: float = 0.0


@dataclass
class CacheMetrics:
    """キャッシュメトリクス"""

    hit_rate: float = 0.0
    miss_rate: float = 0.0
    eviction_rate: float = 0.0
    memory_usage: float = 0.0
    average_access_time: float = 0.0
    total_requests: int = 0
    total_hits: int = 0
    total_misses: int = 0


@dataclass
class OptimizationStrategy:
    """最適化戦略"""

    strategy_name: str
    max_size: int
    ttl_seconds: int
    eviction_policy: str
    prefetch_enabled: bool = False
    compression_enabled: bool = False
    predicted_hit_rate: float = 0.0


class LRUCache:
    """LRU + 予測キャッシュ"""

    def __init__(self, max_size:
        """初期化メソッド"""
    int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.access_patterns = defaultdict(int)
        self.prediction_model = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """キー取得"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                entry.hit_count += 1
                # LRUで最新に移動
                self.cache.move_to_end(key)
                return entry.value
            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None):
        """キー設定"""
        with self.lock:
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl=ttl,
                size_bytes=len(pickle.dumps(value)),
            )

            if key in self.cache:
                self.cache[key] = entry
                self.cache.move_to_end(key)
            else:
                self.cache[key] = entry

            # サイズ制限チェック
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def predict_next_access(self, current_key: str) -> List[str]:
        """次のアクセス予測"""
        # 簡易予測モデル
        if current_key in self.prediction_model:
            return self.prediction_model[current_key][:5]
        return []

    def update_prediction_model(self, access_sequence: List[str]):
        """予測モデル更新"""
        for i in range(len(access_sequence) - 1):
            current = access_sequence[i]
            next_key = access_sequence[i + 1]

            if current not in self.prediction_model:
                self.prediction_model[current] = []

            if next_key not in self.prediction_model[current]:
                self.prediction_model[current].append(next_key)


class CacheOptimizationEngine(EldersServiceLegacy):
    """キャッシュ最適化エンジン"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="CacheOptimizationEngine")
        self.tracking_db = UnifiedTrackingDB()
        self.cache_instances = {}
        self.optimization_strategies = {}
        self.metrics = CacheMetrics()
        self.access_log = []
        self._initialize_components()

    def _initialize_components(self):
        """コンポーネント初期化"""
        self.default_cache = LRUCache(max_size=1000)
        self.cache_instances["default"] = self.default_cache

        # デフォルト最適化戦略
        self.optimization_strategies["default"] = OptimizationStrategy(
            strategy_name="default",
            max_size=1000,
            ttl_seconds=3600,
            eviction_policy="lru",
            prefetch_enabled=True,
            compression_enabled=False,
        )

        logger.info("⚡ Cache Optimization Engine初期化完了")

    @enforce_boundary(DomainBoundary.EXECUTION, "optimize_cache")
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """キャッシュ最適化処理"""
        try:
            action = request.get("action", "optimize")

            if action == "optimize":
                return await self._optimize_cache(request)
            elif action == "analyze":
                return await self._analyze_cache_usage(request)
            elif action == "tune":
                return await self._tune_cache_parameters(request)
            elif action == "prefetch":
                return await self._execute_prefetch(request)
            elif action == "metrics":
                return await self._get_cache_metrics(request)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"キャッシュ最適化エラー: {e}")
            return {"error": str(e)}

    async def _optimize_cache(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """キャッシュ最適化実行"""
        cache_name = request.get("cache_name", "default")
        usage_data = request.get("usage_data", {})

        logger.info(f"⚡ キャッシュ最適化開始: {cache_name}")

        # 1. 使用状況分析
        usage_analysis = await self._analyze_usage_patterns(cache_name, usage_data)

        # 2. 最適化戦略決定
        optimal_strategy = await self._determine_optimal_strategy(usage_analysis)

        # 3. キャッシュ設定適用
        optimization_result = await self._apply_optimization_strategy(
            cache_name, optimal_strategy
        )

        # 4. プリフェッチ実行
        if optimal_strategy.prefetch_enabled:
            prefetch_result = await self._execute_prefetch(
                {"cache_name": cache_name, "strategy": optimal_strategy}
            )
            optimization_result["prefetch"] = prefetch_result

        # 5. メトリクス更新
        await self._update_optimization_metrics(cache_name, optimal_strategy)

        return {
            "cache_name": cache_name,
            "optimization_strategy": optimal_strategy.__dict__,
            "optimization_result": optimization_result,
            "usage_analysis": usage_analysis,
            "estimated_improvement": usage_analysis.get("estimated_improvement", 0),
        }

    async def _analyze_usage_patterns(
        self, cache_name: str, usage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用パターン分析"""
        cache = self.cache_instances.get(cache_name, self.default_cache)

        # アクセスパターン分析
        access_frequency = defaultdict(int)
        access_times = defaultdict(list)

        for entry in cache.cache.values():
            access_frequency[entry.key] = entry.access_count
            access_times[entry.key].append(entry.last_accessed)

        # 統計計算
        total_accesses = sum(access_frequency.values())
        avg_access_frequency = (
            total_accesses / len(access_frequency) if access_frequency else 0
        )

        # ホットキー特定
        hot_keys = sorted(access_frequency.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        # 時間的パターン分析
        temporal_patterns = self._analyze_temporal_patterns(access_times)

        # メモリ使用量分析
        memory_usage = sum(entry.size_bytes for entry in cache.cache.values())

        analysis = {
            "total_entries": len(cache.cache),
            "total_accesses": total_accesses,
            "avg_access_frequency": avg_access_frequency,
            "hot_keys": hot_keys,
            "temporal_patterns": temporal_patterns,
            "memory_usage_bytes": memory_usage,
            "estimated_improvement": self._estimate_improvement_potential(
                access_frequency, temporal_patterns
            ),
        }

        logger.info(f"📊 使用パターン分析完了: {len(hot_keys)}個のホットキー検出")
        return analysis

    async def _determine_optimal_strategy(
        self, usage_analysis: Dict[str, Any]
    ) -> OptimizationStrategy:
        """最適化戦略決定"""
        total_entries = usage_analysis.get("total_entries", 0)
        memory_usage = usage_analysis.get("memory_usage_bytes", 0)
        hot_keys = usage_analysis.get("hot_keys", [])

        # 基本戦略決定
        if total_entries < 100:
            # 小規模キャッシュ
            strategy = OptimizationStrategy(
                strategy_name="small_cache",
                max_size=500,
                ttl_seconds=7200,
                eviction_policy="lru",
                prefetch_enabled=False,
                compression_enabled=False,
            )
        elif total_entries < 1000:
            # 中規模キャッシュ
            strategy = OptimizationStrategy(
                strategy_name="medium_cache",
                max_size=2000,
                ttl_seconds=3600,
                eviction_policy="lru",
                prefetch_enabled=True,
                compression_enabled=False,
            )
        else:
            # 大規模キャッシュ
            strategy = OptimizationStrategy(
                strategy_name="large_cache",
                max_size=5000,
                ttl_seconds=1800,
                eviction_policy="lru",
                prefetch_enabled=True,
                compression_enabled=True,
            )

        # ホットキー数に基づく調整
        if len(hot_keys) > 50:
            strategy.prefetch_enabled = True
            strategy.max_size = int(strategy.max_size * 1.2)

        # メモリ使用量に基づく調整
        if memory_usage > 100 * 1024 * 1024:  # 100MB
            strategy.compression_enabled = True
            strategy.ttl_seconds = int(strategy.ttl_seconds * 0.8)

        # 予測ヒット率計算
        strategy.predicted_hit_rate = self._predict_hit_rate(usage_analysis, strategy)

        return strategy

    async def _apply_optimization_strategy(
        self, cache_name: str, strategy: OptimizationStrategy
    ) -> Dict[str, Any]:
        """最適化戦略適用"""
        cache = self.cache_instances.get(cache_name, self.default_cache)

        # キャッシュサイズ調整
        if cache.max_size != strategy.max_size:
            old_size = cache.max_size
            cache.max_size = strategy.max_size

            # サイズ超過時の調整
            if len(cache.cache) > strategy.max_size:
                excess = len(cache.cache) - strategy.max_size
                for _ in range(excess):
                    cache.cache.popitem(last=False)

        # 戦略を保存
        self.optimization_strategies[cache_name] = strategy

        result = {
            "cache_size_adjusted": True,
            "old_max_size": old_size if "old_size" in locals() else cache.max_size,
            "new_max_size": strategy.max_size,
            "strategy_applied": strategy.strategy_name,
            "current_entries": len(cache.cache),
        }

        logger.info(f"⚡ 最適化戦略適用完了: {strategy.strategy_name}")
        return result

    async def _execute_prefetch(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """プリフェッチ実行"""
        cache_name = request.get("cache_name", "default")
        strategy = request.get("strategy")

        if not strategy or not strategy.prefetch_enabled:
            return {"prefetch_enabled": False}

        cache = self.cache_instances.get(cache_name, self.default_cache)

        # アクセスログから予測
        recent_accesses = self.access_log[-100:] if self.access_log else []

        # 予測キー取得
        predicted_keys = []
        for access in recent_accesses:
            predictions = cache.predict_next_access(access)
            predicted_keys.extend(predictions)

        # 重複除去と優先度付け
        unique_predictions = list(set(predicted_keys))

        prefetch_count = 0
        for key in unique_predictions[:10]:  # 上位10個をプリフェッチ
            if key not in cache.cache:
                # 実際のプリフェッチ処理（ここでは模擬）
                prefetch_count += 1

        result = {
            "prefetch_enabled": True,
            "predicted_keys": len(unique_predictions),
            "prefetch_executed": prefetch_count,
        }

        logger.info(f"📥 プリフェッチ実行完了: {prefetch_count}個のキー")
        return result

    async def _get_cache_metrics(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """キャッシュメトリクス取得"""
        cache_name = request.get("cache_name", "default")
        cache = self.cache_instances.get(cache_name, self.default_cache)

        # メトリクス計算
        total_entries = len(cache.cache)
        total_hits = sum(entry.hit_count for entry in cache.cache.values())
        total_accesses = sum(entry.access_count for entry in cache.cache.values())

        hit_rate = total_hits / total_accesses if total_accesses > 0 else 0
        memory_usage = sum(entry.size_bytes for entry in cache.cache.values())

        metrics = {
            "cache_name": cache_name,
            "total_entries": total_entries,
            "hit_rate": hit_rate,
            "miss_rate": 1 - hit_rate,
            "memory_usage_bytes": memory_usage,
            "memory_usage_mb": memory_usage / 1024 / 1024,
            "total_hits": total_hits,
            "total_accesses": total_accesses,
            "average_entry_size": (
                memory_usage / total_entries if total_entries > 0 else 0
            ),
        }

        return metrics

    def _analyze_temporal_patterns(
        self, access_times: Dict[str, List[datetime]]
    ) -> Dict[str, Any]:
        """時間的パターン分析"""
        patterns = {
            "peak_hours": [],
            "access_frequency_distribution": {},
            "temporal_clustering": {},
        }

        # 時間帯別アクセス分析
        hour_counts = defaultdict(int)
        for key, times in access_times.items():
            for time in times:
                hour_counts[time.hour] += 1

        # ピーク時間帯特定
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        patterns["peak_hours"] = sorted_hours[:3]

        return patterns

    def _estimate_improvement_potential(
        self, access_frequency: Dict[str, int], temporal_patterns: Dict[str, Any]
    ) -> float:
        """改善可能性推定"""
        # 基本改善可能性
        base_improvement = 0.1

        # アクセス頻度の偏りに基づく改善
        if access_frequency:
            frequencies = list(access_frequency.values())
            max_freq = max(frequencies)
            min_freq = min(frequencies)

            if max_freq > min_freq * 10:  # 10倍以上の差
                base_improvement += 0.15

        # 時間的パターンに基づく改善
        if temporal_patterns.get("peak_hours"):
            base_improvement += 0.1

        return min(base_improvement, 0.5)  # 最大50%改善

    def _predict_hit_rate(
        self, usage_analysis: Dict[str, Any], strategy: OptimizationStrategy
    ) -> float:
        """ヒット率予測"""
        current_hit_rate = 0.7  # 現在のヒット率（推定）

        # 戦略に基づく改善予測
        improvements = 0

        if strategy.prefetch_enabled:
            improvements += 0.1

        if strategy.max_size > 1000:
            improvements += 0.05

        if strategy.compression_enabled:
            improvements += 0.03

        predicted_rate = min(current_hit_rate + improvements, 0.95)
        return predicted_rate

    async def _analyze_cache_usage(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """キャッシュ使用状況分析"""
        cache_name = request.get("cache_name", "default")

        # 使用状況分析実行
        usage_analysis = await self._analyze_usage_patterns(cache_name, {})

        # 推奨事項生成
        recommendations = self._generate_recommendations(usage_analysis)

        return {
            "cache_name": cache_name,
            "usage_analysis": usage_analysis,
            "recommendations": recommendations,
        }

    async def _tune_cache_parameters(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """キャッシュパラメータチューニング"""
        cache_name = request.get("cache_name", "default")
        parameters = request.get("parameters", {})

        # パラメータ適用
        cache = self.cache_instances.get(cache_name, self.default_cache)

        if "max_size" in parameters:
            cache.max_size = parameters["max_size"]

        return {
            "cache_name": cache_name,
            "tuned_parameters": parameters,
            "status": "applied",
        }

    async def _update_optimization_metrics(
        self, cache_name: str, strategy: OptimizationStrategy
    ):
        """最適化メトリクス更新"""
        metrics_record = {
            "timestamp": datetime.now().isoformat(),
            "cache_name": cache_name,
            "strategy": strategy.__dict__,
            "optimization_type": "cache_optimization",
        }

        await self.tracking_db.save_search_record(metrics_record)

    def _generate_recommendations(self, usage_analysis: Dict[str, Any]) -> List[str]:
        """推奨事項生成"""
        recommendations = []

        memory_usage = usage_analysis.get("memory_usage_bytes", 0)
        hot_keys = usage_analysis.get("hot_keys", [])

        if memory_usage > 50 * 1024 * 1024:  # 50MB
            recommendations.append("メモリ使用量が多いため、圧縮を有効化することを推奨")

        if len(hot_keys) > 20:
            recommendations.append(
                "ホットキーが多いため、プリフェッチを有効化することを推奨"
            )

        if usage_analysis.get("estimated_improvement", 0) > 0.2:
            recommendations.append(
                "大幅な改善が見込まれるため、キャッシュサイズの拡張を推奨"
            )

        return recommendations

    def validate_request(self, request: Dict[str, Any]) -> bool:
        """リクエスト検証"""
        return isinstance(request, dict) and "action" in request

    def get_capabilities(self) -> List[str]:
        """機能一覧"""
        return [
            "cache_optimization",
            "usage_analysis",
            "parameter_tuning",
            "prefetch_execution",
            "metrics_collection",
            "performance_prediction",
        ]


# エクスポート用のファクトリ関数
def create_cache_optimization_engine() -> CacheOptimizationEngine:
    """Cache Optimization Engine作成"""
    return CacheOptimizationEngine()


if __name__ == "__main__":
    # テスト実行
    async def test_cache_optimizer():
        """test_cache_optimizerテストメソッド"""
        optimizer = create_cache_optimization_engine()

        # テストキャッシュ最適化
        result = await optimizer.process_request(
            {
                "action": "optimize",
                "cache_name": "test_cache",
                "usage_data": {
                    "total_requests": 1000,
                    "cache_hits": 700,
                    "memory_usage": 50 * 1024 * 1024,
                },
            }
        )

        print(f"キャッシュ最適化結果: {result}")

    asyncio.run(test_cache_optimizer())
