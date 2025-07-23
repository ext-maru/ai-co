"""
失敗時自動フォールバックシステム

Elder Servants、Elder Flow、組織間協調における失敗を自動検知し、
適切な代替手段を自動実行する耐障害性システム。
"""

import asyncio
import logging
import time
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from ..base.elder_servant_base import (
    ElderServantBase,
    ServantCapability,
    ServantDomain,
    ServantRequest,
    ServantResponse,
)
from ..coordination.four_organizations_coordinator import (
    CoordinationResult,
    CoordinationTask,
    FourOrganizationsCoordinator,
)
from ..load_balancing.load_balancer import LoadBalancer, get_load_balancer
from ..registry.servant_registry import ServantRegistry, get_registry


class FailureType(Enum):
    """失敗タイプ"""

    SERVANT_UNAVAILABLE = "servant_unavailable"  # サーバント利用不可
    SERVANT_TIMEOUT = "servant_timeout"  # サーバントタイムアウト
    SERVANT_ERROR = "servant_error"  # サーバント実行エラー
    COORDINATION_FAILURE = "coordination_failure"  # 協調失敗
    ELDER_FLOW_FAILURE = "elder_flow_failure"  # Elder Flow失敗
    NETWORK_ERROR = "network_error"  # ネットワークエラー
    RESOURCE_EXHAUSTED = "resource_exhausted"  # リソース枯渇
    QUALITY_GATE_FAILURE = "quality_gate_failure"  # 品質ゲート失敗
    DEPENDENCY_FAILURE = "dependency_failure"  # 依存関係失敗


class FallbackStrategy(Enum):
    """フォールバック戦略"""

    RETRY = "retry"  # リトライ
    ALTERNATIVE_SERVANT = "alternative_servant"  # 代替サーバント
    DEGRADED_MODE = "degraded_mode"  # 劣化モード
    EMERGENCY_BYPASS = "emergency_bypass"  # 緊急バイパス
    CIRCUIT_BREAKER = "circuit_breaker"  # サーキットブレーカー
    GRACEFUL_DEGRADATION = "graceful_degradation"  # 段階的劣化
    ROLLBACK = "rollback"  # ロールバック
    ESCALATION = "escalation"  # エスカレーション


class RecoveryAction(Enum):
    """復旧アクション"""

    AUTOMATIC_RETRY = "automatic_retry"  # 自動リトライ
    SWITCH_TO_BACKUP = "switch_to_backup"  # バックアップに切り替え
    REDUCE_QUALITY = "reduce_quality"  # 品質要求下げ
    SKIP_NON_CRITICAL = "skip_non_critical"  # 非重要処理スキップ
    NOTIFY_ADMIN = "notify_admin"  # 管理者通知
    EMERGENCY_STOP = "emergency_stop"  # 緊急停止


@dataclass
class FailureContext:
    """失敗コンテキスト"""

    failure_id: str
    failure_type: FailureType
    failed_component: str  # サーバント名、フロー名など
    original_request: Dict[str, Any]
    error_details: Dict[str, Any]
    timestamp: datetime
    retry_count: int = 0
    previous_attempts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FallbackPlan:
    """フォールバック計画"""

    plan_id: str
    failure_context: FailureContext
    strategy: FallbackStrategy
    recovery_actions: List[RecoveryAction]
    alternative_options: List[Dict[str, Any]]
    estimated_recovery_time: float
    success_probability: float
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FallbackResult:
    """フォールバック結果"""

    fallback_id: str
    original_failure: FailureContext
    executed_plan: FallbackPlan
    final_status: str  # success, partial, failed
    recovery_time: float
    alternative_used: Optional[str]
    lessons_learned: List[str]
    completed_at: datetime = field(default_factory=datetime.now)


