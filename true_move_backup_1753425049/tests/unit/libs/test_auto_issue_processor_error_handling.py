#!/usr/bin/env python3
"""
Auto Issue Processor エラーハンドリングのテスト
Issue #191対応
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from libs.auto_issue_processor_error_handling import (
    ErrorType,
    RecoveryAction,
    ErrorContext,
    RecoveryResult,
    ErrorClassifier,
    ResourceCleaner,
    CircuitBreaker,
    CircuitState,
    RetryStrategy,
    GitHubAPIRecoveryStrategy,
    GitOperationRecoveryStrategy,
    NetworkRecoveryStrategy,
    AutoIssueProcessorErrorHandler,
    with_error_recovery
)


class TestErrorClassifier:
    """エラー分類器のテスト"""
    
    def test_classify_github_api_error(self):
        """GitHub APIエラーの分類"""
        error = Exception("API rate limit exceeded")
        error_type = ErrorClassifier.classify_error(error, "github_api_call")
        assert error_type == ErrorType.GITHUB_API_ERROR
        
        error = Exception("Unauthorized: Bad credentials")
        error_type = ErrorClassifier.classify_error(error, "github_api_call")
        assert error_type == ErrorType.GITHUB_API_ERROR
    
    def test_classify_git_operation_error(self):
        """Git操作エラーの分類"""
        error = Exception("Merge conflict in file.py")
        error_type = ErrorClassifier.classify_error(error, "git_merge")
        assert error_type == ErrorType.GIT_OPERATION_ERROR
        
        error = Exception("Branch 'feature' already exists")
        error_type = ErrorClassifier.classify_error(error, "create_branch")
        assert error_type == ErrorType.GIT_OPERATION_ERROR
    
    def test_classify_network_error(self):
        """ネットワークエラーの分類"""
        error = Exception("Connection timeout")
        error_type = ErrorClassifier.classify_error(error, "api_call")
        assert error_type == ErrorType.NETWORK_ERROR
        
        error = ConnectionError("Network is unreachable")
        error_type = ErrorClassifier.classify_error(error, "api_call")
        assert error_type == ErrorType.NETWORK_ERROR
    
    def test_classify_system_resource_error(self):
        """システムリソースエラーの分類"""
        error = MemoryError("Out of memory")
        error_type = ErrorClassifier.classify_error(error, "process_data")
        assert error_type == ErrorType.SYSTEM_RESOURCE_ERROR
        
        error = PermissionError("Permission denied")
        error_type = ErrorClassifier.classify_error(error, "file_write")
        assert error_type == ErrorType.SYSTEM_RESOURCE_ERROR
    
    def test_classify_unknown_error(self):
        """不明なエラーの分類"""
        error = Exception("Something went wrong")
        error_type = ErrorClassifier.classify_error(error, "unknown_operation")
        assert error_type == ErrorType.UNKNOWN_ERROR


class TestCircuitBreaker:
    """サーキットブレーカーのテスト"""
    
    def test_initial_state(self):
        """初期状態のテスト"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True
    
    def test_open_on_threshold(self):
        """閾値到達時のOPEN状態遷移"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        # 3回失敗でOPENになる
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False
    
    def test_half_open_after_timeout(self):
        """タイムアウト後のHALF_OPEN状態遷移"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
        
        # OPENにする
        for _ in range(3):
            cb.record_failure()
        
        # タイムアウト待機
        time.sleep(0.2)
        
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_close_on_success(self):
        """成功時のCLOSED状態遷移"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
        
        # OPENにしてHALF_OPENにする
        for _ in range(3):
            cb.record_failure()
        time.sleep(0.2)
        cb.can_execute()  # HALF_OPENに遷移
        
        # 成功でCLOSEDに戻る
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestRetryStrategy:
    """リトライ戦略のテスト"""
    
    def test_get_retry_delay(self):
        """リトライ遅延の計算"""
        # GitHub APIエラーは長めの遅延
        delay = RetryStrategy.get_retry_delay(ErrorType.GITHUB_API_ERROR, 0)
        assert 60 <= delay <= 80  # ジッターを考慮
        
        # ネットワークエラーは短めの遅延
        delay = RetryStrategy.get_retry_delay(ErrorType.NETWORK_ERROR, 0)
        assert 5 <= delay <= 7
        
        # バリデーションエラーは即座にリトライ
        delay = RetryStrategy.get_retry_delay(ErrorType.VALIDATION_ERROR, 0)
        assert delay == 0
    
    def test_exponential_backoff(self):
        """指数バックオフの確認"""
        base_delay = RetryStrategy.get_retry_delay(ErrorType.NETWORK_ERROR, 0)
        second_delay = RetryStrategy.get_retry_delay(ErrorType.NETWORK_ERROR, 1)
        
        # 2回目は概ね2倍になる（ジッターを考慮）
        assert second_delay > base_delay * 1.5
    
    def test_get_max_retries(self):
        """最大リトライ回数の取得"""
        assert RetryStrategy.get_max_retries(ErrorType.GITHUB_API_ERROR) == 3
        assert RetryStrategy.get_max_retries(ErrorType.NETWORK_ERROR) == 5
        assert RetryStrategy.get_max_retries(ErrorType.VALIDATION_ERROR) == 1


@pytest.mark.asyncio
class TestResourceCleaner:
    """リソースクリーナーのテスト"""
    
    async def test_cleanup_files(self, tmp_path):
        """ファイルクリーンアップのテスト"""
        # テストファイルを作成
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        context = ErrorContext(
            error_type=ErrorType.UNKNOWN_ERROR,
            original_error=Exception("test"),
            operation="test_op",
            files_created=[str(test_file)]
        )
        
        cleaner = ResourceCleaner()
        cleaned = await cleaner.cleanup_partial_resources(context)
        
        assert not test_file.exists()
        assert f"file:{test_file}" in cleaned
    
    async def test_cleanup_branch(self):
        """ブランチクリーンアップのテスト"""
        mock_git_ops = Mock()
        mock_git_ops._run_git_command = Mock(return_value={"success": True})
        
        context = ErrorContext(
            error_type=ErrorType.GIT_OPERATION_ERROR,
            original_error=Exception("test"),
            operation="test_op",
            branch_name="test-branch"
        )
        
        cleaner = ResourceCleaner(git_ops=mock_git_ops)
        cleaned = await cleaner.cleanup_partial_resources(context)
        
        # ローカルとリモートブランチの削除が呼ばれたか確認
        assert mock_git_ops._run_git_command.call_count == 2
        assert "local_branch:test-branch" in cleaned
        assert "remote_branch:test-branch" in cleaned


@pytest.mark.asyncio
class TestRecoveryStrategies:
    """回復戦略のテスト"""
    
    async def test_github_api_rate_limit_recovery(self):
        """GitHub APIレート制限の回復戦略"""
        strategy = GitHubAPIRecoveryStrategy()
        context = ErrorContext(
            error_type=ErrorType.GITHUB_API_ERROR,
            original_error=Exception("API rate limit exceeded"),
            operation="api_call"
        )
        
        assert await strategy.can_handle(context) is True
        result = await strategy.recover(context)
        
        assert result.success is True
        assert result.action_taken == RecoveryAction.RETRY
        assert result.retry_after == 3600  # 1時間待機
    
    async def test_github_api_auth_error_recovery(self):
        """GitHub API認証エラーの回復戦略"""
        strategy = GitHubAPIRecoveryStrategy()
        context = ErrorContext(
            error_type=ErrorType.GITHUB_API_ERROR,
            original_error=Exception("Unauthorized: Bad credentials"),
            operation="api_call"
        )
        
        result = await strategy.recover(context)
        
        assert result.success is False
        assert result.action_taken == RecoveryAction.ABORT
    
    async def test_git_conflict_recovery(self):
        """Gitコンフリクトの回復戦略"""
        strategy = GitOperationRecoveryStrategy()
        context = ErrorContext(
            error_type=ErrorType.GIT_OPERATION_ERROR,
            original_error=Exception("Merge conflict in file.py"),
            operation="git_merge"
        )
        
        assert await strategy.can_handle(context) is True
        result = await strategy.recover(context)
        
        assert result.success is False
        assert result.action_taken == RecoveryAction.ROLLBACK
    
    async def test_network_error_recovery(self):
        """ネットワークエラーの回復戦略"""
        strategy = NetworkRecoveryStrategy()
        context = ErrorContext(
            error_type=ErrorType.NETWORK_ERROR,
            original_error=Exception("Connection timeout"),
            operation="api_call",
            retry_count=0
        )
        
        assert await strategy.can_handle(context) is True
        result = await strategy.recover(context)
        
        assert result.success is True
        assert result.action_taken == RecoveryAction.RETRY
        assert result.retry_after > 0


@pytest.mark.asyncio
class TestAutoIssueProcessorErrorHandler:
    """統合エラーハンドラーのテスト"""
    
    async def test_handle_github_api_error(self):
        """GitHub APIエラーの処理"""
        handler = AutoIssueProcessorErrorHandler()
        
        result = await handler.handle_error(
            error=Exception("API rate limit exceeded"),
            operation="github_api_call",
            issue_number=123,
            retry_count=0
        )
        
        assert result.action_taken == RecoveryAction.RETRY
        assert result.retry_after == 3600
    
    async def test_circuit_breaker_integration(self):
        """サーキットブレーカー統合テスト"""
        handler = AutoIssueProcessorErrorHandler()
        
        # 同じ操作で複数回失敗させる
        for i in range(5):
            result = await handler.handle_error(
                error=Exception("Network error"),
                operation="api_call",
                retry_count=10  # リトライ上限を超えている
            )
        
        # サーキットブレーカーが開く
        cb = handler.get_circuit_breaker("api_call")
        assert cb.state == CircuitState.OPEN
        
        # 次の呼び出しはブロックされる
        result = await handler.handle_error(
            error=Exception("Another error"),
            operation="api_call"
        )
        
        assert result.action_taken == RecoveryAction.CIRCUIT_BREAK
    
    async def test_resource_cleanup_on_rollback(self, tmp_path):
        """ロールバック時のリソースクリーンアップ"""
        # テストファイルを作成
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        handler = AutoIssueProcessorErrorHandler()
        
        result = await handler.handle_error(
            error=Exception("Merge conflict"),
            operation="git_merge",
            files_created=[str(test_file)]
        )
        
        assert result.action_taken == RecoveryAction.ROLLBACK
        assert f"file:{test_file}" in result.cleaned_resources
        assert not test_file.exists()


@pytest.mark.asyncio
class TestErrorRecoveryDecorator:
    """エラー回復デコレーターのテスト"""
    
    async def test_successful_execution(self):
        """正常実行時のテスト"""
        @with_error_recovery()
        async def successful_operation():
            return "success"
        
        result = await successful_operation()
        assert result == "success"
    
    async def test_retry_on_transient_error(self):
        """一時的エラーでのリトライ"""
        call_count = 0
        
        @with_error_recovery()
        async def flaky_operation():
            """flaky_operationメソッド"""
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Network timeout")
            return "success"
        
        # 3回目で成功する
        result = await flaky_operation()
        assert result == "success"
        assert call_count == 3
    
    async def test_abort_on_permanent_error(self):
        """恒久的エラーでの中止"""
        @with_error_recovery()
        async def failing_operation():
            raise Exception("Unauthorized: Bad credentials")
        
        with pytest.raises(Exception) as exc_info:
            await failing_operation()
        
        assert "Operation failed after recovery" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])