#!/bin/bash
# テスト実行エントリーポイント

set -e

echo "🧪 Elders Guild Image Upload Manager - Test Environment"
echo "======================================================="

# テスト環境の初期化
echo "📋 Initializing test environment..."

# テスト用ディレクトリのクリーンアップと作成
rm -rf /app/test_uploads/* /app/test_data/* 2>/dev/null || true
mkdir -p /app/test_uploads /app/test_data /app/test_config

# テスト用データベースの初期化
echo "🗄️ Setting up test database..."
export DATABASE_URL="sqlite:///test_data/test.db"

# 引数に応じてテスト実行
case "${1:-all}" in
    "all")
        echo "🚀 Running all tests..."
        python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing --cov-report=html:test_coverage
        ;;
    "unit")
        echo "🔧 Running unit tests only..."
        python -m pytest tests/unit/ -v --tb=short --cov=app --cov-report=term-missing
        ;;
    "integration")
        echo "🔗 Running integration tests only..."
        python -m pytest tests/integration/ -v --tb=short
        ;;
    "coverage")
        echo "📊 Running coverage analysis..."
        python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html:test_coverage --cov-fail-under=80
        ;;
    "quick")
        echo "⚡ Running quick tests (no coverage)..."
        python -m pytest tests/ -v --tb=short -x
        ;;
    "debug")
        echo "🐛 Running tests in debug mode..."
        python -m pytest tests/ -v --tb=long --pdb-trace
        ;;
    "specific")
        echo "🎯 Running specific test: $2"
        python -m pytest "$2" -v --tb=short
        ;;
    "lint")
        echo "🔍 Running code quality checks..."
        echo "  - Black formatting check..."
        black --check app/ tests/
        echo "  - isort import sorting check..."
        isort --check-only app/ tests/
        echo "  - Flake8 linting..."
        flake8 app/ tests/
        echo "✅ Code quality checks passed!"
        ;;
    "format")
        echo "🎨 Formatting code..."
        black app/ tests/
        isort app/ tests/
        echo "✅ Code formatted!"
        ;;
    "interactive")
        echo "🖥️ Starting interactive shell..."
        /bin/bash
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        echo "Available commands:"
        echo "  all         - Run all tests with coverage"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests only"
        echo "  coverage    - Run coverage analysis"
        echo "  quick       - Quick test run without coverage"
        echo "  debug       - Debug mode with pdb"
        echo "  specific    - Run specific test file"
        echo "  lint        - Code quality checks"
        echo "  format      - Format code"
        echo "  interactive - Interactive shell"
        echo ""
        echo "Examples:"
        echo "  docker run test-image all"
        echo "  docker run test-image specific tests/unit/test_models.py"
        echo "  docker run test-image lint"
        exit 1
        ;;
esac

echo ""
echo "✅ Test execution completed!"