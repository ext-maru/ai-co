---
audience: administrators
author: claude-elder
category: technical
dependencies: []
description: '---'
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: draft
subcategory: research
tags:
- technical
- docker
- postgresql
- four-sages
title: PostgreSQL最適化戦略 - エルダーズギルド統合プラットフォーム
version: 1.0.0
---

# PostgreSQL最適化戦略 - エルダーズギルド統合プラットフォーム

**文書番号**: ELDERS-POSTGRESQL-2025-001
**作成日**: 2025年7月11日
**作成者**: Four Sages Database Committee
**承認者**: クロードエルダー

---

## 1. 現状分析

### 1.1 現在のPostgreSQL使用状況

```yaml
発見されたPostgreSQL実装:
  elders-guild-web:
    - イメージ: pgvector/pgvector:pg16
    - 使用目的: ベクター検索対応
    - 特徴: AI/ML向け最適化済み

  contract-upload-system:
    - イメージ: postgres:15
    - 使用目的: 基本的なデータ保存
    - 特徴: 標準実装

  upload-image-service:
    - イメージ: postgres:15-alpine
    - 使用目的: 軽量実装
    - 特徴: 最小構成
```

### 1.2 現在の問題点

```yaml
発見された問題:
  設定の分散:
    - 3つの異なる実装
    - 統一されていない設定
    - 重複するリソース

  機能の未活用:
    - 基本的なCRUD操作のみ
    - 高度なPostgreSQL機能未使用
    - パフォーマンスチューニング不足

  セキュリティの課題:
    - 平文パスワード使用
    - 権限管理の不備
    - 監査ログの不足
```

---

## 2. PostgreSQL最適化戦略

### 2.1 エルダーズギルド統合PostgreSQL設計

```yaml
統合PostgreSQL設計:
  Base Configuration:
    - Version: PostgreSQL 16
    - Extensions: pgvector, pg_stat_statements, pg_cron
    - Architecture: Master-Slave with Read Replicas
    - Connection Pooling: PgBouncer

  Database Schema:
    elders_guild_unified:
      - knowledge_base (Knowledge Sage)
      - task_management (Task Sage)
      - incident_tracking (Incident Sage)
      - rag_contexts (RAG Sage)
      - system_metadata (Shared)
      - audit_logs (Compliance)
```

### 2.2 4賢者特化データベース設計

#### 2.2.1 Knowledge Sage Database

```sql
-- Knowledge Sage専用スキーマ
CREATE SCHEMA knowledge_sage;

-- 知識エンティティテーブル
CREATE TABLE knowledge_sage.knowledge_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,

    -- ベクター検索用
    embedding vector(1536),

    -- メタデータ (JSONB最適化)
    metadata JSONB NOT NULL DEFAULT '{}',

    -- 全文検索用
    search_vector tsvector,

    -- 品質スコア
    quality_score FLOAT DEFAULT 0.0,

    -- 分類・タグ
    category VARCHAR(100),
    tags TEXT[],

    -- 関係性
    parent_id UUID REFERENCES knowledge_sage.knowledge_entities(id),

    -- 監査情報
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    version INTEGER DEFAULT 1
);

-- ベクター検索用インデックス
CREATE INDEX idx_knowledge_embedding ON knowledge_sage.knowledge_entities
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);

-- 全文検索用インデックス
CREATE INDEX idx_knowledge_search ON knowledge_sage.knowledge_entities
USING gin(search_vector);

-- メタデータ検索用インデックス
CREATE INDEX idx_knowledge_metadata ON knowledge_sage.knowledge_entities
USING gin(metadata);

-- 知識関係テーブル
CREATE TABLE knowledge_sage.knowledge_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES knowledge_sage.knowledge_entities(id),
    target_id UUID NOT NULL REFERENCES knowledge_sage.knowledge_entities(id),
    relationship_type VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 関係性検索用インデックス
CREATE INDEX idx_knowledge_rel_source ON knowledge_sage.knowledge_relationships(source_id);
CREATE INDEX idx_knowledge_rel_target ON knowledge_sage.knowledge_relationships(target_id);
CREATE INDEX idx_knowledge_rel_type ON knowledge_sage.knowledge_relationships(relationship_type);
```

#### 2.2.2 Task Sage Database

