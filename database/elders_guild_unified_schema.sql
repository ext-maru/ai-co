-- ============================================================================
-- エルダーズギルド統合データベーススキーマ
-- 文書番号: ELDERS-DB-2025-001
-- 作成日: 2025年7月11日
-- 承認者: クロードエルダー
-- ============================================================================

-- 拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ============================================================================
-- 1. 知識賢者 (Knowledge Sage) スキーマ
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS knowledge_sage;

-- 知識エンティティテーブル
CREATE TABLE IF NOT EXISTS knowledge_sage.knowledge_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'text',

    -- ベクター検索用 (OpenAI ada-002: 1536次元)
    embedding vector(1536),

    -- メタデータ (JSONB最適化)
    metadata JSONB NOT NULL DEFAULT '{}',

    -- 全文検索用
    search_vector tsvector,

    -- 品質スコア (0.0-1.0)
    quality_score FLOAT DEFAULT 0.0 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),

    -- 分類・タグ
    category VARCHAR(100),
    tags TEXT[],

    -- 階層構造
    parent_id UUID REFERENCES knowledge_sage.knowledge_entities(id),

    -- 監査情報
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    version INTEGER DEFAULT 1,

    -- 統計情報
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE
);

-- 知識関係テーブル
CREATE TABLE IF NOT EXISTS knowledge_sage.knowledge_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES knowledge_sage.knowledge_entities(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES knowledge_sage.knowledge_entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 同じ関係の重複防止
    UNIQUE(source_id, target_id, relationship_type)
);

-- ============================================================================
-- 2. タスク賢者 (Task Sage) スキーマ
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS task_sage;

-- タスクテーブル（パーティション対応）
CREATE TABLE IF NOT EXISTS task_sage.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- ステータス管理
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    priority INTEGER NOT NULL DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),

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
) PARTITION BY RANGE (created_at);

-- 2025年パーティション
CREATE TABLE IF NOT EXISTS task_sage.tasks_2025 PARTITION OF task_sage.tasks
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- ワークフローテーブル
CREATE TABLE IF NOT EXISTS task_sage.workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL, -- DAG定義
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'paused', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    created_by VARCHAR(100)
);

-- ============================================================================
-- 3. インシデント賢者 (Incident Sage) スキーマ
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS incident_sage;

-- インシデントテーブル
CREATE TABLE IF NOT EXISTS incident_sage.incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- 重要度・ステータス
    severity VARCHAR(20) NOT NULL
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'investigating', 'resolved', 'closed')),

    -- 時間管理
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,

    -- 影響範囲
    affected_systems TEXT[],
    impact_level VARCHAR(20) CHECK (impact_level IN ('low', 'medium', 'high', 'critical')),

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
) PARTITION BY RANGE (created_at);

-- 2025年パーティション
CREATE TABLE IF NOT EXISTS incident_sage.incidents_2025 PARTITION OF incident_sage.incidents
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- 時系列メトリクステーブル
CREATE TABLE IF NOT EXISTS incident_sage.metrics (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    tags JSONB DEFAULT '{}',
    source VARCHAR(100),

    PRIMARY KEY (time, metric_name)
);

-- ============================================================================
-- 4. RAG賢者 (RAG Sage) スキーマ
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS rag_sage;

-- 文書テーブル
CREATE TABLE IF NOT EXISTS rag_sage.documents (
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
    language VARCHAR(10) DEFAULT 'ja',
    metadata JSONB DEFAULT '{}',

    -- 統計情報
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,

    -- 品質情報
    quality_score FLOAT DEFAULT 0.0 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    relevance_score FLOAT DEFAULT 0.0 CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),

    -- 監査情報
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- コンテキストテーブル
CREATE TABLE IF NOT EXISTS rag_sage.contexts (
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
    response_quality FLOAT CHECK (response_quality >= 0.0 AND response_quality <= 1.0),

    -- フィードバック
    user_feedback INTEGER CHECK (user_feedback >= 1 AND user_feedback <= 5),
    feedback_text TEXT,

    -- 統計情報
    response_time INTERVAL,
    token_count INTEGER,

    -- 監査情報
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 5. 共通システムスキーマ
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS system_metadata;

-- システム設定テーブル
CREATE TABLE IF NOT EXISTS system_metadata.configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100)
);

-- 監査ログテーブル
CREATE TABLE IF NOT EXISTS system_metadata.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- ============================================================================
-- 6. インデックス作成
-- ============================================================================

-- Knowledge Sage インデックス
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding ON knowledge_sage.knowledge_entities
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);

CREATE INDEX IF NOT EXISTS idx_knowledge_search ON knowledge_sage.knowledge_entities
    USING gin(search_vector);

CREATE INDEX IF NOT EXISTS idx_knowledge_metadata ON knowledge_sage.knowledge_entities
    USING gin(metadata);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_sage.knowledge_entities (category);

CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_sage.knowledge_entities
    USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_knowledge_created_at ON knowledge_sage.knowledge_entities (created_at);

CREATE INDEX IF NOT EXISTS idx_knowledge_quality ON knowledge_sage.knowledge_entities (quality_score DESC);

-- Knowledge Relationships インデックス
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_source ON knowledge_sage.knowledge_relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_target ON knowledge_sage.knowledge_relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_type ON knowledge_sage.knowledge_relationships(relationship_type);

-- Task Sage インデックス
CREATE INDEX IF NOT EXISTS idx_tasks_status ON task_sage.tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON task_sage.tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_scheduled ON task_sage.tasks(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_tasks_dependencies ON task_sage.tasks USING gin(dependencies);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON task_sage.tasks(created_at);

-- Incident Sage インデックス
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incident_sage.incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incident_sage.incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incident_sage.incidents(created_at);
CREATE INDEX IF NOT EXISTS idx_incidents_systems ON incident_sage.incidents USING gin(affected_systems);

CREATE INDEX IF NOT EXISTS idx_metrics_time ON incident_sage.metrics(time);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON incident_sage.metrics(metric_name);

-- RAG Sage インデックス
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON rag_sage.documents
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);

