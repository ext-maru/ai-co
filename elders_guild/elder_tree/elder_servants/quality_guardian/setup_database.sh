#!/bin/bash

# SQLiteデータベース初期化スクリプト
# このスクリプトはSQLiteデータベースの初期化、テーブル作成、初期データ投入を行います

set -e  # エラー時にスクリプトを停止

# 設定
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_DIR="${PROJECT_DIR}/db"
CONFIG_DIR="${PROJECT_DIR}/config"
LOG_DIR="${PROJECT_DIR}/logs"
DATABASE_PATH="${DB_DIR}/ai_co.db"
BACKUP_DIR="${DB_DIR}/backups"

# ログファイル
LOG_FILE="${LOG_DIR}/database_setup.log"

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# ディレクトリ作成
create_directories() {
    log "必要なディレクトリを作成中..."

    mkdir -p "$DB_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"

    log_success "ディレクトリ作成完了"
}

# SQLiteがインストールされているかチェック
check_sqlite() {
    log "SQLiteの確認中..."

    if ! command -v sqlite3 &> /dev/null; then
        log_error "SQLite3がインストールされていません"
        log "Ubuntu/Debian: sudo apt-get install sqlite3"
        log "CentOS/RHEL: sudo yum install sqlite"
        log "macOS: brew install sqlite"
        exit 1
    fi

    local sqlite_version=$(sqlite3 --version | cut -d' ' -f1)
    log_success "SQLite3が利用可能です (バージョン: $sqlite_version)"
}

# 既存データベースのバックアップ
backup_existing_database() {
    if [ -f "$DATABASE_PATH" ]; then
        log "既存のデータベースをバックアップ中..."

        local backup_file="${BACKUP_DIR}/ai_co_backup_$(date +%Y%m%d_%H%M%S).db"
        cp "$DATABASE_PATH" "$backup_file"

        log_success "バックアップ完了: $backup_file"
    fi
}

# メインテーブル作成
create_main_tables() {
    log "メインテーブルを作成中..."

    sqlite3 "$DATABASE_PATH" << 'EOF'
-- タスク履歴テーブル
CREATE TABLE IF NOT EXISTS task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL UNIQUE,
    worker TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    summary TEXT,
    status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    task_type TEXT DEFAULT 'general' CHECK (task_type IN ('general', 'coding', 'analysis', 'documentation', 'testing')),
    priority INTEGER DEFAULT 0 CHECK (priority >= 0 AND priority <= 10),
    execution_time_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ユーザーテーブル
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    full_name TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user', 'readonly')),
    is_active BOOLEAN DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- プロジェクトテーブル
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    owner_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users (id)
);

-- タスクとプロジェクトの関連テーブル
CREATE TABLE IF NOT EXISTS task_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    project_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (task_id) REFERENCES task_history (task_id),
    UNIQUE(task_id, project_id)
);

-- 設定テーブル
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ファイル管理テーブル
CREATE TABLE IF NOT EXISTS file_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    file_hash TEXT,
    mime_type TEXT,
    project_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);

-- 実行ログテーブル
CREATE TABLE IF NOT EXISTS execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    log_level TEXT DEFAULT 'INFO' CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES task_history (task_id)
);
EOF

    log_success "メインテーブル作成完了"
}

# インデックス作成
create_indexes() {
    log "インデックスを作成中..."

    sqlite3 "$DATABASE_PATH" << 'EOF'
-- task_history テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id);
CREATE INDEX IF NOT EXISTS idx_task_history_worker ON task_history(worker);
CREATE INDEX IF NOT EXISTS idx_task_history_status ON task_history(status);
CREATE INDEX IF NOT EXISTS idx_task_history_task_type ON task_history(task_type);
CREATE INDEX IF NOT EXISTS idx_task_history_created_at ON task_history(created_at);
CREATE INDEX IF NOT EXISTS idx_task_history_updated_at ON task_history(updated_at);

-- users テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- projects テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);

-- task_projects テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_task_projects_task_id ON task_projects(task_id);
CREATE INDEX IF NOT EXISTS idx_task_projects_project_id ON task_projects(project_id);

-- system_settings テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);
CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category);

-- file_registry テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_file_registry_file_path ON file_registry(file_path);
CREATE INDEX IF NOT EXISTS idx_file_registry_file_name ON file_registry(file_name);
CREATE INDEX IF NOT EXISTS idx_file_registry_project_id ON file_registry(project_id);

-- execution_logs テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_execution_logs_task_id ON execution_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_log_level ON execution_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_execution_logs_created_at ON execution_logs(created_at);
EOF

    log_success "インデックス作成完了"
}