```sql
-- Task Sage専用スキーマ
CREATE SCHEMA task_sage;

-- タスクテーブル
CREATE TABLE task_sage.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- ステータス管理
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 5,

    -- 時間管理
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    deadline TIMESTAMP WITH TIME ZONE,

    -- 依存関係
    dependencies UUID[],

    -- リソース要件
    resource_requirements JSONB DEFAULT '{}',

    -- 実行結果
    result JSONB DEFAULT '{}',
    error_message TEXT,

    -- 実行統計
    execution_time INTERVAL,
    retry_count INTEGER DEFAULT 0,

    -- 監査情報
    created_by VARCHAR(100),
    assigned_to VARCHAR(100),

    -- パーティション用
    partition_date DATE GENERATED ALWAYS AS (DATE(created_at)) STORED
);

-- パーティションテーブル作成
CREATE TABLE task_sage.tasks_2025 PARTITION OF task_sage.tasks
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- インデックス
CREATE INDEX idx_tasks_status ON task_sage.tasks(status);
CREATE INDEX idx_tasks_priority ON task_sage.tasks(priority);
CREATE INDEX idx_tasks_scheduled ON task_sage.tasks(scheduled_at);
CREATE INDEX idx_tasks_dependencies ON task_sage.tasks USING gin(dependencies);

-- ワークフローテーブル
CREATE TABLE task_sage.workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL, -- DAG定義
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1
);
```

#### 2.2.3 Incident Sage Database

```sql
-- Incident Sage専用スキーマ
CREATE SCHEMA incident_sage;

-- インシデントテーブル
CREATE TABLE incident_sage.incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- 重要度・ステータス
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',

    -- 時間管理
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,

    -- 影響範囲
    affected_systems TEXT[],
    impact_level VARCHAR(20),

    -- 担当者
    assignee VARCHAR(100),
    resolver VARCHAR(100),

    -- 解決情報
    root_cause TEXT,
    resolution TEXT,

    -- メタデータ
    metadata JSONB DEFAULT '{}',

    -- パーティション用
    partition_date DATE GENERATED ALWAYS AS (DATE(created_at)) STORED
);

-- 時系列データ用テーブル（TimescaleDB拡張使用）
CREATE TABLE incident_sage.metrics (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    tags JSONB DEFAULT '{}',
    source VARCHAR(100),

    PRIMARY KEY (time, metric_name)
);

-- TimescaleDB ハイパーテーブル化
SELECT create_hypertable('incident_sage.metrics', 'time');

-- 自動データ圧縮
SELECT add_compression_policy('incident_sage.metrics', INTERVAL '7 days');

-- 古いデータの自動削除
SELECT add_retention_policy('incident_sage.metrics', INTERVAL '90 days');
```

#### 2.2.4 RAG Sage Database

```sql
-- RAG Sage専用スキーマ
CREATE SCHEMA rag_sage;

-- 文書テーブル
CREATE TABLE rag_sage.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,

    -- ベクター検索
    embedding vector(1536),

    -- メタデータ
    source VARCHAR(200),
    source_url TEXT,
    document_type VARCHAR(50),
    metadata JSONB DEFAULT '{}',

    -- 統計情報
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,

    -- 品質情報
    quality_score FLOAT DEFAULT 0.0,
    relevance_score FLOAT DEFAULT 0.0,

    -- 監査情報
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 文書検索用インデックス
CREATE INDEX idx_documents_embedding ON rag_sage.documents
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);

CREATE INDEX idx_documents_type ON rag_sage.documents(document_type);
CREATE INDEX idx_documents_source ON rag_sage.documents(source);
CREATE INDEX idx_documents_metadata ON rag_sage.documents USING gin(metadata);

-- コンテキストテーブル
CREATE TABLE rag_sage.contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    user_id VARCHAR(100),

    -- クエリ情報
    query TEXT NOT NULL,
    query_embedding vector(1536),

    -- 検索結果
    retrieved_documents UUID[],
    search_results JSONB,

    -- 回答情報
    response TEXT,
    response_quality FLOAT,

    -- フィードバック
    user_feedback INTEGER, -- 1-5スケール
    feedback_text TEXT,

    -- 統計情報
    response_time INTERVAL,
    token_count INTEGER,

    -- 監査情報
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- コンテキスト検索用インデックス
CREATE INDEX idx_contexts_session ON rag_sage.contexts(session_id);
CREATE INDEX idx_contexts_user ON rag_sage.contexts(user_id);
CREATE INDEX idx_contexts_created ON rag_sage.contexts(created_at);
```

---

## 3. 高度なPostgreSQL機能活用

### 3.1 ベクター検索最適化

```sql
-- pgvector 最適化設定
SET maintenance_work_mem = '2GB';
SET max_parallel_workers_per_gather = 4;

-- HNSW インデックス（より高速な検索）
CREATE INDEX idx_knowledge_embedding_hnsw ON knowledge_sage.knowledge_entities
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- 検索クエリ最適化
CREATE OR REPLACE FUNCTION knowledge_sage.semantic_search(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.8,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(500),
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ke.id,
        ke.title,
        ke.content,
        1 - (ke.embedding <=> query_embedding) AS similarity
    FROM knowledge_sage.knowledge_entities ke
    WHERE 1 - (ke.embedding <=> query_embedding) > similarity_threshold
    ORDER BY ke.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
```

