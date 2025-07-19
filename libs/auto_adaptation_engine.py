#!/usr/bin/env python3
"""
Auto Adaptation Engine - 自動適応エンジン
システムパラメータの動的調整と継続的最適化を実現

4賢者との連携:
📚 ナレッジ賢者: 段階的な調整で安定性を保つパターンの実装
🔍 RAG賢者: 類似システムからの教訓を活かした安全な適応
📋 タスク賢者: 優先順位に基づく適応戦略の実行管理
🚨 インシデント賢者: 過剰適応と不安定化のリスク管理
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


class AutoAdaptationEngine:
    """自動適応エンジン"""

    def __init__(self):
        """AutoAdaptationEngine 初期化"""
        self.engine_id = f"adapt_engine_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 安全性機構
        self.safety_constraints = SafetyConstraints()
        self.rollback_manager = RollbackManager()
        self.parameter_optimizer = ParameterOptimizer()

        # 適応管理
        self.active_adaptations = {}
        self.adaptation_history = deque(maxlen=1000)
        self.learned_patterns = defaultdict(list)

        # 設定
        self.adaptation_config = {
            "max_parameter_change": 0.5,  # 50%
            "min_confidence_threshold": 0.7,
            "stability_window": timedelta(minutes=5),
            "gradual_steps_max": 5,
        }

        # 4賢者統合フラグ
        self.knowledge_sage_integration = True
        self.rag_sage_integration = True
        self.task_sage_integration = True
        self.incident_sage_integration = True

        # ナレッジベースパス
        self.knowledge_base_path = (
            PROJECT_ROOT / "knowledge_base" / "adaptation_history"
        )
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"AutoAdaptationEngine initialized: {self.engine_id}")

    def adapt(
        self, metrics: Dict[str, Any], confidence_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """メトリクスに基づいて自動適応"""
        try:
            # 1. 現在のパフォーマンス評価
            performance_analysis = self.analyze_performance(metrics)

            if not performance_analysis.get("adaptation_needed", False):
                return {
                    "adapted": False,
                    "reason": "Performance is acceptable",
                    "current_score": performance_analysis.get("performance_score", 0),
                }

            # 2. 現在のパラメータ取得（仮）
            current_parameters = self._get_current_parameters()

            # 3. 最適パラメータの推定
            optimal_params = self.calculate_optimal_parameters(
                performance_analysis, current_parameters
            )

            # 4. 安全性チェック
            safety_check = self.check_safety_constraints(optimal_params)
            if not safety_check["is_safe"]:
                optimal_params = safety_check.get("adjusted_parameters", optimal_params)

            # 5. 段階的適用
            if optimal_params.get("adaptation_strategy") == "gradual":
                application_result = self.apply_adaptation(optimal_params)
                return {
                    "adapted": True,
                    "adaptation_id": application_result["adaptation_id"],
                    "strategy": "gradual",
                    "steps": optimal_params.get("gradual_steps", []),
                }

            return {"adapted": False, "reason": "Adaptation criteria not met"}

        except Exception as e:
            logger.error(f"Error during adaptation: {str(e)}")
            return {"adapted": False, "error": str(e)}

    def analyze_performance(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンスを分析"""
        try:
            performance_score = 100.0
            degraded_metrics = []
            bottlenecks = []

            # メトリクス評価
            for metric_name, metric_data in current_metrics.items():
                if (
                    isinstance(metric_data, dict)
                    and "current" in metric_data
                    and "baseline" in metric_data
                ):
                    current = metric_data["current"]
                    baseline = metric_data["baseline"]

                    # 劣化率計算
                    if baseline > 0:
                        if metric_name in ["response_time", "error_rate"]:
                            # 低い方が良いメトリクス
                            degradation = (current - baseline) / baseline
                        else:
                            # 高い方が良いメトリクス（throughput等）
                            degradation = (baseline - current) / baseline

                        if degradation > 0.1:  # 10%以上の劣化
                            degraded_metrics.append(metric_name)
                            performance_score -= degradation * 50

                            # ボトルネック特定
                            if degradation > 0.2:
                                bottlenecks.append(
                                    {
                                        "type": self._identify_bottleneck_type(
                                            metric_name
                                        ),
                                        "severity": "high"
                                        if degradation > 0.3
                                        else "medium",
                                    }
                                )

            # リソース使用率チェック
            if "resource_utilization" in current_metrics:
                resources = current_metrics["resource_utilization"]
                if resources.get("cpu", 0) > 70:
                    bottlenecks.append({"type": "cpu", "severity": "high"})
                if resources.get("memory", 0) > 80:
                    bottlenecks.append({"type": "memory", "severity": "high"})

            # 適応必要性判定
            adaptation_needed = len(degraded_metrics) > 0 or performance_score < 80

            # 信頼レベル計算
            confidence_level = self._calculate_confidence(current_metrics)

            return {
                "performance_score": max(0, performance_score),
                "degraded_metrics": degraded_metrics,
                "bottlenecks": bottlenecks,
                "adaptation_needed": adaptation_needed,
                "confidence_level": confidence_level,
                "analysis_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error analyzing performance: {str(e)}")
            return {
                "performance_score": 0,
                "degraded_metrics": [],
                "bottlenecks": [],
                "adaptation_needed": False,
                "confidence_level": 0,
                "error": str(e),
            }

    def calculate_optimal_parameters(
        self, performance_analysis: Dict[str, Any], current_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """最適パラメータを計算"""
        try:
            recommended_parameters = current_parameters.copy()

            # ボトルネックに基づく最適化
            for bottleneck in performance_analysis.get("bottlenecks", []):
                if (
                    bottleneck["type"] == "thread_pool"
                    and bottleneck["severity"] == "high"
                ):
                    # スレッドプールサイズを増やす
                    current_size = current_parameters.get("thread_pool_size", 10)
                    recommended_parameters["thread_pool_size"] = min(
                        current_size * 2, 100
                    )

                elif (
                    bottleneck["type"] == "cache_size"
                    and bottleneck["severity"] == "medium"
                ):
                    # キャッシュサイズを増やす
                    current_cache = current_parameters.get("cache_size", 100)
                    recommended_parameters["cache_size"] = min(current_cache * 2, 1000)

                elif bottleneck["type"] == "cpu":
                    # CPU最適化: バッチサイズ調整等
                    if "batch_size" in current_parameters:
                        recommended_parameters["batch_size"] = max(
                            current_parameters["batch_size"] // 2, 1
                        )

            # 期待される改善度計算
            expected_improvement = self._estimate_improvement(
                current_parameters, recommended_parameters
            )

            # 適応戦略決定
            parameter_change_ratio = self._calculate_change_ratio(
                current_parameters, recommended_parameters
            )

            adaptation_strategy = (
                "gradual" if parameter_change_ratio > 0.3 else "immediate"
            )

            # リスク評価
            risk_assessment = self._assess_adaptation_risk(
                current_parameters, recommended_parameters
            )

            # 段階的適応計画
            gradual_steps = []
            if adaptation_strategy == "gradual":
                gradual_steps = self._create_gradual_steps(
                    current_parameters, recommended_parameters
                )

            return {
                "recommended_parameters": recommended_parameters,
                "expected_improvement": expected_improvement,
                "adaptation_strategy": adaptation_strategy,
                "risk_assessment": risk_assessment,
                "gradual_steps": gradual_steps,
                "confidence_score": performance_analysis.get("confidence_level", 0.8),
            }

        except Exception as e:
            logger.error(f"Error calculating optimal parameters: {str(e)}")
            return {"recommended_parameters": current_parameters, "error": str(e)}

    def apply_adaptation(self, adaptation_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """適応を適用"""
        try:
            adaptation_id = f"adapt_{uuid.uuid4().hex[:8]}"

            # 現在のパラメータをチェックポイントとして保存
            rollback_point = self._create_rollback_point()

            # 段階的適応の場合
            if adaptation_strategy.get("adaptation_strategy") == "gradual":
                steps = adaptation_strategy.get("gradual_steps", [])
                if steps:
                    # 最初のステップを適用
                    first_step = steps[0]
                    applied_params = self._apply_parameters(first_step["parameters"])

                    adaptation_state = {
                        "adaptation_id": adaptation_id,
                        "status": "in_progress",
                        "current_step": 1,
                        "total_steps": len(steps),
                        "applied_parameters": applied_params,
                        "rollback_point": rollback_point,
                        "start_time": datetime.now(),
                        "strategy": adaptation_strategy,
                    }

                    # アクティブな適応として記録
                    self.active_adaptations[adaptation_id] = adaptation_state

                    return adaptation_state

            # 即時適応の場合
            applied_params = self._apply_parameters(
                adaptation_strategy["recommended_parameters"]
            )

            return {
                "adaptation_id": adaptation_id,
                "status": "completed",
                "current_step": 1,
                "applied_parameters": applied_params,
                "rollback_point": rollback_point,
                "start_time": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error applying adaptation: {str(e)}")
            return {"adaptation_id": None, "status": "error", "error": str(e)}

    def monitor_adaptation(
        self, adaptation_state: Dict[str, Any], current_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """適応をモニタリング"""
        try:
            # 進捗計算
            adaptation_progress = self._calculate_adaptation_progress(
                adaptation_state, current_metrics
            )

            # 成功基準チェック
            criteria_met = self._check_success_criteria(
                adaptation_state, current_metrics
            )

            # 異常検出
            anomalies = self._detect_adaptation_anomalies(current_metrics)

            # 推奨アクション決定
            recommendation = self._determine_recommendation(
                adaptation_progress, criteria_met, anomalies
            )

            # 詳細メトリクス
            detailed_metrics = self._analyze_detailed_metrics(current_metrics)

            return {
                "adaptation_progress": adaptation_progress,
                "criteria_met": criteria_met,
                "anomalies_detected": len(anomalies) > 0,
                "anomalies": anomalies,
                "recommendation": recommendation,
                "detailed_metrics": detailed_metrics,
                "monitoring_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error monitoring adaptation: {str(e)}")
            return {"recommendation": "error", "error": str(e)}

    def rollback_if_needed(
        self, current_state: Dict[str, Any], rollback_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """必要に応じてロールバック"""
        try:
            rollback_reasons = []

            # エラー率チェック
            current_error_rate = (
                current_state.get("metrics", {}).get("error_rate", {}).get("current", 0)
            )

            if current_error_rate > rollback_criteria.get("error_rate_threshold", 0.05):
                rollback_reasons.append(
                    f"Error rate {current_error_rate} exceeds threshold"
                )

            # パフォーマンス劣化チェック
            for metric_name, metric_data in current_state.get("metrics", {}).items():
                if isinstance(metric_data, dict):
                    current = metric_data.get("current", 0)
                    baseline = metric_data.get("baseline", 1)

                    if baseline > 0:
                        if metric_name in ["response_time", "error_rate"]:
                            # 高い方が悪いメトリクス
                            degradation = (current - baseline) / baseline
                        else:
                            # 低い方が悪いメトリクス（throughput等）
                            degradation = (baseline - current) / baseline

                        threshold = rollback_criteria.get(
                            "performance_degradation_threshold", -0.1
                        )
                        if degradation > abs(threshold):  # 閾値の絶対値で比較
                            rollback_reasons.append(
                                f"performance_degradation: {metric_name} degraded by {degradation*100:.1f}%"
                            )

            # ロールバック実行判定
            rollback_needed = len(rollback_reasons) > 0

            if rollback_needed:
                # ロールバック実行
                rollback_point = current_state.get("rollback_point", {})
                restored_params = self._execute_rollback(rollback_point)

                return {
                    "rollback_needed": True,
                    "rollback_executed": True,
                    "rollback_reason": rollback_reasons,
                    "restored_parameters": restored_params,
                    "rollback_time": datetime.now(),
                }

            return {
                "rollback_needed": False,
                "rollback_executed": False,
                "rollback_reason": [],
                "restored_parameters": None,
                "rollback_time": None,
            }

        except Exception as e:
            logger.error(f"Error during rollback check: {str(e)}")
            return {
                "rollback_needed": False,
                "rollback_executed": False,
                "error": str(e),
            }

    def save_adaptation_history(
        self, completed_adaptation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """適応履歴を保存（ナレッジ賢者連携）"""
        try:
            history_id = f"hist_{uuid.uuid4().hex[:8]}"

            # パターン抽出
            patterns = self._extract_adaptation_patterns(completed_adaptation)

            # 履歴データ構築
            history_data = {
                "history_id": history_id,
                "adaptation": completed_adaptation,
                "patterns": patterns,
                "saved_at": datetime.now(),
            }

            # ファイルに保存
            save_path = self.knowledge_base_path / f"{history_id}_adaptation.json"
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=2, default=str)

            # メモリ内履歴に追加
            self.adaptation_history.append(history_data)

            # ナレッジ統合
            knowledge_integration = {
                "status": "success",
                "patterns_count": len(patterns),
                "knowledge_updated": True,
            }

            return {
                "saved": True,
                "history_id": history_id,
                "knowledge_base_path": str(save_path),
                "patterns_extracted": patterns,
                "knowledge_integration": knowledge_integration,
            }

        except Exception as e:
            logger.error(f"Error saving adaptation history: {str(e)}")
            return {"saved": False, "error": str(e)}

    def learn_from_adaptation(
        self, adaptation_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """適応結果から学習"""
        try:
            learned_patterns = []
            success_strategies = []
            failure_patterns = []

            for result in adaptation_results:
                if result.get("success"):
                    # 成功パターン抽出
                    strategy = self._extract_success_strategy(result)
                    success_strategies.append(strategy)

                    # パターン学習
                    pattern = {
                        "type": "success",
                        "parameter": list(result.get("parameter_changes", {}).keys())[
                            0
                        ],
                        "change_ratio": self._calculate_change_ratio_from_result(
                            result
                        ),
                        "improvement": result.get("improvement", 0),
                    }
                    learned_patterns.append(pattern)
                else:
                    # 失敗パターン抽出
                    failure = self._extract_failure_pattern(result)
                    failure_patterns.append(failure)

            # 最適化ルール生成
            optimization_rules = self._generate_optimization_rules(
                success_strategies, failure_patterns
            )

            # 信頼度スコア計算
            confidence_scores = self._calculate_strategy_confidence(
                success_strategies, failure_patterns
            )

            # 学習結果を内部パターンライブラリに追加
            for pattern in learned_patterns:
                pattern_key = pattern.get("parameter", "unknown")
                self.learned_patterns[pattern_key].append(pattern)

            return {
                "learned_patterns": learned_patterns,
                "success_strategies": success_strategies,
                "failure_patterns": failure_patterns,
                "optimization_rules": optimization_rules,
                "confidence_scores": confidence_scores,
                "learning_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error learning from adaptation: {str(e)}")
            return {"learned_patterns": [], "error": str(e)}

    def check_safety_constraints(
        self, adaptation_proposal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """安全性制約をチェック（インシデント賢者連携）"""
        try:
            violations = []
            is_safe = True

            recommended = adaptation_proposal.get("recommended_parameters", {})

            # パラメータ制約チェック
            constraints = self.safety_constraints.get_constraints()

            for param, value in recommended.items():
                if param in constraints:
                    constraint = constraints[param]
                    if value < constraint.get(
                        "min", float("-inf")
                    ) or value > constraint.get("max", float("inf")):
                        violations.append(
                            {
                                "parameter": param,
                                "value": value,
                                "constraint": constraint,
                                "type": "out_of_bounds",
                            }
                        )
                        is_safe = False

            # リスクレベル評価
            risk_level = self._evaluate_risk_level(violations, recommended)

            # インシデント確率計算
            incident_probability = self._calculate_incident_probability(
                recommended, violations
            )

            # パラメータ調整
            adjusted_parameters = recommended.copy()
            if not is_safe:
                adjusted_parameters = self._adjust_parameters_for_safety(
                    recommended, violations
                )

            return {
                "is_safe": is_safe,
                "violations": violations,
                "adjusted_parameters": adjusted_parameters,
                "risk_level": risk_level,
                "incident_probability": incident_probability,
                "safety_check_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error checking safety constraints: {str(e)}")
            return {"is_safe": False, "error": str(e)}

    def create_gradual_adaptation_plan(
        self, adaptation_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """段階的適応計画を作成"""
        try:
            current = adaptation_request["current_parameters"]
            target = adaptation_request["target_parameters"]
            speed = adaptation_request.get("adaptation_speed", "moderate")

            # ステップ数決定
            change_magnitude = self._calculate_total_change(current, target)

            if speed == "conservative":
                num_steps = min(5, max(3, int(change_magnitude * 10)))
            elif speed == "aggressive":
                num_steps = 2
            else:  # moderate
                num_steps = min(4, max(2, int(change_magnitude * 5)))

            # ステップ生成
            steps = []
            for i in range(num_steps):
                progress = (i + 1) / num_steps
                step_params = {}

                for param, target_value in target.items():
                    if param in current:
                        current_value = current[param]
                        # 線形補間
                        step_value = (
                            current_value + (target_value - current_value) * progress
                        )
                        step_params[param] = round(step_value)

                steps.append(
                    {
                        "step_number": i + 1,
                        "parameters": step_params,
                        "duration": f"{10 * (i + 1)}_minutes",
                        "success_criteria": {
                            "stability_time": "2_minutes",
                            "error_rate_threshold": 0.05,
                            "performance_improvement": 0.05 * (i + 1),
                        },
                    }
                )

            # 総実行時間推定
            total_duration = sum(10 * (i + 1) for i in range(num_steps))

            # リスク緩和策
            risk_mitigation = {
                "monitoring_frequency": "high",
                "rollback_enabled": True,
                "alert_thresholds": {"error_rate": 0.05, "response_time_increase": 1.5},
            }

            return {
                "total_steps": num_steps,
                "steps": steps,
                "estimated_duration": f"{total_duration}_minutes",
                "risk_mitigation": risk_mitigation,
                "adaptation_speed": speed,
            }

        except Exception as e:
            logger.error(f"Error creating gradual adaptation plan: {str(e)}")
            return {"total_steps": 0, "error": str(e)}

    def create_sage_coordinated_adaptation(
        self, complex_scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """4賢者協調による適応計画作成"""
        try:
            sage_contributions = {}

            # ナレッジ賢者: 過去の成功パターン
            if self.knowledge_sage_integration:
                sage_contributions["knowledge_sage"] = {
                    "successful_patterns": self._get_historical_success_patterns(),
                    "failure_patterns": self._get_historical_failure_patterns(),
                    "recommendation": "Apply proven gradual adaptation pattern",
                }

            # RAG賢者: 類似ケースの参照
            if self.rag_sage_integration:
                sage_contributions["rag_sage"] = {
                    "similar_cases": self._find_similar_adaptation_cases(
                        complex_scenario
                    ),
                    "best_practices": ["Monitor continuously", "Use canary deployment"],
                    "confidence": 0.85,
                }

            # タスク賢者: 実行優先順位
            if self.task_sage_integration:
                sage_contributions["task_sage"] = {
                    "priority_order": [
                        "stabilize_errors",
                        "improve_performance",
                        "optimize_resources",
                    ],
                    "execution_timeline": "2_hours_total",
                    "parallelization": False,
                }

            # インシデント賢者: リスク評価
            if self.incident_sage_integration:
                sage_contributions["incident_sage"] = {
                    "risk_level": "medium",
                    "potential_incidents": [
                        "performance_degradation",
                        "memory_pressure",
                    ],
                    "mitigation_required": True,
                    "safety_measures": ["gradual_rollout", "continuous_monitoring"],
                }

            # 統合戦略作成
            integrated_strategy = self._integrate_sage_recommendations(
                sage_contributions, complex_scenario
            )

            # 実行計画
            execution_plan = self._create_integrated_execution_plan(
                integrated_strategy, sage_contributions
            )

            # 成功確率推定
            success_probability = self._estimate_success_with_sages(
                integrated_strategy, sage_contributions
            )

            return {
                "sage_contributions": sage_contributions,
                "integrated_strategy": integrated_strategy,
                "execution_plan": execution_plan,
                "success_probability": success_probability,
                "coordination_timestamp": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error in sage coordination: {str(e)}")
            return {"sage_contributions": {}, "error": str(e)}

    # ===== Private Helper Methods =====

    def _get_current_parameters(self) -> Dict[str, Any]:
        """現在のパラメータを取得（仮実装）"""
        return {
            "thread_pool_size": 10,
            "cache_size": 100,
            "connection_pool_size": 50,
            "batch_size": 20,
            "timeout_seconds": 30,
        }

    def _identify_bottleneck_type(self, metric_name: str) -> str:
        """メトリクス名からボトルネックタイプを特定"""
        if "response" in metric_name.lower():
            return "thread_pool"
        elif "throughput" in metric_name.lower():
            return "connection_pool"
        elif "cache" in metric_name.lower():
            return "cache_size"
        else:
            return "general"

    def _calculate_confidence(self, metrics: Dict[str, Any]) -> float:
        """信頼レベルを計算"""
        confidence = 1.0

        # サンプル数による信頼度調整
        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict):
                samples = metric_data.get("samples", 0)
                if samples < 100:
                    confidence *= 0.8
                elif samples < 1000:
                    confidence *= 0.9

        return confidence

    def _estimate_improvement(
        self, current: Dict[str, Any], recommended: Dict[str, Any]
    ) -> float:
        """期待される改善度を推定"""
        improvement = 0.0

        # パラメータ変更に基づく改善推定
        for param, new_value in recommended.items():
            if param in current:
                old_value = current[param]
                if old_value > 0:
                    change_ratio = (new_value - old_value) / old_value

                    # パラメータ別の影響係数
                    impact_factor = {
                        "thread_pool_size": 0.3,
                        "cache_size": 0.2,
                        "connection_pool_size": 0.2,
                        "batch_size": 0.15,
                    }.get(param, 0.1)

                    improvement += change_ratio * impact_factor

        return min(improvement, 0.5)  # 最大50%改善

    def _calculate_change_ratio(
        self, current: Dict[str, Any], recommended: Dict[str, Any]
    ) -> float:
        """パラメータ変更率を計算"""
        if not current:
            return 0.0

        total_change = 0.0
        param_count = 0

        for param, new_value in recommended.items():
            if param in current and current[param] > 0:
                old_value = current[param]
                change = abs(new_value - old_value) / old_value
                total_change += change
                param_count += 1

        return total_change / param_count if param_count > 0 else 0.0

    def _assess_adaptation_risk(
        self, current: Dict[str, Any], recommended: Dict[str, Any]
    ) -> Dict[str, Any]:
        """適応リスクを評価"""
        risk_score = 0.0
        risk_factors = []

        # 大幅な変更はリスク
        change_ratio = self._calculate_change_ratio(current, recommended)
        if change_ratio > 0.5:
            risk_score += 0.3
            risk_factors.append("Large parameter change")

        # 特定のパラメータのリスク評価
        if "timeout_seconds" in recommended:
            if recommended["timeout_seconds"] < 10:
                risk_score += 0.2
                risk_factors.append("Very short timeout")

        return {
            "risk_score": risk_score,
            "risk_level": "high"
            if risk_score > 0.5
            else "medium"
            if risk_score > 0.3
            else "low",
            "risk_factors": risk_factors,
        }

    def _create_gradual_steps(
        self, current: Dict[str, Any], target: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """段階的適応のステップを作成"""
        steps = []
        num_steps = 3  # デフォルト

        for i in range(num_steps):
            progress = (i + 1) / num_steps
            step_params = {}

            for param, target_value in target.items():
                if param in current:
                    current_value = current[param]
                    step_value = (
                        current_value + (target_value - current_value) * progress
                    )
                    step_params[param] = (
                        int(step_value)
                        if isinstance(current_value, int)
                        else step_value
                    )

            steps.append(
                {
                    "step_number": i + 1,
                    "parameters": step_params,
                    "duration": f"{10 * (i + 1)}_minutes",
                    "success_criteria": {"response_time_improvement": 0.1 * (i + 1)},
                }
            )

        return steps

    def _create_rollback_point(self) -> Dict[str, Any]:
        """ロールバックポイントを作成"""
        return {
            "original_parameters": self._get_current_parameters(),
            "checkpoint_id": f"chk_{uuid.uuid4().hex[:8]}",
            "created_at": datetime.now(),
        }

    def _apply_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """パラメータを適用（仮実装）"""
        # 実際の実装では、システムパラメータを変更
        logger.info(f"Applying parameters: {parameters}")
        return parameters

    def _calculate_adaptation_progress(
        self, state: Dict[str, Any], metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """適応の進捗を計算"""
        # response_timeの改善率を計算
        current_improvement = 0.0

        if "response_time" in metrics:
            rt_data = metrics["response_time"]
            if "current" in rt_data and "baseline" in rt_data:
                baseline = rt_data["baseline"]
                current = rt_data["current"]
                if baseline > 0:
                    current_improvement = (baseline - current) / baseline

        # 目標改善率
        target_improvement = state.get("success_criteria", {}).get(
            "response_time_improvement", 0.1
        )

        progress_percentage = (
            (current_improvement / target_improvement * 100)
            if target_improvement > 0
            else 0
        )

        return {
            "current_improvement": current_improvement,
            "target_improvement": target_improvement,
            "progress_percentage": min(progress_percentage, 100),
        }

    def _check_success_criteria(
        self, state: Dict[str, Any], metrics: Dict[str, Any]
    ) -> bool:
        """成功基準をチェック"""
        criteria = state.get("success_criteria", {})

        # response_time改善チェック
        if "response_time_improvement" in criteria:
            required_improvement = criteria["response_time_improvement"]
            progress = self._calculate_adaptation_progress(state, metrics)

            return progress["current_improvement"] >= required_improvement

        return True

    def _detect_adaptation_anomalies(
        self, metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """適応中の異常を検出"""
        anomalies = []

        # エラー率チェック
        if "error_rate" in metrics:
            error_rate = metrics["error_rate"].get("current", 0)
            if error_rate > 0.05:
                anomalies.append(
                    {"type": "high_error_rate", "severity": "high", "value": error_rate}
                )

        return anomalies

    def _determine_recommendation(
        self,
        progress: Dict[str, Any],
        criteria_met: bool,
        anomalies: List[Dict[str, Any]],
    ) -> str:
        """推奨アクションを決定"""
        if anomalies:
            return "rollback"
        elif criteria_met and progress.get("progress_percentage", 0) >= 100:
            return "proceed_to_next_step"
        elif progress.get("progress_percentage", 0) > 50:
            return "continue_monitoring"
        else:
            return "continue_monitoring"

    def _analyze_detailed_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """詳細メトリクスを分析"""
        return {"metric_count": len(metrics), "timestamp": datetime.now()}

    def _execute_rollback(self, rollback_point: Dict[str, Any]) -> Dict[str, Any]:
        """ロールバックを実行"""
        original_params = rollback_point.get("original_parameters", {})
        return self._apply_parameters(original_params)

    def _extract_adaptation_patterns(self, adaptation: Dict[str, Any]) -> List[str]:
        """適応からパターンを抽出"""
        patterns = []

        if adaptation.get("success"):
            # スレッドプール最適化パターン
            param_changes = adaptation.get("initial_state", {}).get("parameters", {})
            if "thread_pool_size" in param_changes:
                patterns.append("thread_pool_optimization")

            # 高改善率パターン
            improvements = adaptation.get("improvements", {})
            if any(imp > 0.2 for imp in improvements.values()):
                patterns.append("high_improvement_achieved")

        return patterns

    def _extract_success_strategy(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """成功戦略を抽出"""
        param_changes = result.get("parameter_changes", {})
        param_name = list(param_changes.keys())[0] if param_changes else "unknown"

        return {
            "parameter": param_name,
            "change": param_changes.get(param_name, {}),
            "improvement": result.get("improvement", 0),
            "conditions": result.get("conditions", {}),
        }

    def _extract_failure_pattern(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """失敗パターンを抽出"""
        param_changes = result.get("parameter_changes", {})
        param_name = list(param_changes.keys())[0] if param_changes else "unknown"

        return {
            "parameter": param_name,
            "change": param_changes.get(param_name, {}),
            "degradation": result.get("improvement", 0),
            "failure_reason": "parameter_too_aggressive",
        }

    def _calculate_change_ratio_from_result(self, result: Dict[str, Any]) -> float:
        """結果から変更率を計算"""
        changes = result.get("parameter_changes", {})
        if not changes:
            return 0.0

        total_ratio = 0.0
        for param, change_data in changes.items():
            if isinstance(change_data, dict):
                from_val = change_data.get("from", 0)
                to_val = change_data.get("to", 0)
                if from_val > 0:
                    total_ratio += abs(to_val - from_val) / from_val

        return total_ratio / len(changes) if changes else 0.0

    def _generate_optimization_rules(
        self, successes: List[Dict[str, Any]], failures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """最適化ルールを生成"""
        rules = []

        # 成功パターンからルール生成
        for success in successes:
            if success["improvement"] > 0.2:
                rules.append(
                    {
                        "rule": f"Increase {success['parameter']} when performance degrades",
                        "confidence": 0.8,
                    }
                )

        # 失敗パターンからルール生成
        for failure in failures:
            rules.append(
                {
                    "rule": f"Avoid aggressive changes to {failure['parameter']}",
                    "confidence": 0.9,
                }
            )

        return rules

    def _calculate_strategy_confidence(
        self, successes: List[Dict[str, Any]], failures: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """戦略の信頼度を計算"""
        confidence_scores = {}

        # パラメータ別の成功率計算
        param_stats = defaultdict(lambda: {"success": 0, "failure": 0})

        for success in successes:
            param = success["parameter"]
            param_stats[param]["success"] += 1

        for failure in failures:
            param = failure["parameter"]
            param_stats[param]["failure"] += 1

        for param, stats in param_stats.items():
            total = stats["success"] + stats["failure"]
            if total > 0:
                confidence_scores[param] = stats["success"] / total

        return confidence_scores

    def _evaluate_risk_level(
        self, violations: List[Dict[str, Any]], parameters: Dict[str, Any]
    ) -> str:
        """リスクレベルを評価"""
        if len(violations) > 3:
            return "critical"
        elif len(violations) > 1:
            return "high"
        elif len(violations) > 0:
            return "medium"
        else:
            return "low"

    def _calculate_incident_probability(
        self, parameters: Dict[str, Any], violations: List[Dict[str, Any]]
    ) -> float:
        """インシデント発生確率を計算"""
        base_probability = 0.1

        # 違反ごとに確率増加
        for violation in violations:
            base_probability += 0.15

        # 特定の危険なパラメータ
        if parameters.get("timeout_seconds", 30) < 5:
            base_probability += 0.3

        return min(base_probability, 0.9)

    def _adjust_parameters_for_safety(
        self, parameters: Dict[str, Any], violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """安全性のためパラメータを調整"""
        adjusted = parameters.copy()

        for violation in violations:
            param = violation["parameter"]
            constraint = violation["constraint"]

            if param in adjusted:
                # 制約内に収める
                if adjusted[param] < constraint.get("min", float("-inf")):
                    adjusted[param] = constraint["min"]
                elif adjusted[param] > constraint.get("max", float("inf")):
                    adjusted[param] = constraint["max"]

        return adjusted

    def _calculate_total_change(
        self, current: Dict[str, Any], target: Dict[str, Any]
    ) -> float:
        """総変更量を計算"""
        total_change = 0.0
        param_count = 0

        for param in target:
            if param in current:
                current_val = current[param]
                target_val = target[param]
                if current_val > 0:
                    change = abs(target_val - current_val) / current_val
                    total_change += change
                    param_count += 1

        return total_change / param_count if param_count > 0 else 0.0

    def _get_historical_success_patterns(self) -> List[Dict[str, Any]]:
        """過去の成功パターンを取得"""
        # 履歴から成功パターンを抽出
        patterns = []
        for history in list(self.adaptation_history)[-10:]:
            if history.get("adaptation", {}).get("success"):
                patterns.append({"pattern": "gradual_increase", "success_rate": 0.85})
        return patterns

    def _get_historical_failure_patterns(self) -> List[Dict[str, Any]]:
        """過去の失敗パターンを取得"""
        return [{"pattern": "aggressive_timeout_reduction", "failure_rate": 0.9}]

    def _find_similar_adaptation_cases(
        self, scenario: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """類似の適応ケースを検索"""
        # 簡略化: 固定の類似ケース
        return [
            {
                "case_id": "case_001",
                "similarity": 0.85,
                "outcome": "success",
                "strategy": "gradual_adaptation",
            }
        ]

    def _integrate_sage_recommendations(
        self, contributions: Dict[str, Any], scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """賢者の推奨を統合"""
        # リスクレベルに基づいて戦略を調整
        risk_level = contributions.get("incident_sage", {}).get("risk_level", "medium")

        if risk_level in ["high", "critical"]:
            adaptation_speed = "conservative"
        else:
            adaptation_speed = "moderate"

        return {
            "balanced_parameters": {
                "thread_pool_size": 15,  # 控えめな増加
                "cache_size": 150,
            },
            "safety_measures": contributions.get("incident_sage", {}).get(
                "safety_measures", []
            ),
            "monitoring_enhanced": True,
            "adaptation_speed": adaptation_speed,
        }

    def _create_integrated_execution_plan(
        self, strategy: Dict[str, Any], contributions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """統合実行計画を作成"""
        return {
            "phases": [
                {"phase": "preparation", "duration": "10_minutes"},
                {"phase": "gradual_adaptation", "duration": "30_minutes"},
                {"phase": "monitoring", "duration": "20_minutes"},
                {"phase": "finalization", "duration": "10_minutes"},
            ],
            "checkpoints": ["after_each_phase"],
            "rollback_points": ["after_phase_1", "after_phase_2"],
        }

    def _estimate_success_with_sages(
        self, strategy: Dict[str, Any], contributions: Dict[str, Any]
    ) -> float:
        """賢者の知見を統合して成功確率を推定"""
        base_probability = 0.6

        # 各賢者の貢献による調整
        if contributions.get("knowledge_sage", {}).get("successful_patterns"):
            base_probability += 0.1

        if contributions.get("rag_sage", {}).get("confidence", 0) > 0.8:
            base_probability += 0.1

        if contributions.get("incident_sage", {}).get("risk_level") == "low":
            base_probability += 0.1

        return min(base_probability, 0.95)


class SafetyConstraints:
    """安全性制約管理"""

    def __init__(self):
        self.constraints = {
            "thread_pool_size": {"min": 1, "max": 100},
            "cache_size": {"min": 10, "max": 5000},
            "timeout_seconds": {"min": 5, "max": 300},
            "connection_pool_size": {"min": 5, "max": 200},
            "batch_size": {"min": 1, "max": 1000},
        }

    def get_constraints(self) -> Dict[str, Dict[str, Any]]:
        """制約を取得"""
        return self.constraints


class RollbackManager:
    """ロールバック管理"""

    def __init__(self):
        self.rollback_history = deque(maxlen=100)

    def create_checkpoint(self, parameters: Dict[str, Any]) -> str:
        """チェックポイントを作成"""
        checkpoint_id = f"rb_{uuid.uuid4().hex[:8]}"
        self.rollback_history.append(
            {
                "checkpoint_id": checkpoint_id,
                "parameters": parameters.copy(),
                "created_at": datetime.now(),
            }
        )
        return checkpoint_id


class ParameterOptimizer:
    """パラメータ最適化"""

    def __init__(self):
        self.optimization_history = deque(maxlen=500)

    def optimize(
        self, current: Dict[str, Any], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """パラメータを最適化"""
        # 簡略化: 現在の値から少しずつ改善
        optimized = current.copy()

        for param, value in current.items():
            if param in constraints:
                # 制約内で10%改善を試みる
                new_value = value * 1.1
                max_val = constraints[param].get("max", float("inf"))
                optimized[param] = min(new_value, max_val)

        return optimized
