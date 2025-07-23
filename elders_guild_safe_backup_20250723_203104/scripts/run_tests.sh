#!/bin/bash
# Elder Tree v2 テスト実行スクリプト
# エルダーズギルドの品質基準に準拠

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Elder Tree v2 Test Suite${NC}"
echo "=================================="

# プロジェクトルートに移動
cd /home/aicompany/ai_co/elder_tree_v2

# 仮想環境をアクティベート（存在する場合）
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# テストオプション
COVERAGE_THRESHOLD=95
PARALLEL_WORKERS=4

# 引数処理
TEST_TYPE="${1:-all}"
VERBOSE="${2:-}"

# ヘルプ表示
if [ "$TEST_TYPE" = "help" ] || [ "$TEST_TYPE" = "--help" ]; then
    echo "Usage: $0 [test_type] [options]"
    echo ""
    echo "Test types:"
    echo "  all        - Run all tests (default)"
    echo "  unit       - Run unit tests only"
    echo "  integration - Run integration tests only"
    echo "  coverage   - Run with coverage report"
    echo "  benchmark  - Run performance benchmarks"
    echo "  quality    - Run quality checks"
    echo "  watch      - Run tests in watch mode"
    echo ""
    echo "Options:"
    echo "  -v, --verbose - Verbose output"
    echo ""
    exit 0
fi

# Poetry環境チェック
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Poetry not found. Installing test dependencies with pip...${NC}"
    pip install -r requirements-dev.txt 2>/dev/null || true
else
    echo -e "${GREEN}Installing/updating test dependencies...${NC}"
    poetry install --with dev
fi

# テスト実行関数
run_unit_tests() {
    echo -e "\n${YELLOW}Running Unit Tests...${NC}"
    pytest tests/unit \
        -v \
        -n $PARALLEL_WORKERS \
        --tb=short \
        --maxfail=5 \
        ${VERBOSE:+-vv}
}

run_integration_tests() {
    echo -e "\n${YELLOW}Running Integration Tests...${NC}"
    pytest tests/integration \
        -v \
        --tb=short \
        --maxfail=3 \
        ${VERBOSE:+-vv}
}

run_coverage_tests() {
    echo -e "\n${YELLOW}Running Tests with Coverage...${NC}"
    pytest tests \
        --cov=elder_tree \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        -v \
        ${VERBOSE:+-vv}
    
    echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
}

run_benchmark_tests() {
    echo -e "\n${YELLOW}Running Performance Benchmarks...${NC}"
    pytest tests \
        -v \
        --benchmark-only \
        --benchmark-autosave \
        --benchmark-compare \
        ${VERBOSE:+--benchmark-verbose}
}

run_quality_checks() {
    echo -e "\n${YELLOW}Running Quality Checks...${NC}"
    
    # Ruff (linting)
    echo -e "\n${BLUE}Checking with Ruff...${NC}"
    ruff check src/ tests/ || true
    
    # Black (formatting)
    echo -e "\n${BLUE}Checking code formatting...${NC}"
    black --check src/ tests/ || true
    
    # isort (import sorting)
    echo -e "\n${BLUE}Checking import order...${NC}"
    isort --check-only src/ tests/ || true
    
    # MyPy (type checking)
    echo -e "\n${BLUE}Checking types...${NC}"
    mypy src/ || true
    
    # エルダーズギルド品質チェック
    if [ -f "/home/aicompany/ai_co/libs/elders_code_quality.py" ]; then
        echo -e "\n${BLUE}Running Elders Guild Quality Check...${NC}"
        python3 -c "
import sys
sys.path.insert(0, '/home/aicompany/ai_co')
from libs.elders_code_quality import CodeQualityAnalyzer
analyzer = CodeQualityAnalyzer()
result = analyzer.analyze_directory('src/')
print(f'Overall Quality Score: {result.get(\"average_score\", 0):.1f}/100')
print(f'Iron Will Compliance: {\"PASS\" if result.get(\"iron_will_compliant\", False) else \"FAIL\"}')
"
    fi
}

run_watch_mode() {
    echo -e "\n${YELLOW}Running Tests in Watch Mode...${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop${NC}"
    
    # pytest-watchがインストールされているか確認
    if ! pip show pytest-watch > /dev/null 2>&1; then
        echo -e "${YELLOW}Installing pytest-watch...${NC}"
        pip install pytest-watch
    fi
    
    ptw tests --runner "pytest -v --tb=short"
}

# テスト前の準備
prepare_test_environment() {
    echo -e "${GREEN}Preparing test environment...${NC}"
    
    # テスト用ディレクトリ作成
    mkdir -p tests/reports
    mkdir -p tests/coverage
    
    # 環境変数設定
    export ENVIRONMENT=test
    export LOG_LEVEL=WARNING
    export ELDER_TREE_TEST_MODE=1
}

# メイン実行
prepare_test_environment

case $TEST_TYPE in
    "all")
        run_unit_tests
        run_integration_tests
        run_coverage_tests
        ;;
    "unit")
        run_unit_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "coverage")
        run_coverage_tests
        ;;
    "benchmark")
        run_benchmark_tests
        ;;
    "quality")
        run_quality_checks
        ;;
    "watch")
        run_watch_mode
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

# 結果サマリー
echo -e "\n${GREEN}Test execution completed!${NC}"
echo "=================================="

# カバレッジサマリー表示（coverage実行時）
if [ "$TEST_TYPE" = "coverage" ] || [ "$TEST_TYPE" = "all" ]; then
    echo -e "\n${YELLOW}Coverage Summary:${NC}"
    coverage report --skip-covered --skip-empty | tail -n 5
fi

# 終了メッセージ
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
else
    echo -e "\n${RED}❌ Some tests failed!${NC}"
    exit 1
fi