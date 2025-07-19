-- エルダーズ知識管理システムのスキーマ
-- Created: 2025-07-07

-- 知識カテゴリテーブル
CREATE TABLE IF NOT EXISTS knowledge_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER REFERENCES knowledge_categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- エルダーズ（知識提供者）テーブル
CREATE TABLE IF NOT EXISTS elders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    expertise TEXT[],  -- 専門分野の配列
    description TEXT,
    reliability_score FLOAT DEFAULT 1.0 CHECK (reliability_score >= 0 AND reliability_score <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知識エントリテーブル（ベクトル埋め込み付き）
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category_id INTEGER REFERENCES knowledge_categories(id),
    elder_id INTEGER REFERENCES elders(id),
    embedding vector(1536),  -- OpenAI embeddings dimension
    metadata JSONB,
    tags TEXT[],
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知識の関連性テーブル
CREATE TABLE IF NOT EXISTS knowledge_relations (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,  -- 'prerequisite', 'related', 'contradicts', etc.
    strength FLOAT DEFAULT 0.5 CHECK (strength >= 0 AND strength <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, relation_type)
);

-- 知識検索履歴テーブル
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    query_embedding vector(1536),
    results JSONB,
    user_feedback INTEGER CHECK (user_feedback IN (-1, 0, 1)),  -- -1: bad, 0: neutral, 1: good
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_knowledge_entries_embedding ON knowledge_entries USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_knowledge_entries_category ON knowledge_entries(category_id);
CREATE INDEX idx_knowledge_entries_elder ON knowledge_entries(elder_id);
CREATE INDEX idx_knowledge_entries_tags ON knowledge_entries USING GIN(tags);
CREATE INDEX idx_knowledge_entries_metadata ON knowledge_entries USING GIN(metadata);
CREATE INDEX idx_search_history_embedding ON search_history USING ivfflat (query_embedding vector_cosine_ops) WITH (lists = 100);

-- 更新日時自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_knowledge_categories_updated_at BEFORE UPDATE ON knowledge_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_elders_updated_at BEFORE UPDATE ON elders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_entries_updated_at BEFORE UPDATE ON knowledge_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- サンプルカテゴリの挿入
INSERT INTO knowledge_categories (name, description) VALUES
    ('技術', 'プログラミング、システム設計、インフラストラクチャなど'),
    ('ビジネス', 'ビジネス戦略、マーケティング、経営管理など'),
    ('生活の知恵', '日常生活、健康、人間関係など'),
    ('歴史と文化', '歴史的出来事、文化的知識、伝統など');

-- サンプルエルダーの挿入
INSERT INTO elders (name, expertise, description) VALUES
    ('技術長老', ARRAY['プログラミング', 'システム設計', 'AI/ML'], '30年以上の技術経験を持つエンジニア'),
    ('経営長老', ARRAY['経営戦略', 'リーダーシップ', '組織運営'], '複数の企業を成功に導いた経営者'),
    ('生活の達人', ARRAY['健康', '人間関係', '時間管理'], '豊富な人生経験から得た知恵を共有');
