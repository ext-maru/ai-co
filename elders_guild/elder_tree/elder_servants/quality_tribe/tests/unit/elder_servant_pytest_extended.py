#!/usr/bin/env python3
"""
Elder Servant拡張テストスイート (pytest版)
Issue #93: OSS移行プロジェクト - unittest → pytest

より包括的なElderServantテスト
"""

from typing import List

import pytest

from elders_guild.elder_tree.core.elders_legacy import EldersLegacyDomain, EldersServiceLegacy
from elders_guild.elder_tree.elder_servants.base.elder_servant import (
    ElderServant,
    ServantCapability,
    ServantCategory,
    ServantRequest,
    ServantResponse,
    TaskPriority,
    TaskResult,
    TaskStatus,
)


class TestElderServantExtended(ElderServant):
    """拡張テスト用ElderServant実装"""

    def __init__(self):
        capabilities = [
            ServantCapability(
                "test_capability", "テスト用機能", ["test_input"], ["test_output"], 1
            ),
            ServantCapability(
                "advanced_test", "高度テスト機能", ["complex_input"], ["complex_output"], 3
            )
        ]
        super().__init__(
            servant_id="test_servant_extended_001",
            servant_name="TestServantExtended",
            category=ServantCategory.DWARF,
            specialization="extended_test_specialization",
            capabilities=capabilities,
        )

    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """専門特化能力の取得"""
        return [
            ServantCapability(
                "test_specialized", "テスト専門能力", ["test_data"], ["test_result"], 2
            ),
            ServantCapability(
                "performance_test", "パフォーマンステスト", ["load_data"], ["metrics"], 4
            )
        ]

    async def execute_task(self, task: dict) -> TaskResult:
        """拡張テスト用タスク実行"""
        task_id = task.get("task_id", "test_task")
        task_type = task.get("task_type", "default")

        # より詳細なタスク処理シミュレーション
        if task_type == "success_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data={
                    "message": "success",
                    "processed": True,
                    "task_type": task_type,
                    "processing_details": {
                        "steps_completed": 5,
                        "validations_passed": 3,
                        "optimizations_applied": 2
                    }
                },
                quality_score=98.5,
                execution_time_ms=150.0,
            )
        elif task_type == "failure_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                result_data={},
                error_message="Simulated failure for testing",
                quality_score=0.0,
                execution_time_ms=75.0,
            )
        elif task_type == "warning_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data={
                    "message": "completed with warnings",
                    "warnings": ["Performance degradation detected", "Memory usage high"]
                },
                quality_score=88.0,  # Iron Will閾値未満
                execution_time_ms=300.0,
            )
        elif task_type == "performance_test":
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data={
                    "performance_metrics": {
                        "throughput": 1000,
                        "latency_ms": 50,
                        "cpu_usage": 45.2,
                        "memory_mb": 128
                    }
                },
                quality_score=96.8,
                execution_time_ms=100.0,
            )
        else:
            # デフォルト処理
            return TaskResult(
                task_id=task_id,
                servant_id=self.servant_id,
                status=TaskStatus.COMPLETED,
                result_data={"message": "default processing", "task_type": task_type},
                quality_score=95.0,
                execution_time_ms=100.0,
            )


@pytest.fixture
def extended_servant():
    """拡張テスト用ElderServantインスタンス"""
    return TestElderServantExtended()


@pytest.fixture
def success_request():
    """成功テスト用リクエスト"""
    return ServantRequest(
        task_id="req_success_001",
        task_type="success_test",
        priority=TaskPriority.HIGH,
        payload={"data": "test_data", "options": {"validate": True}},
        context={"user_id": "test_user", "session_id": "test_session"}
    )


@pytest.fixture
def failure_request():
    """失敗テスト用リクエスト"""
    return ServantRequest(
        task_id="req_failure_001",
        task_type="failure_test",
        priority=TaskPriority.MEDIUM,
        payload={"data": "failure_data"},
        context={"test_mode": True}
    )


