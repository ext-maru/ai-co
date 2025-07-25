"""
Servant自動選択システム

タスクの特性、組織の専門性、現在の負荷状況、過去の実績を考慮して
最適なElder Servantを自動選択するインテリジェントシステム。
"""

import asyncio
import logging
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple

from ..base.elder_servant_base import (
    ElderServantBase,
    ServantCapability,
    ServantDomain,
    ServantRequest,
    ServantResponse,
)
from ..registry.servant_registry import ServantRegistry, get_registry

class SelectionCriteria(Enum):
    """選択基準"""

    PERFORMANCE = "performance"  # パフォーマンス重視
    QUALITY = "quality"  # 品質重視
    AVAILABILITY = "availability"  # 可用性重視
    EXPERTISE = "expertise"  # 専門性重視
    LOAD_BALANCE = "load_balance"  # 負荷分散重視
    COST_EFFICIENCY = "cost_efficiency"  # コスト効率重視

class TaskType(Enum):
    """タスクタイプ分類"""

    URGENT = "urgent"  # 緊急タスク
    COMPLEX = "complex"  # 複雑タスク
    ROUTINE = "routine"  # 定型タスク
    RESEARCH = "research"  # 調査タスク
    IMPLEMENTATION = "implementation"  # 実装タスク
    MAINTENANCE = "maintenance"  # 保守タスク
    TESTING = "testing"  # テストタスク
    SECURITY = "security"  # セキュリティタスク

@dataclass
class TaskProfile:
    """タスクプロファイル"""

    task_id: str
    task_type: TaskType
    priority: str
    estimated_duration: float
    required_capabilities: List[ServantCapability]
    preferred_domain: Optional[ServantDomain]
    complexity_score: float  # 0.0-1.0
    urgency_score: float  # 0.0-1.0
    quality_requirement: float  # 0.0-1.0
    constraints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServantProfile:
    """サーバントプロファイル"""

    servant: ElderServantBase
    domain: ServantDomain
    capabilities: List[ServantCapability]
    current_load: float  # 0.0-1.0
    performance_history: Dict[str, float]
    quality_scores: Dict[str, float]
    specialization_score: Dict[ServantCapability, float]
    availability_score: float  # 0.0-1.0
    cost_factor: float  # 相対的コスト (1.0が基準)

@dataclass
class SelectionResult:
    """選択結果"""

    selected_servant: ElderServantBase
    selection_score: float
    selection_reasoning: Dict[str, Any]
    alternative_servants: List[Tuple[ElderServantBase, float]]
    confidence: float  # 0.0-1.0
    estimated_execution_time: float
    selection_criteria_used: SelectionCriteria

