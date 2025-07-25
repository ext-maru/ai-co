#!/usr/bin/env python3
"""
Tests for Elder Flow Quality Gate V2
Phase 3強化版品質ゲートのテスト
"""

import pytest
import asyncio

import os
from pathlib import Path

from libs.elder_flow_quality_gate_v2 import (
    ElderFlowQualityGateV2, AdaptiveQualityConfig,
    ElderFlowQualityIntegrationV2
)
from libs.elder_system.issue_classifier_v2 import IssueCategory

class TestAdaptiveQualityConfig:
    """適応型品質設定のテスト"""
    
    def test_implementation_oriented_config(self):
        """実装系Issue用設定のテスト"""
        config = AdaptiveQualityConfig(IssueCategory.IMPLEMENTATION_ORIENTED)
        
        assert config.minimum_quality_score == 85.0
        assert config.iron_will_compliance_rate == 1.0
        assert config.maximum_security_risk_level == 3
        assert config.complexity_threshold == 8
        assert config.test_coverage_minimum == 90.0
    
    def test_design_oriented_config(self):
        """設計系Issue用設定のテスト"""
        config = AdaptiveQualityConfig(IssueCategory.DESIGN_ORIENTED)
        
        assert config.minimum_quality_score == 70.0
        assert config.iron_will_compliance_rate == 1.0
        assert config.maximum_security_risk_level == 5
        assert config.complexity_threshold == 15
        assert config.documentation_coverage_minimum == 90.0
    
    def test_maintenance_oriented_config(self):
        """保守系Issue用設定のテスト"""
        config = AdaptiveQualityConfig(IssueCategory.MAINTENANCE_ORIENTED)
        
        assert config.minimum_quality_score == 80.0
        assert config.iron_will_compliance_rate == 1.0
        assert config.maximum_security_risk_level == 4
        assert config.complexity_threshold == 10

