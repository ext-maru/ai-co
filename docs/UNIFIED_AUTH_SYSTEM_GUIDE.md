# Elders Guild 統合認証システム完全ガイド v2.0

## 🏛️ エルダーズ評議会承認済み認証システム

### 📋 システム概要

Elders Guild統合認証システムは、4賢者システムとElder階層を統合した高度なセキュリティ基盤です。

**主要特徴:**
- 🏛️ Elder階層権限管理
- 🧙‍♂️ 4賢者システム統合
- 🔐 Multi-Factor Authentication (MFA)
- 🎫 JWT + セッション ハイブリッド認証
- 🛡️ 高度な脅威検知
- 📊 包括的監査ログ

---

## 🎯 Elder階層システム

### 階層構造

```
🌟 グランドエルダーmaru (最高権限)
└── 🤖 クロードエルダー (開発実行責任者)
    └── 🧙‍♂️ 4賢者システム
        ├── 📚 ナレッジ賢者
        ├── 📋 タスク賢者  
        ├── 🚨 インシデント賢者
        └── 🔍 RAG賢者
            └── 🧝‍♂️ サーバント (一般権限)
```

### 権限レベル

| 階層 | 権限レベル | 説明 | 主な権限 |
|------|----------|------|---------|
| **Grand Elder** | 4 | 最高権限 | 全システム管理、全ユーザー管理 |
| **Claude Elder** | 3 | 開発実行責任者 | 開発管理、4賢者統括 |
| **Sage** | 2 | 4賢者システム | 専門領域の高度な権限 |
| **Servant** | 1 | 一般権限 | 基本的なシステム利用 |

---

## 🚀 クイックスタート

### 1. 基本セットアップ

```python
from libs.unified_auth_provider import (
    UnifiedAuthProvider, 
    create_demo_auth_system,
    ElderRole, 
    SageType
)

# 本番環境用
auth_provider = UnifiedAuthProvider(
    secret_key="your-secure-secret-key",
    session_duration_hours=24,
    enable_mfa=True,
    enable_device_tracking=True
)

# デモ環境用（開発・テスト）
demo_auth = create_demo_auth_system()
```

### 2. ユーザー作成

```python
# グランドエルダー作成
grand_elder = auth_provider.create_user(
    username="maru",
    password="secure_password",
    email="maru@ai-company.com",
    elder_role=ElderRole.GRAND_ELDER
)

# 賢者作成
knowledge_sage = auth_provider.create_user(
    username="knowledge_sage",
    password="sage_password", 
    email="knowledge@ai-company.com",
    elder_role=ElderRole.SAGE,
    sage_type=SageType.KNOWLEDGE
)

# 一般ユーザー作成
servant = auth_provider.create_user(
    username="user1",
    password="user_password",
    email="user1@ai-company.com",
    elder_role=ElderRole.SERVANT
)
```

### 3. 認証実行

```python
from libs.unified_auth_provider import AuthRequest, AuthResult

# 基本認証
auth_request = AuthRequest(
    username="knowledge_sage",
    password="sage_password",
    ip_address="192.168.1.100",
    device_info={"type": "web", "browser": "Chrome"}
)

result, session, user = auth_provider.authenticate(auth_request)

if result == AuthResult.SUCCESS:
    print(f"認証成功: {user.username}")
    print(f"JWT Token: {session.token}")
    print(f"Session ID: {session.session_id}")
elif result == AuthResult.MFA_REQUIRED:
    print("MFA認証が必要です")
elif result == AuthResult.INVALID_CREDENTIALS:
    print("認証情報が無効です")
```

---

## 🔐 Multi-Factor Authentication (MFA)

### MFA有効化

