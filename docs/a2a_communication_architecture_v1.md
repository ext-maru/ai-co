# A2A（Agent to Agent）通信システム アーキテクチャ設計書 v1.0

## 📋 システム概要

A2A（Agent to Agent）通信システムは、Elders Guild内の4賢者（Four Sages）、エルダーズ（Elders）、およびエルダーサーバント（Elder Servants）間の効率的で安全な通信を実現するフレームワークです。

### 🎯 設計目標

1. **高性能**: 非同期通信による低レイテンシ実現
2. **高可用性**: メッセージキューイングによる信頼性確保
3. **セキュリティ**: 暗号化と認証による安全な通信
4. **スケーラビリティ**: 負荷分散による拡張性
5. **監視可能性**: 包括的なロギングとメトリクス

## 🏗️ アーキテクチャ概要

### システム階層構造

```
┌─────────────────────────────────────────────┐
│                Elder Council                │
│          (エルダー評議会)                    │
└─────────────────┬───────────────────────────┘
                  │ A2A Protocol
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│ Four  │    │Elder  │    │Elder  │
│Sages  │    │Servants│   │Servants│
│4賢者   │    │サーバント│   │サーバント│
└───────┘    └───────┘    └───────┘
```

### コア構成要素

1. **A2A Communication Layer**: 通信抽象化層
2. **Message Queue (RabbitMQ)**: 非同期メッセージング
3. **Protocol Handler**: プロトコル処理
4. **Security Layer**: 認証・認可・暗号化
5. **Monitoring & Logging**: 監視・ログ機能

## 🔄 通信パターン

### 1. 同期通信パターン

```python
# 直接通信 - 緊急時または即座に応答が必要な場合
response = await a2a_client.sync_call(
    target_agent="knowledge_sage",
    method="query_knowledge",
    params={"query": "A2A protocol specs"},
    timeout=5.0
)
```

### 2. 非同期通信パターン

```python
# メッセージキュー経由 - 通常の業務処理
await a2a_client.async_send(
    target_agent="task_sage",
    message_type="task_assignment",
    payload={"task_id": "12345", "priority": "high"},
    delivery_mode="persistent"
)
```

### 3. ブロードキャストパターン

```python
# 複数エージェントへの一斉送信
await a2a_client.broadcast(
    target_groups=["four_sages", "elder_servants"],
    message_type="system_alert",
    payload={"alert_level": "warning", "message": "System maintenance"}
)
```

### 4. パブリッシュ・サブスクライブパターン

```python
# イベント駆動通信
await a2a_client.publish(
    topic="task_completion",
    event_data={"task_id": "12345", "status": "completed", "result": {...}}
)

# サブスクライバー側
@a2a_client.subscribe("task_completion")
async def handle_task_completion(event_data):
    # タスク完了処理
    pass
```

## 🛡️ セキュリティアーキテクチャ

### 認証・認可フロー

```
Agent A                A2A Gateway              Agent B
   │                       │                       │
   │──1. Auth Request──────▶│                       │
   │◀─2. JWT Token─────────│                       │
   │                       │                       │
   │──3. Message + JWT─────▶│                       │
   │                       │──4. Validate Token───▶│
   │                       │◀─5. Validation OK─────│
   │                       │──6. Encrypted Msg────▶│
   │                       │                       │
```

### セキュリティ要素

1. **JWT認証**: エージェント間の身元確認
2. **TLS暗号化**: 通信データの暗号化
3. **RBAC**: ロールベースアクセス制御
4. **Rate Limiting**: DDoS攻撃防止
5. **Message Integrity**: メッセージ改ざん検証

## 📊 メッセージプロトコル

### A2A Message Format (JSON)

```json
{
  "header": {
    "message_id": "uuid-v4",
    "timestamp": "2025-07-09T12:00:00Z",
    "source_agent": "knowledge_sage",
    "target_agent": "task_sage",
    "message_type": "query_request",
    "correlation_id": "optional-uuid",
    "ttl": 3600,
    "priority": "normal"
  },
  "auth": {
    "jwt_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "signature": "hash_signature"
  },
  "payload": {
    "method": "get_task_history",
    "params": {
      "agent_id": "task_sage",
      "time_range": "7d"
    }
  },
  "metadata": {
    "encryption": "AES-256",
    "compression": "gzip",
    "schema_version": "1.0"
  }
}
```

### メッセージタイプ定義

