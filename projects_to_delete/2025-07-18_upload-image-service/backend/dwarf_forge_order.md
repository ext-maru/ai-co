# 🔨 ドワーフ工房発注書 - FastAPIバックエンド鍛造依頼

## 📋 発注内容

### 1. **FastAPI プロジェクト構造**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーション本体
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # 依存性注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py       # APIルーター統合
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── sessions.py
│   │           ├── uploads.py
│   │           └── admin.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 設定管理
│   │   ├── security.py      # セキュリティ設定
│   │   └── database.py      # データベース接続
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py       # SQLAlchemyモデル
│   │   └── file.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── session.py       # Pydanticスキーマ
│   │   └── file.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── session_service.py
│   │   ├── file_service.py
│   │   └── google_drive_service.py
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_api/
├── alembic/                 # データベースマイグレーション
├── requirements.txt
├── .env.example
└── docker-compose.yml
```

### 2. **必要な機能実装**

#### **セッション管理API**
- POST /api/v1/sessions - セッション作成
- GET /api/v1/sessions/{id} - セッション取得
- PUT /api/v1/sessions/{id}/status - ステータス更新
- GET /api/v1/admin/sessions - 管理者用一覧

#### **ファイルアップロードAPI**
- POST /api/v1/sessions/{id}/upload - ファイルアップロード
- GET /api/v1/sessions/{id}/files - ファイル一覧
- DELETE /api/v1/files/{id} - ファイル削除

#### **Google Drive設定API**
- GET /api/v1/admin/google-drive/settings - 設定取得
- PUT /api/v1/admin/google-drive/settings - 設定更新
- POST /api/v1/admin/google-drive/test-connection - 接続テスト
- POST /api/v1/admin/google-drive/upload-credentials - 認証ファイルアップロード

### 3. **技術仕様**

#### **使用技術**
- FastAPI 0.100+
- SQLAlchemy 2.0+
- Pydantic 2.0+
- Uvicorn
- Python 3.11+

#### **データベース**
- 開発: SQLite
- 本番: PostgreSQL対応

#### **品質要件**
- TDD必須（pytest使用）
- 型ヒント100%
- エラーハンドリング完備
- ログ出力設定
- CORS対応

### 4. **参考実装**
mock_server.py の API仕様を参考に、本格的な実装を行う

## 📅 納期
即座開始、段階的納品

## 🏛️ 承認
クロードエルダー（発注者）
ドワーフマスター（受注確認待ち）
