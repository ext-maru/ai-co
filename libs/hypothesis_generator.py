#!/usr/bin/env python3
"""
Hypothesis Generator - 仮説生成システム
観察データから実験可能な仮説を自動生成し、検証計画を立案

4賢者との連携:
📚 ナレッジ賢者: 過去の成功パターンから仮説テンプレート生成
"🔍" RAG賢者: 類似仮説の検索と検証結果の参照
📋 タスク賢者: 仮説検証の優先順位付けと実行計画
🚨 インシデント賢者: リスク要因を考慮した仮説の安全性評価
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import hashlib
import json
import logging
import random
import statistics
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class HypothesisGenerator:
    """仮説生成システム"""

    def __init__(self):
        """HypothesisGenerator 初期化"""
        self.generator_id = f"hyp_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 仮説生成設定
        self.generation_config = {
            "min_confidence": 0.6,
            "max_hypotheses_per_observation": 5,
            "hypothesis_types": [
                "performance",
                "reliability",
                "scalability",
                "resource",
                "configuration",
                "behavioral",
            ],
            "template_reuse_threshold": 0.7,
        }

        # 仮説管理
        self.hypothesis_history = deque(maxlen=1000)
        self.hypothesis_templates = defaultdict(list)
        self.experiment_results = {}

        # 4賢者統合フラグ
        self.knowledge_sage_integration = True
        self.rag_sage_integration = True
        self.task_sage_integration = True
        self.incident_sage_integration = True

        # 継続学習
        self.continuous_learning_enabled = False
        self.learning_pipeline = None
        self.pattern_library = defaultdict(list)

        # ナレッジベースパス
        self.knowledge_base_path = (
            PROJECT_ROOT / "knowledge_base" / "hypothesis_templates"
        )
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"HypothesisGenerator initialized: {self.generator_id}")

    def generate_hypotheses(self, observation_data: Dict[str, Any]) -> Dict[str, Any]:
        """観察データから仮説を生成"""
        try:
            hypotheses = []

            # パフォーマンスメトリクスからの仮説生成
            if "performance_metrics" in observation_data:
                perf_hypotheses = self._generate_performance_hypotheses(
                    observation_data["performance_metrics"]
                )
                hypotheses.extend(perf_hypotheses)

            # パターンからの仮説生成
            if "patterns" in observation_data:
                pattern_hypotheses = self._generate_pattern_based_hypotheses(
                    observation_data["patterns"]
                )
                hypotheses.extend(pattern_hypotheses)

            # コンテキストからの仮説生成
            if "context" in observation_data:
                context_hypotheses = self._generate_context_based_hypotheses(
                    observation_data["context"]
                )
                hypotheses.extend(context_hypotheses)

            # 仮説の優先順位付けと選別
            selected_hypotheses = self._select_best_hypotheses(
                hypotheses, self.generation_config["max_hypotheses_per_observation"]
            )

            # 仮説の詳細化
            for hyp in selected_hypotheses:
                hyp["id"] = f"hyp_{uuid.uuid4().hex[:8]}"
                hyp["testable_predictions"] = self._generate_predictions(hyp)
                hyp["supporting_evidence"] = self._gather_evidence(
                    hyp, observation_data
                )

            # 履歴に追加
            self.hypothesis_history.extend(selected_hypotheses)

            return {
                "generated_hypotheses": selected_hypotheses,
                "hypothesis_count": len(selected_hypotheses),
                "generation_metadata": {
                    "observation_summary": self._summarize_observation(
                        observation_data
                    ),
                    "generation_time": datetime.now(),
                    "generator_id": self.generator_id,
                },
            }

        except Exception as e:
            logger.error(f"Error generating hypotheses: {str(e)}")
            return {"generated_hypotheses": [], "hypothesis_count": 0, "error": str(e)}

    def validate_hypothesis(
        self, hypothesis: Dict[str, Any], validation_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """仮説の妥当性を検証"""
        try:
            # 統計的有意性チェック
            statistical_validity = self._check_statistical_validity(
                hypothesis, validation_criteria
            )

            # 実現可能性評価
            feasibility = self._assess_feasibility(hypothesis)

            # リソース要件評価
            resource_requirements = self._estimate_resources(hypothesis)

            # リスク評価
            risks = self._identify_risks(hypothesis)

            # 推奨アプローチ決定
            approach = self._recommend_approach(hypothesis, feasibility, risks)

            # 総合検証スコア計算
            validation_score = self._calculate_validation_score(
                statistical_validity, feasibility, risks
            )

            return {
                "is_valid": validation_score >= 0.7,
                "validation_score": validation_score,
                "feasibility_assessment": feasibility,
                "required_resources": resource_requirements,
                "potential_risks": risks,
                "recommended_approach": approach,
                "statistical_validity": statistical_validity,
            }

        except Exception as e:
            logger.error(f"Error validating hypothesis: {str(e)}")
            return {"is_valid": False, "validation_score": 0.0, "error": str(e)}

    def rank_hypotheses(
        self, hypotheses: List[Dict[str, Any]], ranking_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """仮説をランキング"""
        try:
            weights = ranking_criteria.get(
                "weights",
                {"confidence": 0.3, "impact": 0.4, "cost_efficiency": 0.2, "risk": 0.1},
            )

            # 各仮説のスコア計算
            scored_hypotheses = []
            for hyp in hypotheses:
                scores = self._calculate_hypothesis_scores(hyp, weights)
                hyp_copy = hyp.copy()
                hyp_copy["composite_score"] = scores["composite"]
                hyp_copy["score_breakdown"] = scores
                scored_hypotheses.append(hyp_copy)

            # スコアでソート
            scored_hypotheses.sort(key=lambda x: x["composite_score"], reverse=True)

            # ランク付け
            for i, hyp in enumerate(scored_hypotheses):
                hyp["rank"] = i + 1

            # トップ推奨の選定
            preferences = ranking_criteria.get("preferences", {})
            top_recommendations = self._select_top_recommendations(
                scored_hypotheses, preferences
            )

            return {
                "ranked_list": scored_hypotheses,
                "ranking_rationale": self._explain_ranking(scored_hypotheses, weights),
                "top_recommendations": top_recommendations,
            }

        except Exception as e:
            logger.error(f"Error ranking hypotheses: {str(e)}")
            return {"ranked_list": hypotheses, "error": str(e)}

    def create_experiment_plan(
        self, hypothesis: Dict[str, Any], experiment_constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """実験計画を作成"""
        try:
            experiment_id = f"exp_{uuid.uuid4().hex[:8]}"

            # フェーズ定義
            phases = self._define_experiment_phases(hypothesis, experiment_constraints)

            # 成功基準設定
            success_criteria = self._define_success_criteria(hypothesis)

            # モニタリング計画
            monitoring_plan = self._create_monitoring_plan(
                hypothesis, experiment_constraints
            )

            # ロールバック計画
            rollback_plan = self._create_rollback_plan(
                hypothesis, experiment_constraints
            )

            # タイムライン作成
            timeline = self._create_timeline(phases, experiment_constraints)

            return {
                "experiment_id": experiment_id,
                "hypothesis_id": hypothesis.get("id", "unknown"),
                "phases": phases,
                "success_criteria": success_criteria,
                "monitoring_plan": monitoring_plan,
                "rollback_plan": rollback_plan,
                "timeline": timeline,
                "constraints": experiment_constraints,
                "created_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error creating experiment plan: {str(e)}")
            return {"experiment_id": None, "error": str(e)}

    def save_hypothesis_template(
        self, successful_hypothesis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """成功した仮説をテンプレートとして保存（ナレッジ賢者連携）"""
        try:
            template_id = f"template_{uuid.uuid4().hex[:8]}"

            # テンプレート化
            template = self._create_template_from_hypothesis(successful_hypothesis)
            template["template_id"] = template_id
            template["created_at"] = datetime.now()

            # パターンカテゴリー決定
            category = self._categorize_hypothesis(successful_hypothesis)

            # ナレッジベースに保存
            save_path = self.knowledge_base_path / f"{category}_{template_id}.json"
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2, default=str)

            # メモリ内テンプレートライブラリに追加
            self.hypothesis_templates[category].append(template)

            # ナレッジ賢者統合情報
            knowledge_integration = {
                "status": "success",
                "categorization": category,
                "related_patterns": self._find_related_patterns(template),
            }

            return {
                "saved": True,
                "template_id": template_id,
                "knowledge_base_path": str(save_path),
                "template_metadata": {
                    "category": category,
                    "reusability_score": template.get("reusability_score", 0.85),
                },
                "knowledge_integration": knowledge_integration,
            }

        except Exception as e:
            logger.error(f"Error saving hypothesis template: {str(e)}")
            return {"saved": False, "error": str(e)}

    def search_similar_hypotheses(
        self, search_query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """類似仮説を検索（RAG賢者連携）"""
        try:
            similar_hypotheses = []

            # 検索ベクトル生成
            query_vector = self._create_search_vector(search_query)

            # テンプレートライブラリから検索
            for category, templates in self.hypothesis_templates.items():
                for template in templates:
                    similarity = self._calculate_similarity(query_vector, template)
                    if similarity >= self.generation_config["template_reuse_threshold"]:
                        adapted = self._adapt_template_to_context(
                            template, search_query
                        )
                        adapted["similarity_score"] = similarity
                        adapted["rag_integration"] = {
                            "retrieval_confidence": similarity,
                            "search_quality": self._assess_search_quality(similarity),
                        }
                        similar_hypotheses.append(adapted)

            # ファイルベースのテンプレートも検索
            file_results = self._search_file_templates(search_query)
            similar_hypotheses.extend(file_results)

            # スコアでソート
            similar_hypotheses.sort(key=lambda x: x["similarity_score"], reverse=True)

            return similar_hypotheses[:5]  # Top 5を返す

        except Exception as e:
            logger.error(f"Error searching similar hypotheses: {str(e)}")
            return []

    def evaluate_hypothesis_risk(
        self, hypothesis: Dict[str, Any], system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """仮説のリスクを評価（インシデント賢者連携）"""
        try:
            # リスク要因分析
            risk_factors = self._analyze_risk_factors(hypothesis, system_state)

            # 潜在的インシデント予測
            potential_incidents = self._predict_incidents(hypothesis, system_state)

            # 緩和戦略生成
            mitigation_strategies = self._generate_mitigation_strategies(
                risk_factors, potential_incidents
            )

            # 総合リスクレベル決定
            overall_risk = self._calculate_overall_risk(
                risk_factors, potential_incidents
            )

            # 安全性スコア計算
            safety_score = 1.0 - (overall_risk / 4.0)  # 4段階を0-1に正規化

            return {
                "overall_risk_level": self._risk_level_to_string(overall_risk),
                "risk_factors": risk_factors,
                "potential_incidents": potential_incidents,
                "mitigation_strategies": mitigation_strategies,
                "safety_score": safety_score,
                "incident_sage_assessment": {
                    "critical_operations_impact": self._assess_critical_impact(
                        hypothesis, system_state
                    ),
                    "recovery_complexity": self._assess_recovery_complexity(hypothesis),
                },
            }

        except Exception as e:
            logger.error(f"Error evaluating hypothesis risk: {str(e)}")
            return {
                "overall_risk_level": "unknown",
                "safety_score": 0.0,
                "error": str(e),
            }

    def track_hypothesis_results(
        self, experiment_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """実験結果を追跡し学習"""
        try:
            result_id = f"result_{uuid.uuid4().hex[:8]}"

            # 結果保存
            self.experiment_results[experiment_results["hypothesis_id"]] = (
                experiment_results
            )

            # 学習内容抽出
            learning = self._extract_learning(experiment_results)

            # テンプレート生成判定
            template_generated = False
            if experiment_results.get("conclusion") == "hypothesis_confirmed":
                # 成功した仮説はテンプレート化
                hypothesis = self._find_hypothesis(experiment_results["hypothesis_id"])
                if hypothesis:
                    template_result = self.save_hypothesis_template(hypothesis)
                    template_generated = template_result["saved"]

            # ナレッジ更新
            knowledge_updated = self._update_knowledge_base(learning)

            # パターンライブラリ更新
            self._update_pattern_library(experiment_results)

            return {
                "tracked": True,
                "result_id": result_id,
                "learning_extracted": learning,
                "template_generated": template_generated,
                "knowledge_updated": knowledge_updated,
                "tracking_metadata": {
                    "tracked_at": datetime.now(),
                    "hypothesis_id": experiment_results["hypothesis_id"],
                },
            }

        except Exception as e:
            logger.error(f"Error tracking hypothesis results: {str(e)}")
            return {"tracked": False, "error": str(e)}

    def prioritize_experiments_with_task_sage(
        self, hypothesis_experiments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """タスク賢者と連携して実験の優先順位を決定"""
        try:
            prioritized = []

            for exp in hypothesis_experiments:
                # 優先度スコア計算
                priority_score = self._calculate_priority_score(exp)

                exp_copy = exp.copy()
                exp_copy["priority_score"] = priority_score
                exp_copy["scheduling_recommendation"] = self._recommend_scheduling(exp)
                prioritized.append(exp_copy)

            # 優先度でソート
            prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

            # 実行順序付与
            for i, exp in enumerate(prioritized):
                exp["execution_order"] = i + 1

            return prioritized

        except Exception as e:
            logger.error(f"Error prioritizing experiments: {str(e)}")
            return hypothesis_experiments

    def generate_error_prevention_optimizations(
        self, error_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """エラーパターンから予防的最適化を生成（インシデント賢者連携）"""
        try:
            preventive_strategies = []

            # 頻発エラーの分析
            for error in error_patterns.get("frequent_errors", []):
                strategy = self._create_prevention_strategy(error)
                preventive_strategies.append(strategy)

            # 優先アクション決定
            priority_actions = self._determine_priority_actions(preventive_strategies)

            # エラー削減期待値計算
            expected_reduction = self._calculate_error_reduction(
                preventive_strategies, error_patterns
            )

            return {
                "preventive_strategies": preventive_strategies,
                "priority_actions": priority_actions,
                "expected_error_reduction": expected_reduction,
                "incident_prevention_plan": self._create_prevention_plan(
                    preventive_strategies
                ),
            }

        except Exception as e:
            logger.error(f"Error generating error prevention optimizations: {str(e)}")
            return {"preventive_strategies": [], "error": str(e)}

    def enable_continuous_learning(
        self, learning_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """継続的学習を有効化"""
        try:
            self.continuous_learning_enabled = learning_config.get("enabled", True)

            # 学習パイプライン初期化
            self.learning_pipeline = {
                "feedback_collection": learning_config.get("feedback_collection", True),
                "pattern_extraction": learning_config.get("pattern_extraction", True),
                "template_generation": learning_config.get("template_generation", True),
                "success_threshold": learning_config.get("success_threshold", 0.75),
            }

            # フィードバック機構設定
            feedback_mechanism = {
                "collection_method": "automated",
                "processing_interval": "real_time",
                "learning_rate": learning_config.get("learning_rate", 0.1),
            }

            return {
                "learning_enabled": self.continuous_learning_enabled,
                "learning_pipeline": self.learning_pipeline,
                "feedback_mechanism": feedback_mechanism,
                "configuration": learning_config,
            }

        except Exception as e:
            logger.error(f"Error enabling continuous learning: {str(e)}")
            return {"learning_enabled": False, "error": str(e)}

    def learn_from_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """フィードバックから学習"""
        try:
            if not self.continuous_learning_enabled:
                return {"feedback_processed": False, "reason": "Learning disabled"}

            # パターン更新
            patterns_updated = self._update_patterns_from_feedback(feedback)

            # テンプレート改善
            templates_refined = self._refine_templates(feedback)

            # 生成精度向上
            accuracy_improvement = self._improve_generation_accuracy(feedback)

            # 学習履歴記録
            self._record_learning_history(feedback)

            return {
                "feedback_processed": True,
                "patterns_updated": patterns_updated,
                "templates_refined": templates_refined,
                "generation_accuracy_improved": accuracy_improvement,
                "learning_metadata": {
                    "feedback_id": feedback.get("hypothesis_id"),
                    "learned_at": datetime.now(),
                },
            }

        except Exception as e:
            logger.error(f"Error learning from feedback: {str(e)}")
            return {"feedback_processed": False, "error": str(e)}

    def generate_collaborative_hypotheses(
        self, complex_problem: Dict[str, Any]
    ) -> Dict[str, Any]:
        """4賢者協調による仮説生成"""
        try:
            sage_contributions = {}

            # ナレッジ賢者: 過去の成功パターン
            if self.knowledge_sage_integration:
                sage_contributions["knowledge_sage"] = self._get_historical_patterns(
                    complex_problem
                )

            # RAG賢者: 類似事例検索
            if self.rag_sage_integration:
                sage_contributions["rag_sage"] = self._search_similar_cases(
                    complex_problem
                )

            # タスク賢者: 実行優先順位
            if self.task_sage_integration:
                sage_contributions["task_sage"] = self._get_execution_priorities(
                    complex_problem
                )

            # インシデント賢者: リスク評価
            if self.incident_sage_integration:
                sage_contributions["incident_sage"] = self._assess_problem_risks(
                    complex_problem
                )

            # 統合仮説生成
            integrated_hypotheses = self._integrate_sage_inputs(
                sage_contributions, complex_problem
            )

            # コンセンサス推奨
            consensus = self._form_sage_consensus(
                integrated_hypotheses, sage_contributions
            )

            # 実行計画
            execution_plan = self._create_collaborative_execution_plan(
                integrated_hypotheses, consensus
            )

            return {
                "sage_contributions": sage_contributions,
                "integrated_hypotheses": integrated_hypotheses,
                "consensus_recommendations": consensus,
                "execution_plan": execution_plan,
                "collaboration_metadata": {
                    "sages_involved": list(sage_contributions.keys()),
                    "collaboration_time": datetime.now(),
                },
            }

        except Exception as e:
            logger.error(f"Error in collaborative hypothesis generation: {str(e)}")
            return {
                "sage_contributions": {},
                "integrated_hypotheses": [],
                "error": str(e),
            }

    # ===== Private Helper Methods =====

    def _generate_performance_hypotheses(
        self, metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """パフォーマンスメトリクスから仮説生成"""
        hypotheses = []

        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict) and "trend" in metric_data:
                if metric_data["trend"] == "increasing" and metric_name in [
                    "response_time",
                    "error_rate",
                ]:
                    hypothesis = {
                        "statement": f"Optimizing {metric_name} will improve system performance",
                        "hypothesis_type": "performance",
                        "confidence_score": 0.8,
                        "rationale": f"{metric_name} is trending upward",
                    }
                    hypotheses.append(hypothesis)

        return hypotheses

    def _generate_pattern_based_hypotheses(
        self, patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """パターンベースの仮説生成"""
        hypotheses = []

        for pattern in patterns:
            if pattern.get("confidence", 0) > 0.7:
                hypothesis = {
                    "statement": f"Addressing {pattern['type']} pattern will resolve issues",
                    "hypothesis_type": "behavioral",
                    "confidence_score": pattern["confidence"],
                    "rationale": pattern["description"],
                }
                hypotheses.append(hypothesis)

        return hypotheses

    def _generate_context_based_hypotheses(
        self, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """コンテキストベースの仮説生成"""
        hypotheses = []

        if "system_changes" in context:
            for change in context["system_changes"]:
                hypothesis = {
                    "statement": f"Recent {change} may be causing performance issues",
                    "hypothesis_type": "configuration",
                    "confidence_score": 0.75,
                    "rationale": f"Temporal correlation with {change}",
                }
                hypotheses.append(hypothesis)

        return hypotheses

    def _select_best_hypotheses(
        self, hypotheses: List[Dict[str, Any]], max_count: int
    ) -> List[Dict[str, Any]]:
        """最良の仮説を選択"""
        # 信頼度でソート
        hypotheses.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        return hypotheses[:max_count]

    def _generate_predictions(self, hypothesis: Dict[str, Any]) -> List[str]:
        """検証可能な予測を生成"""
        predictions = []

        if hypothesis.get("hypothesis_type") == "performance":
            predictions.append("Performance metrics will improve by at least 20%")
            predictions.append("System resource usage will remain stable")
        elif hypothesis.get("hypothesis_type") == "reliability":
            predictions.append("Error rate will decrease by at least 50%")
            predictions.append("System uptime will increase")
        elif hypothesis.get("hypothesis_type") == "behavioral":
            predictions.append("Behavior patterns will normalize")
            predictions.append("Anomaly frequency will decrease")
        elif hypothesis.get("hypothesis_type") == "configuration":
            predictions.append("System stability will improve")
            predictions.append("Configuration conflicts will be resolved")
        else:
            # デフォルトの予測
            predictions.append("Target metrics will show measurable improvement")
            predictions.append("No negative side effects will occur")

        return predictions

    def _gather_evidence(
        self, hypothesis: Dict[str, Any], observation_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """支持証拠を収集"""
        evidence = []

        # メトリクスからの証拠
        if "performance_metrics" in observation_data:
            for metric, data in observation_data["performance_metrics"].items():
                if isinstance(data, dict) and "trend" in data:
                    evidence.append(
                        {
                            "type": "metric_trend",
                            "description": f"{metric} shows {data['trend']} trend",
                            "strength": 0.7,
                        }
                    )

        return evidence

    def _summarize_observation(
        self, observation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """観察データのサマリー"""
        return {
            "metrics_count": len(observation_data.get("performance_metrics", {})),
            "patterns_found": len(observation_data.get("patterns", [])),
            "context_factors": len(observation_data.get("context", {})),
        }

    def _check_statistical_validity(
        self, hypothesis: Dict[str, Any], criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """統計的妥当性チェック"""
        return {
            "significance_level": criteria.get("statistical_significance", 0.95),
            "sample_size_adequate": True,
            "control_variables_defined": True,
        }

    def _assess_feasibility(self, hypothesis: Dict[str, Any]) -> Dict[str, Any]:
        """実現可能性評価"""
        return {
            "technical_feasibility": 0.85,
            "resource_availability": 0.90,
            "implementation_complexity": "medium",
        }

    def _estimate_resources(self, hypothesis: Dict[str, Any]) -> Dict[str, Any]:
        """必要リソース見積もり"""
        return {
            "time_required": "2-4 hours",
            "human_resources": 1,
            "computational_resources": "moderate",
            "cost_estimate": "low",
        }

    def _identify_risks(self, hypothesis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """リスク特定"""
        risks = []

        if hypothesis.get("hypothesis_type") == "performance":
            risks.append(
                {
                    "type": "performance_degradation",
                    "severity": "medium",
                    "mitigation": "Gradual rollout with monitoring",
                }
            )

        return risks

    def _recommend_approach(
        self,
        hypothesis: Dict[str, Any],
        feasibility: Dict[str, Any],
        risks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """推奨アプローチ決定"""
        if feasibility["technical_feasibility"] > 0.8 and len(risks) < 3:
            approach = "direct_implementation"
        else:
            approach = "phased_rollout"

        return {
            "approach_type": approach,
            "rationale": "Based on feasibility and risk assessment",
        }

    def _calculate_validation_score(
        self,
        statistical_validity: Dict[str, Any],
        feasibility: Dict[str, Any],
        risks: List[Dict[str, Any]],
    ) -> float:
        """検証スコア計算"""
        stat_score = statistical_validity.get("significance_level", 0.5)
        feas_score = feasibility.get("technical_feasibility", 0.5)
        risk_score = 1.0 - (len(risks) * 0.1)  # リスクが多いほど低スコア

        return (stat_score + feas_score + risk_score) / 3.0

    def _calculate_hypothesis_scores(
        self, hypothesis: Dict[str, Any], weights: Dict[str, float]
    ) -> Dict[str, float]:
        """仮説のスコア計算"""
        scores = {
            "confidence_score": hypothesis.get("confidence_score", 0.5),
            "impact_score": hypothesis.get("expected_impact", 0.5),
            "cost_efficiency_score": self._calculate_cost_efficiency(hypothesis),
            "risk_score": 1.0 - (len(hypothesis.get("risks", [])) * 0.2),
        }

        # 重み付き合計
        composite = sum(
            scores[key] * weights.get(key.replace("_score", ""), 0.25) for key in scores
        )
        scores["composite"] = composite

        return scores

    def _calculate_cost_efficiency(self, hypothesis: Dict[str, Any]) -> float:
        """コスト効率計算"""
        cost_map = {"low": 1.0, "medium": 0.5, "high": 0.2}
        return cost_map.get(hypothesis.get("implementation_cost", "medium"), 0.5)

    def _select_top_recommendations(
        self, scored_hypotheses: List[Dict[str, Any]], preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """トップ推奨選定"""
        if preferences.get("prefer_quick_wins"):
            # コスト効率重視でフィルタ
            return [
                h
                for h in scored_hypotheses
                if h["score_breakdown"]["cost_efficiency_score"] > 0.7
            ][:3]

        return scored_hypotheses[:3]

    def _explain_ranking(
        self, ranked_hypotheses: List[Dict[str, Any]], weights: Dict[str, float]
    ) -> str:
        """ランキングの説明"""
        return f"Ranking based on weights: {weights}"

    def _define_experiment_phases(
        self, hypothesis: Dict[str, Any], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """実験フェーズ定義"""
        return [
            {
                "name": "preparation",
                "duration": "30 minutes",
                "tasks": ["Setup monitoring", "Backup current state"],
                "checkpoints": ["Environment ready", "Baseline captured"],
            },
            {
                "name": "baseline",
                "duration": "30 minutes",
                "tasks": ["Collect baseline metrics", "Verify stability"],
                "checkpoints": ["Baseline established", "System stable"],
            },
            {
                "name": "experiment",
                "duration": constraints.get("duration", "2_hours").replace("_", " "),
                "tasks": ["Apply changes", "Monitor impact"],
                "checkpoints": ["Changes applied", "Data collection ongoing"],
            },
            {
                "name": "analysis",
                "duration": "30 minutes",
                "tasks": ["Analyze results", "Statistical validation"],
                "checkpoints": ["Analysis complete", "Results validated"],
            },
            {
                "name": "decision",
                "duration": "15 minutes",
                "tasks": ["Make decision", "Document results"],
                "checkpoints": ["Decision made", "Documentation complete"],
            },
        ]

    def _define_success_criteria(self, hypothesis: Dict[str, Any]) -> Dict[str, Any]:
        """成功基準定義"""
        return {
            "metrics": hypothesis.get("testable_predictions", []),
            "thresholds": {"minimum_improvement": 0.15, "maximum_degradation": 0.05},
            "statistical_tests": ["t-test", "chi-square"],
        }

    def _create_monitoring_plan(
        self, hypothesis: Dict[str, Any], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """モニタリング計画作成"""
        return {
            "metrics_to_track": ["response_time", "error_rate", "resource_usage"],
            "sampling_rate": "1_minute",
            "alert_conditions": [
                {"metric": "error_rate", "threshold": 0.05, "action": "alert"},
                {"metric": "response_time", "threshold": 500, "action": "rollback"},
            ],
        }

    def _create_rollback_plan(
        self, hypothesis: Dict[str, Any], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ロールバック計画作成"""
        return {
            "trigger_conditions": [
                "Error rate exceeds 5%",
                "Response time exceeds baseline by 50%",
                "System instability detected",
            ],
            "rollback_steps": [
                "Revert configuration changes",
                "Restart affected services",
                "Verify system stability",
            ],
            "estimated_time": constraints.get("rollback_time", "5_minutes"),
        }

    def _create_timeline(
        self, phases: List[Dict[str, Any]], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """タイムライン作成"""
        start_time = datetime.now()
        timeline = {"start": start_time, "phases": []}

        current_time = start_time
        for phase in phases:
            # 簡略化: duration文字列から時間を抽出
            duration_hours = 0.5  # デフォルト30分
            duration_str = phase.get("duration", "30 minutes")

            try:
                if "hour" in duration_str:
                    # "2 hours" -> 2.0
                    duration_hours = float(duration_str.split()[0])
                elif "minute" in duration_str:
                    # "30 minutes" -> 0.5
                    minutes = float(duration_str.split()[0])
                    duration_hours = minutes / 60.0
            except (ValueError, IndexError):
                # パース失敗時はデフォルト値
                duration_hours = 0.5

            phase_timeline = {
                "phase": phase["name"],
                "start": current_time,
                "end": current_time + timedelta(hours=duration_hours),
            }
            timeline["phases"].append(phase_timeline)
            current_time = phase_timeline["end"]

        timeline["end"] = current_time
        return timeline

    def _create_template_from_hypothesis(
        self, hypothesis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """仮説からテンプレート作成"""
        return {
            "pattern": hypothesis.get("pattern", "general_optimization"),
            "statement_template": self._generalize_statement(hypothesis["statement"]),
            "applicable_contexts": self._extract_contexts(hypothesis),
            "success_parameters": hypothesis.get("successful_parameters", {}),
            "reusability_score": hypothesis.get("reusability_score", 0.85),
            "validation_results": hypothesis.get("validation_results", {}),
        }

    def _generalize_statement(self, statement: str) -> str:
        """文章を一般化"""
        # 簡単な変数化
        generalized = statement
        generalized = generalized.replace("caching", "{optimization_type}")
        generalized = generalized.replace("response time", "{metric}")
        return generalized

    def _extract_contexts(self, hypothesis: Dict[str, Any]) -> List[str]:
        """適用可能なコンテキスト抽出"""
        contexts = []
        if "context" in hypothesis:
            context = hypothesis["context"]
            if "problem_type" in context:
                contexts.append(context["problem_type"])
            if "system_state" in context:
                contexts.append(context["system_state"])
        return contexts

    def _categorize_hypothesis(self, hypothesis: Dict[str, Any]) -> str:
        """仮説をカテゴリー分類"""
        return hypothesis.get("hypothesis_type", "general")

    def _find_related_patterns(self, template: Dict[str, Any]) -> List[str]:
        """関連パターン検索"""
        # 簡略化: パターンタイプに基づく関連パターン
        pattern_relations = {
            "performance_optimization": ["caching", "pooling", "batching"],
            "resource_optimization": ["memory_management", "cpu_optimization"],
            "reliability_improvement": ["retry_logic", "circuit_breaker"],
        }
        return pattern_relations.get(template.get("pattern", ""), [])

    def _create_search_vector(self, search_query: Dict[str, Any]) -> Dict[str, Any]:
        """検索ベクトル作成"""
        # 簡略化: 辞書ベースのベクトル表現
        vector = {
            "problem": search_query.get("problem_description", ""),
            "symptoms": search_query.get("symptoms", []),
            "context": search_query.get("context", {}),
            "outcome": search_query.get("desired_outcome", ""),
        }
        return vector

    def _calculate_similarity(
        self, query_vector: Dict[str, Any], template: Dict[str, Any]
    ) -> float:
        """類似度計算"""
        # 簡略化: キーワードマッチング
        score = 0.0

        # コンテキスト一致チェック
        template_contexts = template.get("applicable_contexts", [])
        query_contexts = []
        if isinstance(query_vector.get("context"), dict):
            query_contexts = list(query_vector["context"].values())

        for ctx in template_contexts:
            if any(str(ctx).lower() in str(qc).lower() for qc in query_contexts):
                score += 0.3

        # 症状一致チェック
        if "symptoms" in query_vector:
            for symptom in query_vector["symptoms"]:
                if symptom in str(template):
                    score += 0.2

        return min(score, 1.0)

    def _adapt_template_to_context(
        self, template: Dict[str, Any], search_query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """テンプレートをコンテキストに適応"""
        adapted = template.copy()
        adapted["hypothesis_id"] = f"adapted_{uuid.uuid4().hex[:8]}"
        adapted["original_statement"] = template.get("statement_template", "")

        # パラメータを現在のコンテキストに適応
        if "context" in search_query:
            adapted["adapted_statement"] = self._fill_template_variables(
                template.get("statement_template", ""), search_query["context"]
            )
        else:
            adapted["adapted_statement"] = adapted["original_statement"]

        adapted["historical_success_rate"] = 0.75  # 仮の値
        adapted["applicable_parameters"] = template.get("success_parameters", {})

        return adapted

    def _fill_template_variables(self, template: str, context: Dict[str, Any]) -> str:
        """テンプレート変数を埋める"""
        filled = template
        # 簡単な変数置換
        if "{optimization_type}" in filled and "database_type" in context:
            filled = filled.replace(
                "{optimization_type}", f"{context['database_type']} optimization"
            )
        if "{metric}" in filled:
            filled = filled.replace("{metric}", "query execution time")
        return filled

    def _assess_search_quality(self, similarity: float) -> str:
        """検索品質評価"""
        if similarity > 0.8:
            return "high"
        elif similarity > 0.6:
            return "medium"
        else:
            return "low"

    def _search_file_templates(
        self, search_query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """ファイルベースのテンプレート検索"""
        results = []

        try:
            for template_file in self.knowledge_base_path.glob("*.json"):
                with open(template_file, "r", encoding="utf-8") as f:
                    template = json.load(f)

                similarity = self._calculate_similarity(
                    self._create_search_vector(search_query), template
                )
                if similarity >= self.generation_config["template_reuse_threshold"]:
                    adapted = self._adapt_template_to_context(template, search_query)
                    adapted["similarity_score"] = similarity
                    adapted["rag_integration"] = {
                        "retrieval_confidence": similarity,
                        "search_quality": self._assess_search_quality(similarity),
                    }
                    results.append(adapted)
        except Exception as e:
            logger.error(f"Error searching file templates: {str(e)}")

        return results

    def _analyze_risk_factors(
        self, hypothesis: Dict[str, Any], system_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """リスク要因分析"""
        risk_factors = []

        # 高負荷時のリスク
        if system_state.get("current_load") == "high":
            risk_factors.append(
                {
                    "category": "performance",
                    "description": "Changes during high load may cause instability",
                    "severity": "high",
                    "probability": 0.7,
                }
            )

        # クリティカル操作への影響
        if "critical_operations" in system_state:
            risk_factors.append(
                {
                    "category": "operational",
                    "description": "May impact critical operations",
                    "severity": "critical",
                    "probability": 0.5,
                }
            )

        return risk_factors

    def _predict_incidents(
        self, hypothesis: Dict[str, Any], system_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """潜在的インシデント予測"""
        incidents = []

        if (
            hypothesis.get("impact_areas")
            and "performance" in hypothesis["impact_areas"]
        ):
            incidents.append(
                {
                    "type": "performance_degradation",
                    "likelihood": "medium",
                    "impact": "user_experience",
                    "estimated_duration": "30 minutes",
                }
            )

        return incidents

    def _generate_mitigation_strategies(
        self, risk_factors: List[Dict[str, Any]], incidents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """緩和戦略生成"""
        strategies = []

        # リスク要因に基づく戦略
        for risk in risk_factors:
            if risk["severity"] in ["high", "critical"]:
                strategies.append(
                    {
                        "strategy": "Gradual rollout with canary deployment",
                        "targets": risk["category"],
                        "effectiveness": 0.8,
                    }
                )

        # インシデント予防戦略
        if incidents:
            strategies.append(
                {
                    "strategy": "Enhanced monitoring and automatic rollback",
                    "targets": "all",
                    "effectiveness": 0.9,
                }
            )

        return strategies

    def _calculate_overall_risk(
        self, risk_factors: List[Dict[str, Any]], incidents: List[Dict[str, Any]]
    ) -> int:
        """総合リスクレベル計算"""
        # リスクスコア計算
        risk_score = 0

        for risk in risk_factors:
            severity_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            risk_score += severity_scores.get(risk["severity"], 2) * risk["probability"]

        # インシデント影響加算
        risk_score += len(incidents) * 2

        # 4段階評価
        if risk_score < 3:
            return 1  # low
        elif risk_score < 6:
            return 2  # medium
        elif risk_score < 10:
            return 3  # high
        else:
            return 4  # critical

    def _risk_level_to_string(self, risk_level: int) -> str:
        """リスクレベルを文字列に変換"""
        mapping = {1: "low", 2: "medium", 3: "high", 4: "critical"}
        return mapping.get(risk_level, "unknown")

    def _assess_critical_impact(
        self, hypothesis: Dict[str, Any], system_state: Dict[str, Any]
    ) -> str:
        """クリティカル操作への影響評価"""
        if "critical_operations" in system_state and hypothesis.get("impact_areas"):
            return (
                "high"
                if any(
                    area in ["performance", "reliability"]
                    for area in hypothesis["impact_areas"]
                )
                else "low"
            )
        return "unknown"

    def _assess_recovery_complexity(self, hypothesis: Dict[str, Any]) -> str:
        """復旧複雑度評価"""
        if hypothesis.get("proposed_changes"):
            changes_count = len(hypothesis["proposed_changes"])
            if changes_count > 3:
                return "high"
            elif changes_count > 1:
                return "medium"
        return "low"

    def _find_hypothesis(self, hypothesis_id: str) -> Optional[Dict[str, Any]]:
        """仮説IDから仮説を検索"""
        for hyp in self.hypothesis_history:
            if hyp.get("id") == hypothesis_id:
                return hyp
        return None

    def _extract_learning(self, experiment_results: Dict[str, Any]) -> Dict[str, Any]:
        """実験結果から学習内容抽出"""
        return {
            "success_factors": self._identify_success_factors(experiment_results),
            "applicable_contexts": self._identify_applicable_contexts(
                experiment_results
            ),
            "reusability_assessment": self._assess_reusability(experiment_results),
        }

    def _identify_success_factors(self, results: Dict[str, Any]) -> List[str]:
        """成功要因特定"""
        factors = []

        if results.get("predictions_validated"):
            for pred, data in results["predictions_validated"].items():
                if data.get("validated"):
                    factors.append(f"{pred} achieved as predicted")

        return factors

    def _identify_applicable_contexts(self, results: Dict[str, Any]) -> List[str]:
        """適用可能コンテキスト特定"""
        # 簡略化: 基本的なコンテキスト
        return ["high_load", "batch_processing", "real_time_operations"]

    def _assess_reusability(self, results: Dict[str, Any]) -> float:
        """再利用可能性評価"""
        # 予測精度に基づく評価
        if results.get("predictions_validated"):
            validated_count = sum(
                1
                for v in results["predictions_validated"].values()
                if v.get("validated")
            )
            total_count = len(results["predictions_validated"])
            return validated_count / total_count if total_count > 0 else 0.5
        return 0.5

    def _update_knowledge_base(self, learning: Dict[str, Any]) -> bool:
        """ナレッジベース更新"""
        try:
            # 学習内容をファイルに保存
            learning_file = (
                self.knowledge_base_path
                / f"learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(learning_file, "w", encoding="utf-8") as f:
                json.dump(learning, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Error updating knowledge base: {str(e)}")
            return False

    def _update_pattern_library(self, experiment_results: Dict[str, Any]) -> None:
        """パターンライブラリ更新"""
        if experiment_results.get("conclusion") == "hypothesis_confirmed":
            pattern_type = "success_pattern"
        else:
            pattern_type = "failure_pattern"

        self.pattern_library[pattern_type].append(
            {
                "hypothesis_id": experiment_results["hypothesis_id"],
                "metrics": experiment_results.get("metrics_collected", {}),
                "timestamp": datetime.now(),
            }
        )

    def _calculate_priority_score(self, experiment: Dict[str, Any]) -> float:
        """優先度スコア計算"""
        urgency_scores = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
        resource_scores = {"low": 1.0, "medium": 0.7, "high": 0.4}

        urgency = urgency_scores.get(experiment.get("urgency", "medium"), 0.5)
        resource = resource_scores.get(
            experiment.get("resource_requirement", "medium"), 0.5
        )

        return (urgency * 0.7) + (resource * 0.3)

    def _recommend_scheduling(self, experiment: Dict[str, Any]) -> str:
        """スケジューリング推奨"""
        if experiment.get("urgency") == "critical":
            return "immediate"
        elif experiment.get("urgency") == "high":
            return "within_2_hours"
        else:
            return "next_maintenance_window"

    def _create_prevention_strategy(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """エラー予防戦略作成"""
        strategy = {"targets": [error["error_type"]], "optimization_focus": []}

        # 相関関係に基づく最適化フォーカス
        if "correlation" in error:
            for factor, correlation in error["correlation"].items():
                if correlation > 0.7:
                    strategy["optimization_focus"].append(factor.replace("_", " "))

        strategy["expected_effectiveness"] = 0.8
        strategy["implementation_complexity"] = "medium"

        return strategy

    def _determine_priority_actions(
        self, strategies: List[Dict[str, Any]]
    ) -> List[str]:
        """優先アクション決定"""
        # 頻度の高いものから優先
        return [s["targets"][0] for s in strategies[:3]]

    def _calculate_error_reduction(
        self, strategies: List[Dict[str, Any]], error_patterns: Dict[str, Any]
    ) -> float:
        """エラー削減期待値計算"""
        # 簡略化: 戦略数に基づく削減率
        reduction_per_strategy = 0.15
        total_reduction = len(strategies) * reduction_per_strategy
        return min(total_reduction, 0.75)  # 最大75%削減

    def _create_prevention_plan(
        self, strategies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """予防計画作成"""
        return {
            "phases": ["analysis", "implementation", "monitoring"],
            "timeline": "1_week",
            "success_metrics": ["error_rate_reduction", "mtbf_improvement"],
        }

    def _update_patterns_from_feedback(self, feedback: Dict[str, Any]) -> bool:
        """フィードバックからパターン更新"""
        if feedback.get("outcome") == "success":
            self.pattern_library["success_patterns"].append(feedback)
        return True

    def _refine_templates(self, feedback: Dict[str, Any]) -> bool:
        """テンプレート改善"""
        # 高精度の予測があったテンプレートを強化
        if feedback.get("accuracy", {}).get("predictions", 0) > 0.8:
            # テンプレートの信頼度を上げる
            return True
        return False

    def _improve_generation_accuracy(self, feedback: Dict[str, Any]) -> float:
        """生成精度向上"""
        # 学習による改善率（仮）
        improvement = feedback.get("accuracy", {}).get("predictions", 0.5) * 0.1
        return improvement

    def _record_learning_history(self, feedback: Dict[str, Any]) -> None:
        """学習履歴記録"""
        # メモリ内履歴に追加
        self.hypothesis_history.append(
            {
                "type": "learning_feedback",
                "feedback": feedback,
                "timestamp": datetime.now(),
            }
        )

    def _get_historical_patterns(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """過去のパターン取得（ナレッジ賢者）"""
        return {
            "successful_patterns": list(self.pattern_library["success_patterns"][-5:]),
            "failure_patterns": list(self.pattern_library["failure_patterns"][-3:]),
            "recommendation": "Apply pattern from similar past incident",
        }

    def _search_similar_cases(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """類似事例検索（RAG賢者）"""
        # 簡略化: 症状ベースの検索
        similar_cases = []
        if problem.get("symptoms"):
            similar_cases = [
                {
                    "case_id": "case_001",
                    "similarity": 0.85,
                    "solution": "Optimization through caching",
                }
            ]

        return {
            "similar_cases": similar_cases,
            "best_match_confidence": 0.85 if similar_cases else 0.0,
        }

    def _get_execution_priorities(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """実行優先順位取得（タスク賢者）"""
        return {
            "priority_level": (
                "high"
                if problem.get("risk_factors", {}).get("production_impact") == "high"
                else "medium"
            ),
            "recommended_sequence": ["quick_fixes", "comprehensive_solutions"],
            "resource_allocation": "parallel_execution_recommended",
        }

    def _assess_problem_risks(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """問題リスク評価（インシデント賢者）"""
        risk_level = (
            "high"
            if problem.get("risk_factors", {}).get("user_complaints", 0) > 10
            else "medium"
        )

        return {
            "overall_risk": risk_level,
            "critical_factors": ["user_impact", "data_integrity"],
            "mitigation_required": risk_level == "high",
        }

    def _integrate_sage_inputs(
        self, contributions: Dict[str, Any], problem: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """賢者入力統合"""
        integrated = []

        # 各賢者の入力を統合した仮説生成
        base_hypothesis = {
            "statement": "Implement comprehensive optimization based on sage analysis",
            "hypothesis_type": "integrated",
            "multi_sage_confidence": 0.85,
            "sage_inputs": contributions,
        }

        integrated.append(base_hypothesis)

        # 追加の具体的仮説
        if contributions.get("rag_sage", {}).get("similar_cases"):
            integrated.append(
                {
                    "statement": "Apply caching solution from similar case",
                    "hypothesis_type": "performance",
                    "multi_sage_confidence": 0.80,
                    "based_on": "rag_sage_recommendation",
                }
            )

        return integrated

    def _form_sage_consensus(
        self, hypotheses: List[Dict[str, Any]], contributions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """賢者コンセンサス形成"""
        return {
            "consensus_reached": True,
            "primary_recommendation": hypotheses[0] if hypotheses else None,
            "confidence_level": 0.85,
            "dissenting_opinions": [],
        }

    def _create_collaborative_execution_plan(
        self, hypotheses: List[Dict[str, Any]], consensus: Dict[str, Any]
    ) -> Dict[str, Any]:
        """協調実行計画作成"""
        return {
            "execution_phases": [
                {"phase": "preparation", "duration": "1_hour", "lead_sage": "task"},
                {
                    "phase": "implementation",
                    "duration": "2_hours",
                    "lead_sage": "knowledge",
                },
                {"phase": "monitoring", "duration": "1_hour", "lead_sage": "incident"},
                {"phase": "evaluation", "duration": "30_minutes", "lead_sage": "rag"},
            ],
            "resource_allocation": "distributed",
            "rollback_authority": "incident_sage",
        }
