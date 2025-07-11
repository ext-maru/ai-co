#!/usr/bin/env python3
"""
Elder Flow Task Decomposer - タスク分解エンジン
Created: 2025-01-11
Author: Claude Elder
Version: 1.0.0

ユーザーの要求を自動的に並列実行可能なタスクに分解
"""

import re
import json
import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import ast

# タスク分解に必要なインポート
import sys
import os
sys.path.append(os.path.dirname(__file__))

from elder_flow_parallel_executor import (
    ServantType, TaskPriority, create_parallel_task, ServantTask
)


class TaskCategory(Enum):
    """タスクカテゴリー"""
    AUTHENTICATION = "authentication"  # 認証系
    API = "api"                       # API系
    DATABASE = "database"             # データベース系
    FRONTEND = "frontend"             # フロントエンド系
    BACKEND = "backend"              # バックエンド系
    TESTING = "testing"              # テスト系
    DOCUMENTATION = "documentation"   # ドキュメント系
    DEPLOYMENT = "deployment"        # デプロイメント系
    SECURITY = "security"            # セキュリティ系
    OPTIMIZATION = "optimization"    # 最適化系


@dataclass
class DecomposedTask:
    """分解されたタスク"""
    task_id: str
    category: TaskCategory
    description: str
    servant_type: ServantType
    command: str
    arguments: Dict[str, Any]
    dependencies: Set[str] = field(default_factory=set)
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_time: int = 60  # 推定時間（秒）