class AutoFallbackSystem:
    """
    自動フォールバックシステム

    Elder Servants エコシステム全体の耐障害性を提供し、
    失敗発生時の自動復旧とサービス継続性を保証する。
    """

    def __init__(
        self,
        registry: Optional[ServantRegistry] = None,
        coordinator: Optional[FourOrganizationsCoordinator] = None,
        load_balancer: Optional[LoadBalancer] = None,
    ):
        self.logger = logging.getLogger("elder_servants.auto_fallback")
        self.registry = registry or get_registry()
        self.coordinator = coordinator or FourOrganizationsCoordinator()
        self.load_balancer = load_balancer or get_load_balancer()

        # 失敗検知と履歴
        self.active_failures: Dict[str, FailureContext] = {}
        self.failure_history: deque = deque(maxlen=1000)
        self.fallback_history: deque = deque(maxlen=500)

        # フォールバック設定
        self.fallback_config = {
            "max_retry_attempts": 3,
            "retry_delays": [1.0, 2.0, 5.0],  # 指数バックオフ
            "circuit_breaker_threshold": 5,
            "circuit_breaker_timeout": 60.0,
            "emergency_timeout": 30.0,
            "quality_degradation_steps": [0.9, 0.8, 0.7, 0.5],
        }

        # サーキットブレーカー状態
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # 統計情報
        self.fallback_stats = {
            "total_failures_detected": 0,
            "successful_fallbacks": 0,
            "failed_fallbacks": 0,
            "automatic_recoveries": 0,
            "escalations_required": 0,
            "average_recovery_time": 0.0,
            "failure_types": defaultdict(int),
            "recovery_strategies": defaultdict(int),
        }

        # アラートシステム
        self.alert_callbacks: List[Callable] = []

        # パフォーマンス監視
        self.performance_monitor = PerformanceMonitor()

    async def handle_failure(self, failure_context: FailureContext) -> FallbackResult:
        """
        失敗処理メインエントリーポイント

        Args:
            failure_context: 失敗コンテキスト

        Returns:
            フォールバック結果
        """
        start_time = time.time()
        self.logger.error(
            f"Handling failure: {failure_context.failure_id} - {failure_context.failure_type.value}"
        )

        try:
            # 失敗記録
            self._record_failure(failure_context)

            # サーキットブレーカーチェック
            if self._is_circuit_open(failure_context.failed_component, encoding="utf-8"):
                return await self._handle_circuit_breaker_open(failure_context, encoding="utf-8")

            # フォールバック計画生成
            fallback_plan = await self._generate_fallback_plan(failure_context)

            # フォールバック実行
            result = await self._execute_fallback_plan(fallback_plan)

            # 統計更新
            self._update_fallback_stats(result, time.time() - start_time)

            # 学習データ保存
            await self._learn_from_fallback(result)

            return result

        except Exception as e:
            # Handle specific exception case
            self.logger.critical(f"Fallback system failure: {str(e)}")
            # 緊急フォールバック
            return await self._emergency_fallback(failure_context, str(e))

    async def _generate_fallback_plan(
        self, failure_context: FailureContext
    ) -> FallbackPlan:
        """フォールバック計画生成"""
        strategy = await self._determine_fallback_strategy(failure_context)
        recovery_actions = await self._plan_recovery_actions(failure_context, strategy)
        alternative_options = await self._identify_alternatives(failure_context)

        # 成功確率と復旧時間推定
        success_probability = self._estimate_success_probability(
            failure_context, strategy
        )
        recovery_time = self._estimate_recovery_time(failure_context, strategy)

        plan = FallbackPlan(
            plan_id=f"fallback_{failure_context.failure_id}_{int(time.time())}",
            failure_context=failure_context,
            strategy=strategy,
            recovery_actions=recovery_actions,
            alternative_options=alternative_options,
            estimated_recovery_time=recovery_time,
            success_probability=success_probability,
        )

        self.logger.info(
            f"Generated fallback plan {plan.plan_id} with strategy {strategy.value}"
        )
        return plan

    async def _determine_fallback_strategy(
        self, failure_context: FailureContext
    ) -> FallbackStrategy:
        """フォールバック戦略決定"""
        failure_type = failure_context.failure_type
        retry_count = failure_context.retry_count

        # 失敗タイプとリトライ回数に基づく戦略選択
        if retry_count < self.fallback_config["max_retry_attempts"]:
            if failure_type in [FailureType.SERVANT_TIMEOUT, FailureType.NETWORK_ERROR]:
                return FallbackStrategy.RETRY
            elif failure_type == FailureType.SERVANT_UNAVAILABLE:
                return FallbackStrategy.ALTERNATIVE_SERVANT

        # 高次フォールバック戦略
        if failure_type == FailureType.COORDINATION_FAILURE:
            return FallbackStrategy.DEGRADED_MODE
        elif failure_type == FailureType.QUALITY_GATE_FAILURE:
            return FallbackStrategy.GRACEFUL_DEGRADATION
        elif failure_type == FailureType.RESOURCE_EXHAUSTED:
            return FallbackStrategy.CIRCUIT_BREAKER
        else:
            return FallbackStrategy.EMERGENCY_BYPASS

    async def _plan_recovery_actions(
        self, failure_context: FailureContext, strategy: FallbackStrategy
    ) -> List[RecoveryAction]:
        """復旧アクション計画"""
        actions = []

        if strategy == FallbackStrategy.RETRY:
            actions.append(RecoveryAction.AUTOMATIC_RETRY)

        elif strategy == FallbackStrategy.ALTERNATIVE_SERVANT:
            actions.extend(
                [RecoveryAction.SWITCH_TO_BACKUP, RecoveryAction.AUTOMATIC_RETRY]
            )

        elif strategy == FallbackStrategy.DEGRADED_MODE:
            actions.extend(
                [
                    RecoveryAction.REDUCE_QUALITY,
                    RecoveryAction.SKIP_NON_CRITICAL,
                    RecoveryAction.SWITCH_TO_BACKUP,
                ]
            )

        elif strategy == FallbackStrategy.GRACEFUL_DEGRADATION:
            actions.extend(
                [RecoveryAction.REDUCE_QUALITY, RecoveryAction.AUTOMATIC_RETRY]
            )

        elif strategy == FallbackStrategy.CIRCUIT_BREAKER:
            actions.extend(
                [RecoveryAction.SWITCH_TO_BACKUP, RecoveryAction.NOTIFY_ADMIN]
            )

        elif strategy == FallbackStrategy.EMERGENCY_BYPASS:
            actions.extend(
                [RecoveryAction.SKIP_NON_CRITICAL, RecoveryAction.NOTIFY_ADMIN]
            )

        # 重大失敗の場合は管理者通知を追加
        if failure_context.retry_count >= 2:
            if RecoveryAction.NOTIFY_ADMIN not in actions:
                actions.append(RecoveryAction.NOTIFY_ADMIN)

        return actions

    async def _identify_alternatives(
        self, failure_context: FailureContext
    ) -> List[Dict[str, Any]]:
        """代替選択肢特定"""
        alternatives = []

        # 失敗したサーバントの代替を検索
        if failure_context.failure_type in [
            FailureType.SERVANT_UNAVAILABLE,
            FailureType.SERVANT_ERROR,
            FailureType.SERVANT_TIMEOUT,
        ]:
            alternatives.extend(await self._find_alternative_servants(failure_context))

        # 協調失敗の場合の代替戦略
        elif failure_context.failure_type == FailureType.COORDINATION_FAILURE:
            alternatives.extend(
                await self._find_alternative_coordination_strategies(failure_context)
            )

        # Elder Flow失敗の場合の代替フロー
        elif failure_context.failure_type == FailureType.ELDER_FLOW_FAILURE:
            alternatives.extend(await self._find_alternative_flows(failure_context))

        return alternatives

    async def _find_alternative_servants(
        self, failure_context: FailureContext
    ) -> List[Dict[str, Any]]:
        """代替サーバント検索"""
        alternatives = []
        failed_servant_name = failure_context.failed_component

        try:
            # 失敗したサーバントの情報取得
            failed_servant = self.registry.get_servant(failed_servant_name)
            if not failed_servant:
                return alternatives

            # 同じドメインの他のサーバント検索
            domain_servants = self.registry.find_by_domain(failed_servant.domain)

            for servant in domain_servants:
                if servant.name != failed_servant_name:
                    # 健全性チェック
                    if not self._is_circuit_open(servant.name, encoding="utf-8"):
                        alternatives.append(
                            {
                                "type": "alternative_servant",
                                "servant_name": servant.name,
                                "domain": servant.domain.value,
                                "capabilities": [
                                    cap.value for cap in servant.get_capabilities()
                                ],
                                "estimated_success_rate": self._estimate_servant_success_rate(
                                    servant
                                ),
                            }
                        )

            # 他のドメインで同じ能力を持つサーバント検索
            if failed_servant:
                capabilities = failed_servant.get_capabilities()
                for capability in capabilities:
                    # Process each item in collection
                    cross_domain_servants = self.registry.find_by_capability(capability)

                    for servant in cross_domain_servants:
                        # Process each item in collection
                        if (
                            servant.name != failed_servant_name
                            and servant.domain != failed_servant.domain
                            and not self._is_circuit_open(servant.name, encoding="utf-8")
                        ):
                            alternatives.append(
                                {
                                    "type": "cross_domain_servant",
                                    "servant_name": servant.name,
                                    "domain": servant.domain.value,
                                    "capabilities": [
                                        cap.value for cap in servant.get_capabilities()
                                    ],
                                    "estimated_success_rate": self._estimate_servant_success_rate(
                                        servant
                                    )
                                    * 0.8,  # 削減
                                }
                            )

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Error finding alternative servants: {str(e)}")

        return alternatives

    async def _find_alternative_coordination_strategies(
        self, failure_context: FailureContext
    ) -> List[Dict[str, Any]]:
        """代替協調戦略検索"""
        alternatives = []

        # 段階的劣化戦略
        alternatives.append(
            {
                "type": "degraded_coordination",
                "description": "重要組織のみでの協調実行",
                "reduced_organizations": ["dwarf_workshop", "elf_forest"],
                "estimated_success_rate": 0.7,
            }
        )

        # 単一組織フォールバック
        alternatives.append(
            {
                "type": "single_organization",
                "description": "最も適した単一組織での実行",
                "primary_organization": "dwarf_workshop",
                "estimated_success_rate": 0.6,
            }
        )

        # 緊急モード
        alternatives.append(
            {
                "type": "emergency_mode",
                "description": "緊急対応騎士団による迅速処理",
                "emergency_organization": "incident_knights",
                "estimated_success_rate": 0.8,
            }
        )

        return alternatives

    async def _find_alternative_flows(
        self, failure_context: FailureContext
    ) -> List[Dict[str, Any]]:
        """代替フロー検索"""
        alternatives = []

        # 簡略化フロー
        alternatives.append(
            {
                "type": "simplified_flow",
                "description": "重要フェーズのみの簡略化実行",
                "phases": ["servant_execution", "quality_gate"],
                "estimated_success_rate": 0.75,
            }
        )

        # 手動モード
        alternatives.append(
            {
                "type": "manual_mode",
                "description": "手動確認付きフロー実行",
                "manual_checkpoints": True,
                "estimated_success_rate": 0.9,
            }
        )

        return alternatives

    async def _execute_fallback_plan(self, plan: FallbackPlan) -> FallbackResult:
        """フォールバック計画実行"""
        start_time = time.time()
        failure_context = plan.failure_context

        self.logger.info(
            f"Executing fallback plan {plan.plan_id} with strategy {plan.strategy.value}"
        )

        try:
            result = None
            alternative_used = None

            # 戦略別実行
            if plan.strategy == FallbackStrategy.RETRY:
                result = await self._execute_retry(plan)

            elif plan.strategy == FallbackStrategy.ALTERNATIVE_SERVANT:
                result = await self._execute_alternative_servant(plan)
                alternative_used = "alternative_servant"

            elif plan.strategy == FallbackStrategy.DEGRADED_MODE:
                result = await self._execute_degraded_mode(plan)
                alternative_used = "degraded_mode"

            elif plan.strategy == FallbackStrategy.GRACEFUL_DEGRADATION:
                result = await self._execute_graceful_degradation(plan)
                alternative_used = "graceful_degradation"

            elif plan.strategy == FallbackStrategy.CIRCUIT_BREAKER:
                result = await self._execute_circuit_breaker(plan)
                alternative_used = "circuit_breaker"

            elif plan.strategy == FallbackStrategy.EMERGENCY_BYPASS:
                result = await self._execute_emergency_bypass(plan)
                alternative_used = "emergency_bypass"

            else:
                raise ValueError(f"Unknown fallback strategy: {plan.strategy}")

            # 結果評価
            final_status = (
                "success" if result and result.get("success", False) else "failed"
            )

            # 学習データ生成
            lessons_learned = self._extract_lessons_learned(plan, result, final_status)

            fallback_result = FallbackResult(
                fallback_id=plan.plan_id,
                original_failure=failure_context,
                executed_plan=plan,
                final_status=final_status,
                recovery_time=time.time() - start_time,
                alternative_used=alternative_used,
                lessons_learned=lessons_learned,
            )

            # アラート送信
            if final_status == "failed":
                await self._send_alert(f"Fallback failed: {plan.plan_id}", "critical")
            elif alternative_used:
                await self._send_alert(
                    f"Fallback activated: {alternative_used}", "warning"
                )

            return fallback_result

        except Exception as e:
            # Handle specific exception case
            self.logger.error(f"Fallback execution failed: {str(e)}")
            return FallbackResult(
                fallback_id=plan.plan_id,
                original_failure=failure_context,
                executed_plan=plan,
                final_status="failed",
                recovery_time=time.time() - start_time,
                alternative_used=None,
                lessons_learned=[f"Execution error: {str(e)}"],
            )

    async def _execute_retry(self, plan: FallbackPlan) -> Dict[str, Any]:
        """リトライ実行"""
        failure_context = plan.failure_context
        retry_delay = self.fallback_config["retry_delays"][
            min(
                failure_context.retry_count,
                len(self.fallback_config["retry_delays"]) - 1,
            )
        ]

        self.logger.info(
            f"Retrying after {retry_delay}s delay (attempt {failure_context.retry_count + 1})"
        )

        # 指数バックオフ待機
        await asyncio.sleep(retry_delay)

        # 元のリクエストを再実行
        try:
            # 失敗したサーバントまたはコンポーネントでリトライ
            if failure_context.failed_component in self.registry._servants:
                servant = self.registry.get_servant(failure_context.failed_component)
                if servant:
                    # ServantRequest再構築
                    original_req = failure_context.original_request
                    request = ServantRequest(
                        task_id=original_req.get("task_id", "retry_task"),
                        task_type=original_req.get("task_type", "retry"),
                        priority=original_req.get("priority", "medium"),
                        data=original_req.get("data", {}),
                        context=original_req.get("context", {}),
                    )

                    response = await servant.execute_with_quality_gate(request)
                    return {
                        "success": response.status == "success",
                        "response": response.__dict__,
                    }

            return {"success": False, "error": "Component not available for retry"}

        except Exception as e:
            # Handle specific exception case
            return {"success": False, "error": str(e)}

    async def _execute_alternative_servant(self, plan: FallbackPlan) -> Dict[str, Any]:
        """代替サーバント実行"""
        alternatives = plan.alternative_options

        # 成功率の高い代替案から順次試行
        sorted_alternatives = sorted(
            [
                alt
                for alt in alternatives
                if alt.get("type") in ["alternative_servant", "cross_domain_servant"]
            ],
            key=lambda x: x.get("estimated_success_rate", 0),
            reverse=True,
        )

        for alternative in sorted_alternatives:
            # Process each item in collection
            try:
                servant_name = alternative["servant_name"]
                servant = self.registry.get_servant(servant_name)

                if servant and not self._is_circuit_open(servant_name, encoding="utf-8"):
                    # Complex condition - consider breaking down
                    # 元のリクエスト実行
                    original_req = plan.failure_context.original_request
                    request = ServantRequest(
                        task_id=f"fallback_{original_req.get('task_id', 'alt_task')}",
                        task_type=original_req.get("task_type", "alternative"),
                        priority=original_req.get("priority", "medium"),
                        data=original_req.get("data", {}),
                        context={
                            **original_req.get("context", {}),
                            "fallback_mode": True,
                        },
                    )

                    response = await servant.execute_with_quality_gate(request)

                    if response.status == "success":
                        self.logger.info(
                            f"Alternative servant {servant_name} succeeded"
                        )
                        return {
                            "success": True,
                            "alternative_used": servant_name,
                            "response": response.__dict__,
                        }
                    else:
                        self.logger.warning(
                            f"Alternative servant {servant_name} failed: {response.errors}"
                        )

            except Exception as e:
                # Handle specific exception case
                self.logger.error(
                    f"Alternative servant {alternative.get('servant_name')} error: {str(e)}"
                )
                continue

        return {"success": False, "error": "All alternative servants failed"}

    async def _execute_degraded_mode(self, plan: FallbackPlan) -> Dict[str, Any]:
        """劣化モード実行"""
        # 協調失敗時の劣化モード実行
        try:
            # 最小限の組織での協調実行
            from ..coordination.four_organizations_coordinator import (
                CoordinationPattern,
                CoordinationTask,
                TaskComplexity,
            )

            degraded_task = CoordinationTask(
                task_id=f"degraded_{plan.failure_context.failure_id}",
                name="Degraded Mode Execution",
                description="Degraded mode fallback execution",
                complexity=TaskComplexity.SIMPLE,
                pattern=CoordinationPattern.SEQUENTIAL,
                required_organizations=[ServantDomain.DWARF_WORKSHOP],  # 最小構成
                optional_organizations=[],
                context={
                    "degraded_mode": True,
                    "original_failure": plan.failure_context.failure_id,
                },
            )

            result = await self.coordinator.coordinate_task(degraded_task)

            return {
                "success": result.status == "success",
                "degraded_execution": True,
                "result": result.__dict__,
            }

        except Exception as e:
            # Handle specific exception case
            return {
                "success": False,
                "error": f"Degraded mode execution failed: {str(e)}",
            }

    async def _execute_graceful_degradation(self, plan: FallbackPlan) -> Dict[str, Any]:
        """段階的劣化実行"""
        # 品質要求を段階的に下げて実行
        quality_steps = self.fallback_config["quality_degradation_steps"]

        for quality_level in quality_steps:
            # Process each item in collection
            try:
                self.logger.info(
                    f"Attempting graceful degradation with quality level {quality_level}"
                )

                # 品質要求を下げた実行
                # （実際の実装では品質パラメータを調整）
                original_req = plan.failure_context.original_request
                degraded_request = {
                    **original_req,
                    "context": {
                        **original_req.get("context", {}),
                        "quality_level": quality_level,
                        "graceful_degradation": True,
                    },
                }

                # 簡略化実行（詳細実装は要件による）
                await asyncio.sleep(0.1)  # 模擬実行

                return {
                    "success": True,
                    "quality_level": quality_level,
                    "graceful_degradation": True,
                }

            except Exception as e:
                # Handle specific exception case
                self.logger.warning(
                    f"Graceful degradation at level {quality_level} failed: {str(e)}"
                )
                continue

        return {"success": False, "error": "All quality degradation levels failed"}

    async def _execute_circuit_breaker(self, plan: FallbackPlan) -> Dict[str, Any]:
        """サーキットブレーカー実行"""
        component = plan.failure_context.failed_component

        # サーキットブレーカーを開く
        self._open_circuit_breaker(component)

        # 代替ルートでの実行
        try:
            # 負荷分散システムに代替要求
            if hasattr(self.load_balancer, "route_request"):
                original_req = plan.failure_context.original_request
                request = ServantRequest(
                    task_id=f"circuit_breaker_{original_req.get('task_id', 'cb_task')}",
                    task_type=original_req.get("task_type", "circuit_breaker"),
                    priority=original_req.get("priority", "medium"),
                    data=original_req.get("data", {}),
                    context={
                        **original_req.get("context", {}),
                        "circuit_breaker_mode": True,
                    },
                )

                # 失敗したコンポーネントを除外したルーティング
                routing_result = await self.load_balancer.route_request(request)

                if routing_result.selected_servant.name != component:
                    # 代替サーバントで実行
                    response = (
                        await routing_result.selected_servant.execute_with_quality_gate(
                            request
                        )
                    )

                    return {
                        "success": response.status == "success",
                        "circuit_breaker_active": True,
                        "alternative_used": routing_result.selected_servant.name,
                        "response": response.__dict__,
                    }

            return {"success": False, "error": "No alternative route available"}

        except Exception as e:
            # Handle specific exception case
            return {
                "success": False,
                "error": f"Circuit breaker execution failed: {str(e)}",
            }

    async def _execute_emergency_bypass(self, plan: FallbackPlan) -> Dict[str, Any]:
        """緊急バイパス実行"""
        # 重要でない処理をスキップして最小限の処理のみ実行
        try:
            self.logger.warning(
                "Executing emergency bypass - non-critical operations skipped"
            )

            # 緊急時最小処理（実装は要件による）
            essential_result = {
                "emergency_bypass": True,
                "non_critical_skipped": True,
                "minimal_processing": True,
                "timestamp": datetime.now().isoformat(),
            }

            return {"success": True, "emergency_result": essential_result}

        except Exception as e:
            # Handle specific exception case
            return {"success": False, "error": f"Emergency bypass failed: {str(e)}"}

    # === サーキットブレーカー管理 ===

    def _is_circuit_open(self, component_name: str) -> bool:
        """サーキットブレーカー状態チェック"""
        if component_name not in self.circuit_breakers:
            return False

        circuit = self.circuit_breakers[component_name]

        if circuit["state"] == "open":
            # タイムアウトチェック
            if (
                time.time() - circuit["opened_at"]
                > self.fallback_config["circuit_breaker_timeout"]
            ):
                circuit["state"] = "half_open"
                self.logger.info(
                    f"Circuit breaker for {component_name} moved to half-open state"
                )

            return circuit["state"] == "open"

        return False

    def _open_circuit_breaker(self, component_name: str):
        """サーキットブレーカーを開く"""
        self.circuit_breakers[component_name] = {
            "state": "open",
            "opened_at": time.time(),
            "failure_count": self.circuit_breakers.get(component_name, {}).get(
                "failure_count", 0
            )
            + 1,
        }

        self.logger.warning(f"Circuit breaker opened for {component_name}")

    def _record_failure(self, failure_context: FailureContext):
        """失敗記録"""
        self.active_failures[failure_context.failure_id] = failure_context
        self.failure_history.append(failure_context)

        # サーキットブレーカー失敗カウント
        component = failure_context.failed_component
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = {"state": "closed", "failure_count": 0}

        self.circuit_breakers[component]["failure_count"] += 1

        # 閾値チェック
        if (
            self.circuit_breakers[component]["failure_count"]
            >= self.fallback_config["circuit_breaker_threshold"]
        ):
            self._open_circuit_breaker(component)

        # 統計更新
        self.fallback_stats["total_failures_detected"] += 1
        self.fallback_stats["failure_types"][failure_context.failure_type.value] += 1

    def _estimate_success_probability(
        self, failure_context: FailureContext, strategy: FallbackStrategy
    ) -> float:
        """成功確率推定"""
        # 戦略別ベース確率
        base_probabilities = {
            FallbackStrategy.RETRY: 0.6,
            FallbackStrategy.ALTERNATIVE_SERVANT: 0.8,
            FallbackStrategy.DEGRADED_MODE: 0.7,
            FallbackStrategy.GRACEFUL_DEGRADATION: 0.75,
            FallbackStrategy.CIRCUIT_BREAKER: 0.85,
            FallbackStrategy.EMERGENCY_BYPASS: 0.9,
        }

        base_prob = base_probabilities.get(strategy, 0.5)

        # リトライ回数による調整
        retry_penalty = failure_context.retry_count * 0.1

        # 失敗タイプによる調整
        type_adjustments = {
            FailureType.SERVANT_TIMEOUT: -0.1,
            FailureType.RESOURCE_EXHAUSTED: -0.2,
            FailureType.NETWORK_ERROR: -0.15,
        }

        type_adjustment = type_adjustments.get(failure_context.failure_type, 0.0)

        return max(0.1, min(0.95, base_prob - retry_penalty + type_adjustment))

    def _estimate_recovery_time(
        self, failure_context: FailureContext, strategy: FallbackStrategy
    ) -> float:
        """復旧時間推定"""
        # 戦略別ベース時間（秒）
        base_times = {
            FallbackStrategy.RETRY: 5.0,
            FallbackStrategy.ALTERNATIVE_SERVANT: 10.0,
            FallbackStrategy.DEGRADED_MODE: 15.0,
            FallbackStrategy.GRACEFUL_DEGRADATION: 20.0,
            FallbackStrategy.CIRCUIT_BREAKER: 8.0,
            FallbackStrategy.EMERGENCY_BYPASS: 3.0,
        }

        base_time = base_times.get(strategy, 10.0)

        # リトライ回数による調整
        retry_delay = sum(
            self.fallback_config["retry_delays"][: failure_context.retry_count]
        )

        return base_time + retry_delay

    def _estimate_servant_success_rate(self, servant: ElderServantBase) -> float:
        """サーバント成功率推定"""
        metrics = servant.get_metrics()
        return metrics.get("success_rate", 0.5)

    def _extract_lessons_learned(
        self, plan: FallbackPlan, result: Dict[str, Any], final_status: str
    ) -> List[str]:
        """学習データ抽出"""
        lessons = []

        if final_status == "success":
            lessons.append(
                f"Strategy {plan.strategy.value} successful for {plan.failure_context." \
                    "failure_type.value}"
            )

            if result.get("alternative_used"):
                lessons.append(
                    f"Alternative {result['alternative_used']} proved reliable"
                )
        else:
            lessons.append(
                f"Strategy {plan.strategy.value} failed for {plan.failure_context." \
                    "failure_type.value}"
            )

            if "error" in result:
                lessons.append(f"Error pattern: {result['error']}")

        # 復旧時間の学習
        if plan.estimated_recovery_time > 0:
            actual_time = plan.failure_context.timestamp
            if hasattr(plan, "recovery_time"):
                time_diff = abs(plan.recovery_time - plan.estimated_recovery_time)
                if time_diff > plan.estimated_recovery_time * 0.5:
                    lessons.append(f"Recovery time estimation needs adjustment")

        return lessons

    async def _learn_from_fallback(self, result: FallbackResult):
        """フォールバック学習"""
        # 成功パターンの記録
        if result.final_status == "success":
            success_pattern = {
                "failure_type": result.original_failure.failure_type.value,
                "strategy": result.executed_plan.strategy.value,
                "recovery_time": result.recovery_time,
                "alternative_used": result.alternative_used,
            }

            # 成功パターンを重みに反映（簡易学習）
            # 実際の実装では機械学習アルゴリズムを使用

        # 失敗パターンの記録
        else:
            failure_pattern = {
                "failure_type": result.original_failure.failure_type.value,
                "failed_strategy": result.executed_plan.strategy.value,
                "lessons": result.lessons_learned,
            }

            # 失敗パターンを回避ロジックに反映

    async def _emergency_fallback(
        self, failure_context: FailureContext, error: str
    ) -> FallbackResult:
        """緊急フォールバック"""
        self.logger.critical(
            f"Emergency fallback activated for {failure_context.failure_id}"
        )

        # 最小限の緊急処理
        emergency_plan = FallbackPlan(
            plan_id=f"emergency_{failure_context.failure_id}",
            failure_context=failure_context,
            strategy=FallbackStrategy.EMERGENCY_BYPASS,
            recovery_actions=[
                RecoveryAction.EMERGENCY_STOP,
                RecoveryAction.NOTIFY_ADMIN,
            ],
            alternative_options=[],
            estimated_recovery_time=30.0,
            success_probability=0.5,
        )

        return FallbackResult(
            fallback_id=emergency_plan.plan_id,
            original_failure=failure_context,
            executed_plan=emergency_plan,
            final_status="partial",
            recovery_time=0.0,
            alternative_used="emergency_bypass",
            lessons_learned=[f"Emergency fallback due to system error: {error}"],
        )

    async def _handle_circuit_breaker_open(
        self, failure_context: FailureContext
    ) -> FallbackResult:
        """サーキットブレーカー開放時処理"""
        self.logger.warning(
            f"Circuit breaker open for {failure_context.failed_component}, using alternative"
        )

        # 代替ルートでの処理
        circuit_breaker_plan = FallbackPlan(
            plan_id=f"circuit_breaker_{failure_context.failure_id}",
            failure_context=failure_context,
            strategy=FallbackStrategy.CIRCUIT_BREAKER,
            recovery_actions=[RecoveryAction.SWITCH_TO_BACKUP],
            alternative_options=[],
            estimated_recovery_time=5.0,
            success_probability=0.8,
        )

        return await self._execute_fallback_plan(circuit_breaker_plan)

    def _update_fallback_stats(self, result: FallbackResult, execution_time: float):
        """フォールバック統計更新"""
        if result.final_status == "success":
            self.fallback_stats["successful_fallbacks"] += 1
        else:
            self.fallback_stats["failed_fallbacks"] += 1

        self.fallback_stats["recovery_strategies"][
            result.executed_plan.strategy.value
        ] += 1

        # 移動平均で復旧時間更新
        total_fallbacks = (
            self.fallback_stats["successful_fallbacks"]
            + self.fallback_stats["failed_fallbacks"]
        )
        current_avg = self.fallback_stats["average_recovery_time"]

        self.fallback_stats["average_recovery_time"] = (
            current_avg * (total_fallbacks - 1) + execution_time
        ) / total_fallbacks

    async def _send_alert(self, message: str, level: str):
        """アラート送信"""
        alert_data = {
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
            "system": "auto_fallback",
        }

        for callback in self.alert_callbacks:
            # Process each item in collection
            try:
                await callback(alert_data)
            except Exception as e:
                # Handle specific exception case
                self.logger.error(f"Alert callback failed: {str(e)}")

    def add_alert_callback(self, callback: Callable):
        """アラートコールバック追加"""
        self.alert_callbacks.append(callback)

    async def get_fallback_status(self) -> Dict[str, Any]:
        """フォールバックシステム状態取得"""
        return {
            "system_status": {
                "active_failures": len(self.active_failures),
                "circuit_breakers": {
                    name: {"state": cb["state"], "failure_count": cb["failure_count"]}
                    for name, cb in self.circuit_breakers.items()
                },
                "total_fallbacks": len(self.fallback_history),
            },
            "statistics": self.fallback_stats,
            "recent_failures": [
                {
                    "failure_id": fc.failure_id,
                    "type": fc.failure_type.value,
                    "component": fc.failed_component,
                    "timestamp": fc.timestamp.isoformat(),
                }
                for fc in list(self.failure_history)[-10:]  # 最新10件
            ],
        }


