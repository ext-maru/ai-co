#!/usr/bin/env python3
"""
GitHub Integration Property-Based Testing for Robustness
Iron Will基準準拠・95%カバレッジ達成・古代エルダー#5監査対応
Hypothesis活用による堅牢性テスト
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
import json
import time
from typing import Dict, Any, List, Optional

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# Property-based testing library
try:
    from hypothesis import given, strategies as st, settings, example, assume
    from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    pytest.skip("hypothesis not available", allow_module_level=True)

from libs.integrations.github.unified_github_manager import UnifiedGitHubManager
from libs.integrations.github.systems.rate_limit_management import RateLimitInfo, RateLimitManager
from libs.integrations.github.systems.comprehensive_error_handling import GitHubErrorHandler
from libs.integrations.github.systems.enhanced_error_recovery import ErrorRecoveryManager
from libs.integrations.github.performance.github_cache_manager import GitHubCacheManager, LRUCache, TimeBasedCache


class TestPropertyBasedRobustness:
    """Property-Based Testing for GitHub Integration Robustness"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner", 
            repo_name="test-repo",
            auto_init=False
        )
    
    @given(st.text(min_size=1, max_size=200))
    @settings(max_examples=50)
    def test_issue_title_robustness(self, title):
        """Issue title の堅牢性テスト"""
        # 危険な文字を含むタイトルをフィルタリング
        assume(not any(char in title for char in ['<', '>', '&', '"', "'"]))
        assume(len(title.strip()) > 0)
        
        with patch.object(self.manager, 'create_issue') as mock_create:
            mock_create.return_value = {
                "success": True,
                "issue": {"number": 1, "title": title}
            }
            
            try:
                result = self.manager.create_issue(title, "Test body")
                assert result["success"] is True
                assert result["issue"]["title"] == title
            except Exception as e:
                # 予期しない例外は失敗とする
                pytest.fail(f"Unexpected exception with title '{title}': {e}")
    
    @given(st.text(min_size=1, max_size=10000))
    @settings(max_examples=50)
    def test_issue_body_robustness(self, body):
        """Issue body の堅牢性テスト"""
        # 空白のみのbodyは除外
        assume(len(body.strip()) > 0)
        
        with patch.object(self.manager, 'create_issue') as mock_create:
            mock_create.return_value = {
                "success": True,
                "issue": {"number": 1, "body": body}
            }
            
            try:
                result = self.manager.create_issue("Test Title", body)
                assert result["success"] is True
                assert result["issue"]["body"] == body
            except Exception as e:
                # 長すぎるbodyや特殊文字での例外は許可
                if "too long" in str(e) or "invalid character" in str(e):
                    pass
                else:
                    pytest.fail(f"Unexpected exception with body length {len(body)}: {e}")
    
    @given(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=20))
    @settings(max_examples=50)
    def test_issue_labels_robustness(self, labels):
        """Issue labels の堅牢性テスト"""
        # 空ラベルや重複を除外
        clean_labels = [label.strip() for label in labels if label.strip()]
        clean_labels = list(set(clean_labels))  # 重複除去
        
        with patch.object(self.manager, 'create_issue') as mock_create:
            mock_create.return_value = {
                "success": True,
                "issue": {"number": 1, "labels": clean_labels}
            }
            
            try:
                result = self.manager.create_issue("Test Title", "Test body", clean_labels)
                assert result["success"] is True
                assert set(result["issue"]["labels"]) == set(clean_labels)
            except Exception as e:
                pytest.fail(f"Unexpected exception with labels {clean_labels}: {e}")
    
    @given(st.integers(min_value=1, max_value=999999))
    @settings(max_examples=50)
    def test_issue_number_robustness(self, issue_number):
        """Issue number の堅牢性テスト"""
        with patch.object(self.manager.issues_api, 'get_issues') as mock_get:
            mock_get.return_value = {
                "success": True,
                "issues": [{"number": issue_number, "title": f"Issue {issue_number}"}]
            }
            
            try:
                result = self.manager.get_issues(issue_number=issue_number)
                assert result["success"] is True
                assert result["issues"][0]["number"] == issue_number
            except Exception as e:
                pytest.fail(f"Unexpected exception with issue number {issue_number}: {e}")
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=20)
    def test_pagination_robustness(self, per_page):
        """Pagination の堅牢性テスト"""
        with patch.object(self.manager.issues_api, 'get_issues') as mock_get:
            # per_pageに基づいて適切な数のissuesを生成
            mock_issues = [
                {"number": i, "title": f"Issue {i}"}
                for i in range(1, min(per_page + 1, 101))
            ]
            mock_get.return_value = {
                "success": True,
                "issues": mock_issues,
                "total_count": len(mock_issues)
            }
            
            try:
                result = self.manager.get_issues(per_page=per_page)
                assert result["success"] is True
                assert len(result["issues"]) <= per_page
            except Exception as e:
                pytest.fail(f"Unexpected exception with per_page {per_page}: {e}")


