"""
エルダーサーバント基盤クラスのテストスイート
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import uuid

from libs.elder_servants.base.elder_servant import (
    ElderServant, ServantCategory, TaskStatus, TaskPriority,
    ServantCapability, TaskResult, ServantRegistry
)


class MockElderServant(ElderServant):
    """テスト用モックサーバント"""
    
    def __init__(self, servant_id: str = "TEST001", servant_name: str = "TestServant"):
        capabilities = [
            ServantCapability("test_capability", "Test capability", ["test"], ["result"], 1)
        ]
        super().__init__(
            servant_id=servant_id,
            servant_name=servant_name,
            category=ServantCategory.DWARF,
            specialization="testing",
            capabilities=capabilities
        )
        self.execute_task_called = False
        self.mock_result_data = {"status": "completed", "data": "test_result"}
        self.mock_quality_score = 95.0
        
    async def execute_task(self, task: dict) -> TaskResult:
        """タスク実行のモック実装"""
        self.execute_task_called = True
        
        # エラーシミュレーション
        if task.get("force_error"):
            return TaskResult(
                task_id=task.get("task_id", str(uuid.uuid4())),
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                error_message="Forced error for testing",
                execution_time_ms=100.0,
                quality_score=0.0
            )
        
        # 成功ケース
        return TaskResult(
            task_id=task.get("task_id", str(uuid.uuid4())),
            servant_id=self.servant_id,
            status=TaskStatus.COMPLETED,
            result_data=self.mock_result_data,
            execution_time_ms=150.0,
            quality_score=self.mock_quality_score
        )
    
    def get_specialized_capabilities(self) -> list:
        """専門能力取得のモック実装"""
        return [
            ServantCapability("mock_special", "Mock special capability", ["input"], ["output"], 2)
        ]


class TestServantCapability:
    """ServantCapabilityクラスのテスト"""
    
    def test_capability_creation(self):
        """能力定義の作成テスト"""
        cap = ServantCapability(
            name="test_cap",
            description="Test capability",
            input_types=["text", "json"],
            output_types=["result"],
            complexity=5
        )
        
        assert cap.name == "test_cap"
        assert cap.description == "Test capability"
        assert cap.input_types == ["text", "json"]
        assert cap.output_types == ["result"]
        assert cap.complexity == 5
    
    def test_capability_to_dict(self):
        """能力定義の辞書変換テスト"""
        cap = ServantCapability(
            name="test_cap",
            description="Test capability",
            input_types=["text"],
            output_types=["result"],
            complexity=3
        )
        
        cap_dict = cap.to_dict()
        assert cap_dict["name"] == "test_cap"
        assert cap_dict["description"] == "Test capability"
        assert cap_dict["input_types"] == ["text"]
        assert cap_dict["output_types"] == ["result"]
        assert cap_dict["complexity"] == 3


class TestTaskResult:
    """TaskResultクラスのテスト"""
    
    def test_task_result_creation(self):
        """タスク結果の作成テスト"""
        result = TaskResult(
            task_id="task123",
            servant_id="SERV001",
            status=TaskStatus.COMPLETED,
            result_data={"key": "value"},
            execution_time_ms=250.5,
            quality_score=97.5
        )
        
        assert result.task_id == "task123"
        assert result.servant_id == "SERV001"
        assert result.status == TaskStatus.COMPLETED
        assert result.result_data == {"key": "value"}
        assert result.execution_time_ms == 250.5
        assert result.quality_score == 97.5
        assert result.error_message is None
        assert isinstance(result.completed_at, datetime)
    
    def test_task_result_with_error(self):
        """エラー付きタスク結果のテスト"""
        result = TaskResult(
            task_id="task456",
            servant_id="SERV002",
            status=TaskStatus.FAILED,
            error_message="Something went wrong",
            execution_time_ms=50.0,
            quality_score=0.0
        )
        
        assert result.status == TaskStatus.FAILED
        assert result.error_message == "Something went wrong"
        assert result.quality_score == 0.0
    
    def test_task_result_to_dict(self):
        """タスク結果の辞書変換テスト"""
        result = TaskResult(
            task_id="task789",
            servant_id="SERV003",
            status=TaskStatus.COMPLETED,
            result_data={"success": True},
            execution_time_ms=100.0,
            quality_score=98.0
        )
        
        result_dict = result.to_dict()
        assert result_dict["task_id"] == "task789"
        assert result_dict["servant_id"] == "SERV003"
        assert result_dict["status"] == "completed"
        assert result_dict["result_data"] == {"success": True}
        assert result_dict["execution_time_ms"] == 100.0
        assert result_dict["quality_score"] == 98.0
        assert "completed_at" in result_dict


class TestElderServant:
    """ElderServant基盤クラスのテスト"""
    
    @pytest.fixture
    def servant(self):
        """テスト用サーバントフィクスチャ"""
        return MockElderServant()
    
    def test_servant_initialization(self, servant):
        """サーバント初期化テスト"""
        assert servant.servant_id == "TEST001"
        assert servant.servant_name == "TestServant"
        assert servant.category == ServantCategory.DWARF
        assert servant.specialization == "testing"
        assert len(servant.capabilities) == 1
        assert servant.quality_threshold == 95.0
        assert servant.stats["tasks_executed"] == 0
        assert servant.stats["tasks_succeeded"] == 0
        assert servant.stats["tasks_failed"] == 0
    
    @pytest.mark.asyncio
    async def test_process_request_execute_task(self, servant):
        """タスク実行リクエストのテスト"""
        request = {
            "type": "execute_task",
            "task": {
                "task_id": "test_task_001",
                "type": "test",
                "data": "test_data"
            }
        }
        
        response = await servant.process_request(request)
        
        assert response["success"] is True
        assert "result" in response
        assert response["result"]["status"] == "completed"
        assert servant.execute_task_called is True
        assert servant.stats["tasks_executed"] == 1
        assert servant.stats["tasks_succeeded"] == 1
    
    @pytest.mark.asyncio
    async def test_process_request_execute_task_failure(self, servant):
        """タスク実行失敗のテスト"""
        request = {
            "type": "execute_task",
            "task": {
                "task_id": "test_task_002",
                "force_error": True
            }
        }
        
        response = await servant.process_request(request)
        
        assert response["success"] is True
        assert response["result"]["status"] == "failed"
        assert response["result"]["error_message"] == "Forced error for testing"
        assert servant.stats["tasks_executed"] == 1
        assert servant.stats["tasks_failed"] == 1
    
    @pytest.mark.asyncio
    async def test_health_check(self, servant):
        """ヘルスチェックのテスト"""
        # 初期状態
        health = await servant.health_check()
        
        assert health["success"] is True
        assert health["servant_id"] == "TEST001"
        assert health["servant_name"] == "TestServant"
        assert health["category"] == "dwarf"
        assert health["specialization"] == "testing"
        assert health["status"] == "healthy"
        assert health["current_tasks"] == 0
        assert health["stats"]["tasks_executed"] == 0
        assert health["stats"]["success_rate"] == 100.0
        
        # タスク実行後
        await servant.process_request({
            "type": "execute_task",
            "task": {"task_id": "test_health"}
        })
        
        health_after = await servant.health_check()
        assert health_after["stats"]["tasks_executed"] == 1
        assert health_after["stats"]["success_rate"] == 100.0
        assert health_after["stats"]["average_quality_score"] == 95.0
        assert health_after["stats"]["quality_status"] == "excellent"
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, servant):
        """能力取得のテスト"""
        response = await servant.process_request({"type": "get_capabilities"})
        
        assert response["success"] is True
        assert "capabilities" in response
        capabilities = response["capabilities"]
        
        # 基本能力 + 専門能力
        assert len(capabilities) >= 4  # 3 base + 1 specialized
        
        # 基本能力の確認
        cap_names = [cap["name"] for cap in capabilities]
        assert "health_check" in cap_names
        assert "task_execution" in cap_names
        assert "quality_validation" in cap_names
        assert "mock_special" in cap_names
    
    @pytest.mark.asyncio
    async def test_get_stats(self, servant):
        """統計情報取得のテスト"""
        response = await servant.process_request({"type": "get_stats"})
        
        assert response["success"] is True
        assert "stats" in response
        stats = response["stats"]
        
        assert stats["tasks_executed"] == 0
        assert stats["tasks_succeeded"] == 0
        assert stats["tasks_failed"] == 0
        assert stats["average_quality_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, servant):
        """タスクキャンセルのテスト"""
        # 存在しないタスクのキャンセル
        response = await servant.process_request({
            "type": "cancel_task",
            "task_id": "non_existent"
        })
        
        assert response["success"] is False
        assert "not found" in response["error"]
        
        # タスクを追加してキャンセル
        servant.current_tasks["task_to_cancel"] = {
            "status": TaskStatus.RUNNING,
            "started_at": datetime.now()
        }
        
        response = await servant.process_request({
            "type": "cancel_task",
            "task_id": "task_to_cancel"
        })
        
        assert response["success"] is True
        assert "task_to_cancel" not in servant.current_tasks
    
    @pytest.mark.asyncio
    async def test_unknown_request_type(self, servant):
        """未知のリクエストタイプのテスト"""
        response = await servant.process_request({"type": "unknown_type"})
        
        assert response["success"] is False
        assert "Unknown request type" in response["error"]
        assert "supported_types" in response
    
    @pytest.mark.asyncio
    async def test_collaborate_with_sages(self, servant):
        """4賢者との連携テスト"""
        request = {
            "type": "test_collaboration",
            "request_id": "collab_001"
        }
        
        result = await servant.collaborate_with_sages("knowledge", request)
        
        assert result["success"] is True
        assert result["sage_type"] == "knowledge"
        assert "request_id" in result
    
    @pytest.mark.asyncio
    async def test_validate_iron_will_quality(self, servant):
        """Iron Will品質基準検証のテスト"""
        # 高品質データ
        high_quality_data = {
            "success": True,
            "status": "completed",
            "data": {"result": "value"},
            "execution_time_ms": 1000
        }
        
        score = await servant.validate_iron_will_quality(high_quality_data)
        assert score == 100.0
        
        # 低品質データ
        low_quality_data = {
            "success": False,
            "error": "Something failed"
        }
        
        score = await servant.validate_iron_will_quality(low_quality_data)
        assert score < 50.0
    
    def test_string_representation(self, servant):
        """文字列表現のテスト"""
        assert str(servant) == "TestServant(TEST001)"
        assert repr(servant) == "<ElderServant TestServant category=dwarf tasks=0>"


class TestServantRegistry:
    """ServantRegistryクラスのテスト"""
    
    @pytest.fixture
    def registry(self):
        """テスト用レジストリフィクスチャ"""
        return ServantRegistry()
    
    @pytest.fixture
    def servants(self):
        """テスト用サーバント群"""
        return [
            MockElderServant("DWARF001", "CodeCrafter"),
            MockElderServant("DWARF002", "TestForge"),
            MockElderServant("WIZARD001", "TechScout"),
        ]
    
    def test_register_servant(self, registry, servants):
        """サーバント登録のテスト"""
        for servant in servants:
            registry.register_servant(servant)
        
        assert len(registry.servants) == 3
        assert "DWARF001" in registry.servants
        assert registry.servants["DWARF001"].servant_name == "CodeCrafter"
    
    def test_get_servant(self, registry, servants):
        """サーバント取得のテスト"""
        registry.register_servant(servants[0])
        
        servant = registry.get_servant("DWARF001")
        assert servant is not None
        assert servant.servant_name == "CodeCrafter"
        
        non_existent = registry.get_servant("INVALID")
        assert non_existent is None
    
    def test_get_servants_by_category(self, registry, servants):
        """カテゴリ別サーバント取得のテスト"""
        for servant in servants:
            registry.register_servant(servant)
        
        dwarf_servants = registry.get_servants_by_category(ServantCategory.DWARF)
        assert len(dwarf_servants) == 3  # すべてDWARFカテゴリ
    
    def test_get_servants_by_specialization(self, registry, servants):
        """専門分野別サーバント取得のテスト"""
        for servant in servants:
            registry.register_servant(servant)
        
        testing_servants = registry.get_servants_by_specialization("testing")
        assert len(testing_servants) == 3  # すべて"testing"専門
    
    def test_find_best_servant_for_task(self, registry, servants):
        """タスクに最適なサーバント選出のテスト"""
        # 異なる専門分野を設定
        servants[0].specialization = "code_generation"
        servants[1].specialization = "testing"
        servants[2].specialization = "research"
        
        for servant in servants:
            registry.register_servant(servant)
        
        # テスト関連タスク
        test_task = {
            "type": "test",
            "required_capability": "testing"
        }
        
        best = registry.find_best_servant_for_task(test_task)
        assert best is not None
        assert best.specialization == "testing"
        
        # 該当なしタスク
        unknown_task = {
            "type": "unknown",
            "required_capability": "non_existent"
        }
        
        best = registry.find_best_servant_for_task(unknown_task)
        assert best is not None  # 最も負荷の低いサーバントが選ばれる
    
    @pytest.mark.asyncio
    async def test_execute_task_with_best_servant(self, registry, servants):
        """最適サーバントでのタスク実行テスト"""
        for servant in servants:
            registry.register_servant(servant)
        
        task = {
            "task_id": "best_exec_001",
            "type": "test",
            "required_capability": "testing"
        }
        
        result = await registry.execute_task_with_best_servant(task)
        
        assert result.status == TaskStatus.COMPLETED
        assert result.quality_score == 95.0
    
    @pytest.mark.asyncio
    async def test_execute_task_no_servant(self, registry):
        """サーバントなしでのタスク実行テスト"""
        task = {"task_id": "no_servant_001"}
        
        result = await registry.execute_task_with_best_servant(task)
        
        assert result.status == TaskStatus.FAILED
        assert "No suitable servant found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_broadcast_request(self, registry, servants):
        """ブロードキャストリクエストのテスト"""
        for servant in servants:
            registry.register_servant(servant)
        
        request = {"type": "health_check"}
        response = await registry.broadcast_request(request)
        
        assert response["success"] is True
        assert response["responded_servants"] == 3
        assert len(response["broadcast_results"]) == 3
        
        for servant_id, result in response["broadcast_results"].items():
            assert result["success"] is True
            assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_all(self, registry, servants):
        """全サーバントヘルスチェックのテスト"""
        for servant in servants:
            registry.register_servant(servant)
        
        health_report = await registry.health_check_all()
        
        assert health_report["total_servants"] == 3
        assert health_report["healthy_servants"] == 3
        assert health_report["health_rate"] == 100.0
        assert len(health_report["servants"]) == 3
        
        for servant_id, health in health_report["servants"].items():
            assert health["success"] is True
            assert health["status"] == "healthy"


class TestEnums:
    """Enumクラスのテスト"""
    
    def test_servant_category_enum(self):
        """サーバントカテゴリEnumのテスト"""
        assert ServantCategory.DWARF.value == "dwarf"
        assert ServantCategory.WIZARD.value == "wizard"
        assert ServantCategory.ELF.value == "elf"
    
    def test_task_status_enum(self):
        """タスクステータスEnumのテスト"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
    
    def test_task_priority_enum(self):
        """タスク優先度Enumのテスト"""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])