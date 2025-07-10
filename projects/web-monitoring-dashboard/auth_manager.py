"""
Web認証システム実装
Elders Guild Dashboard認証管理
"""

import re
import secrets
import sqlite3
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from functools import wraps
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

import jwt
from flask import request
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash


class AuthenticationError(Exception):
    """認証エラー"""


class AuthorizationError(Exception):
    """認可エラー"""


class User:
    """ユーザーモデル"""

    def __init__(self, username: str, email: str, role: str = "user"):
        self.id: Optional[int] = None
        self.username = username
        self.email = email
        self.role = role
        self.password_hash: Optional[str] = None
        self.is_active = True
        self.created_at: Optional[datetime] = None
        self.last_login: Optional[datetime] = None

    def set_password(self, password: str):
        """パスワードをハッシュ化して設定"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """パスワードを検証"""
        if not password or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（パスワードハッシュは除外）"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class Session:
    """セッションモデル"""

    def __init__(self, user_id: int, duration_hours: int = 24):
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=duration_hours)

    def is_valid(self) -> bool:
        """セッションが有効かチェック"""
        return datetime.now() < self.expires_at

    def extend(self, hours: int = 24):
        """セッションを延長"""
        self.expires_at = datetime.now() + timedelta(hours=hours)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """パスワード強度を検証"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain letters"

    if not re.search(r"[0-9]", password):
        return False, "Password must contain numbers"

    return True, "Password is strong"


