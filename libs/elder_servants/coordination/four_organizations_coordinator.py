"""
4組織間協調システム

ドワーフ工房、RAGウィザーズ、エルフの森、インシデント騎士団の
4組織間協調を管理する統合システム。
Elder Flow連携、タスク分散、品質保証を提供。
"""

import asyncio
import logging
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


class CoordinationPattern(Enum):
    """協調パターン定義"""

    SEQUENTIAL = "sequential"  # 順次実行
    PARALLEL = "parallel"  # 並列実行
    PIPELINE = "pipeline"  # パイプライン実行
    HIERARCHICAL = "hierarchical"  # 階層実行


class TaskComplexity(Enum):
    """タスク複雑度"""

    SIMPLE = "simple"  # 単純タスク (1組織)
    MODERATE = "moderate"  # 中程度 (2-3組織)
    COMPLEX = "complex"  # 複雑 (3-4組織)
    EPIC = "epic"  # 史詩級 (全組織+多段階)


@dataclass
class OrganizationCapability:
    """組織能力定義"""

    domain: ServantDomain
    primary_functions: List[str]
    secondary_functions: List[str]
    collaboration_strength: Dict[ServantDomain, float]
    max_concurrent_tasks: int
    average_response_time: float


@dataclass
class CoordinationTask:
    """協調タスク定義"""

    task_id: str
    name: str
    description: str
    complexity: TaskComplexity
    pattern: CoordinationPattern
    required_organizations: List[ServantDomain]
    optional_organizations: List[ServantDomain]
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    priority: str = "medium"
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CoordinationResult:
    """協調実行結果"""

    task_id: str
    status: str  # success, partial, failed
    total_execution_time: float
    organization_results: Dict[ServantDomain, Any]
    quality_metrics: Dict[str, float]
    coordination_efficiency: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=datetime.now)


class OrganizationCoordinator(Protocol):
    """組織コーディネーターのプロトコル"""

    async def coordinate_task(self, task: CoordinationTask) -> CoordinationResult:
        """タスク協調実行"""
        ...

    async def assess_capacity(self) -> Dict[str, Any]:
        """組織能力評価"""
        ...


