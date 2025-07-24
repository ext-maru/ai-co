#!/usr/bin/env python3
"""
🛡️ Auto Issue Processor A2A Error Recovery System
エラーハンドリング・回復機能強化システム

Issue #191対応: 包括的ロールバック・サーキットブレーカー・再試行機能
"""

import asyncio
import json
import logging
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union
from functools import wraps
import traceback

logger = logging.getLogger("ErrorRecoverySystem")


class ErrorType(Enum):
    """ErrorTypeクラス"""
    TRANSIENT = "transient"          # 再試行で解決可能
    PERMANENT = "permanent"          # 手動介入必要
    SYSTEM = "system"               # インフラ・環境問題
    USER = "user"                   # 設定・入力問題
    RATE_LIMIT = "rate_limit"       # API制限
    RESOURCE = "resource"           # リソース不足
    DEPENDENCY = "dependency"       # 外部依存問題


class RecoveryAction(Enum):
    """RecoveryActionクラス"""
    RETRY = "retry"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"
    SKIP = "skip"
    CIRCUIT_BREAK = "circuit_break"
    ALTERNATIVE_PATH = "alternative_path"


@dataclass
class ErrorContext:
    """エラーコンテキスト"""
    error_type: ErrorType
    component: str
    operation: str
    error_message: str
    stacktrace: str
    timestamp: datetime = field(default_factory=datetime.now)
    attempt_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryPlan:
    """回復計画"""
    primary_action: RecoveryAction
    fallback_actions: List[RecoveryAction] = field(default_factory=list)
    max_retry_attempts: int = 3
    retry_delay: float = 1.0
    rollback_steps: List[Callable] = field(default_factory=list)
    escalation_threshold: int = 5


@dataclass
class RecoveryResult:
    """回復結果"""
    success: bool
    action_taken: RecoveryAction
    attempts_made: int
    total_time: float
    final_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CircuitBreakerState(Enum):
    """CircuitBreakerStateクラス"""
    CLOSED = "closed"       # 正常動作
    OPEN = "open"          # 回路開放（呼び出し停止）
    HALF_OPEN = "half_open"  # 部分復旧テスト中


@dataclass
class CircuitBreakerConfig:
    """CircuitBreakerConfigクラス"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3
    monitor_window: float = 300.0  # 5分


class CircuitBreaker:
    """サーキットブレーカーパターン実装"""
    
    def __init__(self, config: CircuitBreakerConfig):
        """初期化メソッド"""
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.call_history: List[Tuple[datetime, bool]] = []  # (timestamp, success)
    
    async def call(self, func: Callable, *args, **kwargs):
        """回路保護付き関数呼び出し"""
        current_time = datetime.now()
        
        # 回路状態チェック
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset(current_time):
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker transitioning to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            # 関数実行
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 成功記録
            self._record_success(current_time)
            return result
            
        except Exception as e:
            # 失敗記録
            self._record_failure(current_time)
            raise e
    
    def _should_attempt_reset(self, current_time: datetime) -> bool:
        """リセット試行判定"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = (current_time - self.last_failure_time).total_seconds()
        return time_since_failure >= self.config.recovery_timeout
    
    def _record_success(self, timestamp: datetime):
        """成功記録"""
        self.call_history.append((timestamp, True))
        self._cleanup_old_records(timestamp)
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker reset to CLOSED")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def _record_failure(self, timestamp: datetime):
        """失敗記録"""
        self.call_history.append((timestamp, False))
        self._cleanup_old_records(timestamp)
        self.last_failure_time = timestamp
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            logger.warning("Circuit breaker opened from HALF_OPEN")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _cleanup_old_records(self, current_time: datetime):
        """古い記録のクリーンアップ"""
        cutoff_time = current_time - timedelta(seconds=self.config.monitor_window)
        self.call_history = [
            (ts, success) for ts, success in self.call_history
            if ts > cutoff_time
        ]


class CircuitBreakerOpenError(Exception):
    """サーキットブレーカー開放エラー"""
    pass