class TaskDecomposer:
    """タスク分解エンジン"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # パターンマッチング用キーワード
        self.patterns = {
            TaskCategory.AUTHENTICATION: [
                r"oauth", r"認証", r"auth", r"login", r"ログイン",
                r"jwt", r"token", r"session", r"sso"
            ],
            TaskCategory.API: [
                r"api", r"endpoint", r"rest", r"graphql", r"websocket",
                r"route", r"エンドポイント", r"ルート"
            ],
            TaskCategory.DATABASE: [
                r"database", r"db", r"データベース", r"model", r"モデル",
                r"migration", r"schema", r"スキーマ", r"orm"
            ],
            TaskCategory.FRONTEND: [
                r"frontend", r"ui", r"ux", r"フロントエンド", r"画面",
                r"react", r"vue", r"angular", r"component", r"コンポーネント"
            ],
            TaskCategory.BACKEND: [
                r"backend", r"server", r"バックエンド", r"サーバー",
                r"service", r"サービス", r"business logic", r"ビジネスロジック"
            ],
            TaskCategory.TESTING: [
                r"test", r"テスト", r"unit test", r"integration test",
                r"e2e", r"testing", r"coverage", r"カバレッジ"
            ],
            TaskCategory.DOCUMENTATION: [
                r"document", r"doc", r"ドキュメント", r"readme",
                r"api doc", r"仕様書", r"specification"
            ],
            TaskCategory.SECURITY: [
                r"security", r"セキュリティ", r"encryption", r"暗号化",
                r"vulnerability", r"脆弱性", r"penetration", r"pentest"
            ]
        }

        # タスクテンプレート
        self.task_templates = self._initialize_task_templates()

    def _initialize_task_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """タスクテンプレートの初期化"""
        return {
            "oauth2_implementation": [
                {
                    "id": "oauth_models",
                    "description": "OAuth2.0モデル定義",
                    "servant": ServantType.CODE_CRAFTSMAN,
                    "command": "create_file",
                    "template": "oauth_models"
                },
                {
                    "id": "oauth_provider",
                    "description": "OAuth2.0プロバイダー実装",
                    "servant": ServantType.CODE_CRAFTSMAN,
                    "command": "create_file",
                    "template": "oauth_provider",
                    "depends": ["oauth_models"]
                },
                {
                    "id": "oauth_api",
                    "description": "OAuth2.0 API エンドポイント",
                    "servant": ServantType.CODE_CRAFTSMAN,
                    "command": "create_file",
                    "template": "oauth_api",
                    "depends": ["oauth_provider"]
                },
                {
                    "id": "oauth_tests",
                    "description": "OAuth2.0テスト作成",
                    "servant": ServantType.TEST_GUARDIAN,
                    "command": "create_test",
                    "depends": ["oauth_api"]
                },
                {
                    "id": "oauth_security",
                    "description": "セキュリティチェック",
                    "servant": ServantType.QUALITY_INSPECTOR,
                    "command": "security_scan",
                    "depends": ["oauth_tests"],
                    "priority": TaskPriority.HIGH
                }
            ],
            "user_management": [
                {
                    "id": "user_model",
                    "description": "ユーザーモデル定義",
                    "servant": ServantType.CODE_CRAFTSMAN,
                    "command": "create_class",
                    "template": "user_model"
                },
                {
                    "id": "user_service",
                    "description": "ユーザーサービス実装",
                    "servant": ServantType.CODE_CRAFTSMAN,
                    "command": "create_file",
                    "template": "user_service",
                    "depends": ["user_model"]
                },
                {
                    "id": "user_api",
                    "description": "ユーザー管理API",
                    "servant": ServantType.CODE_CRAFTSMAN,
                    "command": "create_file",
                    "template": "user_api",
                    "depends": ["user_service"]
                },
                {
                    "id": "user_tests",
                    "description": "ユーザー管理テスト",
                    "servant": ServantType.TEST_GUARDIAN,
                    "command": "create_test",
                    "depends": ["user_api"]
                }
            ],
            "api_authentication": [
                {
                    "id": "auth_middleware",
                    "description": "認証ミドルウェア",
                    "servant": ServantType.CODE_CRAFTSMAN,
                    "command": "create_file",
                    "template": "auth_middleware"
                },
                {
                    "id": "jwt_handler",
                    "description": "JWT処理実装",
                    "servant": ServantType.CODE_CRAFTSMAN,
                    "command": "create_file",
                    "template": "jwt_handler"
                },
                {
                    "id": "auth_decorator",
                    "description": "認証デコレーター",
                    "servant": ServantType.CODE_CRAFTSMAN,
                    "command": "implement_function",
                    "template": "auth_decorator",
                    "depends": ["jwt_handler"]
                }
            ]
        }

    def decompose_request(self, request: str) -> List[DecomposedTask]:
        """ユーザーリクエストをタスクに分解"""
        self.logger.info(f"🔍 Decomposing request: {request}")

        # カテゴリー識別
        categories = self._identify_categories(request)

        # キーワード抽出
        keywords = self._extract_keywords(request)

        # タスク生成
        tasks = self._generate_tasks(request, categories, keywords)

        # 依存関係の最適化
        tasks = self._optimize_dependencies(tasks)

        # 優先度の調整
        tasks = self._adjust_priorities(tasks)

        self.logger.info(f"📦 Decomposed into {len(tasks)} tasks")
        return tasks

    def _identify_categories(self, request: str) -> Set[TaskCategory]:
        """リクエストからカテゴリーを識別"""
        categories = set()
        request_lower = request.lower()

        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, request_lower):
                    categories.add(category)
                    break

        # デフォルトカテゴリー
        if not categories:
            categories.add(TaskCategory.BACKEND)

        return categories

    def _extract_keywords(self, request: str) -> Dict[str, List[str]]:
        """重要なキーワードを抽出"""
        keywords = {
            "features": [],
            "technologies": [],
            "actions": []
        }

        # 機能キーワード
        feature_patterns = [
            r"実装|implement", r"作成|create", r"追加|add",
            r"修正|fix", r"改善|improve", r"最適化|optimize"
        ]

        # 技術キーワード
        tech_patterns = [
            r"oauth2?\.?0?", r"jwt", r"api", r"rest", r"graphql",
            r"database", r"postgresql", r"mysql", r"mongodb",
            r"react", r"vue", r"angular", r"django", r"flask", r"fastapi"
        ]

        request_lower = request.lower()

        for pattern in feature_patterns:
            matches = re.findall(pattern, request_lower)
            keywords["features"].extend(matches)

        for pattern in tech_patterns:
            matches = re.findall(pattern, request_lower, re.IGNORECASE)
            keywords["technologies"].extend(matches)

        return keywords

    def _generate_tasks(self, request: str, categories: Set[TaskCategory],
                       keywords: Dict[str, List[str]]) -> List[DecomposedTask]:
        """タスクを生成"""
        tasks = []
        task_counter = 0

        # テンプレートベースのタスク生成
        if "oauth" in request.lower():
            tasks.extend(self._create_tasks_from_template("oauth2_implementation", task_counter))
            task_counter += len(self.task_templates["oauth2_implementation"])

        if "ユーザー管理" in request or "user management" in request.lower():
            tasks.extend(self._create_tasks_from_template("user_management", task_counter))
            task_counter += len(self.task_templates["user_management"])

        if "api認証" in request or "api authentication" in request.lower():
            tasks.extend(self._create_tasks_from_template("api_authentication", task_counter))
            task_counter += len(self.task_templates["api_authentication"])

        # カテゴリーベースの追加タスク
        for category in categories:
            if category == TaskCategory.TESTING and not any(t.category == TaskCategory.TESTING for t in tasks):
                tasks.append(self._create_test_task(f"test_{task_counter}", request))
                task_counter += 1

            if category == TaskCategory.DOCUMENTATION and not any(t.category == TaskCategory.DOCUMENTATION for t in tasks):
                tasks.append(self._create_doc_task(f"doc_{task_counter}", request))
                task_counter += 1

        # タスクが無い場合のフォールバック
        if not tasks:
            tasks = self._create_generic_tasks(request, task_counter)

        return tasks

    def _create_tasks_from_template(self, template_name: str,
                                   start_counter: int) -> List[DecomposedTask]:
        """テンプレートからタスクを作成"""
        tasks = []
        template = self.task_templates.get(template_name, [])

        for i, task_template in enumerate(template):
            task_id = f"{template_name}_{start_counter + i}"

            # カテゴリーの決定
            if "test" in task_template["id"]:
                category = TaskCategory.TESTING
            elif "api" in task_template["id"]:
                category = TaskCategory.API
            elif "security" in task_template["id"]:
                category = TaskCategory.SECURITY
            else:
                category = TaskCategory.BACKEND

            # 引数の生成
            arguments = self._generate_task_arguments(task_template)

            # 依存関係の解決
            dependencies = set()
            if "depends" in task_template:
                for dep in task_template["depends"]:
                    dependencies.add(f"{template_name}_{start_counter + self._find_template_index(template, dep)}")

            task = DecomposedTask(
                task_id=task_id,
                category=category,
                description=task_template["description"],
                servant_type=task_template["servant"],
                command=task_template["command"],
                arguments=arguments,
                dependencies=dependencies,
                priority=task_template.get("priority", TaskPriority.MEDIUM)
            )

            tasks.append(task)

        return tasks

    def _find_template_index(self, template: List[Dict], task_id: str) -> int:
        """テンプレート内のタスクインデックスを検索"""
        for i, t in enumerate(template):
            if t["id"] == task_id:
                return i
        return 0

    def _generate_task_arguments(self, task_template: Dict[str, Any]) -> Dict[str, Any]:
        """タスクの引数を生成"""
        command = task_template["command"]
        template_type = task_template.get("template", "")

        if command == "create_file":
            return self._generate_file_creation_args(template_type)
        elif command == "create_class":
            return self._generate_class_creation_args(template_type)
        elif command == "create_test":
            return self._generate_test_creation_args(template_type)
        elif command == "implement_function":
            return self._generate_function_args(template_type)
        else:
            return {}

    def _generate_file_creation_args(self, template_type: str) -> Dict[str, Any]:
        """ファイル作成の引数生成"""
        file_templates = {
            "oauth_models": {
                "file_path": "output/src/auth/models.py",
                "content": '''from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class OAuthClient:
    """OAuth2.0クライアント"""
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    allowed_scopes: List[str]
    client_name: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class OAuthToken:
    """OAuth2.0トークン"""
    access_token: str
    refresh_token: Optional[str]
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str = ""
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AuthorizationCode:
    """認可コード"""
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scope: str
    expires_at: datetime
    used: bool = False
'''
            },
            "oauth_provider": {
                "file_path": "output/src/auth/oauth_provider.py",
                "content": '''import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from .models import OAuthClient, OAuthToken, AuthorizationCode

class OAuth2Provider:
    """OAuth2.0プロバイダー実装"""

    def __init__(self):
        self.clients: Dict[str, OAuthClient] = {}
        self.tokens: Dict[str, OAuthToken] = {}
        self.auth_codes: Dict[str, AuthorizationCode] = {}

    def register_client(self, client: OAuthClient) -> None:
        """クライアント登録"""
        self.clients[client.client_id] = client

    def generate_authorization_code(self, client_id: str, user_id: str,
                                  redirect_uri: str, scope: str) -> str:
        """認可コード生成"""
        code = secrets.token_urlsafe(32)
        auth_code = AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            scope=scope,
            expires_at=datetime.now() + timedelta(minutes=10)
        )
        self.auth_codes[code] = auth_code
        return code

    def exchange_code_for_token(self, code: str, client_id: str,
                               client_secret: str) -> Optional[OAuthToken]:
        """認可コードをトークンに交換"""
        if code not in self.auth_codes:
            return None

        auth_code = self.auth_codes[code]
        if auth_code.used or auth_code.expires_at < datetime.now():
            return None

        client = self.clients.get(client_id)
        if not client or client.client_secret != client_secret:
            return None

        # トークン生成
        token = OAuthToken(
            access_token=secrets.token_urlsafe(32),
            refresh_token=secrets.token_urlsafe(32),
            expires_in=3600,
            scope=auth_code.scope
        )

        auth_code.used = True
        self.tokens[token.access_token] = token
        return token

    def validate_token(self, access_token: str) -> bool:
        """トークン検証"""
        token = self.tokens.get(access_token)
        if not token:
            return False

        expires_at = token.created_at + timedelta(seconds=token.expires_in)
        return datetime.now() < expires_at
'''
            },
            "oauth_api": {
                "file_path": "src/auth/api.py",
                "content": '''from flask import Flask, request, jsonify, redirect
from urllib.parse import urlencode
from .oauth_provider import OAuth2Provider
from .models import OAuthClient

app = Flask(__name__)
oauth_provider = OAuth2Provider()

@app.route('/oauth/authorize', methods=['GET'])
def authorize():
    """認可エンドポイント"""
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    response_type = request.args.get('response_type')
    scope = request.args.get('scope', '')
    state = request.args.get('state', '')

    # クライアント検証
    client = oauth_provider.clients.get(client_id)
    if not client:
        return jsonify({"error": "invalid_client"}), 400

    if redirect_uri not in client.redirect_uris:
        return jsonify({"error": "invalid_redirect_uri"}), 400

    # ユーザー認証（簡略化）
    user_id = "authenticated_user"

    # 認可コード生成
    code = oauth_provider.generate_authorization_code(
        client_id, user_id, redirect_uri, scope
    )

    # リダイレクト
    params = {"code": code}
    if state:
        params["state"] = state

    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    return redirect(redirect_url)

@app.route('/oauth/token', methods=['POST'])
def token():
    """トークンエンドポイント"""
    grant_type = request.form.get('grant_type')

    if grant_type == 'authorization_code':
        code = request.form.get('code')
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')

        token = oauth_provider.exchange_code_for_token(
            code, client_id, client_secret
        )

        if not token:
            return jsonify({"error": "invalid_grant"}), 400

        return jsonify({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "token_type": token.token_type,
            "expires_in": token.expires_in,
            "scope": token.scope
        })

    return jsonify({"error": "unsupported_grant_type"}), 400

@app.route('/api/user', methods=['GET'])
def get_user():
    """保護されたリソース"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"error": "invalid_token"}), 401

    token = auth_header[7:]
    if not oauth_provider.validate_token(token):
        return jsonify({"error": "invalid_token"}), 401

    return jsonify({
        "id": "user123",
        "name": "Test User",
        "email": "user@example.com"
    })
