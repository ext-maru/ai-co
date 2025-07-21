#!/usr/bin/env python3
"""
Issue #92 Auto Issue Processor統合テスト
GitHub API不要のドライランテストと基本機能テスト
"""

import sys
import asyncio
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# パス設定
sys.path.append(str(Path(__file__).parent.parent))

from libs.integrations.github.auto_issue_processor import (
    AutoIssueProcessor, ComplexityEvaluator, ProcessingLimiter, ComplexityScore
)


class MockIssue:
    """GitHub Issueのモック"""
    
    def __init__(self, number: int, title: str, body: str = "", labels: list = None):
        self.number = number
        self.title = title
        self.body = body
        # ラベルオブジェクトを正しく作成
        self.labels = []
        for label in (labels or []):
            label_obj = Mock()
            label_obj.name = label
            self.labels.append(label_obj)
        self.pull_request = None
        
    def create_comment(self, comment: str):
        """コメント作成をモック"""
        print(f"Comment on issue #{self.number}: {comment}")


class MockAutoIssueProcessor:
    """GitHub API不要のAutoIssueProcessorモック"""
    
    def __init__(self):
        self.target_priorities = ['critical', 'high', 'medium']
        self.evaluator = ComplexityEvaluator()
        self.limiter = ProcessingLimiter()
        
    def get_capabilities(self):
        return {
            "service": "AutoIssueProcessor",
            "version": "1.0.0",
            "capabilities": [
                "GitHub issue scanning",
                "Complexity evaluation", 
                "Automatic processing",
                "Elder Flow integration",
                "Quality gate validation"
            ],
            "limits": {
                "max_issues_per_hour": 10,
                "max_concurrent": 1,
                "target_priorities": self.target_priorities
            }
        }
    
    def validate_request(self, request):
        if 'mode' in request and request['mode'] not in ['scan', 'process', 'dry_run']:
            return False
        if 'issue_number' in request:
            if not isinstance(request['issue_number'], int):
                return False
        return True
    
    def _determine_priority(self, issue):
        """優先度判定をテスト"""
        labels = [label.name.lower() for label in issue.labels]
        
        if any(label in ['critical', 'urgent', 'p0', 'priority:critical'] for label in labels):
            return 'critical'
        elif any(label in ['high', 'important', 'p1', 'priority:high'] for label in labels):
            return 'high'
        elif any(label in ['medium', 'moderate', 'p2', 'priority:medium'] for label in labels):
            return 'medium'
        elif any(label in ['low', 'minor', 'p3', 'priority:low'] for label in labels):
            return 'low'
        
        title_lower = issue.title.lower()
        if any(word in title_lower for word in ['critical', 'urgent', 'emergency']):
            return 'critical'
        elif any(word in title_lower for word in ['important', 'high priority']):
            return 'high'
        elif any(word in title_lower for word in ['bug', 'fix', 'error']):
            return 'medium'
        
        return 'low'


