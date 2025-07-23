"""
Elder階層統合BaseWorkerクラス v1.0
Elders Guild Elder Hierarchy Integrated Worker System

エルダーズ評議会承認済み統合認証基盤
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

# 既存システムとの統合
from core.base_worker import BaseWorker
from core.security_module import SecurityModule
from libs.unified_auth_provider import (
    AuthSession,
    ElderRole,
    SageType,
    UnifiedAuthProvider,
    User,
    elder_auth_required,
    sage_auth_required,
)

# ログ設定
logger = logging.getLogger(__name__)


class WorkerExecutionMode(Enum):
    """ワーカー実行モード"""

    GRAND_ELDER = "grand_elder_mode"  # 🌟 最高権限モード
    CLAUDE_ELDER = "claude_elder_mode"  # 🤖 開発実行責任者モード
    SAGE_MODE = "sage_mode"  # 🧙‍♂️ 賢者モード
    SERVANT_MODE = "servant_mode"  # 🧝‍♂️ 基本モード
    EMERGENCY_MODE = "emergency_mode"  # 🚨 緊急時モード


class ElderTaskPriority(Enum):
    """Elder階層タスク優先度"""

    CRITICAL = "critical"  # グランドエルダー専用
    HIGH = "high"  # クロードエルダー以上
    MEDIUM = "medium"  # 賢者以上
    LOW = "low"  # サーバント可能


@dataclass
class ElderTaskContext:
    """Elder階層タスク実行コンテキスト"""

    user: User
    session: AuthSession
    task_id: str
    execution_mode: WorkerExecutionMode
    priority: ElderTaskPriority
    permissions: List[str]
    audit_enabled: bool = True
    emergency_override: bool = False


@dataclass
class ElderTaskResult:
    """Elder階層タスク実行結果"""

    task_id: str
    status: str
    result: Any
    execution_time: float
    elder_context: ElderTaskContext
    audit_log: Dict[str, Any]
    security_events: List[Dict[str, Any]]


class ElderAuditLogger:
    """Elder階層専用監査ログ"""

    def __init__(self):
        """初期化メソッド"""
        self.logger = logging.getLogger("elder_audit")
        self.events = []

    def log_elder_action(self, context: ElderTaskContext, action: str, result: Any):
        """Elder行動ログ記録"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "user_id": context.user.id,
            "username": context.user.username,
            "elder_role": context.user.elder_role.value,
            "sage_type": context.user.sage_type.value
            if context.user.sage_type
            else None,
            "task_id": context.task_id,
            "action": action,
            "execution_mode": context.execution_mode.value,
            "priority": context.priority.value,
            "result_status": str(result)[:100] if result else None,
            "emergency_override": context.emergency_override,
        }

        self.events.append(event)
        self.logger.info(
            f"Elder Action: {context.user.username} ({context.user.elder_role.value}) - {action}"
        )

    def log_security_event(
        self, context: ElderTaskContext, event_type: str, details: Dict
    ):
        """セキュリティイベントログ"""
        security_event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_context": {
                "user_id": context.user.id,
                "elder_role": context.user.elder_role.value,
                "sage_type": context.user.sage_type.value
                if context.user.sage_type
                else None,
            },
            "task_context": {
                "task_id": context.task_id,
                "execution_mode": context.execution_mode.value,
            },
            "details": details,
            "risk_level": self._calculate_risk_level(event_type, context),
        }

        self.events.append(security_event)
        self.logger.warning(
            f"Security Event: {event_type} - User: {context.user.username}"
        )

    def _calculate_risk_level(self, event_type: str, context: ElderTaskContext) -> str:
        """リスクレベル算出"""
        high_risk_events = [
            "permission_denied",
            "unauthorized_access",
            "privilege_escalation",
        ]
        if event_type in high_risk_events:
            return "high"
        elif context.execution_mode == WorkerExecutionMode.EMERGENCY_MODE:
            return "medium"
        else:
            return "low"


