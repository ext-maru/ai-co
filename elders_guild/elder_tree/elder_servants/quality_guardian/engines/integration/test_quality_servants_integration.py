"""
🧪 Quality Servants 統合テスト
3サーバントとオーケストレータの動作検証
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import httpx
from datetime import datetime

# テスト対象のインポート
from libs.quality.servants.quality_watcher_servant import QualityWatcherServant
from libs.quality.servants.test_forge_servant import TestForgeServant
from libs.quality.servants.comprehensive_guardian_servant import ComprehensiveGuardianServant
from libs.quality.quality_pipeline_orchestrator import QualityPipelineOrchestrator

class TestQualityServantsIntegration:
    """品質サーバント統合テストスイート"""
    
    @pytest.fixture
    def quality_watcher(self):
        """QualityWatcherサーバントのフィクスチャ"""
        servant = QualityWatcherServant(port=8810)
        # エンジンをモック化
        servant.static_engine = AsyncMock()
        return servant
    
    @pytest.fixture
    def test_forge(self):
        """TestForgeサーバントのフィクスチャ"""
        servant = TestForgeServant(port=8811)
        # エンジンをモック化
        servant.test_engine = AsyncMock()
        return servant
    
    @pytest.fixture
    def comprehensive_guardian(self):
        """ComprehensiveGuardianサーバントのフィクスチャ"""
        servant = ComprehensiveGuardianServant(port=8812)
        # エンジンをモック化
        servant.comprehensive_engine = AsyncMock()
        return servant
    
    @pytest.fixture
    def orchestrator(self):
        """オーケストレータのフィクスチャ"""
        return QualityPipelineOrchestrator()
    
    @pytest.mark.asyncio
    async def test_quality_watcher_analyze_command(self, quality_watcher):
        """QualityWatcher: analyze_static_qualityコマンドのテスト"""
        # エンジン結果のモック
        quality_watcher.static_engine.execute_full_pipeline.return_value = Mock(
            quality_score=96.5,
            issues_found=3,

            scores={"pylint": 9.7, "mypy": 100, "format": 100, "import": 100},
            syntax_errors=0,
            security_issues=0
        )
        
        # メッセージ作成
        from python_a2a import Message, TextContent, MessageRole
        message = Message(
            content=TextContent(text=json.dumps({"target_path": "/test/path"})),
            role=MessageRole.USER
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
    async def test_test_forge_verify_command(self, test_forge):
        """TestForge: verify_test_qualityコマンドのテスト"""
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
            assertion_quality_score=90.0
        )
        
        # メッセージ作成
        from python_a2a import Message, TextContent, MessageRole
        message = Message(
            content=TextContent(text=json.dumps({"target_path": "/test/path"})),
            role=MessageRole.USER
        )
        
        # コマンド実行
        result_message = await test_forge.verify_test_quality(message)
        
        # 結果検証
        result = json.loads(result_message.content.text)
        assert result["servant"] == "test-forge"
        assert result["command"] == "verify_test_quality"
        assert result["verdict"] == "APPROVED"
        assert result["coverage"] == 97.5
        assert result["tdd_score"] == 92.0
        assert result["certification"] == "TDD_MASTER"
        assert result["tdd_compliant"] == True
    
    @pytest.mark.asyncio
    async def test_comprehensive_guardian_assess_command(self, comprehensive_guardian):
        """ComprehensiveGuardian: assess_comprehensive_qualityコマンドのテスト"""
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
            performance_bottlenecks=0
        )
        
        # メッセージ作成
        from python_a2a import Message, TextContent, MessageRole
        message = Message(
            content=TextContent(text=json.dumps({"target_path": "/test/path"})),
            role=MessageRole.USER
        )
        
        # コマンド実行
        result_message = await comprehensive_guardian.assess_comprehensive_quality(message)
        
        # 結果検証
        result = json.loads(result_message.content.text)
        assert result["servant"] == "comprehensive-guardian"
        assert result["command"] == "assess_comprehensive_quality"
        assert result["verdict"] == "APPROVED"
        assert result["overall_score"] == pytest.approx(92.5, 0.1)  # 重み付き平均
        assert result["certification"] == "COMPREHENSIVE_EXCELLENCE"
        assert "📚 Documentation Excellence" in result["achievements"]
        assert "🔒 Zero Vulnerabilities" in result["achievements"]
    
    @pytest.mark.asyncio
    async def test_orchestrator_successful_pipeline(self, orchestrator):
        """オーケストレータ: 成功パイプラインのテスト"""
        # HTTPクライアントのモック
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # 各サーバントの成功レスポンスを設定
            mock_responses = [
                # Block A: QualityWatcher
                Mock(
                    status_code=200,
                    json=lambda: {
                        "content": {
                            "text": json.dumps({
                                "servant": "quality-watcher",
                                "verdict": "APPROVED",
                                "quality_score": 96.5,
                                "iron_will_compliance": 100.0,
                                "certification": "ELDER_GRADE",
                                "timestamp": datetime.now().isoformat()
                            })
                        }
                    }
                ),
                # Block B: TestForge
                Mock(
                    status_code=200,
                    json=lambda: {
                        "content": {
                            "text": json.dumps({
                                "servant": "test-forge",
                                "verdict": "APPROVED",
                                "coverage": 97.5,
                                "tdd_score": 92.0,
                                "tdd_compliant": True,
                                "certification": "TDD_MASTER",
                                "timestamp": datetime.now().isoformat()
                            })
                        }
                    }
                ),
                # Block C: ComprehensiveGuardian
                Mock(
                    status_code=200,
                    json=lambda: {
                        "content": {
                            "text": json.dumps({
                                "servant": "comprehensive-guardian",
                                "verdict": "APPROVED",
                                "overall_score": 92.5,
                                "certification": "COMPREHENSIVE_EXCELLENCE",
                                "breakdown": {},
                                "achievements": ["📚 Documentation Excellence"],
                                "timestamp": datetime.now().isoformat()
                            })
                        }
                    }
                )
            ]
            
            # postメソッドが順番に異なるレスポンスを返すように設定
            mock_client.post.side_effect = mock_responses
            
            # パイプライン実行
            result = await orchestrator.execute_pipeline("/test/path")
            
            # 結果検証
            assert result["success"] == True
            assert result["overall_status"] == "APPROVED"
            assert "quality_certificate" in result
            assert result["quality_certificate"]["overall_grade"] == "PLATINUM_EXCELLENCE"
            
            # 各ブロックの結果確認
            assert result["blocks"]["A"]["verdict"] == "APPROVED"
            assert result["blocks"]["B"]["verdict"] == "APPROVED"
            assert result["blocks"]["C"]["verdict"] == "APPROVED"
            
            # HTTPリクエストが3回呼ばれたことを確認
            assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_orchestrator_failure_at_block_b(self, orchestrator):
        """オーケストレータ: Block Bで失敗するパイプラインのテスト"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Block Aは成功、Block Bは失敗
            mock_responses = [
                # Block A: Success
                Mock(
                    status_code=200,
                    json=lambda: {
                        "content": {
                            "text": json.dumps({
                                "servant": "quality-watcher",
                                "verdict": "APPROVED",
                                "quality_score": 96.5,
                                "certification": "ELDER_GRADE"
                            })
                        }
                    }
                ),
                # Block B: Failure
                Mock(
                    status_code=200,
                    json=lambda: {
                        "content": {
                            "text": json.dumps({
                                "servant": "test-forge",
                                "verdict": "NEEDS_IMPROVEMENT",
                                "coverage": 75.0,
                                "tdd_score": 65.0,
                                "certification": "TDD_APPRENTICE"
                            })
                        }
                    }
                )
            ]
            
            mock_client.post.side_effect = mock_responses
            
            # パイプライン実行
            result = await orchestrator.execute_pipeline("/test/path")
            
            # 結果検証
            assert result["success"] == False
            assert result["overall_status"] == "FAILED_AT_BLOCK_B"
            assert result["failure_reason"] == "Test quality standards not met"
            assert "quality_certificate" not in result
            
            # Block Cは実行されないことを確認
            assert mock_client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_health_check_all_servants(self, quality_watcher, test_forge, comprehensive_guardian):
        """全サーバントのヘルスチェックテスト"""
        # 各サーバントのヘルスチェック
        from python_a2a import Message, TextContent, MessageRole
        message = Message(
            content=TextContent(text="{}"),
            role=MessageRole.USER
        )
        
        # QualityWatcher
        health_result = await quality_watcher.health_check(message)
        health_data = json.loads(health_result.content.text)
        assert health_data["status"] == "healthy"
        assert health_data["servant"] == "quality-watcher"
        assert health_data["port"] == 8810
        
        # TestForge
        health_result = await test_forge.health_check(message)
        health_data = json.loads(health_result.content.text)
        assert health_data["status"] == "healthy"
        assert health_data["servant"] == "test-forge"
        assert health_data["port"] == 8811
        
        # ComprehensiveGuardian
        health_result = await comprehensive_guardian.health_check(message)
        health_data = json.loads(health_result.content.text)
        assert health_data["status"] == "healthy"
        assert health_data["servant"] == "comprehensive-guardian"
        assert health_data["port"] == 8812
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_message(self, quality_watcher):
        """エラーハンドリング: 無効なメッセージのテスト"""
        from python_a2a import Message, TextContent, MessageRole
        
        # 無効なJSONメッセージ
        message = Message(
            content=TextContent(text="invalid json"),
            role=MessageRole.USER
        )
        
        # エンジンも適切な結果を返すようモック
        quality_watcher.static_engine.execute_full_pipeline.return_value = Mock(
            quality_score=0,
            issues_found=0
        )
        
        # エラーが適切に処理されることを確認
        result_message = await quality_watcher.analyze_static_quality(message)
        result = json.loads(result_message.content.text)
        
        # エラーでも正常なレスポンスが返ることを確認
        assert result["servant"] == "quality-watcher"
        assert "verdict" in result

