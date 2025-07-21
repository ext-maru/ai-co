#!/bin/bash
# EITMS System Status Check Script
# エルダーズギルド統合タスク管理システム状態確認スクリプト

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_DIR="$PROJECT_ROOT/run"
LOG_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"

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

log_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

check_service_status() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            local cpu_usage=$(ps -p "$pid" -o %cpu --no-headers | xargs)
            local mem_usage=$(ps -p "$pid" -o %mem --no-headers | xargs)
            echo -e "  ${GREEN}✓${NC} ${service_name} (PID: $pid, CPU: ${cpu_usage}%, MEM: ${mem_usage}%)"
            return 0
        else
            echo -e "  ${RED}✗${NC} ${service_name} (PID file exists but process not found)"
            return 1
        fi
    else
        echo -e "  ${RED}✗${NC} ${service_name} (PID file not found)"
        return 1
    fi
}

check_database() {
    local db_path="$DATA_DIR/eitms.db"
    
    if [ -f "$db_path" ]; then
        local db_size=$(du -h "$db_path" | cut -f1)
        local task_count=$(sqlite3 "$db_path" "SELECT COUNT(*) FROM unified_tasks;" 2>/dev/null || echo "N/A")
        echo -e "  ${GREEN}✓${NC} Main database (Size: $db_size, Tasks: $task_count)"
    else
        echo -e "  ${RED}✗${NC} Main database not found"
    fi
    
    # Check 4 Sages databases
    for sage in knowledge task incident rag; do
        local sage_db="$DATA_DIR/${sage}_sage.db"
        if [ -f "$sage_db" ]; then
            local sage_size=$(du -h "$sage_db" | cut -f1)
            echo -e "  ${GREEN}✓${NC} ${sage} sage database (Size: $sage_size)"
        else
            echo -e "  ${RED}✗${NC} ${sage} sage database not found"
        fi
    done
}

check_logs() {
    local services=("unified_data_model" "auto_sync" "core_sync" "api_sync" "ai_optimization" "monitoring")
    
    for service in "${services[@]}"; do
        local log_file="$LOG_DIR/${service}.log"
        if [ -f "$log_file" ]; then
            local log_size=$(du -h "$log_file" | cut -f1)
            local last_modified=$(stat -c %y "$log_file" | cut -d' ' -f1,2)
            local error_count=$(grep -c "ERROR" "$log_file" 2>/dev/null || echo "0")
            local warning_count=$(grep -c "WARNING" "$log_file" 2>/dev/null || echo "0")
            
            if [ "$error_count" -gt 0 ]; then
                echo -e "  ${RED}!${NC} ${service}.log (Size: $log_size, Errors: $error_count, Warnings: $warning_count)"
            elif [ "$warning_count" -gt 0 ]; then
                echo -e "  ${YELLOW}!${NC} ${service}.log (Size: $log_size, Errors: $error_count, Warnings: $warning_count)"
            else
                echo -e "  ${GREEN}✓${NC} ${service}.log (Size: $log_size, No errors)"
            fi
        else
            echo -e "  ${RED}✗${NC} ${service}.log not found"
        fi
    done
}

check_system_resources() {
    # CPU Usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d% -f1)
    echo -e "  CPU Usage: ${cpu_usage}%"
    
    # Memory Usage
    local mem_info=$(free -h | awk 'NR==2{printf "Memory Usage: %s/%s (%.2f%%)", $3,$2,$3*100/$2}')
    echo -e "  $mem_info"
    
    # Disk Usage for project directory
    local disk_usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2{printf "Disk Usage: %s/%s (%s)", $3,$2,$5}')
    echo -e "  $disk_usage"
    
    # Load Average
    local load_avg=$(uptime | awk -F'load average:' '{ print $2 }')
    echo -e "  Load Average:$load_avg"
}

check_network_ports() {
    local ports=(8000 8001 8002 8003 8004 8005 8006 8007 8888)
    
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep ":$port " > /dev/null; then
            echo -e "  ${GREEN}✓${NC} Port $port is open"
        else
            echo -e "  ${YELLOW}-${NC} Port $port is not in use"
        fi
    done
}

show_recent_activity() {
    local main_log="$LOG_DIR/eitms.log"
    
    if [ -f "$main_log" ]; then
        echo -e "${BLUE}Recent Activity (last 10 lines):${NC}"
        tail -10 "$main_log" | sed 's/^/  /'
    else
        log_warning "Main log file not found"
    fi
}

generate_summary() {
    local services=("unified_data_model" "auto_sync" "core_sync" "api_sync" "ai_optimization" "monitoring")
    local running_count=0
    local total_count=${#services[@]}
    
    for service in "${services[@]}"; do
        if check_service_status "$service" > /dev/null 2>&1; then
            ((running_count++))
        fi
    done
    
    echo
    log_header "SYSTEM SUMMARY"
    
    if [ $running_count -eq $total_count ]; then
        echo -e "${GREEN}System Status: HEALTHY${NC}"
        echo -e "All $total_count services are running"
    elif [ $running_count -gt 0 ]; then
        echo -e "${YELLOW}System Status: PARTIAL${NC}"
        echo -e "$running_count of $total_count services are running"
    else
        echo -e "${RED}System Status: DOWN${NC}"
        echo -e "No services are running"
    fi
    
    # Uptime information
    if [ -f "$PID_DIR/unified_data_model.pid" ]; then
        local first_pid=$(cat "$PID_DIR/unified_data_model.pid" 2>/dev/null || echo "")
        if [ -n "$first_pid" ] && ps -p "$first_pid" > /dev/null 2>&1; then
            local start_time=$(ps -o lstart= -p "$first_pid" 2>/dev/null | xargs)
            echo -e "System started: $start_time"
        fi
    fi
}

# Main execution
main() {
    log_header "EITMS STATUS CHECK"
    echo "Timestamp: $(date)"
    echo "Project Root: $PROJECT_ROOT"
    echo
    
    log_header "SERVICE STATUS"
    local services=("unified_data_model" "auto_sync" "core_sync" "api_sync" "ai_optimization" "monitoring")
    for service in "${services[@]}"; do
        check_service_status "$service"
    done
    echo
    
    log_header "DATABASE STATUS"
    check_database
    echo
    
    log_header "LOG STATUS"
    check_logs
    echo
    
    log_header "SYSTEM RESOURCES"
    check_system_resources
    echo
    
    log_header "NETWORK PORTS"
    check_network_ports
    echo
    
    # Show recent activity if requested
    if [ "$1" == "--verbose" ] || [ "$1" == "-v" ]; then
        show_recent_activity
        echo
    fi
    
    generate_summary
    
    echo
    log_info "Status check completed"
    
    if [ "$1" == "--tail-logs" ]; then
        log_info "Following logs... (Press Ctrl+C to stop)"
        tail -f "$LOG_DIR"/*.log 2>/dev/null || log_warning "No log files to follow"
    fi
}

# Run main function
main "$@"