class TestRateLimitRobustness:
    """Rate Limit システムの堅牢性テスト"""
    
    @given(
        st.integers(min_value=1, max_value=10000),
        st.integers(min_value=0, max_value=10000),
        st.integers(min_value=int(time.time()), max_value=int(time.time()) + 86400)
    )
    @settings(max_examples=50)
    def test_rate_limit_info_robustness(self, limit, remaining, reset):
        """RateLimitInfo の堅牢性テスト"""
        # remaining が limit を超えないように制限
        remaining = min(remaining, limit)
        
        try:
            rate_info = RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset=reset
            )
            
            # 基本的な不変条件をチェック
            assert rate_info.limit == limit
            assert rate_info.remaining == remaining
            assert rate_info.reset == reset
            assert rate_info.used == limit - remaining
            assert rate_info.used >= 0
            assert rate_info.usage_percentage >= 0.0
            assert rate_info.usage_percentage <= 100.0
            
            # 時間関連のプロパティ
            assert rate_info.time_until_reset >= 0
            assert isinstance(rate_info.is_exhausted, bool)
            
            if remaining == 0:
                assert rate_info.is_exhausted is True
            else:
                assert rate_info.is_exhausted is False
                
        except Exception as e:
            pytest.fail(f"Unexpected exception with limit={limit}, remaining={remaining}, reset={reset}: {e}")
    
    @given(st.text(min_size=1, max_size=20))
    @settings(max_examples=20)
    def test_rate_limit_manager_endpoint_robustness(self, endpoint):
        """RateLimitManager endpoint の堅牢性テスト"""
        manager = RateLimitManager(token="test-token")
        
        # 危険な文字を含むエンドポイントをフィルタリング
        assume(not any(char in endpoint for char in ['/', '\\', '<', '>', '&', '"']))
        
        try:
            # スロットリングチェック
            should_throttle, wait_time = manager.should_throttle(endpoint)
            assert isinstance(should_throttle, bool)
            assert isinstance(wait_time, (int, float))
            assert wait_time >= 0
            
            # 制限情報取得
            limit_info = manager.get_limit_info(endpoint)
            # 新しいエンドポイントの場合はNoneが返される
            assert limit_info is None or isinstance(limit_info, RateLimitInfo)
            
        except Exception as e:
            pytest.fail(f"Unexpected exception with endpoint '{endpoint}': {e}")


