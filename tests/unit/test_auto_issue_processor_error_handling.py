#!/usr/bin/env python3
"""
Auto Issue Processor エラーハンドリング強化のテスト
Issue #191対応: 包括的なエラーハンドリングと回復機能の実装
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import time

# テスト対象モジュールをインポート
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from libs.auto_issue_processor_error_handling import (
    ErrorType, ErrorContext, ErrorClassifier, RecoveryAction, RecoveryResult,
    CircuitBreaker, RetryStrategy, ResourceCleaner, AutoIssueProcessorErrorHandler,
    GitHubAPIRecoveryStrategy, GitOperationRecoveryStrategy, NetworkRecoveryStrategy,
    with_error_recovery, CircuitBreakerError, CircuitBreakerOpenError
)


class TestErrorClassifier:
    """エラー分類器のテスト"""
    
    def test_classify_github_api_errors(self):
        """GitHub APIエラーの分類テスト"""
        errors = [
            Exception("Rate limit exceeded"),
            Exception("API rate limit"),
            Exception("GitHub API forbidden"),
            Exception("Unauthorized access to GitHub"),
        ]
        
        for error in errors:
            assert ErrorClassifier.classify_error(error, "test") == ErrorType.GITHUB_API_ERROR
    
    def test_classify_git_operation_errors(self):
        """Git操作エラーの分類テスト"""
        errors = [
            Exception("Merge conflict detected"),
            Exception("Branch already exists"),
            Exception("Repository not found"),
            Exception("Git push failed"),
        ]
        
        for error in errors:
            assert ErrorClassifier.classify_error(error, "test") == ErrorType.GIT_OPERATION_ERROR
    
    def test_classify_network_errors(self):
        """ネットワークエラーの分類テスト"""
        errors = [
            Exception("Network connection failed"),
            Exception("Connection timeout"),
            Exception("DNS resolution failed"),
            Exception("Socket error"),
            TimeoutError("Request timeout"),
        ]
        
        for error in errors:
            assert ErrorClassifier.classify_error(error, "test") == ErrorType.NETWORK_ERROR
    
    def test_classify_system_resource_errors(self):
        """システムリソースエラーの分類テスト"""
        errors = [
            MemoryError("Out of memory"),
            Exception("Disk space full"),
            PermissionError("Permission denied"),
            Exception("Resource exhausted"),
        ]
        
        for error in errors:
            assert ErrorClassifier.classify_error(error, "test") == ErrorType.SYSTEM_RESOURCE_ERROR


class TestCircuitBreaker:
    """サーキットブレーカーのテスト"""
    
    def test_initial_state_is_closed(self):
        """初期状態はCLOSEDであること"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        assert cb.can_execute() is True
        assert cb.state.value == "closed"
    
    def test_circuit_opens_after_threshold(self):
        """失敗閾値を超えるとOPENになること"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        # 3回失敗を記録
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state.value == "open"
        assert cb.can_execute() is False
    
    def test_circuit_half_open_after_timeout(self):
        """タイムアウト後にHALF_OPENになること"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
        
        # Circuit を開く
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state.value == "open"
        
        # タイムアウトを待つ
        time.sleep(0.2)
        
        assert cb.can_execute() is True
        assert cb.state.value == "half_open"
    
    def test_circuit_closes_on_success(self):
        """成功でCLOSEDに戻ること"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
        
        # Circuit を開く
        for _ in range(3):
            cb.record_failure()
        
        # タイムアウトを待ってHALF_OPENにする
        time.sleep(0.2)
        
        # stateプロパティにアクセスしてHALF_OPENに遷移
        assert cb.state.value == "half_open"
        
        # 成功を記録
        cb.record_success()
        
        assert cb.state.value == "closed"
        assert cb.failure_count == 0


class TestRetryStrategy:
    """リトライ戦略のテスト"""
    
    def test_get_retry_delay_for_github_api_error(self):
        """GitHub APIエラーのリトライ遅延計算"""
        delay = RetryStrategy.get_retry_delay(ErrorType.GITHUB_API_ERROR, 0)
        # ベース遅延60秒 + ジッター
        assert 60 <= delay <= 78  # 60 + 0.3 * 60
    
    def test_get_retry_delay_exponential_backoff(self):
        """指数バックオフの動作確認"""
        delays = []
        for i in range(3):
            delay = RetryStrategy.get_retry_delay(ErrorType.NETWORK_ERROR, i)
            delays.append(delay)
        
        # 各遅延が前回よりも長いこと
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]
    
    def test_get_max_retries(self):
        """エラータイプ別の最大リトライ回数"""
        assert RetryStrategy.get_max_retries(ErrorType.GITHUB_API_ERROR) == 3
        assert RetryStrategy.get_max_retries(ErrorType.NETWORK_ERROR) == 5
        assert RetryStrategy.get_max_retries(ErrorType.VALIDATION_ERROR) == 1


class TestResourceCleaner:
    """リソースクリーナーのテスト"""
    
    @pytest.mark.asyncio
    async def test_cleanup_files(self, tmp_path):
        """ファイルクリーンアップのテスト"""
        cleaner = ResourceCleaner()
        
        # テストファイルを作成
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        context = ErrorContext(
            error_type=ErrorType.UNKNOWN_ERROR,
            original_error=Exception("test"),
            operation="test",
            files_created=[str(test_file)]
        )
        
        cleaned = await cleaner.cleanup_partial_resources(context)
        
        assert len(cleaned) == 1
        assert "file:" in cleaned[0]
        assert not test_file.exists()
    
    @pytest.mark.asyncio
    async def test_cleanup_with_git_ops(self):
        """Git操作を含むクリーンアップのテスト"""
        mock_git_ops = Mock()
        mock_git_ops._run_git_command = Mock(return_value={"success": True})
        
        cleaner = ResourceCleaner(git_ops=mock_git_ops)
        
        context = ErrorContext(
            error_type=ErrorType.GIT_OPERATION_ERROR,
            original_error=Exception("test"),
            operation="test",
            branch_name="test-branch"
        )
        
        cleaned = await cleaner.cleanup_partial_resources(context)
        
        # ローカルとリモートブランチの削除が呼ばれたこと
        assert mock_git_ops._run_git_command.call_count == 2
        assert len(cleaned) == 2


class TestRecoveryStrategies:
    """回復戦略のテスト"""
    
    @pytest.mark.asyncio
    async def test_github_api_recovery_rate_limit(self):
        """GitHub APIレート制限エラーの回復戦略"""
        strategy = GitHubAPIRecoveryStrategy()
        
        context = ErrorContext(
            error_type=ErrorType.GITHUB_API_ERROR,
            original_error=Exception("Rate limit exceeded"),
            operation="test"
        )
        
        assert await strategy.can_handle(context) is True
        
        result = await strategy.recover(context)
        assert result.success is True
        assert result.action_taken == RecoveryAction.RETRY
        assert result.retry_after == 3600  # 1時間
    
    @pytest.mark.asyncio
    async def test_github_api_recovery_auth_error(self):
        """GitHub API認証エラーの回復戦略"""
        strategy = GitHubAPIRecoveryStrategy()
        
        context = ErrorContext(
            error_type=ErrorType.GITHUB_API_ERROR,
            original_error=Exception("Unauthorized"),
            operation="test"
        )
        
        result = await strategy.recover(context)
        assert result.success is False
        assert result.action_taken == RecoveryAction.ABORT
    
    @pytest.mark.asyncio
    async def test_git_operation_recovery_conflict(self):
        """Gitコンフリクトエラーの回復戦略"""
        strategy = GitOperationRecoveryStrategy()
        
        context = ErrorContext(
            error_type=ErrorType.GIT_OPERATION_ERROR,
            original_error=Exception("Merge conflict"),
            operation="test"
        )
        
        result = await strategy.recover(context)
        assert result.success is False
        assert result.action_taken == RecoveryAction.ROLLBACK
    
    @pytest.mark.asyncio
    async def test_network_recovery_retry(self):
        """ネットワークエラーのリトライ戦略"""
        strategy = NetworkRecoveryStrategy()
        
        context = ErrorContext(
            error_type=ErrorType.NETWORK_ERROR,
            original_error=Exception("Connection timeout"),
            operation="test",
            retry_count=0
        )
        
        result = await strategy.recover(context)
        assert result.success is True
        assert result.action_taken == RecoveryAction.RETRY
        assert result.retry_after > 0


class TestAutoIssueProcessorErrorHandler:
    """統合エラーハンドラーのテスト"""
    
    @pytest.mark.asyncio
    async def test_handle_error_with_circuit_breaker(self):
        """サーキットブレーカーを使用したエラーハンドリング"""
        handler = AutoIssueProcessorErrorHandler()
        
        # サーキットブレーカーを開く
        cb = handler.get_circuit_breaker("test_operation")
        for _ in range(5):
            cb.record_failure()
        
        result = await handler.handle_error(
            Exception("test error"),
            "test_operation"
        )
        
        assert result.success is False
        assert result.action_taken == RecoveryAction.CIRCUIT_BREAK
    
    @pytest.mark.asyncio
    async def test_handle_error_with_recovery(self):
        """回復戦略を使用したエラーハンドリング"""
        handler = AutoIssueProcessorErrorHandler()
        
        result = await handler.handle_error(
            Exception("Network connection failed"),
            "test_operation",
            retry_count=0
        )
        
        assert result.action_taken == RecoveryAction.RETRY
        assert result.retry_after > 0
    
    @pytest.mark.asyncio
    async def test_handle_error_with_rollback(self):
        """ロールバックを伴うエラーハンドリング"""
        mock_git_ops = Mock()
        mock_git_ops._run_git_command = Mock(return_value={"success": True})
        
        handler = AutoIssueProcessorErrorHandler(git_ops=mock_git_ops)
        
        result = await handler.handle_error(
            Exception("Merge conflict detected"),
            "test_operation",
            branch_name="test-branch"
        )
        
        assert result.action_taken == RecoveryAction.ROLLBACK
        assert len(result.cleaned_resources) > 0


class TestErrorRecoveryDecorator:
    """エラー回復デコレーターのテスト"""
    
    @pytest.mark.asyncio
    async def test_decorator_successful_execution(self):
        """正常実行時のデコレーター動作"""
        
        @with_error_recovery()
        async def successful_function():
            return "success"
        
        result = await successful_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_decorator_with_retry(self):
        """リトライを伴うデコレーター動作"""
        call_count = 0
        
        @with_error_recovery()
        async def failing_then_succeeding_function():
            """failing_then_succeeding_functionメソッド"""
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Network connection failed")
            return "success"
        
        # モックを使って遅延をスキップ
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await failing_then_succeeding_function()
            assert result == "success"
            assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_decorator_max_retries_exceeded(self):
        """最大リトライ回数超過時のデコレーター動作"""
        
        @with_error_recovery()
        async def always_failing_function():
            raise Exception("Permanent failure")
        
        with pytest.raises(Exception) as exc_info:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await always_failing_function()
        
        assert "Operation failed after recovery" in str(exc_info.value)