class FourOrganizationsCoordinator:
    """
    4組織間協調システム

    エルダーズギルドの4組織間の協調タスクを管理し、
    最適な実行パターンでタスクを分散実行する。
    """

    def __init__(self, registry: Optional[ServantRegistry] = None)self.logger = logging.getLogger("elder_servants.coordination")
    """初期化メソッド"""
        self.registry = registry or get_registry()

        # 組織能力定義
        self.organization_capabilities = self._initialize_organization_capabilities()

        # 協調パターンマッピング
        self.coordination_patterns = {
            TaskComplexity.SIMPLE: CoordinationPattern.SEQUENTIAL,
            TaskComplexity.MODERATE: CoordinationPattern.PARALLEL,
            TaskComplexity.COMPLEX: CoordinationPattern.PIPELINE,
            TaskComplexity.EPIC: CoordinationPattern.HIERARCHICAL,
        }

        # 実行統計
        self.execution_stats = {
            "total_coordinated_tasks": 0,
            "successful_coordinations": 0,
            "failed_coordinations": 0,
            "average_coordination_time": 0,
            "organization_workload": defaultdict(int),
        }

        # アクティブタスク管理
        self.active_tasks: Dict[str, CoordinationTask] = {}
        self.task_results: Dict[str, CoordinationResult] = {}

    def _initialize_organization_capabilities(
        self,
    ) -> Dict[ServantDomain, OrganizationCapability]:
        """組織能力の初期化"""
        return {
            ServantDomain.DWARF_WORKSHOP: OrganizationCapability(
                domain=ServantDomain.DWARF_WORKSHOP,
                primary_functions=[
                    "code_generation",
                    "testing",
                    "build_automation",
                    "deployment",
                    "refactoring",
                    "api_development",
                ],
                secondary_functions=["documentation", "integration", "ui_development"],
                collaboration_strength={
                    ServantDomain.RAG_WIZARDS: 0.9,
                    ServantDomain.ELF_FOREST: 0.8,
                    ServantDomain.INCIDENT_KNIGHTS: 0.7,
                },
                max_concurrent_tasks=12,
                average_response_time=2.5,
            ),
            ServantDomain.RAG_WIZARDS: OrganizationCapability(
                domain=ServantDomain.RAG_WIZARDS,
                primary_functions=[
                    "research",
                    "analysis",
                    "knowledge_extraction",
                    "pattern_recognition",
                    "data_mining",
                    "insight_generation",
                ],
                secondary_functions=[
                    "documentation",
                    "requirements_analysis",
                    "trend_prediction",
                ],
                collaboration_strength={
                    ServantDomain.DWARF_WORKSHOP: 0.9,
                    ServantDomain.ELF_FOREST: 0.8,
                    ServantDomain.INCIDENT_KNIGHTS: 0.8,
                },
                max_concurrent_tasks=8,
                average_response_time=3.0,
            ),
            ServantDomain.ELF_FOREST: OrganizationCapability(
                domain=ServantDomain.ELF_FOREST,
                primary_functions=[
                    "monitoring",
                    "performance_optimization",
                    "health_checking",
                    "resource_management",
                    "quality_assurance",
                    "maintenance",
                ],
                secondary_functions=["alerting", "log_analysis", "capacity_planning"],
                collaboration_strength={
                    ServantDomain.DWARF_WORKSHOP: 0.8,
                    ServantDomain.RAG_WIZARDS: 0.8,
                    ServantDomain.INCIDENT_KNIGHTS: 0.9,
                },
                max_concurrent_tasks=8,
                average_response_time=1.5,
            ),
            ServantDomain.INCIDENT_KNIGHTS: OrganizationCapability(
                domain=ServantDomain.INCIDENT_KNIGHTS,
                primary_functions=[
                    "security_scanning",
                    "incident_response",
                    "threat_detection",
                    "vulnerability_assessment",
                    "crisis_management",
                    "emergency_repair",
                ],
                secondary_functions=["compliance_checking", "audit", "risk_assessment"],
                collaboration_strength={
                    ServantDomain.ELF_FOREST: 0.9,
                    ServantDomain.DWARF_WORKSHOP: 0.7,
                    ServantDomain.RAG_WIZARDS: 0.8,
                },
                max_concurrent_tasks=4,
                average_response_time=1.0,
            ),
        }

    async def coordinate_task(self, task: CoordinationTask) -> CoordinationResult:
        """
        協調タスクの実行

        タスクの複雑度と要求組織に基づいて最適な協調パターンを選択し、
        組織間の協調実行を管理する。
        """
        start_time = time.time()
        self.logger.info(f"Starting coordination for task: {task.task_id}")

        # タスクをアクティブリストに追加
        self.active_tasks[task.task_id] = task

        try:
            # 組織能力の事前チェック
            capacity_check = await self._check_organization_capacity(task)
            if not capacity_check["can_execute"]:
                return self._create_failed_result(
                    task,
                    f"Insufficient capacity: {capacity_check['reason']}",
                    start_time,
                )

            # 協調パターン決定
            coordination_pattern = self._determine_coordination_pattern(task)

            # 実行計画作成
            execution_plan = await self._create_execution_plan(
                task, coordination_pattern
            )

            # 協調実行
            if coordination_pattern == CoordinationPattern.SEQUENTIAL:
                result = await self._execute_sequential(task, execution_plan)
            elif coordination_pattern == CoordinationPattern.PARALLEL:
                result = await self._execute_parallel(task, execution_plan)
            elif coordination_pattern == CoordinationPattern.PIPELINE:
                result = await self._execute_pipeline(task, execution_plan)
            elif coordination_pattern == CoordinationPattern.HIERARCHICAL:
                result = await self._execute_hierarchical(task, execution_plan)
            else:
                raise ValueError(
                    f"Unknown coordination pattern: {coordination_pattern}"
                )

            # 統計更新
            execution_time = time.time() - start_time
            self._update_execution_stats(task, result, execution_time)

            # 結果保存
            self.task_results[task.task_id] = result

            self.logger.info(
                f"Coordination completed for task: {task.task_id}, status: {result.status}"
            )
            return result

        except Exception as e:
            error_msg = f"Coordination failed for task {task.task_id}: {str(e)}"
            self.logger.error(error_msg)
            return self._create_failed_result(task, error_msg, start_time)

        finally:
            # アクティブタスクから削除
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]

    async def _check_organization_capacity(
        self, task: CoordinationTask
    ) -> Dict[str, Any]:
        """組織能力チェック"""
        capacity_status = {"can_execute": True, "reason": ""}

        for domain in task.required_organizations:
            org_capability = self.organization_capabilities.get(domain)
            if not org_capability:
                capacity_status["can_execute"] = False
                capacity_status["reason"] = f"Organization {domain.value} not available"
                break

            # 現在の負荷チェック
            current_workload = self.execution_stats["organization_workload"][domain]
            if current_workload >= org_capability.max_concurrent_tasks:
                capacity_status["can_execute"] = False
                capacity_status["reason"] = (
                    f"Organization {domain.value} at max capacity"
                )
                break

            # サーバント可用性チェック
            available_servants = self.registry.find_by_domain(domain)
            if not available_servants:
                capacity_status["can_execute"] = False
                capacity_status["reason"] = f"No servants available in {domain.value}"
                break

        return capacity_status

    def _determine_coordination_pattern(
        self, task: CoordinationTask
    ) -> CoordinationPattern:
        """協調パターンの決定"""
        # 明示的にパターンが指定されている場合
        if hasattr(task, "pattern") and task.pattern:
            return task.pattern

        # 複雑度に基づく自動決定
        return self.coordination_patterns.get(
            task.complexity, CoordinationPattern.SEQUENTIAL
        )

    async def _create_execution_plan(
        self, task: CoordinationTask, pattern: CoordinationPattern
    ) -> Dict[str, Any]:
        """実行計画作成"""
        plan = {
            "task_id": task.task_id,
            "pattern": pattern,
            "phases": [],
            "dependencies": task.dependencies,
            "timeout": task.timeout_seconds,
        }

        if pattern == CoordinationPattern.SEQUENTIAL:
            # 順次実行: 組織を順番に実行
            for i, domain in enumerate(task.required_organizations):
                plan["phases"].append(
                    {
                        "phase": i + 1,
                        "organizations": [domain],
                        "depends_on": [i] if i > 0 else [],
                    }
                )

        elif pattern == CoordinationPattern.PARALLEL:
            # 並列実行: 全組織を同時実行
            plan["phases"].append(
                {
                    "phase": 1,
                    "organizations": task.required_organizations,
                    "depends_on": [],
                }
            )

        elif pattern == CoordinationPattern.PIPELINE:
            # パイプライン実行: 依存関係に基づく段階実行
            # 基本的なパイプライン順序: ウィザーズ → ドワーフ → エルフ → 騎士団
            pipeline_order = [
                ServantDomain.RAG_WIZARDS,
                ServantDomain.DWARF_WORKSHOP,
                ServantDomain.ELF_FOREST,
                ServantDomain.INCIDENT_KNIGHTS,
            ]

            for i, domain in enumerate(pipeline_order):
                if not (domain in task.required_organizations):
                    continue  # Early return to reduce nesting
                # Reduced nesting - original condition satisfied
                if domain in task.required_organizations:
                    plan["phases"].append(
                        {
                            "phase": i + 1,
                            "organizations": [domain],
                            "depends_on": [i] if i > 0 else [],
                        }
                    )

        elif pattern == CoordinationPattern.HIERARCHICAL:
            # 階層実行: 調査→実装→検証→保守の階層構造
            plan["phases"] = [
                {
                    "phase": 1,
                    "name": "research_phase",
                    "organizations": [ServantDomain.RAG_WIZARDS],
                    "depends_on": [],
                },
                {
                    "phase": 2,
                    "name": "implementation_phase",
                    "organizations": [ServantDomain.DWARF_WORKSHOP],
                    "depends_on": [1],
                },
                {
                    "phase": 3,
                    "name": "verification_phase",
                    "organizations": [
                        ServantDomain.ELF_FOREST,
                        ServantDomain.INCIDENT_KNIGHTS,
                    ],
                    "depends_on": [2],
                },
            ]

        return plan

    async def _execute_sequential(
        self, task: CoordinationTask, plan: Dict[str, Any]
    ) -> CoordinationResult:
        """順次実行"""
        organization_results = {}
        errors = []
        warnings = []

        # 繰り返し処理
        for phase in plan["phases"]:
            for domain in phase["organizations"]:
                try:
                    result = await self._execute_organization_task(task, domain)
                    organization_results[domain] = result

                    if result.status == "failed":
                        errors.append(
                            f"Organization {domain.value} failed: {result.errors}"
                        )
                    elif result.warnings:
                        warnings.extend(result.warnings)

                except Exception as e:
                    error_msg = f"Error in {domain.value}: {str(e)}"
                    errors.append(error_msg)
                    organization_results[domain] = {
                        "status": "error",
                        "error": error_msg,
                    }

        # 全体ステータス決定
        if errors:
            overall_status = (
                "failed" if len(errors) >= len(organization_results) // 2 else "partial"
            )
        else:
            overall_status = "success"

        return CoordinationResult(
            task_id=task.task_id,
            status=overall_status,
            total_execution_time=0,  # 後で計算
            organization_results=organization_results,
            quality_metrics=self._calculate_quality_metrics(organization_results),
            coordination_efficiency=self._calculate_coordination_efficiency(
                organization_results
            ),
            errors=errors,
            warnings=warnings,
        )

    async def _execute_parallel(
        self, task: CoordinationTask, plan: Dict[str, Any]
    ) -> CoordinationResult:
        """並列実行"""
        organization_results = {}
        errors = []
        warnings = []

        # 全組織を並列実行
        tasks_to_execute = []
        for domain in task.required_organizations:
            tasks_to_execute.append(self._execute_organization_task(task, domain))

        # 並列実行
        results = await asyncio.gather(*tasks_to_execute, return_exceptions=True)

        # 結果処理
        for i, result in enumerate(results):
            domain = task.required_organizations[i]

            if isinstance(result, Exception):
                error_msg = f"Error in {domain.value}: {str(result)}"
                errors.append(error_msg)
                organization_results[domain] = {"status": "error", "error": error_msg}
            else:
                organization_results[domain] = result
                if result.status == "failed":
                    errors.extend(result.errors)
                if result.warnings:
                    warnings.extend(result.warnings)

        # 全体ステータス決定
        successful_orgs = sum(
            1
            for result in organization_results.values()
            if isinstance(result, ServantResponse) and result.status == "success"
        )

        if successful_orgs == len(organization_results):
            overall_status = "success"
        elif successful_orgs >= len(organization_results) // 2:
            overall_status = "partial"
        else:
            overall_status = "failed"

        return CoordinationResult(
            task_id=task.task_id,
            status=overall_status,
            total_execution_time=0,
            organization_results=organization_results,
            quality_metrics=self._calculate_quality_metrics(organization_results),
            coordination_efficiency=self._calculate_coordination_efficiency(
                organization_results
            ),
            errors=errors,
            warnings=warnings,
        )

    async def _execute_pipeline(
        self, task: CoordinationTask, plan: Dict[str, Any]
    ) -> CoordinationResult:
        """パイプライン実行"""
        organization_results = {}
        errors = []
        warnings = []
        pipeline_context = task.context.copy()

        # フェーズごとに順次実行し、前フェーズの結果を次に渡す
        for phase in plan["phases"]:
            for domain in phase["organizations"]:
                try:
                    # 前フェーズの結果をコンテキストに追加
                    enhanced_task = CoordinationTask(
                        task_id=f"{task.task_id}_phase_{phase['phase']}",
                        name=task.name,
                        description=task.description,
                        complexity=task.complexity,
                        pattern=task.pattern,
                        required_organizations=[domain],
                        optional_organizations=[],
                        context={
                            **pipeline_context,
                            "pipeline_data": organization_results,
                        },
                    )

                    result = await self._execute_organization_task(
                        enhanced_task, domain
                    )
                    organization_results[domain] = result

                    # 成功した場合は結果をパイプラインコンテキストに追加
                    if result.status == "success":
                        pipeline_context[f"{domain.value}_result"] = result.data
                    else:
                        errors.append(
                            f"Pipeline stage {domain.value} failed: {result.errors}"
                        )
                        # パイプライン中断判定
                        if not (len(errors) > 0:  # 厳密なパイプライン):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if len(errors) > 0:  # 厳密なパイプライン
                            break

                except Exception as e:
                    error_msg = f"Pipeline error in {domain.value}: {str(e)}"
                    errors.append(error_msg)
                    organization_results[domain] = {
                        "status": "error",
                        "error": error_msg,
                    }
                    break  # パイプライン中断

        # パイプライン成功判定
        if errors:
            overall_status = "failed"
        else:
            overall_status = "success"

        return CoordinationResult(
            task_id=task.task_id,
            status=overall_status,
            total_execution_time=0,
            organization_results=organization_results,
            quality_metrics=self._calculate_quality_metrics(organization_results),
            coordination_efficiency=self._calculate_coordination_efficiency(
                organization_results
            ),
            errors=errors,
            warnings=warnings,
        )

    async def _execute_hierarchical(
        self, task: CoordinationTask, plan: Dict[str, Any]
    ) -> CoordinationResult:
        """階層実行"""
        organization_results = {}
        errors = []
        warnings = []
        hierarchical_context = task.context.copy()

        # 各階層フェーズを実行
        for phase in plan["phases"]:
            phase_name = phase.get("name", f"phase_{phase['phase']}")
            phase_results = {}

            # フェーズ内の組織を並列実行
            if len(phase["organizations"]) > 1:
                tasks_to_execute = []
                for domain in phase["organizations"]:
                    enhanced_task = CoordinationTask(
                        task_id=f"{task.task_id}_{phase_name}_{domain.value}",
                        name=f"{task.name} - {phase_name}",
                        description=task.description,
                        complexity=task.complexity,
                        pattern=task.pattern,
                        required_organizations=[domain],
                        optional_organizations=[],
                        context={**hierarchical_context, "phase": phase_name},
                    )
                    tasks_to_execute.append(
                        self._execute_organization_task(enhanced_task, domain)
                    )

                # 並列実行
                results = await asyncio.gather(
                    *tasks_to_execute, return_exceptions=True
                )

                # 結果処理
                for i, result in enumerate(results):
                    domain = phase["organizations"][i]
                    if isinstance(result, Exception):
                        error_msg = (
                            f"Hierarchical error in {domain.value}: {str(result)}"
                        )
                        errors.append(error_msg)
                        phase_results[domain] = {"status": "error", "error": error_msg}
                    else:
                        phase_results[domain] = result
                        if not (result.status == "success"):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if result.status == "success":
                            hierarchical_context[
                                f"{domain.value}_phase_{phase_name}"
                            ] = result.data
            else:
                # 単一組織の場合
                domain = phase["organizations"][0]
                enhanced_task = CoordinationTask(
                    task_id=f"{task.task_id}_{phase_name}_{domain.value}",
                    name=f"{task.name} - {phase_name}",
                    description=task.description,
                    complexity=task.complexity,
                    pattern=task.pattern,
                    required_organizations=[domain],
                    optional_organizations=[],
                    context={**hierarchical_context, "phase": phase_name},
                )

                try:
                    result = await self._execute_organization_task(
                        enhanced_task, domain
                    )
                    phase_results[domain] = result
                    if result.status == "success":
                        hierarchical_context[f"{domain.value}_phase_{phase_name}"] = (
                            result.data
                        )
                    else:
                        errors.extend(result.errors)
                except Exception as e:
                    error_msg = f"Hierarchical error in {domain.value}: {str(e)}"
                    errors.append(error_msg)
                    phase_results[domain] = {"status": "error", "error": error_msg}

            # フェーズ結果を全体結果に統合
            organization_results.update(phase_results)

            # フェーズ失敗時の継続判定
            phase_success = all(
                isinstance(result, ServantResponse) and result.status == "success"
                for result in phase_results.values()
            )

            if not phase_success and phase_name in ["research_phase"]:
                # 重要フェーズ失敗時は階層実行を中止
                errors.append(
                    f"Critical phase {phase_name} failed, stopping hierarchical execution"
                )
                break

        # 階層実行成功判定
        if errors:
            overall_status = "failed" if "Critical phase" in str(errors) else "partial"
        else:
            overall_status = "success"

        return CoordinationResult(
            task_id=task.task_id,
            status=overall_status,
            total_execution_time=0,
            organization_results=organization_results,
            quality_metrics=self._calculate_quality_metrics(organization_results),
            coordination_efficiency=self._calculate_coordination_efficiency(
                organization_results
            ),
            errors=errors,
            warnings=warnings,
        )

    async def _execute_organization_task(
        self, task: CoordinationTask, domain: ServantDomain
    ) -> ServantResponse:
        """組織別タスク実行"""
        # 該当ドメインのサーバントを取得
        servants = self.registry.find_by_domain(domain)
        if not servants:
            raise ValueError(f"No servants available for domain {domain.value}")

        # 最適なサーバントを選択（負荷分散）
        selected_servant = self._select_optimal_servant(servants, task)

        # リクエスト作成
        servant_request = ServantRequest(
            task_id=f"{task.task_id}_{domain.value}",
            task_type=task.name,
            priority=task.priority,
            data={
                "coordination_task": True,
                "task_context": task.context,
                "organization_role": domain.value,
            },
            context=task.context,
        )

        # 組織ワークロード更新
        self.execution_stats["organization_workload"][domain] += 1

        try:
            # サーバント実行
            response = await selected_servant.execute_with_quality_gate(servant_request)
            return response

        finally:
            # ワークロード減算
            self.execution_stats["organization_workload"][domain] = max(
                0, self.execution_stats["organization_workload"][domain] - 1
            )

    def _select_optimal_servant(
        self, servants: List[ElderServantBase], task: CoordinationTask
    ) -> ElderServantBase:
        """最適サーバント選択"""
        if len(servants) == 1:
            return servants[0]

        # 負荷分散ベースの選択
        selected_servant = min(
            servants, key=lambda s: s.get_metrics()["tasks_processed"]
        )
        return selected_servant

    def _calculate_quality_metrics(
        self, organization_results: Dict[ServantDomain, Any]
    ) -> Dict[str, float]:
        """品質メトリクス計算"""
        total_quality = 0
        valid_results = 0

        for domain, result in organization_results.items():
            if isinstance(result, ServantResponse) and result.status == "success":
                # 仮の品質スコア計算
                quality_score = 90.0  # ベーススコア
                if not result.errors:
                    quality_score += 5.0
                if not result.warnings:
                    quality_score += 3.0

                total_quality += quality_score
                valid_results += 1

        average_quality = total_quality / valid_results if valid_results > 0 else 0

        return {
            "average_quality": average_quality,
            "organization_coverage": len(organization_results),
            "success_rate": (
                valid_results / len(organization_results) if organization_results else 0
            ),
        }

    def _calculate_coordination_efficiency(
        self, organization_results: Dict[ServantDomain, Any]
    ) -> float:
        """協調効率計算"""
        successful_organizations = sum(
            1
            for result in organization_results.values()
            if isinstance(result, ServantResponse) and result.status == "success"
        )

        total_organizations = len(organization_results)
        base_efficiency = (
            successful_organizations / total_organizations
            if total_organizations > 0
            else 0
        )

        # 組織間協調ボーナス
        if successful_organizations >= 3:
            base_efficiency *= 1.1  # 3組織以上の協調ボーナス
        if successful_organizations == total_organizations:
            base_efficiency *= 1.05  # 完全協調ボーナス

        return min(1.0, base_efficiency)

    def _create_failed_result(
        self, task: CoordinationTask, error_message: str, start_time: float
    ) -> CoordinationResult:
        """失敗結果作成"""
        return CoordinationResult(
            task_id=task.task_id,
            status="failed",
            total_execution_time=time.time() - start_time,
            organization_results={},
            quality_metrics={
                "average_quality": 0,
                "organization_coverage": 0,
                "success_rate": 0,
            },
            coordination_efficiency=0.0,
            errors=[error_message],
        )

    def _update_execution_stats(
        self, task: CoordinationTask, result: CoordinationResult, execution_time: float
    ):
        """実行統計更新"""
        self.execution_stats["total_coordinated_tasks"] += 1

        if result.status == "success":
            self.execution_stats["successful_coordinations"] += 1
        else:
            self.execution_stats["failed_coordinations"] += 1

        # 移動平均で実行時間更新
        total_tasks = self.execution_stats["total_coordinated_tasks"]
        current_avg = self.execution_stats["average_coordination_time"]
        self.execution_stats["average_coordination_time"] = (
            current_avg * (total_tasks - 1) + execution_time
        ) / total_tasks

    async def get_coordination_status(self) -> Dict[str, Any]:
        """協調システム状態取得"""
        return {
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.task_results),
            "execution_stats": self.execution_stats,
            "organization_workloads": dict(
                self.execution_stats["organization_workload"]
            ),
            "system_health": await self._assess_system_health(),
        }

    async def _assess_system_health(self) -> Dict[str, Any]:
        """システム健全性評価"""
        health_status = {
            "overall_healthy": True,
            "organization_health": {},
            "issues": [],
        }

        for domain, capability in self.organization_capabilities.items():
            servants = self.registry.find_by_domain(domain)
            workload = self.execution_stats["organization_workload"][domain]

            org_health = {
                "available_servants": len(servants),
                "current_workload": workload,
                "max_capacity": capability.max_concurrent_tasks,
                "utilization_rate": workload / capability.max_concurrent_tasks,
                "healthy": True,
            }

            # 健全性チェック
            if len(servants) == 0:
                org_health["healthy"] = False
                health_status["issues"].append(
                    f"No servants available in {domain.value}"
                )
                health_status["overall_healthy"] = False

            if org_health["utilization_rate"] > 0.9:
                health_status["issues"].append(
                    f"High utilization in {domain.value}: {org_health['utilization_rate']:0.1%}"
                )

            health_status["organization_health"][domain.value] = org_health

        return health_status

    # 便利メソッド
    async def create_simple_task(
        self, name: str, primary_domain: ServantDomain, description: str = ""
    ) -> CoordinationTask:
        """簡単なタスク作成"""
        return CoordinationTask(
            task_id=f"simple_{name}_{int(time.time())}",
            name=name,
            description=description or f"Simple task: {name}",
            complexity=TaskComplexity.SIMPLE,
            pattern=CoordinationPattern.SEQUENTIAL,
            required_organizations=[primary_domain],
            optional_organizations=[],
        )

    async def create_collaboration_task(
        self, name: str, organizations: List[ServantDomain], description: str = ""
    ) -> CoordinationTask:
        """協調タスク作成"""
        complexity = (
            TaskComplexity.MODERATE
            if len(organizations) <= 2
            else TaskComplexity.COMPLEX
        )

        return CoordinationTask(
            task_id=f"collab_{name}_{int(time.time())}",
            name=name,
            description=description or f"Collaboration task: {name}",
            complexity=complexity,
            pattern=CoordinationPattern.PARALLEL,
            required_organizations=organizations,
            optional_organizations=[],
        )


# グローバルコーディネーターインスタンス
_global_coordinator = None


def get_coordinator() -> FourOrganizationsCoordinator:
    """グローバルコーディネーターインスタンスを取得"""
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = FourOrganizationsCoordinator()
    return _global_coordinator
