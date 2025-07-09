"""
統合認証プロバイダー v2.0
AI Company Authentication System - 4賢者システム統合版

エルダーズ評議会承認済み認証システム
"""
import secrets
import hashlib
import jwt
import pyotp
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import logging

# Configure logging
logger = logging.getLogger(__name__)


class AuthResult(Enum):
    """認証結果"""
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    MFA_REQUIRED = "mfa_required"
    MFA_INVALID = "mfa_invalid"
    SESSION_EXPIRED = "session_expired"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"


class ElderRole(Enum):
    """Elder階層システム"""
    GRAND_ELDER = "grand_elder"    # 最高権限 - グランドエルダーmaru
    CLAUDE_ELDER = "claude_elder"  # 開発実行責任者 - クロードエルダー
    SAGE = "sage"                  # 4賢者システム
    SERVANT = "servant"            # 一般権限


class SageType(Enum):
    """4賢者タイプ"""
    KNOWLEDGE = "knowledge"     # ナレッジ賢者
    TASK = "task"              # タスク賢者
    INCIDENT = "incident"      # インシデント賢者
    RAG = "rag"               # RAG賢者


@dataclass
class User:
    """ユーザーモデル"""
    id: int
    username: str
    email: str
    elder_role: ElderRole
    sage_type: Optional[SageType] = None
    is_active: bool = True
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class AuthSession:
    """認証セッション"""
    session_id: str
    user_id: int
    token: str
    refresh_token: str
    expires_at: datetime
    device_info: Dict[str, Any]
    ip_address: str
    is_trusted: bool = False
    mfa_verified: bool = False


@dataclass
class AuthRequest:
    """認証リクエスト"""
    username: str
    password: str
    mfa_token: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    remember_me: bool = False


