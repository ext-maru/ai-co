#!/bin/bash
# TDD Cycle Runner
# Red -> Green -> Refactor

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Starting TDD Cycle...${NC}"

# Red Phase: Run tests (expect failures)
echo -e "${RED}📍 Red Phase: Running tests (expecting failures)...${NC}"
poetry run pytest tests/ -v --tb=short || true

# Prompt for implementation
echo -e "${YELLOW}⚡ Implement code to make tests pass, then press Enter...${NC}"
read -p "Press Enter when ready to continue..."

# Green Phase: Run tests (expect success)
echo -e "${GREEN}📍 Green Phase: Running tests (expecting success)...${NC}"
poetry run pytest tests/ -v

# Coverage Report
echo -e "${YELLOW}📊 Coverage Report:${NC}"
poetry run pytest --cov=elder_tree --cov-report=term-missing

# Refactor Phase
echo -e "${YELLOW}♻️  Refactor Phase: Running quality checks...${NC}"
poetry run black src/ tests/
poetry run ruff src/ tests/
poetry run mypy src/

echo -e "${GREEN}✅ TDD Cycle Complete!${NC}"