class ElderAuthIntegration:
    """Elder階層認証統合システム"""

    def __init__(self, auth_provider: UnifiedAuthProvider):
        """初期化メソッド"""
        self.auth_provider = auth_provider
        self.audit_logger = ElderAuditLogger()

    def validate_elder_task_execution(
        self,
        user: User,
        required_role: ElderRole,
        required_sage: Optional[SageType] = None,
    ) -> bool:
        """Elder階層タスク実行権限検証"""
        # Elder階層チェック
        if not self.auth_provider.check_elder_permission(user, required_role):
            self.audit_logger.log_security_event(
                ElderTaskContext(
                    user,
                    None,
                    "unknown",
                    WorkerExecutionMode.SERVANT_MODE,
                    ElderTaskPriority.LOW,
                    [],
                ),
                "permission_denied",
                {
                    "required_role": required_role.value,
                    "user_role": user.elder_role.value,
                },
            )
            return False

        # 賢者権限チェック（必要な場合）
        if required_sage and not self.auth_provider.check_sage_permission(
            user, required_sage
        ):
            self.audit_logger.log_security_event(
                ElderTaskContext(
                    user,
                    None,
                    "unknown",
                    WorkerExecutionMode.SAGE_MODE,
                    ElderTaskPriority.MEDIUM,
                    [],
                ),
                "sage_permission_denied",
                {
                    "required_sage": required_sage.value,
                    "user_sage": user.sage_type.value if user.sage_type else None,
                },
            )
            return False

        return True

    def determine_execution_mode(self, user: User) -> WorkerExecutionMode:
        """ユーザーに基づく実行モード決定"""
        if user.elder_role == ElderRole.GRAND_ELDER:
            return WorkerExecutionMode.GRAND_ELDER
        elif user.elder_role == ElderRole.CLAUDE_ELDER:
            return WorkerExecutionMode.CLAUDE_ELDER
        elif user.elder_role == ElderRole.SAGE:
            return WorkerExecutionMode.SAGE_MODE
        else:
            return WorkerExecutionMode.SERVANT_MODE

    def get_permitted_actions(self, user: User) -> List[str]:
        """ユーザーの許可アクション一覧取得"""
        actions = ["basic_read", "basic_write"]

        if user.elder_role == ElderRole.GRAND_ELDER:
            actions.extend(
                [
                    "system_admin",
                    "user_management",
                    "emergency_override",
                    "council_decisions",
                    "global_settings",
                ]
            )
        elif user.elder_role == ElderRole.CLAUDE_ELDER:
            actions.extend(
                [
                    "development_management",
                    "sage_coordination",
                    "system_monitoring",
                    "deployment_control",
                ]
            )
        elif user.elder_role == ElderRole.SAGE:
            if user.sage_type == SageType.KNOWLEDGE:
                actions.extend(["knowledge_management", "documentation", "learning"])
            elif user.sage_type == SageType.TASK:
                actions.extend(["task_management", "project_control", "scheduling"])
            elif user.sage_type == SageType.INCIDENT:
                actions.extend(
                    ["incident_response", "emergency_action", "security_control"]
                )
            elif user.sage_type == SageType.RAG:
                actions.extend(["information_search", "data_analysis", "research"])

        return actions


