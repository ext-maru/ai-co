-- AI Company 統合データベーススキーマ v1.0
-- ナレッジ・インシデント・タスク統合管理

-- ============================================
-- 統一エンティティテーブル
-- ============================================

-- メインエンティティテーブル
CREATE TABLE IF NOT EXISTS unified_entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('knowledge', 'incident', 'task', 'worker', 'system')),
    title TEXT NOT NULL,
    content TEXT,
    metadata JSON NOT NULL DEFAULT '{}',
    relationships JSON NOT NULL DEFAULT '{}',
    search_metadata JSON NOT NULL DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 型別特殊フィールド
    knowledge_data JSON DEFAULT NULL,  -- 知識特有データ
    incident_data JSON DEFAULT NULL,   -- インシデント特有データ
    task_data JSON DEFAULT NULL,       -- タスク特有データ
    worker_data JSON DEFAULT NULL      -- ワーカー特有データ
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_entities_type ON unified_entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_created ON unified_entities(created_at);
CREATE INDEX IF NOT EXISTS idx_entities_updated ON unified_entities(updated_at);
CREATE INDEX IF NOT EXISTS idx_entities_title ON unified_entities(title);

-- JSONフィールド用インデックス
CREATE INDEX IF NOT EXISTS idx_entities_status ON unified_entities(
    json_extract(metadata, '$.status')
);
CREATE INDEX IF NOT EXISTS idx_entities_priority ON unified_entities(
    json_extract(metadata, '$.priority')
);
CREATE INDEX IF NOT EXISTS idx_entities_category ON unified_entities(
    json_extract(metadata, '$.category')
);

-- ============================================
-- エンティティ関係性テーブル
-- ============================================

CREATE TABLE IF NOT EXISTS entity_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata JSON DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    
    UNIQUE(source_id, target_id, relationship_type),
    FOREIGN KEY (source_id) REFERENCES unified_entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES unified_entities(id) ON DELETE CASCADE
);

-- 関係性インデックス
CREATE INDEX IF NOT EXISTS idx_rel_source ON entity_relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON entity_relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_rel_type ON entity_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_rel_weight ON entity_relationships(weight);

-- ============================================
-- 検索インデックステーブル
-- ============================================

CREATE TABLE IF NOT EXISTS search_index (
    entity_id TEXT PRIMARY KEY,
    content_vector BLOB,           -- ベクトル埋め込み
    keywords TEXT,                 -- キーワード (カンマ区切り)
    indexed_content TEXT,          -- 検索用正規化コンテンツ
    embedding_model TEXT DEFAULT 'text-embedding-ada-002',
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (entity_id) REFERENCES unified_entities(id) ON DELETE CASCADE
);

-- 検索インデックス
CREATE INDEX IF NOT EXISTS idx_search_keywords ON search_index(keywords);
CREATE INDEX IF NOT EXISTS idx_search_indexed_at ON search_index(indexed_at);

-- ============================================
-- 使用統計・効果測定テーブル
-- ============================================

CREATE TABLE IF NOT EXISTS entity_usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    usage_type TEXT NOT NULL,      -- 'search', 'reference', 'resolve', 'create'
    context JSON DEFAULT '{}',     -- 使用コンテキスト
    outcome BOOLEAN,               -- 成功/失敗
    effectiveness_score REAL,     -- 効果スコア (0.0-1.0)
    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    used_by TEXT,                  -- 使用者/システム
    
    FOREIGN KEY (entity_id) REFERENCES unified_entities(id) ON DELETE CASCADE
);

-- 使用統計インデックス
CREATE INDEX IF NOT EXISTS idx_usage_entity ON entity_usage_stats(entity_id);
CREATE INDEX IF NOT EXISTS idx_usage_type ON entity_usage_stats(usage_type);
CREATE INDEX IF NOT EXISTS idx_usage_date ON entity_usage_stats(used_at);
CREATE INDEX IF NOT EXISTS idx_usage_outcome ON entity_usage_stats(outcome);

-- ============================================
-- 学習・進化追跡テーブル
-- ============================================

CREATE TABLE IF NOT EXISTS learning_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,      -- 'auto_knowledge_creation', 'relationship_discovery', 'effectiveness_update'
    source_entity_id TEXT,
    target_entity_id TEXT,
    learning_data JSON NOT NULL,
    confidence_score REAL,
    applied BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified_at DATETIME,
    verified_by TEXT,
    
    FOREIGN KEY (source_entity_id) REFERENCES unified_entities(id),
    FOREIGN KEY (target_entity_id) REFERENCES unified_entities(id)
);

