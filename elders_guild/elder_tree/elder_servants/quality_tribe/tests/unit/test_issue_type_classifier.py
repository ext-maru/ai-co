#!/usr/bin/env python3
"""
Issue Type Classifier Test Suite

Elder Flow Phase 2: Issue種別判定システムのテスト
設計系・実装系・その他のIssueを高精度で分類する機能のテスト
"""

import pytest
from typing import Dict, Any
import json

from elders_guild.elder_tree.elder_system.issue_classifier import IssueTypeClassifier, IssueType


class TestIssueTypeClassifier:
    """Issue種別判定システムのテストスイート"""
    
    @pytest.fixture
    def classifier(self):
        """テスト用classifierインスタンス"""
        return IssueTypeClassifier()
    
    @pytest.fixture
    def sample_issues(self) -> Dict[str, Dict[str, Any]]:
        """テスト用のサンプルIssueデータ"""
        return {
            "architecture_issue": {
                "number": 189,
                "title": "[ARCHITECTURE] エルダーズギルドシステムアーキテクチャ再設計",
                "body": """
## 背景
現在のシステムアーキテクチャには以下の課題があります：
- スケーラビリティの限界
- モジュール間の密結合
- テストの困難さ

## 提案
新しいマイクロサービスアーキテクチャへの移行を提案します。
                """,
                "labels": ["architecture", "design"]
            },
            "performance_issue": {
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
            "oauth_issue": {
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
            "api_issue": {
                "number": 102,
                "title": "REST API v2の実装",
                "body": """
REST API v2を実装：
- OpenAPI 3.0仕様に準拠
- エンドポイントの設計と実装
- レート制限の実装
                """,
                "labels": ["api", "implementation"]
            },
            "bug_fix_issue": {
                "number": 103,
                "title": "バグ修正: ログイン画面でのエラー",
                "body": """
ログイン画面で特定の条件下でエラーが発生します。
再現手順：
1.0 メールアドレスに特殊文字を含む
2.0 パスワードを入力
3.0 ログインボタンをクリック
                """,
                "labels": ["bug", "urgent"]
            },
            "documentation_issue": {
                "number": 104,
                "title": "ドキュメント更新: API使用ガイド",
                "body": """
APIの使用ガイドを更新する必要があります：
- 新しいエンドポイントの説明追加
- サンプルコードの更新
- エラーレスポンスの説明
                """,
                "labels": ["documentation"]
            },
            "refactoring_issue": {
                "number": 105,
                "title": "リファクタリング: データベースアクセス層",
                "body": """
データベースアクセス層のリファクタリング：
- ORMの導入
- クエリの最適化
- トランザクション管理の改善
                """,
                "labels": ["refactoring", "implementation"]
            },
            "test_issue": {
                "number": 106,
                "title": "テストカバレッジの向上",
                "body": """
現在のテストカバレッジ75%を90%以上に向上させる：
- ユニットテストの追加
- 統合テストの実装
- E2Eテストの自動化
                """,
                "labels": ["testing", "quality"]
            }
        }
    
    def test_classify_design_issue(self, classifier, sample_issues):
        """設計系Issueの分類テスト"""
        issue = sample_issues["architecture_issue"]
        result = classifier.classify(issue)
        
        assert result.issue_type == IssueType.DESIGN
        assert result.confidence >= 0.9
        assert "architecture" in result.keywords
        assert result.recommended_flow == "elder_flow"
    
    def test_classify_implementation_issues(self, classifier, sample_issues):
        """実装系Issueの分類テスト"""
        implementation_issues = [
            "performance_issue",
            "oauth_issue", 
            "api_issue",
            "refactoring_issue"
        ]
        
        for issue_key in implementation_issues:
            issue = sample_issues[issue_key]
            result = classifier.classify(issue)
            
            assert result.issue_type == IssueType.IMPLEMENTATION
            assert result.confidence >= 0.8
            assert result.recommended_flow == "manual_implementation"
            assert result.technical_requirements is not None
    
    def test_classify_bug_fix_issue(self, classifier, sample_issues):
        """バグ修正Issueの分類テスト"""
        issue = sample_issues["bug_fix_issue"]
        result = classifier.classify(issue)
        
        assert result.issue_type == IssueType.BUG_FIX
        assert result.confidence >= 0.8
        assert "bug" in result.keywords
        assert result.priority == "urgent"
    
    def test_classify_documentation_issue(self, classifier, sample_issues):
        """ドキュメント系Issueの分類テスト"""
        issue = sample_issues["documentation_issue"]
        result = classifier.classify(issue)
        
        assert result.issue_type == IssueType.DOCUMENTATION
        assert result.confidence >= 0.9
        assert "documentation" in result.keywords
        assert result.recommended_flow == "documentation_flow"
    
    def test_classify_test_issue(self, classifier, sample_issues):
        """テスト系Issueの分類テスト"""
        issue = sample_issues["test_issue"]
        result = classifier.classify(issue)
        
        assert result.issue_type == IssueType.TEST
        assert result.confidence >= 0.8
        assert "testing" in result.keywords or "test" in result.keywords
    
    def test_extract_technical_requirements(self, classifier, sample_issues):
        """技術要件抽出のテスト"""
        # Continue.dev Issue
        continue_issue = sample_issues["performance_issue"]
        result = classifier.classify(continue_issue)
        
        assert "caching" in result.technical_requirements
        assert "parallel_processing" in result.technical_requirements
        assert "memory_optimization" in result.technical_requirements
        
        # OAuth Issue
        oauth_issue = sample_issues["oauth_issue"]
        result = classifier.classify(oauth_issue)
        
        assert "jwt" in result.technical_requirements
        assert "refresh_token" in result.technical_requirements
        assert "authorization_flow" in result.technical_requirements
    
    def test_confidence_levels(self, classifier):
        """信頼度レベルのテスト"""
        # 明確なアーキテクチャIssue
        clear_architecture = {
            "number": 200,
            "title": "[ARCHITECTURE] システム全体設計",
            "body": "アーキテクチャの全面的な見直し",
            "labels": ["architecture", "design"]
        }
        result = classifier.classify(clear_architecture)
        assert result.confidence >= 0.95
        
        # 曖昧なIssue
        ambiguous_issue = {
            "number": 201,
            "title": "改善提案",
            "body": "いくつかの改善点があります",
            "labels": []
        }
        result = classifier.classify(ambiguous_issue)
        assert result.confidence < 0.7
    
    def test_safety_check_recommendations(self, classifier, sample_issues):
        """安全チェック推奨のテスト"""
        # 実装系Issue
        impl_issue = sample_issues["performance_issue"]
        result = classifier.classify(impl_issue)
        
        assert result.safety_checks is not None
        assert "elder_flow_compatibility" in result.safety_checks
        assert "technical_complexity" in result.safety_checks
        assert "risk_assessment" in result.safety_checks
    
    def test_batch_classification(self, classifier, sample_issues):
        """バッチ分類のテスト"""
        issues = list(sample_issues.values())
        results = classifier.classify_batch(issues)
        
        assert len(results) == len(issues)
        
        # 分類結果の統計
        type_counts = {}
        for result in results:
            issue_type = result.issue_type.value
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        # 期待される分類数を確認
        assert type_counts.get("implementation", 0) >= 4
        assert type_counts.get("design", 0) >= 1
        assert type_counts.get("bug_fix", 0) >= 1
    
    def test_classification_report(self, classifier, sample_issues):
        """分類レポート生成のテスト"""
        issues = list(sample_issues.values())
        results = classifier.classify_batch(issues)
        report = classifier.generate_classification_report(results)
        
        assert "total_issues" in report
        assert "type_distribution" in report
        assert "confidence_stats" in report
        assert "recommendations" in report
        
        assert report["total_issues"] == len(issues)
        assert report["confidence_stats"]["average"] > 0.8
    
    def test_edge_cases(self, classifier):
        """エッジケースのテスト"""
        # 空のIssue
        empty_issue = {
            "number": 300,
            "title": "",
            "body": "",
            "labels": []
        }
        result = classifier.classify(empty_issue)
        assert result.issue_type == IssueType.UNKNOWN
        assert result.confidence < 0.5
        
        # 非常に長いタイトル
        long_title_issue = {
            "number": 301,
            "title": "実装 " * 100 + "OAuth認証システム",
            "body": "OAuth実装",
            "labels": []
        }
        result = classifier.classify(long_title_issue)
        assert result.issue_type == IssueType.IMPLEMENTATION
    
    def test_japanese_content_classification(self, classifier):
        """日本語コンテンツの分類テスト"""
        japanese_issues = {
            "設計": {
                "number": 400,
                "title": "【設計】新規サービスアーキテクチャ",
                "body": "マイクロサービス設計の提案",
                "labels": []
            },
            "実装": {
                "number": 401,
                "title": "認証システムを実装する",
                "body": "JWTベースの認証を実装",
                "labels": []
            },
            "バグ": {
                "number": 402,
                "title": "【バグ】ログイン不具合修正",
                "body": "特定条件でログインできない問題",
                "labels": []
            }
        }
        
        result_design = classifier.classify(japanese_issues["設計"])
        assert result_design.issue_type == IssueType.DESIGN
        
        result_impl = classifier.classify(japanese_issues["実装"])
        assert result_impl.issue_type == IssueType.IMPLEMENTATION
        
        result_bug = classifier.classify(japanese_issues["バグ"])
        assert result_bug.issue_type == IssueType.BUG_FIX
    
    def test_multi_type_detection(self, classifier):
        """複数タイプが混在するIssueのテスト"""
        mixed_issue = {
            "number": 500,
            "title": "APIリファクタリングとドキュメント更新",
            "body": """
このIssueでは以下を実施します：
1.0 REST APIのリファクタリング（実装）
2.0 APIドキュメントの更新（ドキュメント）
3.0 新しいテストケースの追加（テスト）
            """,
            "labels": ["api", "documentation", "test"]
        }
        
        result = classifier.classify(mixed_issue)
        # 主要なタイプが選択される
        assert result.issue_type in [IssueType.IMPLEMENTATION, IssueType.HYBRID]
        # 複数のタイプが検出される
        assert len(result.detected_types) > 1
    
    def test_custom_keywords_configuration(self, classifier):
        """カスタムキーワード設定のテスト"""
        # カスタムキーワードを追加
        custom_config = {
            "implementation_keywords": ["develop", "create", "build"],
            "design_keywords": ["architect", "plan", "structure"]
        }
        
        custom_classifier = IssueTypeClassifier(config=custom_config)
        
        issue = {
            "number": 600,
            "title": "Develop new feature",
            "body": "Create and build the new module",
            "labels": []
        }
        
        result = custom_classifier.classify(issue)
        assert result.issue_type == IssueType.IMPLEMENTATION
    
    def test_labels_as_objects(self, classifier):
        """ラベルがオブジェクト形式の場合のテスト"""
        issue_with_object_labels = {
            "number": 700,
            "title": "Bug Fix: Authentication error",
            "body": "Fix authentication bug in login flow",
            "labels": [
                {"name": "bug", "color": "d73a4a"},
                {"name": "urgent", "color": "e11d21"}
            ]
        }
        
        result = classifier.classify(issue_with_object_labels)
        assert result.issue_type == IssueType.BUG_FIX
        assert result.priority == "urgent"
        assert result.confidence >= 0.8
    
    def test_pattern_matching_specifics(self, classifier):
        """パターンマッチングの詳細テスト"""
        # Architecture marker test
        arch_marker_issue = {
            "number": 800,
            "title": "[DESIGN] New system layout",
            "body": "Simple redesign",
            "labels": []
        }
        result = classifier.classify(arch_marker_issue)
        assert result.issue_type == IssueType.DESIGN
        assert result.confidence >= 0.9
        
        # Bug marker test
        bug_marker_issue = {
            "number": 801,
            "title": "[FIX] Login issue",
            "body": "Minor fix needed",
            "labels": []
        }
        result = classifier.classify(bug_marker_issue)
        assert result.issue_type == IssueType.BUG_FIX
        assert result.confidence >= 0.9
        
        # Japanese markers
        jp_bug_issue = {
            "number": 802,
            "title": "【修正】認証エラー",
            "body": "ログイン時のエラーを修正",
            "labels": []
        }
        result = classifier.classify(jp_bug_issue)
        assert result.issue_type == IssueType.BUG_FIX
    
    def test_technical_terms_detection(self, classifier):
        """技術用語検出の詳細テスト"""
        tech_issues = [
            {
                "number": 900,
                "title": "Add JWT authentication",
                "body": "Implement token-based auth with JWT",
                "labels": []
            },
            {
                "number": 901,
                "title": "Database optimization",
                "body": "Optimize SQL queries and add indexes",
                "labels": []
            },
            {
                "number": 902,
                "title": "Cache implementation",
                "body": "Add Redis cache for performance",
                "labels": []
            }
        ]
        
        for issue in tech_issues:
            result = classifier.classify(issue)
            assert result.issue_type == IssueType.IMPLEMENTATION
            assert result.technical_requirements is not None
            assert len(result.technical_requirements) > 0
    
    def test_hybrid_type_conditions(self, classifier):
        """ハイブリッドタイプ判定の詳細条件テスト"""
        # Refactoring + Implementation (should be IMPLEMENTATION)
        refactor_impl_issue = {
            "number": 1000,
            "title": "Refactor and optimize API endpoints",
            "body": "Refactor existing API endpoints and implement new ones",
            "labels": ["refactoring", "implementation"]
        }
        result = classifier.classify(refactor_impl_issue)
        assert result.issue_type == IssueType.IMPLEMENTATION
        
        # Multiple high scores (should be HYBRID)
        truly_hybrid_issue = {
            "number": 1001,
            "title": "Fix bug and update documentation",
            "body": "Fix authentication bug and update API documentation",
            "labels": ["bug", "documentation"]
        }
        result = classifier.classify(truly_hybrid_issue)
        # This should be either BUG_FIX or HYBRID depending on scores
        assert result.issue_type in [IssueType.BUG_FIX, IssueType.HYBRID]
    
    def test_priority_edge_cases(self, classifier):
        """優先度判定のエッジケーステスト"""
        priority_issues = [
            {
                "number": 1100,
                "title": "Critical security vulnerability",
                "body": "Urgent fix needed",
                "labels": ["critical", "security"]
            },
            {
                "number": 1101,
                "title": "Important feature request",
                "body": "High priority feature",
                "labels": ["high", "feature"]
            },
            {
                "number": 1102,
                "title": "Minor UI improvement",
                "body": "Small enhancement",
                "labels": ["low", "enhancement"]
            },
            {
                "number": 1103,
                "title": "Error in production",
                "body": "Production error without priority label",
                "labels": ["production"]
            }
        ]
        
        results = []
        for issue in priority_issues:
            result = classifier.classify(issue)
            results.append((issue["number"], result.priority))
        
        assert results[0][1] == "critical"
        assert results[1][1] == "high"
        assert results[2][1] == "low"
        assert results[3][1] == "urgent"  # "error" in title
    
    def test_safety_checks_for_different_types(self, classifier):
        """異なるタイプの安全チェック推奨テスト"""
        # Bug fix safety checks
        bug_issue = {
            "number": 1200,
            "title": "[BUG] Critical system failure",
            "body": "System crashes on startup",
            "labels": ["bug"]
        }
        result = classifier.classify(bug_issue)
        assert "regression_test" in result.safety_checks
        assert "impact_analysis" in result.safety_checks
        
        # Refactoring safety checks
        refactor_issue = {
            "number": 1201,
            "title": "Refactor core module",
            "body": "Restructure core system module",
            "labels": ["refactoring"]
        }
        result = classifier.classify(refactor_issue)
        assert "behavior_preservation" in result.safety_checks
        assert "performance_impact" in result.safety_checks
        
        # Security-related implementation
        security_impl = {
            "number": 1202,
            "title": "Implement OAuth security layer",
            "body": "Add OAuth authentication and authorization",
            "labels": ["implementation", "security"]
        }
        result = classifier.classify(security_impl)
        assert "security_review" in result.safety_checks
    
    def test_batch_classification_with_errors(self, classifier):
        """エラーが発生する場合のバッチ分類テスト"""
        issues = [
            {
                "number": 1300,
                "title": "Normal issue",
                "body": "Normal content",
                "labels": ["implementation"]
            },
            None,  # This will cause an error
            {
                "number": 1302,
                "title": "Another normal issue",
                "body": "More content",
                "labels": ["bug"]
            }
        ]
        
        results = classifier.classify_batch(issues)
        assert len(results) == 3
        assert results[0].issue_type == IssueType.IMPLEMENTATION
        assert results[1].issue_type == IssueType.UNKNOWN  # Error case
        assert results[1].confidence == 0.0
        assert results[2].issue_type == IssueType.BUG_FIX
    
    def test_extract_keywords_edge_cases(self, classifier):
        """キーワード抽出のエッジケーステスト"""
        # Issue with duplicate keywords
        duplicate_keyword_issue = {
            "number": 1400,
            "title": "Test test testing test",
            "body": "Test the test module with test cases",
            "labels": ["test", "testing", "test"]
        }
        result = classifier.classify(duplicate_keyword_issue)
        # Keywords should be unique
        keyword_counts = {}
        for keyword in result.keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # No duplicate keywords
        assert all(count == 1 for count in keyword_counts.values())
    
    def test_unknown_type_classification(self, classifier):
        """UNKNOWN タイプの分類テスト"""
        # Very vague issue
        vague_issue = {
            "number": 1500,
            "title": "Something",
            "body": "Need to do something",
            "labels": []
        }
        result = classifier.classify(vague_issue)
        assert result.issue_type == IssueType.UNKNOWN
        assert result.recommended_flow == "manual_review"
        assert result.confidence < 0.5
    
    def test_technical_requirements_comprehensive(self, classifier):
        """技術要件抽出の包括的テスト"""
        comprehensive_tech_issue = {
            "number": 1600,
            "title": "Implement comprehensive system",
            "body": """
            We need to implement:
            - JWT token authentication with refresh tokens
            - Parallel processing for better performance
            - Memory optimization and caching with LRU
            - Database optimization with SQL improvements
            - API endpoints with REST architecture
            - Security with encryption for sensitive data
            - Authorization flow for user permissions
            """,
            "labels": ["implementation"]
        }
        
        result = classifier.classify(comprehensive_tech_issue)
        assert result.issue_type == IssueType.IMPLEMENTATION
        assert result.technical_requirements is not None
        
        expected_requirements = [
            "jwt", "refresh_token", "parallel_processing",
            "memory_optimization", "caching", "database",
            "api_endpoints", "security", "authorization_flow"
        ]
        
        for req in expected_requirements:
            assert req in result.technical_requirements
    
    def test_score_calculation_edge_cases(self, classifier):
        """スコア計算のエッジケーステスト"""
        # Empty scores scenario
        empty_everything = {
            "number": 1700,
            "title": "",
            "body": None,
            "labels": None
        }
        result = classifier.classify(empty_everything)
        assert result.issue_type == IssueType.UNKNOWN
        assert result.confidence == 0.0
        
        # Very high confidence scenario
        super_clear_issue = {
            "number": 1701,
            "title": "[BUG] [FIX] Critical bug fix needed",
            "body": "Bug bug bug error error fail crash",
            "labels": ["bug", "critical", "urgent"]
        }
        result = classifier.classify(super_clear_issue)
        assert result.issue_type == IssueType.BUG_FIX
        assert result.confidence >= 0.95