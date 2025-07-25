#!/usr/bin/env python3
"""
Tests for Elder Flow Enhancement Engine
Phase 2-4統合エンジンのテスト
"""

import pytest
import json
from typing import Dict, Any

from libs.elder_system.elder_flow_enhancement_engine import (
    ElderFlowEnhancementEngine, ElderFlowMode
)
from libs.elder_system.issue_classifier_v2 import IssueCategory


class TestElderFlowEnhancementEngine:
    """Elder Flow強化エンジンのテスト"""
    
    @pytest.fixture
    def engine(self):
        """テスト用エンジン"""
        return ElderFlowEnhancementEngine()
    
    @pytest.fixture
    def implementation_issue(self):
        """実装系Issue"""
        return {
            'number': 83,
            'title': '⚡ Performance optimization - Implement caching',
            'body': '''Implement Redis caching with:
            - Response time under 50ms
            - Support 5000 concurrent users
            - Python FastAPI framework
            ''',
            'labels': ['enhancement', 'performance']
        }
    
    @pytest.fixture
    def design_issue(self):
        """設計系Issue"""
        return {
            'number': 100,
            'title': '[ARCHITECTURE] Design microservices architecture',
            'body': '''Design the system architecture for microservices:
            - Service boundaries
            - Communication patterns
            - Data flow diagrams
            - API design documentation
            ''',
            'labels': ['architecture', 'design']
        }
    
    @pytest.fixture
    def maintenance_issue(self):
        """保守系Issue"""
        return {
            'number': 150,
            'title': 'Refactor authentication module',
            'body': '''Refactor the existing auth module:
            - Update to use JWT tokens
            - Improve code structure
            - Add missing tests
            ''',
            'labels': ['refactoring', 'maintenance']
        }
    
    def test_analyze_implementation_issue(self, engine, implementation_issue):
        """実装系Issueの分析テスト"""
        result = engine.analyze_issue(implementation_issue)
        
        assert result['issue_category'] == IssueCategory.IMPLEMENTATION_ORIENTED.value
        assert result['elder_flow_mode'] == ElderFlowMode.IMPLEMENTATION.value
        assert result['recommended_approach'] == 'technical_implementation'
        
        # 技術分析が含まれているか
        assert 'technical_analysis' in result
        tech_analysis = result['technical_analysis']
        assert 'python' in tech_analysis['technical_stack']['languages']
        assert 'fastapi' in tech_analysis['technical_stack']['frameworks']
        assert 'redis' in tech_analysis['technical_stack']['databases']
        
        # 実装プロンプトが生成されているか
        assert 'implementation_prompt' in result
        assert 'Redis' in result['implementation_prompt']
    
    def test_analyze_design_issue(self, engine, design_issue):
        """設計系Issueの分析テスト"""
        result = engine.analyze_issue(design_issue)
        
        assert result['issue_category'] == IssueCategory.DESIGN_ORIENTED.value
        assert result['elder_flow_mode'] == ElderFlowMode.DESIGN.value
        assert result['recommended_approach'] == 'elder_flow_design'
        
        # 設計分析が含まれているか
        assert 'design_analysis' in result
        design = result['design_analysis']
        assert design['has_architecture'] is True
        assert design['has_documentation'] is True
        assert design['has_diagrams'] is True
        assert design['has_api_design'] is True
        assert design['estimated_documents'] > 0
    
    def test_analyze_maintenance_issue(self, engine, maintenance_issue):
        """保守系Issueの分析テスト"""
        result = engine.analyze_issue(maintenance_issue)
        
        assert result['issue_category'] == IssueCategory.MAINTENANCE_ORIENTED.value
        assert result['elder_flow_mode'] == ElderFlowMode.HYBRID.value
        assert result['recommended_approach'] == 'hybrid'
        
        # 両方の分析が含まれているか
        assert 'technical_analysis' in result
        assert 'design_analysis' in result
    
    def test_elder_flow_config_generation(self, engine, implementation_issue):
        """Elder Flow設定生成のテスト"""
        result = engine.analyze_issue(implementation_issue)
        
        config = result['elder_flow_config']
        assert config['mode'] == ElderFlowMode.IMPLEMENTATION.value
        
        # 品質要件
        quality = config['quality_requirements']
        assert quality['minimum_score'] == 85  # 実装系は高い基準
        assert quality['iron_will_compliance'] is True
        assert quality['test_coverage'] == 90
        
        # 実行フェーズ
        phases = config['execution_phases']
        assert '4_sages_consultation' in phases
        assert 'technical_implementation' in phases
        assert 'unit_test_creation' in phases
        assert 'quality_gate' in phases
    
    def test_risk_assessment(self, engine):
        """リスク評価のテスト"""
        # 複雑なIssue
        complex_issue = {
            'number': 200,
            'title': 'Implement polyglot microservices backend',
            'body': '''Implement new microservices backend with:
            - API Gateway in Node.js Express
            - Authentication service in Go
            - Main business logic in Python FastAPI
            - Real-time notifications in Node.js with WebSockets
            - Databases: PostgreSQL, MongoDB, Redis
            - Must handle 10000 requests/sec
            - Response time under 50ms
            - Kubernetes deployment on AWS EKS
            ''',
            'labels': ['feature', 'backend', 'performance']
        }
        
        result = engine.analyze_issue(complex_issue)
        risk = result['risk_assessment']
        
        assert risk['overall_risk_level'] in ['medium', 'high']
        assert risk['mitigation_required'] is True
        assert len(risk['risk_factors']) > 0
        
        # 複雑度によるリスクが含まれているか
        complexity_risks = [r for r in risk['risk_factors'] 
                           if r['type'] == 'technical_complexity']
        assert len(complexity_risks) > 0
    
    def test_generate_implementation_prompt(self, engine, implementation_issue):
        """実装プロンプト生成のテスト"""
        result = engine.analyze_issue(implementation_issue)
        prompt = engine.generate_elder_flow_prompt(result)
        
        # プロンプトの構成要素
        assert 'IMPLEMENTATION Mode' in prompt
        assert 'Issue: #83' in prompt
        assert '## Implementation Requirements' in prompt
        assert 'Follow TDD approach' in prompt
        assert '90% test coverage' in prompt
        assert 'No TODO/FIXME comments' in prompt
    
    def test_generate_design_prompt(self, engine, design_issue):
        """設計プロンプト生成のテスト"""
        result = engine.analyze_issue(design_issue)
        prompt = engine.generate_elder_flow_prompt(result)
        
        assert 'DESIGN Mode' in prompt
        assert '## Design Requirements' in prompt
        assert 'architecture documentation' in prompt
        assert 'API endpoints' in prompt
        assert 'documentation files' in prompt
    
    def test_error_handling(self, engine):
        """エラーハンドリングのテスト"""
        # 不正なIssueデータ
        invalid_issue = {
            'number': None,
            'title': None,
            'body': None
        }
        
        result = engine.analyze_issue(invalid_issue)
        
        # エラーが含まれているが、クラッシュしない
        assert 'error' in result or 'recommended_approach' in result
        assert result['elder_flow_mode'] == ElderFlowMode.DESIGN.value
    
    def test_confidence_based_risk(self, engine):
        """信頼度に基づくリスク評価のテスト"""
        # あいまいなIssue
        ambiguous_issue = {
            'number': 300,
            'title': 'Update system',
            'body': 'Need to update the system with new features',
            'labels': []
        }
        
        result = engine.analyze_issue(ambiguous_issue)
        
        # 低信頼度の場合、リスクが上がる
        if result.get('confidence', 1.0) < 0.7:
            risk = result['risk_assessment']
            uncertainty_risks = [r for r in risk['risk_factors']
                               if r['type'] == 'classification_uncertainty']
            assert len(uncertainty_risks) > 0
    
    def test_technical_stack_complexity(self, engine):
        """技術スタックの複雑度判定テスト"""
        multi_lang_issue = {
            'number': 400,
            'title': 'Build polyglot service',
            'body': '''Implement service using:
            - Python for API
            - Go for performance-critical parts
            - JavaScript for frontend
            - PostgreSQL and MongoDB
            ''',
            'labels': ['feature']
        }
        
        result = engine.analyze_issue(multi_lang_issue)
        tech = result['technical_analysis']['technical_stack']
        
        assert tech['is_complex'] is True
        assert len(tech['languages']) >= 3
        
        # 複雑度が高いはず
        assert result['technical_analysis']['complexity'] in ['high', 'very_high']
        
        # リスク緩和計画が追加されているか
        phases = result['elder_flow_config']['execution_phases']
        assert 'risk_mitigation_planning' in phases


if __name__ == "__main__":
    pytest.main([__file__, "-v"])