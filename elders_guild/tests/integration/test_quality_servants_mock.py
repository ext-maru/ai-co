"""
🧪 Quality Servants 統合テスト（モック版）
python-a2aをモック化してテスト実行
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

# python-a2aモジュールをモック
class MockA2AServer:
    def __init__(self):
        pass

class MockMessage:
    def __init__(self, content, role):
        self.content = content
        self.role = role

class MockTextContent:
    def __init__(self, text):
        self.text = text

class MockMessageRole:
    USER = "user"
    AGENT = "agent"

def mock_skill(name):
    """スキルデコレータのモック"""
    def decorator(func):
        func._skill_name = name
        return func
    return decorator

# python-a2aモジュールのモックを設定
with patch.dict('sys.modules', {
    'python_a2a': MagicMock(
        A2AServer=MockA2AServer,
        skill=mock_skill,
        Message=MockMessage,
        TextContent=MockTextContent,
        MessageRole=MockMessageRole
    )
}):
    # テスト対象のインポート
    from libs.quality.servants.quality_watcher_servant import QualityWatcherServant
    from libs.quality.servants.test_forge_servant import TestForgeServant
    from libs.quality.servants.comprehensive_guardian_servant import ComprehensiveGuardianServant
    from libs.quality.quality_pipeline_orchestrator import QualityPipelineOrchestrator

class TestQualityServantsMock:
    """品質サーバント統合テスト（モック版）"""
    
    @pytest.fixture
    def quality_watcher(self):
        """QualityWatcherサーバントのフィクスチャ"""
        servant = QualityWatcherServant(port=8810)
        # エンジンをモック化
        servant.static_engine = AsyncMock()
        servant.static_engine.initialize = AsyncMock(return_value=True)
        return servant
    
    @pytest.fixture
    def test_forge(self):
        """TestForgeサーバントのフィクスチャ"""
        servant = TestForgeServant(port=8811)
        # エンジンをモック化
        servant.test_engine = AsyncMock()
        servant.test_engine.initialize = AsyncMock(return_value=True)
        return servant
    
    @pytest.fixture
    def comprehensive_guardian(self):
        """ComprehensiveGuardianサーバントのフィクスチャ"""
        servant = ComprehensiveGuardianServant(port=8812)
        # エンジンをモック化
        servant.comprehensive_engine = AsyncMock()
        servant.comprehensive_engine.initialize = AsyncMock(return_value=True)
        return servant
    
    @pytest.mark.asyncio
    async def test_quality_watcher_initialization(self, quality_watcher):
        """QualityWatcherの初期化テスト"""
        result = await quality_watcher.initialize()
        assert result == True
        assert quality_watcher.agent_name == "quality-watcher"
        assert quality_watcher.port == 8810
        assert quality_watcher.command == "analyze_static_quality"
    
    @pytest.mark.asyncio
    async def test_quality_watcher_analyze_approved(self, quality_watcher):
        """QualityWatcher: 承認ケースのテスト"""
        # エンジン結果のモック
        quality_watcher.static_engine.execute_full_pipeline.return_value = Mock(
            quality_score=96.5,
            issues_found=3,

            scores={"pylint": 9.7, "mypy": 100, "format": 100, "import": 100},
            syntax_errors=0,
            security_issues=0,
            critical_issues=0,
            major_issues=2,
            minor_issues=1,
            complexity_score=15,
            maintainability_index=85,
            type_coverage_percentage=95
        )
        
        # メッセージ作成
        message = MockMessage(
            content=MockTextContent(text=json.dumps({"target_path": "/test/path"})),
            role=MockMessageRole.USER
        )
        
        # コマンド実行
        result_message = await quality_watcher.analyze_static_quality(message)
        
        # 結果検証
        result = json.loads(result_message.content.text)
        assert result["servant"] == "quality-watcher"
        assert result["command"] == "analyze_static_quality"
        assert result["verdict"] == "APPROVED"
        assert result["quality_score"] == 96.5
        assert result["certification"] == "ELDER_GRADE"
        assert result["iron_will_compliance"] == 100.0
    
    @pytest.mark.asyncio
    async def test_quality_watcher_analyze_conditional(self, quality_watcher):
        """QualityWatcher: 条件付き承認ケースのテスト"""
        # エンジン結果のモック（スコアが低い）
        quality_watcher.static_engine.execute_full_pipeline.return_value = Mock(
            quality_score=87.0,
            issues_found=10,

            scores={"pylint": 8.5, "mypy": 95, "format": 100, "import": 100},
            syntax_errors=0,
            security_issues=0
        )
        
        message = MockMessage(
            content=MockTextContent(text=json.dumps({"target_path": "/test/path"})),
            role=MockMessageRole.USER
        )
        
        result_message = await quality_watcher.analyze_static_quality(message)
        result = json.loads(result_message.content.text)
        
        assert result["verdict"] == "CONDITIONAL"
        assert result["quality_score"] == 87.0
        assert result["certification"] == "APPRENTICE_GRADE"
        assert "requirements" in result
        assert result["auto_fix_available"] == True
    
    @pytest.mark.asyncio
    async def test_test_forge_initialization(self, test_forge):
        """TestForgeの初期化テスト"""
        result = await test_forge.initialize()
        assert result == True
        assert test_forge.agent_name == "test-forge"
        assert test_forge.port == 8811
        assert test_forge.command == "verify_test_quality"
    
    @pytest.mark.asyncio
    async def test_test_forge_verify_approved(self, test_forge):
        """TestForge: 承認ケースのテスト"""
        # エンジン結果のモック
        test_forge.test_engine.execute_full_test_suite.return_value = Mock(
            coverage_percentage=97.5,
            tdd_quality_score=92.0,
            test_failures=0,
            total_tests=150,
            passed_tests=150,
            unit_test_count=100,
            integration_test_count=30,
            property_test_count=20,
            tox_environments_tested=["py38", "py39", "py310"],
            test_to_code_ratio=1.2,
            tdd_cycle_detected=True,
            test_naming_compliance=95.0,
            assertion_quality_score=90.0,
            function_count=80,
            edge_case_coverage=85,
            test_duplication_percentage=5
        )
        
        message = MockMessage(
            content=MockTextContent(text=json.dumps({"target_path": "/test/path"})),
            role=MockMessageRole.USER
        )
        
        result_message = await test_forge.verify_test_quality(message)
        result = json.loads(result_message.content.text)
        
        assert result["servant"] == "test-forge"
        assert result["command"] == "verify_test_quality"
        assert result["verdict"] == "APPROVED"
        assert result["coverage"] == 97.5
        assert result["tdd_score"] == 92.0
        assert result["certification"] == "TDD_MASTER"
        assert result["tdd_compliant"] == True
    
    @pytest.mark.asyncio
    async def test_comprehensive_guardian_initialization(self, comprehensive_guardian):
        """ComprehensiveGuardianの初期化テスト"""
        result = await comprehensive_guardian.initialize()
        assert result == True
        assert comprehensive_guardian.agent_name == "comprehensive-guardian"
        assert comprehensive_guardian.port == 8812
        assert comprehensive_guardian.command == "assess_comprehensive_quality"
    
    @pytest.mark.asyncio
    async def test_comprehensive_guardian_assess_approved(self, comprehensive_guardian):
        """ComprehensiveGuardian: 承認ケースのテスト"""
        # エンジン結果のモック
        comprehensive_guardian.comprehensive_engine.execute_all_analyses.return_value = Mock(
            documentation_score=92.0,
            security_score=94.0,
            config_score=91.0,
            performance_score=93.0,
            zero_vulnerabilities=True,
            full_api_documentation=True,
            security_vulnerabilities=0,
            config_issues=0,
            missing_docs_count=2,
            performance_bottlenecks=0,
            config_errors=0,
            doc_completeness=95,
            api_doc_coverage=98,
            security_compliance_level="HIGH",
            config_consistency=92,
            config_best_practices_score=90,
            performance_efficiency=94,
            optimization_level="ADVANCED",
            target_path="/test/path",
            overall_quality_score=92.5
        )
        
        message = MockMessage(
            content=MockTextContent(text=json.dumps({"target_path": "/test/path"})),
            role=MockMessageRole.USER
        )
        
        result_message = await comprehensive_guardian.assess_comprehensive_quality(message)
        result = json.loads(result_message.content.text)
        
        assert result["servant"] == "comprehensive-guardian"
        assert result["command"] == "assess_comprehensive_quality"
        assert result["verdict"] == "APPROVED"
        assert result["overall_score"] == pytest.approx(92.5, 0.1)
        assert result["certification"] == "COMPREHENSIVE_EXCELLENCE"
        assert len(result["achievements"]) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, quality_watcher):
        """エラーハンドリングのテスト"""
        # エンジンがエラーを投げる
        quality_watcher.static_engine.execute_full_pipeline.side_effect = Exception("Engine error")
        
        message = MockMessage(
            content=MockTextContent(text=json.dumps({"target_path": "/test/path"})),
            role=MockMessageRole.USER
        )
        
        result_message = await quality_watcher.analyze_static_quality(message)
        result = json.loads(result_message.content.text)
        
        assert result["success"] == False
        assert result["verdict"] == "ERROR"
        assert "error" in result
        assert result["error"] == "Engine error"
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """オーケストレータの初期化テスト"""
        orchestrator = QualityPipelineOrchestrator()
        assert orchestrator.name == "quality-pipeline-orchestrator"
        assert len(orchestrator.servants) == 3
        assert "quality-watcher" in orchestrator.servants
        assert "test-forge" in orchestrator.servants
        assert "comprehensive-guardian" in orchestrator.servants
    
    @pytest.mark.asyncio
    async def test_orchestrator_mock_pipeline(self):
        """オーケストレータのモックパイプラインテスト"""
        orchestrator = QualityPipelineOrchestrator()
        
        # HTTPクライアントをモック
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            
            # 成功レスポンスのモック
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = {
                "content": {
                    "text": json.dumps({
                        "verdict": "APPROVED",
                        "quality_score": 95.0,
                        "certification": "ELDER_GRADE"
                    })
                }
            }
            success_response.raise_for_status = Mock()
            
            mock_async_client.post.return_value = success_response
            
            # パイプライン実行
            result = await orchestrator.execute_pipeline("/test/path")
            
            # 基本的な結果確認
            assert "pipeline_id" in result
            assert result["target_path"] == "/test/path"
            assert "blocks" in result
            assert "overall_status" in result
            assert "duration_seconds" in result

class TestServantFeatures:
    """サーバント機能テスト"""
    
    @pytest.fixture
    def quality_watcher(self):
        """QualityWatcherサーバントのフィクスチャ"""
        servant = QualityWatcherServant(port=8810)
        servant.static_engine = AsyncMock()
        servant.static_engine.initialize = AsyncMock(return_value=True)
        return servant
    
    @pytest.fixture
    def test_forge(self):
        """TestForgeサーバントのフィクスチャ"""
        servant = TestForgeServant(port=8811)
        servant.test_engine = AsyncMock()
        servant.test_engine.initialize = AsyncMock(return_value=True)
        return servant
    
    @pytest.fixture
    def comprehensive_guardian(self):
        """ComprehensiveGuardianサーバントのフィクスチャ"""
        servant = ComprehensiveGuardianServant(port=8812)
        servant.comprehensive_engine = AsyncMock()
        servant.comprehensive_engine.initialize = AsyncMock(return_value=True)
        return servant
    
    @pytest.mark.asyncio
    async def test_health_check_functionality(self, quality_watcher, test_forge, comprehensive_guardian):
        """ヘルスチェック機能のテスト"""
        message = MockMessage(
            content=MockTextContent(text="{}"),
            role=MockMessageRole.USER
        )
        
        # 各サーバントのヘルスチェック
        for servant in [quality_watcher, test_forge, comprehensive_guardian]:
            health_result = await servant.health_check(message)
            health_data = json.loads(health_result.content.text)
            
            assert health_data["status"] == "healthy"
            assert "servant" in health_data
            assert "port" in health_data
            assert "metrics" in health_data
    
    @pytest.mark.asyncio
    async def test_quality_certificate_generation(self, comprehensive_guardian):
        """品質証明書生成機能のテスト"""
        # 最新結果を返すようモック
        result_mock = Mock()
        result_mock.overall_quality_score = 92.0
        result_mock.target_path = "/test/path"
        result_mock.documentation_score = 91
        result_mock.security_score = 93
        result_mock.config_score = 90
        result_mock.performance_score = 94
        result_mock.doc_completeness = 95
        result_mock.api_doc_coverage = 98
        result_mock.security_vulnerabilities = 0
        result_mock.security_compliance_level = "HIGH"
        result_mock.config_consistency = 92
        result_mock.config_best_practices_score = 90
        result_mock.performance_efficiency = 94
        result_mock.optimization_level = "ADVANCED"
        result_mock.__dict__ = {"test": "data"}  # hashlib用
        
        comprehensive_guardian.comprehensive_engine.get_latest_result = AsyncMock(
            return_value=result_mock
        )
        
        message = MockMessage(
            content=MockTextContent(text=json.dumps({"target_path": "/test/path"})),
            role=MockMessageRole.USER
        )
        
        result_message = await comprehensive_guardian.generate_quality_certificate(message)
        result = json.loads(result_message.content.text)
        
        assert result["success"] == True
        assert "certificate" in result
        cert = result["certificate"]
        assert "certificate_id" in cert
        assert cert["issuer"] == "ComprehensiveGuardian - Elder Council"
        assert cert["project_info"]["certification_level"] == "GOLD"

# テスト実行用
if __name__ == "__main__":
    pytest.main([__file__, "-v"])