-- Elders Guild Projects Portfolio Database
-- プロジェクトポートフォリオ管理用データベース

-- データベース権限設定
GRANT ALL PRIVILEGES ON DATABASE projects_portfolio TO projects_admin;
GRANT ALL ON SCHEMA public TO projects_admin;

-- プロジェクトマスターテーブル
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL UNIQUE,
    project_path VARCHAR(500) NOT NULL,
    description TEXT,
    project_type VARCHAR(100), -- 'web', 'api', 'desktop', 'mobile', 'service'
    language VARCHAR(50),
    framework VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'maintenance', 'deprecated', 'development'
    port_number INTEGER,
    docker_image VARCHAR(255),
    repository_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_deployment TIMESTAMP WITH TIME ZONE,
    version VARCHAR(50),
    metadata JSONB
);

-- プロジェクト健全性監視テーブル
CREATE TABLE IF NOT EXISTS project_health (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    status_code INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    health_score REAL -- 0.0 - 1.0
);

-- プロジェクト利用統計テーブル
CREATE TABLE IF NOT EXISTS project_usage (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    request_count INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_response_time_ms REAL,
    date_recorded DATE DEFAULT CURRENT_DATE
);

-- プロジェクト設定テーブル
CREATE TABLE IF NOT EXISTS project_configs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    config_key VARCHAR(255) NOT NULL,
    config_value TEXT,
    config_type VARCHAR(50) DEFAULT 'string', -- 'string', 'json', 'number', 'boolean'
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- プロジェクトデプロイメント履歴テーブル
CREATE TABLE IF NOT EXISTS project_deployments (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    version VARCHAR(50),
    deployment_status VARCHAR(50), -- 'success', 'failed', 'in_progress', 'rolled_back'
    deployment_log TEXT,
    deployed_by VARCHAR(255),
    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rollback_at TIMESTAMP WITH TIME ZONE,
    environment VARCHAR(50) DEFAULT 'production' -- 'development', 'staging', 'production'
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects (project_name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects (status);
CREATE INDEX IF NOT EXISTS idx_projects_type ON projects (project_type);
CREATE INDEX IF NOT EXISTS idx_project_health_project_id ON project_health (project_id);
CREATE INDEX IF NOT EXISTS idx_project_health_checked_at ON project_health (checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_usage_project_id ON project_usage (project_id);
CREATE INDEX IF NOT EXISTS idx_project_usage_date ON project_usage (date_recorded DESC);
CREATE INDEX IF NOT EXISTS idx_project_configs_project_id ON project_configs (project_id);
CREATE INDEX IF NOT EXISTS idx_project_deployments_project_id ON project_deployments (project_id);

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

DROP TRIGGER IF EXISTS update_project_configs_updated_at ON project_configs;
CREATE TRIGGER update_project_configs_updated_at 
    BEFORE UPDATE ON project_configs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 初期データ挿入
INSERT INTO projects (
    project_name, project_path, description, project_type, language, framework,
    port_number, docker_image, status, version, metadata
) VALUES (
    'image-upload-manager',
    '/projects/image-upload-manager',
    '顧客画像アップロード管理システム - Google Drive連携対応',
    'web',
    'python',
    'flask',
    5000,
    'elders-guild-image-upload-manager:latest',
    'active',
    '1.0.0',
    '{"test_coverage": 85, "last_test_run": "2025-07-10", "dependencies": ["flask", "pillow", "google-drive-api"]}'
) ON CONFLICT (project_name) DO UPDATE SET
    description = EXCLUDED.description,
    updated_at = NOW();

-- 初期設定データ
INSERT INTO project_configs (project_id, config_key, config_value, config_type) VALUES
((SELECT id FROM projects WHERE project_name = 'image-upload-manager'), 'FLASK_ENV', 'production', 'string'),
((SELECT id FROM projects WHERE project_name = 'image-upload-manager'), 'MAX_UPLOAD_SIZE', '50485760', 'number'),
((SELECT id FROM projects WHERE project_name = 'image-upload-manager'), 'GOOGLE_DRIVE_ENABLED', 'false', 'boolean'),
((SELECT id FROM projects WHERE project_name = 'image-upload-manager'), 'ALLOWED_EXTENSIONS', '["jpg", "jpeg", "png", "gif"]', 'json')
ON CONFLICT DO NOTHING;

-- 権限設定
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO projects_admin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO projects_admin;

-- 完了ログ
INSERT INTO project_usage (project_id, request_count, unique_visitors, error_count, avg_response_time_ms) VALUES
((SELECT id FROM projects WHERE project_name = 'image-upload-manager'), 0, 0, 0, 0.0);

COMMIT;