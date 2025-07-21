#!/bin/bash
# EITMS System Status Check Script
# Version: 1.0.0
# Last Updated: 2025-07-22

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== EITMS System Status ===${NC}"
echo -e "Time: $(date)"
echo ""

# Function to check service status
check_service() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"/health"}
    
    # Check if port is open
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        # Try health endpoint
        if curl -s -f "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name${NC} - Running on port $port (Healthy)"
        else
            echo -e "${YELLOW}⚠ $service_name${NC} - Running on port $port (No health response)"
        fi
    else
        echo -e "${RED}✗ $service_name${NC} - Not running on port $port"
    fi
}

# Check infrastructure services
echo -e "${BLUE}Infrastructure Services:${NC}"
echo -e "------------------------"

# PostgreSQL
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL${NC} - Running"
    # Check database connectivity
    if PGPASSWORD=$EITMS_DB_PASS psql -h localhost -U ${EITMS_DB_USER:-eitms_user} -d ${EITMS_DB_NAME:-eitms_production} -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "  └─ Database connection: ${GREEN}OK${NC}"
    else
        echo -e "  └─ Database connection: ${RED}Failed${NC}"
    fi
else
    echo -e "${RED}✗ PostgreSQL${NC} - Not running"
fi

# Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis${NC} - Running"
    # Check Redis memory usage
    used_memory=$(redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    echo -e "  └─ Memory usage: $used_memory"
else
    echo -e "${RED}✗ Redis${NC} - Not running"
fi

echo ""

# Check EITMS services
echo -e "${BLUE}EITMS Services:${NC}"
echo -e "---------------"

check_service "GitHub Connector" 8001
check_service "Task Tracker Interface" 8002
check_service "Todo System Bridge" 8003
check_service "Real-time Sync Engine" 8004
check_service "WebSocket Server" 8005 "/ws"
check_service "Unified Query Processor" 8006
check_service "AI Optimization Engine" 8007

echo ""

# Check system resources
echo -e "${BLUE}System Resources:${NC}"
echo -e "-----------------"

# CPU usage
cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
echo -e "CPU Usage: ${cpu_usage}%"

# Memory usage
mem_info=$(free -h | grep Mem)
mem_total=$(echo $mem_info | awk '{print $2}')
mem_used=$(echo $mem_info | awk '{print $3}')
mem_percent=$(free | grep Mem | awk '{print ($3/$2) * 100.0}')
printf "Memory Usage: %.1f%% (Used: %s / Total: %s)\n" $mem_percent $mem_used $mem_total

# Disk usage
disk_usage=$(df -h /home/aicompany | awk 'NR==2 {print $5}')
disk_info=$(df -h /home/aicompany | awk 'NR==2')
echo -e "Disk Usage: $disk_usage"

echo ""

# Check recent logs for errors
echo -e "${BLUE}Recent Errors (last 10 minutes):${NC}"
echo -e "--------------------------------"

error_count=0
if [ -d "/home/aicompany/ai_co/logs" ]; then
    for log_file in /home/aicompany/ai_co/logs/eitms_*.log; do
        if [ -f "$log_file" ]; then
            recent_errors=$(find "$log_file" -mmin -10 -exec grep -i "error\|exception" {} \; | wc -l)
            if [ $recent_errors -gt 0 ]; then
                service_name=$(basename "$log_file" .log | sed 's/eitms_//')
                echo -e "${YELLOW}⚠ $service_name: $recent_errors errors${NC}"
                error_count=$((error_count + recent_errors))
            fi
        fi
    done
fi

if [ $error_count -eq 0 ]; then
    echo -e "${GREEN}No recent errors found${NC}"
fi

echo ""

# Check sync status
echo -e "${BLUE}Sync Status:${NC}"
echo -e "------------"

if [ -n "$EITMS_DB_PASS" ]; then
    sync_status=$(PGPASSWORD=$EITMS_DB_PASS psql -h localhost -U ${EITMS_DB_USER:-eitms_user} -d ${EITMS_DB_NAME:-eitms_production} -t -c "
        SELECT source, status, last_sync_at, items_synced 
        FROM sync_status 
        ORDER BY source
    " 2>/dev/null)
    
    if [ -n "$sync_status" ]; then
        echo "$sync_status" | while IFS='|' read -r source status last_sync items; do
            source=$(echo $source | xargs)
            status=$(echo $status | xargs)
            last_sync=$(echo $last_sync | xargs)
            items=$(echo $items | xargs)
            
            if [ -n "$source" ]; then
                status_icon="?"
                case "$status" in
                    "success") status_icon="${GREEN}✓${NC}" ;;
                    "pending") status_icon="${YELLOW}⏳${NC}" ;;
                    "failed") status_icon="${RED}✗${NC}" ;;
                esac
                
                echo -e "$status_icon $source - Last sync: $last_sync (Items: $items)"
            fi
        done
    else
        echo -e "${YELLOW}Unable to retrieve sync status${NC}"
    fi
else
    echo -e "${YELLOW}Database credentials not configured${NC}"
fi

echo ""
echo -e "${BLUE}================================${NC}"

# Overall status
all_services_running=true
critical_services=("8001" "8002" "8003" "8004" "8006" "8007")

for port in "${critical_services[@]}"; do
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        all_services_running=false
        break
    fi
done

if [ "$all_services_running" = true ] && [ $error_count -eq 0 ]; then
    echo -e "${GREEN}System Status: HEALTHY${NC}"
else
    echo -e "${YELLOW}System Status: DEGRADED${NC}"
fi

echo -e "${BLUE}================================${NC}"