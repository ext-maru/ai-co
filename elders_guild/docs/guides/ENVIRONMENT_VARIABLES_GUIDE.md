# 🏛️ Elders Guild 環境変数ガイド

## 概要

Elders Guildプロジェクトでは、ハードコーディングを避けて環境変数を使用することで、異なる環境での柔軟な設定とセキュリティを実現しています。

## セットアップ

### 1. 環境変数ファイルの作成

```bash
# プロジェクトルートで実行
cp .env.example .env
```

### 2. 環境変数の編集

`.env`ファイルを編集して、あなたの環境に合わせて値を設定してください：

```bash
# エディタで開く
nano .env
# または
vim .env
```

## 主要な環境変数

### システムパス

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `ELDERS_GUILD_HOME` | Elders Guildのホームディレクトリ | `/home/aicompany/ai_co/elders_guild` |
| `PROJECT_ROOT` | プロジェクトルートディレクトリ | `${ELDERS_GUILD_HOME}` |

### データベース設定

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `DATABASE_URL` | PostgreSQL接続URL | `postgresql://aicompany:password@localhost/elder_tree` |
| `SQLITE_URL` | SQLite接続URL | `sqlite+aiosqlite:///elder_tree.db` |
| `REDIS_URL` | Redis接続URL | `redis://localhost:6379/0` |

### サービスポート

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `API_PORT` | APIサーバーポート | `8000` |
| `WEB_PORT` | Webサーバーポート | `8080` |
| `PROMETHEUS_PORT` | Prometheusポート | `9090` |
| `CONSUL_PORT` | Consulポート | `8500` |
| `REDIS_PORT` | Redisポート | `6379` |

### A2A設定

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `A2A_KNOWLEDGE_SAGE_PORT` | Knowledge Sageポート | `8806` |
| `A2A_TASK_SAGE_PORT` | Task Sageポート | `8809` |
| `A2A_INCIDENT_SAGE_PORT` | Incident Sageポート | `8807` |
| `A2A_RAG_SAGE_PORT` | RAG Sageポート | `8808` |

### セキュリティ

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `DB_PASSWORD` | データベースパスワード | `password` |
| `SECRET_KEY` | アプリケーションシークレットキー | `your-secret-key-here` |
| `API_TOKEN` | APIトークン | `your-api-token-here` |

⚠️ **警告**: 本番環境では必ずこれらの値を変更してください！

### 環境設定

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `ENVIRONMENT` | 実行環境 | `development` |
| `DEBUG` | デバッグモード | `true` |
| `LOG_LEVEL` | ログレベル | `INFO` |

## プログラムでの使用方法

### Python

```python
from shared_libs.config import config

# 環境変数の使用
api_url = config.API_BASE_URL
redis_url = config.REDIS_URL

# データベースパスの取得
db_path = config.get_db_path("knowledge.db")

# サービスURLの動的生成
service_url = config.get_service_url("prometheus")
```

### Bash

```bash
# .envファイルの読み込み
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 環境変数の使用
echo "API Port: ${API_PORT:-8000}"
echo "Project Root: ${ELDERS_GUILD_HOME}"
```

## Docker環境での使用

Docker Composeを使用する場合、`.env`ファイルは自動的に読み込まれます：

```yaml
services:
  api:
    image: elders-guild-api
    ports:
      - "${API_PORT}:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
```

## セキュリティのベストプラクティス

1. **`.env`ファイルをGitにコミットしない**
   - `.gitignore`に`.env`が含まれていることを確認

2. **本番環境では環境変数を直接設定**
   ```bash
   export DATABASE_URL="postgresql://prod_user:secure_password@prod_host/prod_db"
   ```

3. **シークレット管理ツールの使用を検討**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets

## トラブルシューティング

### 環境変数が読み込まれない

```bash
# 現在の環境変数を確認
env | grep ELDERS

# .envファイルの存在確認
ls -la .env

# 手動で環境変数を読み込む
source .env
```

### パスが正しく解決されない

```python
# デバッグ用コード
from shared_libs.config import config
print(f"ELDERS_GUILD_HOME: {config.ELDERS_GUILD_HOME}")
print(f"Current working directory: {os.getcwd()}")
```

## 関連ドキュメント

- [セットアップガイド](../setup/SETUP_GUIDE.md)
- [デプロイメントガイド](../deployment/DEPLOYMENT_GUIDE.md)
- [セキュリティガイド](../security/SECURITY_GUIDE.md)