-- 学習イベントインデックス
CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_events(event_type);
CREATE INDEX IF NOT EXISTS idx_learning_source ON learning_events(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_learning_applied ON learning_events(applied);
CREATE INDEX IF NOT EXISTS idx_learning_verified ON learning_events(verified);

-- ============================================
-- システム設定・メタデータテーブル
-- ============================================

CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value JSON NOT NULL,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT DEFAULT 'system'
);

-- システム設定初期値
INSERT OR IGNORE INTO system_metadata (key, value, description) VALUES
('schema_version', '"1.0"', 'データベーススキーマバージョン'),
('last_migration', '"2025-07-06"', '最後のマイグレーション日時'),
('search_model', '"text-embedding-ada-002"', '使用中の埋め込みモデル'),
('learning_threshold', '0.7', '自動学習の信頼度閾値'),
('knowledge_quality_threshold', '0.8', '知識品質の最小閾値');

-- ============================================
-- ビュー定義
-- ============================================

-- 知識エンティティビュー
CREATE VIEW IF NOT EXISTS knowledge_entities AS
SELECT 
    id,
    title,
    content,
    metadata,
    knowledge_data,
    json_extract(knowledge_data, '$.confidence_score') as confidence_score,
    json_extract(knowledge_data, '$.verification_status') as verification_status,
    json_extract(knowledge_data, '$.usage_count') as usage_count,
    json_extract(knowledge_data, '$.effectiveness_rating') as effectiveness_rating,
    created_at,
    updated_at
FROM unified_entities 
WHERE type = 'knowledge';

-- インシデントエンティティビュー
CREATE VIEW IF NOT EXISTS incident_entities AS
SELECT 
    id,
    title,
    content,
    metadata,
    incident_data,
    json_extract(incident_data, '$.severity') as severity,
    json_extract(incident_data, '$.status') as status,
    json_extract(incident_data, '$.affected_systems') as affected_systems,
    json_extract(incident_data, '$.root_cause') as root_cause,
    created_at,
    updated_at
FROM unified_entities 
WHERE type = 'incident';

-- タスクエンティティビュー
CREATE VIEW IF NOT EXISTS task_entities AS
SELECT 
    id,
    title,
    content,
    metadata,
    task_data,
    json_extract(task_data, '$.task_type') as task_type,
    json_extract(task_data, '$.status') as status,
    json_extract(task_data, '$.assigned_worker') as assigned_worker,
    json_extract(task_data, '$.completion_percentage') as completion_percentage,
    created_at,
    updated_at
FROM unified_entities 
WHERE type = 'task';

-- 効果的な知識ビュー（高評価・高使用率）
CREATE VIEW IF NOT EXISTS effective_knowledge AS
SELECT 
    ke.*,
    COALESCE(avg_stats.avg_effectiveness, 0.0) as avg_effectiveness,
    COALESCE(usage_stats.usage_count, 0) as total_usage_count
FROM knowledge_entities ke
LEFT JOIN (
    SELECT 
        entity_id,
        AVG(effectiveness_score) as avg_effectiveness
    FROM entity_usage_stats 
    WHERE effectiveness_score IS NOT NULL
    GROUP BY entity_id
) avg_stats ON ke.id = avg_stats.entity_id
LEFT JOIN (
    SELECT 
        entity_id,
        COUNT(*) as usage_count
    FROM entity_usage_stats
    GROUP BY entity_id
) usage_stats ON ke.id = usage_stats.entity_id
WHERE ke.verification_status = 'verified'
ORDER BY avg_effectiveness DESC, total_usage_count DESC;

-- ============================================
-- トリガー定義
-- ============================================

-- エンティティ更新時刻自動更新
CREATE TRIGGER IF NOT EXISTS update_entity_timestamp
    AFTER UPDATE ON unified_entities
BEGIN
    UPDATE unified_entities 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- 検索インデックス自動更新
CREATE TRIGGER IF NOT EXISTS auto_update_search_index
    AFTER UPDATE OF content, title ON unified_entities
BEGIN
    UPDATE search_index 
    SET 
        keywords = lower(NEW.title || ' ' || COALESCE(NEW.content, '')),
        indexed_content = NEW.title || ' ' || COALESCE(NEW.content, ''),
        indexed_at = CURRENT_TIMESTAMP
    WHERE entity_id = NEW.id;
END;

-- 新規エンティティの検索インデックス作成
CREATE TRIGGER IF NOT EXISTS auto_create_search_index
    AFTER INSERT ON unified_entities
