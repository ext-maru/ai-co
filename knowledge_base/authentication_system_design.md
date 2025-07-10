# Elders Guild Authentication System Architecture v2.0

## 📋 システム概要

### 🎯 設計目標
- **統一認証**: 既存システムの統合・改良
- **セキュリティ強化**: MFA、OAuth2、高度な脅威検知
- **スケーラビリティ**: マイクロサービス対応
- **Elder階層統合**: 4賢者システムとの完全連携

### 🏛️ Elder階層システム統合
```
🌟 グランドエルダーmaru
└── 🤖 クロードエルダー
    ├── 📚 ナレッジ賢者
    ├── 📋 タスク賢者
    ├── 🚨 インシデント賢者
    └── 🔍 RAG賢者
```

## 🔐 認証アーキテクチャ

### 1. **統合認証プロバイダー** (`libs/unified_auth_provider.py`)
```python
class UnifiedAuthProvider:
    """
    統一認証プロバイダー
    - 複数認証方式の統合管理
    - Elder階層システム連携
    - 4賢者システム統合
    """
    
    def __init__(self):
        self.jwt_manager = JWTManager()
        self.session_manager = SessionManager()
        self.mfa_manager = MFAManager()
        self.oauth_manager = OAuth2Manager()
        self.elder_integration = ElderAuthIntegration()
```

### 2. **Multi-Factor Authentication (MFA)** (`libs/mfa_manager.py`)
```python
class MFAManager:
    """
    多要素認証管理
    - TOTP (Time-based One-Time Password)
    - SMS認証
    - Email認証
    - Hardware keys (FIDO2/WebAuthn)
    """
    
    async def enable_totp(self, user_id: int) -> TOTPSecret:
        # TOTP設定
        
    async def verify_totp(self, user_id: int, token: str) -> bool:
        # TOTP検証
        
    async def send_sms_code(self, user_id: int, phone: str) -> str:
        # SMS認証コード送信
```

### 3. **OAuth2/OpenID Connect** (`libs/oauth2_manager.py`)
```python
class OAuth2Manager:
    """
    OAuth2/OIDC統合
    - Google OAuth2
    - GitHub OAuth2
    - Microsoft Azure AD
    - 企業LDAP/Active Directory
    """
    
    async def initiate_oauth_flow(self, provider: str, redirect_uri: str) -> OAuthState:
        # OAuth2フロー開始
        
    async def handle_oauth_callback(self, state: str, code: str) -> AuthResult:
        # OAuth2コールバック処理
```

### 4. **API Key Management** (`libs/api_key_manager.py`)
```python
class APIKeyManager:
    """
    APIキー管理
    - キー生成・失効
    - スコープ制御
    - 使用状況追跡
    - 自動ローテーション
    """
    
    async def generate_api_key(self, user_id: int, scopes: List[str]) -> APIKey:
        # APIキー生成
        
    async def validate_api_key(self, key: str) -> Optional[APIKeyInfo]:
        # APIキー検証
```

### 5. **Elder Authority Integration** (`libs/elder_auth_integration.py`)
```python
class ElderAuthIntegration:
    """
    Elder階層システム統合
    - 4賢者システム連携
    - 階層権限管理
    - 評議会認証
    - 賢者間通信認証
    """
    
    async def authenticate_elder(self, elder_id: str, credentials: Dict) -> ElderAuthResult:
        # Elder認証
        
    async def authorize_sage_action(self, sage_type: str, action: str, user: User) -> bool:
        # 賢者アクション認可
```

## 🗄️ データベース設計

### 認証関連テーブル