class ServantAutoSelector:
    """
    Servant自動選択システム

    機械学習ベースの選択アルゴリズムを使用して、
    タスクに最適なElder Servantを自動選択する。
    """

    def __init__(self, registry: Optional[ServantRegistry] = None):
        """初期化メソッド"""
        self.logger = logging.getLogger("elder_servants.auto_selector")
        self.registry = registry or get_registry()

        # 学習データ蓄積
        self.selection_history: List[Dict[str, Any]] = []
        self.performance_feedback: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # 選択統計
        self.selection_stats = {
            "total_selections": 0,
            "successful_selections": 0,
            "failed_selections": 0,
            "average_selection_score": 0.0,
            "criteria_usage": defaultdict(int),
        }

        # 学習モデル重み（初期値）
        self.model_weights = {
            "performance_weight": 0.25,
            "quality_weight": 0.25,
            "availability_weight": 0.20,
            "expertise_weight": 0.20,
            "load_balance_weight": 0.10,
        }

        # キャッシュ
        self.servant_profiles_cache: Dict[str, ServantProfile] = {}
        self.cache_expiry = timedelta(minutes=5)
        self.last_cache_update = datetime.now()

    async def select_optimal_servant(
        self,
        task_profile: TaskProfile,
        criteria: SelectionCriteria = SelectionCriteria.PERFORMANCE,
    ) -> SelectionResult:
        """
        最適なサーバント選択

        Args:
            task_profile: タスクプロファイル
            criteria: 選択基準

        Returns:
            選択結果
        """
        start_time = time.time()
        self.logger.info(f"Starting servant selection for task: {task_profile.task_id}")

        try:
            # サーバントプロファイル更新
            await self._update_servant_profiles()

            # 候補サーバント取得
            candidate_servants = await self._get_candidate_servants(task_profile)

            if not candidate_servants:
                raise ValueError("No suitable servants available for this task")

            # 選択スコア計算
            scored_candidates = await self._calculate_selection_scores(
                task_profile, candidate_servants, criteria
            )

            # 最適サーバント選択
            best_servant, best_score = max(scored_candidates, key=lambda x: x[1])

            # 代替案作成
            alternatives = sorted(
                [
                    (servant, score)
                    for servant, score in scored_candidates
                    if servant != best_servant
                ],
                key=lambda x: x[1],
                reverse=True,
            )[
                :3
            ]  # 上位3つの代替案

            # 信頼度計算
            confidence = self._calculate_confidence(best_score, scored_candidates)

            # 実行時間推定
            estimated_time = await self._estimate_execution_time(
                best_servant, task_profile
            )

            # 選択理由生成
            reasoning = await self._generate_selection_reasoning(
                best_servant, task_profile, criteria, best_score
            )

            selection_result = SelectionResult(
                selected_servant=best_servant,
                selection_score=best_score,
                selection_reasoning=reasoning,
                alternative_servants=alternatives,
                confidence=confidence,
                estimated_execution_time=estimated_time,
                selection_criteria_used=criteria,
            )

            # 選択履歴記録
            await self._record_selection_history(
                task_profile, selection_result, start_time
            )

            # 統計更新
            self._update_selection_stats(criteria, best_score)

            self.logger.info(
                f"Selected servant: {best_servant.name} (score: {best_score:0.3f}, confidence:" \
                    " {confidence:0.3f})"
            )
            return selection_result

        except Exception as e:
            # Handle specific exception case
            self.logger.error(
                f"Servant selection failed for task {task_profile.task_id}: {str(e)}"
            )
            raise

    async def _update_servant_profiles(self):
        """サーバントプロファイル更新"""
        current_time = datetime.now()

        # キャッシュ有効性チェック
        if (
            current_time - self.last_cache_update
        ) < self.cache_expiry and self.servant_profiles_cache:
            return

        self.servant_profiles_cache.clear()

        # 全サーバント情報取得
        all_servants_info = self.registry.list_all_servants()

        for servant_info in all_servants_info:
            # Process each item in collection
            servant = self.registry.get_servant(servant_info["name"])
            if not servant:
                continue

            # サーバント詳細プロファイル作成
            profile = await self._create_servant_profile(servant, servant_info)
            self.servant_profiles_cache[servant_info["name"]] = profile

        self.last_cache_update = current_time

            f"Updated {len(self.servant_profiles_cache)} servant profiles"
        )

    async def _create_servant_profile(
        self, servant: ElderServantBase, servant_info: Dict[str, Any]
    ) -> ServantProfile:
        """個別サーバントプロファイル作成"""
        metrics = servant.get_metrics()

        # 現在の負荷計算
        current_load = self._calculate_current_load(metrics)

        # パフォーマンス履歴
        performance_history = {
            "average_processing_time": metrics.get("average_processing_time", 0),
            "success_rate": metrics.get("success_rate", 0),
            "tasks_processed": metrics.get("tasks_processed", 0),
        }

        # 品質スコア
        quality_scores = metrics.get("quality_scores", {})

        # 専門化スコア計算
        specialization_score = await self._calculate_specialization_scores(servant)

        # 可用性スコア
        availability_score = self._calculate_availability_score(servant, metrics)

        # コスト要素（ドメインベース）
        cost_factor = self._calculate_cost_factor(servant.domain)

        return ServantProfile(
            servant=servant,
            domain=servant.domain,
            capabilities=servant.get_capabilities(),
            current_load=current_load,
            performance_history=performance_history,
            quality_scores=quality_scores,
            specialization_score=specialization_score,
            availability_score=availability_score,
            cost_factor=cost_factor,
        )

    def _calculate_current_load(self, metrics: Dict[str, Any]) -> float:
        """現在の負荷計算"""
        tasks_processed = metrics.get("tasks_processed", 0)

        # 簡易負荷計算（実際の実装ではより詳細な計算が必要）
        if tasks_processed == 0:
            return 0.0

        # 最近のタスク処理頻度に基づく負荷推定
        base_load = min(tasks_processed / 100.0, 1.0)  # 100タスクで満負荷と仮定

        # 成功率が低い場合は負荷が高いと判定
        success_rate = metrics.get("success_rate", 1.0)
        load_adjustment = 1.0 + (1.0 - success_rate) * 0.5

        return min(base_load * load_adjustment, 1.0)

    async def _calculate_specialization_scores(
        self, servant: ElderServantBase
    ) -> Dict[ServantCapability, float]:
        """専門化スコア計算"""
        specialization_scores = {}
        servant_capabilities = servant.get_capabilities()

        # サーバントのドメインに基づく専門性
        domain_expertise = {
            ServantDomain.DWARF_WORKSHOP: {
                ServantCapability.CODE_GENERATION: 0.9,
                ServantCapability.TESTING: 0.85,
                ServantCapability.REFACTORING: 0.8,
                ServantCapability.PERFORMANCE: 0.7,
            },
            ServantDomain.RAG_WIZARDS: {
                ServantCapability.ANALYSIS: 0.95,
                ServantCapability.DOCUMENTATION: 0.8,
                ServantCapability.PERFORMANCE: 0.6,
            },
            ServantDomain.ELF_FOREST: {
                ServantCapability.MONITORING: 0.95,
                ServantCapability.PERFORMANCE: 0.9,
                ServantCapability.ANALYSIS: 0.7,
            },
            ServantDomain.INCIDENT_KNIGHTS: {
                ServantCapability.SECURITY: 0.95,
                ServantCapability.TESTING: 0.8,
                ServantCapability.MONITORING: 0.75,
            },
        }

        domain_scores = domain_expertise.get(servant.domain, {})

        for capability in ServantCapability:
            if capability in servant_capabilities:
                # サーバントが持つ能力は基本スコア + ドメイン専門性
                base_score = 0.6
                domain_bonus = domain_scores.get(capability, 0.0)
                specialization_scores[capability] = min(base_score + domain_bonus, 1.0)
            else:
                # 持たない能力は低スコア
                specialization_scores[capability] = domain_scores.get(capability, 0.1)

        return specialization_scores

    def _calculate_availability_score(
        self, servant: ElderServantBase, metrics: Dict[str, Any]
    ) -> float:
        """可用性スコア計算"""
        # 成功率ベース
        success_rate = metrics.get("success_rate", 0.5)

        # 処理速度ベース
        avg_time = metrics.get("average_processing_time", 10.0)
        speed_score = max(0.0, 1.0 - (avg_time / 60.0))  # 60秒で0点

        # 負荷ベース
        current_load = self._calculate_current_load(metrics)
        load_score = 1.0 - current_load

        # 重み付き平均
        availability = success_rate * 0.5 + speed_score * 0.3 + load_score * 0.2
        return max(0.0, min(1.0, availability))

    def _calculate_cost_factor(self, domain: ServantDomain) -> float:
        """コスト要素計算"""
        # ドメイン別相対コスト
        domain_costs = {
            ServantDomain.DWARF_WORKSHOP: 1.0,  # 標準
            ServantDomain.RAG_WIZARDS: 1.2,  # 高コスト（調査研究）
            ServantDomain.ELF_FOREST: 0.8,  # 低コスト（監視保守）
            ServantDomain.INCIDENT_KNIGHTS: 1.5,  # 高コスト（緊急対応）
        }

        return domain_costs.get(domain, 1.0)

    async def _get_candidate_servants(
        self, task_profile: TaskProfile
    ) -> List[ServantProfile]:
        """候補サーバント取得"""
        candidates = []

        # 優先ドメインが指定されている場合
        if task_profile.preferred_domain:
            domain_servants = self.registry.find_by_domain(
                task_profile.preferred_domain
            )
            for servant in domain_servants:
                # Process each item in collection
                if servant.name in self.servant_profiles_cache:
                    candidates.append(self.servant_profiles_cache[servant.name])
        else:
            # 必要能力ベースで候補選出
            for capability in task_profile.required_capabilities:
                capability_servants = self.registry.find_by_capability(capability)
                for servant in capability_servants:
                    # Process each item in collection
                    if servant.name in self.servant_profiles_cache:
                        profile = self.servant_profiles_cache[servant.name]
                        # Removed invalid continue statement
                        if profile not in candidates:
                            candidates.append(profile)

        # 全候補が見つからない場合は全サーバントから選択
        if not candidates:
            candidates = list(self.servant_profiles_cache.values())

        # 基本的なフィルタリング
        filtered_candidates = []
        for profile in candidates:
            # 負荷チェック
            if profile.current_load < 0.95:  # 95%以下の負荷
                # 可用性チェック
                if profile.availability_score > 0.2:  # 最低限の可用性
                    filtered_candidates.append(profile)

        return filtered_candidates if filtered_candidates else candidates

    async def _calculate_selection_scores(
        self,
        task_profile: TaskProfile,
        candidates: List[ServantProfile],
        criteria: SelectionCriteria,
    ) -> List[Tuple[ElderServantBase, float]]:
        """選択スコア計算"""
        scored_candidates = []

        for profile in candidates:
            # Process each item in collection
            score = await self._calculate_individual_score(
                task_profile, profile, criteria
            )
            scored_candidates.append((profile.servant, score))

        return scored_candidates

    async def _calculate_individual_score(
        self,
        task_profile: TaskProfile,
        profile: ServantProfile,
        criteria: SelectionCriteria,
    ) -> float:
        """個別スコア計算"""
        scores = {}

        # パフォーマンススコア
        scores["performance"] = self._calculate_performance_score(task_profile, profile)

        # 品質スコア
        scores["quality"] = self._calculate_quality_score(task_profile, profile)

        # 可用性スコア
        scores["availability"] = profile.availability_score

        # 専門性スコア
        scores["expertise"] = self._calculate_expertise_score(task_profile, profile)

        # 負荷分散スコア
        scores["load_balance"] = 1.0 - profile.current_load

        # コスト効率スコア
        scores["cost_efficiency"] = 1.0 / profile.cost_factor

        # 基準に基づく重み調整
        weights = self._get_criteria_weights(criteria)

        # 重み付きスコア計算
        weighted_score = 0.0
        for factor, weight in weights.items():
            weighted_score += scores.get(factor, 0.0) * weight

        # 学習済み重みの適用
        model_adjustment = self._apply_model_weights(scores, task_profile)

        final_score = weighted_score * 0.7 + model_adjustment * 0.3
        return max(0.0, min(1.0, final_score))

    def _calculate_performance_score(
        self, task_profile: TaskProfile, profile: ServantProfile
    ) -> float:
        """パフォーマンススコア計算"""
        # 処理速度
        avg_time = profile.performance_history.get("average_processing_time", 10.0)
        speed_score = max(0.0, 1.0 - (avg_time / 30.0))  # 30秒で0点

        # 成功率
        success_rate = profile.performance_history.get("success_rate", 0.5)

        # 経験値（処理タスク数）
        tasks_processed = profile.performance_history.get("tasks_processed", 0)
        experience_score = min(1.0, tasks_processed / 50.0)  # 50タスクで満点

        return speed_score * 0.4 + success_rate * 0.4 + experience_score * 0.2

    def _calculate_quality_score(
        self, task_profile: TaskProfile, profile: ServantProfile
    ) -> float:
        """品質スコア計算"""
        quality_scores = profile.quality_scores

        if not quality_scores:
            return 0.5  # デフォルト

        # タスクの品質要求レベルに応じた重み付け
        if task_profile.quality_requirement > 0.8:
            # 高品質要求
            weights = {
                "root_cause_resolution": 0.3,
                "test_coverage": 0.3,
                "security_score": 0.2,
                "maintainability_score": 0.2,
            }
        else:
            # 標準品質要求
            weights = {
                "root_cause_resolution": 0.25,
                "test_coverage": 0.25,
                "performance_score": 0.25,
                "maintainability_score": 0.25,
            }

        weighted_quality = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            # Process each item in collection
            if metric in quality_scores:
                weighted_quality += (quality_scores[metric] / 100.0) * weight
                total_weight += weight

        return weighted_quality / total_weight if total_weight > 0 else 0.5

    def _calculate_expertise_score(
        self, task_profile: TaskProfile, profile: ServantProfile
    ) -> float:
        """専門性スコア計算"""
        expertise_scores = []

        for capability in task_profile.required_capabilities:
            # Process each item in collection
            score = profile.specialization_score.get(capability, 0.0)
            expertise_scores.append(score)

        if not expertise_scores:
            return 0.5

        # 必要能力での平均専門性
        avg_expertise = sum(expertise_scores) / len(expertise_scores)

        # 複雑度による調整
        complexity_bonus = task_profile.complexity_score * 0.2

        return min(1.0, avg_expertise + complexity_bonus)

    def _get_criteria_weights(self, criteria: SelectionCriteria) -> Dict[str, float]:
        """基準別重み取得"""
        weights_map = {
            SelectionCriteria.PERFORMANCE: {
                "performance": 0.5,
                "availability": 0.2,
                "load_balance": 0.2,
                "expertise": 0.1,
            },
            SelectionCriteria.QUALITY: {
                "quality": 0.5,
                "expertise": 0.3,
                "performance": 0.2,
            },
            SelectionCriteria.AVAILABILITY: {
                "availability": 0.5,
                "load_balance": 0.3,
                "performance": 0.2,
            },
            SelectionCriteria.EXPERTISE: {
                "expertise": 0.6,
                "quality": 0.25,
                "performance": 0.15,
            },
            SelectionCriteria.LOAD_BALANCE: {
                "load_balance": 0.5,
                "availability": 0.3,
                "performance": 0.2,
            },
            SelectionCriteria.COST_EFFICIENCY: {
                "cost_efficiency": 0.4,
                "performance": 0.3,
                "load_balance": 0.3,
            },
        }

        return weights_map.get(
            criteria,
            {
                "performance": 0.25,
                "quality": 0.25,
                "availability": 0.2,
                "expertise": 0.2,
                "load_balance": 0.1,
            },
        )

    def _apply_model_weights(
        self, scores: Dict[str, float], task_profile: TaskProfile
    ) -> float:
        """学習済みモデル重み適用"""
        weighted_score = 0.0

        for factor, weight in self.model_weights.items():
            # Process each item in collection
            factor_name = factor.replace("_weight", "")
            score = scores.get(factor_name, 0.0)
            weighted_score += score * weight

        # タスクタイプによる調整
        task_type_bonus = self._get_task_type_bonus(task_profile.task_type, scores)

        return weighted_score + task_type_bonus

    def _get_task_type_bonus(
        self, task_type: TaskType, scores: Dict[str, float]
    ) -> float:
        """タスクタイプボーナス"""
        bonus_map = {
            TaskType.URGENT: scores.get("availability", 0) * 0.1,
            TaskType.COMPLEX: scores.get("expertise", 0) * 0.1,
            TaskType.ROUTINE: scores.get("load_balance", 0) * 0.1,
            TaskType.RESEARCH: scores.get("expertise", 0) * 0.1,
            TaskType.IMPLEMENTATION: scores.get("performance", 0) * 0.1,
            TaskType.MAINTENANCE: scores.get("availability", 0) * 0.1,
            TaskType.TESTING: scores.get("quality", 0) * 0.1,
            TaskType.SECURITY: scores.get("quality", 0) * 0.1,
        }

        return bonus_map.get(task_type, 0.0)

    def _calculate_confidence(
        self, best_score: float, all_scores: List[Tuple[ElderServantBase, float]]
    ) -> float:
        """選択信頼度計算"""
        if len(all_scores) <= 1:
            return 1.0

        scores = [score for _, score in all_scores]
        scores.sort(reverse=True)

        # 最高スコアと2番目のスコアの差
        score_gap = scores[0] - scores[1] if len(scores) > 1 else scores[0]

        # スコア分散
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = math.sqrt(variance)

        # 信頼度計算
        gap_confidence = min(1.0, score_gap * 2.0)  # 0.5の差で満点
        variance_confidence = max(0.0, 1.0 - std_dev)  # 分散が小さいほど高信頼度
        absolute_confidence = best_score  # 絶対スコア

        return (
            gap_confidence * 0.4 + variance_confidence * 0.3 + absolute_confidence * 0.3
        )

    async def _estimate_execution_time(
        self, servant: ElderServantBase, task_profile: TaskProfile
    ) -> float:
        """実行時間推定"""
        metrics = servant.get_metrics()
        base_time = metrics.get("average_processing_time", 5.0)

        # 複雑度による調整
        complexity_factor = 1.0 + task_profile.complexity_score

        # 負荷による調整
        profile = self.servant_profiles_cache.get(servant.name)
        if profile:
            load_factor = 1.0 + (profile.current_load * 0.5)
        else:
            load_factor = 1.0

        estimated_time = base_time * complexity_factor * load_factor

        # 推定継続時間が指定されている場合は考慮
        if task_profile.estimated_duration > 0:
            estimated_time = (estimated_time + task_profile.estimated_duration) / 2

        return estimated_time

    async def _generate_selection_reasoning(
        self,
        servant: ElderServantBase,
        task_profile: TaskProfile,
        criteria: SelectionCriteria,
        score: float,
    ) -> Dict[str, Any]:
        """選択理由生成"""
        profile = self.servant_profiles_cache.get(servant.name)

        reasoning = {
            "selected_servant": servant.name,
            "domain": servant.domain.value,
            "selection_criteria": criteria.value,
            "overall_score": score,
            "key_factors": [],
            "strengths": [],
            "considerations": [],
        }

        if profile:
            # 主要要因
            if criteria == SelectionCriteria.PERFORMANCE:
                success_rate = profile.performance_history.get("success_rate", 0)
                reasoning["key_factors"].append(f"高い成功率: {success_rate:0.1%}")

            elif criteria == SelectionCriteria.QUALITY:
                avg_quality = (
                    sum(profile.quality_scores.values()) / len(profile.quality_scores)
                    if profile.quality_scores
                    else 0
                )
                reasoning["key_factors"].append(f"品質スコア: {avg_quality:0.1f}")

            elif criteria == SelectionCriteria.AVAILABILITY:
                reasoning["key_factors"].append(
                    f"可用性スコア: {profile.availability_score:0.2f}"
                )

            # 強み
            if profile.availability_score > 0.8:
                reasoning["strengths"].append("高い可用性")

            if profile.current_load < 0.3:
                reasoning["strengths"].append("低負荷状態")

            max_expertise = (
                max(profile.specialization_score.values())
                if profile.specialization_score
                else 0
            )
            if max_expertise > 0.8:
                reasoning["strengths"].append("高い専門性")

            # 考慮事項
            if profile.current_load > 0.7:
                reasoning["considerations"].append("現在の負荷が高め")

            if profile.cost_factor > 1.2:
                # Complex condition - consider breaking down
                reasoning["considerations"].append("相対的にコストが高い")

        return reasoning

    async def _record_selection_history(
        self,
        task_profile: TaskProfile,
        selection_result: SelectionResult,
        start_time: float,
    ):
        """選択履歴記録"""
        selection_time = time.time() - start_time

        history_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_profile.task_id,
            "task_type": task_profile.task_type.value,
            "selected_servant": selection_result.selected_servant.name,
            "selection_score": selection_result.selection_score,
            "confidence": selection_result.confidence,
            "criteria": selection_result.selection_criteria_used.value,
            "selection_time": selection_time,
            "alternatives_count": len(selection_result.alternative_servants),
        }

        self.selection_history.append(history_record)

        # 履歴サイズ制限
        if len(self.selection_history) > 1000:
            self.selection_history = self.selection_history[-800:]  # 最新800件を保持

    def _update_selection_stats(self, criteria: SelectionCriteria, score: float):
        """選択統計更新"""
        self.selection_stats["total_selections"] += 1
        self.selection_stats["criteria_usage"][criteria.value] += 1

        # 移動平均でスコア更新
        total = self.selection_stats["total_selections"]
        current_avg = self.selection_stats["average_selection_score"]
        self.selection_stats["average_selection_score"] = (
            current_avg * (total - 1) + score
        ) / total

    async def provide_feedback(
        self,
        task_id: str,
        servant_name: str,
        actual_performance: Dict[str, Any],
        success: bool,
    ):
        """フィードバック提供（学習用）"""
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "servant_name": servant_name,
            "actual_performance": actual_performance,
            "success": success,
        }

        self.performance_feedback[servant_name].append(feedback)

        # 統計更新
        if success:
            self.selection_stats["successful_selections"] += 1
        else:
            self.selection_stats["failed_selections"] += 1

        # モデル重み学習（簡易版）
        await self._update_model_weights(feedback)

    async def _update_model_weights(self, feedback: Dict[str, Any]):
        """モデル重み更新（機械学習）"""
        # 簡易的な学習アルゴリズム
        learning_rate = 0.01

        if feedback["success"]:
            # 成功時は現在の重みを強化
            for weight_key in self.model_weights:
                self.model_weights[weight_key] *= 1.0 + learning_rate
        else:
            # 失敗時は重みを調整
            for weight_key in self.model_weights:
                self.model_weights[weight_key] *= 1.0 - learning_rate

        # 正規化
        total_weight = sum(self.model_weights.values())
        for weight_key in self.model_weights:
            self.model_weights[weight_key] /= total_weight

    async def get_selection_statistics(self) -> Dict[str, Any]:
        """選択統計取得"""
        return {
            "selection_stats": self.selection_stats,
            "model_weights": self.model_weights,
            "recent_selections": self.selection_history[-10:],  # 最新10件
            "cache_status": {
                "cached_servants": len(self.servant_profiles_cache),
                "last_update": self.last_cache_update.isoformat(),
                "cache_valid": (datetime.now() - self.last_cache_update)
                < self.cache_expiry,
            },
        }

    # 便利メソッド
    async def quick_select(
        self,
        task_name: str,
        task_type: TaskType,
        required_capabilities: List[ServantCapability],
        priority: str = "medium",
    ) -> ElderServantBase:
        """クイック選択（簡易インターフェース）"""
        task_profile = TaskProfile(
            task_id=f"quick_{task_name}_{int(time.time())}",
            task_type=task_type,
            priority=priority,
            estimated_duration=0.0,
            required_capabilities=required_capabilities,
            preferred_domain=None,
            complexity_score=0.5,
            urgency_score=0.5 if priority == "medium" else 0.8,
            quality_requirement=0.7,
        )

        result = await self.select_optimal_servant(task_profile)
        return result.selected_servant

# グローバルセレクターインスタンス
_global_selector = None

def get_auto_selector() -> ServantAutoSelector:
    """グローバル自動選択インスタンスを取得"""
    global _global_selector
    if _global_selector is None:
        # Complex condition - consider breaking down
        _global_selector = ServantAutoSelector()
    return _global_selector
