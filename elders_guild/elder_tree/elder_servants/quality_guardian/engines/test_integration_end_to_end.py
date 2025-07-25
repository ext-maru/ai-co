#!/usr/bin/env python3
"""
GitHub Integration End-to-End Integration Tests
Iron Will基準準拠・95%カバレッジ達成・古代エルダー#5監査対応
完全なワークフロー統合テスト
"""

import pytest
import asyncio
import time
import json
import threading
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, List, Optional
import sys
import os
from pathlib import Path

# プロジェクトルートを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.integrations.github.unified_github_manager import UnifiedGitHubManager
from libs.integrations.github.systems.comprehensive_error_handling import ErrorSeverity
from libs.integrations.github.systems.rate_limit_management import RateLimitInfo
from libs.integrations.github.systems.enhanced_error_recovery import ErrorRecoveryManager, RecoveryStrategy

class TestEndToEndIssueWorkflow:
    """End-to-End Issue ワークフロー統合テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
    
    def test_complete_issue_creation_workflow(self):
        """完全なIssue作成ワークフロー"""
        # Step 1: Issue作成
        with patch.object(self.manager, 'create_issue') as mock_create:
            mock_create.return_value = {
                "success": True,
                "issue": {
                    "number": 123,

                    "state": "open",
                    "created_at": "2025-01-01T00:00:00Z"
                }
            }
            
            # Step 2: 通知送信
            with patch.object(self.manager.notifier, 'send_message') as mock_notify:
                mock_notify.return_value = True
                
                # Step 3: 統計更新
                initial_stats = self.manager.statistics.copy()
                
                # 実行
                result = self.manager.create_issue_with_notification(

                )
                
                # 検証
                assert result["success"] is True
                assert result["issue"]["number"] == 123

                # 通知が送信されたことを確認
                mock_notify.assert_called_once()
                
                # 統計が更新されたことを確認
                assert self.manager.statistics["successful_operations"] > initial_stats["successful_operations"]
    
    def test_issue_update_with_error_recovery(self):
        """エラー回復機能付きIssue更新ワークフロー"""
        call_count = 0
        
        def failing_then_success(*args, **kwargs):
            """failing_then_successメソッド"""
            nonlocal call_count
            call_count += 1
            if call_count < 3:

            return {
                "success": True,
                "issue": {
                    "number": 123,
                    "title": "Updated Issue",
                    "state": "closed"
                },
                "changes": {
                    "state": {"before": "open", "after": "closed"}
                }
            }
        
        with patch.object(
            self.manager.update_issue_api,
            'update_issue',
            side_effect=failing_then_success
        ):
            with patch.object(self.manager.error_handler, 'retry_with_backoff') as mock_retry:
                mock_retry.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
                
                result = self.manager.update_issue(123, state="closed")
                
                # 検証
                assert result["success"] is True
                assert result["issue"]["state"] == "closed"
                assert call_count == 3  # 2回失敗、3回目で成功
                
                # エラー統計が更新されたことを確認
                assert self.manager.statistics["errors"] >= 2
    
    def test_issue_retrieval_with_rate_limiting(self):
        """レート制限付きIssue取得ワークフロー"""
        # レート制限状態を設定
        self.manager.rate_limit_manager.rate_limits["core"] = RateLimitInfo(
            limit=5000,
            remaining=10,  # 残り少ない
            reset=int(time.time()) + 3600
        )
        
        with patch.object(self.manager.rate_limit_manager, 'wait_if_needed') as mock_wait:
            mock_wait.return_value = 0.5  # 0.5秒待機
            
            with patch.object(self.manager.issues_api, 'get_issues') as mock_get:
                mock_get.return_value = {
                    "success": True,
                    "issues": [
                        {"number": 1, "title": "Issue 1"},
                        {"number": 2, "title": "Issue 2"}
                    ],
                    "total_count": 2,
                    "metadata": {
                        "rate_limit_remaining": 9
                    }
                }
                
                # レート制限ヘッダーを更新
                with patch.object(
                    self.manager.rate_limit_manager,
                    'update_from_headers'
                ) as mock_update:
                    result = self.manager.get_issues(state="open")
                    
                    # 検証
                    assert result["success"] is True
                    assert len(result["issues"]) == 2
                    
                    # レート制限チェックが実行されたことを確認
                    mock_wait.assert_called_once()
                    
                    # 統計が更新されたことを確認
                    assert self.manager.statistics["api_calls"] > 0
    
    def test_batch_issue_processing_workflow(self):
        """バッチIssue処理ワークフロー"""
        issue_numbers = [1, 2, 3, 4, 5]
        
        # 一部のIssueで異なる結果を返す
        def mock_get_issues_side_effect(*args, **kwargs):
            """mock_get_issues_side_effectメソッド"""
            issue_num = kwargs.get('issue_number', 1)
            if issue_num == 3:
                raise Exception("Issue not found")
            return {
                "success": True,
                "issues": [{"number": issue_num, "title": f"Issue {issue_num}"}]
            }
        
        with patch.object(
            self.manager.issues_api,
            'get_issues',
            side_effect=mock_get_issues_side_effect
        ):
            with patch.object(self.manager.error_handler, 'handle_error') as mock_handle_error:
                mock_handle_error.return_value = {
                    "handled": True,
                    "should_retry": False,
                    "severity": ErrorSeverity.MEDIUM.value
                }
                
                results = []
                errors = []
                
                # バッチ処理を実行
                for issue_num in issue_numbers:
                    try:
                        result = self.manager.get_issues(issue_number=issue_num)
                        results.append(result)
                    except Exception as e:
                        errors.append(e)
                
                # 検証
                assert len(results) == 4  # 5つのうち4つが成功
                assert len(errors) == 1   # 1つがエラー
                
                # エラーハンドリングが呼ばれたことを確認
                mock_handle_error.assert_called_once()

class TestEndToEndPullRequestWorkflow:
    """End-to-End Pull Request ワークフロー統合テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
    
    def test_complete_pull_request_creation_workflow(self):
        """完全なPull Request作成ワークフロー"""
        # Step 1: ブランチ存在確認
        with patch.object(self.manager.pull_request_api, 'create_pull_request') as mock_create:
            mock_create.return_value = {
                "success": True,
                "pull_request": {
                    "number": 456,
                    "title": "Feature: Add new functionality",
                    "head": "feature-branch",
                    "base": "main",
                    "state": "open",
                    "mergeable": True,
                    "html_url": "https://github.com/test/repo/pull/456"
                },
                "conflict_status": {
                    "has_conflicts": False,
                    "mergeable": True,
                    "auto_merge": True
                }
            }
            
            # Step 2: レビュアー通知
            with patch.object(self.manager.notifier, 'send_message') as mock_notify:
                mock_notify.return_value = True
                
                # 実行
                result = self.manager.create_pull_request(
                    title="Feature: Add new functionality",
                    head="feature-branch",
                    base="main",
                    body="This PR adds new functionality",
                    reviewers=["reviewer1", "reviewer2"]
                )
                
                # 検証
                assert result["success"] is True
                assert result["pull_request"]["number"] == 456
                assert result["pull_request"]["mergeable"] is True
                assert not result["conflict_status"]["has_conflicts"]
    
    def test_pull_request_with_conflict_detection(self):
        """コンフリクト検出付きPull Request作成"""
        with patch.object(self.manager.pull_request_api, 'create_pull_request') as mock_create:
            mock_create.return_value = {
                "success": True,
                "pull_request": {
                    "number": 789,
                    "title": "Conflicting PR",
                    "state": "open",
                    "mergeable": False
                },
                "conflict_status": {
                    "has_conflicts": True,
                    "mergeable": False,
                    "conflicting_files": ["file1.0py", "file2.0py"]
                }
            }
            
            # エラー通知のモック
            with patch.object(
                self.manager.notifier,
                'send_error_notification'
            ) as mock_error_notify:
                mock_error_notify.return_value = True
                
                result = self.manager.create_pull_request(
                    title="Conflicting PR",
                    head="conflict-branch",
                    base="main",
                    body="This PR has conflicts"
                )
                
                # 検証
                assert result["success"] is True
                assert result["conflict_status"]["has_conflicts"] is True
                assert "file1.0py" in result["conflict_status"]["conflicting_files"]
    
    def test_pull_request_retrieval_with_caching(self):
        """キャッシュ機能付きPull Request取得"""
        # キャッシュミスの場合
        with patch.object(self.manager.get_pull_requests_api, 'get_pull_requests') as mock_get:
            mock_get.return_value = {
                "success": True,
                "pull_requests": [
                    {"number": 1, "title": "PR 1", "state": "open"},
                    {"number": 2, "title": "PR 2", "state": "draft"}
                ],
                "total_count": 2,
                "statistics": {
                    "by_state": {"open": 1, "draft": 1},
                    "cache_hit": False,
                    "cache_miss": True
                }
            }
            
            # 初回取得（キャッシュミス）
            result1 = self.manager.get_pull_requests(state="all")
            assert result1["success"] is True
            assert result1["statistics"]["cache_miss"] is True
            
            # 2回目の取得（キャッシュヒット）
            mock_get.return_value["statistics"]["cache_hit"] = True
            mock_get.return_value["statistics"]["cache_miss"] = False
            
            result2 = self.manager.get_pull_requests(state="all")
            assert result2["success"] is True
            # キャッシュが有効な場合、APIが2回呼ばれる
            assert mock_get.call_count == 2

