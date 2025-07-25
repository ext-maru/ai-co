# Elder Tree v2 完全セットアップガイド

**作成日**: 2025年7月23日  
**作成者**: クロードエルダー（Claude Elder）  
**バージョン**: 2.0.0

## 🎯 このガイドの目的

Elder Tree v2を新規環境にセットアップし、全11サービスを正常に動作させるための完全ガイドです。

## 📋 前提条件

- Docker 20.10以上
- Docker Compose 2.0以上
- Python 3.11以上（開発時）
- Git
- 8GB以上のRAM推奨

## 🚀 クイックスタート

```bash
# リポジトリのクローン
git clone https://github.com/your-org/elder-tree-v2.git
cd elder-tree-v2

# 環境変数の設定
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
# .envファイルの必須項目
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
OPENAI_API_KEY=your_openai_key        # RAG Sage用
ANTHROPIC_API_KEY=your_anthropic_key  # Incident Sage用
```

### 2. ディレクトリ構造の確認

```
elder-tree-v2/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── src/
│   └── elder_tree/
│       ├── __init__.py
│       ├── __main__.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base_agent.py
│       │   ├── knowledge_sage.py
│       │   ├── task_sage.py
│       │   ├── incident_sage.py
│       │   └── rag_sage.py
│       ├── workflows/
│       │   ├── __init__.py
│       │   └── simple_elder_flow.py
│       └── servants/
│           ├── __init__.py
│           └── simple_code_crafter.py
└── config/
    ├── prometheus/
    └── grafana/
```

### 3. 初回起動手順

```bash
# 1. ネットワーク作成
docker network create elder_tree_network

# 2. インフラサービスの起動
docker-compose up -d postgres redis consul

# 3. ヘルスチェック待機（約30秒）
sleep 30

# 4. アプリケーションサービスの起動
docker-compose up -d

# 5. 動作確認
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
docker-compose logs -f

# 特定サービスのログ
docker-compose logs -f knowledge_sage

# ログをファイルに保存
docker-compose logs > elder_tree_logs_$(date +%Y%m%d).txt
```

## 🔐 セキュリティ考慮事項

1. **環境変数の管理**
   - `.env`ファイルはGitにコミットしない
   - 本番環境では環境変数管理システムを使用

2. **ネットワーク分離**
   - elder_tree_networkで内部通信を隔離
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
        image: elder-tree/knowledge-sage:v2.0.0
        ports:
        - containerPort: 50051
```

### スケーリング考慮事項
- 各Sageは水平スケーリング可能
- RedisをクラスタモードVで実行
- PostgreSQLのレプリケーション設定

## 📚 関連ドキュメント

- [Flask移行ノウハウ集](../migration/flask-migration-knowhow.md)
- [アーキテクチャ設計書](../../architecture/elder-tree-v2-architecture.md)
- [API仕様書](../../api/elder-tree-v2-api-spec.md)

---

**サポート**: エルダーズギルド技術サポート  
**ライセンス**: MIT License