#### 1. `users` テーブル (拡張)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    hashed_password VARCHAR(255) NOT NULL,
    
    -- Elder階層
    elder_role VARCHAR(20) DEFAULT 'servant',
    sage_type VARCHAR(20),
    elder_level INTEGER DEFAULT 0,
    
    -- セキュリティ
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    backup_codes TEXT[],
    
    -- アカウント状態
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    
    -- セキュリティ追跡
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    password_changed_at TIMESTAMP,
    
    -- OAuth統合
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(100),
    oauth_data JSONB,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    last_password_change TIMESTAMP
);
```

#### 2. `user_sessions` テーブル (拡張)
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- セッション情報
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    jwt_token_id VARCHAR(100),
    
    -- デバイス情報
    device_id VARCHAR(100),
    device_name VARCHAR(100),
    device_type VARCHAR(50),
    device_fingerprint VARCHAR(255),
    
    -- 接続情報
    ip_address INET,
    user_agent TEXT,
    geolocation JSONB,
    
    -- セキュリティ
    is_trusted_device BOOLEAN DEFAULT FALSE,
    requires_mfa BOOLEAN DEFAULT FALSE,
    mfa_verified BOOLEAN DEFAULT FALSE,
    
    -- 状態
    is_active BOOLEAN DEFAULT TRUE,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP
);
```

#### 3. `api_keys` テーブル (新規)
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- キー情報
    key_id VARCHAR(50) UNIQUE NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    
    -- メタデータ
    name VARCHAR(100) NOT NULL,
    description TEXT,
    scopes TEXT[] DEFAULT '{}',
    
    -- 使用制限
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_hour INTEGER DEFAULT 3600,
    rate_limit_per_day INTEGER DEFAULT 86400,
    
    -- 統計
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    
    -- 状態
    is_active BOOLEAN DEFAULT TRUE,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP
);
```

#### 4. `mfa_devices` テーブル (新規)
```sql
CREATE TABLE mfa_devices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- デバイス情報
    device_type VARCHAR(20) NOT NULL, -- 'totp', 'sms', 'email', 'fido2'
    device_name VARCHAR(100) NOT NULL,
    device_identifier VARCHAR(255),
    
    -- TOTP設定
    totp_secret VARCHAR(255),
    totp_algorithm VARCHAR(10) DEFAULT 'SHA1',
    totp_digits INTEGER DEFAULT 6,
    totp_period INTEGER DEFAULT 30,
    
    -- FIDO2設定
    fido2_credential_id VARCHAR(255),
    fido2_public_key TEXT,
    fido2_counter INTEGER DEFAULT 0,
    
    -- 状態
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    last_used TIMESTAMP
);
```

#### 5. `oauth_integrations` テーブル (新規)
```sql
CREATE TABLE oauth_integrations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- OAuth情報
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(100) NOT NULL,
    
    -- トークン情報
    access_token VARCHAR(500),
    refresh_token VARCHAR(500),
    token_expires_at TIMESTAMP,
    
    -- プロバイダー情報
    provider_data JSONB,
    profile_data JSONB,
    
    -- 状態
    is_active BOOLEAN DEFAULT TRUE,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_sync TIMESTAMP
);
```

#### 6. `auth_audit_log` テーブル (新規)
```sql
CREATE TABLE auth_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- イベント情報
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(20) NOT NULL, -- 'auth', 'authz', 'security'
    event_action VARCHAR(50) NOT NULL,
    event_result VARCHAR(20) NOT NULL, -- 'success', 'failure', 'blocked'
    
    -- 詳細情報
    details JSONB,
    error_message TEXT,
    
    -- 接続情報
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- セキュリティ
    risk_score INTEGER DEFAULT 0,
    flagged BOOLEAN DEFAULT FALSE,
    
    -- タイムスタンプ
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔒 セキュリティ機能

### 1. **パスワードセキュリティ**
```python
class PasswordSecurity:
    """
    パスワードセキュリティ管理
    - 強度チェック
    - ハッシュ化 (bcrypt/scrypt)
    - 履歴管理
    - 自動期限切れ
    """
    
    def validate_password_strength(self, password: str, user_context: Dict) -> PasswordValidation:
        # パスワード強度検証
        
    def check_password_history(self, user_id: int, password: str) -> bool:
        # パスワード履歴チェック
```

### 2. **脅威検知システム**
```python
class ThreatDetector:
    """
    脅威検知システム
    - 異常ログイン検知
    - ブルートフォース攻撃検知
    - デバイス異常検知
    - 地理的異常検知
    """
    
    async def analyze_login_attempt(self, user_id: int, login_data: Dict) -> ThreatScore:
        # ログイン試行分析
        
    async def detect_brute_force(self, ip_address: str, user_id: int) -> bool:
        # ブルートフォース攻撃検知
```

