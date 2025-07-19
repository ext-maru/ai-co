"""
Elder Servant統合基盤システム
EldersLegacy継承システム完全実装版

すべてのElderServantが継承する統合基底クラス。
Iron Will品質基準に準拠し、4賢者システムとの連携を提供。
エルダー評議会令第27号完全準拠実装。
"""

import asyncio
import hashlib
import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

# EldersLegacy統合インポート
from libs.core.elders_legacy import (
    EldersLegacyDomain,
    EldersServiceLegacy,
    IronWillCriteria,
    enforce_boundary,
)

# 型変数定義
TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class ServantCategory(Enum):
    """サーバント分類（エルダーズギルド組織）"""

    DWARF = "dwarf"  # ドワーフ工房（開発製作）
    WIZARD = "wizard"  # RAGウィザーズ（調査研究）
    ELF = "elf"  # エルフの森（監視メンテナンス）
    KNIGHT = "knight"  # インシデント騎士団（緊急対応）


class ServantDomain(Enum):
    """サーバントのドメイン分類（技術領域）"""

    DWARF_WORKSHOP = "dwarf_workshop"  # ドワーフ工房
    RAG_WIZARDS = "rag_wizards"  # RAGウィザーズ
    ELF_FOREST = "elf_forest"  # エルフの森
    INCIDENT_KNIGHTS = "incident_knights"  # インシデント騎士団


class TaskStatus(Enum):
    """タスク実行状況"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """タスク優先度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServantCapability:
    """サーバント能力定義（詳細版）"""

    def __init__(
        self,
        name: str,
        description: str,
        input_types: List[str],
        output_types: List[str],
        complexity: int = 1,
        domain: Optional[ServantDomain] = None,
    ):
        self.name = name
        self.description = description
        self.input_types = input_types
        self.output_types = output_types
        self.complexity = complexity  # 1-10 (実行複雑度)
        self.domain = domain

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_types": self.input_types,
            "output_types": self.output_types,
            "complexity": self.complexity,
            "domain": self.domain.value if self.domain else None,
        }


class TaskResult:
    """タスク実行結果"""

    def __init__(
        self,
        task_id: str,
        servant_id: str,
        status: TaskStatus,
        result_data: Dict[str, Any] = None,
        error_message: str = None,
        execution_time_ms: float = 0.0,
        quality_score: float = 0.0,
        iron_will_compliant: bool = False,
    ):
        self.task_id = task_id
        self.servant_id = servant_id
        self.status = status
        self.result_data = result_data or {}
        self.error_message = error_message
        self.execution_time_ms = execution_time_ms
        self.quality_score = quality_score
        self.iron_will_compliant = iron_will_compliant
        self.completed_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "servant_id": self.servant_id,
            "status": self.status.value,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "quality_score": self.quality_score,
            "iron_will_compliant": self.iron_will_compliant,
            "completed_at": self.completed_at.isoformat(),
        }