'''
            },
            "user_service": {
                "file_path": "src/users/service.py",
                "content": '''from typing import List, Optional
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
'''
            },
            "auth_middleware": {
                "file_path": "src/middleware/auth.py",
                "content": '''from functools import wraps
from flask import request, jsonify
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-here"

def create_jwt_token(user_id: str, expires_in: int = 3600) -> str:
    """JWTトークン生成"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(seconds=expires_in),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_jwt_token(token: str) -> dict:
    """JWTトークン検証"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """認証必須デコレーター"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({"error": "No authorization header"}), 401

        try:
            # Bearer トークンの抽出
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)

            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            # リクエストにユーザー情報を追加
            request.current_user = payload

        except Exception as e:
            return jsonify({"error": "Invalid authorization header"}), 401

        return f(*args, **kwargs)

    return decorated_function

def require_roles(*roles):
    """ロール必須デコレーター"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # まず認証チェック
            auth_result = require_auth(lambda: None)()
            if auth_result:
                return auth_result

            # ロールチェック
            user_roles = request.current_user.get('roles', [])
            if not any(role in user_roles for role in roles):
                return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
'''
            }
        }

        return file_templates.get(template_type, {
            "file_path": f"src/{template_type}.py",
            "content": "# Auto-generated file"
        })

    def _generate_class_creation_args(self, template_type: str) -> Dict[str, Any]:
        """クラス作成の引数生成"""
        class_templates = {
            "user_model": {
                "class_name": "User",
                "base_classes": ["BaseModel"],
                "attributes": ["id", "username", "email", "password_hash", "created_at", "updated_at"],
                "methods": ["save", "delete", "update", "to_dict", "from_dict"]
            }
        }

        return class_templates.get(template_type, {
            "class_name": "GeneratedClass",
            "attributes": ["id"],
            "methods": ["__init__"]
        })

    def _generate_test_creation_args(self, template_type: str) -> Dict[str, Any]:
        """テスト作成の引数生成"""
        # テンプレートタイプから対象モジュールを推定
        target_map = {
            "oauth": "src.auth.oauth_provider",
            "user": "src.users.service",
            "api": "src.auth.api"
        }

        target_module = "src.main"
        for key, value in target_map.items():
            if key in template_type:
                target_module = value
                break

        return {
            "test_file": f"tests/test_{template_type}.py",
            "target_module": target_module,
            "test_cases": [
                {
                    "name": "test_creation",
                    "description": "作成テスト",
                    "code": "assert True  # TODO: Implement"
                },
                {
                    "name": "test_validation",
                    "description": "検証テスト",
                    "code": "assert True  # TODO: Implement"
                },
                {
                    "name": "test_error_handling",
                    "description": "エラー処理テスト",
                    "code": "assert True  # TODO: Implement"
                }
            ]
        }

    def _generate_function_args(self, template_type: str) -> Dict[str, Any]:
        """関数実装の引数生成"""
        function_templates = {
            "auth_decorator": {
                "function_name": "require_token",
                "parameters": ["f"],
                "return_type": "Callable",
                "docstring": "トークン認証を要求するデコレーター",
                "body": '''@wraps(f)
def decorated(*args, **kwargs):
    token = request.headers.get('X-Auth-Token')
    if not token or not validate_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    return f(*args, **kwargs)
return decorated'''
            }
        }

        return function_templates.get(template_type, {
            "function_name": "generated_function",
            "parameters": [],
            "return_type": "Any",
            "body": "pass"
        })

    def _create_test_task(self, task_id: str, request: str) -> DecomposedTask:
        """汎用テストタスク作成"""
        return DecomposedTask(
            task_id=task_id,
            category=TaskCategory.TESTING,
            description="統合テスト作成",
            servant_type=ServantType.TEST_GUARDIAN,
            command="create_test",
            arguments={
                "test_file": "tests/test_integration.py",
                "target_module": "src.main",
                "test_cases": [
                    {"name": "test_integration", "code": "assert True"}
                ]
            }
        )

    def _create_doc_task(self, task_id: str, request: str) -> DecomposedTask:
        """汎用ドキュメントタスク作成"""
        return DecomposedTask(
            task_id=task_id,
            category=TaskCategory.DOCUMENTATION,
            description="ドキュメント生成",
            servant_type=ServantType.DOCUMENTATION_SCRIBE,
            command="create_readme",
            arguments={
                "project_name": "Generated Project",
                "description": f"Auto-generated from: {request[:50]}...",
                "sections": [
                    {"title": "Installation", "content": "pip install -r requirements.txt"},
                    {"title": "Usage", "content": "See documentation"}
                ]
            }
        )

    def _create_generic_tasks(self, request: str, start_counter: int) -> List[DecomposedTask]:
        """汎用タスク作成（フォールバック）"""
        tasks = []

        # 基本的な実装タスク
        tasks.append(DecomposedTask(
            task_id=f"generic_impl_{start_counter}",
            category=TaskCategory.BACKEND,
            description="基本実装",
            servant_type=ServantType.CODE_CRAFTSMAN,
            command="create_file",
            arguments={
                "file_path": "src/main.py",
                "content": "# Implementation based on: " + request[:100]
            }
        ))

        # テスト
        tasks.append(DecomposedTask(
            task_id=f"generic_test_{start_counter + 1}",
            category=TaskCategory.TESTING,
            description="テスト作成",
            servant_type=ServantType.TEST_GUARDIAN,
            command="create_test",
            arguments={
                "test_file": "tests/test_main.py",
                "target_module": "src.main",
                "test_cases": [{"name": "test_basic", "code": "assert True"}]
            },
            dependencies={f"generic_impl_{start_counter}"}
        ))

        return tasks

    def _optimize_dependencies(self, tasks: List[DecomposedTask]) -> List[DecomposedTask]:
        """依存関係の最適化"""
        # 依存関係グラフの構築
        task_map = {task.task_id: task for task in tasks}

        # 循環依存のチェック
        for task in tasks:
            if self._has_circular_dependency(task, task_map, set()):
                self.logger.warning(f"Circular dependency detected for {task.task_id}")
                task.dependencies.clear()

        return tasks

    def _has_circular_dependency(self, task: DecomposedTask,
                                task_map: Dict[str, DecomposedTask],
                                visited: Set[str]) -> bool:
        """循環依存のチェック"""
        if task.task_id in visited:
            return True

        visited.add(task.task_id)

        for dep_id in task.dependencies:
            if dep_id in task_map:
                if self._has_circular_dependency(task_map[dep_id], task_map, visited.copy()):
                    return True

        return False

    def _adjust_priorities(self, tasks: List[DecomposedTask]) -> List[DecomposedTask]:
        """優先度の調整"""
        for task in tasks:
            # セキュリティ関連は最高優先度
            if task.category == TaskCategory.SECURITY:
                task.priority = TaskPriority.CRITICAL

            # テストは高優先度
            elif task.category == TaskCategory.TESTING:
                task.priority = TaskPriority.HIGH

            # 依存されているタスクは優先度を上げる
            dep_count = sum(1 for t in tasks if task.task_id in t.dependencies)
            if dep_count > 2:
                task.priority = TaskPriority.HIGH

        return tasks

    def convert_to_servant_tasks(self, decomposed_tasks: List[DecomposedTask]) -> List[ServantTask]:
        """分解されたタスクをServantTaskに変換"""
        servant_tasks = []

        for task in decomposed_tasks:
            servant_task = create_parallel_task(
                task_id=task.task_id,
                servant_type=task.servant_type,
                command=task.command,
                dependencies=task.dependencies,
                priority=task.priority,
                **task.arguments
            )
            servant_tasks.append(servant_task)

        return servant_tasks

    def visualize_task_graph(self, tasks: List[DecomposedTask]) -> str:
        """タスクグラフの可視化"""
        graph = "Task Decomposition Graph\n"
        graph += "=" * 50 + "\n\n"

        # カテゴリー別にグループ化
        by_category = {}
        for task in tasks:
            if task.category not in by_category:
                by_category[task.category] = []
            by_category[task.category].append(task)

        # カテゴリーごとに表示
        for category, category_tasks in by_category.items():
            graph += f"\n📦 {category.value.upper()}\n"
            graph += "-" * 30 + "\n"

            for task in category_tasks:
                priority_icon = {
                    TaskPriority.CRITICAL: "🔴",
                    TaskPriority.HIGH: "🟡",
                    TaskPriority.MEDIUM: "🟢",
                    TaskPriority.LOW: "🔵"
                }.get(task.priority, "⚪")

                graph += f"{priority_icon} {task.task_id}: {task.description}\n"

                if task.dependencies:
                    for dep in task.dependencies:
                        graph += f"   └─> {dep}\n"

        return graph


# Example usage
if __name__ == "__main__":
    decomposer = TaskDecomposer()

    # テストリクエスト
    test_requests = [
        "OAuth2.0認証システムを実装してください",
        "ユーザー管理機能とAPI認証を追加",
        "RESTful APIをセキュアに実装"
    ]

    for request in test_requests:
        print(f"\n🔍 Request: {request}")
        print("=" * 60)

        # タスク分解
        tasks = decomposer.decompose_request(request)

        # グラフ表示
        print(decomposer.visualize_task_graph(tasks))

        # サーバントタスクに変換
        servant_tasks = decomposer.convert_to_servant_tasks(tasks)
        print(f"\n✅ Generated {len(servant_tasks)} servant tasks")