### 3. **セッション管理**
```python
class SessionManager:
    """
    セッション管理
    - JWT + Redis セッション
    - デバイス追跡
    - 同時セッション制御
    - 自動期限切れ
    """
    
    async def create_session(self, user: User, device_info: Dict) -> SessionResult:
        # セッション作成
        
    async def validate_session(self, session_token: str) -> Optional[Session]:
        # セッション検証
```

## 🔧 実装計画

### Phase 1: 基盤構築
1. **統合認証プロバイダー実装**
   - `libs/unified_auth_provider.py`
   - `libs/elder_auth_integration.py`
   - 基本認証フロー

2. **データベース拡張**
   - 新テーブル作成
   - 既存テーブル拡張
   - マイグレーション

3. **セキュリティ強化**
   - `libs/password_security.py`
   - `libs/threat_detector.py`
   - 基本脅威検知

### Phase 2: 高度機能
1. **MFA実装**
   - `libs/mfa_manager.py`
   - TOTP, SMS, Email認証
   - バックアップコード

2. **OAuth2統合**
   - `libs/oauth2_manager.py`
   - Google, GitHub, Microsoft連携
   - 企業LDAP連携

3. **APIキー管理**
   - `libs/api_key_manager.py`
   - スコープ制御
   - 使用状況追跡

### Phase 3: 最適化
1. **パフォーマンス向上**
   - Redis キャッシュ
   - 分散セッション
   - 負荷分散

2. **監視・運用**
   - セキュリティダッシュボード
   - アラート システム
   - 自動復旧機能

3. **AI統合**
   - 異常検知AI
   - 自動セキュリティ調整
   - 予測的脅威対応

## 🧪 テスト戦略

### 1. **ユニットテスト**
```python
# tests/unit/test_unified_auth_provider.py
class TestUnifiedAuthProvider:
    def test_basic_authentication(self):
        # 基本認証テスト
        
    def test_mfa_flow(self):
        # MFA フローテスト
        
    def test_oauth_integration(self):
        # OAuth統合テスト
```

### 2. **統合テスト**
```python
# tests/integration/test_auth_flow.py
class TestAuthenticationFlow:
    def test_full_login_flow(self):
        # 完全ログインフローテスト
        
    def test_session_management(self):
        # セッション管理テスト
```

### 3. **セキュリティテスト**
```python
# tests/security/test_security_features.py
class TestSecurityFeatures:
    def test_brute_force_protection(self):
        # ブルートフォース保護テスト
        
    def test_jwt_security(self):
        # JWT セキュリティテスト
```

## 📊 監視・運用

### 1. **セキュリティメトリクス**
- 認証成功率
- 失敗ログイン試行
- MFA使用率
- セッション期間
- 脅威検知数

### 2. **アラート設定**
- 異常ログイン検知
- 大量失敗試行
- 新デバイス接続
- 権限昇格試行

### 3. **ダッシュボード**
- リアルタイム認証状況
- セキュリティ統計
- ユーザー活動
- 脅威マップ

## 🔄 マイグレーション計画

### 1. **既存システム統合**
- FastAPI backend 統合
- Legacy web auth 統合
- Security layer 統合

### 2. **段階的移行**
- Phase 1: 基盤構築 (2週間)
- Phase 2: 高度機能 (3週間)
- Phase 3: 最適化 (2週間)

### 3. **後方互換性**
- 既存APIの維持
- 段階的な機能移行
- ユーザー影響最小化

---

## 🎯 成功指標

### セキュリティ指標
- **認証成功率**: 99.9%以上
- **不正アクセス防止**: 100%
- **MFA採用率**: 80%以上
- **脅威検知精度**: 95%以上

### パフォーマンス指標
- **認証レスポンス時間**: 200ms以下
- **セッション作成時間**: 50ms以下
- **システム稼働率**: 99.99%

### ユーザビリティ指標
- **ログイン成功率**: 98%以上
- **MFA設定完了率**: 85%以上
- **パスワードリセット使用率**: 5%以下

---

**更新日**: 2025年7月9日  
**承認**: エルダーズ評議会  
**実装責任者**: クロードエルダー
**次期レビュー**: 2025年7月16日