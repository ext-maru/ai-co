#!/usr/bin/env python3
"""
Issue Type Classifier V2 Tests
Phase 2強化版のテストスイート
"""

import pytest
from libs.elder_system.issue_classifier_v2 import (
    IssueTypeClassifierV2, IssueCategory, IssueType, EnhancedClassificationResult
)

class TestIssueTypeClassifierV2:
    """Phase 2強化版Issue分類器のテスト"""
    
    @pytest.fixture
    def classifier(self):
        """テスト用分類器インスタンス"""
        return IssueTypeClassifierV2()
    
    def test_design_oriented_issue_classification(self, classifier):
        """設計系Issueの分類テスト"""
        issue = {
            "title": "[ARCHITECTURE] システム再設計提案",
            "body": "マイクロサービスアーキテクチャへの移行設計",
            "labels": ["design", "architecture"]
        }
        
        result = classifier.classify(issue)
        
        assert result.category == IssueCategory.DESIGN_ORIENTED
        assert result.issue_type == IssueType.ARCHITECTURE_DESIGN
        assert result.elder_flow_recommended is True
        assert result.confidence > 0.8
        assert "アーキテクチャ設計書の生成に適している" in result.elder_flow_reason
    
    def test_implementation_oriented_issue_classification(self, classifier):
        """実装系Issueの分類テスト（Issue #83）"""
        issue = {
            "title": "⚡ Continue.dev Phase 2 - パフォーマンス最適化",
            "body": """## 概要
Continue.dev統合のパフォーマンス最適化を実装します。

## 実装内容
### 🔧 最適化機能
- [ ] レスポンス時間最適化
- [ ] キャッシング機能実装
- [ ] 並列処理最適化
- [ ] メモリ使用量最適化""",
            "labels": ["enhancement", "priority:low"]
        }
        
        result = classifier.classify(issue)
        
        assert result.category == IssueCategory.IMPLEMENTATION_ORIENTED
        assert result.issue_type == IssueType.PERFORMANCE_OPTIMIZATION
        assert result.elder_flow_recommended is False
        assert result.confidence > 0.7
        assert "技術固有の知識が必要" in result.elder_flow_reason
        assert "continue_dev" in result.detected_technologies
    
    def test_maintenance_oriented_issue_classification(self, classifier):
        """保守系Issueの分類テスト"""
        issue = {
            "title": "バグ修正: ログイン機能のエラー",
            "body": "ユーザーがログインできない不具合を修正",

        }
        
        result = classifier.classify(issue)
        
        assert result.category == IssueCategory.MAINTENANCE_ORIENTED

        assert result.elder_flow_recommended is False
        assert "具体的なコード理解が必要" in result.elder_flow_reason
    
    def test_documentation_issue_classification(self, classifier):
        """ドキュメント系Issueの分類テスト"""
        issue = {
            "title": "READMEの更新",
            "body": "インストール手順とAPIリファレンスの追加",
            "labels": ["documentation"]
        }
        
        result = classifier.classify(issue)
        
        assert result.issue_type == IssueType.DOCUMENTATION
        assert result.elder_flow_recommended is True
        assert "ドキュメント生成はElder Flowの得意分野" in result.elder_flow_reason
    
    def test_technology_detection(self, classifier):
        """技術スタック検出テスト"""
        issue = {
            "title": "OAuth2.0認証の実装",
            "body": "JWT tokenを使用したOAuth2.0フローの実装。Dockerコンテナで動作確認。",
            "labels": []
        }
        
        result = classifier.classify(issue)
        
        assert "auth" in result.detected_technologies
        assert "docker" in result.detected_technologies
        assert result.issue_type == IssueType.INTEGRATION
    
    def test_complexity_calculation(self, classifier):
        """複雑度計算テスト"""
        simple_issue = {
            "title": "タイポ修正",
            "body": "READMEのタイポを修正します",
            "labels": []
        }
        
        complex_issue = {
            "title": "複雑なシステム統合",
            "body": """複数のマイクロサービスを統合し、認証システムと連携。
パフォーマンスの最適化も必要。難しい課題が多数存在。
OAuth, JWT, Redis, Kubernetes, AWS Lambda等を使用。""" * 10,  # 長いテキスト
            "labels": ["complex", "integration"]
        }
        
        simple_result = classifier.classify(simple_issue)
        complex_result = classifier.classify(complex_issue)
        
        assert simple_result.complexity_score < 20
        assert complex_result.complexity_score > 50
    
    def test_risk_level_calculation(self, classifier):
        """リスクレベル計算テスト"""
        critical_issue = {
            "title": "セキュリティ脆弱性の修正",
            "body": "認証バイパスの脆弱性を緊急修正",

        }
        
        low_risk_issue = {
            "title": "UIの微調整",
            "body": "ボタンの色を変更",
            "labels": ["enhancement", "low"]
        }
        
        critical_result = classifier.classify(critical_issue)
        low_risk_result = classifier.classify(low_risk_issue)
        
        assert critical_result.risk_level == "critical"
        assert low_risk_result.risk_level == "low"
    
    def test_technical_requirements_extraction(self, classifier):
        """技術要件抽出テスト"""
        issue = {
            "title": "キャッシング機能の実装",
            "body": """並列処理とメモリ最適化を含むキャッシング実装。
非同期処理も必要。OAuth認証とJWTトークンの実装も含む。""",
            "labels": []
        }
        
        result = classifier.classify(issue)
        
        assert "caching_implementation" in result.technical_requirements
        assert "parallel_processing" in result.technical_requirements
        assert "memory_optimization" in result.technical_requirements
        assert "asynchronous_processing" in result.technical_requirements
        assert "oauth_implementation" in result.technical_requirements
        assert "jwt_tokens" in result.technical_requirements
    
    def test_safety_checks_determination(self, classifier):
        """安全チェック決定テスト"""
        performance_issue = {
            "title": "パフォーマンス最適化",
            "body": "システム全体のパフォーマンス改善",
            "labels": ["performance", "critical"]
        }
        
        result = classifier.classify(performance_issue)
        
        assert "code_review" in result.safety_checks
        assert "performance_benchmarking" in result.safety_checks
        assert "load_testing" in result.safety_checks
        assert "security_review" in result.safety_checks  # criticalラベルのため
    
    def test_recommended_flow_determination(self, classifier):
        """推奨フロー決定テスト"""
        # 高信頼度の設計系
        design_issue = {
            "title": "[ARCHITECTURE] 詳細設計書作成",
            "body": "システムアーキテクチャの詳細設計",
            "labels": ["architecture"]
        }
        
        # 低信頼度の曖昧なIssue
        vague_issue = {
            "title": "変更",
            "body": "",
            "labels": []
        }
        
        design_result = classifier.classify(design_issue)
        vague_result = classifier.classify(vague_issue)
        
        # 信頼度が80%未満の場合はレビュー付きになる
        assert design_result.recommended_flow in ["elder_flow_auto", "elder_flow_with_review"]
        assert design_result.elder_flow_recommended is True
        assert vague_result.recommended_flow == "manual_review_required"
    
    def test_edge_cases(self, classifier):
        """エッジケーステスト"""
        # 空のIssue
        empty_issue = {
            "title": "",
            "body": None,
            "labels": []
        }
        
        # 非常に長いタイトル
        long_title_issue = {
            "title": "A" * 500,
            "body": "Test",
            "labels": []
        }
        
        # 多数のラベル
        many_labels_issue = {
            "title": "Test",
            "body": "Test",

        }
        
        # エラーが発生しないことを確認
        empty_result = classifier.classify(empty_issue)
        long_result = classifier.classify(long_title_issue)
        labels_result = classifier.classify(many_labels_issue)
        
        assert empty_result.issue_type == IssueType.UNKNOWN
        assert empty_result.confidence < 0.5
        assert long_result is not None
        assert labels_result is not None
    
    def test_hybrid_issue_detection(self, classifier):
        """ハイブリッドIssue検出テスト"""
        hybrid_issue = {
            "title": "新機能実装とバグ修正",
            "body": """新しい認証機能を実装しつつ、既存のバグも修正。
さらにドキュメントの更新とテストの追加も必要。""",

        }
        
        result = classifier.classify(hybrid_issue)
        
        # 複数の要素が含まれる場合の判定
        assert result.confidence < 0.9  # 確信度は高くないはず
    
    def test_priority_determination(self, classifier):
        """優先度判定テスト"""
        critical_issue = {
            "title": "緊急: システムダウン",
            "body": "本番環境でシステムがダウン",
            "labels": ["critical", "blocker"]
        }
        
        low_issue = {
            "title": "UIの微調整",
            "body": "ボタンの余白調整",
            "labels": ["low", "enhancement"]
        }
        
        critical_result = classifier.classify(critical_issue)
        low_result = classifier.classify(low_issue)
        
        assert critical_result.priority == "critical"
        assert low_result.priority == "low"
    
    def test_summary_report_generation(self, classifier):
        """サマリーレポート生成テスト"""
        issue = {
            "title": "テストIssue",
            "body": "テスト内容",
            "labels": ["test"]
        }
        
        result = classifier.classify(issue)
        report = classifier.generate_summary_report(result)
        
        assert "基本分類" in report
        assert "Elder Flow判定" in report
        assert "詳細情報" in report
        assert "技術情報" in report
        assert result.issue_type.value in report

if __name__ == "__main__":
    pytest.main([__file__, "-v"])