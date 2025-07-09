#!/usr/bin/env python3
"""
エンタープライズ認証・認可システム
JWT + OAuth2.0 + RBAC 実装
"""

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import jwt
from functools import wraps

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, Blueprint, jsonify, request, g
from werkzeug.security import generate_password_hash, check_password_hash

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint作成
auth_api = Blueprint('auth_api', __name__, url_prefix='/api/auth')

# 設定
JWT_SECRET_KEY = secrets.token_urlsafe(32)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

class UserManager:
    """ユーザー管理システム"""
    
    def __init__(self):
        # モックユーザーデータ
        self.users = {
            "admin@ai-company.com": {
                "id": "user_001",
                "email": "admin@ai-company.com",
                "name": "Admin User",
                "password_hash": generate_password_hash("admin123"),
                "roles": ["admin", "user"],
                "permissions": ["all"],
                "created_at": "2025-01-01T00:00:00Z",
                "last_login": None
            },
            "developer@ai-company.com": {
                "id": "user_002",
                "email": "developer@ai-company.com",
                "name": "Developer User",
                "password_hash": generate_password_hash("dev123"),
                "roles": ["developer", "user"],
                "permissions": ["read", "write", "deploy"],
                "created_at": "2025-01-15T00:00:00Z",
                "last_login": None
            },
            "viewer@ai-company.com": {
                "id": "user_003",
                "email": "viewer@ai-company.com",
                "name": "Viewer User",
                "password_hash": generate_password_hash("view123"),
                "roles": ["viewer"],
                "permissions": ["read"],
                "created_at": "2025-02-01T00:00:00Z",
                "last_login": None
            }
        }
    
    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """ユーザー認証"""
        user = self.users.get(email)
        if user and check_password_hash(user["password_hash"], password):
            # パスワードハッシュを除外してユーザー情報を返す
            user_data = {k: v for k, v in user.items() if k != "password_hash"}
            user_data["last_login"] = datetime.now().isoformat()
            return user_data
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """IDによるユーザー取得"""
        for user in self.users.values():
            if user["id"] == user_id:
                return {k: v for k, v in user.items() if k != "password_hash"}
        return None
    
    def create_user(self, email: str, name: str, password: str, roles: List[str]) -> Dict[str, Any]:
        """新規ユーザー作成"""
        if email in self.users:
            raise ValueError("User already exists")
        
        user_id = f"user_{len(self.users) + 1:03d}"
        permissions = self._get_permissions_for_roles(roles)
        
        self.users[email] = {
            "id": user_id,
            "email": email,
            "name": name,
            "password_hash": generate_password_hash(password),
            "roles": roles,
            "permissions": permissions,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        return {
            "id": user_id,
            "email": email,
            "name": name,
            "roles": roles,
            "permissions": permissions
        }
    
    def _get_permissions_for_roles(self, roles: List[str]) -> List[str]:
        """ロールに基づく権限取得"""
        role_permissions = {
            "admin": ["all"],
            "developer": ["read", "write", "deploy"],
            "viewer": ["read"],
            "user": ["read", "write"]
        }
        
        permissions = set()
        for role in roles:
            if role in role_permissions:
                permissions.update(role_permissions[role])
        
        return list(permissions)

class RBACManager:
    """ロールベースアクセス制御 (RBAC)"""
    
    def __init__(self):
        # ロール定義
        self.roles = {
            "admin": {
                "name": "Administrator",
                "description": "Full system access",
                "permissions": ["all"],
                "inherits": []
            },
            "developer": {
                "name": "Developer",
                "description": "Development and deployment access",
                "permissions": ["read", "write", "deploy", "debug"],
                "inherits": ["user"]
            },
            "viewer": {
                "name": "Viewer",
                "description": "Read-only access",
                "permissions": ["read"],
                "inherits": []
            },
            "user": {
                "name": "Standard User",
                "description": "Basic user access",
                "permissions": ["read", "write"],
                "inherits": ["viewer"]
            }
        }
        
        # リソース権限マッピング
        self.resource_permissions = {
            "sages": ["read", "write", "admin"],
            "webhooks": ["read", "write", "admin"],
            "integrations": ["read", "write", "admin"],
            "users": ["read", "admin"],
            "logs": ["read", "admin"],
            "settings": ["read", "write", "admin"]
        }
    
    def check_permission(self, user_roles: List[str], resource: str, action: str) -> bool:
        """権限チェック"""
        # admin は全権限を持つ
        if "admin" in user_roles:
            return True
        
        # ユーザーの全権限を収集
        user_permissions = set()
        for role in user_roles:
            if role in self.roles:
                user_permissions.update(self.roles[role]["permissions"])
                # 継承されたロールの権限も追加
                for inherited in self.roles[role]["inherits"]:
                    if inherited in self.roles:
                        user_permissions.update(self.roles[inherited]["permissions"])
        
        # リソースに対する権限チェック
        if resource in self.resource_permissions:
            required_permission = f"{resource}:{action}"
            return action in user_permissions or "all" in user_permissions
        
        return False
    
    def get_user_permissions(self, user_roles: List[str]) -> Dict[str, List[str]]:
        """ユーザーの全権限取得"""
        permissions = {}
        
        for resource in self.resource_permissions:
            resource_perms = []
            for action in ["read", "write", "admin"]:
                if self.check_permission(user_roles, resource, action):
                    resource_perms.append(action)
            if resource_perms:
                permissions[resource] = resource_perms
        
        return permissions

class SecurityAuditLogger:
    """セキュリティ監査ログ"""
    
    def __init__(self):
        self.audit_logs = []
    
    def log_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """監査イベントログ記録"""
        log_entry = {
            "id": f"audit_{len(self.audit_logs) + 1:06d}",
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "ip_address": request.remote_addr if request else "system",
            "user_agent": request.headers.get('User-Agent', 'system') if request else "system"
        }
        
        self.audit_logs.append(log_entry)
        logger.info(f"Security audit: {event_type} by {user_id}")
        
        # 実際の実装では永続化する
        return log_entry
    
    def get_audit_logs(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """監査ログ取得"""
        logs = self.audit_logs
        
        if filters:
            if "event_type" in filters:
                logs = [l for l in logs if l["event_type"] == filters["event_type"]]
            if "user_id" in filters:
                logs = [l for l in logs if l["user_id"] == filters["user_id"]]
            if "start_date" in filters:
                logs = [l for l in logs if l["timestamp"] >= filters["start_date"]]
            if "end_date" in filters:
                logs = [l for l in logs if l["timestamp"] <= filters["end_date"]]
        
        return logs

# マネージャーインスタンス
user_manager = UserManager()
rbac_manager = RBACManager()
audit_logger = SecurityAuditLogger()

# JWT トークン生成・検証
def generate_jwt_token(user_data: Dict[str, Any]) -> str:
    """JWTトークン生成"""
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "roles": user_data["roles"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """JWTトークン検証"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None

# 認証デコレーター
def require_auth(f):
    """認証必須デコレーター"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authorization required"}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # ユーザー情報をgオブジェクトに保存
        g.current_user = payload
        return f(*args, **kwargs)
    
    return decorated_function

def require_permission(resource: str, action: str):
    """権限必須デコレーター"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({"error": "Authentication required"}), 401
            
            user_roles = g.current_user.get('roles', [])
            
            if not rbac_manager.check_permission(user_roles, resource, action):
                audit_logger.log_event("permission_denied", g.current_user['user_id'], {
                    "resource": resource,
                    "action": action,
                    "roles": user_roles
                })
                return jsonify({"error": "Permission denied"}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# API エンドポイント

@auth_api.route('/login', methods=['POST'])
def login():
    """ユーザーログイン"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        user = user_manager.authenticate(email, password)
        
        if not user:
            audit_logger.log_event("login_failed", email, {"reason": "invalid_credentials"})
            return jsonify({"error": "Invalid credentials"}), 401
        
        # JWTトークン生成
        token = generate_jwt_token(user)
        
        # 監査ログ
        audit_logger.log_event("login_success", user["id"], {"email": email})
        
        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "roles": user["roles"]
            },
            "expires_in": JWT_EXPIRATION_HOURS * 3600
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/logout', methods=['POST'])
@require_auth
def logout():
    """ユーザーログアウト"""
    try:
        user_id = g.current_user['user_id']
        audit_logger.log_event("logout", user_id, {})
        
        # 実際の実装ではトークンをブラックリストに追加
        return jsonify({
            "success": True,
            "message": "Logged out successfully"
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/me')
@require_auth
def get_current_user():
    """現在のユーザー情報取得"""
    try:
        user_id = g.current_user['user_id']
        user = user_manager.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # ユーザーの権限情報を追加
        user["permissions"] = rbac_manager.get_user_permissions(user["roles"])
        
        return jsonify({
            "success": True,
            "user": user
        })
        
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/users', methods=['POST'])
@require_auth
@require_permission('users', 'admin')
def create_user():
    """新規ユーザー作成（管理者のみ）"""
    try:
        data = request.json
        email = data.get('email')
        name = data.get('name')
        password = data.get('password')
        roles = data.get('roles', ['user'])
        
        if not all([email, name, password]):
            return jsonify({"error": "Email, name, and password required"}), 400
        
        user = user_manager.create_user(email, name, password, roles)
        
        audit_logger.log_event("user_created", g.current_user['user_id'], {
            "new_user_id": user["id"],
            "email": email,
            "roles": roles
        })
        
        return jsonify({
            "success": True,
            "user": user
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/audit/logs')
@require_auth
@require_permission('logs', 'read')
def get_audit_logs():
    """監査ログ取得"""
    try:
        filters = {}
        
        if request.args.get('event_type'):
            filters['event_type'] = request.args.get('event_type')
        if request.args.get('user_id'):
            filters['user_id'] = request.args.get('user_id')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        logs = audit_logger.get_audit_logs(filters)
        
        return jsonify({
            "success": True,
            "logs": logs,
            "count": len(logs)
        })
        
    except Exception as e:
        logger.error(f"Get audit logs error: {e}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/roles')
@require_auth
def get_roles():
    """利用可能なロール一覧"""
    try:
        roles = []
        for role_id, role_data in rbac_manager.roles.items():
            roles.append({
                "id": role_id,
                "name": role_data["name"],
                "description": role_data["description"],
                "permissions": role_data["permissions"]
            })
        
        return jsonify({
            "success": True,
            "roles": roles
        })
        
    except Exception as e:
        logger.error(f"Get roles error: {e}")
        return jsonify({"error": str(e)}), 500

@auth_api.route('/permissions/check', methods=['POST'])
@require_auth
def check_permission():
    """権限チェック"""
    try:
        data = request.json
        resource = data.get('resource')
        action = data.get('action')
        
        if not resource or not action:
            return jsonify({"error": "Resource and action required"}), 400
        
        user_roles = g.current_user.get('roles', [])
        has_permission = rbac_manager.check_permission(user_roles, resource, action)
        
        return jsonify({
            "success": True,
            "has_permission": has_permission,
            "user_roles": user_roles,
            "resource": resource,
            "action": action
        })
        
    except Exception as e:
        logger.error(f"Check permission error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # テスト用実行
    app = Flask(__name__)
    app.register_blueprint(auth_api)
    
    # テストログイン
    print("=== 認証システムテスト ===")
    print("テストユーザー:")
    print("- admin@ai-company.com / admin123")
    print("- developer@ai-company.com / dev123")
    print("- viewer@ai-company.com / view123")
    
    app.run(debug=True, port=5003)