"""
統合Elder Servant基盤システム用包括的テストスイート

EldersLegacy継承システム完全実装の検証
Iron Will品質基準の95%カバレッジテスト
"""

import unittest
from datetime import datetime
from typing import Dict, Any, List

from libs.elder_servants.base.unified_elder_servant import (
    UnifiedElderServant,
    DwarfWorkshopServant,
    RAGWizardServant,
    ElfForestServant,
    IncidentKnightServant,
    ServantRegistry,
    ServantCategory,
    ServantDomain,
    ServantCapability,
    ServantRequest,
    ServantResponse,
    TaskStatus,
    TaskPriority,
    TaskResult,
    IronWillMetrics,
    iron_will_quality_gate,
    unified_servant_registry,
)
from libs.core.elders_legacy import EldersLegacyDomain, EldersServiceLegacy


class TestUnifiedElderServant(UnifiedElderServant):
    """テスト用統合ElderServant実装"""

    def __init__(self):
        capabilities = [
            ServantCapability(
                "test_capability", 
                "テスト用機能", 
                ["test_input"], 
                ["test_output"], 
                1,
                ServantDomain.DWARF_WORKSHOP
            )
        ]
        super().__init__(
            servant_id="test_unified_001",
            servant_name="TestUnifiedServant",
            category=ServantCategory.DWARF,
            domain=ServantDomain.DWARF_WORKSHOP,
            specialization="test_specialization",
            capabilities=capabilities,
        )

    async def execute_task(self, task: Dict[str, Any]) -> TaskResulttask_id = task.get("task_id", "test_task"):
    """スト用タスク実行"""

        # 成功パターンのモック実装:
        if task.get("task_type") == "success_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data={
                    "success": True,
                    "status": "completed",
                    "data": {"message": "Task completed successfully"},
                    "execution_time_ms": 100,
                },
                execution_time_ms=100.0,
                quality_score=98.5,
                iron_will_compliant=True,
            )

        # 失敗パターンのモック実装
        elif task.get("task_type") == "failure_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                error_message="Intentional test failure",
                execution_time_ms=50.0,
                quality_score=0.0,
                iron_will_compliant=False,
            )

        # Iron Will品質テスト
        elif task.get("task_type") == "iron_will_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data={
                    "success": True,
                    "status": "completed",
                    "data": {"result": "excellent"},
                    "execution_time_ms": 80,
                },
                execution_time_ms=80.0,
                quality_score=96.0,
                iron_will_compliant=True,
            )

        # デフォルト成功
        return TaskResult(
            task_id=task_id,
            servant_id=self.servant_id,
            status=TaskStatus.COMPLETED,
            result_data={
                "success": True,
                "status": "completed", 
                "data": {"message": "Default success"},
                "execution_time_ms": 150,
            },
            execution_time_ms=150.0,
            quality_score=95.0,
            iron_will_compliant=True,
        )

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """専門能力取得"""
        return [
            ServantCapability(
                "test_specialized",
                "専門テスト機能",
                ["specialized_input"],
                ["specialized_output"],
                2,
                self.domain,
            )
        ]


