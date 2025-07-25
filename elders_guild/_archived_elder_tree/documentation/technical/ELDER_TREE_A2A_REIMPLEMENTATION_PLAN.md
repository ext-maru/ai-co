# 🔄 Elder Tree A2A再実装計画書

**Document Type**: Re-implementation Plan  
**Version**: 2.0.0  
**Created**: 2025年7月22日  
**Author**: Claude Elder (クロードエルダー)  
**Status**: OSS First Policy準拠

---

## 📋 **実装方針**

### 🎯 **基本方針**
1. **設計書遵守**: ELDER_TREE_A2A_IMPLEMENTATION.md を完全準拠
2. **OSS First**: 全ての機能でOSS活用を最優先
3. **段階的移行**: 既存コードを段階的に置き換え

---

## 🛠️ **技術スタック（OSS活用）**

### ✅ **採用OSS一覧**

| カテゴリ | OSS | バージョン | 選定理由 |
|---------|-----|-----------|----------|
| **通信基盤** | a2a-python | ^0.1.0 | Google製、設計書指定 |
| **RPC** | grpcio | ^1.51.1 | a2a内包、高性能 |
| **メッセージ定義** | protobuf | ^4.24.0 | 型安全性、言語間互換 |
| **Web API** | fastapi | ^0.104.0 | 高速、型ヒント対応 |
| **ASGIサーバー** | uvicorn | ^0.24.0 | FastAPI推奨 |
| **データ検証** | pydantic | ^2.5.0 | FastAPI統合 |
| **ORM** | sqlmodel | ^0.0.14 | Pydantic統合 |
| **DB Driver** | asyncpg | ^0.29.0 | PostgreSQL非同期 |
| **キャッシュ** | redis | ^5.0.1 | 実績豊富 |
| **メトリクス** | prometheus-client | ^0.19.0 | 業界標準 |
| **構造化ログ** | structlog | ^23.2.0 | 高機能ログ |
| **トレーシング** | opentelemetry-api | ^1.21.0 | 分散トレース |
| **テスト** | pytest | ^7.4.3 | Python標準 |
| **非同期テスト** | pytest-asyncio | ^0.21.1 | pytest拡張 |
| **フォーマッター** | black | ^23.11.0 | Python標準 |
| **リンター** | ruff | ^0.1.6 | 高速 |
| **型チェック** | mypy | ^1.7.0 | 静的型検査 |
| **パッケージ管理** | poetry | ^1.7.0 | 依存関係管理 |
| **コンテナ** | docker | latest | デプロイ標準 |

---

## 📦 **実装計画**

### Phase 1: 基盤整備（Day 1）

#### 1.1 プロジェクト構造作成
```bash
# 新ディレクトリ構造作成
mkdir -p ai_co/elder_tree/{core,domains,api,protos}
mkdir -p ai_co/elder_tree/core/{souls,communication,monitoring}
mkdir -p ai_co/elder_tree/domains/{knowledge,task,incident,rag}
```

#### 1.2 Poetry環境セットアップ
```bash
cd ai_co
poetry new elder_tree --name elder-tree
cd elder_tree

# 依存関係追加（OSS一括インストール）
poetry add a2a-python grpcio protobuf fastapi uvicorn pydantic sqlmodel asyncpg redis prometheus-client structlog opentelemetry-api
poetry add --dev pytest pytest-asyncio black ruff mypy
```

#### 1.3 Protocol Buffers定義
```protobuf
// elder_tree/protos/soul_messages.proto
syntax = "proto3";
package elder_tree;

// 設計書通りのメッセージ定義
message SoulMessage {
    string message_id = 1;
    string sender_soul = 2;
    // ...
}
```

### Phase 2: A2A基盤実装（Day 2）

#### 2.1 A2ASoul基底クラス
```python
# elder_tree/core/souls/a2a_soul.py
from a2a import Server, Client, Message
import structlog

logger = structlog.get_logger()

class A2ASoul(ABC):
    """a2a-python統合魂基底クラス"""
    
    def __init__(self, soul_config: Dict[str, Any]):
        # a2a Server初期化
        self.server = Server(
            name=f"elder_tree.{soul_config['soul_name']}",
            port=soul_config['port']
        )
        
        # Prometheusメトリクス
        self.request_counter = Counter(
            'soul_requests_total',
            'Total requests',
            ['soul_name', 'method']
        )
```

#### 2.2 通信レジストリ
```python
# elder_tree/core/communication/service_registry.py
from typing import Dict, List
import consul  # サービスディスカバリー用OSS

class ServiceRegistry:
    """サービスディスカバリー（Consul統合）"""
    
    def __init__(self):
        self.consul = consul.Consul()
    
    async def register_soul(self, soul_name: str, port: int):
        """魂をConsulに登録"""
        self.consul.agent.service.register(
            name=f"elder_tree_{soul_name}",
            service_id=f"{soul_name}_{port}",
            port=port,
            tags=["elder_tree", "soul"]
        )
```