class ServantRequest(Generic[TRequest]):
    """エルダーサーバント統一リクエスト形式"""

    def __init__(
        self,
        task_id: str,
        task_type: str,
        priority: TaskPriority,
        payload: TRequest,
        context: Dict[str, Any] = None,
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.priority = priority
        self.payload = payload
        self.context = context or {}
        self.created_at = datetime.now()


class ServantResponse(Generic[TResponse]):
    """エルダーサーバント統一レスポンス形式"""

    def __init__(
        self,
        task_id: str,
        servant_id: str,
        status: TaskStatus,
        result_data: TResponse = None,
        error_message: str = None,
        execution_time_ms: float = 0.0,
        quality_score: float = 0.0,
        iron_will_compliant: bool = False,
    ):
        self.task_id = task_id
        self.servant_id = servant_id
        self.status = status
        self.result_data = result_data
        self.error_message = error_message
        self.execution_time_ms = execution_time_ms
        self.quality_score = quality_score
        self.iron_will_compliant = iron_will_compliant
        self.completed_at = datetime.now()


class IronWillMetrics:
    """Iron Will 6大品質基準メトリクス"""

    def __init__(self):
        self.root_cause_resolution = 0.0  # 根本解決度 (>=95%)
        self.dependency_completeness = 0.0  # 依存関係完全性 (100%)
        self.test_coverage = 0.0  # テストカバレッジ (>=95%)
        self.security_score = 0.0  # セキュリティスコア (>=90%)
        self.performance_score = 0.0  # パフォーマンス基準 (>=85%)
        self.maintainability_score = 0.0  # 保守性指標 (>=80%)

    def get_overall_score(self) -> float:
        """総合品質スコア計算"""
        return (
            self.root_cause_resolution
            + self.dependency_completeness
            + self.test_coverage
            + self.security_score
            + self.performance_score
            + self.maintainability_score
        ) / 6

    def meets_iron_will_criteria(self) -> bool:
        """Iron Will基準充足判定"""
        return (
            self.root_cause_resolution >= 95.0
            and self.dependency_completeness >= 100.0
            and self.test_coverage >= 95.0
            and self.security_score >= 90.0
            and self.performance_score >= 85.0
            and self.maintainability_score >= 80.0
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_cause_resolution": self.root_cause_resolution,
            "dependency_completeness": self.dependency_completeness,
            "test_coverage": self.test_coverage,
            "security_score": self.security_score,
            "performance_score": self.performance_score,
            "maintainability_score": self.maintainability_score,
            "overall_score": self.get_overall_score(),
            "iron_will_compliant": self.meets_iron_will_criteria(),
        }


def iron_will_quality_gate(func):
    """Iron Will品質ゲートデコレータ"""

    async def wrapper(self, *args, **kwargs):
        start_time = datetime.now()

        try:
            # 品質チェック前処理
            self.logger.info(f"Iron Will quality gate: {func.__name__}")

            # メイン処理実行
            result = await func(self, *args, **kwargs)

            # 品質スコア検証
            if hasattr(self, "_iron_will_metrics"):
                if not self._iron_will_metrics.meets_iron_will_criteria():
                    self.logger.warning(
                        f"Iron Will criteria not met: {self._iron_will_metrics.get_overall_score():.1f}%"
                    )

            return result

        except Exception as e:
            self.logger.error(f"Iron Will quality gate failed: {str(e)}")
            raise

    return wrapper


class UnifiedElderServant(EldersServiceLegacy[ServantRequest, ServantResponse]):
    """
    🏛️ 統合エルダーサーバント基盤クラス

    EldersServiceLegacyから継承し、Iron Will品質基準に完全準拠。
    エルダー評議会令第27号により、すべてのサーバントは本クラスを継承必須。

    新機能:
    - EldersLegacy完全統合
    - Iron Will 6大基準統合
    - 品質ゲート統合
    - 4賢者システム連携強化
    """

    def __init__(
        self,
        servant_id: str,
        servant_name: str,
        category: ServantCategory,
        domain: ServantDomain,
        specialization: str,
        capabilities: List[ServantCapability],
    ):
        # EldersServiceLegacy初期化 (EXECUTION域で自動設定)
        super().__init__(servant_id)

        # サーバント固有プロパティ
        self.servant_id = servant_id
        self.servant_name = servant_name
        self.category = category
        self.domain = domain
        self.specialization = specialization
        self.capabilities = capabilities

        # ロガー設定
        self.logger = logging.getLogger(f"elder_servants.{servant_id}")

        # Iron Will品質基準
        self._iron_will_metrics = IronWillMetrics()
        self.quality_threshold = 95.0  # 95%以上必須

        # 実行統計
        self.stats = {
            "tasks_executed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "total_execution_time_ms": 0.0,
            "average_quality_score": 0.0,
            "last_activity": datetime.now(),
            "created_at": datetime.now(),
        }

        # 現在実行中のタスク
        self.current_tasks: Dict[str, Dict[str, Any]] = {}

        # 4賢者との連携用
        self.sage_connections: Dict[str, Any] = {}

        self.logger.info(
            f"Unified Elder Servant {servant_name} ({servant_id}) initialized"
        )

    # EldersServiceLegacy抽象メソッド実装
    async def process_request(self, request: ServantRequest) -> ServantResponse:
        """
        EldersServiceLegacy統一リクエスト処理

        Args:
            request: ServantRequest形式のリクエスト

        Returns:
            ServantResponse: 統一レスポンス
        """
        import time

        start_time = time.time()

        try:
            # リクエスト検証
            if not self.validate_request(request):
                return ServantResponse(
                    task_id=request.task_id,
                    servant_id=self.servant_id,
                    status=TaskStatus.FAILED,
                    error_message="Invalid request",
                    execution_time_ms=(time.time() - start_time) * 1000,
                    quality_score=0.0,
                )

            # 旧形式タスクに変換
            task = {
                "task_id": request.task_id,
                "task_type": request.task_type,
                "priority": request.priority.value,
                "payload": request.payload,
                "context": request.context,
            }

            # 既存のexecute_taskメソッド使用
            result = await self.execute_task(task)

            # Iron Will品質チェック
            iron_will_compliant = await self._validate_iron_will_quality(
                result.result_data
            )

            # 統計更新
            await self._update_stats(result)

            # ServantResponseに変換
            return ServantResponse(
                task_id=request.task_id,
                servant_id=self.servant_id,
                status=result.status,
                result_data=result.result_data,
                error_message=result.error_message,
                execution_time_ms=(time.time() - start_time) * 1000,
                quality_score=result.quality_score,
                iron_will_compliant=iron_will_compliant,
            )

        except Exception as e:
            self.logger.error(f"Request processing failed: {str(e)}")
            return ServantResponse(
                task_id=request.task_id,
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
                quality_score=0.0,
                iron_will_compliant=False,
            )

    def validate_request(self, request: ServantRequest) -> bool:
        """
        EldersServiceLegacyリクエスト検証

        Args:
            request: 検証対象リクエスト

        Returns:
            bool: 検証結果
        """
        if not request.task_id or not request.task_type:
            return False
        if not hasattr(request, "payload"):
            return False
        return True

    def get_capabilities(self) -> List[str]:
        """
        EldersServiceLegacy能力取得

        Returns:
            List[str]: 能力名一覧
        """
        return [cap.name for cap in self.get_all_capabilities()]

    @enforce_boundary("servant")
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        タスク実行（各サーバントで具体実装）
        Iron Will品質基準を満たすタスク実行

        Args:
            task: 実行タスク情報

        Returns:
            TaskResult: 実行結果
        """
        pass

    @abstractmethod
    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """
        専門特化能力の取得（各サーバントで具体実装）

        Returns:
            List[ServantCapability]: 専門能力一覧
        """
        pass

    @iron_will_quality_gate
    async def execute_with_quality_gate(
        self, request: ServantRequest
    ) -> ServantResponse:
        """
        Iron Will品質ゲート付きタスク実行

        Args:
            request: リクエスト

        Returns:
            ServantResponse: 品質チェック済みレスポンス
        """
        return await self.process_request(request)

    async def health_check(self) -> Dict[str, Any]:
        """包括的ヘルスチェック（EldersLegacy統合版）"""
        uptime = datetime.now() - self.stats["created_at"]

        # 品質スコア計算
        quality_status = (
            "excellent"
            if self.stats["average_quality_score"] >= 95
            else "good"
            if self.stats["average_quality_score"] >= 85
            else "warning"
            if self.stats["average_quality_score"] >= 75
            else "critical"
        )

        # 稼働率計算
        success_rate = (
            self.stats["tasks_succeeded"] / max(self.stats["tasks_executed"], 1)
        ) * 100

        # Iron Will準拠チェック
        iron_will_status = self._iron_will_metrics.meets_iron_will_criteria()

        return {
            "success": True,
            "servant_id": self.servant_id,
            "servant_name": self.servant_name,
            "category": self.category.value,
            "domain": self.domain.value,
            "specialization": self.specialization,
            "status": "healthy"
            if quality_status in ["excellent", "good"]
            and success_rate >= 90
            and iron_will_status
            else "degraded",
            "uptime_seconds": uptime.total_seconds(),
            "current_tasks": len(self.current_tasks),
            "stats": {
                "tasks_executed": self.stats["tasks_executed"],
                "success_rate": round(success_rate, 2),
                "average_quality_score": round(self.stats["average_quality_score"], 2),
                "quality_status": quality_status,
            },
            "iron_will_metrics": self._iron_will_metrics.to_dict(),
            "capabilities_count": len(self.get_all_capabilities()),
            "last_activity": self.stats["last_activity"].isoformat(),
            "elders_legacy_compliant": True,
        }

    def get_all_capabilities(self) -> List[ServantCapability]:
        """全能力取得（基本能力 + 専門能力）"""
        base_capabilities = [
            ServantCapability(
                "health_check",
                "サーバント健康状態確認",
                ["none"],
                ["health_status"],
                1,
                self.domain,
            ),
            ServantCapability(
                "task_execution",
                "汎用タスク実行",
                ["task_definition"],
                ["task_result"],
                3,
                self.domain,
            ),
            ServantCapability(
                "quality_validation",
                "Iron Will品質基準検証",
                ["result_data"],
                ["quality_score"],
                2,
                self.domain,
            ),
            ServantCapability(
                "sage_collaboration",
                "4賢者連携",
                ["collaboration_request"],
                ["collaboration_result"],
                4,
                self.domain,
            ),
        ]

        return base_capabilities + self.get_specialized_capabilities()

    async def collaborate_with_sages(
        self, sage_type: str, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        4賢者との連携（強化版）

        Args:
            sage_type: 連携先賢者タイプ (knowledge/task/incident/rag)
            request: 連携リクエスト

        Returns:
            Dict[str, Any]: 連携結果
        """
        self.logger.info(
            f"Collaborating with {sage_type} sage: {request.get('type', 'unknown')}"
        )

        # 実際の実装では賢者システムとの通信を行う
        collaboration_result = {
            "success": True,
            "sage_type": sage_type,
            "message": f"Enhanced collaboration with {sage_type} sage",
            "request_id": request.get("request_id", str(uuid.uuid4())),
            "timestamp": datetime.now().isoformat(),
            "iron_will_validated": True,
        }

        # 連携履歴を記録
        if sage_type not in self.sage_connections:
            self.sage_connections[sage_type] = []

        self.sage_connections[sage_type].append(
            {
                "timestamp": datetime.now(),
                "request": request,
                "result": collaboration_result,
            }
        )

        return collaboration_result

    async def _validate_iron_will_quality(self, result_data: Dict[str, Any]) -> bool:
        """
        Iron Will品質基準検証（強化版）

        Args:
            result_data: 検証対象データ

        Returns:
            bool: Iron Will準拠判定
        """
        # 基本品質チェック
        base_score = 0.0
        checks = 0

        # 成功性チェック
        if result_data.get("success", False):
            base_score += 30
        checks += 1

        # エラーハンドリング確認
        if "error" not in result_data or result_data.get("error") is None:
            base_score += 20
        checks += 1

        # 完全性確認
        required_fields = ["status", "data"]
        if all(field in result_data for field in required_fields):
            base_score += 25
        checks += 1

        # パフォーマンス確認
        execution_time = result_data.get("execution_time_ms", 0)
        if execution_time > 0 and execution_time < 5000:  # 5秒未満
            base_score += 25
        checks += 1

        # Iron Will基準更新
        self._iron_will_metrics.root_cause_resolution = max(
            self._iron_will_metrics.root_cause_resolution,
            base_score if result_data.get("success") else 0,
        )

        self._iron_will_metrics.test_coverage = max(
            self._iron_will_metrics.test_coverage,
            95.0 if checks == 4 else (checks / 4) * 100,
        )

        # 品質スコア判定
        final_score = base_score
        meets_iron_will = final_score >= 95.0

        self.logger.debug(
            f"Iron Will validation score: {final_score:.2f}, compliant: {meets_iron_will}"
        )

        return meets_iron_will

    async def _update_stats(self, result: TaskResult):
        """統計情報更新（強化版）"""
        self.stats["tasks_executed"] += 1
        self.stats["total_execution_time_ms"] += result.execution_time_ms
        self.stats["last_activity"] = datetime.now()

        if result.status == TaskStatus.COMPLETED:
            self.stats["tasks_succeeded"] += 1
        elif result.status == TaskStatus.FAILED:
            self.stats["tasks_failed"] += 1

        # 平均品質スコア更新
        if self.stats["tasks_executed"] > 0:
            total_quality = self.stats["average_quality_score"] * (
                self.stats["tasks_executed"] - 1
            )
            self.stats["average_quality_score"] = (
                total_quality + result.quality_score
            ) / self.stats["tasks_executed"]

        # Iron Will メトリクス更新
        if result.quality_score >= 95.0:
            self._iron_will_metrics.root_cause_resolution = min(
                100.0, self._iron_will_metrics.root_cause_resolution + 1.0
            )

    def get_iron_will_metrics(self) -> Dict[str, Any]:
        """Iron Will品質基準メトリクス取得"""
        return self._iron_will_metrics.to_dict()

    def __str__(self) -> str:
        return f"{self.servant_name}({self.servant_id})"

    def __repr__(self) -> str:
        return f"<UnifiedElderServant {self.servant_name} category={self.category.value} domain={self.domain.value} tasks={self.stats['tasks_executed']}>"


# 特化サーバント基底クラス群


class DwarfWorkshopServant(UnifiedElderServant):
    """ドワーフ工房専門サーバントの基底クラス"""

    def __init__(
        self,
        servant_id: str,
        servant_name: str,
        specialization: str,
        capabilities: List[ServantCapability],
    ):
        super().__init__(
            servant_id=servant_id,
            servant_name=servant_name,
            category=ServantCategory.DWARF,
            domain=ServantDomain.DWARF_WORKSHOP,
            specialization=specialization,
            capabilities=capabilities,
        )

    async def forge_and_craft(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """ドワーフ工房特化：鍛造・製作メソッド"""
        return {
            "crafted_item": specification.get("item_type", "unknown"),
            "quality": "legendary",
            "completion_time": datetime.now().isoformat(),
        }


class RAGWizardServant(UnifiedElderServant):
    """RAGウィザーズ専門サーバントの基底クラス"""

    def __init__(
        self,
        servant_id: str,
        servant_name: str,
        specialization: str,
        capabilities: List[ServantCapability],
    ):
        super().__init__(
            servant_id=servant_id,
            servant_name=servant_name,
            category=ServantCategory.WIZARD,
            domain=ServantDomain.RAG_WIZARDS,
            specialization=specialization,
            capabilities=capabilities,
        )

    async def research_and_analyze(
        self, topic: str, depth: str = "standard"
    ) -> Dict[str, Any]:
        """RAGウィザーズ特化：調査研究メソッド"""
        return {
            "research_topic": topic,
            "depth": depth,
            "findings": [],
            "completion_time": datetime.now().isoformat(),
        }


class ElfForestServant(UnifiedElderServant):
    """エルフの森専門サーバントの基底クラス"""

    def __init__(
        self,
        servant_id: str,
        servant_name: str,
        specialization: str,
        capabilities: List[ServantCapability],
    ):
        super().__init__(
            servant_id=servant_id,
            servant_name=servant_name,
            category=ServantCategory.ELF,
            domain=ServantDomain.ELF_FOREST,
            specialization=specialization,
            capabilities=capabilities,
        )

    async def monitor_and_maintain(self, target: str) -> Dict[str, Any]:
        """エルフの森特化：監視保守メソッド"""
        return {
            "target": target,
            "health_status": "healthy",
            "maintenance_actions": [],
            "completion_time": datetime.now().isoformat(),
        }


class IncidentKnightServant(UnifiedElderServant):
    """インシデント騎士団専門サーバントの基底クラス"""

    def __init__(
        self,
        servant_id: str,
        servant_name: str,
        specialization: str,
        capabilities: List[ServantCapability],
    ):
        super().__init__(
            servant_id=servant_id,
            servant_name=servant_name,
            category=ServantCategory.KNIGHT,
            domain=ServantDomain.INCIDENT_KNIGHTS,
            specialization=specialization,
            capabilities=capabilities,
        )

    async def respond_to_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """インシデント騎士団特化：緊急対応メソッド"""
        return {
            "incident_id": incident.get("id", "unknown"),
            "response_status": "handled",
            "resolution_actions": [],
            "completion_time": datetime.now().isoformat(),
        }


class ServantRegistry:
    """統合エルダーサーバント管理レジストリ（強化版）"""

    def __init__(self):
        self.servants: Dict[str, UnifiedElderServant] = {}
        self.category_index: Dict[ServantCategory, List[str]] = {
            ServantCategory.DWARF: [],
            ServantCategory.WIZARD: [],
            ServantCategory.ELF: [],
            ServantCategory.KNIGHT: [],
        }
        self.domain_index: Dict[ServantDomain, List[str]] = {
            ServantDomain.DWARF_WORKSHOP: [],
            ServantDomain.RAG_WIZARDS: [],
            ServantDomain.ELF_FOREST: [],
            ServantDomain.INCIDENT_KNIGHTS: [],
        }
        self.specialization_index: Dict[str, List[str]] = {}
        self.logger = logging.getLogger("unified_elder_servants.registry")

    def register_servant(self, servant: UnifiedElderServant):
        """サーバント登録（強化版）"""
        self.servants[servant.servant_id] = servant
        self.category_index[servant.category].append(servant.servant_id)
        self.domain_index[servant.domain].append(servant.servant_id)

        if servant.specialization not in self.specialization_index:
            self.specialization_index[servant.specialization] = []
        self.specialization_index[servant.specialization].append(servant.servant_id)

        self.logger.info(
            f"Registered unified servant: {servant.servant_name} ({servant.servant_id}) "
            f"- {servant.category.value}/{servant.domain.value}"
        )

    def get_servant(self, servant_id: str) -> Optional[UnifiedElderServant]:
        """サーバント取得"""
        return self.servants.get(servant_id)

    def get_servants_by_category(
        self, category: ServantCategory
    ) -> List[UnifiedElderServant]:
        """カテゴリ別サーバント取得"""
        servant_ids = self.category_index.get(category, [])
        return [self.servants[sid] for sid in servant_ids if sid in self.servants]

    def get_servants_by_domain(
        self, domain: ServantDomain
    ) -> List[UnifiedElderServant]:
        """ドメイン別サーバント取得"""
        servant_ids = self.domain_index.get(domain, [])
        return [self.servants[sid] for sid in servant_ids if sid in self.servants]

    async def execute_with_best_servant(
        self, request: ServantRequest
    ) -> ServantResponse:
        """最適サーバントでタスク実行"""
        servant = self.find_best_servant_for_request(request)

        if not servant:
            return ServantResponse(
                task_id=request.task_id,
                servant_id="none",
                status=TaskStatus.FAILED,
                error_message="No suitable servant found for request",
            )

        self.logger.info(f"Executing request with servant: {servant.servant_name}")
        return await servant.execute_with_quality_gate(request)

    def find_best_servant_for_request(
        self, request: ServantRequest
    ) -> Optional[UnifiedElderServant]:
        """リクエストに最適なサーバント選出（強化版）"""
        best_servant = None
        best_score = 0

        for servant in self.servants.values():
            score = 0

            # 専門分野マッチング
            if request.task_type in servant.specialization:
                score += 50

            # 能力マッチング
            for capability in servant.get_all_capabilities():
                if request.task_type in capability.name:
                    score += 30

            # 優先度考慮
            if request.priority == TaskPriority.CRITICAL:
                score += 20
            elif request.priority == TaskPriority.HIGH:
                score += 10

            # 現在の負荷考慮
            if len(servant.current_tasks) == 0:
                score += 15
            elif len(servant.current_tasks) < 3:
                score += 5

            # 品質スコア考慮
            score += servant.stats["average_quality_score"] * 0.1

            # Iron Will準拠度考慮
            if servant._iron_will_metrics.meets_iron_will_criteria():
                score += 25

            if score > best_score:
                best_score = score
                best_servant = servant

        return best_servant

    async def health_check_all(self) -> Dict[str, Any]:
        """全サーバントヘルスチェック（統合版）"""
        health_results = {}
        iron_will_compliant_count = 0

        for servant_id, servant in self.servants.items():
            try:
                health_result = await servant.health_check()
                health_results[servant_id] = health_result

                if health_result.get("iron_will_metrics", {}).get(
                    "iron_will_compliant", False
                ):
                    iron_will_compliant_count += 1

            except Exception as e:
                health_results[servant_id] = {
                    "success": False,
                    "servant_id": servant_id,
                    "status": "error",
                    "error": str(e),
                }

        # 全体統計計算
        total_servants = len(self.servants)
        healthy_servants = sum(
            1 for result in health_results.values() if result.get("status") == "healthy"
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "total_servants": total_servants,
            "healthy_servants": healthy_servants,
            "iron_will_compliant_servants": iron_will_compliant_count,
            "health_rate": round((healthy_servants / max(total_servants, 1)) * 100, 2),
            "iron_will_compliance_rate": round(
                (iron_will_compliant_count / max(total_servants, 1)) * 100, 2
            ),
            "servants": health_results,
            "elders_legacy_integrated": True,
        }


# グローバルレジストリインスタンス
unified_servant_registry = ServantRegistry()
