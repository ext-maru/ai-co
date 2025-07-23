#!/bin/bash
# Phase 0: 準備・基盤構築スクリプト
# Elders Guild A2A Migration Plan - Phase 0

set -e

echo "🏛️ Elders Guild A2A Migration - Phase 0: Preparation"
echo "======================================================="

# 環境変数
PROJECT_ROOT="/home/aicompany/ai_co/elders_guild"
A2A_ROOT="${PROJECT_ROOT}/elders_guild_a2a_v3"
VENV_PATH="${A2A_ROOT}/venv"

# Phase 0.1: 新A2A環境セットアップ
echo "🔧 Step 1: Setting up new A2A environment..."

if [ -d "$A2A_ROOT" ]; then
    echo "⚠️  A2A root directory already exists. Removing..."
    rm -rf "$A2A_ROOT"
fi

mkdir -p "$A2A_ROOT"
cd "$A2A_ROOT"

echo "✅ Created A2A root directory: $A2A_ROOT"

# 仮想環境作成
echo "🐍 Creating Python virtual environment..."
python3 -m venv "$VENV_PATH"
source "$VENV_PATH/bin/activate"
echo "✅ Virtual environment created and activated"

# 必要なパッケージインストール
echo "📦 Installing required packages..."
pip install --upgrade pip
pip install \
    python-a2a==0.5.9 \
    fastapi==0.108.0 \
    uvicorn[standard]==0.25.0 \
    pydantic==2.5.0 \
    pytest==7.4.0 \
    pytest-asyncio==0.21.0 \
    pytest-cov==4.1.0 \
    mypy==1.8.0 \
    black==23.12.0 \
    ruff==0.1.6 \
    prometheus-client==0.19.0 \
    structlog==23.2.0

echo "✅ Packages installed successfully"

# Phase 0.2: ディレクトリ構造準備
echo "🗂️  Step 2: Creating directory structure..."

mkdir -p {agents,tests,configs,scripts,docs,gateway,monitoring}
mkdir -p tests/{unit,integration,performance}
mkdir -p agents/{base,knowledge_sage,task_sage,incident_sage,rag_sage}
mkdir -p configs/{development,staging,production}
mkdir -p scripts/{deployment,testing,monitoring}

echo "✅ Directory structure created"

# Phase 0.3: 基本設定ファイル作成
echo "⚙️ Step 3: Creating configuration files..."

# requirements.txt作成
cat > requirements.txt << 'EOF'
# Elders Guild A2A Requirements
python-a2a==0.5.9
fastapi==0.108.0
uvicorn[standard]==0.25.0
pydantic==2.5.0
prometheus-client==0.19.0
structlog==23.2.0
httpx==0.25.0
python-multipart==0.0.6

# Development & Testing
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
pytest-benchmark==4.0.0
mypy==1.8.0
black==23.12.0
ruff==0.1.6
EOF

