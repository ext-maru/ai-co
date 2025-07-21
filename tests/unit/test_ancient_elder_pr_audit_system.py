#!/usr/bin/env python3
"""
🧪 Ancient Elder PR Audit System Tests
エンシェントエルダー厳格PR監査システムのテスト
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
from pathlib import Path
import sys

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.ancient_elder_pr_audit_system import AncientElderPRAuditSystem


class TestAncientElderPRAuditSystem:
    """Ancient Elder PR Audit System テストクラス"""

    @pytest.fixture
    def audit_system(self):
        """テスト用監査システム"""
        return AncientElderPRAuditSystem()

    @pytest.fixture
    def mock_pr(self):
        """モックPR"""
        pr = Mock()
        pr.number = 123
        pr.title = "Test PR"
        pr.get_files.return_value = []
        return pr

    @pytest.fixture
    def mock_file(self):
        """モックファイル"""
        file = Mock()
        file.filename = "test.py"
        file.patch = """
+def test_function():
+    # This is a test function
+    return True
"""
        return file

    def test_initialization(self, audit_system):
        """初期化テスト"""
        assert audit_system.ancient_elder_min_score == 90
        assert audit_system.iron_will_tolerance == 0
        assert audit_system.coverage_min_threshold == 90
        assert audit_system.security_risk_tolerance == 0

    @pytest.mark.asyncio
    async def test_github_initialization(self, audit_system):
        """GitHub API初期化テスト"""
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
            with patch('github.Github') as mock_github:
                mock_repo = Mock()
                mock_github.return_value.get_repo.return_value = mock_repo
                
                await audit_system.initialize()
                
                assert audit_system.github is not None
                assert audit_system.repo == mock_repo

    @pytest.mark.asyncio
    async def test_github_initialization_no_token(self, audit_system):
        """GitHub API初期化失敗テスト（トークンなし）"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GITHUB_TOKEN環境変数が必要です"):
                await audit_system.initialize()

    @pytest.mark.asyncio
    async def test_calculate_ancient_elder_score_empty_files(self, audit_system, mock_pr):
        """Ancient Elder Score算出テスト（空ファイル）"""
        mock_pr.get_files.return_value = []
        
        score = await audit_system.calculate_ancient_elder_score(mock_pr)
        
        assert score == 0

    @pytest.mark.asyncio
    async def test_calculate_ancient_elder_score_with_files(self, audit_system, mock_pr, mock_file):
        """Ancient Elder Score算出テスト（ファイルあり）"""
        mock_pr.get_files.return_value = [mock_file]
        
        score = await audit_system.calculate_ancient_elder_score(mock_pr)
        
        assert isinstance(score, int)
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_analyze_file_quality_basic(self, audit_system, mock_file):
        """ファイル品質分析テスト（基本）"""
        score = await audit_system.analyze_file_quality(mock_file)
        
        assert isinstance(score, int)
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_analyze_file_quality_with_documentation(self, audit_system, mock_file):
        """ファイル品質分析テスト（ドキュメント付き）"""
        mock_file.patch = '''
+def test_function():
+    """This is a documented function"""
+    return True
'''
        
        score = await audit_system.analyze_file_quality(mock_file)
        
        assert score > 100  # ドキュメント加点

    @pytest.mark.asyncio
    async def test_analyze_file_quality_dangerous_patterns(self, audit_system, mock_file):
        """ファイル品質分析テスト（危険パターン）"""
        mock_file.patch = '''
+def dangerous_function():
+    eval("print('dangerous')")
+    return True
'''
        
        score = await audit_system.analyze_file_quality(mock_file)
        
        assert score < 100  # 危険パターンで減点

    @pytest.mark.asyncio
    async def test_check_iron_will_violations_clean(self, audit_system, mock_pr, mock_file):
        """Iron Will違反チェックテスト（クリーン）"""
        mock_file.patch = '''
+def clean_function():
+    return True
'''
        mock_pr.get_files.return_value = [mock_file]
        
        violations = await audit_system.check_iron_will_violations(mock_pr)
        
        assert violations == 0

    @pytest.mark.asyncio
    async def test_check_iron_will_violations_with_todo(self, audit_system, mock_pr, mock_file):
        """Iron Will違反チェックテスト（TODO付き）"""
        mock_file.patch = '''
+def function_with_todo():
+    # TODO: implement this
+    # FIXME: fix this bug
+    return True
'''
        mock_pr.get_files.return_value = [mock_file]
        
        violations = await audit_system.check_iron_will_violations(mock_pr)
        
        assert violations == 2  # TODO + FIXME

    @pytest.mark.asyncio
    async def test_analyze_test_coverage_no_files(self, audit_system, mock_pr):
        """テストカバレッジ分析テスト（ファイルなし）"""
        mock_pr.get_files.return_value = []
        
        coverage = await audit_system.analyze_test_coverage(mock_pr)
        
        assert coverage == 100  # 実装ファイルがない場合

    @pytest.mark.asyncio
    async def test_analyze_test_coverage_with_tests(self, audit_system, mock_pr):
        """テストカバレッジ分析テスト（テストファイルあり）"""
        impl_file = Mock()
        impl_file.filename = "implementation.py"
        
        test_file = Mock()
        test_file.filename = "test_implementation.py"
        
        mock_pr.get_files.return_value = [impl_file, test_file]
        
        coverage = await audit_system.analyze_test_coverage(mock_pr)
        
        assert coverage == 100  # 1:1の比率

    @pytest.mark.asyncio
    async def test_analyze_test_coverage_insufficient_tests(self, audit_system, mock_pr):
        """テストカバレッジ分析テスト（テスト不足）"""
        impl_file1 = Mock()
        impl_file1.filename = "implementation1.py"
        
        impl_file2 = Mock()
        impl_file2.filename = "implementation2.py"
        
        test_file = Mock()
        test_file.filename = "test_implementation1.py"
        
        mock_pr.get_files.return_value = [impl_file1, impl_file2, test_file]
        
        coverage = await audit_system.analyze_test_coverage(mock_pr)
        
        assert coverage == 50  # 2実装:1テスト = 50%

    @pytest.mark.asyncio
    async def test_evaluate_security_risks_clean(self, audit_system, mock_pr, mock_file):
        """セキュリティリスク評価テスト（クリーン）"""
        mock_file.patch = '''
+def safe_function():
+    return "Hello World"
'''
        mock_pr.get_files.return_value = [mock_file]
        
        risks = await audit_system.evaluate_security_risks(mock_pr)
        
        assert risks == 0

    @pytest.mark.asyncio
    async def test_evaluate_security_risks_with_risks(self, audit_system, mock_pr, mock_file):
        """セキュリティリスク評価テスト（リスクあり）"""
        mock_file.patch = '''
+def risky_function():
+    password = "secret123"
+    eval("print('dangerous')")
+    return password
'''
        mock_pr.get_files.return_value = [mock_file]
        
        risks = await audit_system.evaluate_security_risks(mock_pr)
        
        assert risks >= 2  # password + eval

    def test_make_final_decision_approved(self, audit_system):
        """最終判定テスト（承認）"""
        audit_result = {
            "ancient_elder_score": 95,
            "iron_will_violations": 0,
            "test_coverage": 95,
            "security_risks": 0
        }
        
        decision = audit_system.make_final_decision(audit_result)
        
        assert decision == "APPROVED"

    def test_make_final_decision_rejected_low_score(self, audit_system):
        """最終判定テスト（却下：低スコア）"""
        audit_result = {
            "ancient_elder_score": 40,
            "iron_will_violations": 0,
            "test_coverage": 95,
            "security_risks": 0
        }
        
        decision = audit_system.make_final_decision(audit_result)
        
        assert decision == "REJECTED"

    def test_make_final_decision_rejected_iron_will(self, audit_system):
        """最終判定テスト（却下：Iron Will違反）"""
        audit_result = {
            "ancient_elder_score": 95,
            "iron_will_violations": 15,
            "test_coverage": 95,
            "security_risks": 0
        }
        
        decision = audit_system.make_final_decision(audit_result)
        
        assert decision == "REJECTED"

    def test_make_final_decision_rejected_security(self, audit_system):
        """最終判定テスト（却下：セキュリティリスク）"""
        audit_result = {
            "ancient_elder_score": 95,
            "iron_will_violations": 0,
            "test_coverage": 95,
            "security_risks": 10
        }
        
        decision = audit_system.make_final_decision(audit_result)
        
        assert decision == "REJECTED"

    def test_make_final_decision_conditional(self, audit_system):
        """最終判定テスト（条件付き）"""
        audit_result = {
            "ancient_elder_score": 85,  # 基準未満だが致命的ではない
            "iron_will_violations": 2,
            "test_coverage": 80,
            "security_risks": 1
        }
        
        decision = audit_system.make_final_decision(audit_result)
        
        assert decision == "CONDITIONAL"

    def test_generate_approval_comment(self, audit_system):
        """承認コメント生成テスト"""
        audit_result = {
            "ancient_elder_score": 95,
            "iron_will_violations": 0,
            "test_coverage": 95,
            "security_risks": 0,
            "timestamp": "2025-01-01T00:00:00"
        }
        
        comment = audit_system.generate_approval_comment(audit_result)
        
        assert "APPROVED ✅" in comment
        assert "95/100" in comment
        assert "即座にマージ可能" in comment

    def test_generate_rejection_comment(self, audit_system):
        """差し戻しコメント生成テスト"""
        audit_result = {
            "ancient_elder_score": 40,
            "iron_will_violations": 5,
            "test_coverage": 30,
            "security_risks": 3,
            "timestamp": "2025-01-01T00:00:00"
        }
        
        comment = audit_system.generate_rejection_comment(audit_result)
        
        assert "REJECTED ❌" in comment
        assert "品質スコア不足" in comment
        assert "Iron Will違反" in comment
        assert "テストカバレッジ不足" in comment
        assert "セキュリティリスク" in comment

    def test_generate_conditional_comment(self, audit_system):
        """条件付きコメント生成テスト"""
        audit_result = {
            "ancient_elder_score": 85,
            "iron_will_violations": 2,
            "test_coverage": 80,
            "security_risks": 1,
            "timestamp": "2025-01-01T00:00:00"
        }
        
        comment = audit_system.generate_conditional_comment(audit_result)
        
        assert "CONDITIONAL ⚠️" in comment
        assert "改善推奨事項" in comment
        assert "条件付き承認" in comment

    @pytest.mark.asyncio
    async def test_comprehensive_pr_audit_complete_flow(self, audit_system, mock_pr, mock_file):
        """包括的PR監査テスト（完全フロー）"""
        mock_file.patch = '''
+def test_function():
+    """Well documented function"""
+    return True
'''
        mock_pr.get_files.return_value = [mock_file]
        
        with patch.object(audit_system, 'calculate_ancient_elder_score', return_value=95):
            with patch.object(audit_system, 'check_iron_will_violations', return_value=0):
                with patch.object(audit_system, 'analyze_test_coverage', return_value=95):
                    with patch.object(audit_system, 'evaluate_security_risks', return_value=0):
                        
                        result = await audit_system.comprehensive_pr_audit(mock_pr)
                        
                        assert result["pr_number"] == 123
                        assert result["pr_title"] == "Test PR"
                        assert result["ancient_elder_score"] == 95
                        assert result["iron_will_violations"] == 0
                        assert result["test_coverage"] == 95
                        assert result["security_risks"] == 0
                        assert result["final_decision"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_approve_pr(self, audit_system, mock_pr):
        """PR承認処理テスト"""
        audit_result = {
            "ancient_elder_score": 95,
            "iron_will_violations": 0,
            "test_coverage": 95,
            "security_risks": 0,
            "timestamp": "2025-01-01T00:00:00"
        }
        
        mock_pr.create_issue_comment = Mock()
        
        await audit_system.approve_pr(mock_pr, audit_result)
        
        mock_pr.create_issue_comment.assert_called_once()
        comment_text = mock_pr.create_issue_comment.call_args[0][0]
        assert "APPROVED ✅" in comment_text

    @pytest.mark.asyncio
    async def test_reject_pr(self, audit_system, mock_pr):
        """PR差し戻し処理テスト"""
        audit_result = {
            "ancient_elder_score": 40,
            "iron_will_violations": 5,
            "test_coverage": 30,
            "security_risks": 3,
            "timestamp": "2025-01-01T00:00:00"
        }
        
        mock_pr.create_issue_comment = Mock()
        
        await audit_system.reject_pr(mock_pr, audit_result)
        
        mock_pr.create_issue_comment.assert_called_once()
        comment_text = mock_pr.create_issue_comment.call_args[0][0]
        assert "REJECTED ❌" in comment_text

    @pytest.mark.asyncio
    async def test_conditional_pr(self, audit_system, mock_pr):
        """条件付きPR処理テスト"""
        audit_result = {
            "ancient_elder_score": 85,
            "iron_will_violations": 2,
            "test_coverage": 80,
            "security_risks": 1,
            "timestamp": "2025-01-01T00:00:00"
        }
        
        mock_pr.create_issue_comment = Mock()
        
        await audit_system.conditional_pr(mock_pr, audit_result)
        
        mock_pr.create_issue_comment.assert_called_once()
        comment_text = mock_pr.create_issue_comment.call_args[0][0]
        assert "CONDITIONAL ⚠️" in comment_text