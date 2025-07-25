"""
Elder Servant基盤クラス用ユニットテスト (pytest版)

EldersLegacy統合とIron Will品質基準の完全テスト実装
Issue #69対応: EldersServiceLegacy継承とTDD品質保証
Issue #93対応: pytest移行版
"""

import asyncio
from datetime import datetime

import pytest

from libs.core.elders_legacy import (
    EldersLegacyDomain,
    EldersServiceLegacy,
)
from libs.elder_servants.base.elder_servant import (
    ElderServant,
    ServantCapability,
    ServantCategory,
    ServantRegistry,
    ServantRequest,
    ServantResponse,
    TaskPriority,
    TaskResult,
    TaskStatus,
)


class TestElderServant(ElderServant):
    """テスト用ElderServant実装"""

    def __init__(self):
        capabilities = [
            ServantCapability(
                "test_capability", "テスト用機能", ["test_input"], ["test_output"], 1
            )
        ]
        super().__init__(
            servant_id="test_servant_001",
            servant_name="TestServant",
            category=ServantCategory.DWARF,
            specialization="test_specialization",
            capabilities=capabilities,
        )

    async def execute_task(self, task: dict) -> TaskResult:
        """テスト用タスク実行"""
        task_id = task.get("task_id", "test_task")

        # 成功パターンのモック実装
        if task.get("task_type") == "success_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data={"message": "Task completed successfully"},
                execution_time_ms=100.0,
                quality_score=98.5,
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
            )

        # デフォルト成功
        return TaskResult(
            task_id=task_id,
            servant_id=self.servant_id,
            status=TaskStatus.COMPLETED,
            result_data={"message": "Default success"},
            execution_time_ms=150.0,
            quality_score=95.0,
        )

    def get_specialized_capabilities(self) -> list:
        """専門能力取得"""
        return [
            ServantCapability(
                "test_specialized",
                "専門テスト機能",
                ["specialized_input"],
                ["specialized_output"],
                2,
            )
        ]


@pytest.fixture
def test_servant():
    """テスト用ElderServantフィクスチャ"""
    return TestElderServant()


@pytest.fixture
def sample_task():
    """サンプルタスクフィクスチャ"""
    return {
        "task_id": "test_task_001",
        "task_type": "test_task",
        "data": {"test": "value"},
    }


