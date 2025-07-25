# 🐘 PostgreSQL MCP セットアップガイド

## 📋 概要
PostgreSQL MCP (Model Context Protocol) を使用することで、エルダーズギルドの知識管理システムをPostgreSQLで統合管理します。

## 🚀 セットアップ手順

### 1. 前提条件の確認
```bash
# Node.js (v18以上)
node --version

# PostgreSQL (v15以上)
psql --version

# Python (v3.9以上)
python3 --version
```

### 2. PostgreSQL MCPのインストール
```bash
# インストールスクリプトの実行
cd /home/aicompany/ai_co
./scripts/install_postgres_mcp.sh
```

### 3. PostgreSQLデータベースの準備
```bash
# PostgreSQLにログイン
sudo -u postgres psql

# データベースとユーザーの作成
CREATE USER elders_guild WITH PASSWORD 'elders_2025';
CREATE DATABASE elders_knowledge OWNER elders_guild;
GRANT ALL PRIVILEGES ON DATABASE elders_knowledge TO elders_guild;

# 拡張機能の有効化
\c elders_knowledge
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 4. 接続テスト
```bash
# 環境変数の読み込み
source ~/.bashrc

# MCP経由での接続テスト
node test_postgres_mcp.js

# 直接PostgreSQL接続テスト
psql -h localhost -U elders_guild -d elders_knowledge
```

## 🔧 トラブルシューティング

### Node.jsがない場合
```bash
# Node.js 18のインストール
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### PostgreSQLがない場合
```bash
# PostgreSQL 16のインストール
sudo apt update
sudo apt install postgresql-16 postgresql-client-16
```

### 接続エラーの場合
1. PostgreSQLサービスの確認
```bash
sudo systemctl status postgresql
```

2. pg_hba.confの設定確認
```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
# local all all md5 に変更
sudo systemctl restart postgresql
```

## 📊 動作確認

### MCPツールの確認
```javascript
// test_mcp_tools.js
const mcp = require('@modelcontextprotocol/server-postgres');

// 利用可能なツール一覧
console.log('Available MCP Tools:');
console.log('- list_schemas: スキーマ一覧取得');
console.log('- list_objects: オブジェクト一覧取得');
console.log('- describe_object: オブジェクト詳細取得');
console.log('- execute_query: クエリ実行');
console.log('- explain_query: クエリ実行計画取得');
```

## 🎯 次のステップ

1. **スキーマ作成**
   - エルダーズギルド知識管理スキーマ
   - 4賢者システム用テーブル

2. **Python統合**
   - asyncpgでの接続実装
   - MCPラッパークラス作成

3. **疎通テスト**
   - 基本的なCRUD操作
   - パフォーマンス測定

## 🔐 セキュリティ注意事項

- パスワードは環境変数で管理
- 本番環境では読み取り専用ユーザーを別途作成
- SSL接続の有効化を推奨

---

*エルダーズギルド CorePostgres計画 - Phase 0*