class AuthManager:
    """認証マネージャー"""

    def __init__(self, db_path: str = "auth.db", secret_key: str = None, use_jwt: bool = False):
        self.db_path = db_path
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.use_jwt = use_jwt
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._initialize_database()

    def _initialize_database(self):
        """データベースを初期化"""
        cursor = self.db.cursor()

        # usersテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """
        )

        # sessionsテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        self.db.commit()

    def create_user(self, username: str, email: str, password: str, role: str = "user") -> User:
        """新規ユーザーを作成"""
        # 重複チェック
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            raise ValueError("Username already exists")

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            raise ValueError("Email already exists")

        # ユーザー作成
        user = User(username, email, role)
        user.set_password(password)
        user.created_at = datetime.now()

        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (user.username, user.email, user.password_hash, user.role, user.created_at),
        )

        user.id = cursor.lastrowid
        self.db.commit()

        return user

    def authenticate(self, username: str, password: str) -> Tuple[User, Session]:
        """ユーザーを認証"""
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, role, is_active, created_at, last_login
            FROM users WHERE username = ?
        """,
            (username,),
        )

        row = cursor.fetchone()
        if not row:
            raise AuthenticationError("Invalid username or password")

        user = User(row["username"], row["email"], row["role"])
        user.id = row["id"]
        user.password_hash = row["password_hash"]
        user.is_active = bool(row["is_active"])
        user.created_at = datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        user.last_login = datetime.fromisoformat(row["last_login"]) if row["last_login"] else None

        if not user.check_password(password):
            raise AuthenticationError("Invalid username or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        # セッション作成
        session = Session(user.id)
        cursor.execute(
            """
            INSERT INTO sessions (token, user_id, expires_at)
            VALUES (?, ?, ?)
        """,
            (session.token, session.user_id, session.expires_at),
        )

        # 最終ログイン更新
        cursor.execute(
            """
            UPDATE users SET last_login = ? WHERE id = ?
        """,
            (datetime.now(), user.id),
        )

        self.db.commit()

        return user, session

    def validate_session(self, token: str) -> Optional[User]:
        """セッショントークンを検証"""
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT s.user_id, s.expires_at,
                   u.username, u.email, u.role, u.is_active
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """,
            (token,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        # 期限チェック
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now() >= expires_at:
            # 期限切れセッションを削除
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            self.db.commit()
            return None

        # ユーザー情報を返す
        user = User(row["username"], row["email"], row["role"])
        user.id = row["user_id"]
        user.is_active = bool(row["is_active"])

        return user

    def logout(self, token: str):
        """ログアウト（セッション削除）"""
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        self.db.commit()

    def update_user(self, user_id: int, **kwargs) -> User:
        """ユーザー情報を更新"""
        cursor = self.db.cursor()
        updates = []
        params = []

        if "email" in kwargs:
            updates.append("email = ?")
            params.append(kwargs["email"])

        if "password" in kwargs:
            password_hash = generate_password_hash(kwargs["password"])
            updates.append("password_hash = ?")
            params.append(password_hash)

        if "role" in kwargs:
            updates.append("role = ?")
            params.append(kwargs["role"])

        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            self.db.commit()

        # 更新後のユーザー情報を取得
        cursor.execute(
            """
            SELECT username, email, role, is_active, password_hash
            FROM users WHERE id = ?
        """,
            (user_id,),
        )
        row = cursor.fetchone()

        user = User(row["username"], row["email"], row["role"])
        user.id = user_id
        user.is_active = bool(row["is_active"])
        user.password_hash = row["password_hash"]

        return user

    def deactivate_user(self, user_id: int):
        """ユーザーを無効化"""
        cursor = self.db.cursor()
        cursor.execute(
            """
            UPDATE users SET is_active = FALSE WHERE id = ?
        """,
            (user_id,),
        )

        # 全セッションを削除
        cursor.execute(
            """
            DELETE FROM sessions WHERE user_id = ?
        """,
            (user_id,),
        )

        self.db.commit()

    def clean_expired_sessions(self) -> int:
        """期限切れセッションをクリーンアップ"""
        cursor = self.db.cursor()
        cursor.execute(
            """
            DELETE FROM sessions WHERE datetime(expires_at) < datetime(?)
        """,
            (datetime.now().isoformat(),),
        )

        deleted = cursor.rowcount
        self.db.commit()

        return deleted

    def generate_jwt_token(self, user: User) -> str:
        """JWTトークンを生成"""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            "iat": datetime.now(timezone.utc),
        }

        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def validate_jwt_token(self, token: str) -> Optional[User]:
        """JWTトークンを検証"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            # ユーザー情報を取得
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT username, email, role, is_active
                FROM users WHERE id = ?
            """,
                (payload["user_id"],),
            )

            row = cursor.fetchone()
            if not row or not row["is_active"]:
                return None

            user = User(row["username"], row["email"], row["role"])
            user.id = payload["user_id"]
            user.is_active = bool(row["is_active"])

            return user

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
            return None


def LoginRequired(auth_manager: AuthManager):
    """ログイン必須デコレーター"""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 認証トークンを取得
            token = None
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
            elif "auth_token" in request.cookies:
                token = request.cookies.get("auth_token")

            if not token:
                raise AuthenticationError("Authentication required")

            # トークン検証
            if auth_manager.use_jwt:
                user = auth_manager.validate_jwt_token(token)
            else:
                user = auth_manager.validate_session(token)

            if not user:
                raise AuthenticationError("Invalid or expired token")

            # ユーザー情報を関数に渡す
            return f(user, *args, **kwargs)

        return wrapper

    return decorator


def RoleRequired(auth_manager: AuthManager, required_role: str):
    """特定ロール必須デコレーター"""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 認証トークンを取得
            token = None
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
            elif "auth_token" in request.cookies:
                token = request.cookies.get("auth_token")

            if not token:
                raise AuthenticationError("Authentication required")

            # トークン検証
            if auth_manager.use_jwt:
                user = auth_manager.validate_jwt_token(token)
            else:
                user = auth_manager.validate_session(token)

            if not user:
                raise AuthenticationError("Invalid or expired token")

            # ロールチェック
            if user.role != required_role:
                raise AuthorizationError(f"Role '{required_role}' required")

            # ユーザー情報を関数に渡す
            return f(user, *args, **kwargs)

        return wrapper

    return decorator
