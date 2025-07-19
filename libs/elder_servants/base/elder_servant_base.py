"""
エルダーサーバント基底クラス

すべてのエルダーサーバントが継承する基底クラス。
Iron Will品質基準に準拠し、4賢者システムとの連携を提供。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

# 型変数定義
TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class ServantDomain(Enum):
    """サーバントのドメイン分類"""

    DWARF_WORKSHOP = "dwarf_workshop"  # ドワーフ工房
    RAG_WIZARDS = "rag_wizards"  # RAGウィザーズ
    ELF_FOREST = "elf_forest"  # エルフの森
    INCIDENT_KNIGHTS = "incident_knights"  # インシデント騎士団


class ServantCapability(Enum):
    """サーバントの能力カテゴリ"""

    CODE_GENERATION = "code_generation"
    TESTING = "testing"
    REFACTORING = "refactoring"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"


@dataclass
class ServantRequest(Generic[TRequest]):
    """サーバントへのリクエスト基底クラス"""

    task_id: str
    task_type: str
    priority: str
    data: TRequest
    context: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ServantResponse(Generic[TResponse]):
    """サーバントからのレスポンス基底クラス"""

    task_id: str
    status: str  # success, failed, partial
    data: TResponse
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ElderServantBase(ABC, Generic[TRequest, TResponse]):
    """
    エルダーサーバント基底クラス

    すべてのエルダーサーバントはこのクラスを継承し、
    Iron Will品質基準に準拠した実装を行う。
    """

    def __init__(self, name: str, domain: ServantDomain):
        self.name = name
        self.domain = domain
        self.logger = logging.getLogger(f"elder_servant.{name}")
        self.capabilities: List[ServantCapability] = []
        self._metrics = {
            "tasks_processed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "average_processing_time": 0,
        }
        self._quality_scores = {
            "root_cause_resolution": 0,
            "dependency_completeness": 0,
            "test_coverage": 0,
            "security_score": 0,
            "performance_score": 0,
            "maintainability_score": 0,
        }

    @abstractmethod
    async def process_request(
        self, request: ServantRequest[TRequest]
    ) -> ServantResponse[TResponse]:
        """
        リクエストを処理する抽象メソッド

        各サーバントはこのメソッドを実装し、
        固有の処理ロジックを提供する。
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[ServantCapability]:
        """サーバントの能力リストを返す"""
        pass

    @abstractmethod
    def validate_request(self, request: ServantRequest[TRequest]) -> bool:
        """リクエストの妥当性を検証"""
        pass

    async def execute_with_quality_gate(
        self, request: ServantRequest[TRequest]
    ) -> ServantResponse[TResponse]:
        """
        Iron Will品質ゲートを通してリクエストを実行

        品質基準をチェックし、基準を満たさない場合は
        処理を拒否またはアラートを発生させる。
        """
        start_time = datetime.now()

        try:
            # リクエスト検証
            if not self.validate_request(request):
                return ServantResponse(
                    task_id=request.task_id,
                    status="failed",
                    data=None,
                    errors=["Invalid request"],
                    warnings=[],
                    metrics={},
                )

            # 品質チェック前処理
            self.logger.info(f"Processing task {request.task_id} with {self.name}")

            # メイン処理実行
            response = await self.process_request(request)

            # 品質スコア更新
            await self._update_quality_scores(request, response)

            # メトリクス更新
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(response.status == "success", processing_time)

            # Iron Will基準チェック
            if not self._check_iron_will_criteria():
                response.warnings.append("Iron Will quality criteria not fully met")

            return response

        except Exception as e:
            self.logger.error(f"Error processing task {request.task_id}: {str(e)}")
            self._update_metrics(False, (datetime.now() - start_time).total_seconds())

            return ServantResponse(
                task_id=request.task_id,
                status="failed",
                data=None,
                errors=[str(e)],
                warnings=[],
                metrics=self._metrics,
            )

    def _check_iron_will_criteria(self) -> bool:
        """Iron Will 6大品質基準のチェック"""
        criteria = {
            "root_cause_resolution": 95,
            "dependency_completeness": 100,
            "test_coverage": 95,
            "security_score": 90,
            "performance_score": 85,
            "maintainability_score": 80,
        }

        for metric, threshold in criteria.items():
            if self._quality_scores.get(metric, 0) < threshold:
                self.logger.warning(
                    f"{metric} score {self._quality_scores[metric]} below threshold {threshold}"
                )
                return False

        return True

    async def _update_quality_scores(
        self, request: ServantRequest[TRequest], response: ServantResponse[TResponse]
    ):
        """品質スコアの更新（実装は各サーバントでカスタマイズ可能）"""
        # デフォルト実装：レスポンスのステータスに基づく簡易更新
        if response.status == "success":
            for key in self._quality_scores:
                self._quality_scores[key] = min(100, self._quality_scores[key] + 1)

    def _update_metrics(self, success: bool, processing_time: float):
        """メトリクスの更新"""
        self._metrics["tasks_processed"] += 1
        if success:
            self._metrics["tasks_succeeded"] += 1
        else:
            self._metrics["tasks_failed"] += 1

        # 移動平均で処理時間を更新
        current_avg = self._metrics["average_processing_time"]
        total_tasks = self._metrics["tasks_processed"]
        self._metrics["average_processing_time"] = (
            current_avg * (total_tasks - 1) + processing_time
        ) / total_tasks

    def get_metrics(self) -> Dict[str, Any]:
        """現在のメトリクスを返す"""
        return {
            **self._metrics,
            "quality_scores": self._quality_scores,
            "success_rate": (
                self._metrics["tasks_succeeded"] / self._metrics["tasks_processed"]
                if self._metrics["tasks_processed"] > 0
                else 0
            ),
        }

    async def connect_to_sages(self) -> bool:
        """4賢者システムとの接続を確立"""
        # TODO: 実際の4賢者システムとの連携実装
        self.logger.info(f"{self.name} connecting to 4 Sages system...")
        return True

    async def report_to_elder_council(self, report: Dict[str, Any]):
        """エルダー評議会への報告"""
        # TODO: 実際のエルダー評議会への報告実装
        self.logger.info(f"{self.name} reporting to Elder Council: {report}")

    def __repr__(self):
        return f"<{self.__class__.__name__}(name={self.name}, domain={self.domain})>"