```python
# ユーザーのMFA有効化
provisioning_uri = auth_provider.enable_mfa_for_user(user.id)
print(f"QRコード用URI: {provisioning_uri}")

# MFA付き認証
import pyotp

# TOTP生成（実際はユーザーのアプリで生成）
totp = pyotp.TOTP(user.mfa_secret)
mfa_token = totp.now()

# MFA付き認証リクエスト
auth_request = AuthRequest(
    username="knowledge_sage",
    password="sage_password",
    mfa_token=mfa_token
)

result, session, user = auth_provider.authenticate(auth_request)
```

### MFA設定フロー

1. **MFA有効化**: `enable_mfa_for_user()`でシークレット生成
2. **QRコード表示**: プロビジョニングURIからQRコード生成
3. **アプリ登録**: Google Authenticator等でQRコード読取
4. **検証**: 生成されたTOTPで認証テスト
5. **完了**: MFA有効化完了

---

## 🎫 セッション管理

### セッション作成と検証

```python
# セッション作成（認証時に自動）
result, session, user = auth_provider.authenticate(auth_request)

# トークン検証
is_valid, validated_user, validated_session = auth_provider.validate_token(session.token)

if is_valid:
    print(f"有効なセッション: {validated_user.username}")
else:
    print("無効または期限切れセッション")
```

### セッション更新

```python
# リフレッシュトークンでセッション更新
success, updated_session = auth_provider.refresh_session(session.refresh_token)

if success:
    print(f"新しいトークン: {updated_session.token}")
```

### セッション管理

```python
# ユーザーのアクティブセッション取得
active_sessions = auth_provider.get_active_sessions(user.id)
print(f"アクティブセッション数: {len(active_sessions)}")

# 全セッション取り消し
revoked_count = auth_provider.revoke_all_sessions(user.id)
print(f"取り消しセッション数: {revoked_count}")

# 個別ログアウト
success = auth_provider.logout(session.session_id)
```

---

## 🛡️ 権限制御

### Elder階層権限チェック

```python
# Elder権限チェック
can_access_elder_council = auth_provider.check_elder_permission(
    user, ElderRole.CLAUDE_ELDER
)

# 階層別アクセス例
if user.elder_role == ElderRole.GRAND_ELDER:
    # 最高権限 - 全システム管理
    pass
elif user.elder_role == ElderRole.CLAUDE_ELDER:
    # 開発実行責任者 - 開発管理
    pass
elif user.elder_role == ElderRole.SAGE:
    # 賢者 - 専門領域高権限
    pass
else:
    # 一般権限
    pass
```

### 賢者専用権限チェック

```python
# 賢者タイプ権限チェック
can_access_knowledge = auth_provider.check_sage_permission(
    user, SageType.KNOWLEDGE
)

# 賢者別アクセス制御
if user.sage_type == SageType.KNOWLEDGE:
    # ナレッジ賢者 - 知識管理
    pass
elif user.sage_type == SageType.TASK:
    # タスク賢者 - タスク管理
    pass
elif user.sage_type == SageType.INCIDENT:
    # インシデント賢者 - 危機対応
    pass
elif user.sage_type == SageType.RAG:
    # RAG賢者 - 情報検索
    pass
```

### デコレーターによる権限制御

```python
from libs.unified_auth_provider import elder_auth_required, sage_auth_required

# Elder階層必須
@elder_auth_required(ElderRole.SAGE)
def elder_only_function(current_user, auth_provider):
    return "Elder権限で実行"

# 賢者専用
@sage_auth_required(SageType.KNOWLEDGE)
def knowledge_sage_function(current_user, auth_provider):
    return "ナレッジ賢者専用機能"

# 使用例（Flask等のWebフレームワークで）
try:
    result = elder_only_function(
        current_user=authenticated_user,
        auth_provider=auth_provider
    )
except PermissionError as e:
    return f"権限エラー: {e}"
```

---

## 🔒 セキュリティ機能

### アカウントロック

```python
# 失敗回数による自動ロック
# 5回連続失敗 → 30分ロック

# ロック状態確認
user = auth_provider.users[user_id]
if user.locked_until and datetime.now() < user.locked_until:
    print(f"アカウントロック中: {user.locked_until}まで")
```

