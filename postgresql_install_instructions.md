# PostgreSQL インストール手順

現在、sudo権限がないためPostgreSQLをインストールできません。
システム管理者に以下の手順を実行してもらってください。

## 1. PostgreSQLのインストール

```bash
# パッケージリストの更新
sudo apt-get update

# PostgreSQLとcontribモジュールのインストール
sudo apt-get install -y postgresql postgresql-contrib

# pgvector拡張のインストール（ベクター検索用）
# PostgreSQLのバージョンに応じて以下のいずれかを実行
sudo apt-get install -y postgresql-14-pgvector  # PostgreSQL 14の場合
sudo apt-get install -y postgresql-15-pgvector  # PostgreSQL 15の場合
sudo apt-get install -y postgresql-16-pgvector  # PostgreSQL 16の場合
```

## 2. PostgreSQLサービスの起動

```bash
# サービスの起動
sudo systemctl start postgresql

# 自動起動の有効化
sudo systemctl enable postgresql

# ステータス確認
sudo systemctl status postgresql
```

## 3. データベースとユーザーの作成

```bash
# postgresユーザーでpsqlに接続
sudo -u postgres psql

# 以下のSQLコマンドを実行
CREATE DATABASE ai_company;
CREATE DATABASE ai_company_grimoire;
CREATE USER ai_company_user WITH PASSWORD 'ai_company_pass';
GRANT ALL PRIVILEGES ON DATABASE ai_company TO ai_company_user;
GRANT ALL PRIVILEGES ON DATABASE ai_company_grimoire TO ai_company_user;

-- ai_company_grimoireデータベースに切り替え
\c ai_company_grimoire
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ai_companyデータベースに切り替え
\c ai_company
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- psqlを終了
\q
```

## 4. 接続テスト

```bash
# ai_company_userで接続テスト
psql -h localhost -U ai_company_user -d ai_company -c "SELECT version();"
# パスワード: ai_company_pass

psql -h localhost -U ai_company_user -d ai_company_grimoire -c "SELECT version();"
# パスワード: ai_company_pass
```

## 5. 環境変数の確認

既に`.env`ファイルに以下の設定があります：

```
DATABASE_URL=postgresql://ai_company_user:ai_company_pass@localhost:5432/ai_company
GRIMOIRE_DATABASE_URL=postgresql://ai_company_user:ai_company_pass@localhost:5432/ai_company
```

## インストール後の確認

インストールが完了したら、以下のコマンドで動作確認できます：

```bash
# ai-elder ccコマンドの実行
ai-elder cc

# PostgreSQL接続テスト
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://ai_company_user:ai_company_pass@localhost:5432/ai_company')
    print('✅ PostgreSQL接続成功！')
    conn.close()
except Exception as e:
    print(f'❌ 接続エラー: {e}')
"
```

## 代替案: Docker を使用

sudoが使えない場合、Dockerを使ってPostgreSQLを実行することも可能です：

```bash
# Dockerがインストールされている場合
docker run -d \
  --name postgres-ai-company \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=ai_company \
  -p 5432:5432 \
  ankane/pgvector:latest

# データベースの作成
docker exec -it postgres-ai-company psql -U postgres -c "CREATE DATABASE ai_company_grimoire;"
docker exec -it postgres-ai-company psql -U postgres -c "CREATE USER ai_company_user WITH PASSWORD 'ai_company_pass';"
docker exec -it postgres-ai-company psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ai_company TO ai_company_user;"
docker exec -it postgres-ai-company psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ai_company_grimoire TO ai_company_user;"
```

---

**注意**: 現在はモックGrimoireデータベースが自動的に使用されるため、PostgreSQLが無くても`ai-elder cc`コマンドは正常に動作します。