# トリガー作成
create_triggers() {
    log "トリガーを作成中..."

    sqlite3 "$DATABASE_PATH" << 'EOF'
-- task_history の updated_at 自動更新トリガー
CREATE TRIGGER IF NOT EXISTS update_task_history_timestamp
    AFTER UPDATE ON task_history
    FOR EACH ROW
BEGIN
    UPDATE task_history SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- users の updated_at 自動更新トリガー
CREATE TRIGGER IF NOT EXISTS update_users_timestamp
    AFTER UPDATE ON users
    FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- projects の updated_at 自動更新トリガー
CREATE TRIGGER IF NOT EXISTS update_projects_timestamp
    AFTER UPDATE ON projects
    FOR EACH ROW
BEGIN
    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- system_settings の updated_at 自動更新トリガー
CREATE TRIGGER IF NOT EXISTS update_system_settings_timestamp
    AFTER UPDATE ON system_settings
    FOR EACH ROW
BEGIN
    UPDATE system_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- file_registry の updated_at 自動更新トリガー
CREATE TRIGGER IF NOT EXISTS update_file_registry_timestamp
    AFTER UPDATE ON file_registry
    FOR EACH ROW
BEGIN
    UPDATE file_registry SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
EOF

    log_success "トリガー作成完了"
}

# 初期データ投入
insert_initial_data() {
    log "初期データを投入中..."

    sqlite3 "$DATABASE_PATH" << 'EOF'
-- デフォルト管理者ユーザー
INSERT OR IGNORE INTO users (username, email, full_name, role, is_active)
VALUES ('admin', 'admin@ai-co.local', 'System Administrator', 'admin', 1);

-- デフォルトプロジェクト
INSERT OR IGNORE INTO projects (name, description, status, owner_id)
VALUES ('default', 'Default project for general tasks', 'active', 1);

-- システム設定のデフォルト値
INSERT OR IGNORE INTO system_settings (key, value, description, category) VALUES
('database_version', '1.0.0', 'Database schema version', 'system'),
('max_task_history', '10000', 'Maximum number of task history records to keep', 'performance'),
('log_retention_days', '30', 'Number of days to keep execution logs', 'logging'),
('backup_retention_days', '7', 'Number of days to keep database backups', 'backup'),
('default_task_timeout', '300', 'Default task timeout in seconds', 'execution'),
('enable_task_logging', '1', 'Enable detailed task logging', 'logging'),
('enable_performance_metrics', '1', 'Enable performance metrics collection', 'monitoring'),
('theme', 'default', 'UI theme setting', 'ui'),
('language', 'ja', 'Default language setting', 'ui'),
('timezone', 'Asia/Tokyo', 'Default timezone', 'system');

-- サンプルタスク（オプション）
INSERT OR IGNORE INTO task_history (task_id, worker, model, prompt, response, summary, status, task_type, priority)
VALUES (
    'setup-001',
    'system',
    'setup',
    'Database initialization',
    'Database has been successfully initialized with all required tables and initial data.',
    'Database setup completed successfully',
    'completed',
    'general',
    5
);
EOF

    log_success "初期データ投入完了"
}

# データベース最適化
optimize_database() {
    log "データベースを最適化中..."

    sqlite3 "$DATABASE_PATH" << 'EOF'
-- 外部キー制約を有効化
PRAGMA foreign_keys = ON;

-- WALモードを有効化（パフォーマンス向上）
PRAGMA journal_mode = WAL;

-- 同期モードを設定
PRAGMA synchronous = NORMAL;

-- キャッシュサイズを設定（メモリ使用量を考慮）
PRAGMA cache_size = 10000;

-- 自動バキュームを有効化
PRAGMA auto_vacuum = INCREMENTAL;

-- ページサイズを最適化
PRAGMA page_size = 4096;

-- 統計情報を更新
ANALYZE;

-- データベースを最適化
VACUUM;
EOF

    log_success "データベース最適化完了"
}

# データベース整合性チェック
verify_database() {
    log "データベースの整合性をチェック中..."

    local integrity_check=$(sqlite3 "$DATABASE_PATH" "PRAGMA integrity_check;")
    if [ "$integrity_check" = "ok" ]; then
        log_success "データベースの整合性チェック: OK"
    else
        log_error "データベースの整合性チェック: 失敗"
        log_error "$integrity_check"
        return 1
    fi

    # テーブル一覧表示
    log "作成されたテーブル一覧:"
    sqlite3 "$DATABASE_PATH" ".tables" | while read table; do
        log "  - $table"
    done
}

# 権限設定
set_permissions() {
    log "ファイル権限を設定中..."

    # データベースファイルの権限設定
    chmod 660 "$DATABASE_PATH"

    # ディレクトリの権限設定
    chmod 755 "$DB_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$BACKUP_DIR"

    log_success "権限設定完了"
}

