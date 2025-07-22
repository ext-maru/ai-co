#!/bin/bash
# Elder Tree v2 Services Startup Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Elder Tree v2 Services...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update .env file with your API keys and configuration.${NC}"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Build Docker images
echo -e "${GREEN}Building Docker images...${NC}"
docker-compose build

# Start infrastructure services first
echo -e "${GREEN}Starting infrastructure services...${NC}"
docker-compose up -d postgres redis consul

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
until docker-compose exec -T postgres pg_isready -U elder_tree > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo -e "${GREEN}PostgreSQL is ready!${NC}"

# Wait for Redis to be ready
echo -e "${YELLOW}Waiting for Redis to be ready...${NC}"
until docker-compose exec -T redis redis-cli --raw ping > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo -e "${GREEN}Redis is ready!${NC}"

# Wait for Consul to be ready
echo -e "${YELLOW}Waiting for Consul to be ready...${NC}"
until docker-compose exec -T consul consul members > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo -e "${GREEN}Consul is ready!${NC}"

# Start monitoring services
echo -e "${GREEN}Starting monitoring services...${NC}"
docker-compose up -d prometheus grafana otel_collector

# Start Elder Tree services
echo -e "${GREEN}Starting Elder Tree services...${NC}"
docker-compose up -d knowledge_sage task_sage incident_sage rag_sage

# Wait for sages to be ready
echo -e "${YELLOW}Waiting for 4 Sages to initialize...${NC}"
sleep 10

# Start servants
echo -e "${GREEN}Starting Elder Servants...${NC}"
docker-compose up -d code_crafter

# Start Elder Flow orchestrator
echo -e "${GREEN}Starting Elder Flow orchestrator...${NC}"
docker-compose up -d elder_flow

# Show service status
echo -e "${GREEN}All services started! Checking status...${NC}"
docker-compose ps

# Show service URLs
echo -e "${GREEN}Service URLs:${NC}"
echo -e "  Consul UI:    http://localhost:8500"
echo -e "  Prometheus:   http://localhost:9090"
echo -e "  Grafana:      http://localhost:3000 (admin/admin)"
echo -e "  PostgreSQL:   localhost:5432"
echo -e "  Redis:        localhost:6379"

# Register services with Consul
echo -e "${GREEN}Registering services with Consul...${NC}"
./scripts/register_consul_services.sh

echo -e "${GREEN}Elder Tree v2 is ready!${NC}"