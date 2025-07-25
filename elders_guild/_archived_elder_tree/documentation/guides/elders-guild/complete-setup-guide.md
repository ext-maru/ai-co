# Elders Guild 完全セットアップガイド

**作成日**: 2025年7月23日  
**作成者**: クロードエルダー（Claude Elder）  
**バージョン**: 3.0.0

## 🎯 このガイドの目的

Elders Guild統合版を新規環境にセットアップし、全11サービスを正常に動作させるための完全ガイドです。

## 📋 前提条件

- Docker 20.10以上
- Docker Compose 2.0以上
- Python 3.11以上（開発時）
- Git
- 8GB以上のRAM推奨

## 🚀 クイックスタート

```bash
# リポジトリのクローン
git clone https://github.com/your-org/ai-co.git
cd ai-co/elders_guild

# 環境変数の設定
cd docker
cp .env.example .env
# .envファイルを編集して必要な値を設定

# 全サービスの起動
docker-compose up -d

# 動作確認
docker-compose ps
```

## 📦 サービス構成

### インフラストラクチャ層
| サービス | ポート | 役割 |
|---------|-------|------|
| PostgreSQL | 15432 | データベース |
| Redis | 16379 | キャッシュ・キュー |
| Consul | 8500 | サービスディスカバリ |

### モニタリング層
| サービス | ポート | 役割 |
|---------|-------|------|
| Prometheus | 9090 | メトリクス収集 |
| Grafana | 3000 | ダッシュボード |

### アプリケーション層
| サービス | ポート | 役割 |
|---------|-------|------|
| Knowledge Sage | 50051 | 知識管理 |
| Task Sage | 50052 | タスク管理 |
| Incident Sage | 50053 | インシデント管理 |
| RAG Sage | 50054 | 検索・情報取得 |
| Elder Flow | 50100 | ワークフロー管理 |
| Code Crafter | 50201 | コード生成 |

## 🔧 詳細セットアップ

### 1. 環境変数の設定

```bash
# docker/.envファイルの必須項目
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
OPENAI_API_KEY=your_openai_key        # RAG Sage用
ANTHROPIC_API_KEY=your_anthropic_key  # Incident Sage用
```

### 2. ディレクトリ構造の確認

```
elders_guild/
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── .env
├── src/
│   ├── elder_tree/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── agents/
│   │   ├── workflows/
│   │   └── servants/
│   ├── shared_libs/
│   └── {sage}_sage/
├── tests/
├── scripts/
└── config/
```

### 3. 初回起動手順

```bash
# 1. プロジェクトディレクトリへ移動
cd /home/aicompany/ai_co/elders_guild

# 2. Dockerディレクトリへ移動
cd docker

# 3. ネットワーク作成
docker network create elders_guild_network

# 4. インフラサービスの起動
docker-compose up -d postgres redis consul

# 5. ヘルスチェック待機（約30秒）
sleep 30

# 6. アプリケーションサービスの起動
docker-compose up -d

# 7. 動作確認
docker-compose ps
```

## 🧪 動作確認

### ヘルスチェック
```bash
# Knowledge Sage
curl http://localhost:50051/health

# Elder Flow
curl http://localhost:50100/health

# 全サービスの一括確認
for port in 50051 50052 50053 50054 50100 50201; do
  echo "Checking port $port:"
  curl -s http://localhost:$port/health | jq '.'
done
```

### ワークフロー実行テスト
```bash
curl -X POST http://localhost:50100/message \
  -H "Content-Type: application/json" \
  -d '{
    "type": "execute_flow",
    "task_type": "test_task",
    "requirements": ["test_requirement"],
    "priority": "medium"
  }'
```

## 🚨 トラブルシューティング

### サービスが起動しない場合

1. **ログ確認**
   ```bash
   docker logs <service_name> --tail 50
   ```

2. **ポート競合確認**
   ```bash
   sudo lsof -i :PORT_NUMBER
   ```

3. **イメージ再ビルド**
   ```bash
   cd docker
   docker-compose build --no-cache
   ```

### よくある問題

#### Q: "ModuleNotFoundError"が発生する
A: `__init__.py`ファイルが全ディレクトリに存在することを確認

#### Q: コンテナが再起動ループする
A: [Docker再起動ループガイド](../troubleshooting/docker-container-restart-loop.md)を参照

#### Q: ポートに接続できない
A: docker-compose.ymlでポートマッピングが設定されているか確認

## 📊 監視とメンテナンス

### Prometheusメトリクス
- URL: http://localhost:9090
- 主要メトリクス:
  - `agent_uptime_seconds`: 各エージェントの稼働時間
  - `http_requests_total`: HTTPリクエスト数
  - `sage_task_duration_seconds`: タスク実行時間

### Grafanaダッシュボード
- URL: http://localhost:3000
- デフォルトログイン: admin/admin
- 事前設定済みダッシュボード利用可能

### ログ管理
```bash
# 全サービスのログを確認
cd docker
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f knowledge_sage

# ログをファイルに保存
docker-compose logs > elders_guild_logs_$(date +%Y%m%d).txt
```

## 🔐 セキュリティ考慮事項

1. **環境変数の管理**
   - `.env`ファイルはGitにコミットしない
   - 本番環境では環境変数管理システムを使用

2. **ネットワーク分離**
   - elders_guild_networkで内部通信を隔離
   - 必要最小限のポートのみ公開

3. **非rootユーザー実行**
   - 全コンテナはelderuserで実行
   - セキュリティリスクを最小化

## 🚀 本番環境への展開

### Kubernetes対応
```yaml
# k8s/deployment.yaml の例
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledge-sage
spec:
  replicas: 3
  selector:
    matchLabels:
      app: knowledge-sage
  template:
    metadata:
      labels:
        app: knowledge-sage
    spec:
      containers:
      - name: knowledge-sage
        image: elders-guild/knowledge-sage:v3.0.0
        ports:
        - containerPort: 50051
```

### スケーリング考慮事項
- 各Sageは水平スケーリング可能
- RedisをクラスタモードVで実行
- PostgreSQLのレプリケーション設定

## 📚 関連ドキュメント

- [Flask移行ノウハウ集](../migration/flask-migration-knowhow.md)
- [アーキテクチャ設計書](../../architecture/elders-guild-architecture.md)
- [API仕様書](../../api/elders-guild-api-spec.md)

---

**サポート**: エルダーズギルド技術サポート  
**ライセンス**: MIT License