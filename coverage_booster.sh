#!/bin/bash
#
# Elder Council Coverage Booster Script
# テストカバレッジ向上のための緊急ブースタースクリプト
#

echo "🔮 Elder Council Coverage Booster v1.0"
echo "====================================="
echo

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Python実行コマンドの確認
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo -e "${RED}Error: Python3 not found!${NC}"
    exit 1
fi

# 作業ディレクトリの確認
cd /home/aicompany/ai_co

# 1. テスト環境の健全性チェック
echo -e "${BLUE}1. Testing Environment Health Check${NC}"
echo "----------------------------------------"

# pytest存在確認
if $PYTHON_CMD -m pytest --version &> /dev/null; then
    echo -e "${GREEN}✓ pytest is available${NC}"
else
    echo -e "${RED}✗ pytest not found, installing...${NC}"
    pip3 install pytest pytest-cov
fi

# 2. 既知の良質なテストを実行
echo
echo -e "${BLUE}2. Running High-Quality Tests${NC}"
echo "----------------------------------------"

GOOD_TESTS=(
    "tests/unit/test_performance_optimizer.py"
    "tests/unit/test_hypothesis_generator.py"
    "tests/unit/test_ab_testing_framework.py"
    "tests/unit/test_auto_adaptation_engine.py"
    "tests/unit/test_feedback_loop_system.py"
    "tests/unit/test_knowledge_evolution.py"
    "tests/unit/test_meta_learning_system.py"
    "tests/unit/test_cross_worker_learning.py"
    "tests/unit/test_predictive_evolution.py"
    "tests/unit/test_automated_code_review.py"
    "tests/unit/test_async_worker_optimization.py"
    "tests/unit/test_integration_test_framework.py"
    "tests/unit/test_advanced_monitoring_dashboard.py"
    "tests/unit/test_security_audit_system.py"
)

# 良質なテストを実行
echo "Running ${#GOOD_TESTS[@]} high-quality test files..."
$PYTHON_CMD -m pytest "${GOOD_TESTS[@]}" \
    --cov=libs \
    --cov=core \
    --cov=workers \
    --cov-report=term-missing \
    --cov-report=html \
    -v

# 結果を保存
COVERAGE_RESULT=$?

# 3. 実行可能なテストの収集
echo
echo -e "${BLUE}3. Collecting All Runnable Tests${NC}"
echo "----------------------------------------"

# テストを収集（エラーを除外）
$PYTHON_CMD -m pytest --collect-only -q 2>&1 | \
    grep -E "\.py::" | \
    grep -v "ERROR" | \
    cut -d':' -f1 | \
    sort | uniq > runnable_tests.txt

RUNNABLE_COUNT=$(wc -l < runnable_tests.txt)
echo -e "${GREEN}Found $RUNNABLE_COUNT runnable test files${NC}"

# 4. カバレッジレポートの生成
echo
echo -e "${BLUE}4. Generating Coverage Reports${NC}"
echo "----------------------------------------"

# HTMLレポート生成
if [ -d "htmlcov" ]; then
    echo -e "${GREEN}✓ HTML coverage report generated in htmlcov/${NC}"
    echo "  View with: python3 -m http.server 8080 --directory htmlcov"
fi

# テキストレポート
echo
echo -e "${YELLOW}Coverage Summary:${NC}"
$PYTHON_CMD -m coverage report | tail -20

# 5. 問題のあるテストファイルの特定
echo
echo -e "${BLUE}5. Identifying Problematic Tests${NC}"
echo "----------------------------------------"

# コレクションエラーのあるファイルを特定
$PYTHON_CMD -m pytest --collect-only -q 2>&1 | \
    grep -B1 "ERROR" | \
    grep -E "\.py$" | \
    sort | uniq > problematic_tests.txt

if [ -s problematic_tests.txt ]; then
    PROBLEM_COUNT=$(wc -l < problematic_tests.txt)
    echo -e "${RED}Found $PROBLEM_COUNT problematic test files:${NC}"
    head -10 problematic_tests.txt
else
    echo -e "${GREEN}✓ No problematic test files found${NC}"
fi

# 6. 次のステップの提案
echo
echo -e "${BLUE}6. Next Steps for Coverage Improvement${NC}"
echo "========================================"

# 現在のカバレッジを取得
CURRENT_COVERAGE=$($PYTHON_CMD -m coverage report | tail -1 | awk '{print $NF}')

echo -e "Current Coverage: ${YELLOW}${CURRENT_COVERAGE}${NC}"
echo
echo -e "${GREEN}Recommended Actions:${NC}"
echo "1. Fix import errors in problematic test files"
echo "2. Complete skeleton tests in tests/unit/test_coverage_knights_*.py"
echo "3. Add tests for uncovered modules:"

# カバレッジが低いモジュールを表示
echo
$PYTHON_CMD -m coverage report --skip-covered | \
    grep -E "\.py\s+[0-9]+\s+[0-9]+\s+[0-5][0-9]?%" | \
    head -10

echo
echo -e "${YELLOW}To improve coverage immediately:${NC}"
echo "1. Run: ./fix_test_base.py"
echo "2. Run: ./auto_fix_imports.py"
echo "3. Run: ai-dwarf-workshop mass-produce-tests --priority=core"
echo
echo "====================================="
echo -e "${GREEN}✨ Coverage Booster Complete!${NC}"

exit $COVERAGE_RESULT