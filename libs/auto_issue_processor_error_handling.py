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
from typing import Any, Dict, List, Optional, Callable, TypeVar, ParamSpec, Tuple
import random
from functools import wraps
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import uuid
import traceback

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


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


class ErrorCategory(Enum):
    """エラーカテゴリー"""
    GITHUB_API = "github_api"
    GIT = "git"
    NETWORK = "network"
    SYSTEM = "system"
    VALIDATION = "validation"
    TEMPLATE = "template"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """エラー重要度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecoveryAction(Enum):
    """回復アクション"""
    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP = "skip"
    ABORT = "abort"
    CIRCUIT_BREAK = "circuit_break"


class CircuitState(Enum):
    """サーキットブレーカーの状態"""
    CLOSED = "closed"     # 正常状態（通過可能）
    OPEN = "open"         # 障害状態（通過不可）
    HALF_OPEN = "half_open"  # 回復試行状態


class CircuitBreakerError(Exception):
    """サーキットブレーカー関連のエラー"""
    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """サーキットが開いているときのエラー"""
    pass


@dataclass
class ErrorReport:
    """エラーレポート"""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    operation: str
    issue_number: Optional[int] = None
    branch_name: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_action: Optional[str] = None
    recovery_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_category": self.error_category.value,
            "severity": self.severity.value,
            "operation": self.operation,
            "issue_number": self.issue_number,
            "branch_name": self.branch_name,
            "stack_trace": self.stack_trace,
            "context": self.context,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "recovery_action": self.recovery_action,
            "recovery_time": self.recovery_time
        }


@dataclass
class ErrorPattern:
    """エラーパターン"""
    error_type: str
    error_category: ErrorCategory
    count: int
    first_occurrence: datetime
    last_occurrence: datetime
    operations: List[str]
    recovery_success_rate: float


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
        """__post_init__特殊メソッド"""
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
        """__post_init__特殊メソッド"""
        if self.cleaned_resources is None:
            self.cleaned_resources = []


class ErrorClassifier:
    """エラー分類器"""
    
    # エラー分類規則の定数定義（複雑度削減）
    CLASSIFICATION_RULES = {
        ErrorType.GITHUB_API_ERROR: {
            'error_keywords': ["rate limit", "api", "github", "forbidden", "unauthorized"],
            'type_keywords': []
        },
        ErrorType.GIT_OPERATION_ERROR: {
            'error_keywords': ["git", "branch", "merge", "conflict", "repository"],
            'type_keywords': []
        },
        ErrorType.NETWORK_ERROR: {
            'error_keywords': ["network", "connection", "timeout", "dns", "socket"],
            'type_keywords': ["connectionerror", "timeout", "urlerror"]
        },
        ErrorType.SYSTEM_RESOURCE_ERROR: {
            'error_keywords': ["memory", "disk", "space", "resource", "permission"],
            'type_keywords': ["memoryerror", "oserror", "permissionerror"]
        },
        ErrorType.TEMPLATE_ERROR: {
            'error_keywords': ["template", "jinja", "render"],
            'type_keywords': []
        },
        ErrorType.VALIDATION_ERROR: {
            'error_keywords': ["validation", "invalid", "missing"],
            'type_keywords': ["valueerror", "typeerror", "keyerror"]
        },
        ErrorType.TIMEOUT_ERROR: {
            'error_keywords': ["timeout"],
            'type_keywords': ["timeouterror"]
        }
    }
    
    @staticmethod
    def classify_error(error: Exception, operation: str) -> ErrorType:
        """例外をエラータイプに分類"""
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # 規則ベースの分類
        for error_type, rules in ErrorClassifier.CLASSIFICATION_RULES.items():
            if ErrorClassifier._matches_rules(error_str, error_type_name, rules):
                return error_type
        
        return ErrorType.UNKNOWN_ERROR
    
    @staticmethod
    def _matches_rules(error_str: str, error_type_name: str, rules: Dict[str, List[str]]) -> bool:
        """分類規則にマッチするかチェック"""
        error_match = any(keyword in error_str for keyword in rules['error_keywords'])
        type_match = any(keyword in error_type_name for keyword in rules['type_keywords'])
        return error_match or type_match


class ResourceCleaner:
    """リソースクリーンアップ"""
    
    def __init__(self, git_ops=None):
        """初期化メソッド"""
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
                    result = self.git_ops._run_git_command(
                        ["branch",
                        "-D",
                        context.branch_name],
                        check=False
                    )
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
    
    def __init__(
        self, 
        failure_threshold: int = 5, 
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
        exclude_exceptions: Optional[List[type[Exception]]] = None
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.exclude_exceptions = exclude_exceptions or []
        
        # 状態管理
        self._state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        
        # メトリクス
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        
        # コールバック
        self.on_success: Optional[Callable[[Any], None]] = None
        self.on_failure: Optional[Callable[[Exception], None]] = None
    
    @property
    def state(self) -> CircuitState:
        """現在の状態を取得（HALF_OPEN遷移を含む）"""
        if self._state == CircuitState.OPEN:
            if self.last_failure_time and \
               time.time() - self.last_failure_time > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state
        
    def can_execute(self) -> bool:
        """実行可能かチェック"""
        return self.state != CircuitState.OPEN
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """関数を実行（サーキットブレーカー経由）"""
        self.total_calls += 1
        
        # Circuit is open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker is open. Last failure: {self.last_failure_time}"
            )
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Record success
            self.record_success()
            
            # Call success callback
            if self.on_success:
                self.on_success(result)
            
            return result
            
        except Exception as e:
            # Check if this exception should be ignored
            if any(isinstance(e, exc_type) for exc_type in self.exclude_exceptions):
                raise
            
            # Record failure
            self.record_failure()
            
            # Call failure callback
            if self.on_failure:
                self.on_failure(e)
            
            raise
    
    def record_success(self):
        """成功を記録"""
        self.successful_calls += 1
        if self._state == CircuitState.HALF_OPEN:
            # Half-open状態での成功はCircuitを閉じる
            self.failure_count = 0
            self._state = CircuitState.CLOSED
            logger.info("Circuit breaker closed after successful call")
        else:
            self.failure_count = 0
        
    def record_failure(self):
        """失敗を記録"""
        self.failed_calls += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            # Half-open状態での失敗は即座にOpenに戻る
            self._state = CircuitState.OPEN
            logger.warning("Circuit breaker reopened after failure in half-open state")
        elif self.failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_metrics(self) -> Dict[str, Any]:
        """メトリクスを取得"""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.successful_calls / self.total_calls if self.total_calls > 0 else 0,
            "current_state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time
        }
    
    def decorator(self, func: Callable[..., T]) -> Callable[..., T]:
        """デコレーターとして使用"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            """async_wrapperメソッド"""
            return await self.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            """sync_wrapperメソッド"""
            return asyncio.run(self.call(func, *args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


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
    
    async def can_handle(self, context:
        """handle可能性判定メソッド"""
    ErrorContext) -> bool:
        return context.error_type == ErrorType.GITHUB_API_ERROR
    
    async def recover(self, context:
        """recoverメソッド"""
    ErrorContext) -> RecoveryResult:
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
        """初期化メソッド"""
        self.git_ops = git_ops
    
    async def can_handle(self, context:
        """handle可能性判定メソッド"""
    ErrorContext) -> bool:
        return context.error_type == ErrorType.GIT_OPERATION_ERROR
    
    async def recover(self, context:
        """recoverメソッド"""
    ErrorContext) -> RecoveryResult:
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
                    self.git_ops._run_git_command(
                        ["branch",
                        "-D",
                        context.branch_name],
                        check=False
                    )
                    self.git_ops._run_git_command(
                        ["push",
                        "origin",
                        "--delete",
                        context.branch_name],
                        check=False
                    )
                    
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
    
    async def can_handle(self, context:
        """handle可能性判定メソッド"""
    ErrorContext) -> bool:
        return context.error_type == ErrorType.NETWORK_ERROR
    
    async def recover(self, context:
        """recoverメソッド"""
    ErrorContext) -> RecoveryResult:
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
        """初期化メソッド"""
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
        """decoratorメソッド"""
        async def wrapper(*args, **kwargs):
            """wrapperメソッド"""
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
                        raise Exception(f"Operation failed after recovery: {recovery_result.message}" \
                            "Operation failed after recovery: {recovery_result.message}")
            
            raise Exception(f"Operation {operation} failed after {max_retries} retries")
        
        return wrapper
    return decorator


class ErrorReporter:
    """エラーレポート機能"""
    
    def __init__(self, report_dir:
        """初期化メソッド"""
    str = "/tmp/error_reports"):
        self.report_dir = report_dir
        self.error_history: List[ErrorReport] = []
        
        # レポートディレクトリ作成
        os.makedirs(report_dir, exist_ok=True)
    
    def generate_error_id(self) -> str:
        """ユニークなエラーIDを生成"""
        return f"ERR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
    
    def classify_error(
        self,
        error: Exception,
        operation: str
    ) -> Tuple[ErrorCategory, ErrorSeverity]:
        """エラーを分類して重要度を判定"""
        # ErrorClassifierを使用して分類
        error_type = ErrorClassifier.classify_error(error, operation)
        
        # ErrorType から ErrorCategory への変換
        type_to_category_map = {
            ErrorType.GITHUB_API_ERROR: ErrorCategory.GITHUB_API,
            ErrorType.GIT_OPERATION_ERROR: ErrorCategory.GIT,
            ErrorType.NETWORK_ERROR: ErrorCategory.NETWORK,
            ErrorType.SYSTEM_RESOURCE_ERROR: ErrorCategory.SYSTEM,
            ErrorType.VALIDATION_ERROR: ErrorCategory.VALIDATION,
            ErrorType.TEMPLATE_ERROR: ErrorCategory.TEMPLATE,
            ErrorType.TIMEOUT_ERROR: ErrorCategory.NETWORK,
            ErrorType.UNKNOWN_ERROR: ErrorCategory.UNKNOWN
        }
        
        category = type_to_category_map.get(error_type, ErrorCategory.UNKNOWN)
        severity = self._determine_severity(error, category)
        
        return category, severity
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """エラーの重要度を判定"""
        error_str = str(error).lower()
        
        # 重要度判定ルール
        if category == ErrorCategory.SYSTEM:
            return ErrorSeverity.CRITICAL
        elif category == ErrorCategory.GITHUB_API and "rate limit" in error_str:
            return ErrorSeverity.HIGH
        elif "timeout" in error_str:
            return ErrorSeverity.HIGH
        elif category == ErrorCategory.VALIDATION:
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.MEDIUM
    
    async def create_report(
        self,
        error: Exception,
        operation: str,
        issue_number: Optional[int] = None,
        branch_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_attempted: bool = False,
        recovery_successful: bool = False,
        recovery_action: Optional[str] = None,
        recovery_time: Optional[float] = None
    ) -> ErrorReport:
        """エラーレポートを作成"""
        error_category, severity = self.classify_error(error, operation)
        
        report = ErrorReport(
            error_id=self.generate_error_id(),
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            error_category=error_category,
            severity=severity,
            operation=operation,
            issue_number=issue_number,
            branch_name=branch_name,
            stack_trace=traceback.format_exc(),
            context=context,
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful,
            recovery_action=recovery_action,
            recovery_time=recovery_time
        )
        
        self.error_history.append(report)
        return report
    
    async def save_report(self, report: ErrorReport) -> str:
        """エラーレポートをファイルに保存"""
        report_file = os.path.join(self.report_dir, f"{report.error_id}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Error report saved: {report_file}")
        return report_file
    
    async def get_error_patterns(self, min_occurrence: int = 2) -> List[ErrorPattern]:
        """エラーパターンを分析"""
        error_groups = defaultdict(list)
        
        # エラータイプごとにグループ化
        for report in self.error_history:
            key = f"{report.error_type}_{report.error_category.value}"
            error_groups[key].append(report)
        
        patterns = []
        for key, reports in error_groups.items():
            if len(reports) >= min_occurrence:
                error_type = reports[0].error_type
                error_category = reports[0].error_category
                
                operations = list(set(r.operation for r in reports))
                recovery_successful = sum(1 for r in reports if r.recovery_successful)
                recovery_rate = recovery_successful / len(reports) if reports else 0
                
                pattern = ErrorPattern(
                    error_type=error_type,
                    error_category=error_category,
                    count=len(reports),
                    first_occurrence=min(r.timestamp for r in reports),
                    last_occurrence=max(r.timestamp for r in reports),
                    operations=operations,
                    recovery_success_rate=recovery_rate
                )
                patterns.append(pattern)
        
        return sorted(patterns, key=lambda p: p.count, reverse=True)
    
    async def get_error_trends(self, hours: int = 24) -> Dict[str, Any]:
        """エラートレンドを分析"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [r for r in self.error_history if r.timestamp >= cutoff_time]
        
        if not recent_errors:
            return {"total_errors": 0, "errors_by_category": {}, "errors_by_severity": {}}
        
        category_counts = Counter(r.error_category.value for r in recent_errors)
        severity_counts = Counter(r.severity.value for r in recent_errors)
        
        return {
            "total_errors": len(recent_errors),
            "errors_by_category": dict(category_counts),
            "errors_by_severity": dict(severity_counts),
            "error_rate_per_hour": len(recent_errors) / hours,
            "most_common_error": recent_errors[0].error_type if recent_errors else None
        }
    
    async def generate_summary_report(self) -> Dict[str, Any]:
        """サマリーレポートを生成"""
        if not self.error_history:
            return {"total_errors": 0, "message": "No errors recorded"}
        
        error_types = Counter(r.error_type for r in self.error_history)
        categories = Counter(r.error_category.value for r in self.error_history)
        severities = Counter(r.severity.value for r in self.error_history)
        
        recovery_attempts = sum(1 for r in self.error_history if r.recovery_attempted)
        recovery_successes = sum(1 for r in self.error_history if r.recovery_successful)
        recovery_rate = recovery_successes / recovery_attempts if recovery_attempts > 0 else 0
        
        # 推奨事項
        recommendations = []
        if categories.get("github_api", 0) > 5:
            recommendations.append("Consider implementing more aggressive GitHub API rate limiting")
        if severities.get("critical", 0) > 0:
            recommendations.append("Address critical system errors immediately")
        if recovery_rate < 0.5:
            recommendations.append("Improve error recovery strategies")
        
        return {
            "total_errors": len(self.error_history),
            "unique_error_types": len(error_types),
            "most_common_errors": dict(error_types.most_common(5)),
            "errors_by_category": dict(categories),
            "errors_by_severity": dict(severities),
            "recovery_success_rate": recovery_rate,
            "top_errors": [
                {"type": error_type, "count": count}
                for error_type, count in error_types.most_common(10)
            ],
            "recommendations": recommendations
        }


