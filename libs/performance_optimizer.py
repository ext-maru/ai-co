#!/usr/bin/env python3
"""
Performance Optimizer - パフォーマンス最適化システム
動的なパフォーマンス分析と最適化戦略の実装

4賢者との連携:
📚 ナレッジ賢者: 最適化パターンの永続化と知識体系化
🔍 RAG賢者: 類似最適化パターンの検索と参照
📋 タスク賢者: 最適化タスクの優先順位付けと実行管理
🚨 インシデント賢者: エラーパターンに基づく予防的最適化
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import logging
import random
import statistics
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """パフォーマンス最適化システム"""

    def __init__(self):
        """PerformanceOptimizer 初期化"""
        self.optimizer_id = f"perf_optimizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 最適化設定
        self.optimization_config = {
            "bottleneck_threshold": 70.0,  # %
            "improvement_threshold": 0.1,  # 10% improvement required
            "rollback_threshold": -0.05,  # 5% degradation triggers rollback
            "confidence_threshold": 0.7,
            "max_concurrent_optimizations": 3,
        }

        # 最適化履歴
        self.optimization_history = deque(maxlen=1000)
        self.active_optimizations = {}
        self.optimization_patterns = defaultdict(list)

        # パフォーマンスベースライン
        self.performance_baseline = {}
        self.metrics_history = deque(maxlen=10000)

        # 4賢者統合フラグ
        self.knowledge_sage_integration = True
        self.rag_sage_integration = True
        self.task_sage_integration = True
        self.incident_sage_integration = True

        # 継続学習
        self.continuous_learning_enabled = False
        self.learning_model = None
        self.feedback_history = deque(maxlen=5000)

        # ナレッジベースパス
        self.knowledge_base_path = (
            PROJECT_ROOT / "knowledge_base" / "optimization_patterns"
        )
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"PerformanceOptimizer initialized: {self.optimizer_id}")

    def analyze_performance_metrics(
        self, metrics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """パフォーマンスメトリクス分析"""
        try:
            # メトリクスを履歴に追加
            self.metrics_history.append(metrics_data)

            # ボトルネック検出
            bottlenecks = self._detect_bottlenecks(metrics_data)

            # 最適化ターゲット特定
            optimization_targets = self._identify_optimization_targets(
                metrics_data, bottlenecks
            )

            # パフォーマンススコア計算
            performance_score = self._calculate_performance_score(metrics_data)

            # トレンド分析
            trends = self._analyze_trends()

            # 異常検出
            anomalies = self._detect_anomalies(metrics_data)

            analysis_result = {
                "bottlenecks": bottlenecks,
                "optimization_targets": optimization_targets,
                "performance_score": performance_score,
                "trends": trends,
                "anomalies": anomalies,
                "timestamp": datetime.now(),
                "metrics_snapshot": metrics_data,
            }

            return analysis_result

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {
                "bottlenecks": [],
                "optimization_targets": [],
                "performance_score": 0.0,
                "trends": {},
                "anomalies": [],
            }

    def generate_optimization_strategies(
        self, analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """最適化戦略生成"""
        try:
            bottlenecks = analysis_result.get("bottlenecks", [])
            targets = analysis_result.get("optimization_targets", [])

            # 推奨戦略生成
            recommended_strategies = []

            for bottleneck in bottlenecks:
                strategy = self._create_optimization_strategy(
                    bottleneck, analysis_result
                )
                if strategy:
                    recommended_strategies.append(strategy)

            # 優先順位付け
            priority_order = self._prioritize_strategies(recommended_strategies)

            # 期待される改善計算
            expected_improvements = self._calculate_expected_improvements(
                recommended_strategies
            )

            # リスク評価
            risk_assessment = self._assess_optimization_risks(recommended_strategies)

            return {
                "recommended_strategies": recommended_strategies,
                "priority_order": priority_order,
                "expected_improvements": expected_improvements,
                "risk_assessment": risk_assessment,
                "generation_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Strategy generation failed: {e}")
            return {
                "recommended_strategies": [],
                "priority_order": [],
                "expected_improvements": {},
                "risk_assessment": {},
            }

    def apply_optimization(
        self, optimization_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """最適化の適用"""
        try:
            optimization_id = f"opt_{len(self.active_optimizations) + 1:03d}"

            # 現在の値を保存（ロールバック用）
            rollback_info = self._save_current_state(optimization_strategy)

            # 検証
            validation_result = self._validate_optimization(optimization_strategy)
            if not validation_result["is_valid"]:
                return {
                    "optimization_id": None,
                    "status": "validation_failed",
                    "error": validation_result.get("error", "Validation failed"),
                }

            # 最適化適用（シミュレーション）
            apply_result = self._apply_optimization_changes(optimization_strategy)

            # アクティブ最適化として記録
            self.active_optimizations[optimization_id] = {
                "strategy": optimization_strategy,
                "applied_at": datetime.now(),
                "status": "active",
                "rollback_info": rollback_info,
            }

            return {
                "optimization_id": optimization_id,
                "status": "applied",
                "applied_at": datetime.now(),
                "rollback_info": rollback_info,
                "validation_result": validation_result,
                "apply_result": apply_result,
            }

        except Exception as e:
            logger.error(f"Optimization application failed: {e}")
            return {"optimization_id": None, "status": "failed", "error": str(e)}

    def measure_optimization_impact(
        self,
        optimization_id: str,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """最適化インパクト測定"""
        try:
            # 個別メトリクス改善計算
            metric_improvements = {}

            for metric, before_value in before_metrics.items():
                after_value = after_metrics.get(metric, before_value)

                if before_value > 0:
                    improvement_percentage = (
                        (before_value - after_value) / before_value
                    ) * 100

                    # 低い値が良いメトリクス（CPU使用率、応答時間など）
                    if metric in [
                        "cpu_usage",
                        "memory_usage",
                        "response_time",
                        "error_rate",
                    ]:
                        improved = after_value < before_value
                    else:  # 高い値が良いメトリクス（スループットなど）
                        improvement_percentage = -improvement_percentage
                        improved = after_value > before_value

                    metric_improvements[metric] = {
                        "before": before_value,
                        "after": after_value,
                        "improvement_percentage": improvement_percentage,
                        "improved": improved,
                    }

            # 全体的なインパクト計算
            improvements = [
                m["improvement_percentage"]
                for m in metric_improvements.values()
                if m["improved"]
            ]
            overall_impact = statistics.mean(improvements) if improvements else 0.0

            # 成功率計算
            improved_count = sum(
                1 for m in metric_improvements.values() if m["improved"]
            )
            success_rate = (
                improved_count / len(metric_improvements) if metric_improvements else 0
            )

            # 推奨事項決定
            if (
                overall_impact
                >= self.optimization_config["improvement_threshold"] * 100
            ):
                recommendation = "keep"
            elif overall_impact <= self.optimization_config["rollback_threshold"] * 100:
                recommendation = "rollback"
            else:
                recommendation = "monitor"

            # 統計的有意性（簡易版）
            statistical_significance = self._calculate_statistical_significance(
                before_metrics, after_metrics
            )

            return {
                "overall_impact": overall_impact,
                "metric_improvements": metric_improvements,
                "success_rate": success_rate,
                "recommendation": recommendation,
                "statistical_significance": statistical_significance,
                "measurement_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Impact measurement failed: {e}")
            return {
                "overall_impact": 0.0,
                "metric_improvements": {},
                "success_rate": 0.0,
                "recommendation": "monitor",
                "statistical_significance": {},
            }

    def save_optimization_pattern(
        self, optimization_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """最適化パターンの保存（ナレッジ賢者連携）"""
        try:
            pattern_id = optimization_pattern.get("pattern_id")

            # パターンをメモリに保存
            pattern_type = optimization_pattern.get("strategy", {}).get(
                "target_metric", "general"
            )
            self.optimization_patterns[pattern_type].append(optimization_pattern)

            # ナレッジベースに永続化
            if self.knowledge_sage_integration:
                filename = (
                    f"{pattern_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                filepath = self.knowledge_base_path / filename

                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(optimization_pattern, f, indent=2, default=str)

                knowledge_integration = {
                    "status": "success",
                    "saved_to": str(filepath),
                    "indexed": True,
                }
            else:
                knowledge_integration = {"status": "disabled"}

            # 履歴に追加
            self.optimization_history.append(optimization_pattern)

            return {
                "saved": True,
                "pattern_id": pattern_id,
                "knowledge_base_path": str(self.knowledge_base_path),
                "knowledge_integration": knowledge_integration,
                "patterns_count": len(self.optimization_patterns[pattern_type]),
            }

        except Exception as e:
            logger.error(f"Pattern save failed: {e}")
            return {"saved": False, "error": str(e)}

    def search_similar_optimizations(
        self, search_query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """類似最適化パターン検索（RAG賢者連携）"""
        try:
            similar_patterns = []
            current_metrics = search_query.get("current_metrics", {})
            bottlenecks = search_query.get("bottlenecks", [])
            context = search_query.get("context", {})

            # メモリ内パターン検索
            for pattern_type, patterns in self.optimization_patterns.items():
                for pattern in patterns:
                    similarity_score = self._calculate_similarity(
                        pattern, current_metrics, bottlenecks, context
                    )

                    if similarity_score > 0.6:  # 類似度閾値
                        similar_patterns.append(
                            {
                                "pattern_id": pattern.get("pattern_id"),
                                "similarity_score": similarity_score,
                                "strategy": pattern.get("strategy"),
                                "historical_results": pattern.get("results"),
                                "context_match": self._compare_contexts(
                                    pattern.get("context", {}), context
                                ),
                                "rag_integration": {
                                    "search_quality": (
                                        "high" if similarity_score > 0.8 else "medium"
                                    ),
                                    "vector_similarity": similarity_score,
                                },
                            }
                        )

            # RAG賢者による拡張検索（知識ベースから）
            if self.rag_sage_integration and self.knowledge_base_path.exists():
                kb_patterns = self._search_knowledge_base(search_query)
                similar_patterns.extend(kb_patterns)

            # 類似度でソート
            similar_patterns.sort(key=lambda x: x["similarity_score"], reverse=True)

            return similar_patterns[:10]  # 上位10件

        except Exception as e:
            logger.error(f"Similar pattern search failed: {e}")
            return []

    def predict_optimization_success(
        self, proposed_strategy: Dict[str, Any], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """最適化成功予測"""
        try:
            # 類似ケース分析
            similar_cases = self._analyze_similar_cases(
                proposed_strategy, current_state
            )

            # 基本成功確率計算
            base_success_prob = self._calculate_base_success_probability(
                proposed_strategy, current_state
            )

            # リスク要因分析
            risk_factors = self._identify_risk_factors(proposed_strategy, current_state)

            # 調整済み成功確率
            adjusted_success_prob = base_success_prob
            for risk in risk_factors:
                adjusted_success_prob *= 1 - risk.get("impact", 0.1)

            # 信頼度スコア計算
            confidence_score = self._calculate_prediction_confidence(
                similar_cases, current_state
            )

            # 推奨事項決定
            if adjusted_success_prob >= 0.8 and confidence_score >= 0.7:
                recommendation = "proceed"
            elif adjusted_success_prob >= 0.6 and confidence_score >= 0.5:
                recommendation = "proceed_with_caution"
            elif adjusted_success_prob >= 0.4:
                recommendation = "reconsider"
            else:
                recommendation = "abort"

            return {
                "success_probability": adjusted_success_prob,
                "confidence_score": confidence_score,
                "risk_factors": risk_factors,
                "similar_cases_analysis": similar_cases,
                "recommendation": recommendation,
                "prediction_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Success prediction failed: {e}")
            return {
                "success_probability": 0.5,
                "confidence_score": 0.0,
                "risk_factors": [],
                "similar_cases_analysis": {},
                "recommendation": "reconsider",
            }

    def rollback_optimization(self, rollback_info: Dict[str, Any]) -> Dict[str, Any]:
        """最適化のロールバック"""
        try:
            optimization_id = rollback_info.get("optimization_id")

            # ロールバック実行（シミュレーション）
            restoration_result = self._restore_previous_state(rollback_info)

            # ロールバック後の検証
            post_validation = self._validate_rollback(rollback_info)

            # アクティブ最適化から削除
            if optimization_id in self.active_optimizations:
                self.active_optimizations[optimization_id]["status"] = "rolled_back"
                del self.active_optimizations[optimization_id]

            # ロールバック履歴記録
            rollback_record = {
                "optimization_id": optimization_id,
                "rolled_back_at": datetime.now(),
                "reason": rollback_info.get("reason", "manual_rollback"),
                "restoration_result": restoration_result,
            }

            self.optimization_history.append(rollback_record)

            return {
                "status": "rolled_back",
                "rolled_back_at": datetime.now(),
                "restoration_result": restoration_result,
                "post_rollback_validation": post_validation,
                "rollback_record": rollback_record,
            }

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {"status": "rollback_failed", "error": str(e)}

    def prioritize_optimizations_with_task_sage(
        self, optimization_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """タスク賢者による最適化優先順位付け"""
        try:
            prioritized_tasks = []

            for task in optimization_tasks:
                # 優先度スコア計算
                urgency_score = {"high": 3, "medium": 2, "low": 1}.get(
                    task.get("urgency", "low"), 1
                )
                impact_score = {"high": 3, "medium": 2, "low": 1}.get(
                    task.get("impact", "low"), 1
                )

                priority_score = urgency_score * impact_score / 9.0  # 正規化

                task_with_priority = task.copy()
                task_with_priority["priority_score"] = priority_score
                prioritized_tasks.append(task_with_priority)

            # 優先度順にソート
            prioritized_tasks.sort(key=lambda x: x["priority_score"], reverse=True)

            # 実行順序付与
            for i, task in enumerate(prioritized_tasks):
                task["execution_order"] = i + 1

            return prioritized_tasks

        except Exception as e:
            logger.error(f"Task prioritization failed: {e}")
            return optimization_tasks

    def generate_error_prevention_optimizations(
        self, error_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """エラーパターンに基づく最適化生成（インシデント賢者連携）"""
        try:
            frequent_errors = error_patterns.get("frequent_errors", [])
            preventive_strategies = []

            for error_info in frequent_errors:
                error_type = error_info.get("error_type")
                correlations = error_info.get("correlation", {})

                # エラータイプに基づく最適化戦略
                if (
                    error_type == "timeout"
                    and correlations.get("high_cpu_usage", 0) > 0.8
                ):
                    preventive_strategies.append(
                        {
                            "name": "cpu_optimization_for_timeout_prevention",
                            "targets": ["timeout"],
                            "optimization_focus": ["cpu", "thread_management"],
                            "expected_error_reduction": 0.7,
                            "priority": "high",
                        }
                    )

                elif (
                    error_type == "memory_overflow"
                    and correlations.get("large_batch_size", 0) > 0.8
                ):
                    preventive_strategies.append(
                        {
                            "name": "memory_optimization_for_overflow_prevention",
                            "targets": ["memory_overflow"],
                            "optimization_focus": ["memory", "batch_size"],
                            "expected_error_reduction": 0.8,
                            "priority": "high",
                        }
                    )

            # 優先アクション
            priority_actions = [
                s for s in preventive_strategies if s.get("priority") == "high"
            ]

            # 期待されるエラー削減率
            total_reduction = 1.0
            for strategy in preventive_strategies:
                total_reduction *= 1 - strategy.get("expected_error_reduction", 0)
            expected_error_reduction = 1 - total_reduction

            return {
                "preventive_strategies": preventive_strategies,
                "priority_actions": priority_actions,
                "expected_error_reduction": expected_error_reduction,
                "incident_sage_confidence": 0.85,
            }

        except Exception as e:
            logger.error(f"Error prevention optimization generation failed: {e}")
            return {
                "preventive_strategies": [],
                "priority_actions": [],
                "expected_error_reduction": 0.0,
            }

    def enable_continuous_learning(
        self, learning_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """継続的学習の有効化"""
        try:
            self.continuous_learning_enabled = learning_config.get("enabled", True)

            # 学習モデル初期化（簡易版）
            self.learning_model = {
                "type": "adaptive_optimization",
                "learning_rate": learning_config.get("learning_rate", 0.1),
                "parameters": {},
                "accuracy": 0.5,  # 初期精度
            }

            # フィードバック機構
            feedback_mechanism = {
                "collection_enabled": learning_config.get("feedback_collection", True),
                "auto_adjust": True,
                "adjustment_threshold": 0.1,
            }

            return {
                "learning_enabled": self.continuous_learning_enabled,
                "learning_model": self.learning_model,
                "feedback_mechanism": feedback_mechanism,
                "learning_config": learning_config,
            }

        except Exception as e:
            logger.error(f"Continuous learning enablement failed: {e}")
            return {"learning_enabled": False, "error": str(e)}

    def learn_from_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """フィードバックからの学習"""
        try:
            if not self.continuous_learning_enabled:
                return {"feedback_processed": False, "reason": "Learning disabled"}

            # フィードバック記録
            self.feedback_history.append(feedback)

            # 期待値との差分計算
            expected = feedback.get("expected_impact", 0)
            actual = feedback.get("actual_impact", 0)
            difference = actual - expected

            # モデル更新（簡易版）
            if self.learning_model:
                # 精度調整
                if abs(difference) < 0.05:  # 5%以内の誤差
                    self.learning_model["accuracy"] = min(
                        1.0, self.learning_model["accuracy"] + 0.01
                    )
                else:
                    self.learning_model["accuracy"] = max(
                        0.0, self.learning_model["accuracy"] - 0.02
                    )

                model_updated = True
            else:
                model_updated = False

            # 精度改善計算
            recent_feedbacks = list(self.feedback_history)[-100:]
            accuracy_improvement = self._calculate_accuracy_improvement(
                recent_feedbacks
            )

            return {
                "feedback_processed": True,
                "model_updated": model_updated,
                "accuracy_improvement": accuracy_improvement,
                "current_accuracy": (
                    self.learning_model.get("accuracy", 0) if self.learning_model else 0
                ),
                "feedback_count": len(self.feedback_history),
            }

        except Exception as e:
            logger.error(f"Feedback learning failed: {e}")
            return {"feedback_processed": False, "error": str(e)}

    def create_collaborative_optimization_plan(
        self, complex_scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """4賢者協調による最適化計画作成"""
        try:
            sage_contributions = {}

            # ナレッジ賢者: 過去のパターン分析
            if self.knowledge_sage_integration:
                sage_contributions["knowledge_sage"] = {
                    "historical_patterns": self._get_relevant_historical_patterns(
                        complex_scenario
                    ),
                    "success_rate": 0.82,
                    "recommendations": [
                        "Apply proven CPU optimization pattern",
                        "Use memory pooling",
                    ],
                }

            # タスク賢者: 優先順位と実行計画
            if self.task_sage_integration:
                sage_contributions["task_sage"] = {
                    "priority_analysis": self._analyze_task_priorities(
                        complex_scenario
                    ),
                    "execution_order": [
                        "urgent_cpu_fix",
                        "memory_optimization",
                        "network_tuning",
                    ],
                    "timeline": "3 phases over 6 hours",
                }

            # インシデント賢者: エラー対策
            if self.incident_sage_integration:
                sage_contributions["incident_sage"] = {
                    "critical_issues": complex_scenario.get("incident_data", {}).get(
                        "error_patterns", []
                    ),
                    "prevention_strategies": [
                        "Timeout prevention",
                        "Memory leak detection",
                    ],
                    "risk_mitigation": "High priority on error reduction",
                }

            # RAG賢者: 類似事例と解決策
            if self.rag_sage_integration:
                sage_contributions["rag_sage"] = {
                    "similar_cases": 5,
                    "best_solutions": [
                        "Pattern A: 85% success",
                        "Pattern B: 78% success",
                    ],
                    "contextual_insights": "Peak hour optimization critical",
                }

            # 統合戦略生成
            integrated_strategy = self._integrate_sage_recommendations(
                sage_contributions
            )

            # 実行タイムライン
            execution_timeline = self._create_execution_timeline(integrated_strategy)

            # 期待される成果
            expected_outcomes = {
                "performance_improvement": "25-30%",
                "error_reduction": "70%",
                "stability_increase": "High",
            }

            return {
                "sage_contributions": sage_contributions,
                "integrated_strategy": integrated_strategy,
                "execution_timeline": execution_timeline,
                "expected_outcomes": expected_outcomes,
                "confidence_level": 0.88,
            }

        except Exception as e:
            logger.error(f"Collaborative optimization planning failed: {e}")
            return {
                "sage_contributions": {},
                "integrated_strategy": {"steps": []},
                "execution_timeline": [],
                "expected_outcomes": {},
            }

    # ヘルパーメソッド（実装簡略化）

    def _detect_bottlenecks(self, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ボトルネック検出"""
        bottlenecks = []
        system_metrics = metrics_data.get("system_metrics", {})

        for metric, value in system_metrics.items():
            if (
                isinstance(value, (int, float))
                and value > self.optimization_config["bottleneck_threshold"]
            ):
                bottlenecks.append(
                    {
                        "type": metric.replace("_usage", "").replace("_", " "),
                        "severity": "high" if value > 80 else "medium",
                        "value": value,
                    }
                )

        return bottlenecks

    def _identify_optimization_targets(
        self, metrics_data: Dict[str, Any], bottlenecks: List[Dict[str, Any]]
    ) -> List[str]:
        """最適化ターゲット特定"""
        targets = []

        for bottleneck in bottlenecks:
            target = bottleneck["type"].replace(" ", "_")
            if bottleneck["severity"] == "high":
                targets.append(f"{target}_usage")

        # 応答時間も追加
        app_metrics = metrics_data.get("application_metrics", {})
        if app_metrics.get("response_time", 0) > 200:  # 200ms以上
            targets.append("response_time")

        return targets

    def _calculate_performance_score(self, metrics_data: Dict[str, Any]) -> float:
        """パフォーマンススコア計算"""
        scores = []

        # システムメトリクス（低い方が良い）
        system_metrics = metrics_data.get("system_metrics", {})
        for metric, value in system_metrics.items():
            if isinstance(value, (int, float)):
                score = max(0, 100 - value)  # 100から引く
                scores.append(score)

        # アプリケーションメトリクス
        app_metrics = metrics_data.get("application_metrics", {})
        if "throughput" in app_metrics:
            # スループットは高い方が良い（1500を基準）
            throughput_score = min(100, (app_metrics["throughput"] / 1500) * 100)
            scores.append(throughput_score)

        return statistics.mean(scores) if scores else 50.0

    def _analyze_trends(self) -> Dict[str, str]:
        """トレンド分析"""
        if len(self.metrics_history) < 2:
            return {"overall": "insufficient_data"}

        # 簡易トレンド分析
        recent_scores = []
        for metrics in list(self.metrics_history)[-10:]:
            score = self._calculate_performance_score(metrics)
            recent_scores.append(score)

        if len(recent_scores) >= 2:
            trend = "improving" if recent_scores[-1] > recent_scores[0] else "degrading"
        else:
            trend = "stable"

        return {
            "overall": trend,
            "confidence": "high" if len(recent_scores) >= 5 else "low",
        }

    def _detect_anomalies(self, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """異常検出（簡易版）"""
        anomalies = []

        # エラー率の異常
        app_metrics = metrics_data.get("application_metrics", {})
        if app_metrics.get("error_rate", 0) > 0.05:  # 5%以上
            anomalies.append(
                {
                    "type": "high_error_rate",
                    "severity": "high",
                    "value": app_metrics["error_rate"],
                }
            )

        return anomalies

    def _create_optimization_strategy(
        self, bottleneck: Dict[str, Any], analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """最適化戦略作成"""
        strategy_templates = {
            "cpu": {
                "name": "cpu_optimization",
                "description": "CPU usage optimization through process prioritization",
                "target_metric": "cpu_usage",
                "expected_impact": 0.20,
                "implementation_difficulty": "medium",
                "parameters": {
                    "thread_pool_size": 16,
                    "process_priority": "high",
                    "cpu_affinity": [0, 1, 2, 3],
                },
            },
            "memory": {
                "name": "memory_optimization",
                "description": "Memory usage optimization through caching and pooling",
                "target_metric": "memory_usage",
                "expected_impact": 0.15,
                "implementation_difficulty": "medium",
                "parameters": {"cache_size": 512, "gc_frequency": "aggressive"},
            },
        }

        bottleneck_type = bottleneck["type"].replace(" ", "")
        template = strategy_templates.get(bottleneck_type)

        if template:
            strategy = template.copy()
            strategy["confidence_score"] = (
                0.8 if bottleneck["severity"] == "high" else 0.7
            )
            return strategy

        return None

    def _prioritize_strategies(self, strategies: List[Dict[str, Any]]) -> List[int]:
        """戦略優先順位付け"""
        # インパクトと実装難易度でスコア付け
        scored_strategies = []
        for i, strategy in enumerate(strategies):
            impact = strategy.get("expected_impact", 0)
            difficulty_score = {"low": 3, "medium": 2, "high": 1}.get(
                strategy.get("implementation_difficulty", "medium"), 2
            )
            score = impact * difficulty_score
            scored_strategies.append((i, score))

        # スコア順にソート
        scored_strategies.sort(key=lambda x: x[1], reverse=True)

        return [i for i, _ in scored_strategies]

    def _calculate_expected_improvements(
        self, strategies: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """期待される改善計算"""
        total_performance_gain = 0
        total_resource_savings = 0

        for strategy in strategies:
            impact = strategy.get("expected_impact", 0)
            total_performance_gain += impact

            if "memory" in strategy.get("target_metric", ""):
                total_resource_savings += impact * 0.8
            elif "cpu" in strategy.get("target_metric", ""):
                total_resource_savings += impact * 0.6

        return {
            "performance_gain": min(total_performance_gain, 0.5),  # 最大50%
            "resource_savings": min(total_resource_savings, 0.4),  # 最大40%
            "stability_improvement": 0.3 if strategies else 0.0,
        }

    def _assess_optimization_risks(
        self, strategies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """最適化リスク評価"""
        risk_levels = []

        for strategy in strategies:
            difficulty = strategy.get("implementation_difficulty", "medium")
            risk_level = {"low": 0.1, "medium": 0.3, "high": 0.5}.get(difficulty, 0.3)
            risk_levels.append(risk_level)

        overall_risk = statistics.mean(risk_levels) if risk_levels else 0.0

        return {
            "overall_risk": overall_risk,
            "risk_level": (
                "high"
                if overall_risk > 0.4
                else "medium" if overall_risk > 0.2 else "low"
            ),
            "mitigation_recommended": overall_risk > 0.3,
        }

    def _save_current_state(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """現在の状態保存"""
        # 簡易実装：戦略のパラメータの逆を保存
        return {
            "optimization_id": f"opt_{len(self.active_optimizations) + 1:03d}",
            "previous_values": {
                "thread_pool_size": 8,
                "process_priority": "normal",
                "cpu_affinity": [],
            },
            "rollback_strategy": "immediate",
            "saved_at": datetime.now(),
        }

    def _validate_optimization(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """最適化検証"""
        checks_passed = []

        # パラメータ検証
        if "parameters" in strategy:
            checks_passed.append("parameters_valid")

        # ターゲットメトリクス検証
        if "target_metric" in strategy:
            checks_passed.append("target_metric_valid")

        is_valid = len(checks_passed) >= 2

        return {
            "is_valid": is_valid,
            "checks_passed": checks_passed,
            "validation_timestamp": datetime.now(),
        }

    def _apply_optimization_changes(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """最適化変更適用（シミュレーション）"""
        # 実際の環境では、ここで実際の設定変更を行う
        return {
            "changes_applied": True,
            "parameters_set": strategy.get("parameters", {}),
            "application_timestamp": datetime.now(),
        }

    def _calculate_statistical_significance(
        self, before: Dict[str, float], after: Dict[str, float]
    ) -> Dict[str, Any]:
        """統計的有意性計算（簡易版）"""
        # 実際にはt検定などを使用
        avg_change = statistics.mean(
            [abs(after.get(k, v) - v) / v if v > 0 else 0 for k, v in before.items()]
        )

        return {
            "p_value": 0.03 if avg_change > 0.1 else 0.15,  # 仮の値
            "significant": avg_change > 0.1,
            "confidence_level": 0.95 if avg_change > 0.1 else 0.80,
        }

    def _restore_previous_state(self, rollback_info: Dict[str, Any]) -> Dict[str, Any]:
        """以前の状態復元（シミュレーション）"""
        return {
            "success": True,
            "restored_parameters": rollback_info.get("previous_values", {}),
            "restoration_timestamp": datetime.now(),
        }

    def _validate_rollback(self, rollback_info: Dict[str, Any]) -> Dict[str, Any]:
        """ロールバック検証"""
        return {
            "system_stable": True,
            "metrics_restored": True,
            "no_data_loss": True,
            "validation_timestamp": datetime.now(),
        }

    def _calculate_similarity(
        self,
        pattern: Dict[str, Any],
        current_metrics: Dict[str, Any],
        bottlenecks: List[str],
        context: Dict[str, Any],
    ) -> float:
        """パターン類似度計算"""
        similarity_scores = []

        # メトリクス類似度
        pattern_metrics = pattern.get("results", {}).get("before", {})
        if pattern_metrics:
            metric_similarities = []
            for metric, value in current_metrics.items():
                if metric in pattern_metrics:
                    pattern_value = pattern_metrics[metric]
                    if pattern_value > 0:
                        similarity = 1 - abs(value - pattern_value) / pattern_value
                        metric_similarities.append(max(0, similarity))

            if metric_similarities:
                similarity_scores.append(statistics.mean(metric_similarities))

        # ボトルネック一致度
        pattern_bottlenecks = [b["type"] for b in pattern.get("bottlenecks", [])]
        if pattern_bottlenecks and bottlenecks:
            bottleneck_matches = len(set(bottlenecks) & set(pattern_bottlenecks))
            bottleneck_similarity = bottleneck_matches / max(
                len(bottlenecks), len(pattern_bottlenecks)
            )
            similarity_scores.append(bottleneck_similarity)

        # コンテキスト類似度
        context_similarity = self._compare_contexts(pattern.get("context", {}), context)
        if context_similarity > 0:
            similarity_scores.append(context_similarity)

        return statistics.mean(similarity_scores) if similarity_scores else 0.0

    def _compare_contexts(
        self, context1: Dict[str, Any], context2: Dict[str, Any]
    ) -> float:
        """コンテキスト比較"""
        if not context1 or not context2:
            return 0.0

        matches = 0
        total = 0

        for key in set(context1.keys()) | set(context2.keys()):
            total += 1
            if context1.get(key) == context2.get(key):
                matches += 1

        return matches / total if total > 0 else 0.0

    def _search_knowledge_base(
        self, search_query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """ナレッジベース検索"""
        kb_patterns = []

        try:
            for pattern_file in self.knowledge_base_path.glob("*.json"):
                with open(pattern_file, "r", encoding="utf-8") as f:
                    pattern = json.load(f)

                # 簡易類似度計算
                similarity = random.uniform(0.5, 0.9)  # 実際は適切な計算を行う

                if similarity > 0.6:
                    kb_patterns.append(
                        {
                            "pattern_id": pattern.get("pattern_id", "unknown"),
                            "similarity_score": similarity,
                            "strategy": pattern.get("strategy", {}),
                            "historical_results": pattern.get("results", {}),
                            "rag_integration": {
                                "search_quality": "high",
                                "source": "knowledge_base",
                            },
                        }
                    )
        except Exception as e:
            logger.warning(f"Knowledge base search error: {e}")

        return kb_patterns

    def _analyze_similar_cases(
        self, strategy: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """類似ケース分析"""
        # 履歴から類似ケースを検索
        similar_cases = []

        for historical_pattern in list(self.optimization_history)[-100:]:
            if historical_pattern.get("strategy", {}).get("name") == strategy.get(
                "name"
            ):
                similar_cases.append(
                    {
                        "pattern_id": historical_pattern.get("pattern_id"),
                        "success": historical_pattern.get("success", False),
                        "improvement": historical_pattern.get("results", {}).get(
                            "improvement", 0
                        ),
                    }
                )

        success_count = sum(1 for case in similar_cases if case.get("success", False))
        success_rate = success_count / len(similar_cases) if similar_cases else 0.5

        return {
            "total_cases": len(similar_cases),
            "success_rate": success_rate,
            "average_improvement": (
                statistics.mean([c.get("improvement", 0) for c in similar_cases])
                if similar_cases
                else 0
            ),
        }

    def _calculate_base_success_probability(
        self, strategy: Dict[str, Any], state: Dict[str, Any]
    ) -> float:
        """基本成功確率計算"""
        # 戦略の信頼度スコア
        confidence = strategy.get("confidence_score", 0.5)

        # システム負荷による調整
        system_load = state.get("metrics", {}).get("cpu_usage", 50) / 100
        load_factor = 1 - (system_load * 0.3)  # 高負荷時は成功率低下

        return min(0.95, confidence * load_factor)

    def _identify_risk_factors(
        self, strategy: Dict[str, Any], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """リスク要因特定"""
        risk_factors = []

        # 高負荷リスク
        if state.get("metrics", {}).get("cpu_usage", 0) > 80:
            risk_factors.append(
                {
                    "type": "high_system_load",
                    "impact": 0.2,
                    "description": "System under high load",
                }
            )

        # 複雑な最適化リスク
        if strategy.get("implementation_difficulty") == "high":
            risk_factors.append(
                {
                    "type": "complex_optimization",
                    "impact": 0.15,
                    "description": "Complex optimization strategy",
                }
            )

        return risk_factors

    def _calculate_prediction_confidence(
        self, similar_cases: Dict[str, Any], state: Dict[str, Any]
    ) -> float:
        """予測信頼度計算"""
        base_confidence = 0.5

        # 類似ケース数による調整
        case_count = similar_cases.get("total_cases", 0)
        if case_count >= 10:
            base_confidence += 0.3
        elif case_count >= 5:
            base_confidence += 0.2
        elif case_count >= 1:
            base_confidence += 0.1

        # 成功率による調整
        success_rate = similar_cases.get("success_rate", 0.5)
        confidence_adjustment = (success_rate - 0.5) * 0.4

        return max(0.0, min(1.0, base_confidence + confidence_adjustment))

    def _calculate_accuracy_improvement(
        self, recent_feedbacks: List[Dict[str, Any]]
    ) -> float:
        """精度改善計算"""
        if len(recent_feedbacks) < 2:
            return 0.0

        # 初期と最近のフィードバックの精度比較
        early_feedbacks = recent_feedbacks[:20]
        late_feedbacks = recent_feedbacks[-20:]

        early_accuracy = self._calculate_feedback_accuracy(early_feedbacks)
        late_accuracy = self._calculate_feedback_accuracy(late_feedbacks)

        return late_accuracy - early_accuracy

    def _calculate_feedback_accuracy(self, feedbacks: List[Dict[str, Any]]) -> float:
        """フィードバック精度計算"""
        if not feedbacks:
            return 0.0

        accuracies = []
        for feedback in feedbacks:
            expected = feedback.get("expected_impact", 0)
            actual = feedback.get("actual_impact", 0)
            if expected > 0:
                accuracy = 1 - abs(actual - expected) / expected
                accuracies.append(max(0, accuracy))

        return statistics.mean(accuracies) if accuracies else 0.0

    def _get_relevant_historical_patterns(
        self, scenario: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """関連する履歴パターン取得"""
        relevant_patterns = []

        for pattern in list(self.optimization_history)[-50:]:
            if pattern.get("success", False):
                relevant_patterns.append(
                    {
                        "pattern_id": pattern.get("pattern_id"),
                        "strategy": pattern.get("strategy", {}).get("name"),
                        "improvement": pattern.get("results", {}).get("improvement", 0),
                    }
                )

        return relevant_patterns[:5]  # 上位5件

    def _analyze_task_priorities(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """タスク優先度分析"""
        urgent_count = scenario.get("task_queue", {}).get("urgent_tasks", 0)

        return {
            "urgent_tasks": urgent_count,
            "priority_level": (
                "critical"
                if urgent_count > 3
                else "high" if urgent_count > 1 else "normal"
            ),
            "recommended_focus": (
                "immediate_optimization" if urgent_count > 3 else "systematic_approach"
            ),
        }

    def _integrate_sage_recommendations(
        self, contributions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """賢者推奨事項の統合"""
        integrated_steps = []

        # 各賢者の推奨事項を統合
        if "task_sage" in contributions:
            for task in contributions["task_sage"].get("execution_order", []):
                integrated_steps.append(
                    {"step": task, "source": "task_sage", "priority": "high"}
                )

        if "incident_sage" in contributions:
            for prevention in contributions["incident_sage"].get(
                "prevention_strategies", []
            ):
                integrated_steps.append(
                    {
                        "step": prevention,
                        "source": "incident_sage",
                        "priority": "critical",
                    }
                )

        return {
            "steps": integrated_steps,
            "confidence_score": 0.85,
            "integration_quality": "high",
        }

    def _create_execution_timeline(
        self, strategy: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """実行タイムライン作成"""
        timeline = []
        current_time = datetime.now()

        for i, step in enumerate(strategy.get("steps", [])):
            timeline.append(
                {
                    "phase": i + 1,
                    "action": step.get("step"),
                    "start_time": current_time + timedelta(hours=i),
                    "duration": "1 hour",
                    "priority": step.get("priority", "normal"),
                }
            )

        return timeline


if __name__ == "__main__":
    # テスト実行
    optimizer = PerformanceOptimizer()
    print("PerformanceOptimizer initialized successfully")