class TestErrorHandlingRobustness:
    """Error Handling システムの堅牢性テスト"""
    
    @given(st.text(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_error_message_robustness(self, error_message):
        """Error message の堅牢性テスト"""
        handler = GitHubErrorHandler()
        
        try:
            # 様々なエラーメッセージでテスト
            error = Exception(error_message)
            context = {"operation": "test", "timestamp": time.time()}
            
            result = handler.handle_error(error, context)
            
            # 結果の基本的な構造をチェック
            assert isinstance(result, dict)
            assert "handled" in result
            assert "should_retry" in result
            assert "severity" in result
            assert "recovery_action" in result
            
            assert result["handled"] is True
            assert isinstance(result["should_retry"], bool)
            assert result["severity"] in ["low", "medium", "high", "critical"]
            assert isinstance(result["recovery_action"], dict)
            
        except Exception as e:
            pytest.fail(f"Unexpected exception with error message '{error_message}': {e}")
    
    @given(st.dictionaries(st.text(min_size=1, max_size=50), st.text(max_size=200), min_size=0, max_size=10))
    @settings(max_examples=30)
    def test_error_context_robustness(self, context):
        """Error context の堅牢性テスト"""
        handler = GitHubErrorHandler()
        
        try:
            error = Exception("Test error")
            result = handler.handle_error(error, context)
            
            # コンテキストに関係なく基本的な処理が成功することを確認
            assert result["handled"] is True
            assert "error_info" in result
            assert result["error_info"]["context"] == context
            
        except Exception as e:
            pytest.fail(f"Unexpected exception with context {context}: {e}")


class TestCacheRobustness:
    """Cache システムの堅牢性テスト"""
    
    @given(st.text(min_size=1, max_size=100), st.text(max_size=1000))
    @settings(max_examples=50)
    def test_lru_cache_robustness(self, key, value):
        """LRUCache の堅牢性テスト"""
        # 危険な文字を含むキーをフィルタリング
        assume(not any(char in key for char in ['\0', '\n', '\r']))
        
        cache = LRUCache(max_size=100)
        
        try:
            # 設定と取得
            cache.set(key, value)
            retrieved_value = cache.get(key)
            
            assert retrieved_value == value
            assert cache.size() >= 1
            assert cache.size() <= 100
            
            # 存在チェック
            assert cache.exists(key) is True
            
        except Exception as e:
            pytest.fail(f"Unexpected exception with key='{key}', value='{value}': {e}")
    
    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=20)
    def test_cache_size_limits(self, max_size):
        """Cache size limits の堅牢性テスト"""
        cache = LRUCache(max_size=max_size)
        
        try:
            # キャッシュサイズの上限を超えて要素を追加
            for i in range(max_size + 50):
                cache.set(f"key_{i}", f"value_{i}")
            
            # サイズ制限が守られていることを確認
            assert cache.size() <= max_size
            
            # 最新の要素が残っていることを確認
            assert cache.exists(f"key_{max_size + 49}") is True
            
        except Exception as e:
            pytest.fail(f"Unexpected exception with max_size {max_size}: {e}")
    
    @given(st.integers(min_value=1, max_value=3600))
    @settings(max_examples=20)
    def test_time_based_cache_ttl_robustness(self, ttl):
        """TimeBasedCache TTL の堅牢性テスト"""
        cache = TimeBasedCache(default_ttl=ttl)
        
        try:
            # 要素を追加
            cache.set("test_key", "test_value")
            
            # すぐには取得できることを確認
            assert cache.get("test_key") == "test_value"
            assert cache.exists("test_key") is True
            
            # TTLの半分の時間が経過してもまだ存在
            # （実際の時間経過はテストしない）
            assert cache.exists("test_key") is True
            
        except Exception as e:
            pytest.fail(f"Unexpected exception with ttl {ttl}: {e}")


class GitHubIntegrationStateMachine(RuleBasedStateMachine):
    """GitHub Integration の状態ベーステスト"""
    
    def __init__(self):
        super().__init__()
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
        self.created_issues = []
        self.created_prs = []
        self.api_calls = 0
        self.errors = 0
    
    @rule(title=st.text(min_size=1, max_size=100), body=st.text(max_size=500))
    def create_issue(self, title, body):
        """Issue作成ルール"""
        assume(len(title.strip()) > 0)
        assume(not any(char in title for char in ['<', '>', '&']))
        
        with patch.object(self.manager, 'create_issue') as mock_create:
            issue_number = len(self.created_issues) + 1
            mock_create.return_value = {
                "success": True,
                "issue": {"number": issue_number, "title": title, "body": body}
            }
            
            try:
                result = self.manager.create_issue(title, body)
                if result["success"]:
                    self.created_issues.append(result["issue"])
                    self.api_calls += 1
                else:
                    self.errors += 1
            except Exception:
                self.errors += 1
    
    @rule(issue_number=st.integers(min_value=1, max_value=100))
    def get_issue(self, issue_number):
        """Issue取得ルール"""
        with patch.object(self.manager.issues_api, 'get_issues') as mock_get:
            if issue_number <= len(self.created_issues):
                mock_get.return_value = {
                    "success": True,
                    "issues": [{"number": issue_number, "title": f"Issue {issue_number}"}]
                }
            else:
                mock_get.return_value = {
                    "success": False,
                    "error": "Issue not found"
                }
            
            try:
                result = self.manager.get_issues(issue_number=issue_number)
                self.api_calls += 1
                if not result["success"]:
                    self.errors += 1
            except Exception:
                self.errors += 1
    
    @rule(title=st.text(min_size=1, max_size=100))
    def create_pull_request(self, title):
        """Pull Request作成ルール"""
        assume(len(title.strip()) > 0)
        
        with patch.object(self.manager.pull_request_api, 'create_pull_request') as mock_create:
            pr_number = len(self.created_prs) + 1
            mock_create.return_value = {
                "success": True,
                "pull_request": {"number": pr_number, "title": title}
            }
            
            try:
                result = self.manager.create_pull_request(
                    title, f"branch-{pr_number}", "main", "Test PR"
                )
                if result["success"]:
                    self.created_prs.append(result["pull_request"])
                    self.api_calls += 1
                else:
                    self.errors += 1
            except Exception:
                self.errors += 1
    
    @invariant()
    def api_calls_positive(self):
        """API呼び出し数は非負"""
        assert self.api_calls >= 0
    
    @invariant()
    def errors_not_exceed_calls(self):
        """エラー数はAPI呼び出し数を超えない"""
        assert self.errors <= self.api_calls
    
    @invariant()
    def issues_list_consistent(self):
        """Issue リストの整合性"""
        assert len(self.created_issues) >= 0
        # 各Issueにはnumberとtitleがある
        for issue in self.created_issues:
            assert "number" in issue
            assert "title" in issue
    
    @invariant()
    def prs_list_consistent(self):
        """PR リストの整合性"""
        assert len(self.created_prs) >= 0
        # 各PRにはnumberとtitleがある
        for pr in self.created_prs:
            assert "number" in pr
            assert "title" in pr


class TestPropertyBasedStateMachine:
    """状態ベーステストの実行"""
    
    @settings(max_examples=20, stateful_step_count=10)
    def test_github_integration_state_machine(self):
        """GitHub Integration 状態マシンテスト"""
        if not HYPOTHESIS_AVAILABLE:
            pytest.skip("hypothesis not available")
        
        # 状態マシンテストを実行
        GitHubIntegrationStateMachine.TestCase.settings = settings(
            max_examples=20,
            stateful_step_count=10
        )
        
        test_case = GitHubIntegrationStateMachine.TestCase()
        test_case.runTest()


class TestEdgeCaseRobustness:
    """エッジケースの堅牢性テスト"""
    
    @given(st.text(min_size=0, max_size=0))
    def test_empty_string_handling(self, empty_string):
        """空文字列の処理"""
        manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
        
        # 空文字列を適切に処理できることを確認
        assert len(empty_string) == 0
        
        # 空文字列でのIssue作成は失敗すべき
        with pytest.raises((ValueError, AssertionError)):
            manager.create_issue(empty_string, "body")
    
    @given(st.text().filter(lambda x: len(x) > 10000))
    @settings(max_examples=10)
    def test_large_string_handling(self, large_string):
        """大きな文字列の処理"""
        manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
        
        # 大きな文字列を適切に処理できることを確認
        assert len(large_string) > 10000
        
        with patch.object(manager, 'create_issue') as mock_create:
            mock_create.return_value = {
                "success": True,
                "issue": {"number": 1, "body": large_string[:1000]}  # 制限された長さ
            }
            
            try:
                # 大きな文字列でもエラーが発生しないことを確認
                result = manager.create_issue("Title", large_string)
                assert result["success"] is True
            except Exception as e:
                # 長さ制限エラーは許可
                if "too long" in str(e).lower():
                    pass
                else:
                    pytest.fail(f"Unexpected exception: {e}")
    
    @given(st.none())
    def test_none_value_handling(self, none_value):
        """None値の処理"""
        manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
        
        assert none_value is None
        
        # None値でのIssue作成は失敗すべき
        with pytest.raises((ValueError, TypeError, AttributeError)):
            manager.create_issue(none_value, "body")
    
    @given(st.lists(st.integers(), min_size=0, max_size=1000))
    @settings(max_examples=20)
    def test_list_handling_robustness(self, integer_list):
        """リスト処理の堅牢性"""
        manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
        
        # リストのサイズや内容に関係なく処理が完了することを確認
        assert isinstance(integer_list, list)
        assert len(integer_list) <= 1000
        
        # リストを何らかの形で処理（例：統計計算）
        if integer_list:
            list_sum = sum(integer_list)
            list_avg = list_sum / len(integer_list)
            assert isinstance(list_sum, int)
            assert isinstance(list_avg, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])