### Phase 3: 4賢者移行（Day 3-4）

#### 3.1 既存実装の分析
```python
# 移行スクリプト
# 1. 既存のelders_guild_dev/からビジネスロジック抽出
# 2. A2ASoulを継承した新実装作成
# 3. a2aハンドラーとして再実装
```

#### 3.2 Knowledge Sage移行例
```python
# elder_tree/domains/knowledge/knowledge_sage.py
from elder_tree.core.souls.a2a_soul import A2ASoul
from elder_tree.protos import soul_messages_pb2

class KnowledgeSageA2A(A2ASoul):
    def __init__(self):
        super().__init__({
            "soul_name": "knowledge_sage",
            "domain": "knowledge",
            "port": 50051
        })
        
        # 既存ロジックを移植
        self._migrate_existing_logic()
    
    def _register_domain_handlers(self):
        @self.server.handler("analyze_technology")
        async def analyze_technology(message: Message) -> Message:
            # 既存のanalyze_technologyロジックをa2a化
            pass
```

### Phase 4: API Gateway実装（Day 5）

#### 4.1 FastAPI Gateway
```python
# elder_tree/api/main.py
from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

app = FastAPI(title="Elder Tree API Gateway")
Instrumentator().instrument(app).expose(app)

@app.post("/v1/souls/{soul_name}/call")
async def call_soul(soul_name: str, method: str, payload: dict):
    """統一APIエンドポイント"""
    # a2a-pythonクライアントで魂呼び出し
    client = Client()
    response = await client.call(
        service=f"elder_tree.{soul_name}",
        method=method,
        data=payload
    )
    return response.data
```

### Phase 5: インフラ整備（Day 6）

#### 5.1 Docker化
```dockerfile
# docker/Dockerfile.soul
FROM python:3.11-slim

# Poetryインストール
RUN pip install poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

COPY . .
CMD ["poetry", "run", "python", "-m", "elder_tree.launch"]
```

#### 5.2 Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  # PostgreSQL（公式イメージ使用）
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: elder_tree
    
  # Redis（公式イメージ使用）
  redis:
    image: redis:7-alpine
  
  # Consul（サービスディスカバリー）
  consul:
    image: consul:latest
    
  # 魂コンテナ（設計書通り）
  knowledge-sage:
    build: 
      context: .
      dockerfile: docker/Dockerfile.soul
    environment:
      SOUL_NAME: knowledge_sage
```

### Phase 6: 監視・ログ（Day 7）

#### 6.1 Prometheus + Grafana
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'elder_tree'
    static_configs:
      - targets: ['api-gateway:8000']
```

#### 6.2 構造化ログ設定
```python
# elder_tree/core/logging.py
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

---

## 🧪 **テスト計画**

### 単体テスト
```python
# tests/unit/test_a2a_soul.py
import pytest
from elder_tree.core.souls.a2a_soul import A2ASoul

@pytest.mark.asyncio
async def test_soul_initialization():
    """a2a-python統合テスト"""
    soul = TestSoul({"soul_name": "test", "port": 50999})
    assert soul.server.name == "elder_tree.test"
```

### 統合テスト
```python
# tests/integration/test_soul_communication.py
@pytest.mark.asyncio
async def test_soul_to_soul_communication():
    """魂間通信テスト（実a2a使用）"""
    # 実際のa2aサーバー起動
    # メッセージ送受信確認
```

---

## 📅 **実装スケジュール**

| フェーズ | 期間 | 内容 | 使用OSS |
|---------|------|------|---------|
| Phase 1 | Day 1 | 基盤整備 | Poetry, protobuf |
| Phase 2 | Day 2 | A2A基盤 | a2a-python, structlog |
| Phase 3 | Day 3-4 | 4賢者移行 | 既存→a2a |
| Phase 4 | Day 5 | API Gateway | FastAPI, uvicorn |
| Phase 5 | Day 6 | インフラ | Docker, PostgreSQL, Redis |
| Phase 6 | Day 7 | 監視・ログ | Prometheus, Grafana |
| **合計** | **1週間** | **完全移行** | **20+ OSS活用** |

---

## ✅ **成功基準**

1. **a2a-python完全統合**: 全通信がa2a経由
2. **OSS活用率**: 90%以上
3. **設計書準拠率**: 100%
4. **テストカバレッジ**: 80%以上
5. **パフォーマンス**: レイテンシ < 50ms

---

## 🚀 **実装開始承認**

- 申請者: Claude Elder
- 承認者: グランドエルダー maru様
- 承認日: 2025年7月22日

**「OSS Firstで車輪の再発明を防ぎ、設計書通りの実装を実現する」**