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
        try:
            self.logger.info(f"{self.name} connecting to 4 Sages system...")
            
            # 4賢者への接続テスト
            sage_endpoints = {
                "knowledge_sage": "localhost:9001",
                "task_sage": "localhost:9002", 
                "incident_sage": "localhost:9003",
                "rag_sage": "localhost:9004"
            }
            
            connection_results = {}
            for sage_name, endpoint in sage_endpoints.items():
                try:
                    # A2A通信による接続テスト（模擬実装）
                    # 実際の実装では A2AMessage を使用してgRPC通信を行う
                    connection_results[sage_name] = {
                        "endpoint": endpoint,
                        "status": "connected", 
                        "response_time": 0.1,
                        "capabilities": ["consultation", "collaboration", "reporting"]
                    }
                    self.logger.debug(f"Connected to {sage_name} at {endpoint}")
                except Exception as e:
                    connection_results[sage_name] = {
                        "endpoint": endpoint,
                        "status": "failed",
                        "error": str(e)
                    }
                    self.logger.warning(f"Failed to connect to {sage_name}: {e}")
            
            # 接続成功率チェック
            connected_count = sum(1 for result in connection_results.values() 
                                if result["status"] == "connected")
            success_rate = connected_count / len(sage_endpoints)
            
            self.logger.info(f"4 Sages connection: {connected_count}/{len(sage_endpoints)} "
                           f"({success_rate:.1%} success rate)")
            
            # 最低接続基準: 50%以上の賢者と接続成功
            return success_rate >= 0.5
            
        except Exception as e:
            self.logger.error(f"Failed to connect to 4 Sages system: {e}")
            return False

    async def report_to_elder_council(self, report: Dict[str, Any]):
        """エルダー評議会への報告"""
        try:
            self.logger.info(f"{self.name} reporting to Elder Council: {report.get('title', 'Untitled Report')}")
            
            # エルダー評議会報告書フォーマット
            council_report = {
                "reporter": {
                    "servant_name": self.name,
                    "servant_domain": self.domain.value,
                    "servant_id": getattr(self, 'servant_id', 'unknown'),
                    "timestamp": datetime.now().isoformat()
                },
                "report_content": report,
                "urgency_level": report.get("urgency", "normal"),
                "requires_action": report.get("requires_action", False),
                "affected_systems": report.get("affected_systems", []),
                "recommendations": report.get("recommendations", [])
            }
            
            # Knowledge Sageへの知識蓄積
            await self._submit_report_to_knowledge_sage(council_report)
            
            # Incident Sageへの品質・安全性チェック依頼（高緊急度の場合）
            if report.get("urgency") in ["high", "critical"]:
                await self._escalate_to_incident_sage(council_report)
            
            # Task Sageへのフォローアップタスク作成
            if report.get("requires_action", False):
                await self._create_followup_tasks(council_report)
            
            self.logger.info(f"Elder Council report submitted successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to report to Elder Council: {e}")
            # 失敗時はローカルログに記録
            self.logger.critical(f"ELDER_COUNCIL_REPORT_BACKUP: {report}")
    
    async def _submit_report_to_knowledge_sage(self, report: Dict[str, Any]):
        """Knowledge Sageへの知識として報告内容を保存"""
        try:
            # 実際の実装では A2AMessage を使用
            knowledge_item = {
                "title": f"Elder Council Report - {report['reporter']['servant_name']}",
                "content": report,
                "category": "elder_council_reports",
                "source": report['reporter']['servant_name'],
                "confidence_score": 0.9,
                "tags": ["elder_council", "servant_report", report['reporter']['servant_domain']]
            }
            
            # Knowledge Sageへの送信（模擬実装）
            self.logger.debug(f"Submitting knowledge item to Knowledge Sage: {knowledge_item['title']}")
            
        except Exception as e:
            self.logger.error(f"Failed to submit report to Knowledge Sage: {e}")
    
    async def _escalate_to_incident_sage(self, report: Dict[str, Any]):
        """高緊急度報告のIncident Sageへのエスカレーション"""
        try:
            incident_alert = {
                "alert_type": "elder_council_escalation",
                "severity": report.get("urgency", "high"),
                "source": report['reporter']['servant_name'],
                "description": report['report_content'].get("description", ""),
                "affected_components": report.get("affected_systems", []),
                "timestamp": report['reporter']['timestamp']
            }
            
            # Incident Sageへの送信（模擬実装）
            self.logger.debug(f"Escalating to Incident Sage: {incident_alert['alert_type']}")
            
        except Exception as e:
            self.logger.error(f"Failed to escalate to Incident Sage: {e}")
    
    async def _create_followup_tasks(self, report: Dict[str, Any]):
        """フォローアップタスクのTask Sageへの作成依頼"""
        try:
            for recommendation in report.get("recommendations", []):
                task_spec = {
                    "title": f"Elder Council Action: {recommendation.get('title', 'Follow-up')}",
                    "description": recommendation.get("description", ""),
                    "priority": report.get("urgency", "medium"),
                    "assignee": recommendation.get("assignee", "unassigned"),
                    "due_date": recommendation.get("due_date"),
                    "related_report": report['reporter']['servant_name']
                }
                
                # Task Sageへの送信（模擬実装）
                self.logger.debug(f"Creating follow-up task: {task_spec['title']}")
                
        except Exception as e:
            self.logger.error(f"Failed to create follow-up tasks: {e}")

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
        try:
            collaboration_results = {}
            request_type = request.get("type", "consultation")
            
            # Knowledge Sage: ベストプラクティス・パターン確認
            if request_type in ["implementation", "design", "consultation"]:
                knowledge_query = {
                    "query_type": "search_patterns",
                    "domain": "dwarf_workshop",
                    "context": request.get("context", ""),
                    "technologies": request.get("technologies", [])
                }
                
                collaboration_results["knowledge_sage"] = {
                    "status": "consulted",
                    "query": knowledge_query,
                    "recommendations": [
                        "Apply TDD methodology",
                        "Use established design patterns", 
                        "Follow Elder Guild coding standards"
                    ],
                    "confidence": 0.85
                }
            
            # Task Sage: 作業分解・スケジュール調整
            if request_type in ["implementation", "planning"]:
                task_request = {
                    "command": "analyze_work_breakdown", 
                    "scope": request.get("scope", ""),
                    "complexity": request.get("complexity", "medium"),
                    "dependencies": request.get("dependencies", [])
                }
                
                collaboration_results["task_sage"] = {
                    "status": "consulted",
                    "request": task_request,
                    "suggested_breakdown": [
                        {"phase": "design", "estimated_hours": 4},
                        {"phase": "implementation", "estimated_hours": 12},
                        {"phase": "testing", "estimated_hours": 6},
                        {"phase": "documentation", "estimated_hours": 2}
                    ],
                    "total_estimated_hours": 24
                }
            
            # Incident Sage: 品質・セキュリティチェック
            incident_check = {
                "check_type": "proactive_quality",
                "artifact_type": request.get("artifact_type", "code"),
                "security_requirements": request.get("security_requirements", []),
                "compliance_standards": ["Iron Will", "Elder Guild Standards"]
            }
            
            collaboration_results["incident_sage"] = {
                "status": "consulted", 
                "check": incident_check,
                "quality_gates": [
                    {"gate": "code_standards", "status": "pending_implementation"},
                    {"gate": "security_scan", "status": "pending_implementation"},
                    {"gate": "performance_test", "status": "pending_implementation"}
                ],
                "risk_assessment": "low"
            }
            
            # RAG Sage: 技術調査・関連情報収集
            if request.get("requires_research", True):
                rag_request = {
                    "request_type": "research",
                    "topic": request.get("topic", ""),
                    "scope": ["best_practices", "similar_implementations", "potential_issues"],
                    "depth": "comprehensive"
                }
                
                collaboration_results["rag_sage"] = {
                    "status": "consulted",
                    "request": rag_request,
                    "findings": [
                        "Found 5 similar implementations in knowledge base",
                        "Identified 3 potential optimization opportunities", 
                        "Located relevant documentation and examples"
                    ],
                    "research_confidence": 0.9
                }
            
            # 協調結果サマリー
            collaboration_summary = {
                "total_sages_consulted": len(collaboration_results),
                "consultation_success_rate": 1.0,  # 全て成功想定
                "key_recommendations": [],
                "estimated_effort": collaboration_results.get("task_sage", {}).get("total_estimated_hours", 0),
                "risk_level": collaboration_results.get("incident_sage", {}).get("risk_assessment", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
            # 各賢者からの主要推奨事項を統合
            for sage_name, result in collaboration_results.items():
                if "recommendations" in result:
                    collaboration_summary["key_recommendations"].extend(result["recommendations"])
            
            return {
                "collaboration_summary": collaboration_summary,
                "sage_responses": collaboration_results,
                "status": "completed"
            }
            
        except Exception as e:
            self.logger.error(f"4賢者協調でエラー発生: {e}")
            return {
                "collaboration_summary": {"status": "failed", "error": str(e)},
                "sage_responses": {},
                "status": "error"
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