class TestUnifiedElderServantBase(unittest.TestCase):
    """統合ElderServant基盤クラステスト"""

    def setUp(self)self.servant = TestUnifiedElderServant()
    """テストセットアップ"""

    def test_unified_elder_servant_initialization(self):
        """統合ElderServant初期化テスト"""
        # 基本プロパティ確認
        self.assertEqual(self.servant.servant_id, "test_unified_001")
        self.assertEqual(self.servant.servant_name, "TestUnifiedServant")
        self.assertEqual(self.servant.category, ServantCategory.DWARF)
        self.assertEqual(self.servant.servant_domain, ServantDomain.DWARF_WORKSHOP)
        self.assertEqual(self.servant.specialization, "test_specialization")

        # EldersServiceLegacy継承確認
        self.assertIsInstance(self.servant, EldersServiceLegacy)
        self.assertEqual(self.servant.domain, EldersLegacyDomain.EXECUTION)

        # Iron Will品質基準初期化確認
        self.assertIsInstance(self.servant._iron_will_metrics, IronWillMetrics)
        self.assertEqual(self.servant.quality_threshold, 95.0)

        # 統計初期化確認
        self.assertEqual(self.servant.stats["tasks_executed"], 0)
        self.assertEqual(self.servant.stats["tasks_succeeded"], 0)
        self.assertEqual(self.servant.stats["tasks_failed"], 0)

    def test_servant_capabilities_unified(self):
        """サーバント能力テスト（統合版）"""
        # 全能力取得
        all_capabilities = self.servant.get_all_capabilities()
        self.assertGreater(len(all_capabilities), 0)

        # 基本能力存在確認
        capability_names = [cap.name for cap in all_capabilities]
        self.assertIn("health_check", capability_names)
        self.assertIn("task_execution", capability_names)
        self.assertIn("quality_validation", capability_names)
        self.assertIn("sage_collaboration", capability_names)

        # 専門能力存在確認
        self.assertIn("test_specialized", capability_names)

        # EldersLegacy能力取得メソッド確認
        legacy_capabilities = self.servant.get_capabilities()
        self.assertIsInstance(legacy_capabilities, list)
        self.assertGreater(len(legacy_capabilities), 0)

    def test_iron_will_metrics_initialization(self):
        """Iron Willメトリクス初期化テスト"""
        metrics = self.servant._iron_will_metrics
        
        # 6大基準初期化確認
        self.assertEqual(metrics.root_cause_resolution, 0.0)
        self.assertEqual(metrics.dependency_completeness, 0.0)
        self.assertEqual(metrics.test_coverage, 0.0)
        self.assertEqual(metrics.security_score, 0.0)
        self.assertEqual(metrics.performance_score, 0.0)
        self.assertEqual(metrics.maintainability_score, 0.0)

        # メソッド確認
        self.assertEqual(metrics.get_overall_score(), 0.0)
        self.assertFalse(metrics.meets_iron_will_criteria())

        # 辞書変換確認
        metrics_dict = metrics.to_dict()
        self.assertIn("iron_will_compliant", metrics_dict)
        self.assertFalse(metrics_dict["iron_will_compliant"])


