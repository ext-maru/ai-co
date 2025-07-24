#!/usr/bin/env python3
"""
PROJECT ELDERZAN SecurityLayer - RBAC Manager
プロジェクトエルダーザン セキュリティレイヤー - RBAC管理

Role-Based Access Control システム
4賢者システム統合・階層的権限管理
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class RoleLevel(Enum):
    """ロールレベル"""

    GUEST = 0
    USER = 40
    CLAUDE_AGENT = 60
    SAGE_SYSTEM = 80
    ELDER_COUNCIL = 100


class PermissionScope(Enum):
    """権限スコープ"""

    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"
    RESOURCE = "resource"


class ResourceType(Enum):
    """リソースタイプ"""

    SESSION = "session"
    STORAGE = "storage"
    KNOWLEDGE = "knowledge"
    TASK = "task"
    INCIDENT = "incident"
    RAG = "rag"
    SYSTEM = "system"


@dataclass
class Permission:
    """権限定義"""

    name: str
    description: str
    scope: PermissionScope
    resource_type: ResourceType
    actions: List[str]
    conditions: Optional[Dict[str, Any]] = None

    def matches(self, action: str, resource: str) -> bool:
        """権限マッチング"""
        return action in self.actions or "*" in self.actions


@dataclass
class Role:
    """ロール定義"""

    name: str
    level: RoleLevel
    permissions: List[Permission]
    restrictions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission_name: str) -> boolreturn any(p.name == permission_name for p in self.permissions)
    """権限チェック"""


@dataclass:
class UserRole:
    """ユーザーロール"""

    user_id: str
    role: Role
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None

    def is_expired(self) -> bool:
        """有効期限チェック"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False


