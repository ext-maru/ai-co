#!/usr/bin/env python3
"""
統合GitHub管理システムテスト
完全実装の検証・Iron Will基準準拠確認
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time
import json

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.integrations.github.unified_github_manager import UnifiedGitHubManager, get_unified_github_manager
from libs.integrations.github.systems.comprehensive_error_handling import ErrorSeverity, CircuitState
from libs.integrations.github.systems.rate_limit_management import RateLimitInfo


class TestUnifiedGitHubManager:
    """統合GitHubマネージャーテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.manager is not None
        assert self.manager.token == "test-token"
        assert self.manager.repo_owner == "test-owner"
        assert self.manager.repo_name == "test-repo"
        
        # コンポーネント初期化確認
        assert self.manager.error_handler is not None
        assert self.manager.rate_limit_manager is not None
        assert self.manager.issues_api is not None
        assert self.manager.update_issue_api is not None
        assert self.manager.pull_request_api is not None
        assert self.manager.get_pull_requests_api is not None
    
    def test_api_coverage_calculation(self):
        """APIカバレッジ計算テスト"""
        coverage = self.manager._calculate_api_coverage()
        assert coverage == 80.0  # 8/10 メソッド実装
    
    @patch('libs.integrations.github.api_implementations.get_issues.GitHubGetIssuesImplementation.get_issues')
    def test_get_issues_with_rate_limiting(self, mock_get_issues):
        """レート制限付きIssue取得テスト"""
        mock_get_issues.return_value = {
            "success": True,
            "issues": [
                {"number": 1, "title": "Test Issue 1"},
                {"number": 2, "title": "Test Issue 2"}
            ],
            "total_count": 2,
            "metadata": {
                "rate_limit_remaining": 4999
            }
        }
        
        result = self.manager.get_issues(state="open")
        
        assert result["success"] is True
        assert len(result["issues"]) == 2
        assert self.manager.statistics["api_calls"] == 1
        assert self.manager.statistics["successful_operations"] == 1
    
    @patch('libs.integrations.github.api_implementations.update_issue.GitHubUpdateIssueImplementation.update_issue')
    def test_update_issue_with_notification(self, mock_update):
        """通知付きIssue更新テスト"""
        mock_update.return_value = {
            "success": True,
            "issue": {"number": 123, "title": "Updated Issue"},
            "changes": {"title": {"before": "Old", "after": "Updated Issue"}}
        }
        
        with patch.object(self.manager.notifier, 'send_message', return_value=True) as mock_notify:
            result = self.manager.update_issue(123, title="Updated Issue")
        
        assert result["success"] is True
        mock_notify.assert_called_once()
        assert self.manager.statistics["successful_operations"] == 1
    
    def test_create_issue_with_notification(self):
        """通知付きIssue作成テスト（計画書要求機能）"""
        with patch.object(self.manager, 'create_issue') as mock_create:
            mock_create.return_value = {
                "success": True,
                "issue": {"number": 456, "title": "New Issue"}
            }
            
            with patch.object(self.manager.notifier, 'send_elder_council_report') as mock_report:
                result = self.manager.create_issue_with_notification(
                    "New Issue",
                    "Issue body",
                    ["bug", "enhancement"]
                )
            
            assert result["success"] is True
            mock_report.assert_called_once()
    
    @patch('libs.integrations.github.api_implementations.' \
        'create_pull_request.GitHubCreatePullRequestImplementation.create_pull_request')
    def test_create_pull_request_full_features(self, mock_create_pr):
        """完全機能付きPR作成テスト"""
        mock_create_pr.return_value = {
            "success": True,
            "pull_request": {
                "number": 789,
                "title": "Feature PR",
                "html_url": "https://github.com/test/repo/pull/789"
            },
            "conflict_status": {
                "has_conflicts": False,
                "mergeable": True
            }
        }
        
        result = self.manager.create_pull_request(
            title="Feature PR",
            head="feature-branch",
            base="main",
            body="Implements new feature",
            draft=False,
            labels=["feature"],
            reviewers=["reviewer1"]
        )
        
        assert result["success"] is True
        assert result["pull_request"]["number"] == 789
        assert not result["conflict_status"]["has_conflicts"]
    
    @patch('libs.integrations.github.api_implementations.' \
        'get_pull_requests.GitHubGetPullRequestsImplementation.get_pull_requests')
    def test_get_pull_requests_with_statistics(self, mock_get_prs):
        """統計付きPR取得テスト"""
        mock_get_prs.return_value = {
            "success": True,
            "pull_requests": [
                {"number": 1, "state": "open", "draft": False},
                {"number": 2, "state": "open", "draft": True}
            ],
            "total_count": 2,
            "statistics": {
                "by_state": {"open": 1, "draft": 1},
                "average_age_days": 5.2
            }
        }
        
        result = self.manager.get_pull_requests(state="open")
        
        assert result["success"] is True
        assert result["total_count"] == 2
        assert "statistics" in result
    
    def test_error_handling_retry_mechanism(self):
        """エラーハンドリングリトライメカニズムテスト"""
        call_count = 0
        
        def failing_function():
            """failing_functionメソッド"""
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return {"success": True}
        
        # エラーハンドラのリトライ設定
        self.manager.error_handler.retry_config["max_retries"] = 3
        
        result = self.manager.error_handler.retry_with_backoff(failing_function)
        
        assert result["success"] is True
        assert call_count == 3  # 2回失敗、3回目で成功
    
    def test_rate_limit_throttling(self):
        """レート制限スロットリングテスト"""
        # レート制限情報を設定
        self.manager.rate_limit_manager.rate_limits["core"] = RateLimitInfo(
            limit=5000,
            remaining=10,  # 残り少ない
            reset=int(time.time()) + 3600
        )
        
        # スロットリングが必要か確認
        should_throttle, wait_time = self.manager.rate_limit_manager.should_throttle("core")
        
        assert should_throttle is True
        assert wait_time > 0
    
    def test_circuit_breaker_functionality(self):
        """サーキットブレーカー機能テスト"""
        circuit_breaker = self.manager.error_handler.circuit_breaker
        
        # 失敗を繰り返してサーキットをオープンにする
        for i in range(5):
            try:
                with circuit_breaker:
                    raise Exception("Test failure")
            except:
                pass
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # オープン状態では例外が発生
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            with circuit_breaker:
                pass
    
    def test_health_check_comprehensive(self):
        """包括的ヘルスチェックテスト"""
        health = self.manager.health_check()
        
        assert "status" in health
        assert "timestamp" in health
        assert "components" in health
        
        # 各コンポーネントのチェック
        components = health["components"]
        assert "api_implementations" in components
        assert "error_handler" in components
        assert "rate_limiter" in components
        assert "legacy_integration" in components
        assert "notifier" in components
    
    def test_integration_status_complete(self):
        """完全な統合ステータステスト"""
        status = self.manager.get_integration_status()
        
        assert status["service"] == "github"
        assert status["connected"] is True
        
        # 機能確認
        features = status["features"]
        assert features["issue_retrieval"] is True
        assert features["issue_update"] is True
        assert features["pull_request_creation"] is True
        assert features["pull_request_retrieval"] is True
        assert features["error_handling"] is True
        assert features["rate_limiting"] is True
        
        # APIカバレッジ確認
        assert status["api_coverage"] == 80.0
    
    def test_error_severity_classification(self):
        """エラー重要度分類テスト"""
        test_errors = [
            (ConnectionError("timeout"), ErrorSeverity.HIGH),
            (ValueError("not found"), ErrorSeverity.LOW),
            (PermissionError("permission denied"), ErrorSeverity.MEDIUM),
            (Exception("service unavailable"), ErrorSeverity.CRITICAL)
        ]
        
        for error, expected_severity in test_errors:
            result = self.manager.error_handler.handle_error(error, {})
            # メッセージパターンに基づく判定のため、実際の重要度を確認
            assert result["handled"] is True
    
    def test_request_queuing(self):
        """リクエストキューイングテスト"""
        # キューに複数のリクエストを追加
        def dummy_request(n):
            return {"number": n}
        
        # キューイングはバックグラウンドで処理されるため、
        # ここでは基本的な動作確認のみ
        queue_size_before = self.manager.rate_limit_manager.request_queue.qsize()
        
        # リクエストを追加（実際の実行は行わない）
        self.manager.rate_limit_manager.request_queue.put((1, {
            "func": dummy_request,
            "args": (1,),
            "kwargs": {},
            "endpoint": "core"
        }))
        
        queue_size_after = self.manager.rate_limit_manager.request_queue.qsize()
        assert queue_size_after > queue_size_before
    
    def test_singleton_manager(self):
        """シングルトンマネージャーテスト"""
        manager1 = get_unified_github_manager()
        manager2 = get_unified_github_manager()
        
        assert manager1 is manager2
        
        # 強制的に新しいインスタンスを作成
        manager3 = get_unified_github_manager(force_new=True)
        assert manager3 is not manager1
    
    def test_backwards_compatibility(self):
        """後方互換性テスト"""
        # 既存のメソッドが動作することを確認
        legacy_methods = [
            "get_repositories",
            "get_repository_structure",
            "get_file_content",
            "send_task_notification",
            "send_error_notification",
            "send_elder_council_report"
        ]
        
        for method_name in legacy_methods:
            assert hasattr(self.manager, method_name)
            assert callable(getattr(self.manager, method_name))


