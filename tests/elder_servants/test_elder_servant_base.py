"""
ElderServantBase基底クラスのテスト

Iron Will品質基準に準拠したテストケースを実装。
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, List, Any

from libs.elder_servants.base.elder_servant_base import (
    ElderServantBase,
    ServantDomain,
    ServantCapability,
    ServantRequest,
    ServantResponse
)

# テスト用の具体的なサーバント実装
class TestServant(ElderServantBase[Dict[str, Any], Dict[str, Any]]):
    """テスト用のサーバント実装"""
    
    def __init__(self, name: str, domain: ServantDomain):
        super().__init__(name, domain)
        self.capabilities = [
            ServantCapability.CODE_GENERATION,
            ServantCapability.TESTING
        ]
        self.process_count = 0
        self.should_fail = False
    
    async def process_request(self, request: ServantRequest[Dict[str, Any]]) -> ServantResponse[Dict[str, Any]]:
        """テスト用のリクエスト処理"""
        self.process_count += 1
        
        if self.should_fail:
            raise Exception("Test failure")
        
        return ServantResponse(
            task_id=request.task_id,
            status="success",
            data={"processed": True, "count": self.process_count},
            errors=[],
            warnings=[],
            metrics={"processing_time": 0.1}
        )
    
    def get_capabilities(self) -> List[ServantCapability]:
        return self.capabilities
    
    def validate_request(self, request: ServantRequest[Dict[str, Any]]) -> bool:
        return bool(request.task_id and request.task_type)

class TestElderServantBase:
    """ElderServantBase のテストクラス"""
    
    @pytest.fixture
    def servant(self):
        """テスト用サーバントのフィクスチャ"""
        return TestServant("test_servant", ServantDomain.DWARF_WORKSHOP)
    
    @pytest.fixture
    def sample_request(self):
        """サンプルリクエストのフィクスチャ"""
        return ServantRequest(
            task_id="test_001",
            task_type="test_task",
            priority="high",
            data={"test": "data"},
            context={"user": "test_user"}
        )
    
    def test_servant_initialization(self, servant):
        """サーバントの初期化テスト"""
        assert servant.name == "test_servant"
        assert servant.domain == ServantDomain.DWARF_WORKSHOP
        assert servant._metrics["tasks_processed"] == 0
        assert servant._metrics["tasks_succeeded"] == 0
        assert servant._metrics["tasks_failed"] == 0
        assert all(score == 0 for score in servant._quality_scores.values())
    
    def test_get_capabilities(self, servant):
        """能力取得のテスト"""
        capabilities = servant.get_capabilities()
        assert len(capabilities) == 2
        assert ServantCapability.CODE_GENERATION in capabilities
        assert ServantCapability.TESTING in capabilities
    
    @pytest.mark.asyncio
    async def test_successful_request_processing(self, servant, sample_request):
        """正常なリクエスト処理のテスト"""
        response = await servant.execute_with_quality_gate(sample_request)
        
        assert response.task_id == "test_001"
        assert response.status == "success"
        assert response.data["processed"] is True
        assert response.data["count"] == 1
        assert len(response.errors) == 0
        
        # メトリクスの更新確認
        metrics = servant.get_metrics()
        assert metrics["tasks_processed"] == 1
        assert metrics["tasks_succeeded"] == 1
        assert metrics["tasks_failed"] == 0
        assert metrics["success_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_failed_request_processing(self, servant, sample_request):
        """失敗するリクエスト処理のテスト"""
        servant.should_fail = True
        response = await servant.execute_with_quality_gate(sample_request)
        
        assert response.task_id == "test_001"
        assert response.status == "failed"
        assert response.data is None
        assert len(response.errors) == 1
        assert "Test failure" in response.errors[0]
        
        # メトリクスの更新確認
        metrics = servant.get_metrics()
        assert metrics["tasks_processed"] == 1
        assert metrics["tasks_succeeded"] == 0
        assert metrics["tasks_failed"] == 1
        assert metrics["success_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_invalid_request_validation(self, servant):
        """無効なリクエストの検証テスト"""
        invalid_request = ServantRequest(
            task_id="",  # 無効なタスクID
            task_type="test_task",
            priority="high",
            data={},
            context={}
        )
        
        response = await servant.execute_with_quality_gate(invalid_request)
        
        assert response.status == "failed"
        assert "Invalid request" in response.errors
    
    def test_iron_will_criteria_check(self, servant):
        """Iron Will品質基準のチェックテスト"""
        # 初期状態では基準を満たさない
        assert not servant._check_iron_will_criteria()
        
        # 品質スコアを基準値まで上げる
        servant._quality_scores = {
            "root_cause_resolution": 95,
            "dependency_completeness": 100,
            "test_coverage": 95,
            "security_score": 90,
            "performance_score": 85,
            "maintainability_score": 80
        }
        
        # 基準を満たすことを確認
        assert servant._check_iron_will_criteria()
        
        # 一つでも基準を下回ると失敗
        servant._quality_scores["test_coverage"] = 90
        assert not servant._check_iron_will_criteria()
    
    @pytest.mark.asyncio
    async def test_quality_score_update(self, servant, sample_request):
        """品質スコア更新のテスト"""
        # 初期状態
        assert all(score == 0 for score in servant._quality_scores.values())
        
        # 成功リクエストで品質スコアが向上
        response = await servant.execute_with_quality_gate(sample_request)
        assert response.status == "success"
        
        # スコアが更新されていることを確認
        assert all(score > 0 for score in servant._quality_scores.values())
    
    @pytest.mark.asyncio
    async def test_metrics_calculation(self, servant, sample_request):
        """メトリクス計算のテスト"""
        # 複数のリクエストを処理
        for i in range(5):
            response = await servant.execute_with_quality_gate(sample_request)
            assert response.status == "success"
        
        # 1つ失敗させる
        servant.should_fail = True
        response = await servant.execute_with_quality_gate(sample_request)
        assert response.status == "failed"
        
        # メトリクスの確認
        metrics = servant.get_metrics()
        assert metrics["tasks_processed"] == 6
        assert metrics["tasks_succeeded"] == 5
        assert metrics["tasks_failed"] == 1
        assert metrics["success_rate"] == pytest.approx(5/6, 0.01)
        assert metrics["average_processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_connect_to_sages(self, servant):
        """4賢者システムとの接続テスト"""
        # 現在はモック実装のため常にTrue
        connected = await servant.connect_to_sages()
        assert connected is True
    
    @pytest.mark.asyncio
    async def test_report_to_elder_council(self, servant):
        """エルダー評議会への報告テスト"""
        report = {
            "servant": servant.name,
            "status": "operational",
            "metrics": servant.get_metrics()
        }
        
        # 現在はログ出力のみ、例外が発生しないことを確認
        await servant.report_to_elder_council(report)
    
    def test_servant_representation(self, servant):
        """サーバントの文字列表現テスト"""
        repr_str = repr(servant)
        assert "TestServant" in repr_str
        assert "test_servant" in repr_str
        assert "dwarf_workshop" in repr_str
EOF < /dev/null
