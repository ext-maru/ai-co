#!/usr/bin/env python3
"""
Tests for Technical Requirements Extractor
Phase 4の技術要件抽出エンジンのテスト
"""

import pytest
import json
from typing import Dict, List, Any

from elders_guild.elder_tree.elder_system.technical_requirements_extractor import (
    TechnicalRequirementsExtractor,
    RequirementType,
    TechnicalRequirement,
    TechnicalStack,
    ExtractionResult
)


class TestTechnicalRequirementsExtractor:
    """技術要件抽出エンジンのテスト"""
    
    @pytest.fixture
    def extractor(self):
        """テスト用エクストラクタ"""
        return TechnicalRequirementsExtractor()
    
    @pytest.fixture
    def sample_implementation_issue(self):
        """実装系Issueのサンプル"""
        return {
            'title': '⚡ Performance optimization #83 - Implement caching layer',
            'body': '''## Description
We need to implement a Redis-based caching layer for our FastAPI application.

## Requirements
- Response time should be under 100ms for cached requests
- Support for 10000 concurrent users
- 90% test coverage required
- Use Redis for caching
- Implement cache invalidation strategy
- Add monitoring and metrics

## Technical Details
- Python 3.11+
- FastAPI framework
- PostgreSQL database
- Docker deployment

## Security
- Ensure all cached data is encrypted
- Implement proper authentication for cache access
''',
            'labels': ['enhancement', 'performance', 'backend']
        }
    
    @pytest.fixture
    def sample_oauth_issue(self):
        """OAuth実装Issueのサンプル"""
        return {
            'title': 'Add OAuth2.0 authentication system',
            'body': '''Implement OAuth2.0 authentication with the following providers:
                pass
- Google
- GitHub
- Microsoft

Requirements:
- JWT token based authentication
- Refresh token support
- User profile synchronization
- Secure password hashing with bcrypt
- Role-based access control (RBAC)

The system should handle 5000 requests/sec with 50ms average response time.
All endpoints must use HTTPS.
''',
            'labels': ['feature', 'security', 'authentication']
        }
    
    def test_extract_technical_stack(self, extractor, sample_implementation_issue):
        """技術スタック抽出のテスト"""
        result = extractor.extract_requirements(sample_implementation_issue)
        tech_stack = result.technical_stack
        
        # 言語
        assert 'python' in tech_stack.languages
        
        # フレームワーク
        assert 'fastapi' in tech_stack.frameworks
        
        # データベース
        assert 'postgresql' in tech_stack.databases
        assert 'redis' in tech_stack.databases
        
        # サービス
        assert 'docker' in tech_stack.services
    
    def test_extract_performance_requirements(self, extractor, sample_implementation_issue):
        """パフォーマンス要件抽出のテスト"""
        result = extractor.extract_requirements(sample_implementation_issue)
        
        perf_reqs = [req for req in result.requirements 
                     if req.requirement_type == RequirementType.PERFORMANCE]
        
        assert len(perf_reqs) >= 2  # レスポンスタイムと同時接続数
        
        # レスポンスタイム要件
        response_time_req = next((req for req in perf_reqs 
                                 if 'response_time' in req.category), None)
        assert response_time_req is not None
        assert '100' in response_time_req.specifications.get('value', '')
        
        # 同時接続数要件
        concurrency_req = next((req for req in perf_reqs 
                               if 'concurrency' in req.category), None)
        assert concurrency_req is not None
        assert '10000' in str(concurrency_req.specifications.get('value', ''))
    
    def test_extract_security_requirements(self, extractor, sample_oauth_issue):
        """セキュリティ要件抽出のテスト"""
        result = extractor.extract_requirements(sample_oauth_issue)
        
        sec_reqs = [req for req in result.requirements 
                    if req.requirement_type == RequirementType.SECURITY]
        
        assert len(sec_reqs) >= 1
        
        security_req = sec_reqs[0]
        aspects = security_req.specifications.get('aspects', [])
        
        # セキュリティ関連キーワードが検出されているか
        expected_aspects = ['authentication', 'oauth', 'jwt', 'token', 
                           'password', 'bcrypt', 'rbac', 'https']
        found_aspects = [aspect for aspect in expected_aspects if aspect in aspects]
        assert len(found_aspects) >= 4
    
    def test_extract_testing_requirements(self, extractor, sample_implementation_issue):
        """テスト要件抽出のテスト"""
        result = extractor.extract_requirements(sample_implementation_issue)
        
        test_reqs = [req for req in result.requirements 
                     if req.requirement_type == RequirementType.TESTING]
        
        assert len(test_reqs) >= 1
        
        test_req = test_reqs[0]
        assert test_req.specifications.get('coverage_target') == 90
        assert '90% test coverage' in test_req.constraints[0]
    
    def test_extract_functional_requirements(self, extractor, sample_implementation_issue):
        """機能要件抽出のテスト"""
        result = extractor.extract_requirements(sample_implementation_issue)
        
        func_reqs = [req for req in result.requirements 
                     if req.requirement_type == RequirementType.FUNCTIONAL]
        
        assert len(func_reqs) >= 2  # キャッシュ実装とモニタリング
        
        # 機能要件の説明に実装すべき内容が含まれているか
        descriptions = [req.description for req in func_reqs]
        assert any('cache' in desc.lower() for desc in descriptions)
    
    def test_generate_implementation_steps(self, extractor, sample_implementation_issue):
        """実装ステップ生成のテスト"""
        result = extractor.extract_requirements(sample_implementation_issue)
        
        assert len(result.implementation_steps) >= 3
        
        # ステップの順序確認
        steps_by_phase = {step['phase']: step for step in result.implementation_steps}
        
        # セットアップフェーズ
        assert 'setup' in steps_by_phase
        setup_tasks = steps_by_phase['setup']['tasks']
        assert any('Python' in task for task in setup_tasks)
        
        # 実装フェーズ
        assert 'implementation' in steps_by_phase
        
        # テストフェーズ
        assert 'testing' in steps_by_phase
    
    def test_estimate_complexity(self, extractor, sample_oauth_issue):
        """複雑度推定のテスト"""
        result = extractor.extract_requirements(sample_oauth_issue)
        
        # OAuth実装は複雑なので、高い複雑度が期待される
        assert result.estimated_complexity in ['high', 'very_high']
    
    def test_identify_risk_factors(self, extractor):
        """リスク要因識別のテスト"""
        # セキュリティ要件のないIssue
        simple_issue = {
            'title': 'Add simple calculator function',
            'body': 'Implement add, subtract, multiply, divide functions',
            'labels': ['feature']
        }
        
        result = extractor.extract_requirements(simple_issue)
        
        # セキュリティリスクが識別されるべき
        security_risks = [risk for risk in result.risk_factors 
                         if risk['type'] == 'security']
        assert len(security_risks) >= 1
        
        # テストリスクも識別されるべき
        quality_risks = [risk for risk in result.risk_factors 
                        if risk['type'] == 'quality']
        assert len(quality_risks) >= 1
    
    def test_extract_dependencies(self, extractor, sample_implementation_issue):
        """依存関係抽出のテスト"""
        result = extractor.extract_requirements(sample_implementation_issue)
        
        # FastAPIプロジェクトの基本的な依存関係
        expected_deps = ['fastapi', 'uvicorn', 'pydantic']
        found_deps = [dep for dep in expected_deps if dep in result.dependencies]
        assert len(found_deps) >= 2
    
    def test_generate_implementation_prompt(self, extractor, sample_implementation_issue):
        """実装プロンプト生成のテスト"""
        result = extractor.extract_requirements(sample_implementation_issue)
        prompt = extractor.generate_implementation_prompt(result)
        
        # プロンプトに必要な要素が含まれているか
        assert '## Technical Stack' in prompt
        assert '## Requirements' in prompt
        assert '## Implementation Steps' in prompt
        
        # 具体的な技術要素が含まれているか
        assert 'Python' in prompt or 'python' in prompt
        assert 'FastAPI' in prompt or 'fastapi' in prompt
        assert 'Redis' in prompt or 'redis' in prompt
    
    def test_empty_issue_handling(self, extractor):
        """空のIssueの処理テスト"""
        empty_issue = {
            'title': '',
            'body': '',
            'labels': []
        }
        
        result = extractor.extract_requirements(empty_issue)
        
        # エラーにならず、空の結果が返される
        assert isinstance(result, ExtractionResult)
        assert result.technical_stack.is_empty()
        assert len(result.requirements) == 0
        assert result.estimated_complexity == 'low'
    
    def test_complex_technical_stack(self, extractor):
        """複雑な技術スタックのテスト"""
        complex_issue = {
            'title': 'Microservices migration',
            'body': '''Migrate monolith to microservices:
            - Frontend: React with TypeScript
            - Backend: Python (FastAPI) + Go (gRPC services) + Node.js (GraphQL gateway)
            - Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
            - Infrastructure: Kubernetes on AWS
            - Testing: Jest, pytest, mocha
            ''',
            'labels': ['architecture', 'migration']
        }
        
        result = extractor.extract_requirements(complex_issue)
        tech_stack = result.technical_stack
        
        # 複数の言語
        assert len(tech_stack.languages) >= 3
        assert all(lang in tech_stack.languages for lang in ['python', 'go', 'javascript'])
        
        # 複数のデータベース
        assert len(tech_stack.databases) >= 3
        
        # 高い複雑度
        assert result.estimated_complexity in ['high', 'very_high']
        
        # 複雑性に関するリスク
        complexity_risks = [risk for risk in result.risk_factors 
                           if risk['type'] == 'complexity']
        assert len(complexity_risks) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])