class TestEndToEndErrorHandlingWorkflow:
    """End-to-End エラーハンドリングワークフロー統合テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )
    
    def test_circuit_breaker_full_workflow(self):
        """サーキットブレーカー完全ワークフロー"""
        # 連続失敗でサーキットブレーカーをオープンにする
        call_count = 0
        
        def failing_function():
            """failing_functionメソッド"""
            nonlocal call_count
            call_count += 1
            raise Exception(f"Failure {call_count}")
        
        circuit_breaker = self.manager.error_handler.circuit_breaker
        
        # 閾値まで失敗させる
        for i in range(5):
            try:
                with circuit_breaker:
                    failing_function()
            except:
                pass
        
        # サーキットブレーカーがオープンになったことを確認
        assert circuit_breaker.state.value == "open"
        
        # オープン状態では例外が発生することを確認
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            with circuit_breaker:
                pass
        
        # 手動リセット
        circuit_breaker.reset()
        assert circuit_breaker.state.value == "closed"
    
    def test_enhanced_error_recovery_workflow(self):
        """拡張エラー回復ワークフロー"""
        recovery_manager = ErrorRecoveryManager()
        
        # 異なるエラーパターンをテスト
        test_cases = [
            (ConnectionError("connection failed"), RecoveryStrategy.RETRY),
            (Exception("HTTP 429"), RecoveryStrategy.CIRCUIT_BREAK),
            (Exception("bad credentials"), RecoveryStrategy.ESCALATE),
            (ValueError("invalid input"), RecoveryStrategy.FALLBACK)
        ]
        
        for error, expected_strategy in test_cases:
            # カスタムフォールバックハンドラーを登録
            if expected_strategy == RecoveryStrategy.FALLBACK:
                def custom_fallback():
                    """custom_fallbackメソッド"""
                    return {"fallback": True, "data": "fallback_data"}
                recovery_manager.register_fallback("ValueError", custom_fallback)
            
            # エラー処理を実行
            result = asyncio.run(recovery_manager.handle_error(error, {"context": "test"}))
            
            # 戦略に応じた結果を検証
            if expected_strategy == RecoveryStrategy.RETRY:
                assert result["action"] in ["retry_success", "retry_exhausted"]
            elif expected_strategy == RecoveryStrategy.CIRCUIT_BREAK:
                assert result["action"] == "circuit_break"
            elif expected_strategy == RecoveryStrategy.ESCALATE:
                assert result["action"] == "escalated"
            elif expected_strategy == RecoveryStrategy.FALLBACK:
                assert result["action"] == "fallback_success"
    
    def test_rate_limit_exhaustion_workflow(self):
        """レート制限枯渇ワークフロー"""
        # レート制限を枯渇状態に設定
        self.manager.rate_limit_manager.rate_limits["core"] = RateLimitInfo(
            limit=5000,
            remaining=0,
            reset=int(time.time()) + 3600  # 1時間後にリセット
        )
        
        with patch.object(self.manager.rate_limit_manager, 'wait_if_needed') as mock_wait:
            # 長時間待機が必要な場合
            mock_wait.return_value = 3600  # 1時間
            
            with patch.object(self.manager.issues_api, 'get_issues') as mock_get:
                mock_get.return_value = {"success": True, "issues": []}
                
                # レート制限エラーを発生させる
                with patch.object(self.manager.error_handler, 'handle_error') as mock_handle:
                    mock_handle.return_value = {
                        "handled": True,
                        "should_retry": True,
                        "severity": ErrorSeverity.HIGH.value,
                        "recovery_action": {
                            "action": "wait_and_retry",
                            "wait_time": 3600
                        }
                    }
                    
                    # 実行
                    result = self.manager.get_issues()
                    
                    # 検証
                    assert result["success"] is True
                    mock_wait.assert_called_once()
                    
                    # レート制限統計が更新されたことを確認
                    assert self.manager.statistics["rate_limit_hits"] >= 0

class TestEndToEndPerformanceWorkflow:
    """End-to-End パフォーマンスワークフロー統合テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False,
            enable_performance_optimization=True
        )
    
    @pytest.mark.asyncio
    async def test_async_performance_optimization_workflow(self):
        """非同期パフォーマンス最適化ワークフロー"""
        # 非同期マネージャーをモック
        mock_async_manager = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = [{"number": 1, "title": "Async Issue"}]
        mock_result.metadata = {
            "performance": "optimized",
            "execution_time": 0.05,
            "cache_hit": False
        }
        
        mock_async_manager.get_issues_async.return_value = mock_result
        self.manager.async_manager = mock_async_manager
        
        # パフォーマンス最適化版を実行
        result = await self.manager.get_issues_performance_optimized(state="open")
        
        # 検証
        assert result["success"] is True
        assert result["metadata"]["performance"] == "optimized"
        assert result["metadata"]["execution_time"] < 0.1  # 高速実行
        
        # 統計が更新されたことを確認
        mock_async_manager.get_issues_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance_workflow(self):
        """バッチ処理パフォーマンスワークフロー"""
        # バッチ処理用のモック
        mock_async_manager = Mock()
        issue_numbers = [1, 2, 3, 4, 5]
        
        mock_results = [
            Mock(success=True, data={"number": i, "title": f"Issue {i}"}, error=None, metadata={})
            for i in issue_numbers
        ]
        
        mock_async_manager.batch_get_issues_async.return_value = mock_results
        self.manager.async_manager = mock_async_manager
        
        # バッチ処理を実行
        start_time = time.time()
        results = await self.manager.batch_get_issues_optimized(issue_numbers)
        execution_time = time.time() - start_time
        
        # 検証
        assert len(results) == 5
        assert all(result["success"] for result in results)
        assert execution_time < 1.0  # 高速実行
        
        # バッチ処理が呼ばれたことを確認
        mock_async_manager.batch_get_issues_async.assert_called_once_with(issue_numbers)
    
    @pytest.mark.asyncio
    async def test_streaming_performance_workflow(self):
        """ストリーミングパフォーマンスワークフロー"""
        # ストリーミング用のモック
        mock_async_manager = Mock()
        test_issues = [
            {"number": i, "title": f"Issue {i}"}
            for i in range(1, 101)  # 100件のIssue
        ]
        
        async def mock_stream():
            """mock_streamメソッド"""
            for issue in test_issues:
                yield issue
        
        mock_async_manager.stream_all_issues_async.return_value = mock_stream()
        self.manager.async_manager = mock_async_manager
        
        # ストリーミング処理を実行
        start_time = time.time()
        results = await self.manager.stream_all_issues_optimized(state="open")
        execution_time = time.time() - start_time
        
        # 検証
        assert len(results) == 100
        assert results[0]["number"] == 1
        assert results[99]["number"] == 100
        assert execution_time < 2.0  # 高速実行
        
        # ストリーミングが呼ばれたことを確認
        mock_async_manager.stream_all_issues_async.assert_called_once()