class TestElderServantInitializationExtended:
    """Elder Servant初期化拡張テスト"""

    def test_extended_initialization(self, extended_servant):
        """拡張初期化テスト"""
        assert extended_servant.servant_id == "test_servant_extended_001"
        assert extended_servant.servant_name == "TestServantExtended"
        assert extended_servant.category == ServantCategory.DWARF
        assert extended_servant.specialization == "extended_test_specialization"

        # EldersServiceLegacy継承確認
        assert isinstance(extended_servant, EldersServiceLegacy)
        assert extended_servant.domain == EldersLegacyDomain.EXECUTION

        # 初期統計確認
        assert extended_servant.stats["tasks_executed"] == 0
        assert extended_servant.stats["tasks_succeeded"] == 0
        assert extended_servant.stats["tasks_failed"] == 0

    def test_capabilities_integration(self, extended_servant):
        """能力統合テスト"""
        all_capabilities = extended_servant.get_all_capabilities()
        capability_names = [cap.name for cap in all_capabilities]
        
        # 基本能力確認
        assert "health_check" in capability_names
        assert "task_execution" in capability_names
        assert "quality_validation" in capability_names
        
        # 専門能力確認
        assert "test_specialized" in capability_names
        assert "performance_test" in capability_names
        
        # EldersLegacy能力取得確認
        legacy_capabilities = extended_servant.get_capabilities()
        assert isinstance(legacy_capabilities, list)
        assert len(legacy_capabilities) > 0


class TestElderServantRequestProcessing:
    """ElderServant リクエスト処理テスト"""

    @pytest.mark.asyncio
    async def test_process_request_success(self, extended_servant, success_request):
        """成功リクエスト処理テスト"""
        response = await extended_servant.process_request(success_request)

        # レスポンス基本検証
        assert isinstance(response, ServantResponse)
        assert response.task_id == "req_success_001"
        assert response.servant_id == "test_servant_extended_001"
        assert response.status == TaskStatus.COMPLETED
        assert response.error_message is None or response.error_message == ""
        
        # 結果データ検証
        assert response.result_data is not None
        assert response.result_data["message"] == "success"
        assert response.result_data["processed"] is True
        assert "processing_details" in response.result_data
        
        # 品質検証
        assert response.quality_score >= extended_servant.quality_threshold
        assert response.execution_time_ms > 0

        # 統計更新確認
        assert extended_servant.stats["tasks_executed"] == 1
        assert extended_servant.stats["tasks_succeeded"] == 1
        assert extended_servant.stats["tasks_failed"] == 0

    @pytest.mark.asyncio
    async def test_process_request_failure(self, extended_servant, failure_request):
        """失敗リクエスト処理テスト"""
        response = await extended_servant.process_request(failure_request)

        # レスポンス検証
        assert isinstance(response, ServantResponse)
        assert response.task_id == "req_failure_001"
        assert response.status == TaskStatus.FAILED
        assert response.error_message is not None
        assert response.quality_score == 0.0

        # 統計更新確認
        assert extended_servant.stats["tasks_executed"] == 1
        assert extended_servant.stats["tasks_succeeded"] == 0
        assert extended_servant.stats["tasks_failed"] == 1

    @pytest.mark.asyncio
    async def test_process_request_validation(self, extended_servant):
        """リクエスト検証テスト"""
        # 無効なリクエスト（task_idなし）
        invalid_request = ServantRequest(
            task_id="",
            task_type="test",
            priority=TaskPriority.LOW,
            payload={}
        )
        
        # 検証メソッドテスト
        is_valid = extended_servant.validate_request(invalid_request)
        assert is_valid is False

        # 有効なリクエスト
        valid_request = ServantRequest(
            task_id="valid_001",
            task_type="test",
            priority=TaskPriority.MEDIUM,
            payload={"data": "valid"}
        )
        
        is_valid = extended_servant.validate_request(valid_request)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_concurrent_request_processing(self, extended_servant):
        """並行リクエスト処理テスト"""
        import asyncio
        
        # 複数リクエストを同時実行
        requests = [
            ServantRequest(
                task_id=f"concurrent_{i}",
                task_type="success_test",
                priority=TaskPriority.MEDIUM,
                payload={"index": i}
            )
            for i in range(3)
        ]
        
        # 並行実行
        responses = await asyncio.gather(
            *[extended_servant.process_request(req) for req in requests]
        )
        
        # 結果確認
        assert len(responses) == 3
        for i, response in enumerate(responses):
            assert response.task_id == f"concurrent_{i}"
            assert response.status == TaskStatus.COMPLETED
            
        # 統計確認
        assert extended_servant.stats["tasks_executed"] == 3
        assert extended_servant.stats["tasks_succeeded"] == 3


