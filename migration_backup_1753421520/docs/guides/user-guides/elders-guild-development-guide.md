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
- postgresql
- testing
- guides
title: Elders Guild Development Guide
version: 1.0.0
---

# Elders Guild Development Guide
## エルダーズギルド開発ガイド

**Created**: 2025-01-11
**Author**: Claude Elder
**Version**: 1.0.0

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Coding Standards](#coding-standards)
4. [Development Workflow](#development-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Deployment Process](#deployment-process)
7. [Monitoring and Debugging](#monitoring-and-debugging)
8. [Security Guidelines](#security-guidelines)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

### System Architecture
The Elders Guild platform follows a microservices architecture with event-driven communication:

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                   API Gateway                               │
│                (FastAPI + OAuth2)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                 Event Bus System                            │
│              (Redis + PostgreSQL)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                   4 Sage Systems                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │  Knowledge  │ │    Task     │ │  Incident   │ │   RAG   │ │
│  │    Sage     │ │    Sage     │ │    Sage     │ │  Sage   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Components
- **API Gateway**: Unified entry point for all client requests
- **Event Bus**: Asynchronous communication between services
- **4 Sage Systems**: Specialized microservices for different domains
- **PostgreSQL**: Primary database with pgvector for AI features
- **Redis**: Caching and message queue
- **Monitoring**: Prometheus, Grafana, and custom metrics

---

## 🛠️ Development Environment Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- Node.js 18+ (for frontend development)

### Setup Steps

1. **Clone the Repository**
```bash
git clone https://github.com/your-org/elders-guild.git
cd elders-guild
```

2. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

3. **Install Dependencies**
```bash
# Python dependencies
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt
```

4. **Database Setup**
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run migrations
python -m libs.elders_guild_db_manager --migrate
```

5. **Development Server**
```bash
# Start all services
docker-compose up -d

# Or start API server only
python -m uvicorn libs.elders_guild_api_spec:app --reload
```

### IDE Configuration

#### VS Code Settings
Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "files.associations": {
    "*.py": "python"
  }
}
```

---

## 📏 Coding Standards

### Python Code Style
We follow PEP 8 with modifications:

#### Basic Rules
- Line length: 100 characters
- Indentation: 4 spaces
- String quotes: Double quotes for strings, single quotes for string literals
- Imports: Standard library → Third party → Local imports

#### Code Formatting
```python
# Good
async def create_knowledge_entity(
    title: str,
    content: str,
    category_id: Optional[str] = None,
    tags: List[str] = None
) -> KnowledgeEntity:
    """Create a new knowledge entity.

    Args:
        title: Entity title
        content: Entity content
        category_id: Optional category ID
        tags: Optional list of tags

    Returns:
        Created knowledge entity

    Raises:
        ValidationError: If validation fails
    """
    if tags is None:
        tags = []

    entity = KnowledgeEntity(
        title=title,
        content=content,
        category_id=category_id,
        tags=tags
    )

    await entity.save()
    return entity
```

#### Type Hints
Always use type hints:
```python
from typing import Dict, List, Optional, Any, Union
from libs.elders_guild_data_models import KnowledgeEntity

def process_knowledge_data(
    data: Dict[str, Any],
    filters: Optional[List[str]] = None
) -> List[KnowledgeEntity]:
    """Process knowledge data with optional filters."""
    # Implementation
```

#### Error Handling
```python
class ElderGuildError(Exception):
    """Base exception for Elders Guild."""
    pass

class ValidationError(ElderGuildError):
    """Validation error."""
    pass

# Usage
try:
    result = await process_data(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise ElderGuildError(f"Processing failed: {e}")
```

### Documentation Standards

#### Docstrings
Use Google-style docstrings:
```python
def calculate_similarity(
    vector1: List[float],
    vector2: List[float],
    method: str = "cosine"
) -> float:
    """Calculate similarity between two vectors.

    Args:
        vector1: First vector
        vector2: Second vector
        method: Similarity method ('cosine', 'euclidean', 'dot')

    Returns:
        Similarity score between 0 and 1

    Raises:
        ValueError: If vectors have different dimensions

    Example:
        >>> vec1 = [1.0, 2.0, 3.0]
        >>> vec2 = [4.0, 5.0, 6.0]
        >>> similarity = calculate_similarity(vec1, vec2)
        >>> print(f"Similarity: {similarity:.2f}")
    """
```

#### Code Comments
```python
# Good: Explain why, not what
# Calculate quality score based on content length and metadata richness
# This helps prioritize knowledge entities in search results
quality_score = self._calculate_quality_score(content, metadata)

# Bad: Explain what
# Set quality score to result of calculation
quality_score = self._calculate_quality_score(content, metadata)
```

---

## 🔄 Development Workflow

### Git Workflow
We use Git Flow with protection rules:

#### Branch Strategy
```
main           (production)
├── develop    (development)
│   ├── feature/sage-knowledge-enhancement
│   ├── feature/api-v2-endpoints
│   └── feature/event-bus-optimization
├── release/1.2.0
└── hotfix/critical-bug-fix
```

#### Commit Messages
Follow Conventional Commits:
```
feat: add semantic search to knowledge sage
fix: resolve memory leak in event bus
docs: update API documentation
test: add integration tests for task sage
refactor: optimize database queries
chore: update dependencies
```

#### Pull Request Process
1. Create feature branch from `develop`
2. Implement feature with tests
3. Run all tests and linting
4. Create PR with description
5. Code review (minimum 2 approvals)
6. Merge to `develop`

### Development Cycle

#### 1. Planning Phase
- Create GitHub issues for features
- Define acceptance criteria
- Estimate effort (story points)
- Create technical design document

#### 2. Implementation Phase
- Follow TDD approach
- Write tests first
- Implement minimal viable code
- Refactor for quality

#### 3. Testing Phase
- Unit tests (>95% coverage)
- Integration tests
- Performance tests
- Security tests

#### 4. Review Phase
- Code review checklist
- Security review
- Performance review
- Documentation review

#### 5. Deployment Phase
- Deploy to staging
- Run smoke tests
- Deploy to production
- Monitor metrics

---

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/               # Unit tests
│   ├── test_knowledge_sage.py
│   ├── test_event_bus.py
│   └── test_data_models.py
├── integration/        # Integration tests
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_full_system.py
├── performance/        # Performance tests
│   ├── test_load_testing.py
│   └── test_benchmarks.py
├── security/          # Security tests
│   ├── test_authentication.py
│   └── test_authorization.py
└── fixtures/          # Test fixtures
    ├── sample_data.json
    └── test_config.py
```

### Testing Principles

#### 1. Test Pyramid
```
     /\
    /  \    E2E Tests (10%)
   /____\
  /      \  Integration Tests (20%)
 /________\
/__________\ Unit Tests (70%)
```

#### 2. Test Naming
```python
def test_knowledge_entity_creation_with_valid_data():
    """Test: knowledge entity creation with valid data."""

def test_knowledge_entity_creation_raises_validation_error_for_empty_title():
    """Test: knowledge entity creation raises ValidationError for empty title."""
```

#### 3. Test Structure (AAA Pattern)
```python
@pytest.mark.asyncio
async def test_event_bus_publishes_event_successfully():
    """Test: event bus publishes event successfully."""
    # Arrange
    event_bus = ElderGuildEventBus(mock_db_manager, mock_redis)
    test_event = Event(
        type=EventType.SAGE_KNOWLEDGE_CREATED,
        source="test",
        data={"title": "Test Knowledge"}
    )

    # Act
    await event_bus.publish(test_event)

    # Assert
    assert event_bus.event_queue.qsize() == 1
    published_event = await event_bus.event_queue.get()
    assert published_event.type == EventType.SAGE_KNOWLEDGE_CREATED
```

### Test Categories

#### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution (<1ms per test)
- High coverage (>95%)

#### Integration Tests
- Test component interactions
- Use real databases (test containers)
- Slower execution (<1s per test)
- Focus on critical paths

#### Performance Tests
- Load testing
- Stress testing
- Benchmark comparisons
- Memory usage validation

#### Security Tests
- Authentication testing
- Authorization testing
- Input validation
- SQL injection prevention

---

## 🚀 Deployment Process

### Environment Strategy
```
Development → Staging → Production
     ↓           ↓         ↓
  Local Dev   QA Tests   Live
```

### Deployment Pipeline

#### 1. Automated Testing
```yaml
# GitHub Actions workflow
- Unit Tests (all Python versions)
- Integration Tests (PostgreSQL + Redis)
- Security Scans (Bandit, Safety)
- Performance Tests (benchmarks)
- Docker Build & Security Scan
```

#### 2. Deployment Script
```bash
# Development deployment
./scripts/deploy.sh deploy development

# Production deployment
./scripts/deploy.sh deploy production

# Rollback
./scripts/deploy.sh rollback
```

#### 3. Blue-Green Deployment
```
Blue Environment (Current)    Green Environment (New)
        ↓                            ↓
Load Balancer Switch (Instant)
        ↓
Green Environment (Current)
```

### Configuration Management

#### Environment Variables
```bash
# Core settings
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/db
ENV=production

# Security
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
OPENAI_API_KEY=your-openai-key

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
LOG_LEVEL=INFO
```

#### Docker Configuration
```dockerfile
# Multi-stage build
FROM python:3.11-slim as base
FROM base as development
FROM base as production
```

---

## 📊 Monitoring and Debugging

### Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Loki**: Log aggregation
- **Jaeger**: Distributed tracing

### Key Metrics

#### Application Metrics
```python
# Custom metrics
from prometheus_client import Counter, Histogram, Gauge

# Counters
events_published = Counter('events_published_total', 'Total events published')
events_processed = Counter('events_processed_total', 'Total events processed')

# Histograms
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Gauges
active_connections = Gauge('active_connections', 'Active database connections')

# Usage
events_published.inc()
request_duration.observe(response_time)
active_connections.set(connection_count)
```

#### System Metrics
- CPU usage
- Memory usage
- Disk I/O
- Network I/O
- Database connections
- Redis memory usage

### Logging Standards

#### Log Levels
```python
import logging

logger = logging.getLogger(__name__)

# ERROR: System errors, exceptions
logger.error("Failed to process event %s: %s", event_id, error)

# WARNING: Unexpected situations
logger.warning("Queue size approaching limit: %d", queue_size)

# INFO: Important business events
logger.info("Knowledge entity created: %s", entity_id)

# DEBUG: Detailed debugging information
logger.debug("Processing event: %s", event_data)
```

#### Log Format
```python
# Structured logging
{
    "timestamp": "2025-07-11T10:30:45.123Z",
    "level": "INFO",
    "logger": "elders_guild.knowledge_sage",
    "message": "Knowledge entity created successfully",
    "event_id": "evt_123456",
    "entity_id": "know_789012",
    "user_id": "user_345678",
    "request_id": "req_901234",
    "duration_ms": 45.67
}
```

### Debugging Tools

#### Local Development
```bash
# Debug mode
export DEBUG=true
python -m uvicorn libs.elders_guild_api_spec:app --reload --log-level debug

# Database debugging
export SQLALCHEMY_ECHO=true

# Redis debugging
redis-cli monitor
```

#### Production Debugging
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f api-server
docker-compose logs -f event-worker

# Database queries
docker-compose exec postgres psql -U elder_admin -d elders_guild

# Redis status
docker-compose exec redis redis-cli info
```

---

## 🔒 Security Guidelines

### Authentication & Authorization

#### JWT Implementation
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

#### Role-Based Access Control
```python
class Permission(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SAGE_KNOWLEDGE = "sage.knowledge"
    SAGE_TASK = "sage.task"
    SAGE_INCIDENT = "sage.incident"
    SAGE_RAG = "sage.rag"

def require_permission(permission: Permission):
    """Decorator for permission checking."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user.has_permission(permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Input Validation

#### Pydantic Models
```python
class KnowledgeCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    category_id: Optional[str] = Field(None, regex=r'^[a-zA-Z0-9_-]+$')
    tags: List[str] = Field(default_factory=list, max_items=10)

    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
```

#### SQL Injection Prevention
```python
# Good: Parameterized queries
async def get_knowledge_by_id(knowledge_id: str) -> Optional[KnowledgeEntity]:
    async with get_connection() as conn:
        result = await conn.fetchrow(
            "SELECT * FROM knowledge_entities WHERE id = $1",
            knowledge_id
        )
        return result

# Bad: String concatenation
# Never do this!
# query = f"SELECT * FROM knowledge_entities WHERE id = '{knowledge_id}'"
```

### Data Protection

#### Encryption
```python
from cryptography.fernet import Fernet

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data."""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    return encrypted_data.decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data.encode())
    return decrypted_data.decode()
```

#### Secrets Management
```python
import os
from typing import Optional

class Settings:
    """Application settings."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    def __init__(self):
        # Validate required secrets
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required")
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
```

---

## ⚡ Performance Optimization

### Database Optimization

#### Query Optimization
```python
# Good: Use indexes
CREATE INDEX idx_knowledge_title ON knowledge_entities(title);
CREATE INDEX idx_knowledge_category ON knowledge_entities(category_id);
CREATE INDEX idx_knowledge_created_at ON knowledge_entities(created_at);

# Good: Efficient queries
async def get_knowledge_by_category(category_id: str, limit: int = 10):
    query = """
        SELECT id, title, summary, created_at
        FROM knowledge_entities
        WHERE category_id = $1
        ORDER BY created_at DESC
        LIMIT $2
    """
    return await conn.fetch(query, category_id, limit)

# Bad: N+1 queries
# for entity in entities:
#     category = await get_category_by_id(entity.category_id)
```

#### Connection Pooling
```python
# PostgreSQL connection pool
class DatabaseManager:
    def __init__(self, database_url: str):
        self.pool = None
        self.database_url = database_url

    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )

    async def get_connection(self):
        return self.pool.acquire()
```

### Caching Strategy

#### Redis Caching
```python
import redis.asyncio as redis
from typing import Optional
import json

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[dict]:
        """Get cached value."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: dict, ttl: int = 3600):
        """Set cached value with TTL."""
        await self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str):
        """Delete cached value."""
        await self.redis.delete(key)

# Usage
cache = CacheManager(redis_url)

async def get_knowledge_with_cache(knowledge_id: str):
    # Try cache first
    cached = await cache.get(f"knowledge:{knowledge_id}")
    if cached:
        return cached

    # Query database
    knowledge = await get_knowledge_from_db(knowledge_id)

    # Cache result
    await cache.set(f"knowledge:{knowledge_id}", knowledge.to_dict())

    return knowledge
```

### Async Programming

#### Concurrent Processing
```python
import asyncio
from typing import List

async def process_knowledge_batch(knowledge_ids: List[str]):
    """Process multiple knowledge entities concurrently."""

    # Create tasks
    tasks = [
        process_knowledge_entity(knowledge_id)
        for knowledge_id in knowledge_ids
    ]

    # Execute concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle results
    successful_results = []
    errors = []

    for result in results:
        if isinstance(result, Exception):
            errors.append(result)
        else:
            successful_results.append(result)

    return successful_results, errors
```

### Memory Management

#### Large Data Processing
```python
async def process_large_dataset(dataset_size: int):
    """Process large dataset in chunks."""

    chunk_size = 1000
    total_processed = 0

    for offset in range(0, dataset_size, chunk_size):
        # Process chunk
        chunk = await get_data_chunk(offset, chunk_size)
        await process_chunk(chunk)

        total_processed += len(chunk)

        # Optional: Force garbage collection
        if total_processed % 10000 == 0:
            import gc
            gc.collect()

        # Progress logging
        logger.info(f"Processed {total_processed}/{dataset_size} records")
```

---

## 🛠️ Troubleshooting

### Common Issues

#### Database Connection Issues
```python
# Problem: Connection pool exhausted
# Solution: Proper connection management
async def safe_database_operation():
    async with database_manager.get_connection() as conn:
        # Use connection
        result = await conn.fetchrow("SELECT 1")
        # Connection automatically returned to pool
        return result
```

#### Memory Leaks
```python
# Problem: Event handlers not cleaned up
# Solution: Proper cleanup
class EventProcessor:
    def __init__(self):
        self.handlers = []

    def register_handler(self, handler):
        self.handlers.append(handler)

    async def cleanup(self):
        # Clean up handlers
        for handler in self.handlers:
            if hasattr(handler, 'cleanup'):
                await handler.cleanup()
        self.handlers.clear()
```

#### Performance Issues
```python
# Problem: Blocking operations
# Solution: Use async/await
async def fetch_external_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Problem: Inefficient queries
# Solution: Use proper indexing and query optimization
```

### Debugging Checklist

#### Before Deployment
- [ ] All tests pass
- [ ] No security vulnerabilities
- [ ] Performance tests pass
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] Monitoring dashboards configured

#### Post-Deployment
- [ ] Health checks passing
- [ ] Metrics being collected
- [ ] Logs being generated
- [ ] Error rates within acceptable limits
- [ ] Response times within SLA

### Emergency Procedures

#### Rollback Process
```bash
# Quick rollback
./scripts/deploy.sh rollback

# Manual rollback
docker-compose down
docker-compose up -d --scale api-server=0
# Fix issues
docker-compose up -d
```

#### Incident Response
1. **Acknowledge**: Confirm the incident
2. **Assess**: Determine severity and impact
3. **Respond**: Implement immediate fixes
4. **Communicate**: Update stakeholders
5. **Follow-up**: Post-incident review

---

## 📚 Additional Resources

### Documentation
- [API Documentation](./API_DOCUMENTATION.md)
- [Database Schema](./DATABASE_SCHEMA.md)
- [Event System Guide](./EVENT_SYSTEM.md)
- [Security Best Practices](./SECURITY_GUIDE.md)

### Tools
- [Development Tools](./DEVELOPMENT_TOOLS.md)
- [Testing Framework](./TESTING_FRAMEWORK.md)
- [Monitoring Setup](./MONITORING_SETUP.md)

### Community
- [GitHub Issues](https://github.com/your-org/elders-guild/issues)
- [Discussion Forum](https://github.com/your-org/elders-guild/discussions)
- [Wiki](https://github.com/your-org/elders-guild/wiki)

---

## 📝 Changelog

### Version 1.0.0 (2025-01-11)
- Initial development guide
- Architecture documentation
- Coding standards
- Testing guidelines
- Deployment procedures

---

**Happy Coding! 🚀**

*Remember: Write code that your future self will thank you for.*