class DwarfServant(ElderServantBase[Dict[str, Any], Dict[str, Any]]):
    """ドワーフ工房専門サーバントの基底クラス"""

    def __init__(self, servant_id: str, name: str, specialization: str):
        super().__init__(name, ServantDomain.DWARF_WORKSHOP)
        self.servant_id = servant_id
        self.specialization = specialization
        self.category = "dwarf_workshop"

    async def collaborate_with_sages(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """4賢者との協調（ドワーフ工房特化）"""
        # TODO: 実際の4賢者システムとの連携
        return {
            "knowledge_sage": {"status": "consulted"},
            "task_sage": {"status": "consulted"},
            "incident_sage": {"status": "consulted"},
            "rag_sage": {"status": "consulted"},
        }


class WizardServant(ElderServantBase[Dict[str, Any], Dict[str, Any]]):
    """RAGウィザーズ専門サーバントの基底クラス"""

    def __init__(self, servant_id: str, name: str, specialization: str):
        super().__init__(name, ServantDomain.RAG_WIZARDS)
        self.servant_id = servant_id
        self.specialization = specialization
        self.category = "rag_wizards"

    async def research_and_analyze(self, topic: str) -> Dict[str, Any]:
        """調査研究の共通メソッド"""
        # 専門的な調査ロジックを実装
        return {"research_results": []}


class ElfServant(ElderServantBase[Dict[str, Any], Dict[str, Any]]):
    """エルフの森専門サーバントの基底クラス"""

    def __init__(self, servant_id: str, name: str, specialization: str):
        super().__init__(name, ServantDomain.ELF_FOREST)
        self.servant_id = servant_id
        self.specialization = specialization
        self.category = "elf_forest"

    async def monitor_and_maintain(self, target: str) -> Dict[str, Any]:
        """監視保守の共通メソッド"""
        # 監視・保守ロジックを実装
        return {"health_status": "healthy"}