class TestUnifiedElderServantAsync(unittest.IsolatedAsyncioTestCase):
    """統合ElderServant非同期機能テスト"""

    async def asyncSetUp(self)self.servant = TestUnifiedElderServant()
    """非同期テストセットアップ"""

    async def test_process_request_success_unified(self):
        """正常リクエスト処理テスト（統合版）"""
        request = ServantRequest(
            task_id="unified_test_001",
            task_type="success_test",
            priority=TaskPriority.HIGH,
            payload={"data": "test_data"},
        )

        response = await self.servant.process_request(request)

        # レスポンス検証
        self.assertIsInstance(response, ServantResponse)
        self.assertEqual(response.task_id, "unified_test_001")
        self.assertEqual(response.servant_id, "test_unified_001")
        self.assertEqual(response.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(response.result_data)
        self.assertGreater(response.quality_score, 0)
        self.assertTrue(response.iron_will_compliant)

        # 統計更新確認
        self.assertEqual(self.servant.stats["tasks_executed"], 1)
        self.assertEqual(self.servant.stats["tasks_succeeded"], 1)

    async def test_process_request_failure_unified(self):
        """失敗リクエスト処理テスト（統合版）"""
        request = ServantRequest(
            task_id="unified_test_002",
            task_type="failure_test",
            priority=TaskPriority.MEDIUM,
            payload={"data": "failure_data"},
        )

        response = await self.servant.process_request(request)

        # レスポンス検証
        self.assertEqual(response.status, TaskStatus.FAILED)
        self.assertIsNotNone(response.error_message)
        self.assertEqual(response.quality_score, 0.0)
        self.assertFalse(response.iron_will_compliant)

        # 統計更新確認
        self.assertEqual(self.servant.stats["tasks_executed"], 1)
        self.assertEqual(self.servant.stats["tasks_failed"], 1)

    async def test_iron_will_quality_validation_unified(self):
        """Iron Will品質基準検証テスト（統合版）"""
        # 高品質データテスト
        high_quality_data = {
            "success": True,
            "status": "completed",
            "data": {"result": "excellent"},
            "execution_time_ms": 150,
        }

        is_compliant = await self.servant._validate_iron_will_quality(high_quality_data)
        self.assertTrue(is_compliant)

        # 低品質データテスト
        low_quality_data = {
            "success": False,
            "error": "Something went wrong",
            "execution_time_ms": 10000,  # 10秒 - 遅すぎ
        }

        is_compliant = await self.servant._validate_iron_will_quality(low_quality_data)
        self.assertFalse(is_compliant)

    async def test_execute_with_quality_gate(self):
        """品質ゲート付き実行テスト"""
        request = ServantRequest(
            task_id="quality_gate_001",
            task_type="iron_will_test",
            priority=TaskPriority.HIGH,
            payload={"quality_test": True},
        )

        # 品質ゲート付き実行
        response = await self.servant.execute_with_quality_gate(request)

        # 品質ゲート結果確認
        self.assertIsInstance(response, ServantResponse)
        self.assertEqual(response.status, TaskStatus.COMPLETED)
        self.assertTrue(response.iron_will_compliant)
        self.assertGreaterEqual(response.quality_score, 95.0)

    async def test_health_check_unified_legacy_integration(self):
        """統合ヘルスチェック（EldersLegacy統合版）"""
        # まずタスクを実行して統計を改善
        request = ServantRequest(
            task_id="health_prep_001",
            task_type="success_test",
            priority=TaskPriority.HIGH,
            payload={"prep": "health_check"},
        )
        await self.servant.process_request(request)

        health_result = await self.servant.health_check()

        # 基本構造確認
        self.assertIsInstance(health_result, dict)
        self.assertIn("status", health_result)
        self.assertIn("servant_id", health_result)

        # 統合ElderServant固有情報確認
        self.assertIn("servant_id", health_result)
        self.assertIn("servant_name", health_result)
        self.assertIn("category", health_result)
        self.assertIn("servant_domain", health_result)
        self.assertIn("specialization", health_result)
        self.assertIn("stats", health_result)
        self.assertIn("iron_will_metrics", health_result)
        self.assertIn("capabilities_count", health_result)
        self.assertIn("elders_legacy_compliant", health_result)

        # タスク実行後は健康状態が改善されていることを確認
        self.assertIn(health_result["status"], ["healthy", "degraded"])
        self.assertEqual(health_result["servant_id"], "test_unified_001")
        self.assertEqual(health_result["servant_domain"], "dwarf_workshop")
        self.assertTrue(health_result["elders_legacy_compliant"])
        self.assertGreater(health_result["stats"]["success_rate"], 0)

    async def test_sage_collaboration_enhanced(self):
        """4賢者連携テスト（強化版）"""
        request = {
            "type": "knowledge_request",
            "request_id": "collab_unified_001",
            "data": "test_collaboration_enhanced",
        }

        result = await self.servant.collaborate_with_sages("knowledge", request)

        # 連携結果確認
        self.assertTrue(result["success"])
        self.assertEqual(result["sage_type"], "knowledge")
        self.assertIn("request_id", result)
        self.assertIn("timestamp", result)
        self.assertTrue(result["iron_will_validated"])

        # 連携履歴確認
        self.assertIn("knowledge", self.servant.sage_connections)
        self.assertGreater(len(self.servant.sage_connections["knowledge"]), 0)

    async def test_iron_will_metrics_integration(self):
        """Iron Willメトリクス統合テスト"""
        # 初期状態確認
        initial_metrics = self.servant.get_iron_will_metrics()
        self.assertFalse(initial_metrics["iron_will_compliant"])

        # 高品質タスク実行
        request = ServantRequest(
            task_id="iron_will_integration_001",
            task_type="iron_will_test",
            priority=TaskPriority.CRITICAL,
            payload={"iron_will_test": True},
        )

        response = await self.servant.process_request(request)

        # Iron Will準拠確認
        self.assertTrue(response.iron_will_compliant)
        self.assertGreaterEqual(response.quality_score, 95.0)

        # メトリクス更新確認
        updated_metrics = self.servant.get_iron_will_metrics()
        self.assertGreater(updated_metrics["root_cause_resolution"], 0)


class TestSpecializedServants(unittest.IsolatedAsyncioTestCase):
    """特化サーバント基底クラステスト"""

    async def asyncSetUp(self)self.dwarf_servant = TestDwarfWorkshopServant()
    """特化サーバントテストセットアップ"""
        self.wizard_servant = TestRAGWizardServant()
        self.elf_servant = TestElfForestServant()
        self.knight_servant = TestIncidentKnightServant()

    async def test_dwarf_workshop_servant(self):
        """ドワーフ工房サーバントテスト"""
        # 基本プロパティ確認
        self.assertEqual(self.dwarf_servant.category, ServantCategory.DWARF)
        self.assertEqual(self.dwarf_servant.servant_domain, ServantDomain.DWARF_WORKSHOP)

        # 特化メソッドテスト
        result = await self.dwarf_servant.forge_and_craft({"item_type": "legendary_sword"})
        self.assertEqual(result["crafted_item"], "legendary_sword")
        self.assertEqual(result["quality"], "legendary")
        self.assertIn("completion_time", result)

    async def test_rag_wizard_servant(self):
        """RAGウィザーズサーバントテスト"""
        # 基本プロパティ確認
        self.assertEqual(self.wizard_servant.category, ServantCategory.WIZARD)
        self.assertEqual(self.wizard_servant.servant_domain, ServantDomain.RAG_WIZARDS)

        # 特化メソッドテスト
        result = await self.wizard_servant.research_and_analyze("AI Technology", "deep")
        self.assertEqual(result["research_topic"], "AI Technology")
        self.assertEqual(result["depth"], "deep")
        self.assertIn("completion_time", result)

    async def test_elf_forest_servant(self):
        """エルフの森サーバントテスト"""
        # 基本プロパティ確認
        self.assertEqual(self.elf_servant.category, ServantCategory.ELF)
        self.assertEqual(self.elf_servant.servant_domain, ServantDomain.ELF_FOREST)

        # 特化メソッドテスト
        result = await self.elf_servant.monitor_and_maintain("system_health")
        self.assertEqual(result["target"], "system_health")
        self.assertEqual(result["health_status"], "healthy")
        self.assertIn("completion_time", result)

    async def test_incident_knight_servant(self):
        """インシデント騎士団サーバントテスト"""
        # 基本プロパティ確認
        self.assertEqual(self.knight_servant.category, ServantCategory.KNIGHT)
        self.assertEqual(self.knight_servant.servant_domain, ServantDomain.INCIDENT_KNIGHTS)

        # 特化メソッドテスト
        incident = {"id": "INC001", "severity": "high", "description": "System down"}
        result = await self.knight_servant.respond_to_incident(incident)
        self.assertEqual(result["incident_id"], "INC001")
        self.assertEqual(result["response_status"], "handled")
        self.assertIn("completion_time", result)


class TestServantRegistry(unittest.IsolatedAsyncioTestCase):
    """統合ServantRegistryテスト"""

    async def asyncSetUp(self)self.registry = ServantRegistry()
    """レジストリテストセットアップ"""
        self.servant1 = TestUnifiedElderServant()
        self.servant2 = TestUnifiedElderServant()
        self.servant2.0servant_id = "test_unified_002"
        self.servant2.0servant_name = "TestUnifiedServant2"

    async def test_servant_registration_unified(self)self.registry.register_servant(self.servant1)
    """サーバント登録テスト（統合版）"""

        # 登録確認
        retrieved = self.registry.get_servant("test_unified_001")
        self.assertEqual(retrieved, self.servant1)

        # カテゴリインデックス確認
        dwarf_servants = self.registry.get_servants_by_category(ServantCategory.DWARF)
        self.assertIn(self.servant1, dwarf_servants)

        # ドメインインデックス確認
        workshop_servants = self.registry.get_servants_by_domain(ServantDomain.DWARF_WORKSHOP)
        self.assertIn(self.servant1, workshop_servants)

    async def test_execute_with_best_servant_unified(self)self.registry.register_servant(self.servant1)
    """最適サーバント実行テスト（統合版）"""
        self.registry.register_servant(self.servant2)

        request = ServantRequest(
            task_id="registry_unified_test_001",
            task_type="success_test",
            priority=TaskPriority.HIGH,
            payload={"data": "registry_test"},
        )

        response = await self.registry.execute_with_best_servant(request)

        # 実行結果確認
        self.assertIsInstance(response, ServantResponse)
        self.assertEqual(response.status, TaskStatus.COMPLETED)
        self.assertTrue(response.iron_will_compliant)

    async def test_health_check_all_servants_unified(self)self.registry.register_servant(self.servant1)
    """全サーバントヘルスチェックテスト（統合版）"""
        self.registry.register_servant(self.servant2)

        health_results = await self.registry.health_check_all()

        # 全体結果確認
        self.assertIn("total_servants", health_results)
        self.assertIn("healthy_servants", health_results)
        self.assertIn("iron_will_compliant_servants", health_results)
        self.assertIn("iron_will_compliance_rate", health_results)
        self.assertIn("elders_legacy_integrated", health_results)
        self.assertEqual(health_results["total_servants"], 2)
        self.assertTrue(health_results["elders_legacy_integrated"])

        # 個別結果確認
        self.assertIn("test_unified_001", health_results["servants"])
        self.assertIn("test_unified_002", health_results["servants"])

    async def test_find_best_servant_for_request(self)self.registry.register_servant(self.servant1)
    """最適サーバント選出テスト（強化版）"""
        self.registry.register_servant(self.servant2)

        # クリティカル優先度リクエスト
        critical_request = ServantRequest(
            task_id="critical_test_001",
            task_type="test_specialized",
            priority=TaskPriority.CRITICAL,
            payload={"urgent": True},
        )

        best_servant = self.registry.find_best_servant_for_request(critical_request)
        self.assertIsNotNone(best_servant)
        self.assertIn(best_servant, [self.servant1, self.servant2])


class TestIronWillDecorator(unittest.IsolatedAsyncioTestCase):
    """Iron Will品質ゲートデコレータテスト"""

    async def asyncSetUp(self)self.servant = TestUnifiedElderServant()
    """デコレータテストセットアップ"""

    async def test_iron_will_quality_gate_decorator(self):
        """Iron Will品質ゲートデコレータテスト"""
        
        @iron_will_quality_gate
        async def test_method(self):
            return {"success": True, "quality": "excellent"}

        # デコレータ適用メソッド実行
        result = await test_method(self.servant)
        self.assertEqual(result["success"], True)
        self.assertEqual(result["quality"], "excellent")


# テスト用特化サーバント実装

class TestDwarfWorkshopServant(DwarfWorkshopServant):
    """テスト用ドワーフ工房サーバント"""

    def __init__(self):
        capabilities = [
            ServantCapability(
                "forge_craft", 
                "鍛造・製作", 
                ["specification"], 
                ["crafted_item"], 
                3,
                ServantDomain.DWARF_WORKSHOP
            )
        ]
        super().__init__(
            servant_id="test_dwarf_001",
            servant_name="TestDwarfServant",
            specialization="legendary_crafting",
            capabilities=capabilities,
        )

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        return TaskResult(
            task_id=task.get("task_id", "dwarf_task"),
            servant_id=self.servant_id,
        """execute_taskを実行"""
            status=TaskStatus.COMPLETED,
            result_data={
                "success": True,
                "status": "completed",
                "data": {"forged": True},
                "execution_time_ms": 200,
            },
            quality_score=97.0,
            iron_will_compliant=True,
        )

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        return self.capabilities


class TestRAGWizardServant(RAGWizardServant):
    """テスト用RAGウィザーズサーバント"""

    def __init__(self):
        capabilities = [
            ServantCapability(
                "research_analyze", 
                "調査研究", 
                ["topic"], 
                ["analysis"], 
                4,
                ServantDomain.RAG_WIZARDS
            )
        ]
        super().__init__(
            servant_id="test_wizard_001",
            servant_name="TestWizardServant",
            specialization="deep_research",
            capabilities=capabilities,
        )

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        return TaskResult(
            task_id=task.get("task_id", "wizard_task"),
        """execute_taskを実行"""
            servant_id=self.servant_id,
            status=TaskStatus.COMPLETED,
            result_data={
                "success": True,
                "status": "completed",
                "data": {"researched": True},
                "execution_time_ms": 180,
            },
            quality_score=96.5,
            iron_will_compliant=True,
        )

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        return self.capabilities


class TestElfForestServant(ElfForestServant):
    """テスト用エルフの森サーバント"""

    def __init__(self):
        capabilities = [
            ServantCapability(
                "monitor_maintain", 
                "監視保守", 
                ["target"], 
                ["health_status"], 
                2,
                ServantDomain.ELF_FOREST
            )
        ]
        super().__init__(
            servant_id="test_elf_001",
            servant_name="TestElfServant",
            specialization="forest_guardian",
            capabilities=capabilities,
        )

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        return TaskResult(
        """execute_taskを実行"""
            task_id=task.get("task_id", "elf_task"),
            servant_id=self.servant_id,
            status=TaskStatus.COMPLETED,
            result_data={
                "success": True,
                "status": "completed",
                "data": {"monitored": True},
                "execution_time_ms": 120,
            },
            quality_score=95.5,
            iron_will_compliant=True,
        )

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        return self.capabilities


class TestIncidentKnightServant(IncidentKnightServant):
    """テスト用インシデント騎士団サーバント"""

    def __init__(self):
        capabilities = [
            ServantCapability(
                "respond_incident", 
                "緊急対応", 
                ["incident"], 
                ["response"], 
                5,
                ServantDomain.INCIDENT_KNIGHTS
            )
        ]
        super().__init__(
            servant_id="test_knight_001",
            servant_name="TestKnightServant",
            specialization="emergency_response",
            capabilities=capabilities,
        )

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """execute_taskを実行"""
        return TaskResult(
            task_id=task.get("task_id", "knight_task"),
            servant_id=self.servant_id,
            status=TaskStatus.COMPLETED,
            result_data={
                "success": True,
                "status": "completed",
                "data": {"responded": True},
                "execution_time_ms": 80,
            },
            quality_score=98.0,
            iron_will_compliant=True,
        )

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        return self.capabilities


if __name__ == "__main__":
    unittest.main()