class ElderZanRBACManager:
    """
    PROJECT ELDERZAN RBAC管理システム

    機能:
    - 階層的ロール管理
    - 動的権限チェック
    - 4賢者システム統合
    - セッション権限管理
    - 監査ログ統合
    """

    def __init__(self):
        """RBAC管理システム初期化"""
        # ロール・権限定義
        self.roles: Dict[str, Role] = {}
        self.permissions: Dict[str, Permission] = {}

        # ユーザーロール管理
        self.user_roles: Dict[str, UserRole] = {}
        self.session_permissions: Dict[str, Dict[str, Any]] = {}

        # 統計情報
        self.stats = {
            "permission_checks": 0,
            "role_assignments": 0,
            "permission_grants": 0,
            "permission_denials": 0,
            "errors": 0,
        }

        # デフォルト設定初期化
        self._initialize_default_roles()
        self._initialize_default_permissions()

        logger.info("ElderZanRBACManager initialized successfully")

    def _initialize_default_permissions(self):
        """デフォルト権限初期化"""
        # 基本権限
        permissions = [
            Permission(
                name="read_session",
                description="セッション読み取り",
                scope=PermissionScope.SESSION,
                resource_type=ResourceType.SESSION,
                actions=["read"],
            ),
            Permission(
                name="write_session",
                description="セッション書き込み",
                scope=PermissionScope.SESSION,
                resource_type=ResourceType.SESSION,
                actions=["write", "create", "update"],
            ),
            Permission(
                name="delete_session",
                description="セッション削除",
                scope=PermissionScope.SESSION,
                resource_type=ResourceType.SESSION,
                actions=["delete"],
            ),
            Permission(
                name="access_storage",
                description="ストレージアクセス",
                scope=PermissionScope.GLOBAL,
                resource_type=ResourceType.STORAGE,
                actions=["read", "write"],
            ),
            Permission(
                name="manage_knowledge",
                description="知識管理",
                scope=PermissionScope.GLOBAL,
                resource_type=ResourceType.KNOWLEDGE,
                actions=["read", "write", "update", "delete"],
            ),
            Permission(
                name="execute_tasks",
                description="タスク実行",
                scope=PermissionScope.PROJECT,
                resource_type=ResourceType.TASK,
                actions=["execute", "monitor"],
            ),
            Permission(
                name="handle_incidents",
                description="インシデント処理",
                scope=PermissionScope.GLOBAL,
                resource_type=ResourceType.INCIDENT,
                actions=["read", "write", "resolve"],
            ),
            Permission(
                name="perform_rag",
                description="RAG検索実行",
                scope=PermissionScope.GLOBAL,
                resource_type=ResourceType.RAG,
                actions=["search", "index"],
            ),
            Permission(
                name="admin_system",
                description="システム管理",
                scope=PermissionScope.GLOBAL,
                resource_type=ResourceType.SYSTEM,
                actions=["*"],
            ),
        ]

        for permission in permissions:
            self.permissions[permission.name] = permission

    def _initialize_default_roles(self):
        """デフォルトロール初期化"""
        # ゲストロール
        guest_role = Role(
            name="guest",
            level=RoleLevel.GUEST,
            permissions=[],
            restrictions=["read_only", "rate_limited"],
        )

        # ユーザーロール
        user_role = Role(
            name="user",
            level=RoleLevel.USER,
            permissions=[],
            restrictions=["audit_required", "rate_limited"],
        )

        # Claude Agentロール
        claude_role = Role(
            name="claude_agent",
            level=RoleLevel.CLAUDE_AGENT,
            permissions=[],
            restrictions=["approval_required", "audit_required"],
        )

        # 4賢者システムロール
        sage_role = Role(
            name="sage_system",
            level=RoleLevel.SAGE_SYSTEM,
            permissions=[],
            restrictions=["domain_restricted", "audit_required"],
        )

        # エルダー評議会ロール
        elder_role = Role(
            name="elder_council",
            level=RoleLevel.ELDER_COUNCIL,
            permissions=[],
            restrictions=["audit_required", "multi_approval"],
        )

        # ロール登録
        roles = [guest_role, user_role, claude_role, sage_role, elder_role]
        for role in roles:
            self.roles[role.name] = role

        # 権限が初期化された後に実行（イベントループが存在する場合のみ）
        try:
            asyncio.create_task(self._assign_default_permissions())
        except RuntimeError:
            # イベントループが存在しない場合は同期実行
            self._assign_default_permissions_sync()

    async def _assign_default_permissions(self):
        """デフォルト権限割り当て"""
        # 権限の遅延割り当て
        await asyncio.sleep(0.1)  # 権限初期化待ち
        self._assign_default_permissions_sync()

    def _assign_default_permissions_sync(self):
        """デフォルト権限割り当て（同期版）"""
        # ユーザーロール権限
        if "user" in self.roles:
            self.roles["user"].permissions = [
                self.permissions["read_session"],
                self.permissions["write_session"],
            ]

        # Claude Agentロール権限
        if "claude_agent" in self.roles:
            self.roles["claude_agent"].permissions = [
                self.permissions["read_session"],
                self.permissions["write_session"],
                self.permissions["access_storage"],
                self.permissions["execute_tasks"],
                self.permissions["perform_rag"],
            ]

        # 4賢者システムロール権限
        if "sage_system" in self.roles:
            self.roles["sage_system"].permissions = [
                self.permissions["read_session"],
                self.permissions["write_session"],
                self.permissions["access_storage"],
                self.permissions["manage_knowledge"],
                self.permissions["execute_tasks"],
                self.permissions["handle_incidents"],
                self.permissions["perform_rag"],
            ]

        # エルダー評議会ロール権限
        if "elder_council" in self.roles:
            self.roles["elder_council"].permissions = [self.permissions["admin_system"]]

    async def assign_role(
        self,
        user_id: str,
        role_name: str,
        expires_in_hours: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        ユーザーにロール割り当て

        Args:
            user_id: ユーザーID
            role_name: ロール名
            expires_in_hours: 有効期限（時間）
            context: ロールコンテキスト

        Returns:
            bool: 割り当て成功
        """
        try:
            # ロール存在確認
            if role_name not in self.roles:
                raise ValueError(f"Role not found: {role_name}")

            role = self.roles[role_name]

            # 有効期限設定
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.now() + timedelta(hours=expires_in_hours)

            # ユーザーロール作成
            user_role = UserRole(
                user_id=user_id,
                role=role,
                assigned_at=datetime.now(),
                expires_at=expires_at,
                context=context,
            )

            # ユーザーロール保存
            self.user_roles[user_id] = user_role

            self.stats["role_assignments"] += 1
            logger.info(f"Role assigned: {user_id} -> {role_name}")

            return True

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Role assignment failed: {e}")
            return False

    async def check_permission(
        self,
        user_id: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        権限チェック

        Args:
            user_id: ユーザーID
            action: アクション
            resource: リソース
            context: チェックコンテキスト

        Returns:
            bool: 権限チェック結果
        """
        try:
            self.stats["permission_checks"] += 1

            # ユーザーロール取得
            user_role = self.user_roles.get(user_id)
            if not user_role:
                self.stats["permission_denials"] += 1
                logger.warning(f"No role assigned for user: {user_id}")
                return False

            # ロール有効期限チェック
            if user_role.is_expired():
                self.stats["permission_denials"] += 1
                logger.warning(f"Role expired for user: {user_id}")
                return False

            # 権限チェック
            role = user_role.role

            # 管理者権限チェック
            admin_permission = next(
                (p for p in role.permissions if p.name == "admin_system"), None
            )
            if admin_permission and admin_permission.matches(action, resource):
                self.stats["permission_grants"] += 1
                logger.debug(
                    f"Admin permission granted: {user_id} -> {action}:{resource}"
                )
                return True

            # 個別権限チェック
            for permission in role.permissions:
                if permission.matches(action, resource):
                    # 制限チェック
                    if await self._check_restrictions(
                        user_role, action, resource, context
                    ):
                        self.stats["permission_grants"] += 1
                        logger.debug(
                            f"Permission granted: {user_id} -> {action}:{resource}"
                        )
                        return True

            self.stats["permission_denials"] += 1
            logger.debug(f"Permission denied: {user_id} -> {action}:{resource}")
            return False

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Permission check failed: {e}")
            return False

    async def _check_restrictions(
        self,
        user_role: UserRole,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """制限チェック"""
        try:
            restrictions = user_role.role.restrictions

            # 制限チェック実装
            for restriction in restrictions:
                if restriction == "read_only" and action not in ["read"]:
                    return False
                elif restriction == "audit_required":
                    # 監査ログ記録
                    logger.info(
                        f"Audit required: {user_role.user_id} -> {action}:{resource}"
                    )
                elif restriction == "domain_restricted":
                    # ドメイン制限チェック
                    if not (context and not self._check_domain_restriction(context)):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if context and not self._check_domain_restriction(context):
                        return False
                elif restriction == "approval_required":
                    # 承認必須チェック
                    if await self._check_approval_requirement(:
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if not await self._check_approval_requirement(
                        user_role, action, resource
                    ):
                        return False
                elif restriction == "multi_approval":
                    # 複数承認チェック
                    if await self._check_multi_approval(:
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if not await self._check_multi_approval(
                        user_role, action, resource
                    ):
                        return False

            return True

        except Exception as e:
            logger.error(f"Restriction check failed: {e}")
            return False

    def _check_domain_restriction(self, context: Dict[str, Any]) -> bool:
        """ドメイン制限チェック"""
        # 簡易実装 - 実際の実装では適切なドメイン制限を行う
        allowed_domains = context.get("allowed_domains", [])
        current_domain = context.get("current_domain", "")

        if allowed_domains and current_domain:
            return current_domain in allowed_domains

        return True

    async def _check_approval_requirement(
        self, user_role: UserRole, action: str, resource: str
    ) -> bool:
        """承認要件チェック"""
        # 簡易実装 - 実際の実装では適切な承認システムを実装
        if action in ["delete", "admin"]:
            # 高リスク操作は承認必須
            return False

        return True

    async def _check_multi_approval(
        self, user_role: UserRole, action: str, resource: str
    ) -> bool:
        """複数承認チェック"""
        # 簡易実装 - 実際の実装では適切な複数承認システムを実装
        if user_role.role.level == RoleLevel.ELDER_COUNCIL:
            # エルダー評議会は複数承認システム
            return True

        return True

    async def create_session_permission(
        self,
        session_id: str,
        user_id: str,
        permissions: List[str],
        expires_in_minutes: int = 60,
    ) -> bool:
        """
        セッション権限作成

        Args:
            session_id: セッションID
            user_id: ユーザーID
            permissions: セッション権限リスト
            expires_in_minutes: 有効期限（分）

        Returns:
            bool: 作成成功
        """
        try:
            session_permission = {
                "user_id": user_id,
                "permissions": permissions,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=expires_in_minutes),
            }

            self.session_permissions[session_id] = session_permission

            logger.info(f"Session permission created: {session_id} -> {user_id}")
            return True

        except Exception as e:
            logger.error(f"Session permission creation failed: {e}")
            return False

    async def check_session_permission(
        self, session_id: str, user_id: str, permission: str
    ) -> bool:
        """
        セッション権限チェック

        Args:
            session_id: セッションID
            user_id: ユーザーID
            permission: 権限

        Returns:
            bool: 権限チェック結果
        """
        try:
            session_permission = self.session_permissions.get(session_id)
            if not session_permission:
                return False

            # ユーザーID確認
            if session_permission["user_id"] != user_id:
                return False

            # 有効期限確認
            if datetime.now() > session_permission["expires_at"]:
                return False

            # 権限確認
            return permission in session_permission["permissions"]

        except Exception as e:
            logger.error(f"Session permission check failed: {e}")
            return False

    def get_user_permissions(self, user_id: str) -> List[str]:
        """ユーザー権限一覧取得"""
        try:
            user_role = self.user_roles.get(user_id)
            if not user_role or user_role.is_expired():
                return []

            return [p.name for p in user_role.role.permissions]

        except Exception as e:
            logger.error(f"User permissions retrieval failed: {e}")
            return []

    def get_role_info(self, role_name: str) -> Optional[Dict[str, Any]]:
        """ロール情報取得"""
        try:
            role = self.roles.get(role_name)
            if not role:
                return None

            return {
                "name": role.name,
                "level": role.level.value,
                "permissions": [p.name for p in role.permissions],
                "restrictions": role.restrictions,
                "metadata": role.metadata,
            }

        except Exception as e:
            logger.error(f"Role info retrieval failed: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            "rbac_stats": self.stats.copy(),
            "active_users": len(self.user_roles),
            "active_sessions": len(self.session_permissions),
            "roles_count": len(self.roles),
            "permissions_count": len(self.permissions),
            "timestamp": datetime.now().isoformat(),
        }

    async def cleanup_expired(self):
        """期限切れデータクリーンアップ"""
        try:
            # 期限切れユーザーロール削除
            expired_users = [
                user_id
                for user_id, user_role in self.user_roles.items()
                if user_role.is_expired()
            ]

            for user_id in expired_users:
                del self.user_roles[user_id]
                logger.info(f"Expired user role cleaned up: {user_id}")

            # 期限切れセッション権限削除
            expired_sessions = [
                session_id
                for session_id, session_perm in self.session_permissions.items()
                if datetime.now() > session_perm["expires_at"]
            ]

            for session_id in expired_sessions:
                del self.session_permissions[session_id]
                logger.info(f"Expired session permission cleaned up: {session_id}")

            logger.info(
                f"Cleanup completed: {len(expired_users)} users, {len(expired_sessions)} sessions"
            )

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# 例外クラス
class RBACError(Exception):
    """RBAC エラー基底クラス"""

    pass


class RoleError(RBACError):
    """ロールエラー"""

    pass


class PermissionError(RBACError):
    """権限エラー"""

    pass
