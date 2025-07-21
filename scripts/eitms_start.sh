#!/bin/bash
# EITMS System Startup Script
# Version: 1.0.0
# Last Updated: 2025-07-22
# エルダーズギルド統合タスク管理システム起動スクリプト

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/config/eitms_config.yaml"
ENV_FILE="$PROJECT_ROOT/.env"
LOG_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"
PID_DIR="$PROJECT_ROOT/run"

# Create necessary directories
mkdir -p "$LOG_DIR" "$DATA_DIR" "$PID_DIR"

echo -e "${GREEN}=== EITMS System Startup ===${NC}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as aicompany user
if [ "$USER" != "aicompany" ]; then
    echo -e "${RED}Error: This script must be run as aicompany user${NC}"
    exit 1
fi

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: .env file not found. Using default configuration.${NC}"
fi

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file not found. Creating from template..."
        if [ -f "$PROJECT_ROOT/config/eitms.env.example" ]; then
            cp "$PROJECT_ROOT/config/eitms.env.example" "$ENV_FILE"
            log_warning "Please edit $ENV_FILE with your actual values"
        fi
        exit 1
    fi
    
    log_info "Prerequisites check completed"
}

init_database() {
    log_info "Initializing database..."
    
    # SQLite database creation
    if [ ! -f "$DATA_DIR/eitms.db" ]; then
        log_info "Creating EITMS database..."
        python3 << EOF
import sqlite3
import os

db_path = "$DATA_DIR/eitms.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create unified_tasks table
cursor.execute('''
CREATE TABLE IF NOT EXISTS unified_tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    time_estimated INTEGER,
    time_spent INTEGER,
    assigned_to TEXT,
    dependencies TEXT,
    sub_tasks TEXT,
    github_issue_number INTEGER,
    context TEXT
)
''')

# Create indexes
cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_type ON unified_tasks(task_type)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON unified_tasks(status)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority ON unified_tasks(priority)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON unified_tasks(created_at)')

conn.commit()
conn.close()

print("Database initialized successfully")
EOF
    fi
    
    log_info "Database initialization completed"
}

start_services() {
    log_info "Starting EITMS services..."
    
    # Source environment variables
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    fi
    
    # Start core services
    cd "$PROJECT_ROOT"
    
    # 1. Unified Data Model Service
    log_info "Starting Unified Data Model service..."
    if [ -f "$PROJECT_ROOT/libs/eitms_unified_data_model.py" ]; then
        nohup python3 -m libs.eitms_unified_data_model > "$LOG_DIR/unified_data_model.log" 2>&1 &
        echo $! > "$PID_DIR/unified_data_model.pid"
    else
        log_warning "Unified Data Model module not found"
    fi
    
    # Wait for services to start
    sleep 3
    
    log_info "EITMS services started"
}

check_status() {
    log_info "Checking service status..."
    
    services=("unified_data_model")
    all_running=true
    
    for service in "${services[@]}"; do
        pid_file="$PID_DIR/${service}.pid"
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if ps -p "$pid" > /dev/null 2>&1; then
                log_info "✓ ${service} is running (PID: $pid)"
            else
                log_error "✗ ${service} is not running"
                all_running=false
            fi
        else
            log_warning "✗ ${service} PID file not found"
            all_running=false
        fi
    done
    
    if $all_running; then
        log_info "All EITMS services are running"
    else
        log_error "Some services are not running"
    fi
}

# Main execution
main() {
    log_info "Starting EITMS (Elders Guild Integrated Task Management System)..."
    
    # Parse arguments
    if [ "$1" == "--init-db" ]; then
        check_prerequisites
        init_database
        exit 0
    fi
    
    # Normal startup
    check_prerequisites
    
    # Initialize database if needed
    if [ ! -f "$DATA_DIR/eitms.db" ]; then
        init_database
    fi
    
    # Start services
    start_services
    
    # Check status
    sleep 2
    check_status
    
    log_info "EITMS startup completed"
    log_info "Logs are available in: $LOG_DIR"
    log_info "To check status: $SCRIPT_DIR/eitms_status.sh"
    log_info "To stop: $SCRIPT_DIR/eitms_stop.sh"
}

# Run main function
main "$@"