BEGIN
    INSERT INTO search_index (entity_id, keywords, indexed_content)
    VALUES (
        NEW.id,
        lower(NEW.title || ' ' || COALESCE(NEW.content, '')),
        NEW.title || ' ' || COALESCE(NEW.content, '')
    );
END;

-- ============================================
-- データマイグレーション用プロシージャ
-- ============================================

-- 既存ナレッジベースファイルのインポート準備
CREATE TABLE IF NOT EXISTS migration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_type TEXT NOT NULL,
    source_file TEXT,
    target_entity_id TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    migrated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 既存データベースからのマイグレーション準備
CREATE TABLE IF NOT EXISTS legacy_mapping (
    legacy_id TEXT,
    legacy_table TEXT,
    unified_entity_id TEXT,
    mapping_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (legacy_id, legacy_table)
);

-- ============================================
-- 統計・分析用ビュー
-- ============================================

-- 日別エンティティ作成統計
CREATE VIEW IF NOT EXISTS daily_entity_stats AS
SELECT 
    DATE(created_at) as date,
    type,
    COUNT(*) as count
FROM unified_entities
GROUP BY DATE(created_at), type
ORDER BY date DESC;

-- 関係性統計
CREATE VIEW IF NOT EXISTS relationship_stats AS
SELECT 
    relationship_type,
    COUNT(*) as count,
    AVG(weight) as avg_weight
FROM entity_relationships
GROUP BY relationship_type
ORDER BY count DESC;

-- 学習イベント統計
CREATE VIEW IF NOT EXISTS learning_stats AS
SELECT 
    event_type,
    COUNT(*) as total_events,
    COUNT(CASE WHEN applied = TRUE THEN 1 END) as applied_events,
    COUNT(CASE WHEN verified = TRUE THEN 1 END) as verified_events,
    AVG(confidence_score) as avg_confidence
FROM learning_events
GROUP BY event_type;

-- ============================================
-- 初期データ・サンプル
-- ============================================

-- システムエンティティの作成
INSERT OR IGNORE INTO unified_entities (
    id, type, title, content, metadata
) VALUES 
(
    'system-bootstrap-001',
    'system',
    '統合システム初期化',
    '統合データベースシステムの初期セットアップが完了しました。',
    json('{"status": "active", "priority": "high", "category": "system", "tags": ["bootstrap", "initialization"]}')
);

-- サンプル関係性タイプの定義（設定として）
INSERT OR IGNORE INTO system_metadata (key, value, description) VALUES
('relationship_types', 
 json('["derived_from", "related_to", "depends_on", "resolves", "causes", "prevents", "improves", "replaces"]'),
 '利用可能な関係性タイプ一覧');

-- ============================================
-- 権限・セキュリティ
-- ============================================

-- 将来的なユーザー権限管理用（現在は4賢者システム用）
CREATE TABLE IF NOT EXISTS access_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_type TEXT NOT NULL,    -- 'sage', 'worker', 'user', 'system'
    subject_id TEXT NOT NULL,      -- 賢者ID、ワーカーID等
    resource_type TEXT NOT NULL,   -- 'entity', 'relationship', 'search'
    resource_id TEXT,              -- 特定リソースID（NULLなら全体）
    permission TEXT NOT NULL,      -- 'read', 'write', 'delete', 'admin'
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    granted_by TEXT
);

-- 4賢者システムの基本権限設定
INSERT OR IGNORE INTO access_permissions (subject_type, subject_id, resource_type, permission) VALUES
('sage', 'knowledge_sage', 'entity', 'admin'),
('sage', 'task_oracle', 'entity', 'read'),
('sage', 'crisis_sage', 'entity', 'write'),
('sage', 'search_mystic', 'entity', 'read'),
('sage', 'search_mystic', 'search', 'admin');

-- インデックス
CREATE INDEX IF NOT EXISTS idx_permissions_subject ON access_permissions(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON access_permissions(resource_type, resource_id);

-- ============================================
-- データベース最適化
-- ============================================

-- 統計情報更新
ANALYZE;

-- バキューム（データベース最適化）
-- VACUUM; -- 手動実行時のみ

-- ============================================
-- スキーマバージョン記録
-- ============================================

UPDATE system_metadata 
SET value = '"1.0"', updated_at = CURRENT_TIMESTAMP 
WHERE key = 'schema_version';

UPDATE system_metadata 
SET value = '"2025-07-06T' || time('now') || '"', updated_at = CURRENT_TIMESTAMP 
WHERE key = 'last_migration';

-- 完了ログ
INSERT INTO migration_log (migration_type, source_file, status) 
VALUES ('schema_creation', 'unified_database_schema.sql', 'completed');