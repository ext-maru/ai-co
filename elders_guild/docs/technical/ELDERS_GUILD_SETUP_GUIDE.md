# 📖 Elders Guild Setup and Installation Guide
# Elders Guild 導入・セットアップガイド

**Version 1.0.0 | Last Updated: 2025-07-10**
**Step-by-Step Guide for System Deployment**

---

## 📋 Table of Contents | 目次

1. [Prerequisites | 環境要件と前提条件](#prerequisites--環境要件と前提条件)
2. [Installation Steps | ステップバイステップ導入手順](#installation-steps--ステップバイステップ導入手順)
3. [Configuration Details | 設定ファイルの詳細](#configuration-details--設定ファイルの詳細)
4. [Initial Setup | 初期セットアップ](#initial-setup--初期セットアップ)
5. [Verification | 動作確認](#verification--動作確認)
6. [Troubleshooting | トラブルシューティング](#troubleshooting--トラブルシューティング)
7. [Advanced Configuration | 高度な設定](#advanced-configuration--高度な設定)
8. [Migration Guide | 移行ガイド](#migration-guide--移行ガイド)

---

## Prerequisites | 環境要件と前提条件

### 🖥️ System Requirements

#### Minimum Requirements
- **OS**: Ubuntu 20.04+ / macOS 12+ / Windows 10+ (WSL2)
- **CPU**: 4 cores
- **RAM**: 16GB
- **Storage**: 50GB available space
- **Network**: Stable internet connection

#### Recommended Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 8+ cores
- **RAM**: 32GB+
- **Storage**: 100GB+ SSD
- **Network**: High-speed connection (100Mbps+)

### 🛠️ Software Dependencies

```bash
# Required Software Versions
- Python 3.10+
- Docker 24.0+
- Docker Compose 2.20+
- PostgreSQL 15+
- Redis 7.0+
- RabbitMQ 3.12+
- Node.js 18+ (for web interface)
```

### 📦 Python Dependencies

```bash
# Core Dependencies
pip>=23.0
setuptools>=65.0
wheel>=0.40.0

# AI/ML Libraries
openai>=1.0.0
anthropic>=0.3.0
langchain>=0.1.0
pgvector>=0.2.0
numpy>=1.24.0
pandas>=2.0.0

# Web Framework
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0

# Database
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
alembic>=1.11.0

# Message Queue
pika>=1.3.0
celery>=5.3.0
redis>=5.0.0

# Monitoring
prometheus-client>=0.17.0
sentry-sdk>=1.30.0
```

---

## Installation Steps | ステップバイステップ導入手順

### 🚀 Quick Start (Automated)

```bash
# Clone the repository
git clone https://github.com/ai-company/elders-guild.git
cd elders-guild

# Run automated setup
./scripts/quick_setup.sh

# This script will:
# 1. Check system requirements
# 2. Install dependencies
# 3. Set up databases
# 4. Configure Elder Tree
# 5. Initialize Four Sages
# 6. Start core services
```

### 📝 Manual Installation

#### Step 1: Environment Setup

```bash
# Create project directory
mkdir -p ~/ai_company/ai_co
cd ~/ai_company/ai_co

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Step 2: Database Setup

```bash
# PostgreSQL Setup
sudo -u postgres psql <<EOF
CREATE DATABASE ai_company;
CREATE USER elder_admin WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_company TO elder_admin;

-- Enable pgvector extension
\c ai_company
CREATE EXTENSION IF NOT EXISTS vector;
EOF

# Redis Setup
sudo systemctl start redis
redis-cli ping  # Should return PONG

# RabbitMQ Setup
sudo systemctl start rabbitmq-server
sudo rabbitmqctl add_user elder_user your_password
sudo rabbitmqctl set_permissions -p / elder_user ".*" ".*" ".*"
```

#### Step 3: Elder Tree Initialization

```bash
# Initialize Elder Tree hierarchy
python3 scripts/initialize_elder_tree.py

# Create Elder roles and permissions
python3 scripts/setup_elder_hierarchy.py

# Expected output:
# ✅ Grand Elder maru created
# ✅ Claude Elder initialized
# ✅ Four Sages configured
# ✅ Elder Council established
# ✅ Worker permissions set
```

#### Step 4: Four Sages Configuration

```bash
# Initialize Four Sages
python3 scripts/initialize_four_sages.py \
    --knowledge-path ./knowledge_base \
    --vector-db postgresql://elder_admin:password@localhost/ai_company \
    --enable-learning true \
    --sage-consensus-threshold 0.75
```

#### Step 5: Worker Deployment

```bash
# Build Docker images
docker-compose build

# Start core workers
docker-compose up -d \
    authentication_worker \
    task_worker \
    pm_worker \
    result_worker

# Verify worker status
docker-compose ps
```

#### Step 6: Web Interface Setup

```bash
# Install Node.js dependencies
cd web
npm install

# Build frontend
npm run build

# Start web server
npm run start
```

---

## Configuration Details | 設定ファイルの詳細

### 🔧 Main Configuration File

Create `/config/elders_guild.yaml`:

```yaml
# Elders Guild Main Configuration
version: 1.0.0

# Elder Tree Configuration
elder_tree:
  hierarchy:
    grand_elder:
      name: "maru"
      email: "maru@ai-company.com"
      permissions: ["all"]

    claude_elder:
      name: "Claude Elder"
      email: "claude@ai-company.com"
      permissions: ["operational", "development", "worker_management"]

    four_sages:
      knowledge:
        name: "Knowledge Sage"
        specialization: "learning_and_documentation"
        vector_db: "postgresql://localhost/ai_company"

      task:
        name: "Task Sage"
        specialization: "workflow_optimization"
        queue_size: 10000

      incident:
        name: "Incident Sage"
        specialization: "monitoring_and_security"
        alert_channels: ["email", "slack", "webhook"]

      rag:
        name: "RAG Sage"
        specialization: "search_and_retrieval"
        index_size: "10GB"

# Database Configuration
database:
  main:
    type: "postgresql"
    host: "${DB_HOST:-localhost}"
    port: 5432
    name: "ai_company"
    user: "${DB_USER:-elder_admin}"
    password: "${DB_PASSWORD}"
    pool_size: 20

  vector:
    type: "pgvector"
    dimension: 1536
    index_type: "ivfflat"
    lists: 100

# Message Queue Configuration
message_queue:
  type: "rabbitmq"
  host: "${MQ_HOST:-localhost}"
  port: 5672
  user: "${MQ_USER:-elder_user}"
  password: "${MQ_PASSWORD}"
  vhost: "/"

  exchanges:
    elder_tree: "elder.tree.exchange"
    four_sages: "four.sages.exchange"
    workers: "workers.exchange"

# Worker Configuration
workers:
  default_settings:
    prefetch_count: 10
    max_retries: 3
    timeout: 300
    log_level: "INFO"

  scaling:
    auto_scale: true
    min_instances: 1
    max_instances: 10
    scale_threshold: 0.8

# Security Configuration
security:
  jwt_secret: "${JWT_SECRET}"
  session_timeout: 86400
  enable_mfa: true
  ip_whitelist: []
  rate_limiting:
    enabled: true
    requests_per_minute: 100

# Monitoring Configuration
monitoring:
  prometheus:
    enabled: true
    port: 9090

  sentry:
    enabled: true
    dsn: "${SENTRY_DSN}"

  logging:
    level: "INFO"
    format: "json"
    retention_days: 30
```

### 🌳 Elder Tree Rules Configuration

Create `/config/elder_rules.json`:

```json
{
  "version": "1.0.0",
  "hierarchy_rules": {
    "escalation_paths": {
      "servant_to_sage": {
        "conditions": ["complexity > 0.7", "error_count > 3"],
        "timeout": 300
      },
      "sage_to_elder": {
        "conditions": ["impact == 'system-wide'", "requires_decision == true"],
        "timeout": 600
      },
      "elder_to_grand": {
        "conditions": ["severity == 'critical'", "system_shutdown_risk == true"],
        "timeout": 60
      }
    },
    "communication_protocols": {
      "message_format": "elder_message_v1",
      "encryption": "aes-256-gcm",
      "signature": "ed25519"
    },
    "decision_making": {
      "consensus_required": {
        "four_sages": 3,
        "elder_council": 0.66
      },
      "veto_powers": {
        "grand_elder": true,
        "claude_elder": ["operational_decisions"]
      }
    }
  }
}
```

### 🧙‍♂️ Four Sages Configuration

Create `/config/four_sages_config.yaml`:

```yaml
# Four Sages Specialized Configuration
knowledge_sage:
  knowledge_base:
    path: "./knowledge_base"
    index_refresh: "5m"
    compression: "zstd"

  learning:
    batch_size: 100
    learning_rate: 0.001
    update_frequency: "hourly"

task_sage:
  scheduling:
    algorithm: "priority_weighted_round_robin"
    lookahead: 100
    rebalance_interval: "30s"

  optimization:
    enable_ml: true
    history_window: 7d
    prediction_confidence: 0.85

incident_sage:
  monitoring:
    health_check_interval: "10s"
    metric_retention: "30d"
    anomaly_detection: true

  alerting:
    channels:
      email:
        smtp_server: "${SMTP_SERVER}"
        from: "incident-sage@ai-company.com"
      slack:
        webhook: "${SLACK_WEBHOOK}"
        channel: "#incidents"

  thresholds:
    cpu_critical: 90
    memory_critical: 85
    error_rate_critical: 0.05

rag_sage:
  vector_search:
    algorithm: "hnsw"
    ef_construction: 200
    m: 16

  retrieval:
    top_k: 10
    similarity_threshold: 0.7
    rerank: true

  caching:
    enabled: true
    ttl: "1h"
    max_size: "4GB"
```

---

## Initial Setup | 初期セットアップ

### 🎯 First Run Checklist

1. **Environment Variables**
```bash
# Create .env file
cat > .env <<EOF
# Database
DB_HOST=localhost
DB_USER=elder_admin
DB_PASSWORD=your_secure_password

# Message Queue
MQ_HOST=localhost
MQ_USER=elder_user
MQ_PASSWORD=your_mq_password

# Security
JWT_SECRET=$(openssl rand -base64 32)
ELDER_GUILD_VERSION=1.0.0

# Monitoring
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_ENABLED=true

# Four Sages
SAGE_WISDOM_LEVEL=maximum
AUTO_DOCUMENTATION=true
VECTOR_SEARCH_ENABLED=true
EOF
```

2. **Initialize Elder Accounts**
```python
# scripts/create_elder_accounts.py
from libs.unified_auth_provider import UnifiedAuthProvider

auth = UnifiedAuthProvider()

# Create Grand Elder
auth.create_elder_user(
    username="maru",
    email="maru@ai-company.com",
    role="GRAND_ELDER",
    password="secure_grand_elder_password"
)

# Create Claude Elder
auth.create_elder_user(
    username="claude_elder",
    email="claude@ai-company.com",
    role="CLAUDE_ELDER",
    password="secure_claude_password"
)

# Create Four Sages
for sage in ["knowledge", "task", "incident", "rag"]:
    auth.create_elder_user(
        username=f"{sage}_sage",
        email=f"{sage}@ai-company.com",
        role="SAGE",
        sage_type=sage.upper(),
        password=f"secure_{sage}_password"
    )
```

3. **Bootstrap Knowledge Base**
```bash
# Import initial knowledge
python3 scripts/import_knowledge.py \
    --source ./knowledge_base \
    --vectorize true \
    --sage knowledge

# Verify knowledge import
python3 -c "
from libs.four_sages_integration import FourSagesIntegration
sages = FourSagesIntegration()
stats = sages.get_knowledge_stats()
print(f'Knowledge items: {stats['total_items']}')
print(f'Vector embeddings: {stats['total_embeddings']}')
"
```

---

## Verification | 動作確認

### ✅ System Health Check

```bash
# Run comprehensive health check
python3 scripts/health_check.py --comprehensive

# Expected output:
# ✅ Database Connection: OK
# ✅ Redis Connection: OK
# ✅ RabbitMQ Connection: OK
# ✅ Elder Tree: ACTIVE
# ✅ Four Sages: ALL ONLINE
# ✅ Workers: 32/32 RUNNING
# ✅ Knowledge Base: INDEXED
# ✅ Vector Search: OPERATIONAL
```

### 🧪 Test Commands

```bash
# Test Elder Tree communication
python3 -c "
from libs.elder_tree_hierarchy import ElderTree
tree = ElderTree()
response = tree.send_message(
    from_rank='servant',
    to_rank='sage',
    sage_type='task',
    message='Test message'
)
print(f'Response: {response}')
"

# Test Four Sages coordination
python3 scripts/test_four_sages.py

# Test worker execution
ai-send "Create a simple Python hello world script"
```

### 📊 Monitoring Dashboard

Access the monitoring dashboards:

1. **Elder Tree Status**: http://localhost:3000/elder-tree
2. **Four Sages Monitor**: http://localhost:3000/four-sages
3. **Worker Dashboard**: http://localhost:3000/workers
4. **System Metrics**: http://localhost:9090 (Prometheus)

---

## Troubleshooting | トラブルシューティング

### 🚨 Common Issues and Solutions

#### Issue 1: Database Connection Failed
```bash
# Error: could not connect to database
# Solution:
sudo systemctl status postgresql
sudo systemctl restart postgresql

# Verify connection
psql -h localhost -U elder_admin -d ai_company -c "SELECT 1;"
```

#### Issue 2: Worker Not Starting
```bash
# Check worker logs
docker-compose logs -f <worker_name>

# Common fixes:
docker-compose restart <worker_name>
docker-compose down && docker-compose up -d
```

#### Issue 3: Four Sages Not Responding
```python
# Debug Four Sages
from libs.four_sages_integration import FourSagesIntegration

sages = FourSagesIntegration()
for sage in ['knowledge', 'task', 'incident', 'rag']:
    status = sages.check_sage_health(sage)
    print(f"{sage}: {status}")
```

#### Issue 4: Elder Tree Communication Error
```bash
# Check message queue
sudo rabbitmqctl list_queues
sudo rabbitmqctl list_exchanges

# Reset Elder Tree
python3 scripts/reset_elder_tree.py --preserve-data
```

### 📝 Debug Mode

Enable debug logging:

```bash
# Set debug environment
export ELDER_DEBUG=true
export LOG_LEVEL=DEBUG

# Run with verbose output
python3 scripts/run_with_debug.py
```

---

## Advanced Configuration | 高度な設定

### 🔒 Security Hardening

```yaml
# config/security_hardening.yaml
security:
  # Enable strict mode
  strict_mode: true

  # TLS Configuration
  tls:
    enabled: true
    cert_path: "/etc/ssl/certs/elder.crt"
    key_path: "/etc/ssl/private/elder.key"
    min_version: "1.3"

  # Authentication
  auth:
    password_policy:
      min_length: 16
      require_special: true
      require_numbers: true
      history_count: 5

    session:
      timeout: 3600
      concurrent_limit: 3
      ip_binding: true

  # Audit
  audit:
    log_all_access: true
    retain_days: 90
    encrypt_logs: true
```

### ⚡ Performance Optimization

```yaml
# config/performance.yaml
performance:
  # Database pooling
  database:
    connection_pool:
      min_size: 10
      max_size: 50
      overflow: 20

    query_optimization:
      enable_cache: true
      cache_size: "2GB"
      prepared_statements: true

  # Message queue tuning
  rabbitmq:
    prefetch_count: 20
    heartbeat: 30
    connection_pool: 10

  # Worker optimization
  workers:
    process_pool:
      processes: 8
      maxtasksperchild: 1000

    async_settings:
      event_loop: "uvloop"
      max_concurrent: 100
```

### 🌐 Multi-Region Setup

```yaml
# config/multi_region.yaml
regions:
  primary:
    name: "us-east-1"
    endpoint: "https://primary.elders-guild.com"

  replicas:
    - name: "eu-west-1"
      endpoint: "https://eu.elders-guild.com"
      sync_delay: "5s"

    - name: "ap-northeast-1"
      endpoint: "https://jp.elders-guild.com"
      sync_delay: "10s"

  failover:
    strategy: "automatic"
    health_check_interval: "30s"
    min_healthy_replicas: 1
```

---

## Migration Guide | 移行ガイド

### 📦 Migrating from Previous Version

```bash
# Backup current system
./scripts/backup_system.sh --full

# Run migration script
./scripts/migrate_to_v1.py \
    --from-version 0.9.0 \
    --preserve-data true \
    --verify-integrity true

# Migration steps:
# 1. Database schema update
# 2. Configuration migration
# 3. Knowledge base reindex
# 4. Worker compatibility check
# 5. Permission migration
```

### 🔄 Rolling Update Strategy

```bash
# Phase 1: Update passive components
docker-compose up -d --no-deps \
    documentation_worker \
    audit_worker

# Phase 2: Update Four Sages (one by one)
for sage in knowledge task incident rag; do
    python3 scripts/update_sage.py --sage $sage
    sleep 30
done

# Phase 3: Update core workers
./scripts/rolling_update.sh --group core

# Phase 4: Update Elder Tree
./scripts/update_elder_tree.sh --graceful
```

---

## 📚 Additional Resources

### Documentation
- [Complete Operation Manual](./ELDERS_GUILD_OPERATION_MANUAL.md)
- [API Reference](./ELDERS_GUILD_API_REFERENCE.md)
- [Best Practices Guide](./ELDERS_GUILD_BEST_PRACTICES.md)

### Support Channels
- **Documentation**: https://docs.elders-guild.com
- **Community Forum**: https://forum.elders-guild.com
- **Discord**: https://discord.gg/elders-guild
- **Email Support**: support@elders-guild.com

### Training Materials
- Video Tutorials: https://learn.elders-guild.com
- Interactive Labs: https://labs.elders-guild.com
- Certification Program: https://cert.elders-guild.com

---

**Setup Guide Version**: 1.0.0
**Last Updated**: 2025-07-10
**Next Update**: 2025-08-10

**🏛️ Welcome to the Elders Guild**
**May the wisdom of the Elders guide your path**