class TestElderFlowQualityGateV2:
    """品質ゲートV2のテスト"""
    
    @pytest.fixture
    def quality_gate(self):
        """テスト用品質ゲートインスタンス"""
        return ElderFlowQualityGateV2()
    
    @pytest.fixture
    def clean_code(self):
        """クリーンなコードサンプル"""
        return '''#!/usr/bin/env python3
"""
Clean implementation of a feature
"""

def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two integers"""
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Both arguments must be integers")
    
    result = a + b
    return result

def main():
    """Main function"""
    try:
        result = calculate_sum(5, 10)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
'''
    
    @pytest.fixture
    def iron_will_violation_code(self):
        """Iron Will違反を含むコード"""
        return '''#!/usr/bin/env python3
"""
Code with Iron Will violations
"""

def process_data(data):

    pass

def calculate_result():

    return 42

def quick_fix():

    import time

    return "done"
'''
    
    @pytest.fixture
    def security_violation_code(self):
        """セキュリティ違反を含むコード"""
        return '''#!/usr/bin/env python3
"""
Code with security violations
"""

def execute_command(cmd):
    """Execute system command"""
    import os
    os.system(cmd)  # Security risk!
    
def load_data(filename):
    """Load pickled data"""
    import pickle
    with open(filename, 'rb') as f:
        return pickle.load(f)  # Unsafe deserialization
'''
    
    @pytest.mark.asyncio
    async def test_clean_code_passes_quality_gate(self, quality_gate, clean_code):
        """クリーンなコードが品質ゲートを通過することを確認"""

            f.write(clean_code)

        try:
            context = {
                'task_name': 'Implement feature #123',

            }
            
            results = await quality_gate.check_quality(context)
            
            assert results['passed'] is True
            assert results['quality_score'] >= 70.0
            assert results['iron_will_violations'] == 0
            assert results['critical_violations'] == 0
            
        finally:

    @pytest.mark.asyncio
    async def test_iron_will_violation_fails_gate(self, quality_gate, iron_will_violation_code):
        """Iron Will違反が品質ゲートで不合格になることを確認"""

            f.write(iron_will_violation_code)

        try:
            context = {
                'task_name': 'Implement feature #123',

            }
            
            results = await quality_gate.check_quality(context)
            
            assert results['passed'] is False
            assert results['iron_will_violations'] > 0

            violations = results['violations']
            violation_messages = [v.get('message', '') for v in violations]

        finally:

    @pytest.mark.asyncio
    async def test_security_violation_fails_gate(self, quality_gate, security_violation_code):
        """セキュリティ違反が品質ゲートで不合格になることを確認"""

            f.write(security_violation_code)

        try:
            context = {
                'task_name': 'Implement security feature #456',

            }
            
            results = await quality_gate.check_quality(context)
            
            assert results['passed'] is False
            
            # セキュリティ違反が検出されることを確認
            violations = results['violations']
            security_violations = [v for v in violations 
                                 if v.get('violation_type') == 'security_violation']
            assert len(security_violations) > 0
            
        finally:

    @pytest.mark.asyncio
    async def test_implementation_oriented_stricter_standards(self, quality_gate):
        """実装系Issueにより厳格な基準が適用されることを確認"""
        # 品質スコア75点前後のコード（設計系なら合格、実装系なら不合格）
        # ドキュメント不足、中程度の複雑度
        mediocre_code = '''#!/usr/bin/env python3
def calculate_data(items):
    result = 0
    for item in items:
        if item > 10:
            result += item * 2
        elif item > 5:
            result += item
        else:
            pass
    return result

def process_values(values):
    output = []
    for val in values:
        if val % 2 == 0:
            output.append(val * 2)
        else:
            output.append(val)
    return output

def check_conditions(x, y, z):
    if x > 0 and y > 0:
        if z > 0:
            return x + y + z
        else:
            return x + y
    return 0
'''

            f.write(mediocre_code)

        try:
            # 実装系Issueのコンテキスト
            impl_context = {
                'task_name': '⚡ Performance optimization #83',
                'task_description': 'Optimize caching and parallel processing',

            }
            
            # 設計系Issueのコンテキスト
            design_context = {
                'task_name': '[ARCHITECTURE] System design #189',
                'task_description': 'Design system architecture',

            }
            
            impl_results = await quality_gate.check_quality(impl_context)
            design_results = await quality_gate.check_quality(design_context)
            
            # 実装系は85点必要なので不合格
            assert impl_results['passed'] is False
            assert impl_results['applied_standards']['minimum_score'] == 85.0
            
            # 設計系は70点でOKなので合格
            assert design_results['passed'] is True
            assert design_results['applied_standards']['minimum_score'] == 70.0
            
        finally:

    @pytest.mark.asyncio
    async def test_feedback_generation(self, quality_gate, iron_will_violation_code):
        """フィードバック生成のテスト"""

            f.write(iron_will_violation_code)

        try:
            context = {
                'task_name': 'Implement feature #123',

            }
            
            results = await quality_gate.check_quality(context)
            
            # フィードバックが生成されることを確認
            assert 'violations' in results
            assert results['iron_will_violations'] > 0
            
        finally:

    @pytest.mark.asyncio
    async def test_quality_trends_recording(self, quality_gate, clean_code):
        """品質トレンドの記録テスト"""

            f.write(clean_code)

        try:
            # 複数回実行して履歴を作成
            for i in range(3):
                context = {
                    'task_name': f'Test task #{i}',

                }
                await quality_gate.check_quality(context)
            
            # トレンドが取得できることを確認
            trends = await quality_gate.get_quality_trends()
            
            assert 'total_checks' in trends
            assert trends['total_checks'] >= 3
            
        finally:

class TestElderFlowQualityIntegrationV2:
    """Elder Flow統合のテスト"""
    
    @pytest.fixture
    def integration(self):
        """統合インターフェースのインスタンス"""
        return ElderFlowQualityIntegrationV2()
    
    @pytest.mark.asyncio
    async def test_elder_flow_integration_format(self, integration):
        """Elder Flow互換フォーマットのテスト"""
        good_code = '''#!/usr/bin/env python3
"""Good quality code"""

def hello():
    """Say hello"""
    return "Hello, World!"
'''

            f.write(good_code)

        try:
            context = {
                'task_name': 'Test task',

            }
            
            results = await integration.run_quality_gate(context)
            
            # Elder Flow互換フォーマットの確認
            assert 'passed' in results
            assert 'score' in results
            assert 'details' in results
            assert 'timestamp' in results
            
            details = results['details']
            assert 'files_analyzed' in details
            assert 'violations' in details
            assert 'iron_will_compliant' in details
            assert 'issue_category' in details
            
        finally:

if __name__ == "__main__":
    pytest.main([__file__, "-v"])