# 使用方法表示
show_usage() {
    echo "使用方法: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  -h, --help           このヘルプを表示"
    echo "  -f, --force          既存のデータベースを強制的に再作成"
    echo "  -b, --backup-only    バックアップのみ実行"
    echo "  -v, --verify-only    検証のみ実行"
    echo "  --no-backup          バックアップをスキップ"
    echo "  --no-initial-data    初期データの投入をスキップ"
    echo ""
    echo "例:"
    echo "  $0                   通常の初期化"
    echo "  $0 -f                強制再作成"
    echo "  $0 --verify-only     検証のみ"
}

# 進捗表示
show_progress() {
    local current=$1
    local total=$2
    local desc=$3

    local progress=$((current * 100 / total))
    printf "\r${BLUE}[%d/%d] (%d%%) %s${NC}" "$current" "$total" "$progress" "$desc"
    if [ "$current" -eq "$total" ]; then
        echo ""
    fi
}

# メイン処理
main() {
    local force=false
    local backup_only=false
    local verify_only=false
    local no_backup=false
    local no_initial_data=false

    # 引数解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -f|--force)
                force=true
                shift
                ;;
            -b|--backup-only)
                backup_only=true
                shift
                ;;
            -v|--verify-only)
                verify_only=true
                shift
                ;;
            --no-backup)
                no_backup=true
                shift
                ;;
            --no-initial-data)
                no_initial_data=true
                shift
                ;;
            *)
                log_error "不明なオプション: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # バナー表示
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║      AI Co Database Setup          ║${NC}"
    echo -e "${BLUE}║      SQLite Initialization         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
    echo ""

    log "データベース初期化を開始します..."
    log "データベースパス: $DATABASE_PATH"

    # バックアップのみの場合
    if [ "$backup_only" = true ]; then
        create_directories
        backup_existing_database
        log_success "バックアップ処理が完了しました"
        exit 0
    fi

    # 検証のみの場合
    if [ "$verify_only" = true ]; then
        if [ ! -f "$DATABASE_PATH" ]; then
            log_error "データベースファイルが存在しません: $DATABASE_PATH"
            exit 1
        fi
        verify_database
        log_success "検証処理が完了しました"
        exit 0
    fi

    # 既存データベースの処理
    if [ -f "$DATABASE_PATH" ] && [ "$force" = false ]; then
        log_warning "データベースファイルが既に存在します: $DATABASE_PATH"
        read -p "続行しますか？ [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "処理を中断しました"
            exit 0
        fi
    fi

    # 強制再作成の場合は既存ファイルを削除
    if [ "$force" = true ] && [ -f "$DATABASE_PATH" ]; then
        log "既存のデータベースを削除中..."
        rm -f "$DATABASE_PATH"
    fi

    # 処理ステップ
    local steps=7
    local current_step=0

    # 1. ディレクトリ作成
    ((current_step++))
    show_progress $current_step $steps "ディレクトリ作成中..."
    create_directories

    # 2. SQLiteチェック
    ((current_step++))
    show_progress $current_step $steps "SQLite確認中..."
    check_sqlite

    # 3. バックアップ
    if [ "$no_backup" = false ]; then
        ((current_step++))
        show_progress $current_step $steps "バックアップ作成中..."
        backup_existing_database
    else
        ((current_step++))
        show_progress $current_step $steps "バックアップをスキップ..."
    fi

    # 4. テーブル作成
    ((current_step++))
    show_progress $current_step $steps "テーブル作成中..."
    create_main_tables

    # 5. インデックス・トリガー作成
    ((current_step++))
    show_progress $current_step $steps "インデックス・トリガー作成中..."
    create_indexes
    create_triggers

    # 6. 初期データ投入
    if [ "$no_initial_data" = false ]; then
        ((current_step++))
        show_progress $current_step $steps "初期データ投入中..."
        insert_initial_data
    else
        ((current_step++))
        show_progress $current_step $steps "初期データ投入をスキップ..."
    fi

    # 7. 最適化・権限設定
    ((current_step++))
    show_progress $current_step $steps "最適化・権限設定中..."
    optimize_database
    set_permissions

    # 検証
    verify_database

    echo ""
    log_success "=== データベース初期化が完了しました ==="
    log "データベースファイル: $DATABASE_PATH"
    log "ログファイル: $LOG_FILE"
    log "バックアップディレクトリ: $BACKUP_DIR"

    # データベース情報表示
    local db_size=$(du -h "$DATABASE_PATH" | cut -f1)
    log "データベースサイズ: $db_size"

    # 使用例
    echo ""
    log "=== 使用例 ==="
    log "SQLiteコマンドライン接続: sqlite3 $DATABASE_PATH"
    log "テーブル一覧表示: sqlite3 $DATABASE_PATH '.tables'"
    log "タスク履歴確認: sqlite3 $DATABASE_PATH 'SELECT * FROM task_history LIMIT 5;'"

    echo ""
    log_success "セットアップが正常に完了しました！"
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