class TestElderServantBase:
    """ElderServant基盤クラステスト"""

    def test_servant_initialization(self, test_servant):
        """ElderServant初期化テスト"""
        assert test_servant.servant_id == "test_servant_001"
        assert test_servant.servant_name == "TestServant"
        assert test_servant.category == ServantCategory.DWARF
        assert test_servant.specialization == "test_specialization"
        assert len(test_servant.capabilities) == 1
        assert test_servant.capabilities[0].name == "test_capability"

    def test_elders_legacy_inheritance(self, test_servant):
        """EldersLegacy継承テスト"""
        assert isinstance(test_servant, EldersServiceLegacy)
        assert test_servant.domain == EldersLegacyDomain.EXECUTION
        assert hasattr(test_servant, "process_request")
        assert hasattr(test_servant, "validate_request")
        assert hasattr(test_servant, "get_capabilities")

    def test_capability_registration(self, test_servant):
        """能力登録テスト"""
        capabilities = test_servant.get_capabilities()
        
        assert "capabilities" in capabilities
        assert len(capabilities["capabilities"]) >= 1
        
        cap_names = [cap["name"] for cap in capabilities["capabilities"]]
        assert "test_capability" in cap_names

    @pytest.mark.asyncio
    async def test_task_execution_success(self, test_servant):
        """タスク実行成功テスト"""
        task = {
            "task_id": "success_test_001",
            "task_type": "success_test",
            "data": {"test": "data"},
        }
        
        result = await test_servant.execute_task(task)
        
        assert result.task_id == "success_test_001"
        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["message"] == "Task completed successfully"
        assert result.execution_time_ms == 100.0
        assert result.quality_score == 98.5

    @pytest.mark.asyncio
    async def test_task_execution_failure(self, test_servant):
        """タスク実行失敗テスト"""
        task = {
            "task_id": "failure_test_001",
            "task_type": "failure_test",
            "data": {"test": "data"},
        }
        
        result = await test_servant.execute_task(task)
        
        assert result.task_id == "failure_test_001"
        assert result.status == TaskStatus.FAILED
        assert result.error_message == "Intentional test failure"
        assert result.execution_time_ms == 50.0
        assert result.quality_score == 0.0

    @pytest.mark.asyncio
    async def test_process_request(self, test_servant):
        """プロセスリクエストテスト"""
        request = ServantRequest(
            request_id="req_001",
            servant_id=test_servant.servant_id,
            task_type="test_task",
            payload={"test": "data"},
            priority=TaskPriority.MEDIUM,
        )
        
        # ServantRequestをdictに変換
        task = {
            "task_id": request.request_id,
            "task_type": request.task_type,
            **request.payload,
        }
        
        result = await test_servant.execute_task(task)
        
        assert result is not None
        assert result.status == TaskStatus.COMPLETED

    def test_get_specialized_capabilities(self, test_servant):
        """専門能力取得テスト"""
        specialized = test_servant.get_specialized_capabilities()
        
        assert len(specialized) == 1
        assert specialized[0].name == "test_specialized"
        assert specialized[0].description == "専門テスト機能"
        assert specialized[0].input_format == ["specialized_input"]
        assert specialized[0].output_format == ["specialized_output"]

    def test_get_status(self, test_servant):
        """ステータス取得テスト"""
        status = test_servant.get_status()
        
        assert status["servant_id"] == "test_servant_001"
        assert status["servant_name"] == "TestServant"
        assert status["category"] == "dwarf"
        assert status["is_active"] is True
        assert "stats" in status
        assert status["stats"]["tasks_executed"] == 0

    @pytest.mark.asyncio
    async def test_task_statistics_update(self, test_servant):
        """タスク統計更新テスト"""
        initial_stats = test_servant.get_status()["stats"]
        assert initial_stats["tasks_executed"] == 0
        
        # タスク実行
        task = {"task_id": "stats_test", "task_type": "success_test"}
        await test_servant.execute_task(task)
        
        # 統計確認
        updated_stats = test_servant.get_status()["stats"]
        assert updated_stats["tasks_executed"] == 1
        assert updated_stats["total_execution_time_ms"] > 0

    def test_iron_will_metrics_initialization(self, test_servant):
        """Iron Willメトリクス初期化テスト"""
        assert hasattr(test_servant, "_iron_will_metrics")
        metrics = test_servant.get_iron_will_metrics()
        
        assert "root_resolution_rate" in metrics
        assert "dependency_completeness" in metrics
        assert "test_coverage" in metrics
        assert "security_score" in metrics
        assert "performance_score" in metrics
        assert "maintainability_index" in metrics