class PerformanceMonitor:
    """パフォーマンス監視"""

    def __init__(self):
        self.metrics = defaultdict(list)

    def record_metric(self, metric_name: str, value: float):
        """メトリクス記録"""
        self.metrics[metric_name].append({"value": value, "timestamp": time.time()})

        # 履歴サイズ制限
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-800:]


# グローバルフォールバックシステムインスタンス
_global_fallback_system = None


def get_auto_fallback_system() -> AutoFallbackSystem:
    """グローバル自動フォールバックシステムを取得"""
    global _global_fallback_system
    if _global_fallback_system is None:
        _global_fallback_system = AutoFallbackSystem()
    return _global_fallback_system


# 便利な失敗検知デコレータ
def with_auto_fallback(failure_type: FailureType = FailureType.SERVANT_ERROR):
    """自動フォールバック付きデコレータ"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 失敗コンテキスト作成
                failure_context = FailureContext(
                    failure_id=f"auto_{func.__name__}_{int(time.time())}",
                    failure_type=failure_type,
                    failed_component=func.__name__,
                    original_request={"args": args, "kwargs": kwargs},
                    error_details={
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    },
                    timestamp=datetime.now(),
                )

                # 自動フォールバック実行
                fallback_system = get_auto_fallback_system()
                result = await fallback_system.handle_failure(failure_context)

                if result.final_status == "success":
                    return result
                else:
                    raise e

        return wrapper

    return decorator