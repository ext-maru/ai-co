# Issue理解エンジン設計書
## Issue #184 Phase 2

### 🎯 目標
自然言語処理（NLP）を使用してIssueの内容をより深く理解し、要件を正確に抽出することで、コード生成品質をさらに向上させる。

### 🔧 アーキテクチャ

```
┌─────────────────────┐
│   GitHub Issue      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Issue Analyzer     │ ← spaCy + transformers
├─────────────────────┤
│ - 文章解析          │
│ - エンティティ抽出  │
│ - 意図分類          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│Requirement Extractor│
├─────────────────────┤
│ - 技術要件抽出      │
│ - API仕様解析      │
│ - 制約条件識別      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Enhanced Context    │
├─────────────────────┤
│ - 構造化要件        │
│ - 意図的分類        │
│ - 優先順位付け      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Template Manager    │ → Jinja2 Templates
└─────────────────────┘
```

### 📋 実装コンポーネント

#### 1. Issue Analyzer (`libs/code_generation/issue_analyzer.py`)
- **目的**: Issue内容の深い理解
- **機能**:
  - 文章の構造解析
  - 技術用語の識別
  - 要件と説明の分離
  - 意図の分類（新機能、バグ修正、改善等）

#### 2. Requirement Extractor (`libs/code_generation/requirement_extractor.py`)
- **目的**: 具体的な技術要件の抽出
- **機能**:
  - API仕様の解析（エンドポイント、メソッド、パラメータ）
  - データモデルの抽出
  - 制約条件の識別（パフォーマンス、セキュリティ等）
  - 依存関係の特定

#### 3. NLP Utilities (`libs/code_generation/nlp_utils.py`)
- **目的**: NLP処理の共通機能
- **機能**:
  - spaCyモデルの管理
  - カスタム固有表現認識（技術用語）
  - 文章の前処理

### 🧠 NLP処理フロー

#### ステップ1: 文章解析
```python
# Issue本文を解析
doc = nlp(issue_body)

# 文章を意味的に分類
sections = {
    "requirements": [],
    "examples": [],
    "constraints": [],
    "technical_specs": []
}
```

#### ステップ2: エンティティ抽出
```python
# 技術エンティティを識別
entities = {
    "technologies": ["AWS", "S3", "boto3"],
    "operations": ["upload", "download", "list"],
    "data_types": ["file", "bucket", "metadata"]
}
```

#### ステップ3: 意図分類
```python
# Issueの意図を分類
intent = {
    "primary": "feature_implementation",
    "category": "integration",
    "complexity": "medium"
}
```

#### ステップ4: 要件構造化
```python
# 構造化された要件
structured_requirements = {
    "functional": [
        {"type": "api", "method": "POST", "endpoint": "/upload"},
        {"type": "api", "method": "GET", "endpoint": "/download/{id}"}
    ],
    "non_functional": [
        {"type": "performance", "requirement": "handle 1000 req/s"},
        {"type": "security", "requirement": "use IAM roles"}
    ]
}
```

### 🔍 技術キーワード辞書

#### プログラミング言語/フレームワーク
- Python: `flask`, `django`, `fastapi`, `pandas`, `numpy`
- JavaScript: `react`, `vue`, `express`, `node`
- AWS: `boto3`, `s3`, `ec2`, `lambda`, `dynamodb`

#### 操作/アクション
- CRUD: `create`, `read`, `update`, `delete`, `list`
- API: `endpoint`, `route`, `method`, `request`, `response`
- データ: `process`, `transform`, `aggregate`, `filter`

### 📊 期待される改善

#### Phase 1（現在）の問題点
- キーワードベースの単純なマッチング
- 文脈を考慮しない技術スタック検出
- 要件の優先順位付けなし

#### Phase 2での改善
- 文脈を理解した技術スタック検出
- 要件の重要度と優先順位の自動判定
- より正確なAPI仕様の抽出
- 制約条件の考慮

### 🧪 検証方法

#### テストケース例
```python
# 複雑なIssue例
issue_body = """
We need a RESTful API for user management with the following requirements:

1. User registration with email verification
2. JWT-based authentication
3. Role-based access control (admin, user)
4. Rate limiting: 100 requests per minute per IP
5. Database: PostgreSQL with SQLAlchemy ORM
6. Caching: Redis for session management
7. API documentation with Swagger/OpenAPI

Performance requirements:
- Handle 10,000 concurrent users
- Response time < 200ms for all endpoints
- 99.9% uptime SLA

Security requirements:
- HTTPS only
- Input validation
- SQL injection prevention
- XSS protection
"""

# 期待される抽出結果
expected_requirements = {
    "apis": [
        {"method": "POST", "endpoint": "/users", "purpose": "registration"},
        {"method": "POST", "endpoint": "/auth/login", "purpose": "authentication"},
        {"method": "GET", "endpoint": "/users/{id}", "purpose": "get user"}
    ],
    "technologies": {
        "framework": "fastapi",  # RESTful + Swagger対応
        "database": "postgresql",
        "orm": "sqlalchemy",
        "cache": "redis",
        "auth": "jwt"
    },
    "constraints": {
        "rate_limit": "100/min",
        "concurrent_users": 10000,
        "response_time": "200ms",
        "uptime": "99.9%"
    }
}
```

### 🚀 実装ステップ

1. **NLPライブラリのセットアップ**
   - spaCy英語モデルのインストール
   - 技術用語辞書の作成

2. **Issue Analyzerの実装**
   - 基本的な文章解析
   - セクション分類

3. **Requirement Extractorの実装**
   - API仕様抽出
   - 制約条件識別

4. **Template Managerとの統合**
   - 拡張コンテキストの生成
   - より詳細なテンプレート選択

5. **テストと検証**
   - 実際のIssueでの検証
   - 品質スコアの測定

### 📈 成功指標

- 要件抽出精度: 90%以上
- API仕様の正確性: 95%以上
- 技術スタック検出精度: 95%以上
- コード生成品質スコア: 90点以上（Phase 1: 100点から更なる向上）