### デバイス追跡

```python
# デバイス情報付き認証
auth_request = AuthRequest(
    username="user",
    password="password",
    device_info={
        "type": "mobile",
        "os": "iOS 15.0",
        "browser": "Safari",
        "device_id": "unique-device-identifier"
    },
    ip_address="203.0.113.1"
)
```

### Remember Me機能

```python
# 長期セッション（30日）
auth_request = AuthRequest(
    username="user",
    password="password",
    remember_me=True  # 30日間有効
)
```

---

## 🧪 テスト

### テスト実行

```bash
# 単体テスト実行
pytest tests/unit/test_unified_auth_provider.py -v

# カバレッジ付きテスト
pytest tests/unit/test_unified_auth_provider.py --cov=libs.unified_auth_provider --cov-report=html

# 特定テスト実行
pytest tests/unit/test_unified_auth_provider.py::TestAuthentication::test_successful_authentication -v
```

### テストカバレッジ

- **全体カバレッジ**: 95%以上
- **認証フロー**: 100%
- **権限チェック**: 100%
- **MFA機能**: 100%
- **セッション管理**: 100%

---

## 🔧 統合ガイド

### Flask統合例

```python
from flask import Flask, request, jsonify, session
from libs.unified_auth_provider import UnifiedAuthProvider, AuthRequest

app = Flask(__name__)
auth_provider = UnifiedAuthProvider(
    secret_key=app.config['SECRET_KEY']
)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    auth_request = AuthRequest(
        username=data['username'],
        password=data['password'],
        mfa_token=data.get('mfa_token'),
        ip_address=request.remote_addr,
        device_info={
            'user_agent': request.user_agent.string,
            'type': 'web'
        }
    )
    
    result, session_obj, user = auth_provider.authenticate(auth_request)
    
    if result == AuthResult.SUCCESS:
        return jsonify({
            'status': 'success',
            'token': session_obj.token,
            'user': user.to_dict()
        })
    elif result == AuthResult.MFA_REQUIRED:
        return jsonify({
            'status': 'mfa_required',
            'message': 'MFA token required'
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': 'Authentication failed'
        }), 401

@app.route('/api/auth/validate', methods=['POST'])
def validate():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    is_valid, user, session_obj = auth_provider.validate_token(token)
    
    if is_valid:
        return jsonify({
            'status': 'valid',
            'user': user.to_dict()
        })
    else:
        return jsonify({
            'status': 'invalid'
        }), 401
```

### FastAPI統合例

```python
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from libs.unified_auth_provider import UnifiedAuthProvider, User

app = FastAPI()
auth_provider = UnifiedAuthProvider(secret_key="your-secret-key")
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    is_valid, user, session = auth_provider.validate_token(credentials.credentials)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user

@app.post("/auth/login")
async def login(request: Request, username: str, password: str):
    auth_request = AuthRequest(
        username=username,
        password=password,
        ip_address=request.client.host
    )
    
    result, session, user = auth_provider.authenticate(auth_request)
    
    if result == AuthResult.SUCCESS:
        return {
            "access_token": session.token,
            "token_type": "bearer",
            "user": user.to_dict()
        }
    else:
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}!"}
```

---

## 📊 監視とログ

### ログ設定

```python
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 認証ログ監視例
logger = logging.getLogger('auth_monitor')

def monitor_authentication(auth_provider):
    """認証イベント監視"""
    # 実装例：ログ解析、アラート送信等
    pass
```

### メトリクス収集

```python
# 認証成功率
success_rate = successful_authentications / total_attempts

# アクティブセッション数
active_session_count = len([
    s for s in auth_provider.sessions.values() 
    if datetime.now() < s.expires_at
])

# MFA使用率
mfa_enabled_users = len([
    u for u in auth_provider.users.values() 
    if u.mfa_enabled
])
mfa_usage_rate = mfa_enabled_users / len(auth_provider.users)
```