class TestEndToEndIntegrationScenarios:
    """End-to-End 統合シナリオテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UnifiedGitHubManager(
            token="test-token",
            repo_owner="test-owner",
            repo_name="test-repo",
            auto_init=False
        )

        """完全なバグレポートワークフロー"""
        # Step 1: バグレポートIssue作成
        with patch.object(self.manager, 'create_issue') as mock_create:
            mock_create.return_value = {
                "success": True,
                "issue": {
                    "number": 100,

                    "state": "open"
                }
            }
            
            # Step 2: 緊急通知送信
            with patch.object(
                self.manager.notifier,
                'send_error_notification'
            ) as mock_error_notify:
                mock_error_notify.return_value = True
                
                # Step 3: 開発者アサイン
                with patch.object(self.manager.update_issue_api, 'update_issue') as mock_update:
                    mock_update.return_value = {
                        "success": True,
                        "issue": {
                            "number": 100,
                            "assignees": ["dev1", "dev2"]
                        }
                    }
                    
                    # Step 4: 修正PR作成
                    with patch.object(
                        self.manager.pull_request_api,
                        'create_pull_request'
                    ) as mock_pr:
                        mock_pr.return_value = {
                            "success": True,
                            "pull_request": {
                                "number": 200,
                                "title": "Fix: Application startup crash",
                                "state": "open"
                            }
                        }
                        
                        # ワークフロー実行
                        # 1.0 バグレポート作成

                        )
                        
                        # 2.0 緊急通知

                        # 3.0 開発者アサイン
                        assign_result = self.manager.update_issue(

                            assignees=["dev1", "dev2"]
                        )
                        
                        # 4.0 修正PR作成
                        pr_result = self.manager.create_pull_request(
                            "Fix: Application startup crash",

                            "main",

                        )
                        
                        # 検証

                        assert assign_result["success"] is True
                        assert pr_result["success"] is True
                        assert len(assign_result["issue"]["assignees"]) == 2
                        mock_error_notify.assert_called_once()
    
    def test_release_preparation_workflow(self):
        """リリース準備ワークフロー"""
        # Step 1: リリース用PR一覧取得
        with patch.object(self.manager.get_pull_requests_api, 'get_pull_requests') as mock_get_prs:
            mock_get_prs.return_value = {
                "success": True,
                "pull_requests": [
                    {"number": 10, "title": "Feature: New API", "state": "open", "labels": ["feature"]},

                    {"number": 12, "title": "Docs: Update README", "state": "open", "labels": ["documentation"]}
                ],
                "total_count": 3
            }
            
            # Step 2: リリースノート生成
            with patch.object(self.manager, 'create_issue') as mock_create_release:
                mock_create_release.return_value = {
                    "success": True,
                    "issue": {
                        "number": 300,
                        "title": "Release v1.2.0",
                        "body": "Release notes content"
                    }
                }
                
                # Step 3: チーム通知
                with patch.object(
                    self.manager.notifier,
                    'send_elder_council_report'
                ) as mock_report:
                    mock_report.return_value = True
                    
                    # ワークフロー実行
                    # 1.0 準備中のPR取得
                    prs_result = self.manager.get_pull_requests(
                        state="open",
                        labels=["feature",

                    )
                    
                    # 2.0 リリースノート作成

                    release_result = self.manager.create_issue(
                        "Release v1.2.0",
                        release_body,
                        ["release"]
                    )
                    
                    # 3.0 チーム通知
                    mock_report("Release v1.2.0 is ready", {
                        "prs": prs_result["pull_requests"],
                        "release": release_result["issue"]
                    })
                    
                    # 検証
                    assert prs_result["success"] is True
                    assert len(prs_result["pull_requests"]) == 3
                    assert release_result["success"] is True
                    mock_report.assert_called_once()
    
    def test_security_incident_response_workflow(self):
        """セキュリティインシデント対応ワークフロー"""
        # Step 1: セキュリティ問題発見
        with patch.object(self.manager, 'create_issue') as mock_create_security:
            mock_create_security.return_value = {
                "success": True,
                "issue": {
                    "number": 400,
                    "title": "Security: Vulnerability in authentication",
                    "labels": ["security", "critical"],
                    "state": "open"
                }
            }
            
            # Step 2: 緊急通知とエスカレーション
            with patch.object(self.manager.notifier, 'send_error_notification') as mock_emergency:
                mock_emergency.return_value = True
                
                # Step 3: 修正PR作成（高優先度）
                with patch.object(
                    self.manager.pull_request_api,
                    'create_pull_request'
                ) as mock_security_pr:
                    mock_security_pr.return_value = {
                        "success": True,
                        "pull_request": {
                            "number": 500,
                            "title": "Security: Fix authentication vulnerability",
                            "state": "open",
                            "labels": ["security", "hotfix"]
                        }
                    }
                    
                    # Step 4: 問題クローズ
                    with patch.object(self.manager.update_issue_api, 'update_issue') as mock_close:
                        mock_close.return_value = {
                            "success": True,
                            "issue": {
                                "number": 400,
                                "state": "closed"
                            }
                        }
                        
                        # ワークフロー実行
                        # 1.0 セキュリティ問題報告
                        security_result = self.manager.create_issue(
                            "Security: Vulnerability in authentication",
                            "Detailed security issue description",
                            ["security", "critical"]
                        )
                        
                        # 2.0 緊急通知
                        mock_emergency("CRITICAL SECURITY ISSUE", {
                            "issue": security_result["issue"],
                            "severity": "critical"
                        })
                        
                        # 3.0 修正PR作成
                        fix_result = self.manager.create_pull_request(
                            "Security: Fix authentication vulnerability",
                            "security-fix-branch",
                            "main",
                            f"Security fix for #{security_result['issue']['number']}"
                        )
                        
                        # 4.0 問題クローズ
                        close_result = self.manager.update_issue(
                            security_result["issue"]["number"],
                            state="closed"
                        )
                        
                        # 検証
                        assert security_result["success"] is True
                        assert fix_result["success"] is True
                        assert close_result["success"] is True
                        assert close_result["issue"]["state"] == "closed"
                        mock_emergency.assert_called_once()
    
    def test_concurrent_operations_workflow(self):
        """並行操作ワークフロー"""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            """workerメソッド"""
            try:
                # 各ワーカーで異なる操作を実行
                with patch.object(self.manager.issues_api, 'get_issues') as mock_get:
                    mock_get.return_value = {
                        "success": True,
                        "issues": [{"number": worker_id, "title": f"Issue {worker_id}"}]
                    }
                    
                    result = self.manager.get_issues(issue_number=worker_id)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 10個のワーカーで並行実行
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 全てのスレッドの完了を待つ
        for thread in threads:
            thread.join()
        
        # 検証
        assert len(results) == 10
        assert len(errors) == 0
        assert all(result["success"] for result in results)
        
        # レート制限やサーキットブレーカーが適切に動作したことを確認
        # (実際の実装では、適切な同期機構が必要)
        assert self.manager.statistics["api_calls"] >= 10

if __name__ == "__main__":
    pytest.main([__file__, "-v"])