### 3.2 全文検索最適化

```sql
-- 多言語対応全文検索
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('japanese', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('japanese', COALESCE(NEW.content, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- トリガー作成
CREATE TRIGGER trigger_update_search_vector
    BEFORE INSERT OR UPDATE ON knowledge_sage.knowledge_entities
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

### 3.3 JSON/JSONB最適化

```sql
-- JSONB操作最適化
CREATE INDEX idx_knowledge_metadata_gin ON knowledge_sage.knowledge_entities
USING gin (metadata jsonb_path_ops);

-- 特定のJSONBフィールドにインデックス
CREATE INDEX idx_knowledge_category ON knowledge_sage.knowledge_entities
USING btree ((metadata->>'category'));

-- JSONB検索関数
CREATE OR REPLACE FUNCTION knowledge_sage.search_by_metadata(
    search_criteria JSONB
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(500),
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT ke.id, ke.title, ke.metadata
    FROM knowledge_sage.knowledge_entities ke
    WHERE ke.metadata @> search_criteria;
END;
$$ LANGUAGE plpgsql;
```

### 3.4 パーティショニング戦略

```sql
-- 時間ベースパーティショニング
CREATE TABLE task_sage.tasks_partitioned (
    LIKE task_sage.tasks INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 月別パーティション作成
DO $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..11 LOOP
        start_date := DATE('2025-01-01') + (i || ' months')::INTERVAL;
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'tasks_' || to_char(start_date, 'YYYY_MM');

        EXECUTE format('CREATE TABLE task_sage.%I PARTITION OF task_sage.tasks_partitioned
                       FOR VALUES FROM (%L) TO (%L)',
                       partition_name, start_date, end_date);
    END LOOP;
END $$;
```

---

## 4. パフォーマンス最適化

### 4.1 postgresql.conf最適化

```ini
# エルダーズギルド最適化設定
# Memory Settings
shared_buffers = 4GB                    # 利用可能メモリの25%
effective_cache_size = 12GB             # 利用可能メモリの75%
work_mem = 256MB                        # 複雑クエリ用
maintenance_work_mem = 1GB              # メンテナンス操作用

# Connection Settings
max_connections = 200                   # 同時接続数
superuser_reserved_connections = 3

# Checkpoint Settings
checkpoint_timeout = 15min
checkpoint_completion_target = 0.9
max_wal_size = 2GB
min_wal_size = 1GB

# Performance Settings
random_page_cost = 1.1                 # SSD最適化
effective_io_concurrency = 200         # 並列I/O
default_statistics_target = 100        # 統計情報精度

# Logging Settings
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_duration_statement = 1000      # 1秒以上のクエリをログ
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# Monitoring Settings
shared_preload_libraries = 'pg_stat_statements'
track_activities = on
track_counts = on
track_io_timing = on
track_functions = all
```

### 4.2 接続プーリング設定

```ini
# PgBouncer設定
[databases]
elders_guild = host=localhost port=5432 dbname=elders_guild

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/users.txt

# Pool settings
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 100
reserve_pool_size = 25
reserve_pool_timeout = 3

# Performance
server_reset_query = DISCARD ALL
server_check_query = SELECT 1
server_check_delay = 10
```

### 4.3 読み取り専用レプリカ設定

```yaml
# Docker Compose - Master-Slave構成
services:
  postgres-master:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: elders_guild
      POSTGRES_USER: elder_admin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: ${REPLICATION_PASSWORD}
    command: |
      postgres
      -c wal_level=replica
      -c max_wal_senders=10
      -c max_replication_slots=10
      -c hot_standby=on
    volumes:
      - postgres_master_data:/var/lib/postgresql/data
      - ./postgresql.conf:/etc/postgresql/postgresql.conf

  postgres-slave:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_MASTER_SERVICE: postgres-master
      POSTGRES_SLAVE_SERVICE: postgres-slave
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: ${REPLICATION_PASSWORD}
    command: |
      bash -c "
      pg_basebackup -h postgres-master -D /var/lib/postgresql/data -U replicator -v -P -W
      echo 'standby_mode = on' >> /var/lib/postgresql/data/recovery.conf
      echo 'primary_conninfo = host=postgres-master port=5432 user=replicator' >> /var/lib/postgresql/data/recovery.conf
      postgres
      "
    depends_on:
      - postgres-master
    volumes:
      - postgres_slave_data:/var/lib/postgresql/data
```

---

## 5. 監視・メトリクス

### 5.1 PostgreSQL監視設定

```sql
-- パフォーマンス監視ビュー
CREATE VIEW monitoring.database_performance AS
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables;

-- 接続状況監視
CREATE VIEW monitoring.connection_status AS
SELECT
    datname,
    count(*) as connections,
    count(*) FILTER (WHERE state = 'active') as active_connections,
    count(*) FILTER (WHERE state = 'idle') as idle_connections,
    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
FROM pg_stat_activity
GROUP BY datname;

-- 長時間実行クエリ監視
CREATE VIEW monitoring.long_running_queries AS
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state,
    client_addr
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
AND state = 'active';
```

### 5.2 アラート設定

```sql
-- 監視プロシージャ
CREATE OR REPLACE FUNCTION monitoring.check_database_health()
RETURNS TEXT AS $$
DECLARE
    result TEXT := 'OK';
    long_queries INTEGER;
    blocked_queries INTEGER;
    connection_count INTEGER;
BEGIN
    -- 長時間実行クエリチェック
    SELECT COUNT(*) INTO long_queries FROM monitoring.long_running_queries;
    IF long_queries > 5 THEN
        result := result || '; Long queries: ' || long_queries;
    END IF;

    -- ブロックされたクエリチェック
    SELECT COUNT(*) INTO blocked_queries
    FROM pg_stat_activity
    WHERE wait_event IS NOT NULL AND state = 'active';
    IF blocked_queries > 10 THEN
        result := result || '; Blocked queries: ' || blocked_queries;
    END IF;

    -- 接続数チェック
    SELECT COUNT(*) INTO connection_count FROM pg_stat_activity;
    IF connection_count > 150 THEN
        result := result || '; High connections: ' || connection_count;
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 定期実行（pg_cron使用）
SELECT cron.schedule('database-health-check', '*/5 * * * *', 'SELECT monitoring.check_database_health()');
```

---

## 6. ELDERS-UNITY-2025 プロジェクト統合

### 6.1 プロジェクト計画への追加項目

```yaml
PostgreSQL最適化フェーズ:
  Phase 1.5: データベース基盤強化 (Month 1-2)
    Week 1-2: 統合PostgreSQL設計
      - 4賢者専用スキーマ設計
      - ベクター検索最適化
      - パーティショニング戦略

    Week 3-4: 高度機能実装
      - pgvector統合
      - 全文検索最適化
      - JSON/JSONB活用

  Phase 2.5: パフォーマンス最適化 (Month 4-5)
    Week 1-2: 接続プーリング
      - PgBouncer導入
      - 読み取り専用レプリカ
      - 負荷分散設定

    Week 3-4: 監視・チューニング
      - パフォーマンス監視
      - 自動チューニング
      - アラート設定
```

### 6.2 コスト影響

```yaml
追加コスト:
  インフラ: +¥3,000,000/年
    - 高性能データベースサーバー
    - 読み取り専用レプリカ
    - 監視・バックアップストレージ

  人件費: +¥2,000,000
    - データベース専門エンジニア (2ヶ月)
    - パフォーマンスチューニング
    - 監視設定・運用設計

  ツール: +¥500,000/年
    - 監視ツール
    - バックアップソリューション
    - パフォーマンス分析ツール
```

### 6.3 期待効果

```yaml
パフォーマンス改善:
  - クエリ応答時間: 80%短縮
  - 同時接続数: 5倍向上
  - データ検索精度: 95%向上
  - システム可用性: 99.95%

機能強化:
  - ベクター検索: セマンティック検索実現
  - 全文検索: 多言語対応
  - リアルタイム分析: 時系列データ活用
  - 自動最適化: 継続的パフォーマンス改善
```

---

## 7. 実装優先順位

### 7.1 Phase 1 (緊急): 基盤統合

1. **統合データベース設計**
   - 4賢者専用スキーマ作成
   - 基本テーブル設計
   - インデックス戦略

2. **pgvector導入**
   - ベクター検索機能
   - Knowledge Sage統合
   - RAG Sage統合

### 7.2 Phase 2 (高優先): パフォーマンス最適化

1. **接続プーリング**
   - PgBouncer導入
   - 接続管理最適化

2. **読み取り専用レプリカ**
   - マスター・スレーブ構成
   - 読み取り負荷分散

### 7.3 Phase 3 (中優先): 高度機能

1. **パーティショニング**
   - 時間ベースパーティション
   - 大量データ対応

2. **監視・アラート**
   - リアルタイム監視
   - 自動アラート

---

## 8. 結論

PostgreSQL最適化により、エルダーズギルド統合プラットフォームは以下を実現します：

1. **統合された知識基盤**: 4賢者が共有する統一データベース
2. **高性能ベクター検索**: AI/ML機能の基盤
3. **スケーラブルな設計**: 将来の成長に対応
4. **企業グレードの信頼性**: 99.95%の可用性

この戦略により、エルダーズギルドは真に統合された高性能AIプラットフォームとして機能します。

---

**承認**:
- Database Architect: ________________
- Four Sages Committee: ________________
- Infrastructure Team: ________________

**文書管理番号**: ELDERS-POSTGRESQL-2025-001
**次回レビュー**: 2025年8月11日
