# 🌳 Elder Tree v2.0 - OSS First + TDD/XP

**Real python-a2a (0.5.9) Implementation**

## 🚀 Quick Start

```bash
# Install dependencies
poetry install

# Run TDD cycle
./scripts/run_tdd_cycle.sh

# Watch tests (continuous)
./scripts/watch_tests.sh

# Start API Gateway
poetry run uvicorn elder_tree.api.main:app --reload
```

## 🧪 TDD Development Flow

1. **Red Phase**: Write failing tests
   ```bash
   poetry run pytest tests/acceptance -v  # Acceptance tests fail
   poetry run pytest tests/unit -v        # Unit tests fail
   ```

2. **Green Phase**: Write minimal code to pass
   ```bash
   # Implement in src/elder_tree/
   poetry run pytest tests/ -v  # All tests pass
   ```

3. **Refactor Phase**: Improve code quality
   ```bash
   poetry run black .
   poetry run ruff .
   poetry run mypy src/
   ```

## 📦 Technology Stack (OSS First)

- **Core**: python-a2a (0.5.9) - Real Agent-to-Agent protocol
- **API**: FastAPI + Uvicorn
- **Database**: PostgreSQL + Redis
- **AI/LLM**: Anthropic + OpenAI + LangChain
- **Monitoring**: Prometheus + Grafana
- **Testing**: pytest + pytest-asyncio + pytest-cov

## 📊 Project Structure

```
elder_tree_v2/
├── tests/              # TDD First!
│   ├── acceptance/     # User story tests
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── src/elder_tree/    # Implementation
│   ├── agents/        # python-a2a agents
│   ├── workflows/     # Elder Flow
│   └── api/          # FastAPI Gateway
└── scripts/          # TDD helpers
```

## 🎯 Coverage Goals

- Acceptance Tests: 100% user stories covered
- Unit Tests: 95%+ code coverage
- Integration Tests: All agent interactions

## 📈 Metrics

- API: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Health: http://localhost:8000/health

## 🏛️ Development Principles

1. **OSS First**: Don't reinvent the wheel
2. **TDD/XP**: Red → Green → Refactor
3. **python-a2a**: Real OSS library (not custom)
4. **Iron Will**: 100% quality standards

**Remember: Test First, OSS Always!**
