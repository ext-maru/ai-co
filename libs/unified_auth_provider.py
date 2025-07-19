#!/usr/bin/env python3
"""
統合認証プロバイダー
Elders Guild Elder Hierarchy Authentication System

エルダーズ評議会承認済み統合認証システム
JWT + Session hybrid authentication with Elder hierarchy support
"""

import hashlib
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple

import jwt
import pyotp


class SecurityError(Exception):
    """セキュリティ違反時の例外"""

    pass


logger = logging.getLogger(__name__)


class AuthResult(Enum):
    """認証結果"""

    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    MFA_REQUIRED = "mfa_required"
    INVALID_MFA_CODE = "invalid_mfa_code"
    SESSION_EXPIRED = "session_expired"
    RATE_LIMITED = "rate_limited"
    DEVICE_NOT_TRUSTED = "device_not_trusted"


class ElderRole(Enum):
    """Elder階層"""

    GRAND_ELDER = "grand_elder"  # 🌟 最高権限
    CLAUDE_ELDER = "claude_elder"  # 🤖 開発実行責任者
    SAGE = "sage"  # 🧙‍♂️ 賢者
    SERVANT = "servant"  # 🧝‍♂️ 基本権限


class SageType(Enum):
    """賢者の種類"""

    KNOWLEDGE = "knowledge"  # 📚 ナレッジ賢者
    TASK = "task"  # 📋 タスク賢者
    INCIDENT = "incident"  # 🚨 インシデント賢者
    RAG = "rag"  # 🔍 RAG賢者


@dataclass
class User:
    """ユーザー情報"""

    id: str
    username: str
    email: str
    elder_role: ElderRole
    sage_type: Optional[SageType] = None
    is_active: bool = True
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    trusted_devices: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)


@dataclass
class AuthRequest:
    """認証リクエスト"""

    username: str
    password: str
    mfa_code: Optional[str] = None
    ip_address: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None


@dataclass
class AuthSession:
    """認証セッション"""

    session_id: str
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None


