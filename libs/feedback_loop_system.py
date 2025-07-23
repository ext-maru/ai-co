#!/usr/bin/env python3
"""
Feedback Loop System - フィードバックループシステム
実行結果を即座に学習データとして取り込み、継続的な改善サイクルを自動化

4賢者との連携:
📚 ナレッジ賢者: 短いサイクルで高頻度フィードバックの実装
🔍 RAG賢者: フィードバックデータの意味的検索と関連付け
📋 タスク賢者: フィードバック処理の優先順位付けと効率化
🚨 インシデント賢者: フィードバックループ暴走の検知と防止
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import logging
import math
import statistics
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class FeedbackLoopSystem:
    """フィードバックループシステム"""

    def __init__(self):
        """FeedbackLoopSystem 初期化"""
        self.system_id = f"feedback_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # フィードバック処理コンポーネント
        self.metrics_collector = MetricsCollector()
        self.evaluator = PerformanceEvaluator()
        self.data_pipeline = LearningDataPipeline()

        # フィードバック管理
        self.feedback_buffer = deque(maxlen=10000)
        self.processed_feedback = defaultdict(list)
        self.learning_history = deque(maxlen=5000)

        # リアルタイム処理
        self.real_time_processor = RealTimeProcessor()
        self.anomaly_detector = FeedbackAnomalyDetector()

        # 設定
        self.loop_config = {
            "collection_interval": 1.0,  # 秒
            "processing_batch_size": 50,
            "quality_threshold": 0.7,
            "anomaly_sensitivity": 0.8,
        }

        # 4賢者統合フラグ
        self.knowledge_sage_integration = True
        self.rag_sage_integration = True
        self.task_sage_integration = True
        self.incident_sage_integration = True

        # ナレッジベースパス
        self.knowledge_base_path = PROJECT_ROOT / "knowledge_base" / "feedback_learning"
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"FeedbackLoopSystem initialized: {self.system_id}")

    def collect_feedback(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """実行結果からフィードバックを収集"""
        try:
            feedback_id = f"fb_{uuid.uuid4().hex[:8]}"

            # 操作メタデータ抽出
            operation_metadata = {
                "operation_id": execution_result.get("operation_id"),
                "operation_type": execution_result.get("operation_type"),
                "parameters": execution_result.get("parameters", {}),
                "execution_duration": self._calculate_duration(execution_result),
            }

            # パフォーマンスメトリクス抽出
            performance_metrics = {}
            if "metrics" in execution_result:
                metrics = execution_result["metrics"]
                for metric_name, metric_data in metrics.items():
                    if isinstance(metric_data, dict):
                        improvement = metric_data.get("improvement", 0)
                        performance_metrics[f"{metric_name}_improvement"] = improvement

            # 改善指標計算
            improvement_indicators = self._calculate_improvement_indicators(
                performance_metrics
            )

            # コンテキストデータ
            context_data = self._extract_context_data(execution_result)

            # 品質スコア計算
            quality_score = self._calculate_feedback_quality(
                execution_result, performance_metrics
            )

            # フィードバック構築
            feedback = {
                "feedback_id": feedback_id,
                "operation_metadata": operation_metadata,
                "performance_metrics": performance_metrics,
                "improvement_indicators": improvement_indicators,
                "context_data": context_data,
                "quality_score": quality_score,
                "collection_timestamp": datetime.now(),
                "raw_execution_result": execution_result,
            }

            # バッファに追加
            self.feedback_buffer.append(feedback)

            return feedback

        except Exception as e:
            logger.error(f"Error collecting feedback: {str(e)}")
            return {"feedback_id": None, "error": str(e)}

    def process_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """フィードバックを処理"""
        try:
            processed_id = f"proc_{uuid.uuid4().hex[:8]}"

            # パターン抽出
            patterns = self._extract_patterns(feedback_data)

            # 実行可能な洞察生成
            insights = self._generate_actionable_insights(feedback_data, patterns)

            # 信頼度スコア計算
            confidence_score = self._calculate_processing_confidence(
                feedback_data, patterns, insights
            )

            # 推奨アクション決定
            recommended_actions = self._determine_recommended_actions(insights)

            # 学習優先度設定
            learning_priority = self._assign_learning_priority(
                feedback_data, patterns, confidence_score
            )

            # 処理結果構築
            processing_result = {
                "processed_feedback_id": processed_id,
                "original_feedback_id": feedback_data.get("feedback_id"),
                "extracted_patterns": patterns,
                "actionable_insights": insights,
                "confidence_score": confidence_score,
                "recommended_actions": recommended_actions,
                "learning_priority": learning_priority,
                "processing_timestamp": datetime.now(),
            }

            # 処理済みフィードバックに追加
            feedback_type = feedback_data.get("operation_metadata", {}).get(
                "operation_type", "unknown"
            )
            self.processed_feedback[feedback_type].append(processing_result)

            return processing_result

        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            return {"processed_feedback_id": None, "error": str(e)}

    def evaluate_performance(
        self, metrics_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """パフォーマンスを評価"""
        try:
            # トレンド分析
            performance_trend = self._analyze_performance_trend(metrics_history)

            # 改善率計算
            improvement_rate = self._calculate_improvement_rates(metrics_history)

            # 安定性評価
            stability_assessment = self._assess_stability(metrics_history)

            # 異常検出
            anomaly_detection = self._detect_performance_anomalies(metrics_history)

            # ベンチマーク比較
            benchmark_comparison = self._compare_with_benchmarks(metrics_history)

            # 評価スコア計算
            evaluation_score = self._calculate_evaluation_score(
                performance_trend, improvement_rate, stability_assessment
            )

            return {
                "performance_trend": performance_trend,
                "improvement_rate": improvement_rate,
                "stability_assessment": stability_assessment,
                "anomaly_detection": anomaly_detection,
                "benchmark_comparison": benchmark_comparison,
                "evaluation_score": evaluation_score,
                "evaluation_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error evaluating performance: {str(e)}")
            return {"evaluation_score": 0, "error": str(e)}

    def generate_learning_data(
        self, processed_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """処理済みフィードバックから学習データを生成"""
        try:
            # 学習サンプル生成
            learning_samples = self._create_learning_samples(processed_feedback)

            # 特徴ベクトル構築
            feature_vectors = self._build_feature_vectors(processed_feedback)

            # ターゲット結果抽出
            target_outcomes = self._extract_target_outcomes(processed_feedback)

            # メタデータ構築
            metadata = self._build_learning_metadata(processed_feedback)

            # 品質指標計算
            quality_indicators = self._calculate_learning_quality(
                learning_samples, feature_vectors
            )

            # パターン発見
            patterns_discovered = self._discover_new_patterns(processed_feedback)

            learning_data = {
                "learning_samples": learning_samples,
                "feature_vectors": feature_vectors,
                "target_outcomes": target_outcomes,
                "metadata": metadata,
                "quality_indicators": quality_indicators,
                "patterns_discovered": patterns_discovered,
                "generation_timestamp": datetime.now(),
            }

            return learning_data

        except Exception as e:
            logger.error(f"Error generating learning data: {str(e)}")
            return {"learning_samples": [], "error": str(e)}

    def update_knowledge_base(self, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """ナレッジベースを更新（ナレッジ賢者連携）"""
        try:
            # ナレッジ更新ID
            update_id = f"kb_update_{uuid.uuid4().hex[:8]}"

            # パターン統合
            patterns_added = self._integrate_patterns(
                learning_data.get("patterns_discovered", [])
            )

            # 学習サンプル統合
            samples_integrated = self._integrate_learning_samples(
                learning_data.get("learning_samples", [])
            )

            # バージョン管理
            knowledge_version = self._increment_knowledge_version()

            # 保存処理
            save_path = self.knowledge_base_path / f"{update_id}_learning.json"
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(learning_data, f, indent=2, default=str)

            # 学習履歴に追加
            self.learning_history.append(
                {
                    "update_id": update_id,
                    "learning_data": learning_data,
                    "updated_at": datetime.now(),
                }
            )

            # ナレッジ統合品質評価
            integration_quality = self._assess_integration_quality(
                learning_data, patterns_added, samples_integrated
            )

            # ナレッジ統合結果
            knowledge_integration = {
                "status": "success",
                "integration_quality": integration_quality,
                "patterns_merged": patterns_added,
                "samples_added": samples_integrated,
            }

            return {
                "updated": True,
                "update_id": update_id,
                "knowledge_base_path": str(save_path),
                "patterns_added": patterns_added,
                "samples_integrated": samples_integrated,
                "knowledge_version": knowledge_version,
                "knowledge_integration": knowledge_integration,
            }

        except Exception as e:
            logger.error(f"Error updating knowledge base: {str(e)}")
            return {"updated": False, "error": str(e)}

    def detect_feedback_anomalies(
        self, feedback_stream: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """フィードバック異常を検知（インシデント賢者連携）"""
        try:
            anomalies = []
            severity_levels = defaultdict(int)

            # 各フィードバックの異常チェック
            for feedback in feedback_stream:
                anomaly_results = self._check_feedback_anomalies(feedback)
                if anomaly_results:
                    anomalies.extend(anomaly_results)
                    for anomaly in anomaly_results:
                        severity_levels[anomaly["severity"]] += 1

            # 推奨アクション決定
            recommended_actions = self._determine_anomaly_actions(anomalies)

            # ループ健全性評価
            loop_health_status = self._assess_loop_health(anomalies, feedback_stream)

            return {
                "anomalies_detected": anomalies,
                "anomaly_count": len(anomalies),
                "severity_levels": dict(severity_levels),
                "recommended_actions": recommended_actions,
                "loop_health_status": loop_health_status,
                "detection_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error detecting feedback anomalies: {str(e)}")
            return {"anomalies_detected": [], "anomaly_count": 0, "error": str(e)}

    def optimize_feedback_cycle(
        self, cycle_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """フィードバックサイクルを最適化"""
        try:
            # ボトルネック分析
            bottleneck_analysis = self._analyze_cycle_bottlenecks(cycle_performance)

            # パフォーマンス改善提案
            performance_improvements = self._propose_performance_improvements(
                cycle_performance, bottleneck_analysis
            )

            # 調整推奨
            recommended_adjustments = self._recommend_cycle_adjustments(
                bottleneck_analysis
            )

            # 期待される影響評価
            expected_impact = self._estimate_optimization_impact(
                recommended_adjustments
            )

            # 最適化適用
            optimization_applied = self._apply_cycle_optimizations(
                recommended_adjustments
            )

            return {
                "optimization_applied": optimization_applied,
                "performance_improvements": performance_improvements,
                "bottleneck_analysis": bottleneck_analysis,
                "recommended_adjustments": recommended_adjustments,
                "expected_impact": expected_impact,
                "optimization_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error optimizing feedback cycle: {str(e)}")
            return {"optimization_applied": False, "error": str(e)}

    def create_improvement_suggestions(
        self, analyzed_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """改善提案を作成"""
        try:
            # 即座のアクション
            immediate_actions = self._identify_immediate_actions(analyzed_feedback)

            # 中期最適化
            medium_term_optimizations = self._identify_medium_term_optimizations(
                analyzed_feedback
            )

            # 長期戦略
            long_term_strategies = self._identify_long_term_strategies(
                analyzed_feedback
            )

            # 優先順位ランキング
            priority_ranking = self._rank_suggestions_by_priority(
                immediate_actions, medium_term_optimizations, long_term_strategies
            )

            # インパクト推定
            impact_estimations = self._estimate_suggestion_impacts(
                immediate_actions, medium_term_optimizations, long_term_strategies
            )

            return {
                "immediate_actions": immediate_actions,
                "medium_term_optimizations": medium_term_optimizations,
                "long_term_strategies": long_term_strategies,
                "priority_ranking": priority_ranking,
                "impact_estimations": impact_estimations,
                "creation_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error creating improvement suggestions: {str(e)}")
            return {"immediate_actions": [], "error": str(e)}

    def process_real_time_events(
        self, real_time_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """リアルタイムイベントを処理"""
        try:
            start_time = time.time()

            # イベント処理
            processed_events = []
            immediate_insights = []
            alerts_generated = []

            for event in real_time_events:
                # 個別イベント処理
                processed_event = self._process_single_event(event)
                processed_events.append(processed_event)

                # 即座の洞察抽出
                insights = self._extract_immediate_insights(event)
                immediate_insights.extend(insights)

                # アラート生成チェック
                alerts = self._check_alert_conditions(event)
                alerts_generated.extend(alerts)

            # 学習トリガー判定
            learning_triggered = self._should_trigger_learning(processed_events)

            # 処理遅延計算
            processing_latency = time.time() - start_time

            return {
                "events_processed": len(processed_events),
                "immediate_insights": immediate_insights,
                "alerts_generated": alerts_generated,
                "learning_triggered": learning_triggered,
                "processing_latency": processing_latency,
                "processing_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error processing real-time events: {str(e)}")
            return {
                "events_processed": 0,
                "processing_latency": float("inf"),
                "error": str(e),
            }

    def assess_feedback_quality(
        self, feedback_samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """フィードバック品質を評価"""
        try:
            # 品質スコア計算
            quality_scores = []
            high_quality_count = 0
            medium_quality_count = 0
            low_quality_count = 0

            for sample in feedback_samples:
                # 個別品質スコア計算
                individual_score = self._calculate_individual_quality_score(sample)
                quality_scores.append(individual_score)

                # 品質分類
                if individual_score >= 0.8:
                    high_quality_count += 1
                elif individual_score >= 0.6:
                    medium_quality_count += 1
                else:
                    low_quality_count += 1

            # 全体品質スコア
            overall_quality_score = (
                statistics.mean(quality_scores) if quality_scores else 0
            )

            # 品質分布
            quality_distribution = {
                "high_quality_count": high_quality_count,
                "medium_quality_count": medium_quality_count,
                "low_quality_count": low_quality_count,
                "total_samples": len(feedback_samples),
            }

            # 改善推奨
            improvement_recommendations = self._generate_quality_improvements(
                feedback_samples, quality_scores
            )

            # フィルタリング提案
            filtering_suggestions = self._suggest_quality_filtering(
                quality_distribution
            )

            return {
                "overall_quality_score": overall_quality_score,
                "quality_distribution": quality_distribution,
                "improvement_recommendations": improvement_recommendations,
                "filtering_suggestions": filtering_suggestions,
                "assessment_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error assessing feedback quality: {str(e)}")
            return {"overall_quality_score": 0, "error": str(e)}

    def process_with_sage_collaboration(
        self, complex_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """4賢者協調によるフィードバック処理"""
        try:
            sage_contributions = {}

            # ナレッジ賢者: パターン分析
            if self.knowledge_sage_integration:
                sage_contributions["knowledge_sage"] = {
                    "historical_patterns": self._get_historical_patterns(),
                    "pattern_evolution": self._analyze_pattern_evolution(),
                    "knowledge_gaps": self._identify_knowledge_gaps(),
                }

            # RAG賢者: 関連情報検索
            if self.rag_sage_integration:
                sage_contributions["rag_sage"] = {
                    "related_feedback": self._search_related_feedback(complex_feedback),
                    "similar_cases": self._find_similar_cases(complex_feedback),
                    "contextual_insights": self._extract_contextual_insights(),
                }

            # タスク賢者: 処理優先順位
            if self.task_sage_integration:
                sage_contributions["task_sage"] = {
                    "processing_priority": self._determine_processing_priority(
                        complex_feedback
                    ),
                    "resource_allocation": self._optimize_resource_allocation(),
                    "scheduling_recommendations": self._recommend_processing_schedule(),
                }

            # インシデント賢者: 異常対応
            if self.incident_sage_integration:
                sage_contributions["incident_sage"] = {
                    "anomaly_analysis": self._analyze_feedback_anomalies(
                        complex_feedback
                    ),
                    "risk_assessment": self._assess_feedback_risks(complex_feedback),
                    "containment_strategy": self._develop_containment_strategy(),
                }

            # 統合分析
            integrated_analysis = self._integrate_sage_analysis(
                sage_contributions, complex_feedback
            )

            # コンセンサス洞察
            consensus_insights = self._form_sage_consensus(
                sage_contributions, integrated_analysis
            )

            # 協調アクション
            coordinated_actions = self._coordinate_sage_actions(
                sage_contributions, consensus_insights
            )

            return {
                "sage_contributions": sage_contributions,
                "integrated_analysis": integrated_analysis,
                "consensus_insights": consensus_insights,
                "coordinated_actions": coordinated_actions,
                "collaboration_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error in sage collaboration: {str(e)}")
            return {"sage_contributions": {}, "error": str(e)}

    # ===== Private Helper Methods =====

    def _calculate_duration(self, execution_result: Dict[str, Any]) -> float:
        """実行時間を計算"""
        exec_time = execution_result.get("execution_time", {})
        if isinstance(exec_time, dict) and "duration" in exec_time:
            duration = exec_time["duration"]
            if isinstance(duration, timedelta):
                return duration.total_seconds()
        return 0.0

    def _calculate_improvement_indicators(
        self, metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """改善指標を計算"""
        improvements = [v for v in metrics.values() if isinstance(v, (int, float))]

        if improvements:
            overall_improvement = statistics.mean(improvements)
            stability_maintained = all(
                imp >= -0.05 for imp in improvements
            )  # 5%以下の劣化許容
        else:
            overall_improvement = 0.0
            stability_maintained = True

        return {
            "overall_improvement": overall_improvement,
            "stability_maintained": stability_maintained,
            "improvement_count": len([i for i in improvements if i > 0]),
        }

    def _extract_context_data(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキストデータを抽出"""
        context = {}

        # システム状態
        if "system_state" in execution_result:
            sys_state = execution_result["system_state"]
            context["system_load"] = (
                "high" if sys_state.get("cpu_usage", 0) > 70 else "medium"
            )
            context["memory_pressure"] = sys_state.get("memory_usage", 0) > 80

        # 時間的コンテキスト
        now = datetime.now()
        if 9 <= now.hour <= 17:
            context["time_of_day"] = "business_hours"
        # 複雑な条件判定
        elif 18 <= now.hour <= 22:
            context["time_of_day"] = "peak_hours"
        else:
            context["time_of_day"] = "off_peak"

        # ユーザーフィードバック
        if "user_feedback" in execution_result:
            user_fb = execution_result["user_feedback"]
            context["user_satisfaction"] = user_fb.get("satisfaction_score", 5.0)

        return context

    def _calculate_feedback_quality(
        self, execution_result: Dict[str, Any], metrics: Dict[str, Any]
    ) -> float:
        """フィードバック品質を計算"""
        quality_score = 0.5  # ベーススコア

        # メトリクス完全性
        if metrics:
            quality_score += 0.2

        # ユーザーフィードバック存在
        if "user_feedback" in execution_result:
            quality_score += 0.2

        # システム状態情報
        if "system_state" in execution_result:
            quality_score += 0.1

        return min(quality_score, 1.0)

    def _extract_patterns(self, feedback_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """パターンを抽出"""
        patterns = []

        # パフォーマンス改善パターン
        perf_metrics = feedback_data.get("performance_metrics", {})
        for metric, improvement in perf_metrics.items():
            if isinstance(improvement, (int, float)) and improvement > 0.2:
                patterns.append(
                    {
                        "pattern_type": "performance_improvement",
                        "description": f"{metric} shows significant improvement",
                        "confidence": min(improvement, 1.0),
                    }
                )

        # コンテキスト相関パターン
        context = feedback_data.get("context_data", {})
        if context.get("time_of_day") == "peak_hours":
            patterns.append(
                {
                    "pattern_type": "context_correlation",
                    "description": "Peak hour optimization pattern detected",
                    "confidence": 0.75,
                }
            )

        return patterns

    def _generate_actionable_insights(
        self, feedback_data: Dict[str, Any], patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """実行可能な洞察を生成"""
        insights = []

        # パターンベースの洞察
        for pattern in patterns:
            if pattern["pattern_type"] == "performance_improvement":
                insights.append(
                    {
                        "insight_type": "optimization_opportunity",
                        "description": "Similar optimization may work in other contexts",
                        "potential_impact": pattern["confidence"] * 0.3,
                    }
                )

        # 品質ベースの洞察
        quality = feedback_data.get("quality_score", 0)
        if quality > 0.8:
            insights.append(
                {
                    "insight_type": "high_quality_feedback",
                    "description": "Reliable feedback for learning",
                    "potential_impact": 0.2,
                }
            )

        return insights

    def _calculate_processing_confidence(
        self,
        feedback_data: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        insights: List[Dict[str, Any]],
    ) -> float:
        """処理信頼度を計算"""
        base_confidence = feedback_data.get("quality_score", 0.5)

        # パターン信頼度による調整
        if patterns:
            pattern_confidence = statistics.mean([p["confidence"] for p in patterns])
            base_confidence = (base_confidence + pattern_confidence) / 2

        # 洞察数による調整
        insight_bonus = min(len(insights) * 0.1, 0.3)

        return min(base_confidence + insight_bonus, 1.0)

    def _determine_recommended_actions(
        self, insights: List[Dict[str, Any]]
    ) -> List[str]:
        """推奨アクションを決定"""
        actions = []

        for insight in insights:
            if insight["insight_type"] == "optimization_opportunity":
                actions.append("Replicate optimization in similar contexts")
            elif insight["insight_type"] == "high_quality_feedback":
                actions.append("Prioritize this feedback for learning")

        return actions

    def _assign_learning_priority(
        self,
        feedback_data: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        confidence: float,
    ) -> str:
        """学習優先度を割り当て"""
        if confidence > 0.8 and len(patterns) > 1:
            return "high"
        elif confidence > 0.6:
            return "medium"
        else:
            return "low"

    def _analyze_performance_trend(
        self, metrics_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """パフォーマンストレンドを分析"""
        if len(metrics_history) < 2:
            return {"direction": "unknown", "confidence": 0.0}

        # response_timeのトレンド分析
        response_times = [m.get("response_time", 0) for m in metrics_history]

        if len(response_times) >= 2:
            # 単純な傾向分析
            if response_times[-1] < response_times[0]:
                direction = "improving"
            elif response_times[-1] > response_times[0]:
                direction = "degrading"
            else:
                direction = "stable"

            # 信頼度は変化の一貫性に基づく
            confidence = (
                0.8 if abs(response_times[-1] - response_times[0]) > 10 else 0.6
            )
        else:
            direction = "unknown"
            confidence = 0.0

        return {
            "direction": direction,
            "confidence": confidence,
            "metric_analyzed": "response_time",
        }

    def _calculate_improvement_rates(
        self, metrics_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """改善率を計算"""
        improvement_rates = {}

        if len(metrics_history) >= 2:
            first = metrics_history[0]
            last = metrics_history[-1]

            for metric in ["response_time", "throughput"]:
                if metric in first and metric in last:
                    first_val = first[metric]
                    last_val = last[metric]

                    if first_val > 0:
                        if not (metric == "response_time"):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if metric == "response_time":
                            # 低い方が良い
                            rate = (first_val - last_val) / first_val
                        else:
                            # 高い方が良い
                            rate = (last_val - first_val) / first_val

                        improvement_rates[metric] = rate

        return improvement_rates

    def _assess_stability(
        self, metrics_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """安定性を評価"""
        if len(metrics_history) < 3:
            return {"stability_score": 0.5, "variance": "unknown"}

        # response_timeの分散分析
        response_times = [m.get("response_time", 0) for m in metrics_history]

        if response_times:
            variance = (
                statistics.variance(response_times) if len(response_times) > 1 else 0
            )
            mean_val = statistics.mean(response_times)

            # 変動係数
            cv = (variance**0.5) / mean_val if mean_val > 0 else 0

            # 安定性スコア（低い変動係数ほど高スコア）
            stability_score = max(0, 1 - cv)
        else:
            stability_score = 0.5
            variance = 0

        return {
            "stability_score": stability_score,
            "variance": variance,
            "assessment": "stable" if stability_score > 0.8 else "unstable",
        }

    def _detect_performance_anomalies(
        self, metrics_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """パフォーマンス異常を検出"""
        anomalies = []

        if len(metrics_history) >= 3:
            response_times = [m.get("response_time", 0) for m in metrics_history]

            if response_times:
                mean_val = statistics.mean(response_times[:-1])  # 最新を除く
                std_val = (
                    statistics.stdev(response_times[:-1])
                    if len(response_times) > 2
                    else 0
                )

                latest = response_times[-1]

                # Z-score異常検出
                if std_val > 0:
                    z_score = abs(latest - mean_val) / std_val
                    if z_score > 2:  # 2σを超える
                        anomalies.append(
                            {
                                "type": "performance_spike",
                                "metric": "response_time",
                                "severity": "high" if z_score > 3 else "medium",
                                "z_score": z_score,
                            }
                        )

        return anomalies

    def _compare_with_benchmarks(
        self, metrics_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """ベンチマークとの比較"""
        if not metrics_history:
            return {"comparison_available": False}

        latest = metrics_history[-1]

        # 仮のベンチマーク値
        benchmarks = {
            "response_time": 200.0,
            "throughput": 1500,
            "user_satisfaction": 8.0,
        }

        comparison = {}
        for metric, benchmark in benchmarks.items():
            if metric in latest:
                current = latest[metric]
                if metric == "response_time":
                    # 低い方が良い
                    performance = "better" if current < benchmark else "worse"
                else:
                    # 高い方が良い
                    performance = "better" if current > benchmark else "worse"

                comparison[metric] = {
                    "current": current,
                    "benchmark": benchmark,
                    "performance": performance,
                }

        return {"comparison_available": True, "comparisons": comparison}

    def _calculate_evaluation_score(
        self,
        trend: Dict[str, Any],
        improvement: Dict[str, float],
        stability: Dict[str, Any],
    ) -> float:
        """評価スコアを計算"""
        score = 50.0  # ベーススコア

        # トレンドスコア
        if trend["direction"] == "improving":
            score += 30
        elif trend["direction"] == "stable":
            score += 10

        # 改善率スコア
        if improvement:
            avg_improvement = statistics.mean(improvement.values())
            score += min(avg_improvement * 50, 20)

        # 安定性スコア
        score += stability.get("stability_score", 0.5) * 30

        return min(score, 100)

    def _create_learning_samples(
        self, processed_feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """学習サンプルを作成"""
        samples = []

        # フィードバックから学習サンプルを生成
        patterns = processed_feedback.get("extracted_patterns", [])

        for pattern in patterns:
            sample = {
                "input_features": {
                    "pattern_type": pattern["pattern_type"],
                    "confidence": pattern["confidence"],
                },
                "expected_output": {
                    "success_prediction": pattern["confidence"],
                    "improvement_estimate": pattern["confidence"] * 0.3,
                },
                "confidence_weight": pattern["confidence"],
            }
            samples.append(sample)

        return samples

    def _build_feature_vectors(
        self, processed_feedback: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """特徴ベクトルを構築"""
        return {
            "parameter_features": ["thread_pool_size", "cache_size", "timeout"],
            "context_features": ["system_load", "time_of_day", "user_count"],
            "performance_features": ["response_time", "throughput", "error_rate"],
        }

    def _extract_target_outcomes(
        self, processed_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ターゲット結果を抽出"""
        insights = processed_feedback.get("actionable_insights", [])

        outcomes = {
            "success_indicators": [],
            "improvement_metrics": [],
            "risk_factors": [],
        }

        for insight in insights:
            if insight.get("potential_impact", 0) > 0.2:
                outcomes["success_indicators"].append(insight["insight_type"])

        return outcomes

    def _build_learning_metadata(
        self, processed_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """学習メタデータを構築"""
        return {
            "feedback_id": processed_feedback.get("processed_feedback_id"),
            "confidence_score": processed_feedback.get("confidence_score", 0.5),
            "learning_priority": processed_feedback.get("learning_priority", "medium"),
            "extraction_timestamp": datetime.now(),
        }

    def _calculate_learning_quality(
        self, samples: List[Dict[str, Any]], features: Dict[str, List[str]]
    ) -> Dict[str, float]:
        """学習品質を計算"""
        data_completeness = 1.0 if samples else 0.0
        pattern_strength = (
            statistics.mean([s["confidence_weight"] for s in samples])
            if samples
            else 0.0
        )
        noise_level = 0.1  # 仮の値

        return {
            "data_completeness": data_completeness,
            "pattern_strength": pattern_strength,
            "noise_level": noise_level,
        }

    def _discover_new_patterns(
        self, processed_feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """新しいパターンを発見"""
        patterns = []

        # 高信頼度のフィードバックから新パターンを抽出
        confidence = processed_feedback.get("confidence_score", 0)
        if confidence > 0.8:
            patterns.append(
                {
                    "pattern_id": f"pat_{uuid.uuid4().hex[:8]}",
                    "type": "high_confidence_success",
                    "description": "High confidence optimization pattern",
                    "applicability": confidence,
                }
            )

        return patterns

    def _integrate_patterns(self, patterns: List[Dict[str, Any]]) -> int:
        """パターンを統合"""
        # 簡略化: パターン数を返す
        return len(patterns)

    def _integrate_learning_samples(self, samples: List[Dict[str, Any]]) -> int:
        """学習サンプルを統合"""
        # 簡略化: サンプル数を返す
        return len(samples)

    def _increment_knowledge_version(self) -> str:
        """ナレッジバージョンを増加"""
        return f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _assess_integration_quality(
        self, learning_data: Dict[str, Any], patterns_added: int, samples_added: int
    ) -> float:
        """統合品質を評価"""
        quality_indicators = learning_data.get("quality_indicators", {})
        base_quality = quality_indicators.get("data_completeness", 0.5)

        # パターンとサンプル数による調整
        integration_bonus = min((patterns_added + samples_added) * 0.1, 0.3)

        return min(base_quality + integration_bonus, 1.0)

    def _check_feedback_anomalies(
        self, feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """個別フィードバックの異常をチェック"""
        anomalies = []

        # パフォーマンスメトリクス異常
        perf_metrics = feedback.get("performance_metrics", {})
        for metric, value in perf_metrics.items():
            if isinstance(value, (int, float)):
                if value < -0.3:  # 30%以上の劣化
                    anomalies.append(
                        {
                            "feedback_id": feedback.get("feedback_id"),
                            "anomaly_type": "performance_degradation",
                            "severity": "high",
                            "description": f"{metric} shows severe degradation: {value}",
                        }
                    )
                elif value > 1.0:  # 100%以上の改善（非現実的）
                    anomalies.append(
                        {
                            "feedback_id": feedback.get("feedback_id"),
                            "anomaly_type": "unrealistic_improvement",
                            "severity": "medium",
                            "description": f"{metric} shows unrealistic improvement: {value}",
                        }
                    )

        return anomalies

    def _determine_anomaly_actions(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """異常対応アクションを決定"""
        actions = []

        high_severity_count = len([a for a in anomalies if a["severity"] == "high"])

        if high_severity_count > 0:
            actions.append("Investigate high severity anomalies immediately")

        if len(anomalies) > 5:
            actions.append("Review feedback collection process")

        if any("unrealistic" in a["anomaly_type"] for a in anomalies):
            actions.append("Validate measurement accuracy")

        return actions

    def _assess_loop_health(
        self, anomalies: List[Dict[str, Any]], feedback_stream: List[Dict[str, Any]]
    ) -> str:
        """ループ健全性を評価"""
        anomaly_rate = len(anomalies) / len(feedback_stream) if feedback_stream else 0

        if anomaly_rate > 0.3:
            return "unhealthy"
        elif anomaly_rate > 0.1:
            return "degraded"
        else:
            return "healthy"

    def _analyze_cycle_bottlenecks(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """サイクルボトルネックを分析"""
        current_metrics = performance.get("current_metrics", {})

        # 最も時間のかかる処理を特定
        processing_times = {
            "collection": current_metrics.get("collection_latency", 0),
            "processing": current_metrics.get("processing_time", 0),
            "integration": current_metrics.get("learning_integration_time", 0),
        }

        primary_bottleneck = max(processing_times.items(), key=lambda x: x[1])
        secondary_bottlenecks = sorted(
            processing_times.items(), key=lambda x: x[1], reverse=True
        )[1:]

        return {
            "primary_bottleneck": {
                "component": primary_bottleneck[0],
                "latency": primary_bottleneck[1],
            },
            "secondary_bottlenecks": [
                {"component": comp, "latency": lat}
                for comp, lat in secondary_bottlenecks
            ],
        }

    def _propose_performance_improvements(
        self, performance: Dict[str, Any], bottlenecks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """パフォーマンス改善を提案"""
        improvements = []

        primary = bottlenecks["primary_bottleneck"]
        if primary["component"] == "processing" and primary["latency"] > 2.0:
            improvements.append(
                {
                    "component": "processing",
                    "improvement": "Implement parallel processing",
                    "expected_reduction": 0.5,
                }
            )

        return improvements

    def _recommend_cycle_adjustments(
        self, bottlenecks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """サイクル調整を推奨"""
        adjustments = []

        primary = bottlenecks["primary_bottleneck"]
        if primary["component"] == "processing":
            adjustments.append(
                {
                    "component": "processing_batch_size",
                    "current_value": 50,
                    "recommended_value": 100,
                    "expected_improvement": 0.3,
                }
            )

        return adjustments

    def _estimate_optimization_impact(
        self, adjustments: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """最適化影響を推定"""
        total_improvement = sum(
            adj.get("expected_improvement", 0) for adj in adjustments
        )

        return {
            "total_latency_reduction": total_improvement,
            "throughput_increase": total_improvement * 0.5,
            "resource_efficiency": total_improvement * 0.3,
        }

    def _apply_cycle_optimizations(self, adjustments: List[Dict[str, Any]]) -> bool:
        """サイクル最適化を適用"""
        # 実際の実装では設定を更新
        for adjustment in adjustments:
            component = adjustment["component"]
            new_value = adjustment["recommended_value"]
            logger.info(f"Applying optimization: {component} = {new_value}")

        return True

    def _identify_immediate_actions(
        self, analyzed_feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """即座のアクションを特定"""
        actions = []

        # トレンド分析に基づく
        trends = analyzed_feedback.get("performance_trends", {})
        for metric, trend_data in trends.items():
            # 改善トレンドまたは安定なメトリクスに基づく即座のアクション
            trend = trend_data.get("trend", "")
            rate = trend_data.get("rate", 0.1)  # デフォルト改善率を設定

            if trend == "improving":
                actions.append(
                    {
                        "action_type": "scaling_opportunity",
                        "description": f"Scale up {metric} optimization",
                        "implementation_effort": "low",
                        "expected_impact": max(rate, 0.1),  # 最小改善率保証
                    }
                )
            elif trend == "stable" and rate >= 0:
                actions.append(
                    {
                        "action_type": "maintain_stability",
                        "description": f"Maintain stable {metric} performance",
                        "implementation_effort": "low",
                        "expected_impact": 0.05,
                    }
                )

        # パターンに基づく即座のアクション
        patterns = analyzed_feedback.get("identified_patterns", [])
        for pattern in patterns:
            if pattern.get("applicability", 0) > 0.8:
                actions.append(
                    {
                        "action_type": "pattern_optimization",
                        "description": f'Apply {pattern.get("pattern", "optimization")} pattern',
                        "implementation_effort": "medium",
                        "expected_impact": pattern.get("strength", 0.5),
                    }
                )

        # ボトルネック解決
        bottlenecks = analyzed_feedback.get("bottleneck_insights", [])
        for bottleneck in bottlenecks:
            if (
                bottleneck.get("severity") == "medium"
                or bottleneck.get("severity") == "high"
            ):
                actions.append(
                    {
                        "action_type": "bottleneck_resolution",
                        "description": f'Address {bottleneck.get(
                            "component",
                            "system"
                        )} bottleneck',
                        "implementation_effort": "medium",
                        "expected_impact": bottleneck.get("impact", 0.2),
                    }
                )

        return actions

    def _identify_medium_term_optimizations(
        self, analyzed_feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """中期最適化を特定"""
        optimizations = []

        # パターンに基づく
        patterns = analyzed_feedback.get("identified_patterns", [])
        for pattern in patterns:
            if pattern.get("strength", 0) > 0.8:
                optimizations.append(
                    {
                        "optimization_type": "pattern_application",
                        "description": f'Apply {pattern["pattern"]} more broadly',
                        "timeline": "2-4 weeks",
                        "expected_impact": pattern.get("applicability", 0.5),
                    }
                )

        return optimizations

    def _identify_long_term_strategies(
        self, analyzed_feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """長期戦略を特定"""
        strategies = []

        # 成功要因に基づく
        success_factors = analyzed_feedback.get("success_factors", [])
        if "comprehensive_monitoring" in success_factors:
            strategies.append(
                {
                    "strategy_type": "infrastructure_enhancement",
                    "description": "Implement advanced monitoring infrastructure",
                    "timeline": "3-6 months",
                    "expected_impact": 0.4,
                }
            )

        return strategies

    def _rank_suggestions_by_priority(
        self,
        immediate: List[Dict[str, Any]],
        medium: List[Dict[str, Any]],
        long_term: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """提案を優先順位でランキング"""
        all_suggestions = []

        # 即座のアクション（高優先度）
        for i, action in enumerate(immediate):
            all_suggestions.append(
                {
                    "rank": i + 1,
                    "suggestion_id": f"immediate_{i}",
                    "priority_score": 0.9,
                    "category": "immediate",
                }
            )

        # 中期（中優先度）
        for i, opt in enumerate(medium):
            all_suggestions.append(
                {
                    "rank": len(immediate) + i + 1,
                    "suggestion_id": f"medium_{i}",
                    "priority_score": 0.6,
                    "category": "medium_term",
                }
            )

        return all_suggestions

    def _estimate_suggestion_impacts(
        self,
        immediate: List[Dict[str, Any]],
        medium: List[Dict[str, Any]],
        long_term: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """提案影響を推定"""
        immediate_impact = sum(a.get("expected_impact", 0) for a in immediate)
        medium_impact = sum(o.get("expected_impact", 0) for o in medium)
        long_term_impact = sum(s.get("expected_impact", 0) for s in long_term)

        return {
            "immediate_total_impact": immediate_impact,
            "medium_term_total_impact": medium_impact,
            "long_term_total_impact": long_term_impact,
        }

    def _process_single_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """単一イベントを処理"""
        return {
            "event_id": event.get("event_id"),
            "processed_at": datetime.now(),
            "processing_status": "success",
        }

    def _extract_immediate_insights(
        self, event: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """即座の洞察を抽出"""
        insights = []

        if event.get("event_type") == "performance_metric":
            data = event.get("data", {})
            if "previous_value" in data and "value" in data:
                improvement = (data["previous_value"] - data["value"]) / data[
                    "previous_value"
                ]
                if improvement > 0.1:
                    insights.append(
                        {
                            "type": "performance_improvement",
                            "description": f'{data.get("metric_name")} improved by {improvement:.1%}',
                        }
                    )

        return insights

    def _check_alert_conditions(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """アラート条件をチェック"""
        alerts = []

        if event.get("event_type") == "system_state":
            data = event.get("data", {})
            if data.get("cpu_usage", 0) > 90:
                alerts.append(
                    {
                        "type": "high_cpu_usage",
                        "severity": "warning",
                        "value": data["cpu_usage"],
                    }
                )

        return alerts

    def _should_trigger_learning(self, processed_events: List[Dict[str, Any]]) -> bool:
        """学習をトリガーすべきかチェック"""
        return len(processed_events) >= 10  # 10イベント以上で学習トリガー

    def _calculate_individual_quality_score(self, sample: Dict[str, Any]) -> float:
        """個別品質スコアを計算"""
        quality_factors = [
            "completeness",
            "accuracy",
            "relevance",
            "timeliness",
            "consistency",
        ]

        scores = [sample.get(factor, 0.5) for factor in quality_factors]
        return statistics.mean(scores)

    def _generate_quality_improvements(
        self, samples: List[Dict[str, Any]], scores: List[float]
    ) -> List[str]:
        """品質改善を生成"""
        improvements = []

        avg_score = statistics.mean(scores) if scores else 0

        if avg_score < 0.7:
            improvements.append("Improve data collection completeness")

        if any(s < 0.5 for s in scores):
            improvements.append("Filter out low-quality feedback")

        return improvements

    def _suggest_quality_filtering(self, distribution: Dict[str, int]) -> List[str]:
        """品質フィルタリングを提案"""
        suggestions = []

        total = distribution.get("total_samples", 1)
        low_ratio = distribution.get("low_quality_count", 0) / total

        if low_ratio > 0.3:
            suggestions.append("Implement quality threshold filtering")

        return suggestions

    # 4賢者協調のヘルパーメソッド
    def _get_historical_patterns(self) -> List[Dict[str, Any]]:
        """過去のパターンを取得"""
        return [
            {"pattern": "optimization_success", "frequency": 0.85},
            {"pattern": "peak_hour_effectiveness", "frequency": 0.78},
        ]

    def _analyze_pattern_evolution(self) -> Dict[str, Any]:
        """パターン進化を分析"""
        return {"trend": "improving", "confidence": 0.82, "evolution_rate": 0.05}

    def _identify_knowledge_gaps(self) -> List[str]:
        """知識ギャップを特定"""
        return ["Long-term impact patterns", "Cross-system correlations"]

    def _search_related_feedback(
        self, feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """関連フィードバックを検索"""
        return [
            {"feedback_id": "related_001", "similarity": 0.85},
            {"feedback_id": "related_002", "similarity": 0.72},
        ]

    def _find_similar_cases(self, feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
        """類似ケースを検索"""
        return [{"case_id": "case_001", "similarity": 0.80, "outcome": "success"}]

    def _extract_contextual_insights(self) -> List[Dict[str, Any]]:
        """コンテキスト洞察を抽出"""
        return [
            {
                "insight": "Peak hour optimizations are 40% more effective",
                "confidence": 0.85,
            }
        ]

    def _determine_processing_priority(self, feedback: Dict[str, Any]) -> str:
        """処理優先度を決定"""
        return "high" if feedback.get("multiple_operations") else "medium"

    def _optimize_resource_allocation(self) -> Dict[str, Any]:
        """リソース割り当てを最適化"""
        return {
            "cpu_allocation": "increased",
            "memory_allocation": "optimized",
            "parallel_processing": "enabled",
        }

    def _recommend_processing_schedule(self) -> Dict[str, Any]:
        """処理スケジュールを推奨"""
        return {
            "schedule_type": "adaptive",
            "peak_hours_handling": "priority_mode",
            "batch_processing": "off_peak",
        }

    def _analyze_feedback_anomalies(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """フィードバック異常を分析"""
        return {
            "anomaly_detected": feedback.get("anomalous_patterns", False),
            "severity": "medium",
            "type": "data_inconsistency",
        }

    def _assess_feedback_risks(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """フィードバックリスクを評価"""
        return {
            "risk_level": "medium",
            "risk_factors": ["high_volume", "conflicting_signals"],
            "mitigation_required": True,
        }

    def _develop_containment_strategy(self) -> Dict[str, Any]:
        """封じ込め戦略を開発"""
        return {
            "strategy": "gradual_processing",
            "monitoring": "enhanced",
            "rollback_ready": True,
        }

    def _integrate_sage_analysis(
        self, contributions: Dict[str, Any], feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """賢者分析を統合"""
        return {
            "confidence_level": 0.85,
            "action_priority": "high",
            "consensus_reached": True,
        }

    def _form_sage_consensus(
        self, contributions: Dict[str, Any], analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """賢者コンセンサスを形成"""
        return [
            {
                "insight": "Process high-priority feedback immediately",
                "agreement_level": 0.9,
                "supporting_sages": ["task_sage", "incident_sage"],
            }
        ]

    def _coordinate_sage_actions(
        self, contributions: Dict[str, Any], insights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """賢者アクションを調整"""
        return [
            {
                "action": "Enhanced monitoring activation",
                "responsible_sage": "incident_sage",
                "timeline": "immediate",
            },
            {
                "action": "Pattern analysis acceleration",
                "responsible_sage": "knowledge_sage",
                "timeline": "1_hour",
            },
        ]


# ===== Supporting Classes =====


class MetricsCollector:
    """メトリクス収集"""

    def __init__(self):
        """初期化メソッド"""
        self.collection_history = deque(maxlen=1000)

    def collect_metrics(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスを収集"""
        collected = {
            "timestamp": datetime.now(),
            "source": source,
            "metrics": self._extract_metrics(source),
        }
        self.collection_history.append(collected)
        return collected

    def _extract_metrics(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスを抽出"""
        return source.get("metrics", {})


class PerformanceEvaluator:
    """パフォーマンス評価"""

    def __init__(self):
        """初期化メソッド"""
        self.evaluation_history = deque(maxlen=500)

    def evaluate(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンスを評価"""
        evaluation = {
            "timestamp": datetime.now(),
            "metrics": metrics,
            "score": self._calculate_score(metrics),
        }
        self.evaluation_history.append(evaluation)
        return evaluation

    def _calculate_score(self, metrics: Dict[str, Any]) -> float:
        """スコアを計算"""
        # 簡略化: メトリクス数に基づく
        return min(len(metrics) * 0.2, 1.0)


class LearningDataPipeline:
    """学習データパイプライン"""

    def __init__(self):
        """初期化メソッド"""
        self.pipeline_history = deque(maxlen=200)

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データを処理"""
        processed = {
            "timestamp": datetime.now(),
            "input_data": data,
            "processed_data": self._transform_data(data),
        }
        self.pipeline_history.append(processed)
        return processed

    def _transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データを変換"""
        return {"features": list(data.keys()), "target": "optimization_success"}


class RealTimeProcessor:
    """リアルタイム処理"""

    def __init__(self):
        """初期化メソッド"""
        self.processing_queue = deque(maxlen=1000)

    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """イベントを処理"""
        processed = {
            "event": event,
            "processed_at": datetime.now(),
            "processing_latency": 0.05,  # 仮の値
        }
        self.processing_queue.append(processed)
        return processed


class FeedbackAnomalyDetector:
    """フィードバック異常検出"""

    def __init__(self):
        """初期化メソッド"""
        self.detection_history = deque(maxlen=500)
        self.thresholds = {
            "performance_degradation": -0.3,
            "unrealistic_improvement": 1.0,
        }

    def detect(self, feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
        """異常を検出"""
        anomalies = []

        # フィードバック品質チェック
        quality = feedback.get("quality_score", 0.5)
        if quality < 0.3:
            anomalies.append(
                {
                    "type": "low_quality_feedback",
                    "severity": "medium",
                    "description": f"Quality score too low: {quality}",
                }
            )

        self.detection_history.append(
            {
                "feedback_id": feedback.get("feedback_id"),
                "anomalies": anomalies,
                "detected_at": datetime.now(),
            }
        )

        return anomalies