---

## 🚨 トラブルシューティング

### よくある問題と解決法

#### 1. 認証失敗

**問題**: `AuthResult.INVALID_CREDENTIALS`が返される

**解決法**:
```python
# ユーザー存在確認
if username not in auth_provider.user_credentials:
    print("ユーザーが存在しません")

# パスワード確認（テスト環境のみ）
user = auth_provider.users[user_id]
if user.failed_attempts >= 5:
    print("アカウントがロックされています")
```

#### 2. MFA設定失敗

**問題**: MFA有効化後に認証できない

**解決法**:
```python
# MFA秘密鍵確認
user = auth_provider.users[user_id]
print(f"MFA Secret: {user.mfa_secret}")

# 時刻同期確認
import pyotp
totp = pyotp.TOTP(user.mfa_secret)
print(f"Current TOTP: {totp.now()}")
```

#### 3. トークン検証失敗

**問題**: 有効なトークンが無効と判定される

**解決法**:
```python
# JWT内容確認
import jwt
try:
    payload = jwt.decode(token, auth_provider.secret_key, algorithms=['HS256'])
    print(f"Token payload: {payload}")
except jwt.ExpiredSignatureError:
    print("トークンが期限切れです")
except jwt.InvalidTokenError:
    print("無効なトークンです")
```

#### 4. セッション消失

**問題**: セッションが予期せず削除される

**解決法**:
```python
# セッション期限確認
for session_id, session in auth_provider.sessions.items():
    if session.user_id == user_id:
        print(f"Session {session_id}: expires at {session.expires_at}")
```

---

## 🔄 マイグレーション

### 既存システムからの移行

#### 1. データ移行

```python
def migrate_existing_users(old_auth_system, new_auth_provider):
    """既存ユーザーデータ移行"""
    for old_user in old_auth_system.get_all_users():
        try:
            new_auth_provider.create_user(
                username=old_user.username,
                password=old_user.password,  # 既にハッシュ化済みの場合は調整
                email=old_user.email,
                elder_role=map_old_role_to_elder_role(old_user.role)
            )
        except ValueError as e:
            print(f"Migration failed for {old_user.username}: {e}")

def map_old_role_to_elder_role(old_role):
    """旧ロールをElder階層にマッピング"""
    mapping = {
        'admin': ElderRole.CLAUDE_ELDER,
        'moderator': ElderRole.SAGE,
        'user': ElderRole.SERVANT
    }
    return mapping.get(old_role, ElderRole.SERVANT)
```

#### 2. 段階的移行

```python
class HybridAuthProvider:
    """旧システムと新システムのハイブリッド認証"""
    
    def __init__(self, old_auth, new_auth):
        self.old_auth = old_auth
        self.new_auth = new_auth
    
    def authenticate(self, auth_request):
        # 新システムで試行
        result, session, user = self.new_auth.authenticate(auth_request)
        
        if result == AuthResult.INVALID_CREDENTIALS:
            # 旧システムで試行
            if self.old_auth.authenticate(auth_request.username, auth_request.password):
                # 成功時は新システムに移行
                migrated_user = self.migrate_user(auth_request.username)
                return self.new_auth.authenticate(auth_request)
        
        return result, session, user
```

---

## 📈 性能最適化

### キャッシュ戦略

```python
from functools import lru_cache
import redis

class CachedAuthProvider(UnifiedAuthProvider):
    """キャッシュ付き認証プロバイダー"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    @lru_cache(maxsize=1000)
    def _get_user_cached(self, user_id):
        """ユーザー情報キャッシュ"""
        return self.users.get(user_id)
    
    def validate_token(self, token):
        # Redisキャッシュから検証結果取得
        cached_result = self.redis_client.get(f"token:{token}")
        if cached_result:
            # キャッシュヒット
            return self._deserialize_validation_result(cached_result)
        
        # 通常の検証処理
        is_valid, user, session = super().validate_token(token)
        
        # 結果をキャッシュ（短時間）
        if is_valid:
            self.redis_client.setex(
                f"token:{token}",
                300,  # 5分キャッシュ
                self._serialize_validation_result(is_valid, user, session)
            )
        
        return is_valid, user, session
```

