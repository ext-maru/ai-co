"""
🧪 エルダーサーバント EldersLegacy統合テスト

Issue #69: 基盤修正 - EldersLegacy対応のテストスイート
TDD原則に従い、EldersServiceLegacy継承とIron Will品質基準の検証を行います。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List

# テスト対象インポート
from elders_guild.elder_tree.elder_servants.base.elder_servant import (
    ElderServant,
    ServantCategory,
    ServantCapability,
    ServantRequest,
    ServantResponse,
    TaskStatus,
    TaskPriority,
    TaskResult
)
from elders_guild.elder_tree.core.elders_legacy import (
    EldersServiceLegacy,
    IronWillCriteria,
    EldersLegacyDomain
)


class TestElderServantImplementation(ElderServant):
    """テスト用のエルダーサーバント実装"""
    
    def __init__(self):
        capabilities = [
            ServantCapability(
                "test_capability",
                "テスト能力",
                ["test_input"],
                ["test_output"],
                1
            )
        ]
        super().__init__(
            servant_id="test_servant_001",
            servant_name="TestServant",
            category=ServantCategory.DWARF,
            specialization="testing",
            capabilities=capabilities
        )
        self.should_fail = False
        self.execution_delay = 0.0
    
    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """テスト用タスク実行"""
        if self.execution_delay > 0:
            await asyncio.sleep(self.execution_delay)
        
        if self.should_fail:
            return TaskResult(
                task_id=task.get("task_id", "unknown"),
                servant_id=self.servant_id,
                status=TaskStatus.FAILED,
                error_message="Test failure",
                execution_time_ms=100.0,
                quality_score=0.0
            )
        
        # 成功ケース
        result_data = {
            "success": True,
            "status": "completed",
            "data": {"test": "result"},
            "execution_time_ms": 100.0
        }
        
        quality_score = await self.validate_iron_will_quality(result_data)
        
        return TaskResult(
            task_id=task.get("task_id", "test_001"),
            servant_id=self.servant_id,
            status=TaskStatus.COMPLETED,
            result_data=result_data,
            execution_time_ms=100.0,
            quality_score=quality_score
        )
    
    def get_specialized_capabilities(self) -> List[ServantCapability]:
        """専門能力取得"""
        return [
            ServantCapability(
                "test_specialized",
                "テスト専門能力",
                ["test_spec_input"],
                ["test_spec_output"],
                2
            )
        ]


class TestElderServantLegacyIntegration:
    """エルダーサーバント EldersLegacy統合テストスイート"""
    
    @pytest.fixture
    def servant(self):
        """テスト用サーバントのフィクスチャ"""
        return TestElderServantImplementation()
    
    @pytest.fixture
    def sample_request(self):
        """サンプルリクエストのフィクスチャ"""
        return ServantRequest(
            task_id="test_001",
            task_type="test_task",
            priority=TaskPriority.HIGH,
            payload={"test_data": "sample"},
            context={"user": "test_user"}
        )
    
    # ========== EldersLegacy継承の検証 ==========
    
    def test_elders_legacy_inheritance(self, servant):
        """EldersServiceLegacyからの継承を検証"""
        assert isinstance(servant, EldersServiceLegacy)
        assert hasattr(servant, 'process_request')
        assert hasattr(servant, 'validate_request')
        assert hasattr(servant, 'get_capabilities')
        assert hasattr(servant, 'execute_with_quality_gate')
    
    def test_enforce_boundary_decorator(self, servant):
        """@enforce_boundary デコレータが適用されていることを検証"""
        execute_task_method = getattr(servant, 'execute_task')
        assert hasattr(execute_task_method, '_boundary_enforced')
        assert execute_task_method._boundary_enforced == "servant"
    
    def test_elders_legacy_domain(self, servant):
        """EldersLegacyドメインがEXECUTIONに設定されていることを検証"""
        assert servant.domain == EldersLegacyDomain.EXECUTION
        assert servant.component_id == "test_servant_001"
    
    # ========== Iron Will品質基準のテスト ==========
    
    @pytest.mark.asyncio
    async def test_iron_will_quality_validation_perfect_score(self, servant):
        """Iron Will品質基準の検証（完璧なスコア）"""
        result_data = {
            "success": True,         # 30点
            "status": "completed",   # 25点
            "data": {"result": "ok"}, # 25点  
            "execution_time_ms": 100  # 25点
        }
        
        score = await servant.validate_iron_will_quality(result_data)
        assert score == 100.0  # 満点
        
        # Iron Will基準（95%以上）をクリア
        assert score >= 95.0
    
    @pytest.mark.asyncio
    async def test_iron_will_quality_validation_failing_score(self, servant):
        """Iron Will品質基準の検証（失敗ケース）"""
        result_data = {
            "success": False,        # 0点
            "error": "Test error",   # 0点
            "execution_time_ms": 6000  # 0点（5秒超過）
        }
        
        score = await servant.validate_iron_will_quality(result_data)
        assert score < 95.0  # Iron Will基準未達
        assert score == 0.0  # 最低スコア
    
    @pytest.mark.asyncio
    async def test_iron_will_95_percent_threshold(self, servant):
        """Iron Will 95%閾値の正確な検証"""
        # 95%ちょうどのケース
        result_data = {
            "success": True,         # 30点
            "status": "completed",   # 25点
            "data": {"result": "ok"}, # 25点  
            "execution_time_ms": 4000  # 15点（5秒未満だが遅い）
        }
        
        score = await servant.validate_iron_will_quality(result_data)
        assert score == 95.0  # ちょうど95%
    
    # ========== EldersServiceLegacy統一インターフェース ==========
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, servant, sample_request):
        """process_requestメソッドの正常動作を検証"""
        response = await servant.process_request(sample_request)
        
        assert isinstance(response, ServantResponse)
        assert response.task_id == "test_001"
        assert response.servant_id == "test_servant_001"
        assert response.status == TaskStatus.COMPLETED
        assert response.result_data["success"] is True
        assert response.execution_time_ms > 0
        assert response.quality_score >= 95.0  # Iron Will基準
    
    @pytest.mark.asyncio
    async def test_process_request_failure(self, servant, sample_request):
        """process_requestメソッドの失敗処理を検証"""
        servant.should_fail = True
        
        response = await servant.process_request(sample_request)
        
        assert isinstance(response, ServantResponse)
        assert response.status == TaskStatus.FAILED
        assert response.error_message == "Test failure"
        assert response.quality_score == 0.0
    
    def test_validate_request_valid(self, servant, sample_request):
        """有効なリクエストの検証"""
        assert servant.validate_request(sample_request) is True
    
    def test_validate_request_invalid_no_task_id(self, servant):
        """無効なリクエスト（task_id不足）の検証"""
        invalid_request = ServantRequest(
            task_id="",  # 空のタスクID
            task_type="test_task",
            priority=TaskPriority.HIGH,
            payload={"test": "data"}
        )
        
        assert servant.validate_request(invalid_request) is False
    
    def test_validate_request_invalid_payload(self, servant):
        """無効なリクエスト（payload形式不正）の検証"""
        invalid_request = ServantRequest(
            task_id="test_001",
            task_type="test_task",
            priority=TaskPriority.HIGH,
            payload="invalid_payload"  # dict以外
        )
        
        assert servant.validate_request(invalid_request) is False
    
    def test_get_capabilities_format(self, servant):
        """get_capabilitiesメソッドの形式を検証"""
        capabilities = servant.get_capabilities()
        
        assert isinstance(capabilities, list)
        assert all(isinstance(cap, str) for cap in capabilities)
        assert "test_capability" in capabilities
        assert "test_specialized" in capabilities
    
    # ========== 統合テスト（execute_with_quality_gate） ==========
    
    @pytest.mark.asyncio
    async def test_execute_with_quality_gate_success(self, servant, sample_request):
        """品質ゲート付き実行の成功ケース"""
        response = await servant.execute_with_quality_gate(sample_request)
        
        assert isinstance(response, ServantResponse)
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        
        # メトリクス更新確認
        metrics = servant.get_metrics()
        assert metrics["execution_stats"]["requests_processed"] == 1
        assert metrics["execution_stats"]["requests_succeeded"] == 1
        assert metrics["iron_will_compliant"] is True
    
    @pytest.mark.asyncio
    async def test_execute_with_quality_gate_failure(self, servant, sample_request):
        """品質ゲート付き実行の失敗ケース"""
        servant.should_fail = True
        
        with pytest.raises(Exception):
            await servant.execute_with_quality_gate(sample_request)
        
        # エラー統計更新確認
        metrics = servant.get_metrics()
        assert metrics["execution_stats"]["requests_failed"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_quality_gate_validation_error(self, servant):
        """品質ゲート付き実行のバリデーションエラー"""
        invalid_request = ServantRequest(
            task_id="",  # 無効
            task_type="test_task",
            priority=TaskPriority.HIGH,
            payload={}
        )
        
        with pytest.raises(ValueError, match="Invalid request"):
            await servant.execute_with_quality_gate(invalid_request)
    
    # ========== パフォーマンステスト ==========
    
    @pytest.mark.asyncio
    async def test_performance_under_200ms(self, servant, sample_request):
        """200ms未満での実行を検証"""
        import time
        
        start_time = time.time()
        response = await servant.execute_with_quality_gate(sample_request)
        execution_time = (time.time() - start_time) * 1000
        
        assert execution_time < 200  # 200ms未満
        assert response.execution_time_ms < 200
        
        # パフォーマンススコアが最高値になることを確認
        assert servant.quality_scores[IronWillCriteria.PERFORMANCE_SCORE] == 100.0
    
    @pytest.mark.asyncio
    async def test_performance_timeout_handling(self, servant, sample_request):
        """タイムアウト処理のテスト"""
        servant.execution_delay = 2.0  # 2秒遅延
        
        response = await servant.execute_with_quality_gate(sample_request)
        
        # 遅延があってもタスクは完了する
        assert response.status == TaskStatus.COMPLETED
        assert response.execution_time_ms > 2000
        
        # パフォーマンススコアが下がることを確認
        assert servant.quality_scores[IronWillCriteria.PERFORMANCE_SCORE] == 85.0  # 1秒以上5秒未満
    
    # ========== メトリクスとヘルスチェック ==========
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, servant, sample_request):
        """メトリクス追跡の検証"""
        initial_metrics = servant.get_metrics()
        assert initial_metrics["execution_stats"]["requests_processed"] == 0
        
        # 複数回実行
        for i in range(3):
            await servant.execute_with_quality_gate(sample_request)
        
        updated_metrics = servant.get_metrics()
        assert updated_metrics["execution_stats"]["requests_processed"] == 3
        assert updated_metrics["execution_stats"]["requests_succeeded"] == 3
        assert updated_metrics["execution_stats"]["average_quality_score"] >= 95.0
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, servant, sample_request):
        """正常な健康状態のチェック"""
        # 成功実行でメトリクス向上
        await servant.execute_with_quality_gate(sample_request)
        
        health = await servant.health_check()
        
        assert health["status"] == "healthy"
        assert health["component_id"] == "test_servant_001"
        assert health["domain"] == "execution"
        assert health["iron_will_compliant"] is True
        assert health["quality_score"] >= 95.0
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self, servant):
        """劣化状態のヘルスチェック"""
        # 品質スコアを人工的に下げる
        for criteria in servant.quality_scores:
            servant.quality_scores[criteria] = 50.0  # 基準未満
        
        health = await servant.health_check()
        
        assert health["status"] == "degraded"
        assert health["iron_will_compliant"] is False
    
    # ========== 後方互換性テスト ==========
    
    @pytest.mark.asyncio
    async def test_backward_compatibility_dict_request(self, servant):
        """旧形式のdict型リクエストとの後方互換性"""
        # 旧形式のprocess_request（辞書型）も動作することを確認
        old_request = {
            "type": "execute_task",
            "task": {
                "task_id": "old_001",
                "task_type": "old_test",
                "priority": "high",
                "payload": {"old": "data"}
            }
        }
        
        # 旧形式process_requestが存在し動作することを確認
        # （実装では新形式process_requestに統合されているが、
        # 　execute_taskは引き続き動作する）
        task = old_request["task"]
        result = await servant.execute_task(task)
        
        assert result.task_id == "old_001"
        assert result.status == TaskStatus.COMPLETED


class TestServantRequestResponse:
    """ServantRequest/Response クラスのテスト"""
    
    def test_servant_request_creation(self):
        """ServantRequest作成のテスト"""
        request = ServantRequest(
            task_id="req_001",
            task_type="test_request",
            priority=TaskPriority.MEDIUM,
            payload={"key": "value"},
            context={"user": "tester"}
        )
        
        assert request.task_id == "req_001"
        assert request.task_type == "test_request"
        assert request.priority == TaskPriority.MEDIUM
        assert request.payload == {"key": "value"}
        assert request.context == {"user": "tester"}
        assert isinstance(request.created_at, datetime)
    
    def test_servant_response_creation(self):
        """ServantResponse作成のテスト"""
        response = ServantResponse(
            task_id="resp_001",
            servant_id="test_servant",
            status=TaskStatus.COMPLETED,
            result_data={"result": "success"},
            execution_time_ms=150.0,
            quality_score=97.5
        )
        
        assert response.task_id == "resp_001"
        assert response.servant_id == "test_servant"
        assert response.status == TaskStatus.COMPLETED
        assert response.result_data == {"result": "success"}
        assert response.execution_time_ms == 150.0
        assert response.quality_score == 97.5
        assert isinstance(response.completed_at, datetime)


# ========== ベンチマークテスト ==========

@pytest.mark.benchmark
class TestElderServantPerformance:
    """エルダーサーバントパフォーマンステスト"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """並行リクエスト処理のテスト"""
        servant = TestElderServantImplementation()
        
        requests = [
            ServantRequest(
                task_id=f"concurrent_{i}",
                task_type="performance_test",
                priority=TaskPriority.HIGH,
                payload={"index": i}
            )
            for i in range(10)
        ]
        
        import time
        start_time = time.time()
        
        # 並行実行
        responses = await asyncio.gather(*[
            servant.execute_with_quality_gate(req) for req in requests
        ])
        
        total_time = time.time() - start_time
        
        # 全て成功することを確認
        assert len(responses) == 10
        assert all(resp.status == TaskStatus.COMPLETED for resp in responses)
        assert all(resp.quality_score >= 95.0 for resp in responses)
        
        # 並行実行により効率的であることを確認（目安）
        assert total_time < 2.0  # 10個のタスクが2秒以内
        
        # メトリクス確認
        metrics = servant.get_metrics()
        assert metrics["execution_stats"]["requests_processed"] == 10
        assert metrics["execution_stats"]["requests_succeeded"] == 10