"""
🧪 Elder Servants統合テストスイート
Phase 3 最終検証：統合パフォーマンステスト

EldersLegacy準拠テスト: Iron Will品質基準達成確認
"""

import pytest
import asyncio
import sys
import os

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from elders_guild.elder_tree.elder_servants.integrations.production.integration_test import (
    ElderIntegrationTestSuite, TestSuite, TestScenario
)


class TestElderServantsIntegration:
    """Elder Servants統合テストクラス"""
    
    @pytest.fixture
    async def test_suite(self):
        """テストスイートセットアップ"""
        return ElderIntegrationTestSuite()
    
    @pytest.mark.asyncio
    async def test_performance_target_achievement(self, test_suite):
        """パフォーマンス目標達成テスト"""
        request = {
            'test_suite': 'performance',
            'include_stress_test': False
        }
        
        result = await test_suite.process_request(request)
        
        # パフォーマンス改善が目標を達成しているか確認
        improvement = result.get('performance_comparison', {}).get('improvement_percentage', 0)
        target = 50.0  # 50%改善目標
        
        assert improvement >= target, f"Performance improvement {improvement:0.1f}% did not meet target {target}%"
        assert result.get('meets_target', False), "Performance target not achieved"
    
    @pytest.mark.asyncio
    async def test_reliability_requirements(self, test_suite):
        """信頼性要件テスト"""
        request = {
            'test_suite': 'reliability',
            'include_stress_test': False
        }
        
        result = await test_suite.process_request(request)
        
        # 成功率確認
        success_rate = result.get('test_execution_summary', {}).get('overall_success_rate', 0)
        assert success_rate >= 99.0, f"Success rate {success_rate:0.1f}% below minimum 99%"
    
    @pytest.mark.asyncio
    async def test_integration_completeness(self, test_suite):
        """統合完全性テスト"""
        request = {
            'test_suite': 'integration',
            'include_stress_test': False
        }
        
        result = await test_suite.process_request(request)
        
        # 全コンポーネントテスト実行確認
        detailed_results = result.get('detailed_results', [])
        tested_scenarios = set(r.get('scenario') for r in detailed_results)
        
        # 必須シナリオが実行されているか確認
        required_scenarios = {
            'BASELINE_MEASUREMENT',
            'CACHE_PERFORMANCE', 
            'ASYNC_OPTIMIZATION',
            'PROXY_OVERHEAD',
            'ERROR_RECOVERY',
            'HEALTH_MONITORING',
            'FULL_INTEGRATION'
        }
        
        missing_scenarios = required_scenarios - tested_scenarios
        assert not missing_scenarios, f"Missing test scenarios: {missing_scenarios}"
    
    @pytest.mark.asyncio
    async def test_iron_will_compliance(self, test_suite):
        """Iron Will基準コンプライアンステスト"""
        request = {
            'test_suite': 'quality',
            'include_stress_test': False
        }
        
        result = await test_suite.process_request(request)
        
        # Iron Will基準確認
        iron_will = result.get('iron_will_compliance', {})
        
        assert iron_will.get('root_solution_compliance', 0) >= 95.0, "Root solution compliance below 95%"
        assert iron_will.get('dependency_completeness', 0) >= 100.0, "Dependency completeness below 100%"
        assert iron_will.get('test_coverage', 0) >= 95.0, "Test coverage below 95%"
        assert iron_will.get('security_score', 0) >= 90.0, "Security score below 90%"
        assert iron_will.get('performance_score', 0) >= 85.0, "Performance score below 85%"
        assert iron_will.get('maintainability', 0) >= 80.0, "Maintainability below 80%"
    
    @pytest.mark.asyncio
    async def test_stress_test_stability(self, test_suite):
        """ストレステスト安定性"""
        request = {
            'test_suite': 'scalability',
            'include_stress_test': True
        }
        
        result = await test_suite.process_request(request)
        
        # ストレステスト結果確認
        detailed_results = result.get('detailed_results', [])
        stress_results = [r for r in detailed_results if r.get('scenario') == 'STRESS_TEST']
        
        assert len(stress_results) > 0, "Stress test not executed"
        
        stress_result = stress_results[0]
        assert stress_result.get('success_rate', 0) >= 95.0, "Stress test success rate below 95%"
    
    @pytest.mark.asyncio
    async def test_request_validation(self, test_suite):
        """リクエスト妥当性テスト"""
        # 有効なリクエスト
        valid_request = {'test_suite': 'all'}
        assert test_suite.validate_request(valid_request)
        
        # 無効なリクエスト
        invalid_request = "invalid"
        assert not test_suite.validate_request(invalid_request)
    
    @pytest.mark.asyncio
    async def test_capabilities_coverage(self, test_suite):
        """能力カバレッジテスト"""
        capabilities = test_suite.get_capabilities()
        
        expected_capabilities = [
            "performance_testing",
            "integration_testing", 
            "reliability_testing",
            "stress_testing",
            "benchmark_comparison",
            "quality_assessment"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities, f"Missing capability: {capability}"
    
    @pytest.mark.asyncio
    async def test_full_integration_workflow(self, test_suite):
        """フル統合ワークフローテスト"""
        request = {
            'test_suite': 'all',
            'include_stress_test': True
        }
        
        result = await test_suite.process_request(request)
        
        # 基本構造確認
        assert 'test_execution_summary' in result
        assert 'performance_comparison' in result
        assert 'detailed_results' in result
        assert 'final_assessment' in result
        assert 'meets_target' in result
        assert 'iron_will_compliance' in result
        
        # 実行サマリー確認
        summary = result['test_execution_summary']
        assert summary.get('total_tests', 0) > 0
        assert summary.get('execution_time', 0) > 0
        assert summary.get('overall_success_rate', 0) > 0
        
        # 最終評価確認
        assessment = result['final_assessment']
        assert 'performance_target' in assessment
        assert 'reliability_assessment' in assessment
        assert 'quality_metrics' in assessment
        assert 'overall_status' in assessment


# スタンドアローン実行
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])