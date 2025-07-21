#!/usr/bin/env python3
"""
Auto Issue Processor エラーハンドリング・回復機能
Issue #191対応: 包括的なエラーハンドリングと回復機能の実装
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import random

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """エラータイプの分類"""
    GITHUB_API_ERROR = "github_api_error"
    GIT_OPERATION_ERROR = "git_operation_error"
    NETWORK_ERROR = "network_error"
    SYSTEM_RESOURCE_ERROR = "system_resource_error"
    TEMPLATE_ERROR = "template_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryAction(Enum):
    """回復アクション"""
    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP = "skip"
    ABORT = "abort"
    CIRCUIT_BREAK = "circuit_break"


@dataclass
class ErrorContext:
    """エラーコンテキスト"""
    error_type: ErrorType
    original_error: Exception
    operation: str
    issue_number: Optional[int] = None
    branch_name: Optional[str] = None
    files_created: List[str] = None
    timestamp: float = None
    retry_count: int = 0
    
    def __post_init__(self):
        if self.files_created is None:
            self.files_created = []
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class RecoveryResult:
    """回復処理の結果"""
    success: bool
    action_taken: RecoveryAction
    message: str
    retry_after: Optional[float] = None
    cleaned_resources: List[str] = None
    
    def __post_init__(self):
        if self.cleaned_resources is None:
            self.cleaned_resources = []


class ErrorClassifier:
    """エラー分類器"""
    
    @staticmethod
    def classify_error(error: Exception, operation: str) -> ErrorType:
        """例外をエラータイプに分類"""
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # GitHub API関連エラー
        if any(keyword in error_str for keyword in ["rate limit", "api", "github", "forbidden", "unauthorized"]):
            return ErrorType.GITHUB_API_ERROR
        
        # Git操作エラー
        if any(keyword in error_str for keyword in ["git", "branch", "merge", "conflict", "repository"]):
            return ErrorType.GIT_OPERATION_ERROR
        
        # ネットワークエラー
        if any(keyword in error_str for keyword in ["network", "connection", "timeout", "dns", "socket"]) or \
           any(err_type in error_type_name for err_type in ["connectionerror", "timeout", "urlerror"]):
            return ErrorType.NETWORK_ERROR
        
        # システムリソースエラー
        if any(keyword in error_str for keyword in ["memory", "disk", "space", "resource", "permission"]) or \
           any(err_type in error_type_name for err_type in ["memoryerror", "oserror", "permissionerror"]):
            return ErrorType.SYSTEM_RESOURCE_ERROR
        
        # テンプレートエラー
        if any(keyword in error_str for keyword in ["template", "jinja", "render"]):
            return ErrorType.TEMPLATE_ERROR
        
        # バリデーションエラー
        if any(keyword in error_str for keyword in ["validation", "invalid", "missing"]) or \
           any(err_type in error_type_name for err_type in ["valueerror", "typeerror", "keyerror"]):
            return ErrorType.VALIDATION_ERROR
        
        # タイムアウトエラー
        if "timeout" in error_str or "timeouterror" in error_type_name:
            return ErrorType.TIMEOUT_ERROR
        
        return ErrorType.UNKNOWN_ERROR


class ResourceCleaner:
    """リソースクリーンアップ"""
    
    def __init__(self, git_ops=None):
        self.git_ops = git_ops
        
    async def cleanup_partial_resources(self, context: ErrorContext) -> List[str]:
        """部分的に作成されたリソースをクリーンアップ"""
        cleaned = []
        
        try:
            # 作成されたファイルを削除
            for file_path in context.files_created:
                try:
                    import os
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        cleaned.append(f"file:{file_path}")
                        logger.info(f"Cleaned up file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup file {file_path}: {e}")
            
            # ブランチのクリーンアップ
            if context.branch_name and self.git_ops:
                try:
                    # ローカルブランチを削除
                    result = self.git_ops._run_git_command(["branch", "-D", context.branch_name], check=False)
                    if result["success"]:
                        cleaned.append(f"local_branch:{context.branch_name}")
                        logger.info(f"Cleaned up local branch: {context.branch_name}")
                    
                    # リモートブランチを削除
                    result = self.git_ops._run_git_command(
                        ["push", "origin", "--delete", context.branch_name], 
                        check=False
                    )
                    if result["success"]:
                        cleaned.append(f"remote_branch:{context.branch_name}")
                        logger.info(f"Cleaned up remote branch: {context.branch_name}")
                        
                except Exception as e:
                    logger.warning(f"Failed to cleanup branch {context.branch_name}: {e}")
            
            # ディレクトリのクリーンアップ
            cleanup_dirs = ["auto_implementations", "auto_fixes"]
            for dir_name in cleanup_dirs:
                try:
                    import shutil
                    if os.path.exists(dir_name) and context.issue_number:
                        # 当該Issueに関連するファイルのみ削除
                        for file in os.listdir(dir_name):
                            if str(context.issue_number) in file:
                                file_path = os.path.join(dir_name, file)
                                os.remove(file_path)
                                cleaned.append(f"cleanup_file:{file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup directory {dir_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Critical error during cleanup: {e}")
        
        return cleaned


class CircuitBreaker:
    """サーキットブレーカーパターン実装"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def can_execute(self) -> bool:
        """実行可能かチェック"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False
    
    def record_success(self):
        """成功を記録"""
        self.failure_count = 0
        self.state = "CLOSED"
        
    def record_failure(self):
        """失敗を記録"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class RetryStrategy:
    """リトライ戦略"""
    
    @staticmethod
    def get_retry_delay(error_type: ErrorType, retry_count: int) -> float:
        """エラータイプに応じたリトライ間隔を計算"""
        base_delays = {
            ErrorType.GITHUB_API_ERROR: 60,  # レート制限対応
            ErrorType.NETWORK_ERROR: 5,
            ErrorType.GIT_OPERATION_ERROR: 2,
            ErrorType.SYSTEM_RESOURCE_ERROR: 10,
            ErrorType.TEMPLATE_ERROR: 1,
            ErrorType.VALIDATION_ERROR: 0,  # 即座にリトライ（データ修正後）
            ErrorType.TIMEOUT_ERROR: 30,
            ErrorType.UNKNOWN_ERROR: 5,
        }
        
        base_delay = base_delays.get(error_type, 5)
        
        # 指数バックオフ + ジッター
        exponential_delay = base_delay * (2 ** min(retry_count, 6))
        jitter = random.uniform(0.1, 0.3) * exponential_delay
        
        return exponential_delay + jitter
    
    @staticmethod
    def get_max_retries(error_type: ErrorType) -> int:
        """エラータイプに応じた最大リトライ回数"""
        max_retries = {
            ErrorType.GITHUB_API_ERROR: 3,
            ErrorType.NETWORK_ERROR: 5,
            ErrorType.GIT_OPERATION_ERROR: 3,
            ErrorType.SYSTEM_RESOURCE_ERROR: 2,
            ErrorType.TEMPLATE_ERROR: 5,
            ErrorType.VALIDATION_ERROR: 1,
            ErrorType.TIMEOUT_ERROR: 2,
            ErrorType.UNKNOWN_ERROR: 2,
        }
        
        return max_retries.get(error_type, 2)