class TestIntegrationScenarios:
    """統合シナリオテスト"""
    
    @pytest.mark.asyncio
    async def test_complete_quality_pipeline_scenario(self):
        """完全な品質パイプラインシナリオテスト"""
        orchestrator = QualityPipelineOrchestrator()
        
        # シナリオ: 高品質プロジェクトの評価
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # 全ブロック高品質の結果
            high_quality_responses = [
                # Block A: 優秀な静的解析結果
                Mock(
                    status_code=200,
                    json=lambda: {
                        "content": {
                            "text": json.dumps({
                                "verdict": "APPROVED",
                                "quality_score": 98.5,
                                "iron_will_compliance": 100.0,
                                "certification": "ELDER_GRADE",
                                "details": {
                                    "pylint_score": 9.9,
                                    "type_safety": 100,
                                    "format_compliance": 100,
                                    "import_order": 100
                                }
                            })
                        }
                    }
                ),
                # Block B: 優秀なテスト品質
                Mock(
                    status_code=200,
                    json=lambda: {
                        "content": {
                            "text": json.dumps({
                                "verdict": "APPROVED",
                                "coverage": 99.2,
                                "tdd_score": 95.0,
                                "tdd_compliant": True,
                                "certification": "TDD_MASTER",
                                "details": {
                                    "total_tests": 500,
                                    "passed_tests": 500,
                                    "test_types": {
                                        "unit": 350,
                                        "integration": 100,
                                        "property": 50
                                    }
                                }
                            })
                        }
                    }
                ),
                # Block C: 優秀な包括品質
                Mock(
                    status_code=200,
                    json=lambda: {
                        "content": {
                            "text": json.dumps({
                                "verdict": "APPROVED",
                                "overall_score": 96.0,
                                "certification": "COMPREHENSIVE_EXCELLENCE",
                                "breakdown": {
                                    "documentation": {"score": 95, "grade": "EXCELLENT"},
                                    "security": {"score": 98, "grade": "EXCELLENT"},
                                    "configuration": {"score": 94, "grade": "VERY_GOOD"},
                                    "performance": {"score": 97, "grade": "EXCELLENT"}
                                },
                                "achievements": [
                                    "📚 Documentation Excellence",
                                    "🛡️ Security Champion",
                                    "⚡ Performance Leader",
                                    "🔒 Zero Vulnerabilities"
                                ]
                            })
                        }
                    }
                )
            ]
            
            mock_client.post.side_effect = high_quality_responses
            
            # パイプライン実行
            result = await orchestrator.execute_pipeline("/high-quality/project")
            
            # 最高品質の認定を確認
            assert result["success"] == True
            assert result["quality_certificate"]["overall_grade"] == "PLATINUM_EXCELLENCE"
            assert orchestrator.successful_pipelines == 1
            assert orchestrator.failed_pipelines == 0

# テスト実行用
if __name__ == "__main__":
    pytest.main([__file__, "-v"])