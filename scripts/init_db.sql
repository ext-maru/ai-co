-- Elders Guild Project Web Portal - Database Initialization
-- RAGエルダー推奨pgvector統合データベース

-- pgvector拡張を有効化
CREATE EXTENSION IF NOT EXISTS vector;

-- ユーザー作成（既存の場合はスキップ）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'elder_admin') THEN
        CREATE ROLE elder_admin WITH LOGIN PASSWORD 'sage_wisdom_2025';
    END IF;
END
$$;

-- データベース権限設定
GRANT ALL PRIVILEGES ON DATABASE elders_guild TO elder_admin;
GRANT ALL ON SCHEMA public TO elder_admin;

-- プロジェクトテーブル
CREATE TABLE IF NOT EXISTS projects (
    project_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    project_type VARCHAR(50),
    status VARCHAR(50),
    tech_stack JSONB,
    description TEXT,
    metadata_json JSONB,
    feature_vector vector(50),  -- 特徴ベクトル
    semantic_vector vector(1536),  -- OpenAI embeddings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- プロジェクトドキュメントテーブル
CREATE TABLE IF NOT EXISTS project_documentation (
    project_id VARCHAR(32) PRIMARY KEY,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    overview TEXT,
    architecture TEXT,
    setup_guide TEXT,
    api_reference TEXT,
    usage_examples TEXT,
    diagrams_json JSONB,
    quality_score REAL,
    related_projects JSONB,
    FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE
);

-- 類似プロジェクト検索用テーブル
CREATE TABLE IF NOT EXISTS project_similarities (
    id SERIAL PRIMARY KEY,
    source_project_id VARCHAR(32),
    target_project_id VARCHAR(32),
    similarity_score REAL,
    similarity_type VARCHAR(50), -- 'feature', 'semantic', 'tech_stack'
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (source_project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    FOREIGN KEY (target_project_id) REFERENCES projects (project_id) ON DELETE CASCADE
);

-- システムメトリクステーブル
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value REAL,
    metric_data JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 検索履歴テーブル
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    query TEXT,
    results_count INTEGER,
    execution_time_ms REAL,
    user_ip INET,
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成

-- プロジェクト検索用インデックス
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_projects_description ON projects USING gin(to_tsvector('english', description));
CREATE INDEX IF NOT EXISTS idx_projects_tech_stack ON projects USING gin(tech_stack);
CREATE INDEX IF NOT EXISTS idx_projects_type_status ON projects (project_type, status);
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects (updated_at DESC);

-- ベクトル検索用HNSWインデックス（pgvector）
CREATE INDEX IF NOT EXISTS idx_projects_feature_vector_hnsw 
ON projects USING hnsw (feature_vector vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_projects_semantic_vector_hnsw 
ON projects USING hnsw (semantic_vector vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- 類似度検索用インデックス
CREATE INDEX IF NOT EXISTS idx_similarities_source ON project_similarities (source_project_id, similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_similarities_target ON project_similarities (target_project_id, similarity_score DESC);

-- システムメトリクス用インデックス
CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON system_metrics (metric_name, recorded_at DESC);

-- トリガー関数：更新日時自動更新
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- トリガー作成
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 初期データ挿入
INSERT INTO system_metrics (metric_name, metric_value, metric_data) 
VALUES 
    ('database_initialized', 1, '{"version": "1.0.0", "initialized_at": "' || NOW() || '"}'),
    ('pgvector_enabled', 1, '{"extension": "vector", "status": "active"}')
ON CONFLICT DO NOTHING;

-- サンプルプロジェクト（開発・テスト用）
INSERT INTO projects (
    project_id, name, path, project_type, status, tech_stack, description,
    metadata_json, created_at, updated_at
) VALUES (
    'sample_project_001',
    'Elders Guild Project Portal',
    '/home/aicompany/ai_co',
    'application',
    'active',
    '["python", "fastapi", "nextjs", "postgresql", "docker"]',
    'RAGエルダー推奨による高度なプロジェクト管理・自動資料生成システム',
    '{"lines_of_code": 50000, "files": 150, "complexity": 0.85}',
    NOW() - INTERVAL '7 days',
    NOW()
) ON CONFLICT (project_id) DO NOTHING;

-- 権限設定
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO elder_admin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO elder_admin;

-- 完了ログ
INSERT INTO system_metrics (metric_name, metric_value, metric_data) 
VALUES ('database_setup_complete', 1, '{"completed_at": "' || NOW() || '", "status": "success"}');

COMMIT;