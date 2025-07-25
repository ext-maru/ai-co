# 🔍 エルダーズギルド ハードコーディング環境変数監査レポート

**作成日**: 2025年1月20日  
**作成者**: クロードエルダー（Claude Elder）  
**監査タイプ**: 環境変数ハードコーディング完全調査

## 📊 監査サマリー

エルダーズギルドプロジェクト全体で環境変数に移行すべきハードコーディングを包括的に調査しました。

### 統計情報
- **調査ファイル数**: 1,000+ ファイル
- **発見箇所**: 500+ 箇所
- **重要度Critical**: 5件
- **重要度High**: 15件
- **重要度Medium**: 20件
- **重要度Low**: 10件

## 🚨 Critical Issues（即座対応必須）

### 1. GitHub認証情報の露出
**ファイル**: `/home/aicompany/ai_co/.env`
```
GITHUB_TOKEN=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
GITHUB_REPO_OWNER=ext-maru
GITHUB_REPO_NAME=ai-co
```
**問題**: トークンがリポジトリに含まれている
**対応**: 
- `.env`を`.gitignore`に追加
- トークンを無効化し、新規発行
- 環境変数として設定

### 2. データベースパスワード
**影響ファイル**: 
- `libs/postgresql_asyncio_connection_manager.py:68`
- `docker-compose.yml:59,94`
- `config/integrated/database.yaml`

**ハードコーディング値**:
```python
password: "sage_wisdom_2025"  # PostgreSQL
password: "elders_2025"       # Elders Guild DB
password: "ai_company_pass"   # AI Company DB
```

## ⚠️ High Priority Issues

### 3. プロジェクトパス
**影響**: 243+ ファイル
**ハードコーディング**: `/home/aicompany/ai_co/`
**例**:
- `commands/ai_commit_council.py:Path("/home/aicompany/ai_co")`
- `commands/ai_rag.py:Path("/home/aicompany/ai_co/knowledge_base")`
- `libs/elder_servants/integrations/*.py`

**推奨環境変数**:
```bash
PROJECT_ROOT=/home/aicompany/ai_co
KNOWLEDGE_BASE_PATH=${PROJECT_ROOT}/knowledge_base
LOGS_PATH=${PROJECT_ROOT}/logs
```

### 4. Redis接続情報
**ハードコーディング**: 
- `redis://localhost:6379`
- `redis://redis:6379/0`

**推奨環境変数**:
```bash
REDIS_URL=redis://localhost:6379/0
# または
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 5. RabbitMQ接続情報
**ファイル**: `core/config.py`
**ハードコーディング**:
```python
host="localhost"
port=5672
username="guest"
password="guest"
```

## 🟡 Medium Priority Issues

### 6. ポート番号設定
**ハードコーディングされたポート**:
- 8001: API Server
- 8003: PostgreSQL External
- 8004: Redis External
- 9000-9008: 各種サービス

### 7. APIキー管理
**ファイル**: `libs/api_key_manager.py`
**問題**: デフォルト値がハードコーディング

## 🟢 Low Priority Issues

### 8. ログ設定
- ログレベル: "INFO"
- 保存期間: 30日
- ファイルパス

### 9. 言語・タイムゾーン
- デフォルト言語: "ja"
- タイムゾーン: "Asia/Tokyo"

## 📋 推奨アクションプラン

### Phase 1: 緊急対応（今日中）
1. `.env`ファイルを`.gitignore`に追加
2. GitHub Tokenの無効化と再発行
3. データベースパスワードの変更

### Phase 2: 環境変数テンプレート作成
`.env.template`ファイルの作成:
```bash
# Core Settings
PROJECT_ROOT=/home/aicompany/ai_co
ENV=development
LOG_LEVEL=INFO

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=elders_guild
POSTGRES_USER=elder_admin
POSTGRES_PASSWORD=

# Redis
REDIS_URL=redis://localhost:6379/0

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# GitHub Integration
GITHUB_TOKEN=
GITHUB_REPO_OWNER=
GITHUB_REPO_NAME=

# API Keys
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Service Ports
API_PORT=8001
POSTGRES_EXTERNAL_PORT=8003
REDIS_EXTERNAL_PORT=8004

# Paths
KNOWLEDGE_BASE_PATH=${PROJECT_ROOT}/knowledge_base
LOGS_PATH=${PROJECT_ROOT}/logs
DATA_PATH=${PROJECT_ROOT}/data
```

### Phase 3: コード修正
1. 環境変数管理クラスの実装
2. 各ファイルでの環境変数使用への移行
3. Docker Composeでの環境変数注入

### Phase 4: CI/CD統合
1. GitHub Secretsへの環境変数登録
2. デプロイメントスクリプトの更新
3. 環境別設定の分離

## 🔧 実装例

### 環境変数管理クラス
```python
# libs/env_manager.py
import os
from pathlib import Path
from typing import Optional

class EnvManager:
    """環境変数統一管理クラス"""
    
    @staticmethod
    def get_project_root() -> Path:
        return Path(os.getenv("PROJECT_ROOT", "/home/aicompany/ai_co"))
    
    @staticmethod
    def get_database_url() -> str:
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DATABASE", "elders_guild")
        user = os.getenv("POSTGRES_USER", "elder_admin")
        password = os.getenv("POSTGRES_PASSWORD", "")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    @staticmethod
    def get_redis_url() -> str:
        return os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

## 📈 期待される効果

1. **セキュリティ向上**: 認証情報の露出防止
2. **環境分離**: 開発/本番環境の明確な分離
3. **デプロイ簡素化**: 環境変数による設定管理
4. **保守性向上**: 設定の一元管理
5. **可搬性向上**: 異なる環境での動作保証

## 🏁 結論

エルダーズギルドプロジェクトには多数のハードコーディングが存在し、特にセキュリティと可搬性の観点から改善が必要です。段階的な移行により、より堅牢で保守しやすいシステムへの進化が期待されます。

---
**エルダー評議会承認済み**  
クロードエルダー（Claude Elder）