class TestElderServantHealthAndMetrics:
    """ElderServant ヘルス・メトリクステスト"""

    @pytest.mark.asyncio
    async def test_health_check_initial(self, extended_servant):
        """初期状態ヘルスチェック"""
        health = await extended_servant.health_check()
        
        assert health["success"] is True
        assert health["servant_id"] == extended_servant.servant_id
        assert health["servant_name"] == extended_servant.servant_name
        assert health["category"] == ServantCategory.DWARF.value
        assert health["status"] in ["healthy", "degraded"]  # 初期状態では品質スコア0のため
        assert "uptime_seconds" in health
        assert health["current_tasks"] == 0

    @pytest.mark.asyncio
    async def test_health_check_after_tasks(self, extended_servant, success_request):
        """タスク実行後ヘルスチェック"""
        # タスク実行
        await extended_servant.process_request(success_request)
        
        health = await extended_servant.health_check()
        
        assert health["stats"]["tasks_executed"] == 1
        assert health["stats"]["success_rate"] == 100.0
        assert health["stats"]["quality_status"] == "excellent"
        
    @pytest.mark.asyncio
    async def test_iron_will_quality_validation(self, extended_servant):
        """Iron Will品質検証テスト"""
        # 高品質データ
        high_quality_data = {
            "success": True,
            "status": "completed",
            "data": {"result": "excellent"},
            "execution_time_ms": 100
        }
        
        score = await extended_servant.validate_iron_will_quality(high_quality_data)
        assert score >= 95.0  # Iron Will基準
        
        # 低品質データ
        low_quality_data = {
            "success": False,
            "error": "Something went wrong",
            "execution_time_ms": 6000  # 6秒（遅い）
        }
        
        score = await extended_servant.validate_iron_will_quality(low_quality_data)
        assert score < 95.0


class TestElderServantAdvanced:
    """ElderServant 高度機能テスト"""

    @pytest.mark.asyncio
    async def test_sage_collaboration(self, extended_servant):
        """4賢者連携テスト"""
        collaboration_request = {
            "type": "knowledge_query",
            "request_id": "collab_001",
            "query": "Best practices for task execution"
        }
        
        result = await extended_servant.collaborate_with_sages(
            "knowledge", collaboration_request
        )
        
        assert result["success"] is True
        assert result["sage_type"] == "knowledge"
        assert "request_id" in result

    @pytest.mark.asyncio
    async def test_performance_task_execution(self, extended_servant):
        """パフォーマンステスト実行"""
        performance_request = ServantRequest(
            task_id="perf_001",
            task_type="performance_test",
            priority=TaskPriority.HIGH,
            payload={"load_factor": 1000}
        )
        
        response = await extended_servant.process_request(performance_request)
        
        assert response.status == TaskStatus.COMPLETED
        assert "performance_metrics" in response.result_data
        metrics = response.result_data["performance_metrics"]
        assert "throughput" in metrics
        assert "latency_ms" in metrics
        assert "cpu_usage" in metrics

    @pytest.mark.asyncio
    async def test_statistics_tracking_detailed(self, extended_servant):
        """詳細統計追跡テスト"""
        # 様々なタスクを実行
        tasks = [
            ("success_test", TaskStatus.COMPLETED),
            ("failure_test", TaskStatus.FAILED),
            ("warning_test", TaskStatus.COMPLETED),
            ("performance_test", TaskStatus.COMPLETED)
        ]
        
        for task_type, expected_status in tasks:
            request = ServantRequest(
                task_id=f"stat_{task_type}",
                task_type=task_type,
                priority=TaskPriority.MEDIUM,
                payload={}
            )
            response = await extended_servant.process_request(request)
            assert response.status == expected_status
        
        # 統計確認
        stats = extended_servant.stats
        assert stats["tasks_executed"] == 4
        assert stats["tasks_succeeded"] == 3  # success, warning, performance
        assert stats["tasks_failed"] == 1     # failure
        assert stats["total_execution_time_ms"] > 0
        assert stats["average_quality_score"] > 0


@pytest.mark.parametrize("task_type,expected_status,min_quality", [
    ("success_test", TaskStatus.COMPLETED, 95.0),
    ("failure_test", TaskStatus.FAILED, 0.0),
    ("warning_test", TaskStatus.COMPLETED, 80.0),
    ("performance_test", TaskStatus.COMPLETED, 90.0),
])
@pytest.mark.asyncio
async def test_task_execution_patterns_extended(
    extended_servant, task_type, expected_status, min_quality
):
    """拡張タスク実行パターンテスト"""
    task = {
        "task_id": f"pattern_{task_type}",
        "task_type": task_type,
        "description": f"パターンテスト: {task_type}"
    }

    result = await extended_servant.execute_task(task)
    assert result.status == expected_status
    
    if expected_status == TaskStatus.COMPLETED:
        assert result.quality_score >= min_quality
    else:
        assert result.quality_score == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])