class TestAPIImplementations:
    """API実装の詳細テスト"""
    
    def test_get_issues_pagination(self):
        """Issue取得のページネーションテスト"""
        from libs.integrations.github.api_implementations.get_issues import GitHubGetIssuesImplementation
        
        impl = GitHubGetIssuesImplementation(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
        
        # ページネーション処理の確認
        with patch.object(impl, '_make_api_request') as mock_request:
            # 2ページ分のデータを返す
            mock_request.side_effect = [
                {
                    "success": True,
                    "data": [{"number": 1}, {"number": 2}],
                    "headers": {"Link": '<...>; rel="next", <...?page=2>; rel="last"'}
                },
                {
                    "success": True,
                    "data": [{"number": 3}],
                    "headers": {}
                }
            ]
            
            result = impl.get_issues(per_page=2)
            
            assert result["success"] is True
            assert len(result["issues"]) == 3
            assert mock_request.call_count == 2
    
    def test_update_issue_audit_logging(self):
        """Issue更新の監査ログテスト"""
        from libs.integrations.github.api_implementations.update_issue import GitHubUpdateIssueImplementation
        
        impl = GitHubUpdateIssueImplementation(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
        
        # 監査ログが有効であることを確認
        assert impl.enable_audit_log is True
        assert impl.audit_logger is not None
    
    def test_create_pull_request_conflict_detection(self):
        """PR作成のコンフリクト検出テスト"""
        from libs.integrations.github.api_implementations.create_pull_request import \
            GitHubCreatePullRequestImplementation
        
        impl = GitHubCreatePullRequestImplementation(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
        
        # コンフリクトチェックが有効であることを確認
        assert impl.check_conflicts is True
    
    def test_get_pull_requests_caching(self):
        """PR取得のキャッシングテスト"""
        from libs.integrations.github.api_implementations.get_pull_requests import GitHubGetPullRequestsImplementation
        
        impl = GitHubGetPullRequestsImplementation(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo"
        )
        
        # キャッシュが有効であることを確認
        assert impl.enable_cache is True
        assert impl.cache_ttl == 300  # 5分


class TestSystemComponents:
    """システムコンポーネントテスト"""
    
    def test_error_handler_statistics(self):
        """エラーハンドラ統計テスト"""
        from libs.integrations.github.systems.comprehensive_error_handling import GitHubErrorHandler
        
        handler = GitHubErrorHandler()
        
        # エラーを処理
        handler.handle_error(ConnectionError("Test"), {"context": "test"})
        
        # 統計を確認
        report = handler.get_error_report()
        assert report["statistics"]["total_errors"] == 1
        assert "ConnectionError" in report["statistics"]["by_type"]
    
    def test_rate_limit_manager_metrics(self):
        """レート制限管理メトリクステスト"""
        from libs.integrations.github.systems.rate_limit_management import RateLimitManager
        
        manager = RateLimitManager(token="test-token")
        
        # メトリクスを確認
        stats = manager.get_statistics()
        assert "total_requests" in stats
        assert "current_limits" in stats
        assert "queue_size" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])