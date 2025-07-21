#!/bin/bash
# EITMS System Startup Script
# Version: 1.0.0
# Last Updated: 2025-07-22

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== EITMS System Startup ===${NC}"

# Check if running as aicompany user
if [ "$USER" != "aicompany" ]; then
    echo -e "${RED}Error: This script must be run as aicompany user${NC}"
    exit 1
fi

# Load environment variables
if [ -f "/home/aicompany/ai_co/.env" ]; then
    export $(cat /home/aicompany/ai_co/.env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: .env file not found. Using default configuration.${NC}"
fi

# Function to check if service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN} $service_name is running on port $port${NC}"
        return 0
    else
        echo -e "${RED} $service_name is not running on port $port${NC}"
        return 1
    fi
}

# Function to start a module
start_module() {
    local module_name=$1
    local module_path=$2
    local port=$3
    
    echo -e "${YELLOW}Starting $module_name...${NC}"
    
    # Check if already running
    if check_service "$module_name" "$port"; then
        return 0
    fi
    
    # Start the module
    cd /home/aicompany/ai_co
    nohup python3 "$module_path" > "logs/eitms_${module_name}.log" 2>&1 &
    
    # Wait for startup
    sleep 3
    
    # Verify startup
    if check_service "$module_name" "$port"; then
        echo -e "${GREEN}$module_name started successfully${NC}"
    else
        echo -e "${RED}Failed to start $module_name${NC}"
        return 1
    fi
}

# Create necessary directories
mkdir -p /home/aicompany/ai_co/logs
mkdir -p /home/aicompany/ai_co/data
mkdir -p /home/aicompany/ai_co/backups/eitms

# Check database connection
echo -e "${YELLOW}Checking database connection...${NC}"
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN} PostgreSQL is running${NC}"
else
    echo -e "${RED} PostgreSQL is not running. Please start PostgreSQL first.${NC}"
    exit 1
fi

# Check Redis connection
echo -e "${YELLOW}Checking Redis connection...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN} Redis is running${NC}"
else
    echo -e "${RED} Redis is not running. Please start Redis first.${NC}"
    exit 1
fi

# Initialize database if needed
if [ "$1" == "--init-db" ]; then
    echo -e "${YELLOW}Initializing database...${NC}"
    psql -U postgres < /home/aicompany/ai_co/scripts/eitms_db_init.sql
    echo -e "${GREEN}Database initialized${NC}"
fi

# Start EITMS modules
echo -e "${YELLOW}Starting EITMS modules...${NC}"

# Start each module
start_module "github_connector" "libs/eitms_github_connector.py" 8001
start_module "task_tracker_interface" "libs/eitms_task_tracker_interface.py" 8002
start_module "todo_system_bridge" "libs/eitms_todo_system_bridge.py" 8003
start_module "real_time_sync" "libs/eitms_real_time_sync_engine.py" 8004
start_module "unified_query" "libs/eitms_unified_query_processor.py" 8006
start_module "ai_optimization" "libs/eitms_ai_optimization_engine.py" 8007

# Check overall system status
echo -e "${GREEN}=== EITMS System Status ===${NC}"
check_service "GitHub Connector" 8001
check_service "Task Tracker Interface" 8002
check_service "Todo System Bridge" 8003
check_service "Real-time Sync Engine" 8004
check_service "Unified Query Processor" 8006
check_service "AI Optimization Engine" 8007

echo -e "${GREEN}=== EITMS System Startup Complete ===${NC}"
echo -e "Logs are available in: /home/aicompany/ai_co/logs/"
echo -e "To stop EITMS, run: ./scripts/eitms_stop.sh"