#!/usr/bin/env python3
"""
Implementation Issue Detector Test Suite

Elder Flow Phase 2: 実装系Issue検出・警告システムのテスト
実装系Issueを高精度で検出し、適切な警告を提供する
"""

import pytest
from typing import Dict, Any, List
import json
from unittest.mock import Mock, patch, MagicMock

from libs.elder_system.implementation_issue_detector import (
    ImplementationIssueDetector,
    DetectionResult,
    WarningLevel,
    ImplementationRecommendation
)
from libs.elder_system.issue_classifier import IssueType, IssueTypeClassifier
from libs.elder_system.elder_flow_safety_check import ElderFlowSafetyChecker, SafetyLevel


class TestImplementationIssueDetector:
    """実装系Issue検出・警告システムのテストスイート"""
    
    @pytest.fixture
    def detector(self):
        """テスト用detectorインスタンス"""
        return ImplementationIssueDetector()
    
    @pytest.fixture
    def sample_issues(self) -> List[Dict[str, Any]]:
        """テスト用Issueサンプル"""
        return [
            {
                "number": 83,
                "title": "⚡ Continue.dev Phase 2 - パフォーマンス最適化",
                "body": """
                Continue.devのパフォーマンスを最適化する必要があります：
                - キャッシング機構の実装
                - 並列処理の導入
                - メモリ使用量の削減
                """,
                "labels": ["performance", "implementation"]
            },
            {
                "number": 101,
                "title": "OAuth2.0認証システムの実装",
                "body": """
                新しいOAuth2.0認証システムを実装します：
                - JWTトークンの生成と検証
                - リフレッシュトークンの管理
                - 認可フローの実装
                """,
                "labels": ["security", "implementation"]
            },
            {
                "number": 189,
                "title": "[ARCHITECTURE] エルダーズギルドシステムアーキテクチャ再設計",
                "body": """
                システムアーキテクチャの全面的な見直しを行います。
                マイクロサービス化とスケーラビリティの向上を目指します。
                """,
                "labels": ["architecture", "design"]
            },
            {
                "number": 200,
                "title": "ドキュメント更新: API使用ガイド",
                "body": """
                APIドキュメントを最新の仕様に更新します。
                新しいエンドポイントの説明を追加します。
                """,
                "labels": ["documentation"]
            }
        ]
    
    def test_detect_single_implementation_issue(self, detector, sample_issues):
        """単一の実装系Issue検出テスト"""
        issue = sample_issues[0]  # Continue.dev最適化
        
        result = detector.detect(issue)
        
        assert result.is_implementation
        assert result.warning_level == WarningLevel.HIGH
        assert result.confidence >= 0.8
        assert len(result.warnings) > 0
        assert result.recommendation in [
            ImplementationRecommendation.MANUAL_REVIEW,
            ImplementationRecommendation.EXPERT_REQUIRED
        ]  # パフォーマンス最適化は専門家レビューが推奨される場合もある
        assert "Continue.dev" in result.technical_context
    
    def test_detect_security_implementation_issue(self, detector, sample_issues):
        """セキュリティ関連実装系Issue検出テスト"""
        issue = sample_issues[1]  # OAuth実装
        
        result = detector.detect(issue)
        
        assert result.is_implementation
        assert result.warning_level == WarningLevel.CRITICAL
        assert result.confidence >= 0.85
        assert any("security" in w.lower() for w in result.warnings)
        assert result.recommendation == ImplementationRecommendation.EXPERT_REQUIRED
        assert "OAuth" in result.technical_context
        assert "JWT" in result.technical_context
    
    def test_detect_non_implementation_issue(self, detector, sample_issues):
        """非実装系Issue検出テスト"""
        # アーキテクチャ設計Issue
        design_issue = sample_issues[2]
        result = detector.detect(design_issue)
        
        assert not result.is_implementation
        assert result.warning_level == WarningLevel.NONE
        assert result.recommendation == ImplementationRecommendation.ELDER_FLOW_SAFE
        
        # ドキュメントIssue
        doc_issue = sample_issues[3]
        result = detector.detect(doc_issue)
        
        assert not result.is_implementation
        assert result.warning_level == WarningLevel.NONE
        assert result.recommendation == ImplementationRecommendation.ELDER_FLOW_SAFE
    
    def test_batch_detection(self, detector, sample_issues):
        """バッチ検出テスト"""
        results = detector.detect_batch(sample_issues)
        
        assert len(results) == len(sample_issues)
        
        # 実装系Issueの数を確認
        impl_count = sum(1 for r in results if r.is_implementation)
        assert impl_count == 2  # Continue.dev と OAuth
        
        # 警告レベルの分布
        critical_count = sum(1 for r in results if r.warning_level == WarningLevel.CRITICAL)
        high_count = sum(1 for r in results if r.warning_level == WarningLevel.HIGH)
        
        assert critical_count >= 1  # OAuth
        assert high_count >= 1  # Continue.dev
    
    def test_warning_generation(self, detector):
        """警告メッセージ生成のテスト"""
        # 複雑な実装Issue
        complex_issue = {
            "number": 300,
            "title": "Complete system rewrite",
            "body": """
            Rewrite the entire authentication and database layer:
            - Replace all authentication logic
            - Migrate to new database schema
            - Implement new caching layer
            - Add real-time synchronization
            """,
            "labels": ["implementation", "major-change"]
        }
        
        result = detector.detect(complex_issue)
        
        assert result.is_implementation
        assert result.warning_level == WarningLevel.CRITICAL
        assert len(result.warnings) >= 3
        assert any("complex" in w.lower() for w in result.warnings)
        assert any("risk" in w.lower() for w in result.warnings)
    
    def test_technical_context_extraction(self, detector):
        """技術的コンテキスト抽出のテスト"""
        tech_issue = {
            "number": 400,
            "title": "Implement GraphQL API with subscriptions",
            "body": """
            Add GraphQL support:
            - GraphQL schema definition
            - Resolver implementation
            - WebSocket subscriptions
            - Apollo Server integration
            """,
            "labels": ["api", "implementation"]
        }
        
        result = detector.detect(tech_issue)
        
        assert "GraphQL" in result.technical_context
        assert "WebSocket" in result.technical_context
        assert "Apollo" in result.technical_context
        assert result.technical_complexity_score >= 0.6  # GraphQL実装は中程度以上の複雑度
    
    def test_recommendation_logic(self, detector):
        """推奨事項ロジックのテスト"""
        # 単純な実装
        simple_impl = {
            "number": 500,
            "title": "Add simple utility function",
            "body": "Add a helper function to format dates",
            "labels": ["implementation", "minor"]
        }
        
        result = detector.detect(simple_impl)
        assert result.recommendation in [
            ImplementationRecommendation.MANUAL_REVIEW,
            ImplementationRecommendation.PROCEED_WITH_CAUTION
        ]
        
        # 危険な実装
        dangerous_impl = {
            "number": 501,
            "title": "Replace authentication system",
            "body": "Completely replace the authentication with new OAuth provider",
            "labels": ["implementation", "security", "breaking-change"]
        }
        
        result = detector.detect(dangerous_impl)
        assert result.recommendation == ImplementationRecommendation.EXPERT_REQUIRED
    
    def test_detection_report_generation(self, detector, sample_issues):
        """検出レポート生成のテスト"""
        results = detector.detect_batch(sample_issues)
        report = detector.generate_detection_report(results)
        
        assert "total_issues" in report
        assert "implementation_issues" in report
        assert "warning_distribution" in report
        assert "recommendation_distribution" in report
        assert "high_risk_issues" in report
        
        assert report["total_issues"] == len(sample_issues)
        assert report["implementation_issues"]["count"] == 2
        assert len(report["high_risk_issues"]) >= 1
    
    def test_integration_with_classifier_and_safety_check(self, detector):
        """IssueClassifierとSafetyCheckerとの統合テスト"""
        issue = {
            "number": 600,
            "title": "Implement payment processing system",
            "body": """
            Add payment processing:
            - Stripe integration
            - PCI compliance
            - Transaction logging
            - Refund handling
            """,
            "labels": ["implementation", "payment", "security"]
        }
        
        # 検出実行
        result = detector.detect(issue)
        
        # 統合結果の検証
        assert result.is_implementation
        assert result.warning_level == WarningLevel.CRITICAL
        assert result.classifier_result is not None
        assert result.safety_check_result is not None
        
        # 分類結果の確認
        assert result.classifier_result.issue_type == IssueType.IMPLEMENTATION
        
        # 安全チェック結果の確認
        assert result.safety_check_result.safety_level in [
            SafetyLevel.WARNING,
            SafetyLevel.DANGEROUS
        ]
    
    def test_edge_cases(self, detector):
        """エッジケースのテスト"""
        # 空のIssue
        empty_issue = {
            "number": 700,
            "title": "",
            "body": "",
            "labels": []
        }
        
        result = detector.detect(empty_issue)
        assert not result.is_implementation
        assert result.warning_level == WarningLevel.NONE
        
        # タイトルのみ
        title_only = {
            "number": 701,
            "title": "Implement new feature",
            "body": None,
            "labels": None
        }
        
        result = detector.detect(title_only)
        assert result.is_implementation
        assert result.confidence < 0.7  # 低い信頼度
    
    def test_warning_thresholds(self, detector):
        """警告閾値のテスト"""
        # 閾値ギリギリのケース
        threshold_issue = {
            "number": 800,
            "title": "Update API endpoint",
            "body": "Modify existing endpoint to add new parameter",
            "labels": ["implementation"]
        }
        
        result = detector.detect(threshold_issue)
        assert result.warning_level in [WarningLevel.LOW, WarningLevel.MEDIUM]
    
    def test_custom_configuration(self):
        """カスタム設定のテスト"""
        custom_config = {
            "high_risk_keywords": ["payment", "security", "production"],
            "warning_thresholds": {
                "critical": 0.9,
                "high": 0.7,
                "medium": 0.5,
                "low": 0.3
            }
        }
        
        custom_detector = ImplementationIssueDetector(config=custom_config)
        
        issue = {
            "number": 900,
            "title": "Update production payment system",
            "body": "Modify payment processing logic",
            "labels": ["implementation"]
        }
        
        result = custom_detector.detect(issue)
        assert result.warning_level == WarningLevel.CRITICAL
    
    @patch('libs.elder_system.implementation_issue_detector.logger')
    def test_error_handling(self, mock_logger, detector):
        """エラーハンドリングのテスト"""
        # 不正な入力
        result = detector.detect(None)
        assert not result.is_implementation
        assert result.warning_level == WarningLevel.NONE
        mock_logger.error.assert_called()
    
    def test_performance_optimization_detection(self, detector):
        """パフォーマンス最適化Issue検出の特殊テスト"""
        perf_issue = {
            "number": 1000,
            "title": "⚡ Continue.dev Phase 2 - パフォーマンス最適化",
            "body": "キャッシング機構の実装",
            "labels": ["performance"]
        }
        
        result = detector.detect(perf_issue)
        assert result.is_implementation
        assert "Continue.dev" in result.technical_context
        assert "performance" in [w.lower() for w in result.warnings] or \
               any("performance" in w.lower() for w in result.warnings)