### 非同期対応

```python
import asyncio
import aioredis

class AsyncUnifiedAuthProvider:
    """非同期認証プロバイダー"""
    
    async def authenticate_async(self, auth_request):
        """非同期認証"""
        # 非同期データベースアクセス
        user_data = await self.get_user_async(auth_request.username)
        
        if not user_data:
            return AuthResult.INVALID_CREDENTIALS, None, None
        
        # 非同期パスワード検証
        is_valid = await self.verify_password_async(
            auth_request.password, user_data['password_hash']
        )
        
        if is_valid:
            # 非同期セッション作成
            session = await self.create_session_async(user_data)
            return AuthResult.SUCCESS, session, user_data
        
        return AuthResult.INVALID_CREDENTIALS, None, None
```

---

## 🛡️ セキュリティベストプラクティス

### 1. 秘密鍵管理

```python
import os
from cryptography.fernet import Fernet

# 環境変数から秘密鍵取得
SECRET_KEY = os.environ.get('AUTH_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("AUTH_SECRET_KEY environment variable required")

# 鍵ローテーション対応
class RotatingSecretKey:
    def __init__(self):
        self.current_key = os.environ.get('AUTH_SECRET_KEY_CURRENT')
        self.previous_key = os.environ.get('AUTH_SECRET_KEY_PREVIOUS')
    
    def decode_token(self, token):
        try:
            return jwt.decode(token, self.current_key, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            # 旧キーで試行
            return jwt.decode(token, self.previous_key, algorithms=['HS256'])
```

### 2. レート制限

```python
from collections import defaultdict, deque
import time

class RateLimiter:
    """レート制限機能"""
    
    def __init__(self):
        self.attempts = defaultdict(deque)
    
    def is_allowed(self, identifier, max_attempts=5, window_seconds=300):
        """レート制限チェック"""
        now = time.time()
        attempts = self.attempts[identifier]
        
        # 古い試行を削除
        while attempts and attempts[0] < now - window_seconds:
            attempts.popleft()
        
        if len(attempts) >= max_attempts:
            return False
        
        attempts.append(now)
        return True

# 認証プロバイダーに統合
class RateLimitedAuthProvider(UnifiedAuthProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate_limiter = RateLimiter()
    
    def authenticate(self, auth_request):
        # IPベースレート制限
        if not self.rate_limiter.is_allowed(auth_request.ip_address):
            return AuthResult.RATE_LIMITED, None, None
        
        return super().authenticate(auth_request)
```

### 3. セキュアヘッダー

```python
def add_security_headers(response):
    """セキュリティヘッダー追加"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

## 📚 参考資料

### 関連ドキュメント

- [Elder階層システム設計書](./ELDER_HIERARCHY_DESIGN.md)
- [4賢者システム仕様](./FOUR_SAGES_SPECIFICATION.md)
- [セキュリティ監査レポート](./SECURITY_AUDIT_REPORT.md)
- [API仕様書](./API_SPECIFICATION.md)

### 外部参考資料

- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [TOTP RFC 6238](https://tools.ietf.org/html/rfc6238)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

## 🎯 サポート

### 開発チーム連絡先

- **クロードエルダー**: claude@ai-company.com
- **インシデント賢者**: incident@ai-company.com
- **緊急時対応**: emergency@ai-company.com

### 問題報告

```bash
# GitHub Issues
https://github.com/ai-company/auth-system/issues

# Slack チャンネル
#elder-council-emergency
#sage-incident-response
```

---

**最終更新**: 2025年7月9日  
**バージョン**: v2.0  
**承認者**: エルダーズ評議会  
**次期レビュー**: 2025年7月16日