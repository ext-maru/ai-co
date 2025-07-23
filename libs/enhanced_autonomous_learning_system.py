#!/usr/bin/env python3
"""
Enhanced Autonomous Learning System - 強化版自律学習システム
エルダーズギルド AI自動化タスク - 自律学習アルゴリズム改善実装

機能強化:
- 適応型学習率調整
- 動的パターン重要度評価
- リアルタイム性能最適化
- 予測的インシデント回避
- メタ学習による自己改善
"""

import asyncio
import secrets
import json
import logging
import sqlite3
import statistics
from collections import defaultdict
from collections import deque
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import numpy as np

from .four_sages_integration import FourSagesIntegration

logger = logging.getLogger(__name__)


@dataclass
class EnhancedLearningPattern:
    """強化版学習パターン"""

    pattern_id: str
    pattern_type: str
    context: Dict[str, Any]
    success_rate: float
    usage_count: int
    importance_score: float = 0.5
    adaptation_rate: float = 0.1
    confidence_interval: Tuple[float, float] = (0.0, 1.0)
    last_performance: Optional[float] = None
    trend_direction: str = "stable"  # improving, declining, stable
    meta_features: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def update_performance(self, success: bool, context_similarity: float = 1.0):
        """パフォーマンス更新 - 文脈類似度を考慮"""
        # 適応型学習率（類似度に基づく）
        effective_learning_rate = self.adaptation_rate * context_similarity

        # 成功率更新（指数移動平均）
        old_success_rate = self.success_rate
        self.success_rate = (
            1 - effective_learning_rate
        ) * self.success_rate + effective_learning_rate * (1.0 if success else 0.0)

        # 使用回数と最終パフォーマンス更新
        self.usage_count += 1
        self.last_performance = 1.0 if success else 0.0

        # トレンド方向の判定
        if self.last_performance is not None:
            if self.success_rate > old_success_rate:
                self.trend_direction = "improving"
            elif self.success_rate < old_success_rate:
                self.trend_direction = "declining"
            else:
                self.trend_direction = "stable"

        # 信頼区間の更新（ベイズ推定）
        self._update_confidence_interval()

        # 重要度スコアの動的調整
        self._update_importance_score()

        self.last_updated = datetime.now()

    def _update_confidence_interval(self):
        """信頼区間の更新（ベータ分布ベース）"""
        if self.usage_count > 10:
            # ベータ分布のパラメータ
            alpha = self.success_rate * self.usage_count + 1
            beta = (1 - self.success_rate) * self.usage_count + 1

            # 95%信頼区間の近似計算
            mean = alpha / (alpha + beta)
            variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
            std_dev = np.sqrt(variance)

            # 信頼区間（正規近似）
            margin = 1.96 * std_dev
            self.confidence_interval = (
                max(0.0, mean - margin),
                min(1.0, mean + margin),
            )

    def _update_importance_score(self):
        """重要度スコアの動的更新"""
        # 基本重要度（成功率ベース）
        base_importance = self.success_rate

        # 使用頻度ボーナス
        frequency_bonus = min(0.2, self.usage_count / 100.0)

        # トレンドボーナス/ペナルティ
        trend_modifier = {"improving": 0.1, "stable": 0.0, "declining": -0.1}.get(
            self.trend_direction, 0.0
        )

        # 信頼度ボーナス（信頼区間の狭さ）
        interval_width = self.confidence_interval[1] - self.confidence_interval[0]
        confidence_bonus = max(0.0, 0.1 * (1.0 - interval_width))

        self.importance_score = min(
            1.0,
            max(
                0.0,
                base_importance + frequency_bonus + trend_modifier + confidence_bonus,
            ),
        )

    def predict_success_probability(self, context_features: Dict[str, Any]) -> float:
        """文脈特徴量に基づく成功確率予測"""
        # 基本成功確率
        base_prob = self.success_rate

        # 文脈類似度の計算
        context_similarity = self._calculate_context_similarity(context_features)

        # 類似度に基づく調整
        adjusted_prob = base_prob * (0.5 + 0.5 * context_similarity)

        return min(1.0, max(0.0, adjusted_prob))

    def _calculate_context_similarity(self, new_context: Dict[str, Any]) -> float:
        """文脈類似度の計算"""
        if not self.context or not new_context:
            return 0.5

        # 共通キーの割合
        common_keys = set(self.context.keys()) & set(new_context.keys())
        all_keys = set(self.context.keys()) | set(new_context.keys())

        if not all_keys:
            return 1.0

        key_similarity = len(common_keys) / len(all_keys)

        # 値の類似度（共通キーについて）
        value_similarities = []
        for key in common_keys:
            if self.context[key] == new_context[key]:
                value_similarities.append(1.0)
            elif isinstance(self.context[key], (int, float)) and isinstance(
                new_context[key], (int, float)
            ):
                # 数値の場合は相対差で計算
                diff = abs(self.context[key] - new_context[key])
                max_val = max(abs(self.context[key]), abs(new_context[key]), 1)
                value_similarities.append(1.0 - min(1.0, diff / max_val))
            else:
                value_similarities.append(0.0)

        value_similarity = (
            statistics.mean(value_similarities) if value_similarities else 0.5
        )

        # 総合類似度
        return 0.6 * key_similarity + 0.4 * value_similarity