CREATE INDEX IF NOT EXISTS idx_documents_type ON rag_sage.documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_source ON rag_sage.documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_language ON rag_sage.documents(language);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON rag_sage.documents USING gin(metadata);

CREATE INDEX IF NOT EXISTS idx_contexts_session ON rag_sage.contexts(session_id);
CREATE INDEX IF NOT EXISTS idx_contexts_user ON rag_sage.contexts(user_id);
CREATE INDEX IF NOT EXISTS idx_contexts_created ON rag_sage.contexts(created_at);

-- System Metadata インデックス
CREATE INDEX IF NOT EXISTS idx_audit_table_record ON system_metadata.audit_logs(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at ON system_metadata.audit_logs(changed_at);

-- ============================================================================
-- 7. 関数・プロシージャ
-- ============================================================================

-- 全文検索ベクター更新関数
CREATE OR REPLACE FUNCTION knowledge_sage.update_search_vector()
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

-- 更新時刻自動更新関数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- セマンティック検索関数
CREATE OR REPLACE FUNCTION knowledge_sage.semantic_search(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.8,
    max_results int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(500),
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ke.id,
        ke.title,
        ke.content,
        1 - (ke.embedding <=> query_embedding) AS similarity,
        ke.metadata
    FROM knowledge_sage.knowledge_entities ke
    WHERE ke.embedding IS NOT NULL
    AND 1 - (ke.embedding <=> query_embedding) > similarity_threshold
    ORDER BY ke.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 8. トリガー作成
-- ============================================================================

-- 知識エンティティの全文検索ベクター更新
CREATE TRIGGER trigger_knowledge_search_vector
    BEFORE INSERT OR UPDATE ON knowledge_sage.knowledge_entities
    FOR EACH ROW EXECUTE FUNCTION knowledge_sage.update_search_vector();

-- 更新時刻自動更新トリガー
CREATE TRIGGER trigger_knowledge_updated_at
    BEFORE UPDATE ON knowledge_sage.knowledge_entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_workflows_updated_at
    BEFORE UPDATE ON task_sage.workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_documents_updated_at
    BEFORE UPDATE ON rag_sage.documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_config_updated_at
    BEFORE UPDATE ON system_metadata.configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 9. 初期データ挿入
-- ============================================================================

-- システム設定の初期値
INSERT INTO system_metadata.configurations (key, value, description) VALUES
    ('embedding_model', '"text-embedding-ada-002"', 'OpenAI embedding model'),
    ('vector_dimension', '1536', 'Vector embedding dimension'),
    ('similarity_threshold', '0.8', 'Default similarity threshold for search'),
    ('max_search_results', '10', 'Maximum number of search results'),
    ('knowledge_quality_threshold', '0.7', 'Minimum quality score for knowledge'),
    ('auto_vacuum_enabled', 'true', 'Enable automatic vacuum'),
    ('log_retention_days', '90', 'Log retention period in days')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- 10. 権限設定
-- ============================================================================

-- 賢者ロールの作成
CREATE ROLE IF NOT EXISTS knowledge_sage_role;
CREATE ROLE IF NOT EXISTS task_sage_role;
CREATE ROLE IF NOT EXISTS incident_sage_role;
CREATE ROLE IF NOT EXISTS rag_sage_role;
CREATE ROLE IF NOT EXISTS system_admin_role;

-- 権限付与
GRANT USAGE ON SCHEMA knowledge_sage TO knowledge_sage_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA knowledge_sage TO knowledge_sage_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA knowledge_sage TO knowledge_sage_role;

GRANT USAGE ON SCHEMA task_sage TO task_sage_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA task_sage TO task_sage_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA task_sage TO task_sage_role;

GRANT USAGE ON SCHEMA incident_sage TO incident_sage_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA incident_sage TO incident_sage_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA incident_sage TO incident_sage_role;

GRANT USAGE ON SCHEMA rag_sage TO rag_sage_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA rag_sage TO rag_sage_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA rag_sage TO rag_sage_role;

GRANT USAGE ON SCHEMA system_metadata TO system_admin_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA system_metadata TO system_admin_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA system_metadata TO system_admin_role;

-- 読み取り専用ロール
CREATE ROLE IF NOT EXISTS readonly_role;
GRANT USAGE ON ALL SCHEMAS IN DATABASE current_database() TO readonly_role;
GRANT SELECT ON ALL TABLES IN DATABASE current_database() TO readonly_role;

-- ============================================================================
-- 11. 統計情報・メンテナンス
-- ============================================================================

-- 統計情報の更新
ANALYZE knowledge_sage.knowledge_entities;
ANALYZE task_sage.tasks;
ANALYZE incident_sage.incidents;
ANALYZE rag_sage.documents;

-- 自動VACUUM設定
ALTER TABLE knowledge_sage.knowledge_entities SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE task_sage.tasks SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE incident_sage.incidents SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE rag_sage.documents SET (autovacuum_vacuum_scale_factor = 0.1);

-- ============================================================================
-- スキーマ作成完了
-- ============================================================================

-- 完了メッセージ
SELECT 'エルダーズギルド統合データベーススキーマ作成完了!' as message;
SELECT 'Created schemas: knowledge_sage, task_sage, incident_sage, rag_sage, system_metadata' as schemas;
SELECT 'pgvector extension ready for semantic search' as vector_status;
SELECT 'Full-text search configured for Japanese and English' as search_status;
