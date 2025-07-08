# 🚀 AI Company - Ultimate AI-Powered Development Infrastructure

[![Test Suite](https://github.com/YOUR_USERNAME/ai-company/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/ai-company/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](htmlcov/index.html)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 🎯 Overview

AI Company is a revolutionary development infrastructure that transforms ideas into working code through AI automation. Simply describe what you want, and AI Company will generate, test, deploy, and evolve the code automatically.

**"Humans think, AI executes"** - This is the core philosophy of AI Company.

## ✨ Key Features

- **🤖 AI-Powered Code Generation**: Uses Claude AI to generate production-ready code
- **🧬 Self-Evolution System**: Automatically places and organizes generated files
- **🧪 Comprehensive Test System**: AI-driven test generation with GitHub Actions CI/CD
- **🔄 Git Flow Integration**: Automated version control and deployment
- **📱 Real-time Notifications**: Slack integration for task completion updates
- **🧠 RAG System**: Learns from past tasks to improve future generations
- **💬 Interactive Dialogue**: Complex tasks through conversational interface

## 🚀 Quick Start

### Prerequisites

- Ubuntu 24.04 LTS (WSL2 supported)
- Python 3.12+
- RabbitMQ
- Claude CLI

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/ai-company.git
cd ai-company

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start system
ai-start
```

### Basic Usage

```bash
# Generate code
ai-send "Create a REST API for user management" code

# Interactive dialogue for complex tasks
ai-dialog "Design a scalable e-commerce platform"

# Check status
ai-status

# Run tests
ai-test
```

## 🧪 Test System

AI Company includes a comprehensive test system with AI-driven test generation:

### Features

- **3-Tier Testing**: Unit, Integration, and E2E tests
- **AI Test Generation**: Automatically creates tests for uncovered code
- **GitHub Actions CI/CD**: Automated testing on every push
- **Coverage Tracking**: 80% overall, 85% workers, 90% libs targets
- **Slack Notifications**: Test results and coverage alerts

### Commands

```bash
# Run all tests
ai-test

# Check coverage
ai-test coverage --html

# Generate tests with AI
ai-test generate

# Run specific test type
ai-test unit
ai-test integration
ai-test e2e
```

### CI/CD Pipeline

The GitHub Actions workflow includes:
- Code quality checks (lint, format, type checking)
- Security scanning
- Parallel test execution
- Automatic test generation for low coverage
- Deployment to production on main branch

## 🏗️ Architecture

```
ai_co/
├── core/           # Base classes and utilities
├── workers/        # AI task processors
├── libs/           # Managers and utilities
├── scripts/        # Command-line tools
├── tests/          # Test suites
├── .github/        # GitHub Actions workflows
└── config/         # Configuration files
```

### Core Components

- **TaskWorker**: Main AI task processor
- **TestGeneratorWorker**: AI-driven test generation
- **PMWorker**: Project management and file deployment
- **DialogTaskWorker**: Interactive conversation handler
- **RAGManager**: Context-aware task enhancement
- **TestManager**: Test execution and reporting

## 📊 Monitoring & Management

```bash
# System status
ai-status

# View logs
ai-logs --follow

# Worker management
ai-workers
ai-worker-restart all

# Queue monitoring
ai-queue
```

## 🔧 Configuration

Main configuration files:
- `config/worker.json` - Worker settings
- `config/slack.conf` - Slack notifications
- `config/test.conf` - Test system configuration
- `pytest.ini` - pytest configuration

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure tests pass (`ai-test`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## 📈 Roadmap

- [ ] Kubernetes deployment support
- [ ] Multi-model AI support (GPT-4, Gemini)
- [ ] Web UI dashboard
- [ ] Plugin marketplace
- [ ] Distributed processing

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Claude AI by Anthropic for powering code generation
- RabbitMQ for reliable message queuing
- pytest for comprehensive testing framework

---

**🎊 AI Company - Where ideas become reality through AI automation**

For more information, check out our [comprehensive documentation](docs/README.md).
