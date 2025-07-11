from typing import List, Optional
from datetime import datetime
import hashlib
import secrets

class UserService:
    """ユーザー管理サービス"""

    def __init__(self):
        self.users = {}
        self.sessions = {}

    def create_user(self, username: str, email: str, password: str) -> dict:
        """ユーザー作成"""
        user_id = secrets.token_hex(16)
        password_hash = self._hash_password(password)

        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now(),
            "is_active": True
        }

        self.users[user_id] = user
        return self._sanitize_user(user)

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """ユーザー認証"""
        for user in self.users.values():
            if user["username"] == username:
                if self._verify_password(password, user["password_hash"]):
                    session_token = secrets.token_urlsafe(32)
                    self.sessions[session_token] = user["id"]
                    return session_token
        return None

    def get_user(self, user_id: str) -> Optional[dict]:
        """ユーザー取得"""
        user = self.users.get(user_id)
        return self._sanitize_user(user) if user else None

    def update_user(self, user_id: str, updates: dict) -> Optional[dict]:
        """ユーザー更新"""
        if user_id not in self.users:
            return None

        user = self.users[user_id]
        allowed_fields = ["username", "email"]

        for field in allowed_fields:
            if field in updates:
                user[field] = updates[field]

        user["updated_at"] = datetime.now()
        return self._sanitize_user(user)

    def delete_user(self, user_id: str) -> bool:
        """ユーザー削除"""
        if user_id in self.users:
            del self.users[user_id]
            # セッションも削除
            for token, uid in list(self.sessions.items()):
                if uid == user_id:
                    del self.sessions[token]
            return True
        return False

    def _hash_password(self, password: str) -> str:
        """パスワードハッシュ化"""
        salt = secrets.token_hex(16)
        pwdhash = hashlib.pbkdf2_hmac('sha256',
                                      password.encode('utf-8'),
                                      salt.encode('utf-8'),
                                      100000)
        return salt + pwdhash.hex()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """パスワード検証"""
        salt = password_hash[:32]
        stored_hash = password_hash[32:]
        pwdhash = hashlib.pbkdf2_hmac('sha256',
                                      password.encode('utf-8'),
                                      salt.encode('utf-8'),
                                      100000)
        return pwdhash.hex() == stored_hash

    def _sanitize_user(self, user: dict) -> dict:
        """ユーザー情報のサニタイズ"""
        if not user:
            return None
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"],
            "is_active": user["is_active"]
        }