class UnifiedAuthProvider:
    """統合認証プロバイダー"""

    def __init__(
        self,
        secret_key: str = None,
        session_duration_hours: int = 24,
        enable_mfa: bool = True,
        enable_device_tracking: bool = True,
    ):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.session_duration_hours = session_duration_hours
        self.enable_mfa = enable_mfa
        self.enable_device_tracking = enable_device_tracking

        # ユーザー情報ストレージ
        self.users: Dict[str, User] = {}
        self.user_credentials: Dict[str, Dict[str, str]] = {}
        self.active_sessions: Dict[str, AuthSession] = {}

        # セキュリティ設定
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self.password_min_length = 8

        # レート制限
        self.auth_attempts: Dict[str, List[datetime]] = {}
        self.rate_limit_window_minutes = 15
        self.rate_limit_max_attempts = 10

    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        elder_role: ElderRole,
        sage_type: Optional[SageType] = None,
    ) -> User:
        """ユーザー作成"""
        # 重複チェック
        if any(user.username == username for user in self.users.values()):
            raise ValueError(f"Username '{username}' already exists")

        # パスワード強度チェック
        if len(password) < self.password_min_length:
            raise ValueError(
                f"Password must be at least {self.password_min_length} characters"
            )

        # ユーザーID生成
        user_id = secrets.token_urlsafe(16)

        # ユーザー作成
        user = User(
            id=user_id,
            username=username,
            email=email,
            elder_role=elder_role,
            sage_type=sage_type,
        )

        # パスワードハッシュ化
        salt = secrets.token_urlsafe(16)
        password_hash = self._hash_password(password, salt)

        # ストレージに保存
        self.users[user_id] = user
        self.user_credentials[username] = {
            "user_id": user_id,
            "password_hash": password_hash,
            "salt": salt,
        }

        # Elder階層に基づく権限設定
        user.permissions = self._get_elder_permissions(elder_role, sage_type)

        return user

    def authenticate(
        self, auth_request: AuthRequest
    ) -> Tuple[AuthResult, Optional[AuthSession], Optional[User]]:
        """認証実行"""
        # レート制限チェック
        if not self._check_rate_limit(auth_request.ip_address):
            return AuthResult.RATE_LIMITED, None, None

        # ユーザー取得
        if auth_request.username not in self.user_credentials:
            return AuthResult.INVALID_CREDENTIALS, None, None

        user_creds = self.user_credentials[auth_request.username]
        user = self.users[user_creds["user_id"]]

        # アカウントロックチェック
        if user.locked_until and user.locked_until > datetime.now():
            return AuthResult.ACCOUNT_LOCKED, None, None

        # パスワード検証
        if not self._verify_password(
            auth_request.password, user_creds["password_hash"], user_creds["salt"]
        ):
            user.failed_attempts += 1

            # アカウントロック
            if user.failed_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.now() + timedelta(
                    minutes=self.lockout_duration_minutes
                )
                return AuthResult.ACCOUNT_LOCKED, None, None

            return AuthResult.INVALID_CREDENTIALS, None, None

        # MFA チェック
        if user.mfa_enabled and not auth_request.mfa_code:
            return AuthResult.MFA_REQUIRED, None, None

        if user.mfa_enabled and auth_request.mfa_code:
            if not self._verify_mfa_code(user, auth_request.mfa_code):
                return AuthResult.INVALID_MFA_CODE, None, None

        # 認証成功
        user.failed_attempts = 0
        user.last_login = datetime.now()
        user.locked_until = None

        # セッション作成
        session = self._create_session(user, auth_request)

        return AuthResult.SUCCESS, session, user

    def validate_token(
        self, token: str, current_ip: Optional[str] = None
    ) -> Tuple[bool, Optional[AuthSession], Optional[User]]:
        """トークン検証（IPアドレス検証付き）"""
        try:
            # JWT検証
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            session_id = payload.get("session_id")

            if not session_id or session_id not in self.active_sessions:
                return False, None, None

            session = self.active_sessions[session_id]

            # セッション有効期限チェック
            if session.expires_at < datetime.now():
                del self.active_sessions[session_id]
                return False, None, None

            # IPアドレス検証（セッションハイジャック防止）
            if self.enable_device_tracking and current_ip and session.ip_address:
                if session.ip_address != current_ip:
                    # IPアドレス変更を検出 - セッション無効化
                    del self.active_sessions[session_id]
                    return False, None, None

            user = self.users.get(session.user_id)
            if not user or not user.is_active:
                return False, None, None

            return True, session, user

        except jwt.InvalidTokenError:
            return False, None, None

    def enable_mfa_for_user(self, username: str) -> str:
        """ユーザーのMFA有効化"""
        user_creds = self.user_credentials.get(username)
        if not user_creds:
            raise ValueError(f"User '{username}' not found")

        user = self.users[user_creds["user_id"]]

        # MFA秘密鍵生成
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = True

        # QRコード用のプロビジョニングURI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email, issuer_name="Elders Guild Elder System"
        )

        return provisioning_uri

    def check_elder_permission(self, user: User, required_role: ElderRole) -> bool:
        """Elder階層権限チェック（イミュータブル検証付き）"""
        # ユーザー情報の改ざん検出：認証情報との照合
        if user.username not in self.user_credentials:
            return False

        user_creds = self.user_credentials[user.username]
        stored_user = self.users[user_creds["user_id"]]

        # セッション中の権限改ざんを検出
        # 注意：Pythonではオブジェクト参照が同じになる可能性があるため、
        # より厳密なチェックを実装
        expected_role = stored_user.elder_role

        # ユーザーIDが改ざんされていないかチェック
        if user.id != stored_user.id:
            raise SecurityError(f"ユーザーID改ざん検出: 期待値={stored_user.id}, 実際値={user.id}")

        # 重要：stored_userの元の権限を使用して判定
        role_hierarchy = {
            ElderRole.GRAND_ELDER: 4,
            ElderRole.CLAUDE_ELDER: 3,
            ElderRole.SAGE: 2,
            ElderRole.SERVANT: 1,
        }

        user_level = role_hierarchy.get(expected_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        # デバッグログ（権限チェック記録）
        logger.info(
            f"権限チェック: user={user.username}, role={expected_role.value}, required={required_role.value}, granted={user_level >= required_level}"
        )

        return user_level >= required_level

    def check_sage_permission(self, user: User, required_sage_type: SageType) -> bool:
        """賢者専門権限チェック"""
        if user.elder_role != ElderRole.SAGE:
            return False

        return user.sage_type == required_sage_type

    def logout(self, session_id: str) -> bool:
        """ログアウト"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False

    def _hash_password(self, password: str, salt: str) -> str:
        """パスワードハッシュ化"""
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100000
        ).hex()

    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """パスワード検証"""
        return password_hash == self._hash_password(password, salt)

    def _verify_mfa_code(self, user: User, code: str) -> bool:
        """MFAコード検証"""
        if not user.mfa_secret:
            return False

        totp = pyotp.TOTP(user.mfa_secret)
        return totp.verify(code, valid_window=1)

    def _create_session(self, user: User, auth_request: AuthRequest) -> AuthSession:
        """セッション作成"""
        session_id = secrets.token_urlsafe(32)

        # JWT作成
        payload = {
            "session_id": session_id,
            "user_id": user.id,
            "elder_role": user.elder_role.value,
            "sage_type": user.sage_type.value if user.sage_type else None,
            "iat": datetime.now().timestamp(),
            "exp": (
                datetime.now() + timedelta(hours=self.session_duration_hours)
            ).timestamp(),
        }

        token = jwt.encode(payload, self.secret_key, algorithm="HS256")

        # セッション作成
        session = AuthSession(
            session_id=session_id,
            user_id=user.id,
            token=token,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self.session_duration_hours),
            ip_address=auth_request.ip_address,
            device_info=auth_request.device_info,
        )

        self.active_sessions[session_id] = session
        return session

    def _check_rate_limit(self, ip_address: Optional[str]) -> bool:
        """レート制限チェック"""
        if not ip_address:
            return True

        now = datetime.now()
        window_start = now - timedelta(minutes=self.rate_limit_window_minutes)

        if ip_address not in self.auth_attempts:
            self.auth_attempts[ip_address] = []

        # 古い試行を削除
        self.auth_attempts[ip_address] = [
            attempt
            for attempt in self.auth_attempts[ip_address]
            if attempt > window_start
        ]

        # 制限チェック
        if len(self.auth_attempts[ip_address]) >= self.rate_limit_max_attempts:
            return False

        # 現在の試行を記録
        self.auth_attempts[ip_address].append(now)
        return True

    def _get_elder_permissions(
        self, elder_role: ElderRole, sage_type: Optional[SageType]
    ) -> List[str]:
        """Elder階層に基づく権限取得"""
        permissions = []

        # 基本権限
        permissions.extend(["read", "write", "execute"])

        # Elder階層別権限
        if elder_role == ElderRole.GRAND_ELDER:
            permissions.extend(["admin", "promote", "demote", "configure_system"])
        elif elder_role == ElderRole.CLAUDE_ELDER:
            permissions.extend(["deploy", "manage_workers", "system_config"])
        elif elder_role == ElderRole.SAGE:
            permissions.extend(["advanced_operations", "specialized_tasks"])

            # 賢者専門権限
            if sage_type == SageType.KNOWLEDGE:
                permissions.extend(["knowledge_management", "documentation"])
            elif sage_type == SageType.TASK:
                permissions.extend(["task_management", "scheduling"])
            elif sage_type == SageType.INCIDENT:
                permissions.extend(["incident_response", "security_monitoring"])
            elif sage_type == SageType.RAG:
                permissions.extend(["search_operations", "data_analysis"])

        return permissions


# デコレーター
def elder_auth_required(required_role: ElderRole = ElderRole.SERVANT):
    """Elder階層認証デコレーター"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 実装は実際の使用時に認証プロバイダーと連携
            return func(*args, **kwargs)

        return wrapper

    return decorator


def sage_auth_required(required_sage_type: SageType):
    """賢者専門認証デコレーター"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 実装は実際の使用時に認証プロバイダーと連携
            return func(*args, **kwargs)

        return wrapper

    return decorator


def create_demo_auth_system() -> UnifiedAuthProvider:
    """デモ認証システム作成"""
    # 256bit（32バイト）の強力な秘密鍵を生成
    strong_secret = secrets.token_urlsafe(32)

    auth = UnifiedAuthProvider(
        secret_key=strong_secret,
        session_duration_hours=24,
        enable_mfa=True,
        enable_device_tracking=True,
    )

    # デモユーザー作成
    try:
        # Grand Elder maru
        auth.create_user(
            "maru", "grand_elder_password", "maru@ai-company.com", ElderRole.GRAND_ELDER
        )
        auth.create_user(
            "grand_elder",
            "grand_password",
            "maru@ai-company.com",
            ElderRole.GRAND_ELDER,
        )

        # Claude Elder
        auth.create_user(
            "claude_elder",
            "claude_elder_password",
            "claude@ai-company.com",
            ElderRole.CLAUDE_ELDER,
        )

        # Four Sages
        auth.create_user(
            "knowledge_sage",
            "knowledge_password",
            "knowledge@ai-company.com",
            ElderRole.SAGE,
            SageType.KNOWLEDGE,
        )
        auth.create_user(
            "task_sage",
            "task_password",
            "task@ai-company.com",
            ElderRole.SAGE,
            SageType.TASK,
        )
        auth.create_user(
            "incident_sage",
            "incident_password",
            "incident@ai-company.com",
            ElderRole.SAGE,
            SageType.INCIDENT,
        )
        auth.create_user(
            "rag_sage",
            "rag_password",
            "rag@ai-company.com",
            ElderRole.SAGE,
            SageType.RAG,
        )

        # General user
        auth.create_user(
            "servant1", "servant_password", "servant1@ai-company.com", ElderRole.SERVANT
        )

    except Exception as e:
        logger.error(f"Failed to create demo users: {e}")

    return auth