class UnifiedAuthProvider:
    """
    統合認証プロバイダー
    Elder階層システム統合認証管理
    """
    
    def __init__(self, 
                 secret_key: str,
                 session_duration_hours: int = 24,
                 enable_mfa: bool = True,
                 enable_device_tracking: bool = True):
        self.secret_key = secret_key
        self.session_duration_hours = session_duration_hours
        self.enable_mfa = enable_mfa
        self.enable_device_tracking = enable_device_tracking
        
        # In-memory storage (本番環境では適切なストレージを使用)
        self.users: Dict[int, User] = {}
        self.sessions: Dict[str, AuthSession] = {}
        self.user_credentials: Dict[str, Dict] = {}  # username -> {password_hash, salt}
        
        logger.info("UnifiedAuthProvider initialized")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """パスワードをハッシュ化"""
        return hashlib.pbkdf2_hmac('sha256', 
                                 password.encode('utf-8'), 
                                 salt.encode('utf-8'), 
                                 100000).hex()
    
    def _generate_salt(self) -> str:
        """ソルト生成"""
        return secrets.token_hex(32)
    
    def _generate_session_token(self) -> str:
        """セッショントークン生成"""
        return secrets.token_urlsafe(32)
    
    def _generate_jwt_token(self, user: User, session_id: str) -> str:
        """JWTトークン生成"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'elder_role': user.elder_role.value,
            'sage_type': user.sage_type.value if user.sage_type else None,
            'session_id': session_id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=self.session_duration_hours),
            'iat': datetime.now(timezone.utc),
            'iss': 'ai-company-elder-system'
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def create_user(self, 
                   username: str, 
                   password: str, 
                   email: str,
                   elder_role: ElderRole = ElderRole.SERVANT,
                   sage_type: Optional[SageType] = None) -> User:
        """ユーザー作成"""
        if username in self.user_credentials:
            raise ValueError(f"Username '{username}' already exists")
        
        user_id = len(self.users) + 1
        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            elder_role=elder_role,
            sage_type=sage_type,
            created_at=datetime.now()
        )
        
        self.users[user_id] = user
        self.user_credentials[username] = {
            'password_hash': password_hash,
            'salt': salt,
            'user_id': user_id
        }
        
        logger.info(f"User created: {username} (Elder: {elder_role.value})")
        return user
    
    def authenticate(self, auth_request: AuthRequest) -> Tuple[AuthResult, Optional[AuthSession], Optional[User]]:
        """認証実行"""
        # ユーザー情報取得
        if auth_request.username not in self.user_credentials:
            logger.warning(f"Authentication failed: Unknown user {auth_request.username}")
            return AuthResult.INVALID_CREDENTIALS, None, None
        
        creds = self.user_credentials[auth_request.username]
        user = self.users[creds['user_id']]
        
        # アカウントロック チェック
        if user.locked_until and datetime.now() < user.locked_until:
            logger.warning(f"Authentication blocked: Account locked {auth_request.username}")
            return AuthResult.ACCOUNT_LOCKED, None, None
        
        # パスワード検証
        password_hash = self._hash_password(auth_request.password, creds['salt'])
        if password_hash != creds['password_hash']:
            # 失敗回数を増加
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = datetime.now() + timedelta(minutes=30)
                logger.warning(f"Account locked due to failed attempts: {auth_request.username}")
            return AuthResult.INVALID_CREDENTIALS, None, None
        
        # MFA チェック
        if user.mfa_enabled and self.enable_mfa:
            if not auth_request.mfa_token:
                logger.info(f"MFA required for user: {auth_request.username}")
                return AuthResult.MFA_REQUIRED, None, None
            
            if not self._verify_mfa(user, auth_request.mfa_token):
                logger.warning(f"MFA verification failed: {auth_request.username}")
                return AuthResult.MFA_INVALID, None, None
        
        # 認証成功 - セッション作成
        session = self._create_session(user, auth_request)
        user.failed_attempts = 0  # リセット
        user.last_login = datetime.now()
        
        logger.info(f"Authentication successful: {auth_request.username}")
        return AuthResult.SUCCESS, session, user
    
    def _verify_mfa(self, user: User, mfa_token: str) -> bool:
        """MFA検証"""
        if not user.mfa_secret:
            return False
        
        try:
            totp = pyotp.TOTP(user.mfa_secret)
            return totp.verify(mfa_token)
        except Exception as e:
            logger.error(f"MFA verification error: {e}")
            return False
    
    def _create_session(self, user: User, auth_request: AuthRequest) -> AuthSession:
        """セッション作成"""
        session_id = self._generate_session_token()
        jwt_token = self._generate_jwt_token(user, session_id)
        refresh_token = self._generate_session_token()
        
        duration = timedelta(days=30) if auth_request.remember_me else timedelta(hours=self.session_duration_hours)
        expires_at = datetime.now() + duration
        
        session = AuthSession(
            session_id=session_id,
            user_id=user.id,
            token=jwt_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            device_info=auth_request.device_info or {},
            ip_address=auth_request.ip_address or "unknown",
            mfa_verified=user.mfa_enabled and self.enable_mfa
        )
        
        self.sessions[session_id] = session
        return session
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[User], Optional[AuthSession]]:
        """トークン検証"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            session_id = payload.get('session_id')
            user_id = payload.get('user_id')
            
            if not session_id or session_id not in self.sessions:
                return False, None, None
            
            session = self.sessions[session_id]
            if datetime.now() > session.expires_at:
                # 期限切れセッション削除
                del self.sessions[session_id]
                return False, None, None
            
            user = self.users.get(user_id)
            if not user or not user.is_active:
                return False, None, None
            
            return True, user, session
            
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError) as e:
            logger.warning(f"Token validation failed: {e}")
            return False, None, None
    
    def check_elder_permission(self, user: User, required_role: ElderRole) -> bool:
        """Elder階層権限チェック"""
        role_hierarchy = {
            ElderRole.GRAND_ELDER: 4,
            ElderRole.CLAUDE_ELDER: 3,
            ElderRole.SAGE: 2,
            ElderRole.SERVANT: 1
        }
        
        user_level = role_hierarchy.get(user.elder_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def check_sage_permission(self, user: User, required_sage: SageType) -> bool:
        """賢者権限チェック"""
        # グランドエルダーとクロードエルダーは全権限
        if user.elder_role in [ElderRole.GRAND_ELDER, ElderRole.CLAUDE_ELDER]:
            return True
        
        # 賢者は自分のタイプのみ
        return user.sage_type == required_sage
    
    def enable_mfa_for_user(self, user_id: int) -> str:
        """ユーザーのMFA有効化"""
        if user_id not in self.users:
            raise ValueError("User not found")
        
        user = self.users[user_id]
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = True
        
        # QRコード用のプロビジョニングURI
        provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="AI Company Elder System"
        )
        
        logger.info(f"MFA enabled for user: {user.username}")
        return provisioning_uri
    
    def refresh_session(self, refresh_token: str) -> Tuple[bool, Optional[AuthSession]]:
        """セッション更新"""
        for session in self.sessions.values():
            if session.refresh_token == refresh_token:
                if datetime.now() < session.expires_at:
                    # 新しいトークン生成
                    user = self.users[session.user_id]
                    session.token = self._generate_jwt_token(user, session.session_id)
                    session.expires_at = datetime.now() + timedelta(hours=self.session_duration_hours)
                    return True, session
                else:
                    # 期限切れセッション削除
                    del self.sessions[session.session_id]
                    break
        
        return False, None
    
    def logout(self, session_id: str) -> bool:
        """ログアウト"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session logged out: {session_id}")
            return True
        return False
    
    def get_active_sessions(self, user_id: int) -> List[AuthSession]:
        """ユーザーのアクティブセッション取得"""
        now = datetime.now()
        active_sessions = []
        
        for session in list(self.sessions.values()):
            if session.user_id == user_id:
                if now < session.expires_at:
                    active_sessions.append(session)
                else:
                    # 期限切れセッション削除
                    del self.sessions[session.session_id]
        
        return active_sessions
    
    def revoke_all_sessions(self, user_id: int) -> int:
        """ユーザーの全セッション取り消し"""
        revoked_count = 0
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            if session.user_id == user_id:
                sessions_to_remove.append(session_id)
                revoked_count += 1
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
        
        logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
        return revoked_count


def elder_auth_required(elder_role: ElderRole):
    """Elder権限必須デコレーター"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 実装時はFlaskのcurrent_userなどから取得
            user = kwargs.get('current_user')
            if not user:
                raise PermissionError("Authentication required")
            
            auth_provider = kwargs.get('auth_provider')  # DIで注入想定
            if not auth_provider or not auth_provider.check_elder_permission(user, elder_role):
                raise PermissionError(f"Elder role '{elder_role.value}' required")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def sage_auth_required(sage_type: SageType):
    """賢者権限必須デコレーター"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            if not user:
                raise PermissionError("Authentication required")
            
            auth_provider = kwargs.get('auth_provider')
            if not auth_provider or not auth_provider.check_sage_permission(user, sage_type):
                raise PermissionError(f"Sage type '{sage_type.value}' required")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# デモ用のファクトリー関数
def create_demo_auth_system() -> UnifiedAuthProvider:
    """デモ用認証システム作成"""
    auth = UnifiedAuthProvider(
        secret_key="demo-secret-key-elder-system-2025",
        session_duration_hours=24,
        enable_mfa=True
    )
    
    # デモユーザー作成
    try:
        # グランドエルダーmaru
        auth.create_user("maru", "grand_elder_password", "maru@ai-company.com", 
                        ElderRole.GRAND_ELDER)
        
        # クロードエルダー
        auth.create_user("claude_elder", "claude_elder_password", "claude@ai-company.com",
                        ElderRole.CLAUDE_ELDER)
        
        # 4賢者
        auth.create_user("knowledge_sage", "knowledge_password", "knowledge@ai-company.com",
                        ElderRole.SAGE, SageType.KNOWLEDGE)
        auth.create_user("task_sage", "task_password", "task@ai-company.com",
                        ElderRole.SAGE, SageType.TASK)
        auth.create_user("incident_sage", "incident_password", "incident@ai-company.com",
                        ElderRole.SAGE, SageType.INCIDENT)
        auth.create_user("rag_sage", "rag_password", "rag@ai-company.com",
                        ElderRole.SAGE, SageType.RAG)
        
        # 一般ユーザー
        auth.create_user("servant1", "servant_password", "servant1@ai-company.com",
                        ElderRole.SERVANT)
        
        logger.info("Demo authentication system created with Elder hierarchy")
    except ValueError as e:
        logger.warning(f"Demo user creation skipped: {e}")
    
    return auth