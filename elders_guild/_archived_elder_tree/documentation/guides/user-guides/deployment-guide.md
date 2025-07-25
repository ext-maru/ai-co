---
audience: administrators
author: claude-elder
category: guides
dependencies: []
description: No description available
difficulty: beginner
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: approved
subcategory: user-guides
tags:
- docker
- redis
- tdd
- python
- elder-tree
- postgresql
- a2a-protocol
- guides
title: Elder Tree v2 Deployment Guide
version: 1.0.0
---

# Elder Tree v2 Deployment Guide

## Prerequisites

1. **Docker & Docker Compose**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **API Keys**
   - OpenAI API Key (for RAG Sage embeddings)
   - Anthropic API Key (for Knowledge/Incident Sage)

3. **System Requirements**
   - CPU: 4+ cores recommended
   - RAM: 16GB+ recommended
   - Storage: 50GB+ for data and logs

## Quick Start

1. **Clone and Setup**
   ```bash
   cd /home/aicompany/ai_co/elder_tree_v2
   
   # Copy environment file
   cp .env.example .env
   
   # Edit .env with your API keys
   nano .env
   ```

2. **Start Services**
   ```bash
   # Start all services
   ./scripts/start_services.sh
   
   # Check health
   ./scripts/health_check.sh
   ```

3. **Access Services**
   - Consul UI: http://localhost:8500
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)

## Service Architecture

### Infrastructure Layer
- **PostgreSQL**: Main database for all services
- **Redis**: Cache and real-time data
- **Consul**: Service discovery and health checking

### AI Agent Layer (4 Sages)
- **Knowledge Sage** (port 50051): Knowledge management
- **Task Sage** (port 50052): Task orchestration
- **Incident Sage** (port 50053): Incident management
- **RAG Sage** (port 50054): Document search and analysis

### Servant Layer (4 Tribes)
- **Code Crafter** (Dwarf, port 60101): Code generation
- **Research Wizard** (RAG Wizard, port 60102): Research and documentation
- **Quality Guardian** (Elf, port 60103): Quality assurance
- **Crisis Responder** (Incident Knight, port 60104): Emergency response

### Orchestration Layer
- **Elder Flow** (port 50100): 5-stage workflow automation

### Monitoring Layer
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **OpenTelemetry**: Distributed tracing

## Configuration

### Environment Variables
Key variables in `.env`:
```bash
# Database
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=your_redis_password

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Quality Standards
QUALITY_THRESHOLD=85.0
TEST_COVERAGE_TARGET=95
```

### Service Configuration
Each service can be configured via environment variables in `docker-compose.yml`.

## Operations

### Starting Services
```bash
# Start all services
./scripts/start_services.sh

# Start specific services
docker-compose up -d knowledge_sage task_sage

# View logs
docker-compose logs -f elder_flow
```

### Stopping Services
```bash
# Stop all services
./scripts/stop_services.sh

# Stop specific service
docker-compose stop code_crafter
```

### Health Monitoring
```bash
# Run health check
./scripts/health_check.sh

# Check specific service
curl http://localhost:50051/health

# View Consul UI
open http://localhost:8500
```

### Database Management
```bash
# Connect to PostgreSQL
docker exec -it elder_tree_postgres psql -U elder_tree -d elder_tree_db

# Backup database
docker exec elder_tree_postgres pg_dump -U elder_tree elder_tree_db > backup.sql

# Restore database
docker exec -i elder_tree_postgres psql -U elder_tree elder_tree_db < backup.sql
```

## Using Elder Tree v2

### Basic A2A Communication
```python
from python_a2a import Client

# Connect to Knowledge Sage
client = Client()
sage = client.connect("localhost", 50051)

# Send message
response = sage.send_message("get_knowledge", {
    "category": "best_practices",
    "key": "tdd"
})
```

### Elder Flow Execution
```python
# Execute Elder Flow
flow = client.connect("localhost", 50100)
result = flow.send_message("execute_flow", {
    "task_type": "feature_implementation",
    "requirements": ["OAuth2.0 authentication"],
    "priority": "high"
})
```

## Monitoring & Debugging

### Prometheus Queries
```promql
# Active Elder Flows
elder_flow_active_flows

# Message rate by service
rate(elder_tree_messages_total[5m])

# Task execution time
histogram_quantile(0.95, servant_task_execution_seconds_bucket)
```

### Grafana Dashboards
1. Access Grafana at http://localhost:3000
2. Login with admin/admin
3. Navigate to Elder Tree Overview dashboard

### Debugging
```bash
# View container logs
docker-compose logs -f --tail=100 knowledge_sage

# Enter container shell
docker exec -it knowledge_sage /bin/bash

# Check service registration
curl http://localhost:8500/v1/agent/services | jq

# Test A2A connectivity
python -m elder_tree.agents.knowledge_sage
```

## Troubleshooting

### Common Issues

1. **Services not starting**
   - Check Docker is running: `docker info`
   - Check ports are available: `netstat -tulpn | grep -E '(5005|6010|5432|6379)'`
   - Review logs: `docker-compose logs`

2. **Database connection errors**
   - Ensure PostgreSQL is healthy: `docker-compose ps postgres`
   - Check credentials in .env
   - Verify network connectivity

3. **API key errors**
   - Ensure API keys are set in .env
   - Check key format and validity
   - Review service logs for specific errors

4. **Service discovery issues**
   - Check Consul health: http://localhost:8500
   - Re-register services: `./scripts/register_consul_services.sh`
   - Verify service ports are correct

## Production Deployment

### Security Hardening
1. Use strong passwords in .env
2. Enable TLS for all services
3. Restrict network access
4. Regular security updates

### Scaling
1. Use Docker Swarm or Kubernetes
2. Configure replicas in docker-compose.yml
3. Setup load balancing
4. Use external PostgreSQL/Redis clusters

### Backup Strategy
1. Daily PostgreSQL backups
2. Redis persistence configuration
3. Consul snapshots
4. Application logs rotation

### Monitoring
1. Setup alerting in Prometheus
2. Configure Grafana notifications
3. Integrate with PagerDuty/Slack
4. Regular health checks

## Maintenance

### Updates
```bash
# Pull latest changes
git pull

# Rebuild images
docker-compose build

# Restart services
docker-compose down
./scripts/start_services.sh
```

### Log Management
```bash
# View logs
docker-compose logs --tail=1000 > logs.txt

# Clean old logs
docker system prune -a --volumes
```

### Performance Tuning
1. Adjust PostgreSQL configuration
2. Tune Redis memory settings
3. Configure service resource limits
4. Monitor and optimize queries

## Support

For issues or questions:
1. Check service logs
2. Review health status
3. Consult Elder Tree documentation
4. Contact the development team