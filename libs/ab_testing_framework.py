#!/usr/bin/env python3
"""
A/B Testing Framework - A/Bテストフレームワーク
実験の設計、実行、分析、結果判定を統合的に管理

4賢者との連携:
📚 ナレッジ賢者: 過去のA/Bテスト結果の蓄積と成功パターン分析
🔍 RAG賢者: 類似実験の検索と結果比較
📋 タスク賢者: 実験スケジューリングと並行実験の管理
🚨 インシデント賢者: 実験の安全性監視とロールバック判断
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import hashlib
import json
import logging
import math
import random
import statistics
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from itertools import product
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class ABTestingFramework:
    """A/Bテストフレームワーク"""

    def __init__(self):
        """ABTestingFramework 初期化"""
        self.framework_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 実験管理
        self.experiments = {}
        self.active_experiments = set()
        self.experiment_history = deque(maxlen=1000)
        self.user_assignments = defaultdict(dict)  # user_id -> {exp_id: variant_id}

        # メトリクス追跡
        self.metrics_buffer = defaultdict(list)
        self.aggregated_metrics = defaultdict(lambda: defaultdict(dict))

        # 実験設定
        self.default_config = {
            "min_sample_size": 100,
            "max_experiments_per_user": 3,
            "safety_check_interval": 300,  # 5分
            "anomaly_threshold": 3.0,  # 標準偏差
        }

        # 4賢者統合フラグ
        self.knowledge_sage_integration = True
        self.rag_sage_integration = True
        self.task_sage_integration = True
        self.incident_sage_integration = True

        # ナレッジベースパス
        self.knowledge_base_path = PROJECT_ROOT / "knowledge_base" / "ab_test_results"
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)

        # 安全性監視
        self.safety_monitor = SafetyMonitor()

        logger.info(f"ABTestingFramework initialized: {self.framework_id}")

    def create_experiment(self, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """実験を作成"""
        try:
            experiment_id = f"exp_{uuid.uuid4().hex[:8]}"

            # バリアント設定
            variants = []
            traffic_sum = 0.0

            for variant_config in experiment_config["variants"]:
                variant_id = f"var_{uuid.uuid4().hex[:8]}"
                traffic_pct = experiment_config["traffic_allocation"].get(
                    variant_config["name"], 0.0
                )

                variants.append(
                    {
                        "variant_id": variant_id,
                        "name": variant_config["name"],
                        "description": variant_config.get("description", ""),
                        "parameters": variant_config["parameters"],
                        "traffic_percentage": traffic_pct,
                    }
                )
                traffic_sum += traffic_pct

            # トラフィック割り当て正規化
            if abs(traffic_sum - 1.0) > 0.001:
                for variant in variants:
                    variant["traffic_percentage"] /= traffic_sum

            # 実験オブジェクト作成
            experiment = {
                "experiment_id": experiment_id,
                "name": experiment_config["name"],
                "description": experiment_config.get("description", ""),
                "hypothesis": experiment_config.get("hypothesis", ""),
                "status": "created",
                "variants": variants,
                "metrics": experiment_config["metrics"],
                "duration": experiment_config["duration"],
                "success_criteria": experiment_config["success_criteria"],
                "created_at": datetime.now(),
                "configuration": experiment_config,
            }

            # 実験を保存
            self.experiments[experiment_id] = experiment
            self.experiment_history.append(experiment)

            logger.info(f"Experiment created: {experiment_id}")
            return experiment

        except Exception as e:
            logger.error(f"Error creating experiment: {str(e)}")
            return {"experiment_id": None, "status": "error", "error": str(e)}

    def allocate_traffic(
        self, experiment: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ユーザーをバリアントに割り当て"""
        try:
            experiment_id = experiment["experiment_id"]
            user_id = user_context["user_id"]

            # 既存の割り当てをチェック（sticky assignment）
            if experiment_id in self.user_assignments[user_id]:
                variant_id = self.user_assignments[user_id][experiment_id]
                variant = next(
                    v for v in experiment["variants"] if v["variant_id"] == variant_id
                )

                return {
                    "variant_id": variant_id,
                    "variant_name": variant["name"],
                    "experiment_id": experiment_id,
                    "allocation_reason": "existing_assignment",
                    "sticky": True,
                }

            # 新規割り当て - 決定的ハッシュベース
            hash_input = f"{experiment_id}_{user_id}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            normalized_hash = (hash_value % 10000) / 10000.0

            # トラフィック割合に基づいて割り当て
            cumulative = 0.0
            selected_variant = None

            for variant in experiment["variants"]:
                cumulative += variant["traffic_percentage"]
                if normalized_hash < cumulative:
                    selected_variant = variant
                    break

            if not selected_variant:
                selected_variant = experiment["variants"][-1]

            # 割り当てを保存
            self.user_assignments[user_id][experiment_id] = selected_variant[
                "variant_id"
            ]

            return {
                "variant_id": selected_variant["variant_id"],
                "variant_name": selected_variant["name"],
                "experiment_id": experiment_id,
                "allocation_reason": "new_assignment",
                "sticky": True,
            }

        except Exception as e:
            logger.error(f"Error allocating traffic: {str(e)}")
            return {"variant_id": None, "error": str(e)}

    def track_metrics(self, metric_event: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスを追跡"""
        try:
            event_id = f"evt_{uuid.uuid4().hex[:8]}"
            experiment_id = metric_event["experiment_id"]
            variant_id = metric_event["variant_id"]

            # イベントをバッファに追加
            self.metrics_buffer[experiment_id].append(
                {
                    "event_id": event_id,
                    "variant_id": variant_id,
                    "user_id": metric_event["user_id"],
                    "timestamp": metric_event.get("timestamp", datetime.now()),
                    "metrics": metric_event["metrics"],
                    "context": metric_event.get("context", {}),
                }
            )

            # 集計更新
            aggregation_updated = self._update_aggregations(
                experiment_id, variant_id, metric_event["metrics"]
            )

            # 異常検出
            anomaly_detected, anomaly_details = self._detect_anomalies(
                experiment_id, variant_id, metric_event["metrics"]
            )

            result = {
                "tracked": True,
                "event_id": event_id,
                "aggregation_updated": aggregation_updated,
                "anomaly_detected": anomaly_detected,
            }

            if anomaly_detected:
                result["anomaly_details"] = anomaly_details

            return result

        except Exception as e:
            logger.error(f"Error tracking metrics: {str(e)}")
            return {"tracked": False, "error": str(e)}

    def analyze_results(self, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """実験結果を分析"""
        try:
            # 統計的検定
            statistical_results = self._perform_statistical_tests(experiment_data)

            # 実用的有意性評価
            practical_significance = self._assess_practical_significance(
                experiment_data
            )

            # 信頼区間計算
            confidence_intervals = self._calculate_confidence_intervals(experiment_data)

            # 詳細メトリクス分析
            detailed_metrics = self._analyze_detailed_metrics(experiment_data)

            # 推奨事項生成
            recommendation = self._generate_recommendation(
                statistical_results, practical_significance
            )

            return {
                "statistical_results": statistical_results,
                "practical_significance": practical_significance,
                "confidence_intervals": confidence_intervals,
                "recommendation": recommendation,
                "detailed_metrics": detailed_metrics,
                "analysis_metadata": {
                    "analyzed_at": datetime.now(),
                    "sample_sizes": self._get_sample_sizes(experiment_data),
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}")
            return {"error": str(e)}

    def determine_winner(
        self, analysis_results: Dict[str, Any], success_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """勝者を判定"""
        try:
            # 統計的有意性チェック
            p_value = analysis_results["statistical_results"]["p_value"]
            stat_sig_met = p_value < (1 - success_criteria["statistical_significance"])

            # 実用的有意性チェック
            improvement = analysis_results["practical_significance"][
                "improvement_percentage"
            ]
            pract_sig_met = improvement >= success_criteria["practical_significance"]

            # 効果サイズチェック
            effect_size = analysis_results["statistical_results"]["effect_size"]
            min_effect = success_criteria.get("minimum_effect_size", 0.3)
            effect_size_met = effect_size >= min_effect

            # 勝者判定
            if stat_sig_met and pract_sig_met and effect_size_met:
                # パフォーマンス比較
                variant_performance = analysis_results.get("variant_performance", {})
                winner = min(
                    variant_performance.items(),
                    key=lambda x: x[1].get("mean", float("inf")),
                )[0]
                confidence = "high"
            else:
                winner = None
                confidence = "insufficient"

            # 理由説明
            reasoning = self._explain_decision(
                stat_sig_met,
                pract_sig_met,
                effect_size_met,
                p_value,
                improvement,
                effect_size,
            )

            # ロールアウト推奨
            rollout_recommendation = self._generate_rollout_recommendation(
                winner, confidence, analysis_results
            )

            return {
                "winner": winner,
                "confidence": confidence,
                "reasoning": reasoning,
                "rollout_recommendation": rollout_recommendation,
                "decision_metadata": {
                    "statistical_significance_met": stat_sig_met,
                    "practical_significance_met": pract_sig_met,
                    "effect_size_met": effect_size_met,
                },
            }

        except Exception as e:
            logger.error(f"Error determining winner: {str(e)}")
            return {"winner": None, "confidence": "error", "error": str(e)}

    def save_experiment_results(
        self, experiment_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """実験結果を保存（ナレッジ賢者連携）"""
        try:
            experiment_id = experiment_results["experiment_id"]

            # 学習内容抽出
            learnings = self._extract_learnings(experiment_results)

            # パターン識別
            patterns = self._identify_patterns(experiment_results)

            # ナレッジベースに保存
            save_path = self.knowledge_base_path / f"{experiment_id}_results.json"
            results_to_save = {
                "experiment": experiment_results,
                "learnings": learnings,
                "patterns": patterns,
                "saved_at": datetime.now(),
            }

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(results_to_save, f, indent=2, default=str)

            # ナレッジ統合
            knowledge_integration = {
                "status": "success",
                "patterns_identified": patterns,
                "learnings_count": len(learnings),
            }

            return {
                "saved": True,
                "knowledge_base_path": str(save_path),
                "experiment_id": experiment_id,
                "learnings_extracted": learnings,
                "knowledge_integration": knowledge_integration,
            }

        except Exception as e:
            logger.error(f"Error saving experiment results: {str(e)}")
            return {"saved": False, "error": str(e)}

    def search_similar_experiments(
        self, search_query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """類似実験を検索（RAG賢者連携）"""
        try:
            similar_experiments = []

            # ファイルベースの検索
            for result_file in self.knowledge_base_path.glob("*_results.json"):
                try:
                    with open(result_file, "r", encoding="utf-8") as f:
                        saved_result = json.load(f)

                    experiment = saved_result.get("experiment", {})
                    similarity = self._calculate_experiment_similarity(
                        search_query, experiment
                    )

                    if similarity > 0.7:
                        similar_experiments.append(
                            {
                                "experiment_id": experiment.get("experiment_id"),
                                "similarity_score": similarity,
                                "name": experiment.get("name"),
                                "results_summary": self._summarize_results(experiment),
                                "applicable_learnings": saved_result.get(
                                    "learnings", []
                                ),
                                "rag_integration": {
                                    "retrieval_confidence": similarity,
                                    "search_quality": (
                                        "high" if similarity > 0.8 else "medium"
                                    ),
                                },
                            }
                        )
                except Exception as e:
                    logger.error(f"Error reading result file: {str(e)}")

            # スコアでソート
            similar_experiments.sort(key=lambda x: x["similarity_score"], reverse=True)

            return similar_experiments[:5]  # Top 5

        except Exception as e:
            logger.error(f"Error searching similar experiments: {str(e)}")
            return []

    def monitor_experiment_safety(
        self, experiment_state: Dict[str, Any], safety_thresholds: Dict[str, Any]
    ) -> Dict[str, Any]:
        """実験の安全性を監視（インシデント賢者連携）"""
        try:
            violations = []
            safety_score = 1.0

            # エラー率チェック
            for variant, metrics in experiment_state.get("current_metrics", {}).items():
                error_rate = metrics.get("error_rate", 0)
                if error_rate > safety_thresholds["max_error_rate"]:
                    violations.append(
                        {
                            "type": "error_rate_violation",
                            "variant": variant,
                            "current_value": error_rate,
                            "threshold": safety_thresholds["max_error_rate"],
                        }
                    )
                    safety_score *= 0.5

                # 成功率チェック（閾値が設定されている場合のみ）
                if "min_success_rate" in safety_thresholds:
                    success_rate = metrics.get("success_rate", 1.0)
                    if success_rate < safety_thresholds["min_success_rate"]:
                        violations.append(
                            {
                                "type": "success_rate_violation",
                                "variant": variant,
                                "current_value": success_rate,
                                "threshold": safety_thresholds["min_success_rate"],
                            }
                        )
                        safety_score *= 0.6

            # アラートチェック
            for alert in experiment_state.get("alerts", []):
                if alert["severity"] == "high":
                    safety_score *= 0.7

            # 安全性判定
            is_safe = len(violations) == 0 and safety_score > 0.5

            # 推奨アクション
            if not is_safe:
                if safety_score < 0.3:
                    recommendation = "rollback"
                elif len(violations) > 2:
                    recommendation = "stop_variant"
                else:
                    recommendation = "monitor_closely"
            else:
                recommendation = "continue"

            # インシデントリスク評価
            incident_risk = self._assess_incident_risk(violations, experiment_state)

            return {
                "is_safe": is_safe,
                "safety_score": safety_score,
                "violations": violations,
                "recommendation": recommendation,
                "incident_risk": incident_risk,
                "monitoring_metadata": {
                    "checked_at": datetime.now(),
                    "thresholds_used": safety_thresholds,
                },
            }

        except Exception as e:
            logger.error(f"Error monitoring experiment safety: {str(e)}")
            return {"is_safe": False, "safety_score": 0.0, "error": str(e)}

    def schedule_experiments(
        self,
        experiment_queue: List[Dict[str, Any]],
        current_experiments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """実験をスケジュール（タスク賢者連携）"""
        try:
            # 優先度スコア計算
            for exp in experiment_queue:
                exp["priority_score"] = self._calculate_experiment_priority(exp)

            # 優先度でソート（criticalを最優先に）
            def sort_key(exp):
                """sort_keyメソッド"""
                if exp.get("priority") == "critical":
                    return (2.0, exp["priority_score"])  # criticalは最高優先
                else:
                    return (1.0, exp["priority_score"])

            experiment_queue.sort(key=sort_key, reverse=True)

            # スケジューリング
            scheduled = []
            timeline = []
            resource_allocation = defaultdict(float)
            conflicts_resolved = []

            current_time = datetime.now()

            # 現在の実験の完了時間を考慮
            for current_exp in current_experiments:
                completion_time = current_time + current_exp.get(
                    "completion_eta", timedelta(0)
                )
                timeline.append(
                    {
                        "time_slot": current_time,
                        "experiments": [current_exp["experiment_id"]],
                        "resource_usage": 0.5,  # 仮の値
                    }
                )

            # 新規実験のスケジューリング
            for exp in experiment_queue:
                # コンフリクトチェック
                has_conflict = False
                for scheduled_exp in scheduled:
                    if exp["experiment_id"] in scheduled_exp.get(
                        "conflicts_with", []
                    ) or scheduled_exp["experiment_id"] in exp.get(
                        "conflicts_with", []
                    ):
                        has_conflict = True
                        conflicts_resolved.append(
                            {
                                "experiment_1": exp["experiment_id"],
                                "experiment_2": scheduled_exp["experiment_id"],
                                "resolution": "sequential_execution",
                            }
                        )
                        break

                if not has_conflict or exp["priority"] == "critical":
                    scheduled.append(exp)

                    # タイムライン更新
                    slot_time = current_time + timedelta(
                        hours=len(scheduled) * 2  # 2時間間隔
                    )
                    timeline.append(
                        {
                            "time_slot": slot_time,
                            "experiments": [exp["experiment_id"]],
                            "resource_usage": self._estimate_resource_usage(exp),
                        }
                    )

                    # リソース割り当て
                    resource_allocation[exp["experiment_id"]] = (
                        self._allocate_resources(exp)
                    )

            return {
                "scheduled_experiments": scheduled,
                "execution_timeline": timeline,
                "resource_allocation": dict(resource_allocation),
                "conflict_resolution": conflicts_resolved,
                "scheduling_metadata": {
                    "scheduled_at": datetime.now(),
                    "total_experiments": len(scheduled),
                },
            }

        except Exception as e:
            logger.error(f"Error scheduling experiments: {str(e)}")
            return {"scheduled_experiments": [], "error": str(e)}

    def create_multivariate_experiment(
        self, multivariate_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """多変量実験を作成"""
        try:
            experiment_id = f"mv_exp_{uuid.uuid4().hex[:8]}"

            # 全要因の組み合わせ生成
            factors = multivariate_config["factors"]
            factor_names = list(factors.keys())
            factor_values = [factors[name] for name in factor_names]

            # フルファクトリアルデザイン
            combinations = list(product(*factor_values))

            # バリアント作成
            variants = []
            for i, combo in enumerate(combinations):
                variant_params = dict(zip(factor_names, combo))
                variants.append(
                    {
                        "variant_id": f"var_{i:03d}",
                        "name": f"variant_{i}",
                        "parameters": variant_params,
                        "combination_index": i,
                    }
                )

            # デザイン行列作成
            design_matrix = self._create_design_matrix(
                factors, multivariate_config.get("interactions", True)
            )

            # パワー分析
            power_analysis = self._perform_power_analysis(
                len(variants), multivariate_config.get("minimum_sample_per_cell", 100)
            )

            # 結果にpower_analysisを含める
            result = {
                "experiment_id": experiment_id,
                "type": "multivariate",
                "name": multivariate_config["name"],
                "variants": variants,
                "design_matrix": design_matrix,
                "factors": factors,
                "total_combinations": len(variants),
                "created_at": datetime.now(),
            }

            # design_matrixにpower_analysisを追加
            result["design_matrix"]["power_analysis"] = power_analysis

            return result

        except Exception as e:
            logger.error(f"Error creating multivariate experiment: {str(e)}")
            return {"experiment_id": None, "error": str(e)}

    def perform_sequential_test(
        self, sequential_config: Dict[str, Any], current_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """逐次検定を実行"""
        try:
            # SPRT (Sequential Probability Ratio Test) の実装
            alpha = sequential_config["alpha"]
            beta = sequential_config["beta"]
            min_effect = sequential_config["minimum_detectable_effect"]

            # 現在の統計量計算
            control_data = current_data["control"]
            treatment_data = current_data["treatment"]

            # 二項検定の場合
            p_control = control_data["successes"] / control_data["trials"]
            p_treatment = treatment_data["successes"] / treatment_data["trials"]

            # 対数尤度比
            llr = self._calculate_log_likelihood_ratio(
                control_data, treatment_data, min_effect
            )

            # 境界計算
            upper_bound = math.log((1 - beta) / alpha)
            lower_bound = math.log(beta / (1 - alpha))

            # 決定
            if llr >= upper_bound:
                decision = "stop_accept"  # 処理群が優位
            elif llr <= lower_bound:
                decision = "stop_reject"  # 有意差なし
            else:
                decision = "continue"  # データ収集継続

            # サンプルサイズ節約の推定
            fixed_sample_size = self._calculate_fixed_sample_size(
                alpha, beta, min_effect
            )
            current_sample_size = control_data["trials"] + treatment_data["trials"]
            sample_size_saved = max(0, fixed_sample_size - current_sample_size)

            return {
                "decision": decision,
                "confidence": abs(llr) / max(abs(upper_bound), abs(lower_bound)),
                "bounds": {
                    "upper": upper_bound,
                    "lower": lower_bound,
                    "current_statistic": llr,
                },
                "sample_size_saved": sample_size_saved,
                "test_metadata": {
                    "method": sequential_config["method"],
                    "current_sample_size": current_sample_size,
                },
            }

        except Exception as e:
            logger.error(f"Error performing sequential test: {str(e)}")
            return {"decision": "error", "error": str(e)}

    def start_experiment(self, experiment_id: str) -> None:
        """実験を開始"""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]["status"] = "running"
            self.experiments[experiment_id]["started_at"] = datetime.now()
            self.active_experiments.add(experiment_id)

    def get_experiment_state(self, experiment_id: str) -> Dict[str, Any]:
        """実験の現在状態を取得"""
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]

        # 現在のメトリクス集計
        current_metrics = {}
        for variant in experiment["variants"]:
            variant_metrics = self.aggregated_metrics[experiment_id].get(
                variant["variant_id"], {}
            )
            current_metrics[variant["name"]] = variant_metrics

        return {
            "experiment_id": experiment_id,
            "status": experiment["status"],
            "duration_elapsed": datetime.now()
            - experiment.get("started_at", datetime.now()),
            "current_metrics": current_metrics,
            "alerts": [],  # 簡略化
        }

    def get_experiment_data(self, experiment_id: str) -> Dict[str, Any]:
        """実験データを取得"""
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]

        # メトリクスデータ整形
        metrics_data = {}
        for variant in experiment["variants"]:
            variant_id = variant["variant_id"]
            variant_name = variant["name"]

            # バッファからサンプルデータ取得
            variant_events = [
                e
                for e in self.metrics_buffer[experiment_id]
                if e["variant_id"] == variant_id
            ]

            if variant_events:
                # response_timeの例
                response_times = [
                    e["metrics"].get("response_time", 0)
                    for e in variant_events
                    if "response_time" in e["metrics"]
                ]

                if response_times:
                    metrics_data[variant_name] = {
                        "response_time": {
                            "samples": response_times[:8],  # サンプル
                            "mean": (
                                statistics.mean(response_times) if response_times else 0
                            ),
                            "std": (
                                statistics.stdev(response_times)
                                if len(response_times) > 1
                                else 0
                            ),
                            "count": len(response_times),
                        }
                    }

        return {
            "experiment_id": experiment_id,
            "variants": [v["name"] for v in experiment["variants"]],
            "metrics_data": metrics_data,
            "duration": datetime.now() - experiment.get("started_at", datetime.now()),
            "total_participants": len(
                set(e["user_id"] for e in self.metrics_buffer[experiment_id])
            ),
        }

    def design_experiment_with_sages(
        self, complex_experiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """4賢者協調による実験設計"""
        try:
            sage_contributions = {}

            # ナレッジ賢者: 過去の成功パターン
            if self.knowledge_sage_integration:
                sage_contributions["knowledge_sage"] = {
                    "successful_patterns": self._get_successful_patterns(
                        complex_experiment
                    ),
                    "failure_patterns": self._get_failure_patterns(complex_experiment),
                    "recommendations": [
                        "Use gradual rollout",
                        "Segment users carefully",
                    ],
                }

            # RAG賢者: 類似実験の教訓
            if self.rag_sage_integration:
                similar_experiments = self.search_similar_experiments(
                    {
                        "objectives": complex_experiment.get("objectives", {}),
                        "constraints": complex_experiment.get("constraints", {}),
                    }
                )
                sage_contributions["rag_sage"] = {
                    "similar_experiments": similar_experiments[:3],
                    "key_learnings": self._extract_key_learnings(similar_experiments),
                }

            # タスク賢者: 実験スケジューリング
            if self.task_sage_integration:
                sage_contributions["task_sage"] = {
                    "optimal_schedule": self._determine_optimal_schedule(
                        complex_experiment
                    ),
                    "resource_requirements": self._estimate_resources(
                        complex_experiment
                    ),
                    "parallel_execution": self._can_run_parallel(complex_experiment),
                }

            # インシデント賢者: リスク評価と安全対策
            if self.incident_sage_integration:
                sage_contributions["incident_sage"] = {
                    "risk_assessment": self._assess_experiment_risks(
                        complex_experiment
                    ),
                    "safety_measures": self._recommend_safety_measures(
                        complex_experiment
                    ),
                    "rollback_strategy": self._design_rollback_strategy(
                        complex_experiment
                    ),
                }

            # 統合設計
            integrated_design = self._integrate_sage_recommendations(
                sage_contributions, complex_experiment
            )

            # 成功確率推定
            success_probability = self._estimate_success_probability(
                integrated_design, sage_contributions
            )

            # リスク緩和計画
            risk_mitigation_plan = self._create_risk_mitigation_plan(
                sage_contributions.get("incident_sage", {})
            )

            return {
                "sage_contributions": sage_contributions,
                "integrated_design": integrated_design,
                "risk_mitigation_plan": risk_mitigation_plan,
                "success_probability": success_probability,
                "design_metadata": {
                    "designed_at": datetime.now(),
                    "sages_consulted": list(sage_contributions.keys()),
                },
            }

        except Exception as e:
            logger.error(f"Error in sage collaboration: {str(e)}")
            return {"sage_contributions": {}, "error": str(e)}

    # ===== Private Helper Methods =====

    def _update_aggregations(
        self, experiment_id: str, variant_id: str, metrics: Dict[str, Any]
    ) -> bool:
        """メトリクス集計を更新"""
        try:
            for metric_name, value in metrics.items():
                if (
                    metric_name
                    not in self.aggregated_metrics[experiment_id][variant_id]
                ):
                    self.aggregated_metrics[experiment_id][variant_id][metric_name] = {
                        "sum": 0,
                        "count": 0,
                        "min": float("inf"),
                        "max": float("-inf"),
                    }

                agg = self.aggregated_metrics[experiment_id][variant_id][metric_name]

                if isinstance(value, (int, float)):
                    agg["sum"] += value
                    agg["count"] += 1
                    agg["min"] = min(agg["min"], value)
                    agg["max"] = max(agg["max"], value)
                    agg["mean"] = agg["sum"] / agg["count"]
                elif isinstance(value, bool):
                    agg["count"] += 1
                    agg["sum"] += int(value)
                    agg["rate"] = agg["sum"] / agg["count"]

            return True

        except Exception as e:
            logger.error(f"Error updating aggregations: {str(e)}")
            return False

    def _detect_anomalies(
        self, experiment_id: str, variant_id: str, metrics: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """異常を検出"""
        anomaly_detected = False
        anomaly_details = {}

        try:
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    agg = self.aggregated_metrics[experiment_id][variant_id].get(
                        metric_name, {}
                    )

                    if agg.get("count", 0) > 10:  # 十分なデータがある場合
                        mean = agg.get("mean", 0)
                        # 簡易的な標準偏差計算
                        std = abs(agg.get("max", 0) - agg.get("min", 0)) / 4  # 近似

                        if not (std > 0):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if std > 0:
                            z_score = abs(value - mean) / std
                            if not (z_score > self.default_config["anomaly_threshold"]):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if z_score > self.default_config["anomaly_threshold"]:
                                anomaly_detected = True
                                anomaly_details[metric_name] = {
                                    "value": value,
                                    "expected_range": (mean - 2 * std, mean + 2 * std),
                                    "z_score": z_score,
                                }

            return anomaly_detected, anomaly_details if anomaly_detected else None

        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return False, None

    def _perform_statistical_tests(
        self, experiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """統計的検定を実行"""
        try:
            # t検定の例（response_timeの比較）
            control_data = (
                experiment_data["metrics_data"]
                .get("control", {})
                .get("response_time", {})
            )
            treatment_data = (
                experiment_data["metrics_data"]
                .get("treatment_a", {})
                .get("response_time", {})
            )

            if control_data and treatment_data:
                # Welchのt検定（等分散を仮定しない）
                t_stat, p_value = stats.ttest_ind_from_stats(
                    control_data.get("mean", 0),
                    control_data.get("std", 1),
                    control_data.get("count", 1),
                    treatment_data.get("mean", 0),
                    treatment_data.get("std", 1),
                    treatment_data.get("count", 1),
                    equal_var=False,
                )

                # 効果サイズ（Cohen's d）
                pooled_std = math.sqrt(
                    (
                        control_data.get("std", 1) ** 2
                        + treatment_data.get("std", 1) ** 2
                    )
                    / 2
                )
                effect_size = (
                    abs(control_data.get("mean", 0) - treatment_data.get("mean", 0))
                    / pooled_std
                )

                # 検定力（簡略化）
                power = 0.8 if p_value < 0.05 and effect_size > 0.5 else 0.5
            else:
                t_stat, p_value, effect_size, power = 0, 1.0, 0, 0

            return {
                "test_type": "welch_t_test",
                "test_statistic": t_stat,
                "p_value": p_value,
                "effect_size": effect_size,
                "power": power,
            }

        except Exception as e:
            logger.error(f"Error performing statistical tests: {str(e)}")
            return {"test_type": "error", "p_value": 1.0, "effect_size": 0, "power": 0}

    def _assess_practical_significance(
        self, experiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """実用的有意性を評価"""
        try:
            control_data = (
                experiment_data["metrics_data"]
                .get("control", {})
                .get("response_time", {})
            )
            treatment_data = (
                experiment_data["metrics_data"]
                .get("treatment_a", {})
                .get("response_time", {})
            )

            if control_data and treatment_data:
                control_mean = control_data.get("mean", 0)
                treatment_mean = treatment_data.get("mean", 0)

                if control_mean > 0:
                    improvement_pct = (control_mean - treatment_mean) / control_mean
                else:
                    improvement_pct = 0

                meets_threshold = abs(improvement_pct) >= 0.1  # 10%以上の改善
            else:
                improvement_pct = 0
                meets_threshold = False

            return {
                "improvement_percentage": improvement_pct,
                "meets_threshold": meets_threshold,
                "business_impact": "high" if improvement_pct > 0.2 else "medium",
            }

        except Exception as e:
            logger.error(f"Error assessing practical significance: {str(e)}")
            return {"improvement_percentage": 0, "meets_threshold": False}

    def _calculate_confidence_intervals(
        self, experiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """信頼区間を計算"""
        try:
            confidence_level = 0.95
            z_score = 1.96  # 95%信頼区間

            intervals = {}

            for variant, data in experiment_data["metrics_data"].items():
                metric_data = data.get("response_time", {})
                mean = metric_data.get("mean", 0)
                std = metric_data.get("std", 1)
                n = metric_data.get("count", 1)

                margin_of_error = z_score * (std / math.sqrt(n))
                intervals[variant] = {
                    "mean": mean,
                    "lower": mean - margin_of_error,
                    "upper": mean + margin_of_error,
                }

            # 差の信頼区間
            if "control" in intervals and "treatment_a" in intervals:
                diff_mean = (
                    intervals["control"]["mean"] - intervals["treatment_a"]["mean"]
                )
                diff_margin = math.sqrt(
                    (intervals["control"]["upper"] - intervals["control"]["mean"]) ** 2
                    + (
                        intervals["treatment_a"]["upper"]
                        - intervals["treatment_a"]["mean"]
                    )
                    ** 2
                )
                intervals["difference"] = {
                    "mean": diff_mean,
                    "lower": diff_mean - diff_margin,
                    "upper": diff_mean + diff_margin,
                }

            return intervals

        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {str(e)}")
            return {}

    def _analyze_detailed_metrics(
        self, experiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """詳細メトリクス分析"""
        return {
            "sample_sizes": self._get_sample_sizes(experiment_data),
            "duration": str(experiment_data.get("duration", timedelta(0))),
            "variant_distribution": self._calculate_variant_distribution(
                experiment_data
            ),
        }

    def _get_sample_sizes(self, experiment_data: Dict[str, Any]) -> Dict[str, int]:
        """サンプルサイズを取得"""
        sample_sizes = {}
        for variant, data in experiment_data.get("metrics_data", {}).items():
            sample_sizes[variant] = data.get("response_time", {}).get("count", 0)
        return sample_sizes

    def _calculate_variant_distribution(
        self, experiment_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """バリアント分布を計算"""
        total = experiment_data.get("total_participants", 1)
        distribution = {}

        for variant in experiment_data.get("variants", []):
            count = self._get_sample_sizes(experiment_data).get(variant, 0)
            distribution[variant] = count / total if total > 0 else 0

        return distribution

    def _generate_recommendation(
        self,
        statistical_results: Dict[str, Any],
        practical_significance: Dict[str, Any],
    ) -> str:
        """推奨事項を生成"""
        if (
            statistical_results["p_value"] < 0.05
            and practical_significance["meets_threshold"]
        ):
            return "Significant improvement detected. Recommend proceeding with winner."
        elif statistical_results["p_value"] >= 0.05:
            return "No statistical significance. Continue collecting data or stop experiment."
        else:
            return "Statistical significance without practical impact. Review success criteria."

    def _explain_decision(
        self,
        stat_sig: bool,
        pract_sig: bool,
        effect_size: bool,
        p_value: float,
        improvement: float,
        effect: float,
    ) -> str:
        """決定理由を説明"""
        reasons = []

        if stat_sig:
            reasons.append(f"Statistical significance achieved (p={p_value:.3f})")
        else:
            reasons.append(f"No statistical significance (p={p_value:.3f})")

        if pract_sig:
            reasons.append(
                f"Practical significance met ({improvement:.1%} improvement)"
            )
        else:
            reasons.append(
                f"Practical significance not met ({improvement:.1%} improvement)"
            )

        if effect_size:
            reasons.append(f"Adequate effect size (d={effect:.2f})")
        else:
            reasons.append(f"Insufficient effect size (d={effect:.2f})")

        return "; ".join(reasons)

    def _generate_rollout_recommendation(
        self, winner: Optional[str], confidence: str, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ロールアウト推奨を生成"""
        if winner and confidence == "high":
            strategy = "gradual_rollout"
            phases = [
                {"percentage": 10, "duration": "24_hours"},
                {"percentage": 50, "duration": "48_hours"},
                {"percentage": 100, "duration": "permanent"},
            ]
        else:
            strategy = "no_rollout"
            phases = []

        return {
            "strategy": strategy,
            "phases": phases,
            "monitoring_plan": {
                "metrics": ["error_rate", "performance"],
                "alert_thresholds": {"error_rate": 0.05},
                "rollback_triggers": ["error_spike", "performance_degradation"],
            },
        }

    def _extract_learnings(self, experiment_results: Dict[str, Any]) -> List[str]:
        """学習内容を抽出"""
        learnings = experiment_results.get("learnings", [])

        # 結果から追加の学習を抽出
        if experiment_results.get("winner"):
            learnings.append(f"Variant {experiment_results['winner']} performed best")

        if experiment_results.get("results", {}).get("improvement", 0) > 0.2:
            learnings.append("Significant improvement achieved (>20%)")

        return learnings

    def _identify_patterns(self, experiment_results: Dict[str, Any]) -> List[str]:
        """パターンを識別"""
        patterns = []

        if experiment_results.get("winner") == "treatment_a":
            patterns.append("aggressive_optimization_successful")

        if experiment_results.get("results", {}).get("sample_size", 0) > 5000:
            patterns.append("large_sample_experiment")

        return patterns

    def _calculate_experiment_similarity(
        self, query: Dict[str, Any], experiment: Dict[str, Any]
    ) -> float:
        """実験の類似度を計算"""
        similarity = 0.0

        # タイプ一致
        if query.get("experiment_type") == experiment.get("type"):
            similarity += 0.3

        # メトリクス一致
        if query.get("target_metric") in str(experiment.get("metrics", {})):
            similarity += 0.4

        # コンテキスト一致
        if query.get("context", {}).get("system_component") in str(experiment):
            similarity += 0.3

        return min(similarity, 1.0)

    def _summarize_results(self, experiment: Dict[str, Any]) -> Dict[str, Any]:
        """結果をサマライズ"""
        return {
            "winner": experiment.get("winner", "unknown"),
            "improvement": experiment.get("results", {}).get("improvement", 0),
            "confidence": experiment.get("results", {}).get("confidence", 0),
        }

    def _assess_incident_risk(
        self, violations: List[Dict[str, Any]], experiment_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """インシデントリスクを評価"""
        if len(violations) > 2:
            level = "high"
            impact = "severe"
        elif len(violations) > 0:
            level = "medium"
            impact = "moderate"
        else:
            level = "low"
            impact = "minimal"

        return {
            "level": level,
            "potential_impact": impact,
            "mitigation_actions": (
                [
                    "Monitor closely",
                    "Prepare rollback",
                    "Alert on-call team",
                ]
                if level != "low"
                else []
            ),
        }

    def _calculate_experiment_priority(self, experiment: Dict[str, Any]) -> float:
        """実験の優先度スコアを計算"""
        priority_map = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
        base_priority = priority_map.get(experiment.get("priority", "medium"), 0.5)

        # リソース要件による調整
        resource_map = {"low": 1.0, "medium": 0.8, "high": 0.6}
        resource_factor = resource_map.get(
            experiment.get("resource_requirements", "medium"), 0.8
        )

        return base_priority * resource_factor

    def _estimate_resource_usage(self, experiment: Dict[str, Any]) -> float:
        """リソース使用量を推定"""
        resource_map = {"low": 0.2, "medium": 0.5, "high": 0.8}
        return resource_map.get(experiment.get("resource_requirements", "medium"), 0.5)

    def _allocate_resources(self, experiment: Dict[str, Any]) -> Dict[str, float]:
        """リソースを割り当て"""
        return {
            "cpu": self._estimate_resource_usage(experiment),
            "memory": self._estimate_resource_usage(experiment) * 0.8,
            "bandwidth": self._estimate_resource_usage(experiment) * 0.6,
        }

    def _create_design_matrix(
        self, factors: Dict[str, List[Any]], interactions: bool
    ) -> Dict[str, Any]:
        """デザイン行列を作成"""
        num_factors = len(factors)
        num_levels = [len(levels) for levels in factors.values()]
        total_cells = 1
        for n in num_levels:
            total_cells *= n

        # 自由度計算
        main_effects_df = sum(n - 1 for n in num_levels)
        interaction_df = 0

        if interactions and num_factors > 1:
            # 2要因交互作用の自由度
            for i in range(num_factors):
                for j in range(i + 1, num_factors):
                    interaction_df += (num_levels[i] - 1) * (num_levels[j] - 1)

        return {
            "full_factorial": True,
            "num_factors": num_factors,
            "num_cells": total_cells,
            "degrees_of_freedom": {
                "total": total_cells - 1,
                "main_effects": main_effects_df,
                "interactions": interaction_df,
                "error": total_cells - 1 - main_effects_df - interaction_df,
            },
        }

    def _perform_power_analysis(
        self, num_variants: int, min_sample_per_cell: int
    ) -> Dict[str, Any]:
        """パワー分析を実行"""
        # 簡略化されたパワー分析
        total_sample = num_variants * min_sample_per_cell

        # 効果サイズ別の検出力
        power_by_effect = {
            "small": 0.2 if total_sample < 1000 else 0.5,
            "medium": 0.5 if total_sample < 1000 else 0.8,
            "large": 0.8 if total_sample < 1000 else 0.95,
        }

        return {
            "total_sample_required": total_sample,
            "power_by_effect_size": power_by_effect,
            "recommended_sample": max(total_sample, 1000),
        }

    def _calculate_log_likelihood_ratio(
        self, control: Dict[str, int], treatment: Dict[str, int], min_effect: float
    ) -> float:
        """対数尤度比を計算"""
        # 二項分布の対数尤度比
        p0 = control["successes"] / control["trials"]
        p1 = treatment["successes"] / treatment["trials"]

        # H0: p1 = p0, H1: p1 = p0 + min_effect
        p_null = (control["successes"] + treatment["successes"]) / (
            control["trials"] + treatment["trials"]
        )
        p_alt = p0 + min_effect

        # 尤度計算（簡略化）
        if p1 > p0:
            llr = treatment["successes"] * math.log(max(p1 / p_null, 0.001))
        else:
            llr = treatment["successes"] * math.log(max(p_null / p1, 0.001))

        return llr

    def _calculate_fixed_sample_size(
        self, alpha: float, beta: float, min_effect: float
    ) -> int:
        """固定サンプルサイズを計算"""
        # 二項検定のサンプルサイズ（簡略化）
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(1 - beta)

        p = 0.5  # 仮定
        n = ((z_alpha + z_beta) ** 2 * 2 * p * (1 - p)) / (min_effect**2)

        return int(n * 2)  # 両群の合計

    def _get_successful_patterns(self, experiment: Dict[str, Any]) -> List[str]:
        """成功パターンを取得"""
        patterns = []

        if experiment.get("historical_context", {}).get("successful_patterns"):
            patterns.extend(experiment["historical_context"]["successful_patterns"])

        return patterns

    def _get_failure_patterns(self, experiment: Dict[str, Any]) -> List[str]:
        """失敗パターンを取得"""
        # 過去の失敗から学習
        if experiment.get("historical_context", {}).get("failed_experiments", 0) > 0:
            return ["avoid_drastic_changes", "ensure_proper_monitoring"]
        return []

    def _extract_key_learnings(
        self, similar_experiments: List[Dict[str, Any]]
    ) -> List[str]:
        """主要な学習を抽出"""
        learnings = []
        for exp in similar_experiments[:3]:
            learnings.extend(exp.get("applicable_learnings", []))
        return list(set(learnings))  # 重複除去

    def _determine_optimal_schedule(self, experiment: Dict[str, Any]) -> Dict[str, Any]:
        """最適スケジュールを決定"""
        return {
            "start_time": "next_monday_morning",
            "duration": "1_week",
            "checkpoints": ["24h", "72h", "1w"],
        }

    def _estimate_resources(self, experiment: Dict[str, Any]) -> Dict[str, Any]:
        """リソース要件を推定"""
        return {"compute": "medium", "storage": "low", "bandwidth": "medium"}

    def _can_run_parallel(self, experiment: Dict[str, Any]) -> bool:
        """並列実行可能かチェック"""
        # 目的が競合しない場合は並列実行可能
        objectives = experiment.get("objectives", {})
        return not (
            objectives.get("improve_performance") and objectives.get("reduce_errors")
        )

    def _assess_experiment_risks(self, experiment: Dict[str, Any]) -> Dict[str, Any]:
        """実験リスクを評価"""
        risk_level = "medium"

        if experiment.get("constraints", {}).get("no_negative_impact"):
            risk_level = "high"

        return {
            "overall_risk": risk_level,
            "risk_factors": ["user_impact", "system_stability"],
            "mitigation_required": risk_level in ["high", "critical"],
        }

    def _recommend_safety_measures(self, experiment: Dict[str, Any]) -> List[str]:
        """安全対策を推奨"""
        measures = ["Real-time monitoring", "Automated rollback"]

        if experiment.get("constraints", {}).get("gradual_rollout"):
            measures.append("Phased deployment")

        return measures

    def _design_rollback_strategy(self, experiment: Dict[str, Any]) -> Dict[str, Any]:
        """ロールバック戦略を設計"""
        return {
            "trigger_conditions": ["error_rate > 5%", "response_time > 2x baseline"],
            "rollback_time": "< 5 minutes",
            "data_preservation": True,
        }

    def _integrate_sage_recommendations(
        self, contributions: Dict[str, Any], experiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """賢者の推奨を統合"""
        return {
            "experiment_phases": [
                {"phase": "pilot", "duration": "48h", "traffic": "5%"},
                {"phase": "expansion", "duration": "72h", "traffic": "25%"},
                {"phase": "full_rollout", "duration": "ongoing", "traffic": "100%"},
            ],
            "safety_checkpoints": contributions.get("incident_sage", {}).get(
                "safety_measures", []
            ),
            "success_metrics": ["conversion_rate", "error_rate", "user_satisfaction"],
        }

    def _estimate_success_probability(
        self, design: Dict[str, Any], contributions: Dict[str, Any]
    ) -> float:
        """成功確率を推定"""
        base_probability = 0.5

        # 過去の成功パターンがある場合
        if contributions.get("knowledge_sage", {}).get("successful_patterns"):
            base_probability += 0.2

        # 類似実験が成功している場合
        if contributions.get("rag_sage", {}).get("similar_experiments"):
            base_probability += 0.15

        # 適切な安全対策がある場合
        if contributions.get("incident_sage", {}).get("safety_measures"):
            base_probability += 0.1

        return min(base_probability, 0.95)

    def _create_risk_mitigation_plan(
        self, incident_sage_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """リスク緩和計画を作成"""
        return {
            "monitoring_alerts": [
                {"metric": "error_rate", "threshold": 0.05, "action": "notify"},
                {
                    "metric": "response_time",
                    "threshold": "2x_baseline",
                    "action": "rollback",
                },
            ],
            "escalation_path": ["on-call engineer", "team lead", "incident commander"],
            "rollback_procedure": incident_sage_input.get("rollback_strategy", {}),
        }


class SafetyMonitor:
    """実験の安全性監視"""

    def __init__(self):
        """初期化メソッド"""
        self.alert_history = deque(maxlen=100)
        self.safety_thresholds = {
            "error_rate": 0.05,
            "response_time_degradation": 1.5,
            "success_rate": 0.95,
        }

    def check_safety(self, metrics: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """安全性をチェック"""
        violations = []

        if metrics.get("error_rate", 0) > self.safety_thresholds["error_rate"]:
            violations.append("High error rate detected")

        if metrics.get("success_rate", 1.0) < self.safety_thresholds["success_rate"]:
            violations.append("Low success rate detected")

        return len(violations) == 0, violations
