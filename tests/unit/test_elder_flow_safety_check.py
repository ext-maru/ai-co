#!/usr/bin/env python3
"""
Elder Flow Safety Check System Test Suite

Elder Flow Phase 2: Elder Flow適用前の安全チェック機能
実装系Issueに対してElder Flowを適用する前の安全性確認
"""

import pytest
from typing import Dict, Any
import json
from unittest.mock import Mock, patch, MagicMock

from libs.elder_system.elder_flow_safety_check import (
    ElderFlowSafetyChecker, 
    SafetyCheckResult,
    SafetyLevel,
    ElderFlowRecommendation
)
from libs.elder_system.issue_classifier import IssueType, ClassificationResult


class TestElderFlowSafetyChecker:
    """Elder Flow安全チェックシステムのテストスイート"""
    
    @pytest.fixture
    def safety_checker(self):
        """テスト用safety checkerインスタンス"""
        return ElderFlowSafetyChecker()
    
    @pytest.fixture
    def sample_classification_results(self) -> Dict[str, ClassificationResult]:
        """サンプル分類結果"""
        return {
            "design": ClassificationResult(
                issue_type=IssueType.DESIGN,
                confidence=0.95,
                keywords=["architecture", "design"],
                recommended_flow="elder_flow",
                technical_requirements=None,
                safety_checks=None,
                priority="high"
            ),
            "implementation": ClassificationResult(
                issue_type=IssueType.IMPLEMENTATION,
                confidence=0.85,
                keywords=["oauth", "implementation"],
                recommended_flow="manual_implementation",
                technical_requirements=["oauth", "jwt", "security"],
                safety_checks=["elder_flow_compatibility", "technical_complexity", "security_review"],
                priority="high"
            ),
            "simple_implementation": ClassificationResult(
                issue_type=IssueType.IMPLEMENTATION,
                confidence=0.9,
                keywords=["add", "feature"],
                recommended_flow="manual_implementation",
                technical_requirements=["api_endpoints"],
                safety_checks=["elder_flow_compatibility", "technical_complexity"],
                priority="medium"
            ),
            "bug_fix": ClassificationResult(
                issue_type=IssueType.BUG_FIX,
                confidence=0.88,
                keywords=["bug", "fix"],
                recommended_flow="bug_fix_flow",
                technical_requirements=None,
                safety_checks=["regression_test", "impact_analysis"],
                priority="urgent"
            )
        }
    
    def test_check_elder_flow_safety_design_issue(self, safety_checker, sample_classification_results):
        """設計系Issue（安全）のチェック"""
        classification = sample_classification_results["design"]
        issue = {
            "number": 189,
            "title": "[ARCHITECTURE] System redesign",
            "body": "Full system architecture redesign"
        }
        
        result = safety_checker.check_elder_flow_safety(issue, classification)
        
        assert result.safety_level == SafetyLevel.SAFE
        assert result.recommendation == ElderFlowRecommendation.PROCEED
        assert result.confidence >= 0.9
        assert not result.warnings
        assert "Design issues are well-suited for Elder Flow" in result.reasoning
    
    def test_check_elder_flow_safety_complex_implementation(self, safety_checker, sample_classification_results):
        """複雑な実装系Issue（危険）のチェック"""
        classification = sample_classification_results["implementation"]
        issue = {
            "number": 83,
            "title": "⚡ Continue.dev Phase 2 - パフォーマンス最適化",
            "body": """
            OAuth2.0認証システムの実装
            - JWTトークン管理
            - セキュリティ考慮事項多数
            - 既存システムとの統合
            """
        }
        
        result = safety_checker.check_elder_flow_safety(issue, classification)
        
        assert result.safety_level == SafetyLevel.DANGEROUS
        assert result.recommendation == ElderFlowRecommendation.BLOCK
        assert result.confidence >= 0.75  # 危険な実装でも妥当な信頼度
        assert len(result.warnings) > 0
        assert any("security" in w.lower() for w in result.warnings)
        assert "technical complexity" in result.reasoning.lower()  # 複雑度が含まれていればOK
    
    def test_check_elder_flow_safety_simple_implementation(self, safety_checker, sample_classification_results):
        """単純な実装系Issue（警告）のチェック"""
        classification = sample_classification_results["simple_implementation"]
        issue = {
            "number": 100,
            "title": "Add simple API endpoint",
            "body": "Add a new GET endpoint to return user info"
        }
        
        result = safety_checker.check_elder_flow_safety(issue, classification)
        
        assert result.safety_level == SafetyLevel.WARNING
        assert result.recommendation == ElderFlowRecommendation.CAUTION
        assert result.confidence >= 0.7
        assert len(result.warnings) > 0
        assert result.alternative_suggestions is not None
        assert any("manual" in s.lower() for s in result.alternative_suggestions)
    
    def test_technical_complexity_assessment(self, safety_checker):
        """技術的複雑度の評価テスト"""
        # 低複雑度
        low_complexity = {
            "technical_requirements": ["api_endpoints"],
            "keywords": ["add", "simple"]
        }
        score = safety_checker._assess_technical_complexity(low_complexity)
        assert score < 0.3
        
        # 中複雑度
        medium_complexity = {
            "technical_requirements": ["database", "api_endpoints"],
            "keywords": ["refactor", "optimize"]
        }
        score = safety_checker._assess_technical_complexity(medium_complexity)
        assert 0.3 <= score < 0.7
        
        # 高複雑度
        high_complexity = {
            "technical_requirements": ["security", "oauth", "jwt", "database", "parallel_processing"],
            "keywords": ["complex", "integrate", "security", "performance"]
        }
        score = safety_checker._assess_technical_complexity(high_complexity)
        assert score >= 0.7
    
    def test_risk_factors_detection(self, safety_checker):
        """リスク要因検出のテスト"""
        # セキュリティリスク
        security_issue = {
            "title": "Implement authentication",
            "body": "Add OAuth and JWT token management",
            "technical_requirements": ["oauth", "jwt", "security"]
        }
        risks = safety_checker._detect_risk_factors(security_issue)
        assert "security_critical" in risks
        assert "authentication_system" in risks
        
        # データベースリスク
        db_issue = {
            "title": "Database migration",
            "body": "Migrate all user data to new schema",
            "technical_requirements": ["database"]
        }
        risks = safety_checker._detect_risk_factors(db_issue)
        assert "data_migration" in risks
        
        # パフォーマンスリスク
        perf_issue = {
            "title": "Performance optimization",
            "body": "Implement caching and parallel processing",
            "technical_requirements": ["caching", "parallel_processing"]
        }
        risks = safety_checker._detect_risk_factors(perf_issue)
        assert "performance_critical" in risks
    
    def test_elder_flow_compatibility_score(self, safety_checker):
        """Elder Flow互換性スコアの計算テスト"""
        # 高互換性（設計系）
        design_classification = ClassificationResult(
            issue_type=IssueType.DESIGN,
            confidence=0.95,
            keywords=["architecture"],
            recommended_flow="elder_flow",
            technical_requirements=None,
            safety_checks=None,
            priority="high"
        )
        score = safety_checker._calculate_elder_flow_compatibility(design_classification, {})
        assert score >= 0.9
        
        # 低互換性（複雑実装系）
        impl_classification = ClassificationResult(
            issue_type=IssueType.IMPLEMENTATION,
            confidence=0.85,
            keywords=["oauth", "security"],
            recommended_flow="manual_implementation",
            technical_requirements=["oauth", "jwt", "security", "database"],
            safety_checks=["security_review"],
            priority="high"
        )
        score = safety_checker._calculate_elder_flow_compatibility(
            impl_classification,
            {"risk_factors": ["security_critical", "authentication_system"]}
        )
        assert score < 0.3
    
    def test_generate_warnings(self, safety_checker):
        """警告メッセージ生成のテスト"""
        analysis_result = {
            "technical_complexity": 0.8,
            "risk_factors": ["security_critical", "data_migration"],
            "elder_flow_compatibility": 0.2
        }
        
        warnings = safety_checker._generate_warnings(analysis_result)
        
        assert len(warnings) > 0
        assert any("high technical complexity" in w for w in warnings)
        assert any("security" in w.lower() for w in warnings)
        assert any("data migration" in w.lower() for w in warnings)
    
    def test_generate_alternative_suggestions(self, safety_checker):
        """代替案提案の生成テスト"""
        classification = ClassificationResult(
            issue_type=IssueType.IMPLEMENTATION,
            confidence=0.85,
            keywords=["oauth"],
            recommended_flow="manual_implementation",
            technical_requirements=["oauth", "security"],
            safety_checks=None,
            priority="high"
        )
        
        suggestions = safety_checker._generate_alternative_suggestions(
            classification,
            {"technical_complexity": 0.7}
        )
        
        assert len(suggestions) > 0
        assert any("manual implementation" in s for s in suggestions)
        assert any("expert review" in s.lower() for s in suggestions)
        assert any("phase" in s.lower() or "incremental" in s.lower() for s in suggestions)
    
    def test_batch_safety_check(self, safety_checker, sample_classification_results):
        """バッチ安全チェックのテスト"""
        issues = [
            {
                "number": 1,
                "title": "Design new architecture",
                "body": "System redesign",
                "classification": sample_classification_results["design"]
            },
            {
                "number": 2,
                "title": "Implement OAuth",
                "body": "Add OAuth authentication",
                "classification": sample_classification_results["implementation"]
            },
            {
                "number": 3,
                "title": "Fix login bug",
                "body": "Fix authentication error",
                "classification": sample_classification_results["bug_fix"]
            }
        ]
        
        results = safety_checker.check_batch(issues)
        
        assert len(results) == 3
        assert results[0].safety_level == SafetyLevel.SAFE
        assert results[1].safety_level == SafetyLevel.DANGEROUS
        assert results[2].safety_level in [SafetyLevel.SAFE, SafetyLevel.WARNING]
    
    def test_safety_report_generation(self, safety_checker):
        """安全性レポート生成のテスト"""
        results = [
            SafetyCheckResult(
                safety_level=SafetyLevel.SAFE,
                recommendation=ElderFlowRecommendation.PROCEED,
                confidence=0.95,
                warnings=[],
                reasoning="Safe for Elder Flow",
                alternative_suggestions=None
            ),
            SafetyCheckResult(
                safety_level=SafetyLevel.DANGEROUS,
                recommendation=ElderFlowRecommendation.BLOCK,
                confidence=0.9,
                warnings=["High security risk", "Complex implementation"],
                reasoning="Too complex for Elder Flow",
                alternative_suggestions=["Manual implementation recommended"]
            ),
            SafetyCheckResult(
                safety_level=SafetyLevel.WARNING,
                recommendation=ElderFlowRecommendation.CAUTION,
                confidence=0.75,
                warnings=["Medium complexity"],
                reasoning="Proceed with caution",
                alternative_suggestions=["Consider breaking into smaller tasks"]
            )
        ]
        
        report = safety_checker.generate_safety_report(results)
        
        assert report["total_checks"] == 3
        assert report["safety_distribution"]["safe"] == 1
        assert report["safety_distribution"]["dangerous"] == 1
        assert report["safety_distribution"]["warning"] == 1
        assert report["recommendation_distribution"]["proceed"] == 1
        assert report["recommendation_distribution"]["block"] == 1
        assert report["recommendation_distribution"]["caution"] == 1
        assert report["average_confidence"] > 0.8
    
    def test_edge_cases(self, safety_checker):
        """エッジケースのテスト"""
        # 空の分類結果
        empty_classification = ClassificationResult(
            issue_type=IssueType.UNKNOWN,
            confidence=0.0,
            keywords=[],
            recommended_flow="manual_review",
            technical_requirements=None,
            safety_checks=None,
            priority="medium"
        )
        
        result = safety_checker.check_elder_flow_safety({}, empty_classification)
        assert result.safety_level == SafetyLevel.WARNING
        assert result.recommendation == ElderFlowRecommendation.CAUTION
        
        # 非常に高い信頼度の設計Issue
        perfect_design = ClassificationResult(
            issue_type=IssueType.DESIGN,
            confidence=1.0,
            keywords=["architecture", "design", "blueprint"],
            recommended_flow="elder_flow",
            technical_requirements=None,
            safety_checks=None,
            priority="high"
        )
        
        result = safety_checker.check_elder_flow_safety(
            {"title": "[ARCHITECTURE] Complete redesign"},
            perfect_design
        )
        assert result.safety_level == SafetyLevel.SAFE
        assert result.confidence >= 0.95
    
    @patch('libs.elder_system.elder_flow_safety_check.logger')
    def test_error_handling(self, mock_logger, safety_checker):
        """エラーハンドリングのテスト"""
        # Noneを渡した場合
        result = safety_checker.check_elder_flow_safety(None, None)
        assert result.safety_level == SafetyLevel.WARNING
        assert result.recommendation == ElderFlowRecommendation.CAUTION
        mock_logger.error.assert_called()
    
    def test_configuration_override(self):
        """設定オーバーライドのテスト"""
        custom_config = {
            "complexity_thresholds": {
                "low": 0.2,
                "medium": 0.5,
                "high": 0.8
            },
            "high_risk_keywords": ["custom_risk", "special_danger"]
        }
        
        custom_checker = ElderFlowSafetyChecker(config=custom_config)
        
        # カスタムリスクキーワードのテスト
        issue = {
            "title": "Add custom_risk feature",
            "body": "This has special_danger considerations"
        }
        risks = custom_checker._detect_risk_factors(issue)
        assert len(risks) > 0
    
    def test_integration_with_issue_classifier(self, safety_checker):
        """Issue Classifierとの統合テスト"""
        from libs.elder_system.issue_classifier import IssueTypeClassifier
        
        classifier = IssueTypeClassifier()
        issue = {
            "number": 83,
            "title": "⚡ Continue.dev Phase 2 - パフォーマンス最適化",
            "body": "Implement caching and parallel processing",
            "labels": ["performance", "implementation"]
        }
        
        # 分類実行
        classification = classifier.classify(issue)
        
        # 安全チェック実行
        safety_result = safety_checker.check_elder_flow_safety(issue, classification)
        
        # 統合結果の検証
        assert classification.issue_type == IssueType.IMPLEMENTATION
        assert safety_result.safety_level in [SafetyLevel.WARNING, SafetyLevel.DANGEROUS]
        assert safety_result.recommendation != ElderFlowRecommendation.PROCEED