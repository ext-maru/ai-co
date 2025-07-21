#!/usr/bin/env python3
"""
🧪 Issue #69: 基盤修正 - EldersLegacy対応
完全テストスイート

エルダー評議会令第27号に基づく基盤クラス修正の包括的検証
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.elder_servants.base.elder_servant import (
    ElderServant, ServantCategory, ServantCapability, 
    ServantRequest, ServantResponse, TaskStatus, TaskPriority, TaskResult
)
from libs.core.elders_legacy import (
    EldersServiceLegacy, IronWillCriteria, EldersLegacyDomain, 
    enforce_boundary, elders_legacy_registry
)


class TestElderServantImplementation(ElderServant):
    """Issue #69テスト用のElderServant実装"""
    
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
    
    @enforce_boundary("servant")
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


class TestIssue69FoundationFixes:
    """Issue #69: 基盤修正テストスイート"""
    
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
    
    # ========== エルダー評議会令第27号: EldersLegacy継承確認 ==========
    
    def test_elders_legacy_inheritance_compliance(self, servant):
        """エルダー評議会令第27号: EldersLegacy継承確認"""
        # ElderServantがEldersServiceLegacyを継承していることを確認
        assert isinstance(servant, EldersServiceLegacy)
        assert hasattr(servant, 'process_request')
        assert hasattr(servant, 'validate_request')
        assert hasattr(servant, 'get_capabilities')
        assert hasattr(servant, 'execute_with_quality_gate')
        
        # ドメイン設定確認
        assert servant.domain == EldersLegacyDomain.EXECUTION
        assert servant.component_id == "test_servant_001"
    
    def test_boundary_enforcement_decorator(self, servant):
        """境界強制デコレータ適用確認"""
        execute_task_method = getattr(servant, 'execute_task')
        assert hasattr(execute_task_method, '_boundary_enforced')
        assert execute_task_method._boundary_enforced == "servant"
    
    # ========== Iron Will品質基準95%閾値修正確認 ==========
    
    @pytest.mark.asyncio
    async def test_iron_will_95_percent_threshold_perfect(self, servant):
        """Iron Will 95%閾値: 完璧ケース"""
        perfect_result = {
            "success": True,
            "status": "completed",
            "data": {"result": "ok"},
            "execution_time_ms": 100
        }
        
        score = await servant.validate_iron_will_quality(perfect_result)
        assert score == 100.0
        assert score >= 95.0  # Iron Will基準クリア
    
    @pytest.mark.asyncio
    async def test_iron_will_95_percent_threshold_failing(self, servant):
        """Iron Will 95%閾値: 失敗ケース"""
        failing_result = {
            "success": False,
            "error": "Test error",
            "execution_time_ms": 6000  # 5秒超過
        }
        
        score = await servant.validate_iron_will_quality(failing_result)
        assert score < 95.0  # Iron Will基準未達
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_iron_will_95_percent_threshold_borderline(self, servant):
        """Iron Will 95%閾値: ボーダーラインケース"""
        borderline_result = {
            "success": True,
            "status": "completed",
            "data": {"result": "ok"},
            "execution_time_ms": 4000  # 遅いが5秒未満
        }
        
        score = await servant.validate_iron_will_quality(borderline_result)
        assert score == 95.0  # ちょうど95%
    
    # ========== 統一インターフェース確認 ==========
    
    @pytest.mark.asyncio
    async def test_unified_servant_request_response_interface(self, servant, sample_request):
        """統一ServantRequest/ServantResponseインターフェース"""
        response = await servant.process_request(sample_request)
        
        assert isinstance(response, ServantResponse)
        assert response.task_id == "test_001"
        assert response.servant_id == "test_servant_001"
        assert response.status == TaskStatus.COMPLETED
        assert response.result_data["success"] is True
        assert response.quality_score >= 95.0
    
    @pytest.mark.asyncio
    async def test_unified_interface_validation(self, servant):
        """統一インターフェースのバリデーション"""
        # 有効なリクエスト
        valid_request = ServantRequest(
            task_id="valid_001",
            task_type="test_task",
            priority=TaskPriority.HIGH,
            payload={"data": "valid"}
        )
        assert servant.validate_request(valid_request) is True
        
        # 無効なリクエスト（空のタスクID）
        invalid_request = ServantRequest(
            task_id="",
            task_type="test_task",
            priority=TaskPriority.HIGH,
            payload={"data": "valid"}
        )
        assert servant.validate_request(invalid_request) is False
    
    def test_capabilities_format_compliance(self, servant):
        """能力取得形式確認"""
        capabilities = servant.get_capabilities()
        
        assert isinstance(capabilities, list)
        assert all(isinstance(cap, str) for cap in capabilities)
        assert "test_capability" in capabilities
        assert "test_specialized" in capabilities
    
    # ========== EldersLegacy品質ゲート統合確認 ==========
    
    @pytest.mark.asyncio
    async def test_elders_legacy_quality_gate_success(self, servant, sample_request):
        """EldersLegacy品質ゲート成功ケース"""
        response = await servant.execute_with_quality_gate(sample_request)
        
        assert isinstance(response, ServantResponse)
        assert response.status == TaskStatus.COMPLETED
        assert response.quality_score >= 95.0
        
        # メトリクス確認
        metrics = servant.get_metrics()
        assert metrics["execution_stats"]["requests_processed"] >= 1
        assert metrics["execution_stats"]["requests_succeeded"] >= 1
        assert metrics["iron_will_compliant"] is True
    
    @pytest.mark.asyncio
    async def test_elders_legacy_quality_gate_validation_error(self, servant):
        """EldersLegacy品質ゲートバリデーションエラー"""
        invalid_request = ServantRequest(
            task_id="",  # 無効
            task_type="test_task",
            priority=TaskPriority.HIGH,
            payload={}
        )
        
        with pytest.raises(ValueError, match="Invalid request"):
            await servant.execute_with_quality_gate(invalid_request)
    
    # ========== ヘルスチェック統合確認 ==========
    
    @pytest.mark.asyncio
    async def test_elders_legacy_health_check_integration(self, servant, sample_request):
        """EldersLegacyヘルスチェック統合"""
        # 成功実行でメトリクス向上
        await servant.execute_with_quality_gate(sample_request)
        
        health = await servant.health_check()
        
        assert health["status"] == "healthy"
        assert health["component_id"] == "test_servant_001"
        assert health["domain"] == "execution"
        assert health["iron_will_compliant"] is True
        assert health["quality_score"] >= 95.0
    
    # ========== パフォーマンス・並行性確認 ==========
    
    @pytest.mark.asyncio
    async def test_performance_under_iron_will_standards(self, servant, sample_request):
        """Iron Will基準下でのパフォーマンス"""
        import time
        
        start_time = time.time()
        response = await servant.execute_with_quality_gate(sample_request)
        execution_time = (time.time() - start_time) * 1000
        
        assert execution_time < 200  # 200ms未満
        assert response.execution_time_ms < 200
        
        # パフォーマンススコア確認
        metrics = servant.get_metrics()
        assert metrics["quality_scores"]["performance_score"] == 100.0
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_iron_will_compliance(self, servant):
        """並行実行でのIron Will準拠"""
        requests = [
            ServantRequest(
                task_id=f"concurrent_{i}",
                task_type="concurrent_test",
                priority=TaskPriority.HIGH,
                payload={"index": i}
            )
            for i in range(5)
        ]
        
        # 並行実行
        responses = await asyncio.gather(*[
            servant.execute_with_quality_gate(req) for req in requests
        ])
        
        # 全て成功かつIron Will準拠
        assert len(responses) == 5
        assert all(resp.status == TaskStatus.COMPLETED for resp in responses)
        assert all(resp.quality_score >= 95.0 for resp in responses)
        
        # 最終メトリクス確認
        metrics = servant.get_metrics()
        assert metrics["iron_will_compliant"] is True
        assert metrics["execution_stats"]["requests_processed"] >= 5
    
    # ========== レジストリ統合確認 ==========
    
    def test_elders_legacy_registry_integration(self, servant):
        """EldersLegacyレジストリ統合"""
        # レジストリに登録
        elders_legacy_registry.register(servant)
        
        # 取得確認
        retrieved = elders_legacy_registry.get_component("test_servant_001")
        assert retrieved is not None
        assert retrieved.component_id == servant.component_id
        assert retrieved.domain == EldersLegacyDomain.EXECUTION
        
        # ドメイン別取得確認
        execution_components = elders_legacy_registry.get_components_by_domain(
            EldersLegacyDomain.EXECUTION
        )
        assert len(execution_components) >= 1
        assert any(comp.component_id == "test_servant_001" for comp in execution_components)
    
    @pytest.mark.asyncio
    async def test_registry_health_check_all(self, servant):
        """レジストリ一括ヘルスチェック"""
        # レジストリに登録
        elders_legacy_registry.register(servant)
        
        # 一括ヘルスチェック
        health_results = await elders_legacy_registry.health_check_all()
        
        assert "overall_status" in health_results
        assert "components" in health_results
        assert "test_servant_001" in health_results["components"]
        
        component_health = health_results["components"]["test_servant_001"]
        assert component_health["status"] in ["healthy", "degraded"]
        assert component_health["domain"] == "execution"


# ========== 統合実行テスト ==========

@pytest.mark.asyncio
async def test_issue_69_complete_integration():
    """Issue #69 完全統合テスト"""
    print("🧪 Issue #69: 基盤修正完全統合テスト実行中...")
    
    servant = TestElderServantImplementation()
    
    # 1. EldersLegacy継承確認
    assert isinstance(servant, EldersServiceLegacy)
    
    # 2. Iron Will 95%閾値確認
    sample_request = ServantRequest(
        task_id="integration_001",
        task_type="integration_test",
        priority=TaskPriority.HIGH,
        payload={"integration": True}
    )
    
    response = await servant.execute_with_quality_gate(sample_request)
    assert response.quality_score >= 95.0
    
    # 3. メトリクス確認
    metrics = servant.get_metrics()
    assert metrics["iron_will_compliant"] is True
    
    # 4. ヘルスチェック確認
    health = await servant.health_check()
    assert health["status"] == "healthy"
    
    print("✅ Issue #69 基盤修正: 全ての要件が満たされています")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])