class RecoveryStrategy(ABC):
    """回復戦略の基底クラス"""
    
    @abstractmethod
    async def can_handle(self, context: ErrorContext) -> bool:
        """このエラーを処理できるかチェック"""
        pass
    
    @abstractmethod
    async def recover(self, context: ErrorContext) -> RecoveryResult:
        """回復処理を実行"""
        pass


class GitHubAPIRecoveryStrategy(RecoveryStrategy):
    """GitHub API エラー回復戦略"""
    
    async def can_handle(self, context: ErrorContext) -> bool:
        return context.error_type == ErrorType.GITHUB_API_ERROR
    
    async def recover(self, context: ErrorContext) -> RecoveryResult:
        error_str = str(context.original_error).lower()
        
        # レート制限エラー
        if "rate limit" in error_str:
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.RETRY,
                message="Rate limit detected, waiting before retry",
                retry_after=3600  # 1時間待機
            )
        
        # 認証エラー
        if any(keyword in error_str for keyword in ["unauthorized", "forbidden", "token"]):
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.ABORT,
                message="Authentication failed, check GitHub token"
            )
        
        # その他のAPIエラー
        if context.retry_count < RetryStrategy.get_max_retries(context.error_type):
            delay = RetryStrategy.get_retry_delay(context.error_type, context.retry_count)
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.RETRY,
                message=f"GitHub API error, retrying after {delay}s",
                retry_after=delay
            )
        
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.ABORT,
            message="Max retries exceeded for GitHub API error"
        )


