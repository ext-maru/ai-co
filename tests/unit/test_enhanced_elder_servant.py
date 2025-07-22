"""
Enhanced Elder Servant 基底クラステスト
=====================================

Elder Tree分散AIアーキテクチャの統合基底クラス
EnhancedElderServantの動作確認テスト

Author: Claude Elder
Created: 2025-07-22
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

from libs.elder_servants.base.enhanced_elder_servant import (
    EnhancedElderServant,
    ServantSpecialization,
    ServantTier,
    A2ACommunication,
    SageCollaboration,
    QualityGate,
    LearningConfig,
    ServantMetrics,
    QualityValidationResult,
)


class TestEnhancedElderServant(EnhancedElderServant[Dict[str, Any], Dict[str, Any]]):
    """テスト用具体実装クラス"""
    
    def __init__(self):
        super().__init__(
            servant_id="test_servant_001",
            servant_name="Test Enhanced Servant",
            specialization=ServantSpecialization.IMPLEMENTATION,
            tier=ServantTier.EXPERT,
        )
    
    async def _execute_specialized_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """テスト用専門タスク実行"""
        # シンプルなエコー実装
        return {
            "status": "completed",
            "input_received": request,
            "processing_time": "fast",
            "quality": "high",
        }
    
    def get_specialized_capabilities(self) -> list[str]:
        """テスト用専門能力"""
        return [
            "test_implementation",
            "mock_execution",
            "validation_testing",
            "quality_assurance",
        ]


class TestEnhancedElderServantCore:
    """Enhanced Elder Servant 基底クラステスト"""
    
    @pytest.fixture
    def servant(self):
        """テスト用サーバントインスタンス"""
        return TestEnhancedElderServant()
    
    def test_initialization(self, servant):
        """初期化テスト"""
        assert servant.servant_id == "test_servant_001"
        assert servant.servant_name == "Test Enhanced Servant"
        assert servant.specialization == ServantSpecialization.IMPLEMENTATION
        assert servant.tier == ServantTier.EXPERT
        
        # メトリクス初期化確認
        assert isinstance(servant.metrics, ServantMetrics)
        assert servant.metrics.tasks_executed == 0
        assert servant.metrics.tasks_succeeded == 0
        
        # 設定初期化確認
        assert isinstance(servant.a2a_config, A2ACommunication)
        assert isinstance(servant.sage_config, SageCollaboration)
        assert isinstance(servant.quality_config, QualityGate)
        assert isinstance(servant.learning_config, LearningConfig)
    
    def test_soul_identity(self, servant):
        """Soul Identity統合テスト"""
        identity = servant.soul_identity
        assert identity.soul_id == "test_servant_001"
        assert identity.soul_name == "Test Enhanced Servant"
        assert identity.specializations == ["implementation"]
        assert len(identity.capabilities) >= 3  # 基本能力＋専門能力
    
    def test_specialized_capabilities(self, servant):
        """専門能力テスト"""
        capabilities = servant.get_specialized_capabilities()
        assert "test_implementation" in capabilities
        assert "quality_assurance" in capabilities
        assert len(capabilities) == 4
    
    @pytest.mark.asyncio
    async def test_basic_task_execution(self, servant):
        """基本タスク実行テスト"""
        test_request = {
            "task_type": "test_task",
            "data": {"key": "value"},
            "priority": "high",
        }
        
        response = await servant.process_request(test_request)
        
        # 応答構造確認
        assert response is not None
        assert "status" in response
        assert "input_received" in response
        
        # メトリクス更新確認
        assert servant.metrics.tasks_executed == 1
        assert servant.metrics.tasks_succeeded == 1
        assert servant.metrics.average_quality_score > 0
    
    @pytest.mark.asyncio
    async def test_quality_validation(self, servant):
        """品質検証テスト"""
        test_response = {
            "status": "success",
            "data": {"result": "completed"},
            "quality": "high",
        }
        
        # 品質スコア計算テスト
        basic_score = await servant._calculate_basic_quality_score(test_response)
        assert basic_score > 50  # 基本品質基準
        
        # 品質ゲート検証テスト
        validation_result = await servant._validate_quality_gates(test_response)
        assert isinstance(validation_result, QualityValidationResult)
        assert validation_result.score > 0
    
    @pytest.mark.asyncio
    async def test_preventive_quality_check(self, servant):
        """予防的品質チェックテスト"""
        test_request = {"valid": True, "data": "test"}
        
        check_result = await servant._preventive_quality_check(test_request)
        assert check_result is True
        
        # 無効なリクエストテスト
        invalid_request = None
        check_result = await servant._preventive_quality_check(invalid_request)
        assert check_result is False
    
    @pytest.mark.asyncio
    async def test_sage_consultation(self, servant):
        """4賢者相談テスト"""
        test_request = {"complex_task": True, "requires_knowledge": True}
        
        # 相談必要性判定
        requires_consultation = await servant._requires_sage_consultation(test_request)
        # 複雑なタスクなので相談必要と判定されるはず
        assert requires_consultation is True
        
        # 4賢者相談実行
        consultation_result = await servant._consult_sages(test_request)
        assert "knowledge" in consultation_result or "error" in consultation_result
        assert "task" in consultation_result or "error" in consultation_result
        assert "incident" in consultation_result or "error" in consultation_result
        assert "rag" in consultation_result or "error" in consultation_result
    
    @pytest.mark.asyncio
    async def test_learning_system(self, servant):
        """学習システムテスト"""
        test_request = {"learning_task": True}
        test_response = {"status": "success", "quality": "high"}
        
        # 成功パターン学習
        await servant._learn_from_execution(test_request, test_response, True)
        
        # 学習バッファに記録されることを確認
        assert len(servant.experience_buffer) > 0
        
        # パターン学習確認
        assert len(servant.learned_patterns) > 0
        
        # メトリクス更新確認
        assert servant.metrics.patterns_learned > 0
    
    @pytest.mark.asyncio
    async def test_a2a_communication(self, servant):
        """A2A通信テスト"""
        # A2A通信初期化
        await servant._initialize_a2a_communication()
        
        # メッセージ送信テスト
        test_message = {"type": "test", "data": "hello"}
        response = await servant.send_a2a_message("target_servant", test_message)
        
        assert response["status"] == "success"
        assert servant.metrics.a2a_messages_sent > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, servant):
        """ヘルスチェックテスト"""
        health_status = await servant.health_check()
        
        # 基本フィールド確認
        required_fields = [
            "servant_id", "servant_name", "specialization", 
            "tier", "soul_state", "is_healthy"
        ]
        
        for field in required_fields:
            assert field in health_status
        
        # ステータス確認
        assert health_status["servant_id"] == "test_servant_001"
        assert health_status["is_healthy"] is True
        assert "metrics" in health_status
    
    def test_metrics_update(self, servant):
        """メトリクス更新テスト"""
        initial_executed = servant.metrics.tasks_executed
        
        # メトリクス更新（同期メソッドでテスト）
        import asyncio
        asyncio.run(servant._update_metrics(100.0, True, 95.0))
        
        # 更新確認
        assert servant.metrics.tasks_executed == initial_executed + 1
        assert servant.metrics.tasks_succeeded > 0
        assert servant.metrics.average_quality_score > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, servant):
        """エラーハンドリングテスト"""
        # エラーが発生するリクエスト（実際のタスク実行でエラーを発生させる）
        class FailingTestServant(TestEnhancedElderServant):
            async def _execute_specialized_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
                raise ValueError("Test error")
        
        failing_servant = FailingTestServant()
        
        test_request = {"cause_error": True}
        
        # エラーが適切に処理されることを確認
        with pytest.raises(ValueError):
            await failing_servant.process_request(test_request)
        
        # 失敗メトリクスが更新されることを確認
        assert failing_servant.metrics.tasks_failed > 0
    
    def test_configuration_customization(self):
        """設定カスタマイゼーションテスト"""
        custom_a2a_config = A2ACommunication(
            host="custom_host",
            port=9999,
            max_connections=50,
        )
        
        custom_quality_config = QualityGate(
            iron_will_threshold=98.0,
            auto_rejection=False,
        )
        
        custom_servant = TestEnhancedElderServant.__new__(TestEnhancedElderServant)
        super(TestEnhancedElderServant, custom_servant).__init__(
            servant_id="custom_test",
            servant_name="Custom Test Servant",
            specialization=ServantSpecialization.TESTING,
            tier=ServantTier.MASTER,
            a2a_config=custom_a2a_config,
            quality_config=custom_quality_config,
        )
        
        assert custom_servant.a2a_config.host == "custom_host"
        assert custom_servant.a2a_config.port == 9999
        assert custom_servant.quality_config.iron_will_threshold == 98.0
        assert custom_servant.quality_config.auto_rejection is False


class TestEnhancedElderServantIntegration:
    """統合テストクラス"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """フルワークフロー統合テスト"""
        servant = TestEnhancedElderServant()
        
        # 複雑なリクエストで全機能統合テスト
        complex_request = {
            "task_type": "complex_implementation",
            "requirements": ["high_quality", "secure", "performant"],
            "data": {"input": "complex_data", "size": "large"},
            "priority": "critical",
        }
        
        # 統合処理実行
        response = await servant.process_request(complex_request)
        
        # 統合結果検証
        assert response is not None
        assert "status" in response
        assert response["status"] == "completed"
        
        # すべての機能が連携動作したことを確認
        assert servant.metrics.tasks_executed > 0
        assert servant.metrics.sage_consultations > 0  # 複雑なタスクなので4賢者相談
        assert len(servant.experience_buffer) > 0       # 学習が行われた
        assert servant.metrics.patterns_learned > 0     # パターン学習が実行された
        
        # ヘルスチェックで統合状態確認
        health_status = await servant.health_check()
        assert health_status["is_healthy"] is True
        assert health_status["metrics"]["tasks_executed"] > 0


if __name__ == "__main__":
    """テスト実行"""
    # pytest実行時の基本設定
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])