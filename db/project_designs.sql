-- プロジェクト設計書データベース
-- PMワーカーがプロジェクト全体を管理するためのスキーマ

-- プロジェクトマスター
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,       -- proj_20250102_123456
    task_id TEXT UNIQUE,              -- 元のタスクID
    name TEXT NOT NULL,               -- プロジェクト名
    description TEXT,                 -- プロジェクト概要
    status TEXT DEFAULT 'planning',   -- planning/designing/developing/testing/deployed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 要件定義
CREATE TABLE IF NOT EXISTS requirements (
    requirement_id TEXT PRIMARY KEY,   -- req_20250102_123456
    project_id TEXT NOT NULL,
    type TEXT NOT NULL,               -- functional/non_functional/technical
    description TEXT NOT NULL,
    priority TEXT DEFAULT 'normal',   -- critical/high/normal/low
    status TEXT DEFAULT 'draft',      -- draft/approved/implemented
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- 設計書
CREATE TABLE IF NOT EXISTS designs (
    design_id TEXT PRIMARY KEY,       -- des_20250102_123456
    project_id TEXT NOT NULL,
    type TEXT NOT NULL,              -- architecture/database/api/ui
    content TEXT NOT NULL,           -- JSON形式の設計内容
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'draft',     -- draft/reviewing/approved
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- 開発タスク
CREATE TABLE IF NOT EXISTS development_tasks (
    dev_task_id TEXT PRIMARY KEY,    -- dev_20250102_123456
    project_id TEXT NOT NULL,
    design_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    assigned_worker TEXT,            -- task_worker/se_worker等
    status TEXT DEFAULT 'pending',   -- pending/in_progress/completed/failed
    result TEXT,                     -- 実行結果のJSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (design_id) REFERENCES designs(design_id)
);

-- テスト結果
CREATE TABLE IF NOT EXISTS test_results (
    test_id TEXT PRIMARY KEY,        -- test_20250102_123456
    project_id TEXT NOT NULL,
    dev_task_id TEXT,
    test_type TEXT NOT NULL,         -- unit/integration/e2e
    status TEXT NOT NULL,            -- passed/failed/skipped
    details TEXT,                    -- テスト詳細JSON
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (dev_task_id) REFERENCES development_tasks(dev_task_id)
);

-- フェーズ進捗
CREATE TABLE IF NOT EXISTS phase_progress (
    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    phase TEXT NOT NULL,             -- planning/design/development/testing/deployment
    status TEXT NOT NULL,            -- not_started/in_progress/completed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- プロジェクトファイル（成果物）
CREATE TABLE IF NOT EXISTS project_files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,         -- source/config/doc/test
    phase TEXT NOT NULL,             -- どのフェーズで作成されたか
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- インデックス
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_requirements_project ON requirements(project_id);
CREATE INDEX idx_designs_project ON designs(project_id);
CREATE INDEX idx_dev_tasks_project ON development_tasks(project_id);
CREATE INDEX idx_test_results_project ON test_results(project_id);
CREATE INDEX idx_phase_progress_project ON phase_progress(project_id);
CREATE INDEX idx_project_files_project ON project_files(project_id);