@dataclass
class LearningMetrics:
    """学習メトリクス追跡"""

    total_patterns: int = 0
    active_patterns: int = 0
    successful_predictions: int = 0
    failed_predictions: int = 0
    average_confidence: float = 0.0
    learning_velocity: float = 0.0  # パターン/時間
    adaptation_efficiency: float = 0.0
    meta_learning_score: float = 0.0

    def update_from_predictions(self, predictions: List[Tuple[bool, float]]):
        """予測結果からメトリクス更新"""
        if predictions:
            successes = sum(1 for success, _ in predictions if success)
            self.successful_predictions += successes
            self.failed_predictions += len(predictions) - successes

            confidences = [conf for _, conf in predictions]
            self.average_confidence = statistics.mean(confidences)

    def calculate_accuracy(self) -> float:
        """予測精度計算"""
        total = self.successful_predictions + self.failed_predictions
        if total == 0:
            return 0.0
        return self.successful_predictions / total


class EnhancedAutonomousLearningSystem:
    """強化版自律学習システム"""

    def __init__(self, learning_config: Optional[Dict[str, Any]] = None):
        """初期化メソッド"""
        self.four_sages = FourSagesIntegration()

        # 学習データベース
        self.db_path = Path("data/enhanced_learning.db")
        self.knowledge_base_path = Path("knowledge_base/enhanced_learning")
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)

        # 学習パターン管理
        self.learning_patterns: Dict[str, EnhancedLearningPattern] = {}
        self.pattern_clusters: Dict[str, List[str]] = defaultdict(list)
        self.performance_history: deque = deque(maxlen=1000)

        # 学習設定（デフォルト）
        default_config = {
            "min_pattern_confidence": 0.6,
            "adaptation_learning_rate": 0.1,
            "importance_threshold": 0.3,
            "meta_learning_enabled": True,
            "real_time_optimization": True,
            "predictive_mode": True,
            "clustering_enabled": True,
            "performance_target": 0.85,
        }

        self.config = {**default_config, **(learning_config or {})}

        # メトリクス追跡
        self.metrics = LearningMetrics()
        self.meta_learning_state = {
            "learning_rate_history": deque(maxlen=100),
            "performance_trends": deque(maxlen=50),
            "optimal_parameters": {},
            "adaptation_success_rate": 0.5,
        }

        # リアルタイム最適化
        self.optimization_queue = deque(maxlen=100)
        self.performance_targets = {
            "accuracy": self.config["performance_target"],
            "learning_speed": 0.1,  # パターン/秒
            "adaptation_rate": 0.05,
        }

        self._init_database()
        logger.info("Enhanced Autonomous Learning System initialized")

    def _init_database(self):
        """強化版データベース初期化"""
        self.db_path.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 強化版学習パターンテーブル
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS enhanced_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT UNIQUE,
            pattern_type TEXT,
            context TEXT,
            success_rate REAL,
            usage_count INTEGER,
            importance_score REAL,
            adaptation_rate REAL,
            confidence_interval_low REAL,
            confidence_interval_high REAL,
            trend_direction TEXT,
            meta_features TEXT,
            created_at TIMESTAMP,
            last_updated TIMESTAMP
        )
        """
        )

        # メタ学習履歴テーブル
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS meta_learning_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            learning_rate REAL,
            performance_score REAL,
            adaptation_efficiency REAL,
            active_patterns INTEGER,
            meta_parameters TEXT
        )
        """
        )

        # 予測履歴テーブル
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id TEXT,
            predicted_success_prob REAL,
            actual_success BOOLEAN,
            context_features TEXT,
            prediction_accuracy REAL,
            timestamp TIMESTAMP
        )
        """
        )

        conn.commit()
        conn.close()

    async def start_enhanced_learning(self):
        """強化版自律学習開始"""
        logger.info("🚀 Starting Enhanced Autonomous Learning System")

        # 並行学習タスク
        await asyncio.gather(
            self._adaptive_pattern_learning_loop(),
            self._real_time_optimization_loop(),
            self._meta_learning_loop(),
            self._predictive_analysis_loop(),
            self._performance_monitoring_loop(),
        )

    async def _adaptive_pattern_learning_loop(self):
        """適応型パターン学習ループ"""
        while True:
            try:
                # 動的学習率調整
                self._adjust_learning_rates()

                # 新しいパターンの発見
                await self._discover_new_patterns()

                # パターンの重要度評価と更新
                await self._evaluate_pattern_importance()

                # パターンクラスタリング
                if self.config["clustering_enabled"]:
                    self._cluster_similar_patterns()

                # 低重要度パターンの削除
                self._prune_low_importance_patterns()

                await asyncio.sleep(60)  # 1分間隔

            except Exception as e:
                logger.error(f"Adaptive pattern learning error: {e}")
                await asyncio.sleep(30)

    async def _real_time_optimization_loop(self):
        """リアルタイム最適化ループ"""
        while True:
            try:
                if not self.config["real_time_optimization"]:
                    await asyncio.sleep(60)
                    continue

                # パフォーマンスメトリクス収集
                current_performance = self._collect_current_performance()

                # 最適化機会の特定
                optimization_opportunities = self._identify_optimization_opportunities(
                    current_performance
                )

                # リアルタイム調整実行
                for opportunity in optimization_opportunities:
                    await self._apply_real_time_optimization(opportunity)

                await asyncio.sleep(30)  # 30秒間隔

            except Exception as e:
                logger.error(f"Real-time optimization error: {e}")
                await asyncio.sleep(30)

    async def _meta_learning_loop(self):
        """メタ学習ループ"""
        while True:
            try:
                if not self.config["meta_learning_enabled"]:
                    await asyncio.sleep(300)
                    continue

                # 学習プロセス自体の分析
                learning_analysis = self._analyze_learning_process()

                # 最適学習パラメータの発見
                optimal_params = self._discover_optimal_parameters(learning_analysis)

                # 学習戦略の適応
                if self._validate_parameter_improvement(optimal_params):
                    self._apply_meta_learning_insights(optimal_params)

                # メタ学習履歴の記録
                await self._record_meta_learning_session(
                    learning_analysis, optimal_params
                )

                await asyncio.sleep(300)  # 5分間隔

            except Exception as e:
                logger.error(f"Meta-learning error: {e}")
                await asyncio.sleep(60)

    async def _predictive_analysis_loop(self):
        """予測分析ループ"""
        while True:
            try:
                if not self.config["predictive_mode"]:
                    await asyncio.sleep(120)
                    continue

                # 将来のパフォーマンス予測
                performance_predictions = self._predict_future_performance()

                # 潜在的問題の早期発見
                potential_issues = self._detect_potential_issues(
                    performance_predictions
                )

                # 予防的対策の提案・実行
                for issue in potential_issues:
                    await self._apply_preventive_measures(issue)

                # 予測精度の追跡
                self._track_prediction_accuracy()

                await asyncio.sleep(120)  # 2分間隔

            except Exception as e:
                logger.error(f"Predictive analysis error: {e}")
                await asyncio.sleep(60)

    async def _performance_monitoring_loop(self):
        """パフォーマンス監視ループ"""
        while True:
            try:
                # 学習システム自体のパフォーマンス測定
                system_metrics = self._measure_system_performance()

                # メトリクス更新
                self._update_learning_metrics(system_metrics)

                # パフォーマンス履歴記録
                self.performance_history.append(
                    {
                        "timestamp": datetime.now(),
                        "metrics": system_metrics,
                        "active_patterns": len(self.learning_patterns),
                        "accuracy": self.metrics.calculate_accuracy(),
                    }
                )

                # アラート検出
                alerts = self._detect_performance_alerts(system_metrics)
                if alerts:
                    await self._handle_performance_alerts(alerts)

                await asyncio.sleep(60)  # 1分間隔

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)

    # 学習メソッド実装

    def _adjust_learning_rates(self):
        """動的学習率調整"""
        # 最近のパフォーマンストレンドに基づく調整
        recent_performance = list(self.performance_history)[-10:]

        if len(recent_performance) >= 5:
            # パフォーマンストレンド分析
            accuracies = [p["accuracy"] for p in recent_performance]
            trend = self._calculate_trend(accuracies)

            # 学習率調整
            for pattern in self.learning_patterns.values():
                if trend > 0.05:  # 改善傾向
                    pattern.adaptation_rate = min(0.3, pattern.adaptation_rate * 1.1)
                elif trend < -0.05:  # 悪化傾向
                    pattern.adaptation_rate = max(0.01, pattern.adaptation_rate * 0.9)
                # else: 安定傾向は現状維持

    def _calculate_trend(self, values: List[float]) -> float:
        """値の傾向計算（線形回帰の傾き）"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))

        # 線形回帰の傾きを計算
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    async def _discover_new_patterns(self) -> List[EnhancedLearningPattern]:
        """新しいパターンの発見"""
        # Four Sagesから学習データを取得
        learning_data = await self._collect_sage_learning_data()

        new_patterns = []
        for data in learning_data:
            # パターン候補の生成
            pattern_candidate = self._generate_pattern_candidate(data)

            # 既存パターンとの重複チェック
            if not self._is_duplicate_pattern(pattern_candidate):
                new_pattern = EnhancedLearningPattern(
                    pattern_id=f"pattern_{datetime.now().timestamp()}_{len(new_patterns)}",
                    pattern_type=data.get("type", "general"),
                    context=data.get("context", {}),
                    success_rate=data.get("initial_success_rate", 0.5),
                    usage_count=1,
                    adaptation_rate=self.config["adaptation_learning_rate"],
                )

                self.learning_patterns[new_pattern.pattern_id] = new_pattern
                new_patterns.append(new_pattern)

        return new_patterns

    async def _collect_sage_learning_data(self) -> List[Dict[str, Any]]:
        """賢者から学習データ収集"""
        # 各賢者から最近の活動データを収集
        sage_data = []

        for sage_name in ["knowledge_sage", "task_sage", "incident_sage", "rag_sage"]:
            try:
                # 賢者固有のデータ収集（モック実装）
                sage_specific_data = self._collect_sage_specific_data(sage_name)
                sage_data.extend(sage_specific_data)
            except Exception as e:
                logger.warning(f"Failed to collect data from {sage_name}: {e}")

        return sage_data

    def _collect_sage_specific_data(self, sage_name: str) -> List[Dict[str, Any]]:
        """賢者固有データ収集（モック実装）"""
        import random

        # 賢者別のデータパターン
        sage_patterns = {
            "knowledge_sage": [
                {
                    "type": "knowledge_pattern",
                    "context": {"domain": "api_optimization"},
                    "initial_success_rate": 0.8,
                },
                {
                    "type": "learning_pattern",
                    "context": {"method": "incremental"},
                    "initial_success_rate": 0.75,
                },
            ],
            "task_sage": [
                {
                    "type": "task_optimization",
                    "context": {"priority": "high"},
                    "initial_success_rate": 0.85,
                },
                {
                    "type": "workflow_pattern",
                    "context": {"parallel": True},
                    "initial_success_rate": 0.7,
                },
            ],
            "incident_sage": [
                {
                    "type": "error_prevention",
                    "context": {"severity": "medium"},
                    "initial_success_rate": 0.9,
                },
                {
                    "type": "recovery_pattern",
                    "context": {"auto_heal": True},
                    "initial_success_rate": 0.65,
                },
            ],
            "rag_sage": [
                {
                    "type": "search_optimization",
                    "context": {"semantic": True},
                    "initial_success_rate": 0.8,
                },
                {
                    "type": "context_enhancement",
                    "context": {"relevance": 0.9},
                    "initial_success_rate": 0.75,
                },
            ],
        }

        patterns = sage_patterns.get(sage_name, [])
        return random.sample(patterns, min(2, len(patterns)))

    def _generate_pattern_candidate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """パターン候補生成"""
        return {
            "type": data.get("type", "unknown"),
            "context_hash": hash(str(sorted(data.get("context", {}).items()))),
            "features": self._extract_pattern_features(data),
        }

    def _extract_pattern_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """パターン特徴量抽出"""
        features = {}

        context = data.get("context", {})

        # 基本特徴量
        features["complexity"] = len(str(context))
        features["has_numeric_values"] = any(
            isinstance(v, (int, float)) for v in context.values()
        )
        features["context_size"] = len(context)

        # ドメイン固有特徴量
        if "optimization" in data.get("type", ""):
            features["is_optimization"] = True
        if "error" in data.get("type", "") or "incident" in data.get("type", ""):
            features["is_error_related"] = True

        return features

    def _is_duplicate_pattern(self, candidate: Dict[str, Any]) -> bool:
        """重複パターンチェック"""
        candidate_hash = candidate.get("context_hash")
        candidate_type = candidate.get("type")

        for pattern in self.learning_patterns.values():
            existing_hash = hash(str(sorted(pattern.context.items())))
            if (
                existing_hash == candidate_hash
                and pattern.pattern_type == candidate_type
            ):
                return True

        return False

    async def _evaluate_pattern_importance(self):
        """パターン重要度評価"""
        for pattern in self.learning_patterns.values():
            # 重要度の再計算
            pattern._update_importance_score()

            # 賢者からのフィードバック取得
            sage_feedback = await self._get_sage_feedback_for_pattern(pattern)

            # フィードバックに基づく調整
            if sage_feedback:
                pattern.importance_score = (
                    0.7 * pattern.importance_score
                    + 0.3 * sage_feedback.get("importance", 0.5)
                )

    async def _get_sage_feedback_for_pattern(
        self, pattern: EnhancedLearningPattern
    ) -> Optional[Dict[str, Any]]:
        """パターンに対する賢者フィードバック取得"""
        # 実装簡略化：モックフィードバック
        import random

        if secrets.token_hex(16) < 0.3:  # 30%の確率でフィードバック
            return {
                "importance": random.uniform(0.3, 0.9),
                "confidence": random.uniform(0.6, 0.95),
                "relevance": random.uniform(0.5, 1.0),
            }
        return None

    def _cluster_similar_patterns(self):
        """類似パターンのクラスタリング"""
        if len(self.learning_patterns) < 3:
            return

        # パターンタイプ別にクラスタリング
        type_clusters = defaultdict(list)

        for pattern_id, pattern in self.learning_patterns.items():
            # 基本的なタイプベースクラスタリング
            base_type = pattern.pattern_type.split("_")[0]
            type_clusters[base_type].append(pattern_id)

        # 類似度ベースの詳細クラスタリング
        for cluster_type, pattern_ids in type_clusters.items():
            if len(pattern_ids) > 1:
                detailed_clusters = self._detailed_similarity_clustering(pattern_ids)
                self.pattern_clusters[cluster_type] = detailed_clusters

    def _detailed_similarity_clustering(
        self, pattern_ids: List[str]
    ) -> List[List[str]]:
        """詳細類似度クラスタリング"""
        clusters = []
        remaining_patterns = pattern_ids.copy()

        while remaining_patterns:
            current_cluster = [remaining_patterns.pop(0)]
            current_pattern = self.learning_patterns[current_cluster[0]]

            # 類似パターンを同じクラスタに追加
            for pattern_id in remaining_patterns.copy():
                pattern = self.learning_patterns[pattern_id]
                similarity = current_pattern._calculate_context_similarity(
                    pattern.context
                )

                if similarity > 0.7:  # 70%以上の類似度
                    current_cluster.append(pattern_id)
                    remaining_patterns.remove(pattern_id)

            clusters.append(current_cluster)

        return clusters

    def _prune_low_importance_patterns(self):
        """低重要度パターンの削除"""
        threshold = self.config["importance_threshold"]

        patterns_to_remove = []
        for pattern_id, pattern in self.learning_patterns.items():
            if (
                pattern.importance_score < threshold
                and pattern.usage_count < 5
                and (datetime.now() - pattern.last_updated).days > 7
            ):
                patterns_to_remove.append(pattern_id)

        for pattern_id in patterns_to_remove:
            del self.learning_patterns[pattern_id]
            logger.info(f"Pruned low-importance pattern: {pattern_id}")

    def _collect_current_performance(self) -> Dict[str, Any]:
        """現在のパフォーマンス収集"""
        active_patterns = len(
            [
                p
                for p in self.learning_patterns.values()
                if p.importance_score >= self.config["importance_threshold"]
            ]
        )

        return {
            "total_patterns": len(self.learning_patterns),
            "active_patterns": active_patterns,
            "average_success_rate": (
                statistics.mean(
                    [p.success_rate for p in self.learning_patterns.values()]
                )
                if self.learning_patterns
                else 0.0
            ),
            "average_importance": (
                statistics.mean(
                    [p.importance_score for p in self.learning_patterns.values()]
                )
                if self.learning_patterns
                else 0.0
            ),
            "learning_velocity": (
                len(self.learning_patterns)
                / max(
                    1,
                    (
                        datetime.now()
                        - min(p.created_at for p in self.learning_patterns.values())
                    ).total_seconds()
                    / 3600,
                )
                if self.learning_patterns
                else 0.0
            ),
        }

    def _identify_optimization_opportunities(
        self, performance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """最適化機会の特定"""
        opportunities = []

        # 成功率が低いパターンの改善
        if performance["average_success_rate"] < 0.7:
            opportunities.append(
                {
                    "type": "success_rate_improvement",
                    "target": "low_performing_patterns",
                    "action": "increase_learning_rate",
                }
            )

        # 学習速度の改善
        if performance["learning_velocity"] < 0.1:
            opportunities.append(
                {
                    "type": "learning_velocity_improvement",
                    "target": "pattern_discovery",
                    "action": "enhance_data_collection",
                }
            )

        # 重要度分布の最適化
        if performance["average_importance"] < 0.5:
            opportunities.append(
                {
                    "type": "importance_optimization",
                    "target": "pattern_relevance",
                    "action": "refine_importance_scoring",
                }
            )

        return opportunities

    async def _apply_real_time_optimization(self, opportunity: Dict[str, Any]):
        """リアルタイム最適化の適用"""
        action = opportunity.get("action")

        if action == "increase_learning_rate":
            # 低パフォーマンスパターンの学習率増加
            for pattern in self.learning_patterns.values():
                if pattern.success_rate < 0.7:
                    pattern.adaptation_rate = min(0.3, pattern.adaptation_rate * 1.2)

        elif action == "enhance_data_collection":
            # データ収集頻度の増加（実装簡略化）
            pass

        elif action == "refine_importance_scoring":
            # 重要度スコアリングの調整
            for pattern in self.learning_patterns.values():
                pattern._update_importance_score()

    def _analyze_learning_process(self) -> Dict[str, Any]:
        """学習プロセス分析"""
        if not self.performance_history:
            return {}

        recent_history = list(self.performance_history)[-20:]

        return {
            "performance_trend": self._calculate_trend(
                [h["accuracy"] for h in recent_history]
            ),
            "learning_stability": (
                statistics.stdev([h["accuracy"] for h in recent_history])
                if len(recent_history) > 1
                else 0.0
            ),
            "pattern_growth_rate": (
                len(recent_history[-1]["metrics"]) / max(1, len(recent_history))
                if recent_history
                else 0.0
            ),
            "adaptation_effectiveness": self._calculate_adaptation_effectiveness(),
        }

    def _calculate_adaptation_effectiveness(self) -> float:
        """適応効果性計算"""
        if not self.learning_patterns:
            return 0.0

        # 最近更新されたパターンの改善度
        recent_patterns = [
            p
            for p in self.learning_patterns.values()
            if (datetime.now() - p.last_updated).hours < 24
        ]

        if not recent_patterns:
            return 0.5

        improvement_scores = []
        for pattern in recent_patterns:
            if pattern.trend_direction == "improving":
                improvement_scores.append(1.0)
            elif pattern.trend_direction == "stable":
                improvement_scores.append(0.5)
            else:
                improvement_scores.append(0.0)

        return statistics.mean(improvement_scores)

    def _discover_optimal_parameters(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """最適パラメータの発見"""
        current_performance = analysis.get("performance_trend", 0.0)
        stability = analysis.get("learning_stability", 1.0)

        optimal_params = {}

        # 学習率の最適化
        if current_performance > 0.05 and stability < 0.1:
            # パフォーマンス向上且つ安定
            optimal_params["adaptation_learning_rate"] = min(
                0.2, self.config["adaptation_learning_rate"] * 1.1
            )
        elif current_performance < -0.05 or stability > 0.2:
            # パフォーマンス低下または不安定
            optimal_params["adaptation_learning_rate"] = max(
                0.05, self.config["adaptation_learning_rate"] * 0.9
            )

        # 重要度閾値の最適化
        active_ratio = len(
            [
                p
                for p in self.learning_patterns.values()
                if p.importance_score >= self.config["importance_threshold"]
            ]
        ) / max(1, len(self.learning_patterns))

        if active_ratio < 0.3:  # アクティブパターンが少なすぎる
            optimal_params["importance_threshold"] = max(
                0.1, self.config["importance_threshold"] - 0.05
            )
        elif active_ratio > 0.8:  # アクティブパターンが多すぎる
            optimal_params["importance_threshold"] = min(
                0.8, self.config["importance_threshold"] + 0.05
            )

        return optimal_params

    def _validate_parameter_improvement(self, optimal_params: Dict[str, Any]) -> bool:
        """パラメータ改善の検証"""
        # 簡単な検証：大きな変更でなければ適用
        for key, new_value in optimal_params.items():
            current_value = self.config.get(key, 0.5)
            change_ratio = abs(new_value - current_value) / max(current_value, 0.1)

            if change_ratio > 0.5:  # 50%以上の変更は慎重に
                return False

        return True

    def _apply_meta_learning_insights(self, optimal_params: Dict[str, Any]):
        """メタ学習インサイトの適用"""
        for key, value in optimal_params.items():
            if key in self.config:
                old_value = self.config[key]
                self.config[key] = value
                logger.info(f"Meta-learning update: {key} {old_value} -> {value}")

    async def _record_meta_learning_session(
        self, analysis: Dict[str, Any], optimal_params: Dict[str, Any]
    ):
        """メタ学習セッションの記録"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO meta_learning_history
                (timestamp, learning_rate, performance_score, adaptation_efficiency,
                 active_patterns, meta_parameters)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now(),
                    self.config.get("adaptation_learning_rate", 0.1),
                    analysis.get("performance_trend", 0.0),
                    analysis.get("adaptation_effectiveness", 0.5),
                    len(self.learning_patterns),
                    json.dumps(optimal_params),
                ),
            )

            conn.commit()
        finally:
            conn.close()

    def _predict_future_performance(self) -> Dict[str, Any]:
        """将来パフォーマンス予測"""
        if len(self.performance_history) < 5:
            return {
                "predicted_accuracy": 0.5,
                "trend": 0.0,
                "confidence": 0.3,
                "prediction_horizon": 5,
            }

        recent_accuracies = [
            h["accuracy"] for h in list(self.performance_history)[-10:]
        ]
        trend = self._calculate_trend(recent_accuracies)

        # 線形予測（簡単な実装）
        current_accuracy = recent_accuracies[-1]
        predicted_accuracy = max(
            0.0, min(1.0, current_accuracy + trend * 5)
        )  # 5期間先予測

        # 予測信頼度（トレンドの安定性に基づく）
        accuracy_variance = (
            statistics.variance(recent_accuracies)
            if len(recent_accuracies) > 1
            else 0.5
        )
        confidence = max(0.1, 1.0 - accuracy_variance)

        return {
            "predicted_accuracy": predicted_accuracy,
            "trend": trend,
            "confidence": confidence,
            "prediction_horizon": 5,
        }

    def _detect_potential_issues(
        self, predictions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """潜在的問題の検出"""
        issues = []

        # パフォーマンス低下予測
        if predictions["predicted_accuracy"] < 0.6:
            issues.append(
                {
                    "type": "performance_degradation",
                    "severity": (
                        "high" if predictions["predicted_accuracy"] < 0.4 else "medium"
                    ),
                    "predicted_impact": predictions["predicted_accuracy"],
                    "confidence": predictions["confidence"],
                }
            )

        # 学習停滞の検出
        if abs(predictions["trend"]) < 0.01 and predictions["confidence"] > 0.8:
            issues.append(
                {
                    "type": "learning_stagnation",
                    "severity": "medium",
                    "trend": predictions["trend"],
                    "confidence": predictions["confidence"],
                }
            )

        return issues

    async def _apply_preventive_measures(self, issue: Dict[str, Any]):
        """予防的対策の適用"""
        issue_type = issue["type"]

        if issue_type == "performance_degradation":
            # 学習率の動的調整
            for pattern in self.learning_patterns.values():
                if pattern.success_rate < 0.7:
                    pattern.adaptation_rate = min(0.3, pattern.adaptation_rate * 1.3)

            logger.warning(f"Applied preventive measures for {issue_type}")

        elif issue_type == "learning_stagnation":
            # 新しいパターン発見の促進
            self.config["importance_threshold"] = max(
                0.1, self.config["importance_threshold"] - 0.1
            )

            logger.info(f"Applied preventive measures for {issue_type}")

    def _track_prediction_accuracy(self):
        """予測精度の追跡"""
        # 実装簡略化：基本的な精度追跡のみ
        if hasattr(self, "_previous_predictions"):
            # 前回の予測と実際の結果を比較
            pass

    def _measure_system_performance(self) -> Dict[str, Any]:
        """システムパフォーマンス測定"""
        return {
            "patterns_per_minute": (
                len(self.learning_patterns)
                / max(
                    1,
                    (
                        datetime.now()
                        - min(p.created_at for p in self.learning_patterns.values())
                    ).total_seconds()
                    / 60,
                )
                if self.learning_patterns
                else 0.0
            ),
            "average_adaptation_rate": (
                statistics.mean(
                    [p.adaptation_rate for p in self.learning_patterns.values()]
                )
                if self.learning_patterns
                else 0.1
            ),
            "success_rate_variance": (
                statistics.variance(
                    [p.success_rate for p in self.learning_patterns.values()]
                )
                if len(self.learning_patterns) > 1
                else 0.0
            ),
            "system_efficiency": len(self.learning_patterns)
            / max(1, len(self.optimization_queue)),
        }

    def _update_learning_metrics(self, system_metrics: Dict[str, Any]):
        """学習メトリクス更新"""
        self.metrics.total_patterns = len(self.learning_patterns)
        self.metrics.active_patterns = len(
            [
                p
                for p in self.learning_patterns.values()
                if p.importance_score >= self.config["importance_threshold"]
            ]
        )
        self.metrics.learning_velocity = system_metrics.get("patterns_per_minute", 0.0)
        self.metrics.adaptation_efficiency = self._calculate_adaptation_effectiveness()

    def _detect_performance_alerts(self, metrics: Dict[str, Any]) -> List[str]:
        """パフォーマンスアラート検出"""
        alerts = []

        if metrics.get("patterns_per_minute", 0) < 0.01:
            alerts.append("Low learning velocity detected")

        if metrics.get("success_rate_variance", 0) > 0.3:
            alerts.append("High performance variance detected")

        if metrics.get("system_efficiency", 1) < 0.5:
            alerts.append("Low system efficiency detected")

        return alerts

    async def _handle_performance_alerts(self, alerts: List[str]):
        """パフォーマンスアラート処理"""
        for alert in alerts:
            logger.warning(f"Performance Alert: {alert}")

            # Four Sagesに報告
            if self.four_sages:
                try:
                    await self.four_sages.report_to_claude_elder(
                        sage_type="meta_learning_system",
                        report_type="performance_alert",
                        content={
                            "alert": alert,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                except Exception as e:
                    logger.error(f"Failed to report alert to Claude Elder: {e}")

    def get_enhanced_learning_report(self) -> Dict[str, Any]:
        """強化版学習レポート生成"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_config": self.config.copy(),
            "learning_metrics": {
                "total_patterns": self.metrics.total_patterns,
                "active_patterns": self.metrics.active_patterns,
                "prediction_accuracy": self.metrics.calculate_accuracy(),
                "learning_velocity": self.metrics.learning_velocity,
                "adaptation_efficiency": self.metrics.adaptation_efficiency,
            },
            "pattern_analytics": {
                "pattern_types": list(
                    set(p.pattern_type for p in self.learning_patterns.values())
                ),
                "success_rate_distribution": self._calculate_success_rate_distribution(),
                "importance_distribution": self._calculate_importance_distribution(),
                "trend_analysis": self._analyze_pattern_trends(),
            },
            "meta_learning_insights": {
                "optimal_learning_rate": self._get_optimal_learning_rate(),
                "performance_stability": self._calculate_performance_stability(),
                "adaptation_success_rate": self.meta_learning_state[
                    "adaptation_success_rate"
                ],
            },
            "predictive_analysis": {
                "future_performance": self._predict_future_performance(),
                "potential_issues": len(
                    self._detect_potential_issues(self._predict_future_performance())
                ),
                "system_health": self._assess_system_health(),
            },
            "recommendations": self._generate_improvement_recommendations(),
        }

    def _calculate_success_rate_distribution(self) -> Dict[str, int]:
        """成功率分布計算"""
        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
        }

        for pattern in self.learning_patterns.values():
            rate = pattern.success_rate
            if rate < 0.2:
                distribution["0.0-0.2"] += 1
            elif rate < 0.4:
                distribution["0.2-0.4"] += 1
            elif rate < 0.6:
                distribution["0.4-0.6"] += 1
            elif rate < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1

        return distribution

    def _calculate_importance_distribution(self) -> Dict[str, int]:
        """重要度分布計算"""
        distribution = {"low": 0, "medium": 0, "high": 0}

        for pattern in self.learning_patterns.values():
            importance = pattern.importance_score
            if importance < 0.3:
                distribution["low"] += 1
            elif importance < 0.7:
                distribution["medium"] += 1
            else:
                distribution["high"] += 1

        return distribution

    def _analyze_pattern_trends(self) -> Dict[str, int]:
        """パターントレンド分析"""
        trends = {"improving": 0, "stable": 0, "declining": 0}

        for pattern in self.learning_patterns.values():
            trends[pattern.trend_direction] += 1

        return trends

    def _get_optimal_learning_rate(self) -> float:
        """最適学習率取得"""
        if self.learning_patterns:
            # 高パフォーマンスパターンの平均学習率
            high_performers = [
                p for p in self.learning_patterns.values() if p.success_rate > 0.8
            ]
            if high_performers:
                return statistics.mean([p.adaptation_rate for p in high_performers])

        return self.config["adaptation_learning_rate"]

    def _calculate_performance_stability(self) -> float:
        """パフォーマンス安定性計算"""
        if len(self.performance_history) < 5:
            return 0.5

        recent_accuracies = [
            h["accuracy"] for h in list(self.performance_history)[-10:]
        ]
        variance = (
            statistics.variance(recent_accuracies)
            if len(recent_accuracies) > 1
            else 0.0
        )

        # 安定性は分散の逆数（正規化）
        return max(0.0, min(1.0, 1.0 - variance))

    def _assess_system_health(self) -> str:
        """システム健康度評価"""
        accuracy = self.metrics.calculate_accuracy()
        stability = self._calculate_performance_stability()
        efficiency = self.metrics.adaptation_efficiency

        health_score = (accuracy + stability + efficiency) / 3

        if health_score >= 0.8:
            return "excellent"
        elif health_score >= 0.6:
            return "good"
        elif health_score >= 0.4:
            return "fair"
        else:
            return "poor"

    def _generate_improvement_recommendations(self) -> List[str]:
        """改善推奨事項生成"""
        recommendations = []

        accuracy = self.metrics.calculate_accuracy()
        if accuracy < 0.7:
            recommendations.append(
                "Increase adaptation rates for low-performing patterns"
            )

        if self.metrics.learning_velocity < 0.1:
            recommendations.append("Enhance pattern discovery mechanisms")

        if self._calculate_performance_stability() < 0.6:
            recommendations.append("Implement stability improvement measures")

        active_ratio = self.metrics.active_patterns / max(
            1, self.metrics.total_patterns
        )
        if active_ratio < 0.3:
            recommendations.append(
                "Lower importance threshold to activate more patterns"
            )
        elif active_ratio > 0.8:
            recommendations.append(
                "Raise importance threshold to focus on high-value patterns"
            )

        return recommendations