class ElderAwareBaseWorker(BaseWorker):
    """
    Elder階層統合BaseWorkerクラス

    全てのワーカーはこのクラスを継承してElder階層システムに統合される
    """

    def __init__(
        self,
        auth_provider: Optional[UnifiedAuthProvider] = None,
        required_elder_role: ElderRole = ElderRole.SERVANT,
        required_sage_type: Optional[SageType] = None,
    ):
        super().__init__()

        # Elder階層システム統合
        self.auth_provider = auth_provider or self._create_default_auth_provider()
        self.elder_integration = ElderAuthIntegration(self.auth_provider)
        self.audit_logger = ElderAuditLogger()

        # 権限要件
        self.required_elder_role = required_elder_role
        self.required_sage_type = required_sage_type

        # セキュリティ強化
        self.security_module = SecurityModule()

        logger.info(
            f"ElderAwareBaseWorker initialized - Required: {required_elder_role.value}"
        )

    def _create_default_auth_provider(self) -> UnifiedAuthProvider:
        """デフォルト認証プロバイダー作成"""
        return UnifiedAuthProvider(
            secret_key="default-elder-worker-key-2025",
            session_duration_hours=8,
            enable_mfa=True,
            enable_device_tracking=True,
        )

    @classmethod
    def with_elder_requirements(
        cls,
        elder_role: ElderRole,
        sage_type: Optional[SageType] = None,
        auth_provider: Optional[UnifiedAuthProvider] = None,
    ):
        """Elder要件指定でインスタンス作成"""
        return cls(
            auth_provider=auth_provider,
            required_elder_role=elder_role,
            required_sage_type=sage_type,
        )

    def create_elder_context(
        self,
        user: User,
        session: AuthSession,
        task_id: str,
        priority: ElderTaskPriority = ElderTaskPriority.LOW,
    ) -> ElderTaskContext:
        """Elder実行コンテキスト作成"""
        execution_mode = self.elder_integration.determine_execution_mode(user)
        permissions = self.elder_integration.get_permitted_actions(user)

        return ElderTaskContext(
            user=user,
            session=session,
            task_id=task_id,
            execution_mode=execution_mode,
            priority=priority,
            permissions=permissions,
            audit_enabled=True,
            emergency_override=False,
        )

    async def execute_with_elder_context(
        self, context: ElderTaskContext, task_func: Callable, *args, **kwargs
    ) -> ElderTaskResult:
        """Elder階層コンテキスト付きタスク実行"""
        start_time = datetime.now()

        try:
            # 権限検証
            if not self.elder_integration.validate_elder_task_execution(
                context.user, self.required_elder_role, self.required_sage_type
            ):
                raise PermissionError(
                    f"Insufficient Elder permissions: required {self.required_elder_role.value}"
                )

            # 監査ログ開始
            if context.audit_enabled:
                self.audit_logger.log_elder_action(context, "task_start", None)

            # セキュリティチェック
            await self._perform_security_checks(context)

            # タスク実行
            if context.execution_mode == WorkerExecutionMode.GRAND_ELDER:
                result = await self._execute_grand_elder_mode(
                    context, task_func, *args, **kwargs
                )
            elif context.execution_mode == WorkerExecutionMode.CLAUDE_ELDER:
                result = await self._execute_claude_elder_mode(
                    context, task_func, *args, **kwargs
                )
            elif context.execution_mode == WorkerExecutionMode.SAGE_MODE:
                result = await self._execute_sage_mode(
                    context, task_func, *args, **kwargs
                )
            else:
                result = await self._execute_servant_mode(
                    context, task_func, *args, **kwargs
                )

            # 監査ログ完了
            if context.audit_enabled:
                self.audit_logger.log_elder_action(context, "task_complete", result)

            execution_time = (datetime.now() - start_time).total_seconds()

            return ElderTaskResult(
                task_id=context.task_id,
                status="success",
                result=result,
                execution_time=execution_time,
                elder_context=context,
                audit_log={"events": self.audit_logger.events[-10:]},  # 最新10件
                security_events=[],
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            # エラー監査ログ
            if context.audit_enabled:
                self.audit_logger.log_elder_action(context, "task_error", str(e))
                self.audit_logger.log_security_event(
                    context, "task_execution_error", {"error": str(e)}
                )

            return ElderTaskResult(
                task_id=context.task_id,
                status="error",
                result=None,
                execution_time=execution_time,
                elder_context=context,
                audit_log={"events": self.audit_logger.events[-10:]},
                security_events=[{"error": str(e)}],
            )

    async def _perform_security_checks(self, context: ElderTaskContext):
        """セキュリティチェック実行"""
        # セッション有効性チェック
        if context.session:
            is_valid, _, _ = self.auth_provider.validate_token(context.session.token)
            if not is_valid:
                self.audit_logger.log_security_event(context, "invalid_session", {})
                raise SecurityError("Invalid session token")

        # 異常行動検知
        if (
            context.priority == ElderTaskPriority.CRITICAL
            and context.user.elder_role != ElderRole.GRAND_ELDER
        ):
            self.audit_logger.log_security_event(
                context,
                "privilege_escalation_attempt",
                {
                    "requested_priority": context.priority.value,
                    "user_role": context.user.elder_role.value,
                },
            )
            raise SecurityError("Privilege escalation attempt detected")

        # レート制限チェック（実装例）
        # 実際の実装では Redis 等でレート制限を管理
        pass

    async def _execute_grand_elder_mode(
        self, context: ElderTaskContext, task_func: Callable, *args, **kwargs
    ):
        """🌟 グランドエルダーモード実行"""
        logger.info(f"Executing in Grand Elder mode: {context.task_id}")

        # 最高権限での実行 - 全制限解除
        context.emergency_override = True
        return await task_func(*args, **kwargs)

    async def _execute_claude_elder_mode(
        self, context: ElderTaskContext, task_func: Callable, *args, **kwargs
    ):
        """🤖 クロードエルダーモード実行"""
        logger.info(f"Executing in Claude Elder mode: {context.task_id}")

        # 開発実行責任者権限での実行
        # 4賢者への指示、システム管理権限あり
        return await task_func(*args, **kwargs)

    async def _execute_sage_mode(
        self, context: ElderTaskContext, task_func: Callable, *args, **kwargs
    ):
        """🧙‍♂️ 賢者モード実行"""
        sage_type = (
            context.user.sage_type.value if context.user.sage_type else "unknown"
        )
        logger.info(f"Executing in Sage mode ({sage_type}): {context.task_id}")

        # 賢者専門権限での実行
        if context.user.sage_type == SageType.KNOWLEDGE:
            # ナレッジ賢者: 知識管理専門
            return await self._execute_knowledge_sage_task(task_func, *args, **kwargs)
        elif context.user.sage_type == SageType.TASK:
            # タスク賢者: プロジェクト管理専門
            return await self._execute_task_sage_task(task_func, *args, **kwargs)
        elif context.user.sage_type == SageType.INCIDENT:
            # インシデント賢者: 緊急対応専門
            return await self._execute_incident_sage_task(task_func, *args, **kwargs)
        elif context.user.sage_type == SageType.RAG:
            # RAG賢者: 情報検索専門
            return await self._execute_rag_sage_task(task_func, *args, **kwargs)
        else:
            return await task_func(*args, **kwargs)

    async def _execute_servant_mode(
        self, context: ElderTaskContext, task_func: Callable, *args, **kwargs
    ):
        """🧝‍♂️ サーバントモード実行"""
        logger.info(f"Executing in Servant mode: {context.task_id}")

        # 基本権限での実行 - セキュリティ制限あり
        # 入力検証強化、出力フィルタリング等
        filtered_kwargs = self._filter_servant_inputs(kwargs)
        result = await task_func(*args, **filtered_kwargs)
        return self._filter_servant_output(result)

    async def _execute_knowledge_sage_task(self, task_func: Callable, *args, **kwargs):
        """📚 ナレッジ賢者専用タスク実行"""
        # 知識管理特化処理
        return await task_func(*args, **kwargs)

    async def _execute_task_sage_task(self, task_func: Callable, *args, **kwargs):
        """📋 タスク賢者専用タスク実行"""
        # プロジェクト管理特化処理
        return await task_func(*args, **kwargs)

    async def _execute_incident_sage_task(self, task_func: Callable, *args, **kwargs):
        """🚨 インシデント賢者専用タスク実行"""
        # 緊急対応特化処理
        return await task_func(*args, **kwargs)

    async def _execute_rag_sage_task(self, task_func: Callable, *args, **kwargs):
        """🔍 RAG賢者専用タスク実行"""
        # 情報検索特化処理
        return await task_func(*args, **kwargs)

    def _filter_servant_inputs(self, kwargs: Dict) -> Dict:
        """サーバント入力フィルタリング"""
        # 危険なパラメータ除去
        filtered = kwargs.copy()
        dangerous_keys = ["admin", "sudo", "root", "system", "exec"]
        for key in dangerous_keys:
            if key in filtered:
                logger.warning(f"Dangerous parameter filtered for servant: {key}")
                del filtered[key]
        return filtered

    def _filter_servant_output(self, result: Any) -> Any:
        """サーバント出力フィルタリング"""
        # センシティブ情報の除去
        if isinstance(result, dict):
            filtered = result.copy()
            sensitive_keys = ["password", "secret", "key", "token"]
            for key in sensitive_keys:
                if key in filtered:
                    filtered[key] = "***FILTERED***"
            return filtered
        return result


class SecurityError(Exception):
    """セキュリティエラー"""

    pass


# Elder階層デコレーター（ワーカー専用）
def elder_worker_required(elder_role: ElderRole, sage_type: Optional[SageType] = None):
    """Elder階層ワーカー権限デコレーター"""

    def decorator(method):
        """decoratorメソッド"""
        @wraps(method)
        async def wrapper(self, context: ElderTaskContext, *args, **kwargs):
            """wrapperメソッド"""
            if not isinstance(self, ElderAwareBaseWorker):
                raise TypeError(
                    "elder_worker_required can only be used with ElderAwareBaseWorker"
                )

            # 権限チェック
            if not self.elder_integration.validate_elder_task_execution(
                context.user, elder_role, sage_type
            ):
                raise PermissionError(
                    f"Insufficient Elder permissions: required {elder_role.value}"
                )

            return await method(self, context, *args, **kwargs)

        return wrapper

    return decorator


# ファクトリー関数
def create_elder_worker(
    worker_class,
    elder_role: ElderRole,
    sage_type: Optional[SageType] = None,
    auth_provider: Optional[UnifiedAuthProvider] = None,
):
    """Elder階層ワーカー作成ファクトリー"""
    if not issubclass(worker_class, ElderAwareBaseWorker):
        raise TypeError("Worker class must inherit from ElderAwareBaseWorker")

    return worker_class.with_elder_requirements(
        elder_role=elder_role, sage_type=sage_type, auth_provider=auth_provider
    )


# デモ用テストファンクション
async def demo_elder_worker_execution():
    """Elder階層ワーカーのデモ実行"""
    from libs.unified_auth_provider import create_demo_auth_system

    # デモ認証システム
    auth = create_demo_auth_system()

    # デモワーカー作成
    worker = ElderAwareBaseWorker.with_elder_requirements(
        elder_role=ElderRole.SAGE, sage_type=SageType.KNOWLEDGE, auth_provider=auth
    )

    # デモユーザー（ナレッジ賢者）
    from libs.unified_auth_provider import AuthRequest

    auth_request = AuthRequest(username="knowledge_sage", password="knowledge_password")
    result, session, user = auth.authenticate(auth_request)

    if result.value == "success":
        # タスクコンテキスト作成
        context = worker.create_elder_context(
            user=user,
            session=session,
            task_id="demo_task_001",
            priority=ElderTaskPriority.MEDIUM,
        )

        # デモタスク実行
        async def demo_task():
            return {"message": "ナレッジ賢者によるタスク実行完了", "data": [1, 2, 3]}

        result = await worker.execute_with_elder_context(context, demo_task)
        print(f"Demo Result: {result.status} - {result.result}")
        print(f"Execution Mode: {result.elder_context.execution_mode.value}")
        print(f"Audit Events: {len(result.audit_log['events'])}")
    else:
        print(f"Authentication failed: {result}")


if __name__ == "__main__":
    # デモ実行
    asyncio.run(demo_elder_worker_execution())