```python
class MessageType(Enum):
    # 基本通信
    QUERY_REQUEST = "query_request"
    QUERY_RESPONSE = "query_response"
    COMMAND = "command"
    STATUS_UPDATE = "status_update"

    # エルダー評議会
    COUNCIL_SUMMON = "council_summon"
    COUNCIL_DECISION = "council_decision"
    URGENT_CONSULTATION = "urgent_consultation"

    # タスク管理
    TASK_ASSIGNMENT = "task_assignment"
    TASK_STATUS = "task_status"
    TASK_COMPLETION = "task_completion"

    # 知識管理
    KNOWLEDGE_QUERY = "knowledge_query"
    KNOWLEDGE_UPDATE = "knowledge_update"
    PATTERN_SHARING = "pattern_sharing"

    # インシデント管理
    INCIDENT_ALERT = "incident_alert"
    RECOVERY_REQUEST = "recovery_request"
    HEALTH_CHECK = "health_check"
```

## 🔧 技術スタック

### Core Components

| 層 | 技術 | 用途 |
|---|---|---|
| Application | Python 3.12+ | アプリケーション層 |
| Messaging | RabbitMQ | メッセージキューイング |
| Protocol | AMQP/HTTP/WebSocket | 通信プロトコル |
| Security | TLS 1.3, JWT, AES-256 | セキュリティ |
| Monitoring | Prometheus + Grafana | 監視・メトリクス |
| Logging | Elasticsearch + Kibana | ログ管理 |

### 依存ライブラリ

```python
# 必要ライブラリ
aio-pika         # RabbitMQ async client
cryptography     # 暗号化機能
PyJWT           # JWT処理
asyncio         # 非同期処理
websockets      # WebSocket通信
prometheus-client # メトリクス収集
structlog       # 構造化ログ
```

## 🚀 パフォーマンス設計

### レイテンシ目標

| 通信タイプ | 目標レイテンシ | SLA |
|---|---|---|
| 同期通信 | < 100ms | 99.9% |
| 非同期通信 | < 500ms | 99.5% |
| ブロードキャスト | < 1s | 99.0% |

### スループット目標

- **メッセージ処理**: 10,000 msg/sec
- **同時接続**: 1,000 connections
- **帯域幅**: 100 Mbps

### リソース使用量

- **CPU**: 4 cores (peak時)
- **Memory**: 8GB RAM
- **Storage**: 100GB (ログ・メトリクス含む)

## 📈 監視・ロギング

### Key Metrics

1. **通信メトリクス**
   - メッセージスループット
   - レイテンシ分布
   - エラー率

2. **システムメトリクス**
   - CPU/Memory使用率
   - Network I/O
   - Disk使用量

3. **ビジネスメトリクス**
   - エージェント間協調効率
   - タスク完了率
   - インシデント解決時間

### ログ設計

```json
{
  "timestamp": "2025-07-09T12:00:00Z",
  "level": "INFO",
  "component": "a2a_gateway",
  "message_id": "uuid",
  "source_agent": "knowledge_sage",
  "target_agent": "task_sage",
  "message_type": "query_request",
  "latency_ms": 45,
  "status": "success",
  "trace_id": "distributed_trace_id"
}
```

## 🔄 フェーズ実装計画

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] A2A Communication Layer実装
- [ ] RabbitMQ統合
- [ ] 基本プロトコル実装
- [ ] セキュリティ基盤

### Phase 2: Advanced Features (Week 3-4)
- [ ] 4賢者間通信実装
- [ ] エルダー評議会システム統合
- [ ] パフォーマンス最適化
- [ ] 包括的テスト実装

### Phase 3: Production Ready (Week 5-6)
- [ ] 監視・アラート実装
- [ ] 本格運用移行
- [ ] ドキュメント整備
- [ ] 運用手順書作成

## 📚 既存システムとの統合

### 連携する既存コンポーネント

1. **Elder Council Summoner** (`libs/elder_council_summoner.py`)
2. **Four Sages Integration** (`libs/four_sages_integration.py`)
3. **Knowledge Base Manager** (`libs/knowledge_base_manager.py`)
4. **Task History DB** (`libs/task_history_db.py`)
5. **Worker Health Monitor** (`libs/worker_health_monitor.py`)

### 統合ポイント

- 既存のRabbitMQ基盤活用
- 知識ベースとの連携強化
- エルダー階層構造との整合性
- 4賢者システムとの統合

---

**策定日**: 2025年7月9日
**策定者**: Claude Elder
**バージョン**: 1.0
**レビュー予定**: Phase 1完了後