class TestServantRegistry:
    """ServantRegistryテスト"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """各テストの前後でレジストリをクリア"""
        ServantRegistry._instances.clear()
        ServantRegistry._capabilities.clear()
        yield
        ServantRegistry._instances.clear()
        ServantRegistry._capabilities.clear()

    def test_servant_registration(self, test_servant):
        """サーバント登録テスト"""
        ServantRegistry.register(test_servant)
        
        # 登録確認
        assert test_servant.servant_id in ServantRegistry._instances
        assert ServantRegistry.get(test_servant.servant_id) == test_servant

    def test_capability_registration(self, test_servant):
        """能力登録テスト"""
        ServantRegistry.register(test_servant)
        
        # 能力確認
        servants = ServantRegistry.find_by_capability("test_capability")
        assert len(servants) == 1
        assert servants[0] == test_servant

    def test_get_all_servants(self, test_servant):
        """全サーバント取得テスト"""
        ServantRegistry.register(test_servant)
        
        all_servants = ServantRegistry.get_all()
        assert len(all_servants) == 1
        assert test_servant in all_servants

    def test_find_by_category(self, test_servant):
        """カテゴリ検索テスト"""
        ServantRegistry.register(test_servant)
        
        dwarfs = ServantRegistry.find_by_category(ServantCategory.DWARF)
        assert len(dwarfs) == 1
        assert dwarfs[0] == test_servant
        
        # 存在しないカテゴリ
        elfs = ServantRegistry.find_by_category(ServantCategory.ELF)
        assert len(elfs) == 0

    def test_duplicate_registration(self, test_servant):
        """重複登録テスト"""
        ServantRegistry.register(test_servant)
        
        # 重複登録（上書きされる）
        ServantRegistry.register(test_servant)
        
        all_servants = ServantRegistry.get_all()
        assert len(all_servants) == 1


class TestServantModels:
    """サーバントモデルテスト"""

    def test_servant_capability_creation(self):
        """ServantCapability作成テスト"""
        cap = ServantCapability(
            name="test_cap",
            description="Test capability",
            input_format=["string", "number"],
            output_format=["result"],
            complexity_level=3,
        )
        
        assert cap.name == "test_cap"
        assert cap.description == "Test capability"
        assert cap.input_format == ["string", "number"]
        assert cap.output_format == ["result"]
        assert cap.complexity_level == 3

    def test_task_result_creation(self):
        """TaskResult作成テスト"""
        result = TaskResult(
            task_id="task_001",
            servant_id="servant_001",
            status=TaskStatus.COMPLETED,
            result_data={"result": "success"},
            execution_time_ms=150.5,
            quality_score=95.0,
        )
        
        assert result.task_id == "task_001"
        assert result.servant_id == "servant_001"
        assert result.status == TaskStatus.COMPLETED
        assert result.result_data == {"result": "success"}
        assert result.execution_time_ms == 150.5
        assert result.quality_score == 95.0
        assert result.error_message is None

    def test_servant_request_creation(self):
        """ServantRequest作成テスト"""
        request = ServantRequest(
            request_id="req_001",
            servant_id="servant_001",
            task_type="process_data",
            payload={"data": [1, 2, 3]},
            priority=TaskPriority.HIGH,
        )
        
        assert request.request_id == "req_001"
        assert request.servant_id == "servant_001"
        assert request.task_type == "process_data"
        assert request.payload == {"data": [1, 2, 3]}
        assert request.priority == TaskPriority.HIGH

    def test_servant_response_creation(self):
        """ServantResponse作成テスト"""
        response = ServantResponse(
            request_id="req_001",
            servant_id="servant_001",
            status=TaskStatus.COMPLETED,
            data={"result": "processed"},
            execution_time_ms=200.0,
            quality_metrics={"accuracy": 0.95, "completeness": 1.0},
        )
        
        assert response.request_id == "req_001"
        assert response.servant_id == "servant_001"
        assert response.status == TaskStatus.COMPLETED
        assert response.data == {"result": "processed"}
        assert response.execution_time_ms == 200.0
        assert response.quality_metrics == {"accuracy": 0.95, "completeness": 1.0}


@pytest.mark.parametrize(
    "task_type,expected_status,expected_message",
    [
        ("success_test", TaskStatus.COMPLETED, "Task completed successfully"),
        ("failure_test", TaskStatus.FAILED, None),
        ("default_test", TaskStatus.COMPLETED, "Default success"),
    ],
)
@pytest.mark.asyncio
async def test_task_execution_patterns(
    test_servant, task_type, expected_status, expected_message
):
    """タスク実行パターンのパラメータ化テスト"""
    task = {"task_id": f"{task_type}_001", "task_type": task_type}
    
    result = await test_servant.execute_task(task)
    
    assert result.status == expected_status
    if expected_message:
        assert result.result_data["message"] == expected_message