class ErrorAnalytics:
    """エラー分析機能"""
    
    def __init__(self):
        """初期化メソッド"""
        self.error_data: List[Dict[str, Any]] = []
        self.recovery_data: List[Dict[str, Any]] = []
    
    async def add_error(self, error_type: str, timestamp: datetime, operation: str):
        """エラーデータを追加"""
        self.error_data.append({
            "error_type": error_type,
            "timestamp": timestamp,
            "operation": operation
        })
    
    async def record_recovery(self, error_id: str, recovery_time: float):
        """回復時間を記録"""
        self.recovery_data.append({
            "error_id": error_id,
            "recovery_time": recovery_time,
            "timestamp": datetime.now()
        })
    
    async def calculate_mttr(self) -> float:
        """Mean Time To Recovery を計算"""
        if not self.recovery_data:
            return 0.0
        
        recovery_times = [r["recovery_time"] for r in self.recovery_data]
        return sum(recovery_times) / len(recovery_times)
    
    async def identify_error_clusters(
        self, 
        time_window_minutes: int = 5, 
        min_cluster_size: int = 3
    ) -> List[Dict[str, Any]]:
        """エラークラスターを特定"""
        if len(self.error_data) < min_cluster_size:
            return []
        
        # 時系列でソート
        sorted_errors = sorted(self.error_data, key=lambda x: x["timestamp"])
        clusters = []
        
        current_cluster = [sorted_errors[0]]
        
        for error in sorted_errors[1:]:
            time_diff = (error["timestamp"] - current_cluster[-1]["timestamp"]).total_seconds() / 60
            
            if time_diff <= time_window_minutes:
                current_cluster.append(error)
            else:
                if len(current_cluster) >= min_cluster_size:
                    clusters.append({
                        "start_time": current_cluster[0]["timestamp"],
                        "end_time": current_cluster[-1]["timestamp"],
                        "error_count": len(current_cluster),
                        "error_types": list(set(e["error_type"] for e in current_cluster)),
                        "operations": list(set(e["operation"] for e in current_cluster))
                    })
                current_cluster = [error]
        
        # 最後のクラスターをチェック
        if len(current_cluster) >= min_cluster_size:
            clusters.append({
                "start_time": current_cluster[0]["timestamp"],
                "end_time": current_cluster[-1]["timestamp"],
                "error_count": len(current_cluster),
                "error_types": list(set(e["error_type"] for e in current_cluster)),
                "operations": list(set(e["operation"] for e in current_cluster))
            })
        
        return clusters
    
    async def predict_error_likelihood(self, operation: str, error_type: str) -> float:
        """エラー発生確率を予測"""
        operation_errors = [e for e in self.error_data if e["operation"] == operation]
        
        if not operation_errors:
            return 0.0
        
        specific_errors = [e for e in operation_errors if e["error_type"] == error_type]
        return len(specific_errors) / len(operation_errors)
    
    async def get_error_correlations(self, min_correlation: float = 0.3) -> List[Dict[str, Any]]:
        """エラー間の相関関係を分析"""
        if len(self.error_data) < 10:
            return []
        
        # エラータイプのペアを作成
        error_types = list(set(e["error_type"] for e in self.error_data))
        correlations = []
        
        for i, type1 in enumerate(error_types):
            for type2 in error_types[i+1:]:
                # 同じ操作で発生する頻度を計算
                type1_operations = set(e["operation"] for e in self.error_data if e["error_type"] == type1)
                type2_operations = set(e["operation"] for e in self.error_data if e["error_type"] == type2)
                
                common_operations = type1_operations.intersection(type2_operations)
                total_operations = type1_operations.union(type2_operations)
                
                if total_operations:
                    correlation = len(common_operations) / len(total_operations)
                    
                    if correlation >= min_correlation:
                        correlations.append({
                            "error_type_1": type1,
                            "error_type_2": type2,
                            "correlation_score": correlation,
                            "common_operations": list(common_operations)
                        })
        
        return sorted(correlations, key=lambda x: x["correlation_score"], reverse=True)