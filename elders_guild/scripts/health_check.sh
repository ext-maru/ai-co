#!/bin/bash
# Elder Tree v2 Health Check Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Elder Tree v2 Health Check${NC}"
echo "=============================="

# Function to check service health
check_service() {
    local service=$1
    local port=$2
    
    if curl -s -f http://localhost:$port/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $service (port $port) - Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ $service (port $port) - Unhealthy${NC}"
        return 1
    fi
}

# Function to check Docker container
check_container() {
    local container=$1
    
    if docker ps | grep -q $container; then
        local status=$(docker inspect -f '{{.State.Health.Status}}' $container 2>/dev/null || echo "unknown")
        if [ "$status" = "healthy" ]; then
            echo -e "${GREEN}✓ $container - Running (Healthy)${NC}"
        elif [ "$status" = "unknown" ]; then
            echo -e "${YELLOW}? $container - Running (No health check)${NC}"
        else
            echo -e "${YELLOW}! $container - Running ($status)${NC}"
        fi
        return 0
    else
        echo -e "${RED}✗ $container - Not running${NC}"
        return 1
    fi
}

# Check infrastructure
echo -e "\n${YELLOW}Infrastructure Services:${NC}"
check_container "elder_tree_postgres"
check_container "elder_tree_redis"
check_container "elder_tree_consul"

# Check monitoring
echo -e "\n${YELLOW}Monitoring Services:${NC}"
check_container "elder_tree_prometheus"
check_container "elder_tree_grafana"
check_container "elder_tree_otel"

# Check 4 Sages
echo -e "\n${YELLOW}4 Sages:${NC}"
check_container "knowledge_sage"
check_container "task_sage"
check_container "incident_sage"
check_container "rag_sage"

# Check Elder Flow
echo -e "\n${YELLOW}Elder Flow:${NC}"
check_container "elder_flow"

# Check Servants
echo -e "\n${YELLOW}Elder Servants:${NC}"
check_container "code_crafter"

# Check Consul services
echo -e "\n${YELLOW}Consul Service Discovery:${NC}"
if curl -s http://localhost:8500/v1/agent/services | jq -r 'keys[]' 2>/dev/null | grep -q "knowledge-sage"; then
    echo -e "${GREEN}✓ Services registered in Consul${NC}"
else
    echo -e "${RED}✗ Services not registered in Consul${NC}"
fi

# Database connectivity
echo -e "\n${YELLOW}Database Connectivity:${NC}"
if docker exec -t elder_tree_postgres pg_isready -U elder_tree > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is accepting connections${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not accepting connections${NC}"
fi

# Redis connectivity
echo -e "\n${YELLOW}Redis Connectivity:${NC}"
if docker exec -t elder_tree_redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is responding${NC}"
else
    echo -e "${RED}✗ Redis is not responding${NC}"
fi

echo -e "\n${GREEN}Health check complete!${NC}"