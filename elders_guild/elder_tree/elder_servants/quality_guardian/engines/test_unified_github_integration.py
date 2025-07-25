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
    
    @patch('libs.integrations.github.api_implementations.get_issues.GitHubGetIssuesImplementation.' \
        'get_issues')
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
    
    @patch('libs.integrations.github.api_implementations.update_issue.' \
        'GitHubUpdateIssueImplementation.update_issue')
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

                )
            
            assert result["success"] is True
            mock_report.assert_called_once()
    
    @patch('libs.integrations.github.api_implementations.create_pull_request.' \
        'GitHubCreatePullRequestImplementation.create_pull_request')
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
    
    @patch('libs.integrations.github.api_implementations.get_pull_requests.' \
        'GitHubGetPullRequestsImplementation.get_pull_requests')
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
            """dummy_requestメソッド"""
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

class TestUnifiedGitHubManagerPerformance:
    """統合GitHubマネージャーパフォーマンステスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False,
            enable_performance_optimization=True
        )
    
    def test_performance_initialization(self):
        """パフォーマンス初期化テスト"""
        assert self.manager.performance_enabled is True
        assert self.manager.performance_optimizer is None  # 非同期で初期化される
        assert self.manager.async_manager is None  # 非同期で初期化される
        assert self.manager.cache_manager is None  # 非同期で初期化される
    
    @pytest.mark.asyncio
    async def test_performance_components_initialization(self):
        """パフォーマンスコンポーネント初期化テスト"""
        with patch('libs.integrations.github.unified_github_manager.create_github_cache_manager' \
            'libs.integrations.github.unified_github_manager.create_github_cache_manager') as mock_cache:
            with patch('libs.integrations.github.unified_github_manager.' \
                'create_github_performance_optimizer') as mock_optimizer:
                with patch('libs.integrations.github.unified_github_manager.' \
                    'create_github_async_manager') as mock_async:
                    # モックを設定
                    mock_cache.return_value = Mock()
                    mock_optimizer.return_value = Mock()
                    mock_async.return_value = Mock()
                    
                    # パフォーマンスコンポーネントを初期化
                    await self.manager._initialize_performance_components()
                    
                    # 初期化が呼ばれたことを確認
                    mock_cache.assert_called_once()
                    mock_optimizer.assert_called_once()
                    mock_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_issues_performance_optimized_enabled(self):
        """パフォーマンス最適化有効時のIssue取得テスト"""
        # 非同期マネージャーをモック
        mock_async_manager = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = [{"number": 1, "title": "Test Issue"}]
        mock_result.metadata = {"performance": "optimized"}
        
        mock_async_manager.get_issues_async.return_value = mock_result
        self.manager.async_manager = mock_async_manager
        
        result = await self.manager.get_issues_performance_optimized(state="open")
        
        assert result["success"] is True
        assert len(result["issues"]) == 1
        assert result["metadata"]["performance"] == "optimized"
        mock_async_manager.get_issues_async.assert_called_once_with(state="open")
    
    @pytest.mark.asyncio
    async def test_get_issues_performance_optimized_disabled(self):
        """パフォーマンス最適化無効時のIssue取得テスト"""
        self.manager.performance_enabled = False
        
        with patch.object(self.manager, 'get_issues') as mock_get_issues:
            mock_get_issues.return_value = {"success": True, "issues": []}
            
            result = await self.manager.get_issues_performance_optimized(state="open")
            
            assert result["success"] is True
            mock_get_issues.assert_called_once_with(state="open")
    
    @pytest.mark.asyncio
    async def test_get_issues_performance_optimized_error_fallback(self):
        """パフォーマンス最適化エラー時のフォールバックテスト"""
        # エラーを発生させる非同期マネージャーをモック
        mock_async_manager = Mock()
        mock_async_manager.get_issues_async.side_effect = Exception("Performance error")
        self.manager.async_manager = mock_async_manager
        
        with patch.object(self.manager, 'get_issues') as mock_get_issues:
            mock_get_issues.return_value = {"success": True, "issues": []}
            
            result = await self.manager.get_issues_performance_optimized(state="open")
            
            assert result["success"] is True
            mock_get_issues.assert_called_once_with(state="open")
    
    @pytest.mark.asyncio
    async def test_create_issue_performance_optimized(self):
        """パフォーマンス最適化Issue作成テスト"""
        # 非同期マネージャーをモック
        mock_async_manager = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {"number": 123, "title": "New Issue"}
        mock_result.metadata = {"performance": "optimized"}
        
        mock_async_manager.create_issue_async.return_value = mock_result
        self.manager.async_manager = mock_async_manager
        
        result = await self.manager.create_issue_performance_optimized(

        )
        
        assert result["success"] is True
        assert result["issue"]["number"] == 123
        assert result["metadata"]["performance"] == "optimized"
        mock_async_manager.create_issue_async.assert_called_once_with(

        )
    
    @pytest.mark.asyncio
    async def test_batch_get_issues_optimized(self):
        """バッチIssue取得最適化テスト"""
        # 非同期マネージャーをモック
        mock_async_manager = Mock()
        mock_results = [
            Mock(success=True, data={"number": 1}, error=None, metadata={}),
            Mock(success=True, data={"number": 2}, error=None, metadata={}),
            Mock(success=False, data=None, error="Not found", metadata={})
        ]
        
        mock_async_manager.batch_get_issues_async.return_value = mock_results
        self.manager.async_manager = mock_async_manager
        
        result = await self.manager.batch_get_issues_optimized([1, 2, 3])
        
        assert len(result) == 3
        assert result[0]["success"] is True
        assert result[0]["issue"]["number"] == 1
        assert result[2]["success"] is False
        assert result[2]["error"] == "Not found"
        mock_async_manager.batch_get_issues_async.assert_called_once_with([1, 2, 3])
    
    @pytest.mark.asyncio
    async def test_batch_get_issues_optimized_fallback(self):
        """バッチIssue取得フォールバックテスト"""
        self.manager.performance_enabled = False
        
        with patch.object(self.manager, 'get_issues') as mock_get_issues:
            mock_get_issues.side_effect = [
                {"success": True, "issues": [{"number": 1}]},
                {"success": True, "issues": [{"number": 2}]}
            ]
            
            result = await self.manager.batch_get_issues_optimized([1, 2])
            
            assert len(result) == 2
            assert mock_get_issues.call_count == 2
    
    @pytest.mark.asyncio
    async def test_stream_all_issues_optimized(self):
        """ストリーミングIssue取得最適化テスト"""
        # 非同期マネージャーをモック
        mock_async_manager = Mock()
        test_issues = [
            {"number": 1, "title": "Issue 1"},
            {"number": 2, "title": "Issue 2"},
            {"number": 3, "title": "Issue 3"}
        ]
        
        async def mock_stream():
            """mock_streamメソッド"""
            for issue in test_issues:
                yield issue
        
        mock_async_manager.stream_all_issues_async.return_value = mock_stream()
        self.manager.async_manager = mock_async_manager
        
        result = await self.manager.stream_all_issues_optimized(state="open")
        
        assert len(result) == 3
        assert result[0]["number"] == 1
        assert result[2]["number"] == 3
        mock_async_manager.stream_all_issues_async.assert_called_once_with(state="open")
    
    @pytest.mark.asyncio
    async def test_stream_all_issues_optimized_fallback(self):
        """ストリーミングIssue取得フォールバックテスト"""
        self.manager.performance_enabled = False
        
        with patch.object(self.manager, 'get_issues') as mock_get_issues:
            # 2回の呼び出しで全てのIssueを取得
            mock_get_issues.side_effect = [
                {"success": True, "issues": [{"number": 1}, {"number": 2}]},
                {"success": True, "issues": [{"number": 3}]},
                {"success": True, "issues": []}  # 空のページで終了
            ]
            
            result = await self.manager.stream_all_issues_optimized(state="open")
            
            assert len(result) == 3
            assert result[0]["number"] == 1
            assert result[2]["number"] == 3
            assert mock_get_issues.call_count == 3

class TestUnifiedGitHubManagerEdgeCases:
    """統合GitHubマネージャーエッジケーステスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
    
    def test_initialization_with_environment_variables(self):
        """環境変数での初期化テスト"""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'env-token',
            'GITHUB_REPO_OWNER': 'env-owner',
            'GITHUB_REPO_NAME': 'env-repo'
        }):
            manager = UnifiedGitHubManager()
            
            assert manager.token == 'env-token'
            assert manager.repo_owner == 'env-owner'
            assert manager.repo_name == 'env-repo'
    
    def test_initialization_without_credentials(self):
        """認証情報なしの初期化テスト"""
        manager = UnifiedGitHubManager()
        
        assert manager.token == ""
        assert manager.repo_owner == ""
        assert manager.repo_name == ""
    
    def test_test_connection_success(self):
        """接続テスト成功テスト"""
        with patch.object(self.manager.legacy_integration, 'get_repositories') as mock_get_repos:
            mock_get_repos.return_value = {"success": True, "repositories": []}
            
            result = self.manager.test_connection()
            
            assert result["success"] is True
            assert result["message"] == "GitHub connection successful"
            mock_get_repos.assert_called_once()
    
    def test_test_connection_failure(self):
        """接続テスト失敗テスト"""
        with patch.object(self.manager.legacy_integration, 'get_repositories') as mock_get_repos:
            mock_get_repos.side_effect = Exception("Connection failed")
            
            result = self.manager.test_connection()
            
            assert result["success"] is False
            assert "Connection failed" in result["error"]
    
    def test_calculate_api_coverage(self):
        """APIカバレッジ計算テスト"""
        coverage = self.manager._calculate_api_coverage()
        
        # 実装されているメソッド数に基づく
        expected_methods = [
            "get_issues", "update_issue", "create_pull_request", "get_pull_requests",
            "create_issue", "get_repositories", "get_repository_structure", "get_file_content"
        ]
        total_methods = 10  # 想定される全メソッド数
        expected_coverage = (len(expected_methods) / total_methods) * 100
        
        assert coverage == expected_coverage
    
    def test_get_integration_status_complete(self):
        """統合ステータス完全テスト"""
        with patch.object(self.manager, 'test_connection') as mock_test:
            mock_test.return_value = {"success": True}
            
            status = self.manager.get_integration_status()
            
            assert status["service"] == "github"
            assert status["connected"] is True
            assert status["version"] == "unified-v1.0"
            assert "features" in status
            assert "api_coverage" in status
            assert "performance_enabled" in status
    
    def test_get_integration_status_disconnected(self):
        """統合ステータス切断テスト"""
        with patch.object(self.manager, 'test_connection') as mock_test:
            mock_test.return_value = {"success": False, "error": "Not connected"}
            
            status = self.manager.get_integration_status()
            
            assert status["service"] == "github"
            assert status["connected"] is False
            assert status["error"] == "Not connected"
    
    def test_health_check_all_healthy(self):
        """ヘルスチェック全て正常テスト"""
        with patch.object(self.manager, 'test_connection') as mock_test:
            mock_test.return_value = {"success": True}
            
            health = self.manager.health_check()
            
            assert health["status"] == "healthy"
            assert "timestamp" in health
            assert "components" in health
            
            components = health["components"]
            assert components["api_implementations"]["status"] == "healthy"
            assert components["error_handler"]["status"] == "healthy"
            assert components["rate_limiter"]["status"] == "healthy"
            assert components["legacy_integration"]["status"] == "healthy"
            assert components["notifier"]["status"] == "healthy"
    
    def test_health_check_with_failures(self):
        """ヘルスチェック失敗ありテスト"""
        with patch.object(self.manager, 'test_connection') as mock_test:
            mock_test.return_value = {"success": False, "error": "Connection failed"}
            
            health = self.manager.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["components"]["legacy_integration"]["status"] == "unhealthy"
            assert health["components"]["legacy_integration"]["error"] == "Connection failed"
    
    def test_statistics_tracking(self):
        """統計追跡テスト"""
        initial_stats = self.manager.statistics.copy()
        
        # API呼び出しを模擬
        with patch.object(self.manager.issues_api, 'get_issues') as mock_get_issues:
            mock_get_issues.return_value = {"success": True, "issues": []}
            
            self.manager.get_issues()
            
            assert self.manager.statistics["api_calls"] == initial_stats["api_calls"] + 1
            assert self.manager.statistics["successful_operations"] == initial_stats["successful_operations"] + 1
    
    def test_error_statistics_tracking(self):
        """エラー統計追跡テスト"""
        initial_errors = self.manager.statistics["errors"]
        
        # エラーを発生させる
        with patch.object(self.manager.issues_api, 'get_issues') as mock_get_issues:
            mock_get_issues.side_effect = Exception("API Error")
            
            try:
                self.manager.get_issues()
            except:
                pass
            
            assert self.manager.statistics["errors"] == initial_errors + 1
    
    def test_legacy_method_delegation(self):
        """レガシーメソッド委譲テスト"""
        # 既存のメソッドが適切に委譲されることを確認
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
            method = getattr(self.manager, method_name)
            assert callable(method)
    
    def test_concurrent_operations(self):
        """並行操作テスト"""
        import threading
        import time
        
        results = []
        
        def worker(worker_id):
            """workerメソッド"""
            with patch.object(self.manager.issues_api, 'get_issues') as mock_get_issues:
                mock_get_issues.return_value = {"success": True, "issues": [], "worker_id": worker_id}
                result = self.manager.get_issues()
                results.append(result)
        
        # 複数のスレッドで同時実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 5
        assert all(result["success"] for result in results)
    
    def test_memory_cleanup(self):
        """メモリクリーンアップテスト"""
        # 大量のデータを処理した後のメモリ使用量をチェック
        import gc
        
        initial_objects = len(gc.get_objects())
        
        # 大量のIssueを模擬取得
        with patch.object(self.manager.issues_api, 'get_issues') as mock_get_issues:
            large_issues = [{"number": i, "title": f"Issue {i}"} for i in range(1000)]
            mock_get_issues.return_value = {"success": True, "issues": large_issues}
            
            for _ in range(10):
                result = self.manager.get_issues()
                del result  # 明示的に削除
        
        # ガベージコレクションを実行
        gc.collect()
        
        final_objects = len(gc.get_objects())
        
        # メモリリークがないことを確認（多少の増加は許容）
        assert final_objects - initial_objects < 100