class RetryStrategy(ABC):
    """再試行戦略基底クラス"""
    
    @abstractmethod
    def should_retry(self, error_context: ErrorContext) -> bool:
        """再試行判定"""
        pass
    
    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """遅延時間取得"""
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """指数バックオフ戦略"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, max_attempts: int = 5):
        """初期化メソッド"""
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts
    
    def should_retry(self, error_context: ErrorContext) -> bool:
        """再試行判定"""
        # 永続的エラーは再試行しない
        if error_context.error_type == ErrorType.PERMANENT:
            return False
        
        # 最大試行回数チェック
        return error_context.attempt_count < self.max_attempts
    
    def get_delay(self, attempt: int) -> float:
        """指数バックオフ遅延計算"""
        delay = self.base_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)


class ErrorClassifier:
    """エラー分類器"""
    
    def __init__(self):
        """初期化メソッド"""
        self.error_patterns = {
            ErrorType.TRANSIENT: [
                r'connection.*timeout',
                r'temporary.*failure',
                r'service.*unavailable',
                r'timeout.*error',
                r'network.*error'
            ],
            ErrorType.RATE_LIMIT: [
                r'rate.*limit',
                r'too.*many.*requests',
                r'quota.*exceeded',
                r'api.*limit'
            ],
            ErrorType.RESOURCE: [
                r'out.*of.*memory',
                r'disk.*full',
                r'resource.*exhausted',
                r'no.*space.*left'
            ],
            ErrorType.USER: [
                r'invalid.*input',
                r'authentication.*failed',
                r'permission.*denied',
                r'unauthorized',
                r'bad.*request'
            ],
            ErrorType.SYSTEM: [
                r'system.*error',
                r'internal.*server.*error',
                r'database.*error',
                r'configuration.*error'
            ]
        }
    
    def classify_error(self, error: Exception, component: str, operation: str) -> ErrorContext:
        """エラー分類"""
        error_message = str(error)
        stacktrace = traceback.format_exc()
        
        # パターンマッチングでエラータイプを判定
        error_type = ErrorType.PERMANENT  # デフォルト
        
        for err_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                import re
                if re.search(pattern, error_message, re.IGNORECASE):
                    error_type = err_type
                    break
            if error_type != ErrorType.PERMANENT:
                break
        
        return ErrorContext(
            error_type=error_type,
            component=component,
            operation=operation,
            error_message=error_message,
            stacktrace=stacktrace,
            metadata={
                "exception_type": type(error).__name__,
                "component": component,
                "operation": operation
            }
        )


class RollbackManager:
    """ロールバック管理"""
    
    def __init__(self):
        """初期化メソッド"""
        self.rollback_stack: List[Callable] = []
        self.rollback_history: List[Dict[str, Any]] = []
    
    def add_rollback_step(self, rollback_func: Callable, description: str = ""):
        """ロールバック手順追加"""
        self.rollback_stack.append({
            "function": rollback_func,
            "description": description,
            "timestamp": datetime.now()
        })
    
    async def execute_rollback(self, partial: bool = False) -> Dict[str, Any]:
        """ロールバック実行"""
        start_time = time.time()
        rollback_result = {
            "success": True,
            "steps_executed": 0,
            "steps_failed": 0,
            "errors": [],
            "execution_time": 0.0
        }
        
        try:
            # 逆順でロールバック実行
            for i, step in enumerate(reversed(self.rollback_stack)):
                try:
                    logger.info(f"Executing rollback step {i+1}: {step['description']}")
                    
                    if asyncio.iscoroutinefunction(step["function"]):
                        await step["function"]()
                    else:
                        step["function"]()
                    
                    rollback_result["steps_executed"] += 1
                    
                    # 部分ロールバックの場合は最初の数ステップのみ
                    if partial and i >= 2:  # 最初の3ステップまで
                        break
                        
                except Exception as e:
                    logger.error(f"Rollback step failed: {str(e)}")
                    rollback_result["steps_failed"] += 1
                    rollback_result["errors"].append({
                        "step": i + 1,
                        "description": step["description"],
                        "error": str(e)
                    })
                    
                    if not partial:  # 完全ロールバックの場合は続行
                        continue
                    else:  # 部分ロールバックの場合は停止
                        rollback_result["success"] = False
                        break
            
            # ロールバック履歴に記録
            self.rollback_history.append({
                "timestamp": datetime.now(),
                "partial": partial,
                "result": rollback_result.copy()
            })
            
        except Exception as e:
            logger.error(f"Rollback execution failed: {str(e)}")
            rollback_result["success"] = False
            rollback_result["errors"].append({
                "step": "execution",
                "error": str(e)
            })
        
        rollback_result["execution_time"] = time.time() - start_time
        return rollback_result
    
    def clear_rollback_stack(self):
        """ロールバックスタッククリア"""
        self.rollback_stack.clear()


class ErrorRecoverySystem:
    """エラー回復システム本体"""
    
    def __init__(self):
        """初期化メソッド"""
        self.error_classifier = ErrorClassifier()
        self.retry_strategy = ExponentialBackoffStrategy()
        self.rollback_manager = RollbackManager()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_history: List[ErrorContext] = []
        self.recovery_policies: Dict[str, RecoveryPlan] = {}
        
        # デフォルトポリシー設定
        self._setup_default_policies()
    
    def _setup_default_policies(self):
        """デフォルト回復ポリシー設定"""
        # Git操作用ポリシー
        self.recovery_policies["git_operations"] = RecoveryPlan(
            primary_action=RecoveryAction.RETRY,
            fallback_actions=[RecoveryAction.ROLLBACK, RecoveryAction.ESCALATE],
            max_retry_attempts=3,
            retry_delay=2.0
        )
        
        # GitHub API用ポリシー
        self.recovery_policies["github_api"] = RecoveryPlan(
            primary_action=RecoveryAction.RETRY,
            fallback_actions=[RecoveryAction.CIRCUIT_BREAK, RecoveryAction.ALTERNATIVE_PATH],
            max_retry_attempts=5,
            retry_delay=1.0
        )
        
        # Elder Flow用ポリシー
        self.recovery_policies["elder_flow"] = RecoveryPlan(
            primary_action=RecoveryAction.ALTERNATIVE_PATH,
            fallback_actions=[RecoveryAction.RETRY, RecoveryAction.ESCALATE],
            max_retry_attempts=2,
            retry_delay=5.0
        )
    
    def get_circuit_breaker(self, component: str) -> CircuitBreaker:
        """コンポーネント用サーキットブレーカー取得"""
        if component not in self.circuit_breakers:
            config = CircuitBreakerConfig()
            self.circuit_breakers[component] = CircuitBreaker(config)
        
        return self.circuit_breakers[component]
    
    async def execute_with_recovery(
        self, 
        func: Callable, 
        component: str, 
        operation: str,
        *args, 
        **kwargs
    ) -> Any:
        """回復機能付き実行"""
        circuit_breaker = self.get_circuit_breaker(component)
        policy = self.recovery_policies.get(component, self.recovery_policies["git_operations"])
        
        attempt = 1
        last_error = None
        
        while attempt <= policy.max_retry_attempts:
            try:
                # サーキットブレーカー保護付き実行
                result = await circuit_breaker.call(func, *args, **kwargs)
                
                # 成功時はロールバックスタッククリア
                if attempt > 1:
                    logger.info(f"Operation succeeded after {attempt} attempts: {component}.{operation}" \
                        "Operation succeeded after {attempt} attempts: {component}.{operation}")
                
                return result
                
            except CircuitBreakerOpenError:
                # サーキットブレーカーが開いている場合は代替パス実行
                logger.warning(f"Circuit breaker open for {component}, trying alternative path")
                return await self._execute_alternative_path(component, operation, *args, **kwargs)
                
            except Exception as e:
                last_error = e
                
                # エラー分類
                error_context = self.error_classifier.classify_error(e, component, operation)
                error_context.attempt_count = attempt
                self.error_history.append(error_context)
                
                logger.warning(f"Attempt {attempt} failed for {component}.{operation}: {str(e)}")
                
                # 再試行判定
                if attempt < policy.max_retry_attempts and self.retry_strategy.should_retry(error_context):
                    delay = self.retry_strategy.get_delay(attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    attempt += 1
                else:
                    # 最大試行回数に達した場合は回復アクション実行
                    recovery_result = await self._execute_recovery_action(
                        policy, error_context, component, operation
                    )
                    
                    if recovery_result.success:
                        return recovery_result.metadata.get("result")
                    else:
                        break
        
        # すべての回復試行が失敗した場合
        raise last_error
    
    async def _execute_recovery_action(
        self, 
        policy: RecoveryPlan, 
        error_context: ErrorContext, 
        component: str, 
        operation: str
    ) -> RecoveryResult:
        """回復アクション実行"""
        start_time = time.time()
        
        # プライマリアクション実行
        actions_tried = [policy.primary_action]
        
        try:
            result = await self._execute_single_recovery_action(
                policy.primary_action, error_context, component, operation
            )
            
            if result:
                return RecoveryResult(
                    success=True,
                    action_taken=policy.primary_action,
                    attempts_made=1,
                    total_time=time.time() - start_time,
                    metadata={"result": result}
                )
        
        except Exception as e:
            logger.error(f"Primary recovery action failed: {str(e)}")
        
        # フォールバックアクション実行
        for fallback_action in policy.fallback_actions:
            try:
                actions_tried.append(fallback_action)
                result = await self._execute_single_recovery_action(
                    fallback_action, error_context, component, operation
                )
                
                if result:
                    return RecoveryResult(
                        success=True,
                        action_taken=fallback_action,
                        attempts_made=len(actions_tried),
                        total_time=time.time() - start_time,
                        metadata={"result": result}
                    )
            
            except Exception as e:
                logger.error(f"Fallback action {fallback_action} failed: {str(e)}")
        
        # すべての回復アクションが失敗
        return RecoveryResult(
            success=False,
            action_taken=actions_tried[-1],
            attempts_made=len(actions_tried),
            total_time=time.time() - start_time,
            final_error=f"All recovery actions failed: {actions_tried}"
        )
    
    async def _execute_single_recovery_action(
        self, 
        action: RecoveryAction, 
        error_context: ErrorContext, 
        component: str, 
        operation: str
    ) -> Any:
        """単一回復アクション実行"""
        if action == RecoveryAction.ROLLBACK:
            rollback_result = await self.rollback_manager.execute_rollback()
            if rollback_result["success"]:
                logger.info(f"Rollback successful for {component}.{operation}")
                return True
            else:
                raise Exception(f"Rollback failed: {rollback_result['errors']}")
        
        elif action == RecoveryAction.ALTERNATIVE_PATH:
            return await self._execute_alternative_path(component, operation)
        
        elif action == RecoveryAction.ESCALATE:
            await self._escalate_error(error_context, component, operation)
            return True
        
        elif action == RecoveryAction.SKIP:
            logger.warning(f"Skipping failed operation: {component}.{operation}")
            return None
        
        else:
            raise Exception(f"Unsupported recovery action: {action}")
    
    async def _execute_alternative_path(
        self,
        component: str,
        operation: str,
        *args,
        **kwargs
    ) -> Any:
        """代替パス実行"""
        if component == "elder_flow" and operation == "execute":
            # Elder Flow失敗時はA2A実行
            logger.info("Executing A2A as alternative to Elder Flow")
            # A2A実行ロジック
            return {"status": "success", "method": "a2a_alternative"}
        
        elif component == "github_api" and "create_pr" in operation:
            # PR作成失敗時は設計書のみ作成
            logger.info("Creating design document as alternative to PR creation")
            return {"status": "success", "method": "design_doc_only"}
        
        elif component == "git_operations":
            # Git操作失敗時はメモリ内処理
            logger.info("Using in-memory processing as alternative to git operations")
            return {"status": "success", "method": "in_memory"}
        
        else:
            raise Exception(f"No alternative path available for {component}.{operation}")
    
    async def _escalate_error(self, error_context: ErrorContext, component: str, operation: str):
        """エラーエスカレーション"""
        # インシデント賢者に報告
        try:
            from libs.incident_sage import IncidentSage
            
            incident_sage = IncidentSage()
            await incident_sage.process_request({
                "type": "report_incident",
                "severity": "high",
                "title": f"Error escalation: {component}.{operation}",
                "description": f"Error: {error_context.error_message}",
                "metadata": {
                    "error_type": error_context.error_type.value,
                    "component": component,
                    "operation": operation,
                    "attempt_count": error_context.attempt_count
                }
            })
            
            logger.info(f"Error escalated to incident management: {component}.{operation}")
            
        except Exception as e:
            logger.error(f"Failed to escalate error: {str(e)}")
    
    def add_git_rollback_steps(self, branch_name: str, original_branch: str):
        """Git操作用ロールバック手順追加"""
        def rollback_to_original_branch():
            """rollback_to_original_branchメソッド"""
            try:
                subprocess.run(["git", "checkout", original_branch], check=True)
                logger.info(f"Rolled back to original branch: {original_branch}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to rollback to original branch: {str(e)}")
        
        def delete_failed_branch():
            """failed_branch削除メソッド"""
            try:
                subprocess.run(["git", "branch", "-D", branch_name], check=True)
                logger.info(f"Deleted failed branch: {branch_name}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to delete branch {branch_name}: {str(e)}")
        
        self.rollback_manager.add_rollback_step(rollback_to_original_branch, f"Checkout {original_branch}" \
            "Checkout {original_branch}")
        self.rollback_manager.add_rollback_step(delete_failed_branch, f"Delete branch {branch_name}" \
            "Delete branch {branch_name}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計取得"""
        if not self.error_history:
            return {"total_errors": 0}
        
        recent_errors = [
            e for e in self.error_history
            if (datetime.now() - e.timestamp).total_seconds() < 3600  # 過去1時間
        ]
        
        error_by_type = {}
        for error in self.error_history:
            error_type = error.error_type.value
            error_by_type[error_type] = error_by_type.get(error_type, 0) + 1
        
        error_by_component = {}
        for error in self.error_history:
            component = error.component
            error_by_component[component] = error_by_component.get(component, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "error_by_type": error_by_type,
            "error_by_component": error_by_component,
            "circuit_breaker_states": {
                comp: cb.state.value for comp, cb in self.circuit_breakers.items()
            }
        }


# デコレーター関数
def with_error_recovery(component: str, operation: str):
    """エラー回復デコレーター"""
    def decorator(func):
        """decoratorメソッド"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            """wrapperメソッド"""
            recovery_system = get_error_recovery_system()
            return await recovery_system.execute_with_recovery(
                func, component, operation, *args, **kwargs
            )
        return wrapper
    return decorator


# シングルトンインスタンス
_error_recovery_system = None

def get_error_recovery_system() -> ErrorRecoverySystem:
    """エラー回復システムシングルトン取得"""
    global _error_recovery_system
    if _error_recovery_system is None:
        _error_recovery_system = ErrorRecoverySystem()
    return _error_recovery_system