class GitOperationRecoveryStrategy(RecoveryStrategy):
    """Git操作エラー回復戦略"""
    
    def __init__(self, git_ops=None):
        self.git_ops = git_ops
    
    async def can_handle(self, context: ErrorContext) -> bool:
        return context.error_type == ErrorType.GIT_OPERATION_ERROR
    
    async def recover(self, context: ErrorContext) -> RecoveryResult:
        error_str = str(context.original_error).lower()
        
        # マージコンフリクト
        if "conflict" in error_str:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.ROLLBACK,
                message="Merge conflict detected, rolling back changes"
            )
        
        # ブランチが既に存在
        if "already exists" in error_str and "branch" in error_str:
            # 既存ブランチを削除してリトライ
            if self.git_ops and context.branch_name:
                try:
                    self.git_ops._run_git_command(["branch", "-D", context.branch_name], check=False)
                    self.git_ops._run_git_command(["push", "origin", "--delete", context.branch_name], check=False)
                    
                    return RecoveryResult(
                        success=True,
                        action_taken=RecoveryAction.RETRY,
                        message="Deleted existing branch, retrying",
                        cleaned_resources=[f"branch:{context.branch_name}"]
                    )
                except Exception as e:
                    logger.warning(f"Failed to delete existing branch: {e}")
        
        # unstaged changes エラー
        if "unstaged changes" in error_str:
            if self.git_ops:
                try:
                    # 変更をstash
                    stash_result = self.git_ops.stash_changes()
                    if stash_result["success"]:
                        return RecoveryResult(
                            success=True,
                            action_taken=RecoveryAction.RETRY,
                            message="Stashed unstaged changes, retrying"
                        )
                except Exception as e:
                    logger.warning(f"Failed to stash changes: {e}")
        
        # 一般的なGitエラーのリトライ
        if context.retry_count < RetryStrategy.get_max_retries(context.error_type):
            delay = RetryStrategy.get_retry_delay(context.error_type, context.retry_count)
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.RETRY,
                message=f"Git operation failed, retrying after {delay}s",
                retry_after=delay
            )
        
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.ROLLBACK,
            message="Git operation failed, rolling back"
        )


class NetworkRecoveryStrategy(RecoveryStrategy):
    """ネットワークエラー回復戦略"""
    
    async def can_handle(self, context: ErrorContext) -> bool:
        return context.error_type == ErrorType.NETWORK_ERROR
    
    async def recover(self, context: ErrorContext) -> RecoveryResult:
        if context.retry_count < RetryStrategy.get_max_retries(context.error_type):
            delay = RetryStrategy.get_retry_delay(context.error_type, context.retry_count)
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.RETRY,
                message=f"Network error, retrying after {delay}s",
                retry_after=delay
            )
        
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.CIRCUIT_BREAK,
            message="Network issues persist, activating circuit breaker"
        )