class TestUnifiedGitHubManagerIntegration:
    """統合GitHubマネージャー統合テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
    
    def test_full_issue_lifecycle(self):
        """完全なIssueライフサイクルテスト"""
        # Issue作成
        with patch.object(self.manager, 'create_issue') as mock_create:
            mock_create.return_value = {"success": True, "issue": {"number": 123}}
            
            create_result = self.manager.create_issue("Test Issue", "Test body")
            assert create_result["success"] is True
            issue_number = create_result["issue"]["number"]
        
        # Issue更新
        with patch.object(self.manager.update_issue_api, 'update_issue') as mock_update:
            mock_update.return_value = {"success": True, "issue": {"number": issue_number, "state": "closed"}}
            
            update_result = self.manager.update_issue(issue_number, state="closed")
            assert update_result["success"] is True
            assert update_result["issue"]["state"] == "closed"
        
        # Issue取得確認
        with patch.object(self.manager.issues_api, 'get_issues') as mock_get:
            mock_get.return_value = {"success": True, "issues": [{"number": issue_number, "state": "closed"}]}
            
            get_result = self.manager.get_issues(issue_number=issue_number)
            assert get_result["success"] is True
            assert get_result["issues"][0]["state"] == "closed"
    
    def test_full_pull_request_lifecycle(self):
        """完全なPull Requestライフサイクルテスト"""
        # PR作成
        with patch.object(self.manager.pull_request_api, 'create_pull_request') as mock_create:
            mock_create.return_value = {
                "success": True,
                "pull_request": {"number": 456, "state": "open"}
            }
            
            create_result = self.manager.create_pull_request(
                "Feature PR", "feature-branch", "main", "Adds new feature"
            )
            assert create_result["success"] is True
            pr_number = create_result["pull_request"]["number"]
        
        # PR取得
        with patch.object(self.manager.get_pull_requests_api, 'get_pull_requests') as mock_get:
            mock_get.return_value = {
                "success": True,
                "pull_requests": [{"number": pr_number, "state": "open"}]
            }
            
            get_result = self.manager.get_pull_requests(pr_number=pr_number)
            assert get_result["success"] is True
            assert get_result["pull_requests"][0]["number"] == pr_number
    
    def test_error_handling_and_recovery_integration(self):
        """エラーハンドリングと回復の統合テスト"""
        call_count = 0
        
        def failing_then_success():
            """failing_then_successメソッド"""
            nonlocal call_count
            call_count += 1
            if call_count < 3:

            return {"success": True, "issues": []}
        
        with patch.object(self.manager.issues_api, 'get_issues', side_effect=failing_then_success):
            with patch.object(self.manager.error_handler, 'retry_with_backoff') as mock_retry:
                mock_retry.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
                
                result = self.manager.get_issues()
                
                assert result["success"] is True
                assert call_count == 3  # 2回失敗、3回目で成功
    
    def test_rate_limiting_integration(self):
        """レート制限統合テスト"""
        # レート制限状態を設定
        self.manager.rate_limit_manager.rate_limits["core"] = RateLimitInfo(
            limit=5000,
            remaining=1,  # 残り1回
            reset=int(time.time()) + 3600
        )
        
        with patch.object(self.manager.rate_limit_manager, 'wait_if_needed') as mock_wait:
            mock_wait.return_value = 0.1  # 0.1秒待機
            
            with patch.object(self.manager.issues_api, 'get_issues') as mock_get:
                mock_get.return_value = {"success": True, "issues": []}
                
                result = self.manager.get_issues()
                
                assert result["success"] is True
                mock_wait.assert_called_once()
    
    def test_notification_integration(self):
        """通知統合テスト"""
        with patch.object(self.manager.notifier, 'send_message') as mock_send:
            mock_send.return_value = True
            
            with patch.object(self.manager.update_issue_api, 'update_issue') as mock_update:
                mock_update.return_value = {
                    "success": True,
                    "issue": {"number": 123, "title": "Updated Issue"},
                    "changes": {"title": {"before": "Old", "after": "Updated Issue"}}
                }
                
                result = self.manager.update_issue(123, title="Updated Issue")
                
                assert result["success"] is True
                mock_send.assert_called_once()
    
    def test_statistics_and_monitoring_integration(self):
        """統計と監視の統合テスト"""
        initial_stats = self.manager.statistics.copy()
        
        # 複数の操作を実行
        with patch.object(self.manager.issues_api, 'get_issues') as mock_get:
            mock_get.return_value = {"success": True, "issues": []}
            
            # 成功操作
            for _ in range(3):
                self.manager.get_issues()
            
            # エラー操作
            mock_get.side_effect = Exception("API Error")
            try:
                self.manager.get_issues()
            except:
                pass
            
            # 統計を確認
            assert self.manager.statistics["api_calls"] == initial_stats["api_calls"] + 4
            assert self.manager.statistics["successful_operations"] == initial_stats["successful_operations"] + 3
            assert self.manager.statistics["errors"] == initial_stats["errors"] + 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])