# pyproject.toml作成  
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "elders-guild-a2a"
version = "3.0.0"
description = "Elders Guild A2A Distributed AI System"
authors = [{name = "Claude Elder", email = "claude@elders-guild.ai"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "python-a2a>=0.5.9",
    "fastapi>=0.108.0",
    "uvicorn[standard]>=0.25.0",
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0", 
    "pytest-cov>=4.1.0",
    "mypy>=1.8.0",
    "black>=23.12.0",
    "ruff>=0.1.6",
]

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra --strict-markers --cov=agents --cov-report=term-missing --cov-report=html"
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W", "B", "Q"]
target-version = "py311"
EOF

# Docker設定作成
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# デフォルト実行
CMD ["python", "-m", "agents.base"]
EOF

# Docker Compose設定
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  knowledge-sage:
    build: .
    ports:
      - "8001:8001"
    environment:
      - AGENT_NAME=knowledge-sage
      - AGENT_PORT=8001
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8001/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  task-sage:
    build: .
    ports:
      - "8002:8002"
    environment:
      - AGENT_NAME=task-sage
      - AGENT_PORT=8002
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8002/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  incident-sage:
    build: .
    ports:
      - "8003:8003"
    environment:
      - AGENT_NAME=incident-sage
      - AGENT_PORT=8003
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8003/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  rag-sage:
    build: .
    ports:
      - "8004:8004"
    environment:
      - AGENT_NAME=rag-sage
      - AGENT_PORT=8004
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8004/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  gateway:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SERVICE_TYPE=gateway
      - LOG_LEVEL=INFO
    depends_on:
      - knowledge-sage
      - task-sage
      - incident-sage
      - rag-sage
    command: ["python", "-m", "gateway.main"]

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

networks:
  default:
    name: elders-guild-a2a
EOF

echo "✅ Configuration files created"

# Phase 0.4: テスト環境設定
echo "🧪 Step 4: Setting up test environment..."

# pytest.ini作成
cat > pytest.ini << 'EOF'
[tool:pytest]
minversion = 7.0
addopts = -ra --strict-markers --cov=agents --cov-report=term-missing --cov-report=html
testpaths = tests
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
EOF

# テストヘルパー作成
cat > tests/conftest.py << 'EOF'
"""Test configuration and fixtures for Elders Guild A2A system."""

import pytest
import asyncio
from typing import AsyncGenerator
from python_a2a import A2AServer, A2AClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_agent():
    """Create a test A2A agent for testing."""
    class TestAgent(A2AServer):
        def __init__(self):
            super().__init__(name="test-agent", port=9999)
    
    agent = TestAgent()
    yield agent
    await agent.shutdown()


@pytest.fixture
async def test_client():
    """Create a test A2A client."""
    client = A2AClient("http://localhost:9999/a2a")
    yield client
    await client.close()
EOF

echo "✅ Test environment configured"

# Phase 0.5: CI/CD設定
echo "🚀 Step 5: Setting up CI/CD pipeline..."

mkdir -p .github/workflows

cat > .github/workflows/ci.yml << 'EOF'
name: Elders Guild A2A CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Lint with ruff
      run: |
        ruff check .
    
    - name: Format with black
      run: |
        black --check .
    
    - name: Type check with mypy
      run: |
        mypy agents/
    
    - name: Test with pytest
      run: |
        pytest --cov=agents --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  docker:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build Docker image
      run: |
        docker build -t elders-guild-a2a:latest .
    
    - name: Test Docker image
      run: |
        docker-compose up -d
        sleep 30
        docker-compose ps
        docker-compose logs
        docker-compose down
EOF

echo "✅ CI/CD pipeline configured"

# Phase 0.6: ドキュメント基盤作成
echo "📚 Step 6: Creating documentation structure..."

cat > README.md << 'EOF'
# 🏛️ Elders Guild A2A - Distributed AI System

**Version**: 3.0.0  
**Status**: In Development  
**Migration**: Phase 0 Complete

## 🎯 Overview

Elders Guild A2A is a distributed AI collaboration system where specialized AI agents (4 Sages) work together to solve complex problems using standardized Agent-to-Agent (A2A) communication.

## 🏗️ Architecture

```
🌐 Distributed A2A System
├── 📚 Knowledge Sage (Port 8001) - Knowledge Management
├── 📋 Task Sage (Port 8002) - Task Management  
├── 🚨 Incident Sage (Port 8003) - Incident Response
└── 🔍 RAG Sage (Port 8004) - Research & Analysis

💬 Communication: python-a2a (Google A2A Protocol)
🌐 Gateway: FastAPI (Port 8000)
📊 Monitoring: Prometheus + Grafana
```

## 🚀 Quick Start

```bash
# Development
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run agents
python -m agents.knowledge_sage
python -m agents.task_sage
python -m agents.incident_sage  
python -m agents.rag_sage

# Run gateway
python -m gateway.main

# Docker Compose
docker-compose up -d
```

## 📊 Migration Status

- [x] Phase 0: Preparation & Foundation ✅
- [ ] Phase 1: Base A2A Implementation
- [ ] Phase 2: 4 Sages Migration
- [ ] Phase 3: Tech Debt Removal
- [ ] Phase 4: Production Deployment

## 📚 Documentation

- [Migration Plan](docs/migration/ELDERS_GUILD_A2A_MIGRATION_PLAN.md)
- [Architecture Design](../docs/technical/ELDERS_GUILD_ARCHITECTURE_DESIGN.md)
- [API Documentation](docs/api/)

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests  
pytest tests/integration/

# Performance tests
pytest tests/performance/ --benchmark

# Coverage
pytest --cov=agents --cov-report=html
```

## 🏛️ Elders Guild Principles

- **🎯 OSS First**: Use proven open source libraries
- **🔄 TDD**: Test-Driven Development mandatory
- **📊 Zero Tech Debt**: Clean, maintainable code
- **🌐 Distributed**: True distributed processing
- **📈 Monitored**: Full observability

---

**"Don't Reinvent the Wheel, Embrace Standards, Distribute & Collaborate"**  
**Elders Guild A2A Core Principles**
EOF

cat > docs/README.md << 'EOF'
# 📚 Elders Guild A2A Documentation

## 📋 Documentation Structure

- `migration/` - Migration plans and guides
- `api/` - API documentation
- `architecture/` - System architecture docs
- `deployment/` - Deployment guides
- `troubleshooting/` - Common issues and solutions

## 🔗 Quick Links

- [Migration Plan](migration/ELDERS_GUILD_A2A_MIGRATION_PLAN.md)
- [Architecture Overview](../docs/technical/ELDERS_GUILD_ARCHITECTURE_DESIGN.md)
- [API Reference](api/)
- [Deployment Guide](deployment/)

## 🆕 Latest Updates

- **2025-07-23**: Phase 0 preparation completed
- **2025-07-23**: Migration plan finalized
- **2025-07-23**: Development environment ready
EOF

echo "✅ Documentation structure created"

# Phase 0.7: 品質チェックツール設定
echo "🔍 Step 7: Setting up quality assurance tools..."

# pre-commit設定
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [python-a2a, fastapi, pydantic]
EOF

# Makefile作成
cat > Makefile << 'EOF'
.PHONY: help test lint format type-check install clean docker-build docker-run

help:
	@echo "Elders Guild A2A Development Commands"
	@echo "===================================="
	@echo "install     Install development dependencies"
	@echo "test        Run all tests"
	@echo "lint        Run linting checks"
	@echo "format      Format code with black"
	@echo "type-check  Run mypy type checking"
	@echo "clean       Clean cache and build files"
	@echo "docker-build Build Docker image"
	@echo "docker-run  Run with Docker Compose"

install:
	pip install -r requirements.txt
	pip install -e .[dev]
	pre-commit install

test:
	pytest tests/ -v

lint:
	ruff check .
	black --check .

format:
	black .
	ruff --fix .

type-check:
	mypy agents/

clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

docker-build:
	docker build -t elders-guild-a2a:latest .

docker-run:
	docker-compose up -d
EOF

echo "✅ Quality assurance tools configured"

# Phase 0.8: 最終確認
echo "✅ Step 8: Final verification..."

# 仮想環境再アクティベート
source "$VENV_PATH/bin/activate"

# パッケージ確認
echo "📦 Verifying installed packages..."
python -c "import python_a2a; print(f'python-a2a: {python_a2a.__version__}')"
python -c "import fastapi; print(f'fastapi: {fastapi.__version__}')"
python -c "import pydantic; print(f'pydantic: {pydantic.__version__}')"

# ディレクトリ構造確認
echo "🗂️  Directory structure verification:"
tree -d -L 3 || ls -la

echo ""
echo "🎉 Phase 0: Preparation & Foundation - COMPLETED!"
echo "======================================================="
echo "✅ New A2A environment created: $A2A_ROOT"
echo "✅ Python virtual environment: $VENV_PATH"  
echo "✅ All required packages installed"
echo "✅ Directory structure prepared"
echo "✅ Configuration files created"
echo "✅ CI/CD pipeline configured"
echo "✅ Documentation structure ready"
echo "✅ Quality assurance tools setup"
echo ""
echo "🚀 Ready for Phase 1: Base A2A Implementation"
echo "Next: ./scripts/migration/phase1_base_implementation.sh"
echo ""
echo "🏛️ Elders Guild A2A Migration - Phase 0 Complete!"