class AutoIssueProcessorErrorHandler:
    """Auto Issue Processor 統合エラーハンドラー"""
    
    def __init__(self, git_ops=None):
        self.git_ops = git_ops
        self.resource_cleaner = ResourceCleaner(git_ops)
        self.circuit_breakers = {}  # operation -> CircuitBreaker
        
        # 回復戦略を登録
        self.recovery_strategies = [
            GitHubAPIRecoveryStrategy(),
            GitOperationRecoveryStrategy(git_ops),
            NetworkRecoveryStrategy()
        ]
    
    def get_circuit_breaker(self, operation: str) -> CircuitBreaker:
        """操作に対応するサーキットブレーカーを取得"""
        if operation not in self.circuit_breakers:
            self.circuit_breakers[operation] = CircuitBreaker()
        return self.circuit_breakers[operation]
    
    async def handle_error(
        self, 
        error: Exception, 
        operation: str,
        issue_number: Optional[int] = None,
        branch_name: Optional[str] = None,
        files_created: List[str] = None,
        retry_count: int = 0
    ) -> RecoveryResult:
        """エラーを処理して回復戦略を実行"""
        
        # エラーを分類
        error_type = ErrorClassifier.classify_error(error, operation)
        
        # エラーコンテキストを作成
        context = ErrorContext(
            error_type=error_type,
            original_error=error,
            operation=operation,
            issue_number=issue_number,
            branch_name=branch_name,
            files_created=files_created or [],
            retry_count=retry_count
        )
        
        logger.error(f"Error in {operation}: {error_type.value} - {str(error)}")
        
        # サーキットブレーカーチェック
        circuit_breaker = self.get_circuit_breaker(operation)
        if not circuit_breaker.can_execute():
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.CIRCUIT_BREAK,
                message=f"Circuit breaker is open for {operation}"
            )
        
        # 適切な回復戦略を選択して実行
        for strategy in self.recovery_strategies:
            if await strategy.can_handle(context):
                try:
                    result = await strategy.recover(context)
                    
                    # サーキットブレーカーの状態更新
                    if result.success:
                        circuit_breaker.record_success()
                    else:
                        circuit_breaker.record_failure()
                    
                    # ロールバックが必要な場合
                    if result.action_taken == RecoveryAction.ROLLBACK:
                        cleaned = await self.resource_cleaner.cleanup_partial_resources(context)
                        result.cleaned_resources.extend(cleaned)
                    
                    return result
                    
                except Exception as recovery_error:
                    logger.error(f"Recovery strategy failed: {recovery_error}")
                    circuit_breaker.record_failure()
        
        # 適切な戦略が見つからない場合のデフォルト処理
        circuit_breaker.record_failure()
        cleaned = await self.resource_cleaner.cleanup_partial_resources(context)
        
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.ROLLBACK,
            message=f"No recovery strategy available for {error_type.value}",
            cleaned_resources=cleaned
        )


# デコレーター関数
def with_error_recovery(git_ops=None):
    """エラー回復機能付きデコレーター"""
    error_handler = AutoIssueProcessorErrorHandler(git_ops)
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            operation = f"{func.__name__}"
            retry_count = 0
            max_retries = 3
            
            while retry_count <= max_retries:
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    # 回復処理を実行
                    recovery_result = await error_handler.handle_error(
                        error=e,
                        operation=operation,
                        retry_count=retry_count
                    )
                    
                    if recovery_result.success and recovery_result.action_taken == RecoveryAction.RETRY:
                        retry_count += 1
                        if recovery_result.retry_after:
                            await asyncio.sleep(recovery_result.retry_after)
                        logger.info(f"Retrying {operation} (attempt {retry_count}/{max_retries})")
                        continue
                    else:
                        # 回復不可能または中止
                        logger.error(f"Operation {operation} failed: {recovery_result.message}")
                        raise Exception(f"Operation failed after recovery: {recovery_result.message}")
            
            raise Exception(f"Operation {operation} failed after {max_retries} retries")
        
        return wrapper
    return decorator