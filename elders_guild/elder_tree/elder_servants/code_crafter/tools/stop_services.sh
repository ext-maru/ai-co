#!/bin/bash
# Elder Tree v2 Services Stop Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Elder Tree v2 Services...${NC}"

# Stop all services
docker-compose down

# Optionally remove volumes (uncomment if needed)
# echo -e "${YELLOW}Removing volumes...${NC}"
# docker-compose down -v

echo -e "${GREEN}All services stopped.${NC}"