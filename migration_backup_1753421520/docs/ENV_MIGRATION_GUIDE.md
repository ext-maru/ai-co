# 🔧 環境変数移行ガイド

**作成日**: 2025年1月20日  
**作成者**: クロードエルダー（Claude Elder）  
**対象**: エルダーズギルド開発チーム

## 📋 概要

エルダーズギルドプロジェクトのハードコーディングされた設定値を環境変数に移行しました。

## ✅ 実施内容

### 1. 作成ファイル
- **`.env.template`** - 環境変数テンプレート（全設定項目を網羅）
- **`libs/env_manager.py`** - 環境変数統一管理クラス

### 2. 修正ファイル

#### データベース関連
- `libs/postgresql_asyncio_connection_manager.py` - パスワードのデフォルト値を削除
- `docker-compose.yml` - 環境変数参照に変更

#### パス関連
- `commands/ai_commit_council.py`
- `commands/ai_rag.py`
- `commands/ai_evolve.py`
- `commands/ai_knowledge.py`
- `commands/ai_monitor.py`
- `commands/ai_help.py`

#### 接続情報
- `core/config.py` - RabbitMQ設定を環境変数から取得

## 🚀 使用方法

### 1. 環境変数ファイルの準備
```bash
# テンプレートをコピー
cp .env.template .env

# 必須項目を編集
nano .env
```

### 2. 必須設定項目
```bash
# GitHub（必須）
GITHUB_TOKEN=your_github_token_here

# データベース（必須）
POSTGRES_PASSWORD=your_postgres_password_here

# API Keys（使用する場合）
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### 3. EnvManagerの使用例
```python
from libs.env_manager import EnvManager

# プロジェクトルート取得
root = EnvManager.get_project_root()

# データベースURL取得
db_url = EnvManager.get_database_url()

# ナレッジベースパス取得
kb_path = EnvManager.get_knowledge_base_path()

# GitHub設定取得
github_token = EnvManager.get_github_token()
repo_owner = EnvManager.get_github_repo_owner()
repo_name = EnvManager.get_github_repo_name()
```

## 🔍 環境変数検証
```bash
# EnvManagerのテスト実行
python3 libs/env_manager.py

# 必須環境変数の検証
python3 -c "from libs.env_manager import EnvManager; print(EnvManager.validate_required_env_vars())"
```

## 📊 主要な環境変数

### Core Settings
- `PROJECT_ROOT` - プロジェクトルートパス（デフォルト: /home/aicompany/ai_co）
- `ENV` - 環境（development/staging/production）
- `LOG_LEVEL` - ログレベル（DEBUG/INFO/WARNING/ERROR）

### GitHub
- `GITHUB_TOKEN` - GitHubアクセストークン
- `GITHUB_REPO_OWNER` - リポジトリオーナー
- `GITHUB_REPO_NAME` - リポジトリ名

### Database
- `POSTGRES_HOST` - PostgreSQLホスト
- `POSTGRES_PORT` - PostgreSQLポート
- `POSTGRES_DATABASE` - データベース名
- `POSTGRES_USER` - ユーザー名
- `POSTGRES_PASSWORD` - パスワード

### Redis
- `REDIS_URL` - Redis接続URL
- または `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`

### RabbitMQ
- `RABBITMQ_HOST` - RabbitMQホスト
- `RABBITMQ_PORT` - RabbitMQポート
- `RABBITMQ_USER` - ユーザー名
- `RABBITMQ_PASSWORD` - パスワード

## ⚠️ 注意事項

1. **`.env`ファイルは絶対にコミットしない**（.gitignoreで除外済み）
2. **本番環境では環境変数を直接設定**（.envファイルは使用しない）
3. **パスワードは強固なものを使用**
4. **定期的にトークンをローテーション**

## 🔄 今後の作業

1. 残りのハードコーディング箇所の段階的移行
2. CI/CDパイプラインへの環境変数統合
3. 環境別設定ファイルの整備
4. シークレット管理システムの導入検討

---
**エルダー評議会承認済み**