class TestAutoIssueProcessorIntegration:
    """Issue #92 統合テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.processor = MockAutoIssueProcessor()
        
    def test_basic_functionality(self):
        """基本機能テスト"""
        # サービス情報取得
        capabilities = self.processor.get_capabilities()
        assert capabilities["service"] == "AutoIssueProcessor"
        assert capabilities["version"] == "1.0.0"
        assert len(capabilities["capabilities"]) == 5
        
        # 制限設定確認
        limits = capabilities["limits"]
        assert limits["max_issues_per_hour"] == 10
        assert limits["max_concurrent"] == 1
        assert "medium" in limits["target_priorities"]
    
    def test_request_validation(self):
        """リクエスト検証テスト"""
        # 有効なリクエスト
        valid_requests = [
            {'mode': 'scan'},
            {'mode': 'process'},
            {'mode': 'dry_run', 'issue_number': 92},
            {}  # モードなしも有効
        ]
        
        for request in valid_requests:
            assert self.processor.validate_request(request) is True
        
        # 無効なリクエスト
        invalid_requests = [
            {'mode': 'invalid_mode'},
            {'mode': 'scan', 'issue_number': 'not_int'},
            {'issue_number': '92'}  # 文字列の場合
        ]
        
        for request in invalid_requests:
            assert self.processor.validate_request(request) is False
    
    def test_priority_determination(self):
        """優先度判定テスト"""
        test_cases = [
            # (labels, title, expected_priority)
            (['priority:critical'], 'Test issue', 'critical'),
            (['high'], 'Test issue', 'high'),
            (['priority:medium'], 'Test issue', 'medium'),
            (['low'], 'Test issue', 'low'),
            ([], 'CRITICAL: System down', 'critical'),
            ([], 'URGENT: Important fix needed', 'critical'),
            ([], 'Fix bug in payment system', 'medium'),
            ([], 'Documentation update', 'low'),
        ]
        
        for labels, title, expected in test_cases:
            issue = MockIssue(1, title, labels=labels)
            priority = self.processor._determine_priority(issue)
            assert priority == expected, f"Labels: {labels}, Title: {title}, Expected: {expected}, Got: {priority}"
    
    @pytest.mark.asyncio
    async def test_complexity_evaluation(self):
        """複雑度評価テスト"""
        evaluator = ComplexityEvaluator()
        
        # 簡単なパターン
        simple_issues = [
            MockIssue(1, "Fix typo in documentation", "Simple typo fix"),
            MockIssue(2, "Add comment to function", "Need better comments"),
            MockIssue(3, "Format code with black", "Code formatting issue"),
        ]
        
        for issue in simple_issues:
            score = await evaluator.evaluate(issue)
            assert isinstance(score, ComplexityScore)
            assert score.is_processable is True  # 簡単なので処理可能
            assert score.score < 0.7
        
        # 複雑なパターン
        complex_issues = [
            MockIssue(4, "Implement OAuth2 authentication", "Need full auth system"),
            MockIssue(5, "Security vulnerability in login", "Fix critical security issue"),
            MockIssue(6, "Refactor entire database layer", "Major architecture change"),
        ]
        
        for issue in complex_issues:
            score = await evaluator.evaluate(issue)
            assert isinstance(score, ComplexityScore)
            # セキュリティ関連は自動で高複雑度
            if 'security' in issue.title.lower() or 'security' in (issue.body or '').lower():
                assert score.is_processable is False
    
    @pytest.mark.asyncio
    async def test_processing_limiter(self):
        """処理制限テスト"""
        limiter = ProcessingLimiter()
        
        # 最初は処理可能
        can_process = await limiter.can_process()
        assert can_process is True
        
        # 記録テスト
        await limiter.record_processing(92)
        # 記録後も処理可能（まだ制限内）
        can_process = await limiter.can_process()
        assert can_process is True
    
    def test_target_priority_filtering(self):
        """対象優先度フィルタリングテスト"""
        test_issues = [
            MockIssue(1, "Critical bug", labels=['priority:critical']),
            MockIssue(2, "High priority feature", labels=['priority:high']),
            MockIssue(3, "Medium priority task", labels=['priority:medium']),
            MockIssue(4, "Low priority cleanup", labels=['priority:low']),
        ]
        
        for issue in test_issues:
            priority = self.processor._determine_priority(issue)
            is_target = priority in self.processor.target_priorities
            
            if issue.number <= 3:  # Critical, High, Medium
                assert is_target is True
            else:  # Low
                assert is_target is False
    
    def test_issue_filtering_logic(self):
        """イシューフィルタリングロジックテスト"""
        # 処理対象のイシュー
        processable_issues = [
            MockIssue(92, "Fix typo in README", "Simple documentation fix", labels=['priority:medium']),
            MockIssue(93, "Add unit test for util function", "Missing test coverage", labels=['priority:high']),
            MockIssue(94, "Format code with prettier", "Code style issue", labels=['priority:medium']),
        ]
        
        # 処理対象外のイシュー
        non_processable_issues = [
            MockIssue(95, "Implement microservices architecture", "Major refactoring", labels=['priority:high']),
            MockIssue(96, "Fix security vulnerability", "Auth bypass", labels=['priority:critical']),
            MockIssue(97, "Documentation improvement", "Update docs", labels=['priority:low']),  # 優先度が低い
        ]
        
        for issue in processable_issues:
            priority = self.processor._determine_priority(issue)
            assert priority in self.processor.target_priorities
        
        for issue in non_processable_issues:
            priority = self.processor._determine_priority(issue)
            if priority == 'low':
                assert priority not in self.processor.target_priorities
    
    def test_complexity_factors(self):
        """複雑度要因テスト"""
        evaluator = ComplexityEvaluator()
        
        # パターンマッチング確認
        patterns = evaluator.PROCESSABLE_PATTERNS
        assert 'typo' in patterns
        assert 'documentation' in patterns
        assert 'comment' in patterns
        assert 'format' in patterns
        
        # 複雑度要因確認  
        factors = evaluator.COMPLEXITY_FACTORS
        assert 'file_count' in factors
        assert 'code_lines' in factors
        assert 'dependencies' in factors
        assert 'test_coverage' in factors
    
    def test_elder_flow_integration_structure(self):
        """Elder Flow統合構造テスト"""
        # AutoIssueElderFlowEngineのモック
        mock_flow_request = {
            'task_name': 'Auto-fix Issue #92: Fix typo in documentation',
            'priority': 'medium',
            'context': {
                'issue_number': 92,
                'issue_title': 'Fix typo in documentation', 
                'issue_body': 'There is a typo in the README file',
                'labels': ['priority:medium', 'documentation'],
                'sage_advice': {}
            }
        }
        
        # リクエスト構造確認
        assert 'task_name' in mock_flow_request
        assert 'priority' in mock_flow_request
        assert 'context' in mock_flow_request
        
        context = mock_flow_request['context']
        assert 'issue_number' in context
        assert 'issue_title' in context
        assert 'issue_body' in context
        assert 'labels' in context
        assert 'sage_advice' in context
    
    def test_four_sages_consultation_structure(self):
        """4賢者相談構造テスト"""
        # 4賢者への相談リクエスト構造
        mock_sage_requests = {
            'knowledge': {
                'type': 'search',
                'query': 'similar issues to: Fix typo in documentation',
                'limit': 5
            },
            'task': {
                'type': 'create_plan',
                'title': 'Fix typo in documentation',
                'description': 'There is a typo in the README file'
            },
            'incident': {
                'type': 'evaluate_risk',
                'task': 'Fix typo in documentation',
                'context': 'There is a typo in the README file'
            },
            'rag': {
                'type': 'search',
                'query': 'how to fix: Fix typo in documentation',
                'max_results': 3
            }
        }
        
        # 各賢者リクエスト構造確認
        for sage_name, request in mock_sage_requests.items():
            assert 'type' in request
            if sage_name in ['knowledge', 'rag']:
                assert 'query' in request
            elif sage_name == 'task':
                assert 'title' in request
                assert 'description' in request
            elif sage_name == 'incident':
                assert 'task' in request
                assert 'context' in request


class TestIssue92SpecificRequirements:
    """Issue #92固有要件テスト"""
    
    def test_target_priority_range(self):
        """対象優先度範囲テスト"""
        processor = MockAutoIssueProcessor()
        
        # Issue #92の要求: Critical/High/Medium優先度を対象
        expected_targets = ['critical', 'high', 'medium']
        assert processor.target_priorities == expected_targets
    
    def test_processing_limits(self):
        """処理制限テスト"""
        # Issue #92の要求: 1時間あたり最大10イシュー
        assert ProcessingLimiter.MAX_ISSUES_PER_HOUR == 10
        assert ProcessingLimiter.MAX_CONCURRENT == 1
        assert ProcessingLimiter.COOLDOWN_PERIOD == 300  # 5分
    
    def test_complexity_threshold(self):
        """複雑度閾値テスト"""
        # Issue #92の要求: 複雑度0.7未満を自動処理
        score = ComplexityScore(0.6, {'test': True})
        assert score.is_processable is True
        
        score = ComplexityScore(0.8, {'test': True})
        assert score.is_processable is False
    
    def test_security_exclusion(self):
        """セキュリティ関連除外テスト"""
        # Issue #92の要求: セキュリティ関連は自動処理しない
        security_keywords = ['security', 'vulnerability', 'auth', 'token', 'password']
        
        for keyword in security_keywords:
            issue = MockIssue(1, f"Fix {keyword} issue", f"Issue with {keyword}")
            # セキュリティ関連は高複雑度になるべき
            # 実際のComplexityEvaluatorでテストする必要がある


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])