# デモ実行
if __name__ == "__main__":

    async def demo():
        print("🚀 Enhanced Autonomous Learning System Demo")
        print("=" * 50)

        learning_system = EnhancedAutonomousLearningSystem()

        # システム初期化
        print("1. Initializing enhanced learning system...")
        await learning_system.four_sages.initialize()

        # 学習レポート生成
        print("2. Generating enhanced learning report...")
        report = learning_system.get_enhanced_learning_report()

        print("\n📊 Enhanced Learning Report:")
        print(f"  🧠 Total Patterns: {report['learning_metrics']['total_patterns']}")
        print(
            f"  ⚡ Learning Velocity: {report['learning_metrics']['learning_velocity']:.3f}"
        )
        print(
            f"  🎯 Adaptation Efficiency: {report['learning_metrics']['adaptation_efficiency']:.3f}"
        )
        print(f"  🏥 System Health: {report['predictive_analysis']['system_health']}")

        print("\n🔮 Predictive Analysis:")
        future_perf = report["predictive_analysis"]["future_performance"]
        print(f"  📈 Predicted Accuracy: {future_perf['predicted_accuracy']:.3f}")
        print(f"  📊 Trend: {future_perf['trend']:.3f}")
        print(f"  🎯 Confidence: {future_perf['confidence']:.3f}")

        print("\n💡 Recommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")

        print("\n✨ Enhanced Autonomous Learning Capabilities:")
        print("  ✅ Adaptive learning rate adjustment")
        print("  ✅ Dynamic pattern importance evaluation")
        print("  ✅ Real-time performance optimization")
        print("  ✅ Predictive issue detection")
        print("  ✅ Meta-learning for self-improvement")

        await learning_system.four_sages.cleanup()
        print("\n🎯 Enhanced Autonomous Learning Demo - COMPLETED")

    asyncio.run(demo())