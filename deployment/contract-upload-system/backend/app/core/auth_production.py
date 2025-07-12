"""
本番環境認証システム - Elder Flow準拠
JWT認証とセッション管理
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# パスワードハッシュ化設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT設定
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'development-jwt-secret')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))

# HTTPベアラー認証
security = HTTPBearer()

class AuthenticationError(Exception):
    """認証エラー"""
    pass

class AuthorizationError(Exception):
    """認可エラー"""
    pass

class ProductionAuthenticator:
    """本番環境認証システム"""

    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.failed_attempts: Dict[str, list] = {}
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)

    def hash_password(self, password: str) -> str:
        """パスワードハッシュ化"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """パスワード検証"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """アクセストークン作成"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, user_id: str) -> str:
        """リフレッシュトークン作成"""
        data = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        }
        return jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """トークン検証"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTError:
            raise AuthenticationError("Invalid token")

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """ユーザー認証"""
        # 失敗回数チェック
        if self._is_account_locked(username):
            raise AuthenticationError("Account temporarily locked due to failed attempts")

        # 実際の本番環境では、データベースからユーザー情報を取得
        # ここではデモ用の固定ユーザー
        demo_users = {
            "admin": {
                "id": "admin-001",
                "username": "admin",
                "password_hash": self.hash_password("admin123"),
                "role": "admin",
                "name": "システム管理者"
            },
            "user": {
                "id": "user-001",
                "username": "user",
                "password_hash": self.hash_password("user123"),
                "role": "user",
                "name": "一般ユーザー"
            }
        }

        user = demo_users.get(username)
        if not user:
            self._record_failed_attempt(username)
            raise AuthenticationError("Invalid credentials")

        if not self.verify_password(password, user["password_hash"]):
            self._record_failed_attempt(username)
            raise AuthenticationError("Invalid credentials")

        # 認証成功時は失敗記録をクリア
        self._clear_failed_attempts(username)

        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "name": user["name"]
        }

    def _is_account_locked(self, username: str) -> bool:
        """アカウントロック状態チェック"""
        if username not in self.failed_attempts:
            return False

        attempts = self.failed_attempts[username]

        # 古い失敗記録を削除
        cutoff_time = datetime.utcnow() - self.lockout_duration
        attempts = [attempt for attempt in attempts if attempt > cutoff_time]
        self.failed_attempts[username] = attempts

        return len(attempts) >= self.max_failed_attempts

    def _record_failed_attempt(self, username: str):
        """認証失敗記録"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []

        self.failed_attempts[username].append(datetime.utcnow())
        logger.warning(f"Authentication failed for user: {username}")

    def _clear_failed_attempts(self, username: str):
        """認証失敗記録クリア"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]

    def create_session(self, user: Dict) -> str:
        """セッション作成"""
        session_id = secrets.token_urlsafe(32)

        self.active_sessions[session_id] = {
            "user": user,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "ip_address": None  # 実際の実装では設定
        }

        logger.info(f"Session created for user: {user['username']}")
        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict]:
        """セッション検証"""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        # セッション有効期限チェック
        session_timeout = timedelta(seconds=int(os.getenv('SESSION_TIMEOUT', '3600')))
        if datetime.utcnow() - session["last_activity"] > session_timeout:
            del self.active_sessions[session_id]
            return None

        # 最終活動時刻更新
        session["last_activity"] = datetime.utcnow()

        return session["user"]

    def logout(self, session_id: str):
        """ログアウト"""
        if session_id in self.active_sessions:
            user = self.active_sessions[session_id]["user"]
            del self.active_sessions[session_id]
            logger.info(f"User logged out: {user['username']}")

# グローバル認証インスタンス
authenticator = ProductionAuthenticator()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """現在のユーザー取得 (本番環境)"""
    try:
        token = credentials.credentials
        payload = authenticator.verify_token(token)

        # トークンタイプチェック
        if payload.get("type") == "refresh":
            raise AuthenticationError("Refresh token cannot be used for authentication")

        # ユーザー情報取得
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        # 実際の本番環境では、データベースからユーザー情報を取得
        # ここではデモ用
        demo_users = {
            "admin-001": {"id": "admin-001", "username": "admin", "role": "admin", "name": "システム管理者"},
            "user-001": {"id": "user-001", "username": "user", "role": "user", "name": "一般ユーザー"}
        }

        user = demo_users.get(user_id)
        if not user:
            raise AuthenticationError("User not found")

        return user

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(required_role: str):
    """権限チェックデコレータ"""
    def role_checker(current_user: Dict = Depends(get_current_user)):
        if current_user["role"] != required_role and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# 管理者権限必須
require_admin = require_role("admin")

class LoginRequest:
    """ログインリクエスト"""
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

class TokenResponse:
    """トークンレスポンス"""
    def __init__(self, access_token: str, refresh_token: str, token_type: str = "bearer"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type

async def login(username: str, password: str) -> TokenResponse:
    """ログイン処理"""
    try:
        user = authenticator.authenticate_user(username, password)

        # アクセストークン作成
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = authenticator.create_access_token(
            data={"sub": user["id"], "username": user["username"], "role": user["role"]},
            expires_delta=access_token_expires
        )

        # リフレッシュトークン作成
        refresh_token = authenticator.create_refresh_token(user["id"])

        # セッション作成
        session_id = authenticator.create_session(user)

        logger.info(f"User logged in successfully: {username}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

async def refresh_access_token(refresh_token: str) -> TokenResponse:
    """アクセストークン更新"""
    try:
        payload = authenticator.verify_token(refresh_token)

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        # 新しいアクセストークン作成
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = authenticator.create_access_token(
            data={"sub": user_id},
            expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
