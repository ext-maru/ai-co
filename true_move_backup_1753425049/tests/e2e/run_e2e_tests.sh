#!/bin/bash
# E2E Test Runner for AI Company
# 実際のシステムを起動してエンドツーエンドテストを実行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "🧪 AI Company E2E Test Suite"
echo "============================"
echo ""

# カラー定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# テスト結果
TESTS_PASSED=0
TESTS_FAILED=0

# ログ関数
log_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

# 1. 環境準備
log_test "Setting up test environment..."

# 仮想環境をアクティベート
source venv/bin/activate || {
    log_fail "Failed to activate virtual environment"
    exit 1
}

# RabbitMQの状態確認
if sudo rabbitmqctl status > /dev/null 2>&1; then
    log_success "RabbitMQ is running"
else
    log_fail "RabbitMQ is not running"
    exit 1
fi

# 既存のAI Companyプロセスを停止
log_test "Stopping existing AI Company processes..."
"$PROJECT_ROOT/scripts/ai-stop" > /dev/null 2>&1 || true

# キューをクリア
log_test "Clearing message queues..."
sudo rabbitmqctl purge_queue ai_tasks > /dev/null 2>&1 || true
sudo rabbitmqctl purge_queue ai_pm > /dev/null 2>&1 || true
sudo rabbitmqctl purge_queue ai_results > /dev/null 2>&1 || true
sudo rabbitmqctl purge_queue ai_dialog > /dev/null 2>&1 || true
log_success "Queues cleared"

# 2. システム起動
log_test "Starting AI Company system..."
"$PROJECT_ROOT/scripts/ai-start" > /dev/null 2>&1

# 起動待機
sleep 5

# システム状態確認
if "$PROJECT_ROOT/scripts/ai-status" | grep -q "All workers are running"; then
    log_success "AI Company system started successfully"
else
    log_fail "AI Company system failed to start properly"
    exit 1
fi

# 3. E2Eテストケース実行
log_test "Running E2E test cases..."

# Test 1: シンプルなコード生成タスク
log_test "Test 1: Simple code generation"
TASK_ID=$(date +%s)
TEST_OUTPUT=$(cd "$PROJECT_ROOT" && python3 -c "
import sys
sys.path.insert(0, '.')
from tests.e2e.test_simple_task import run_test
result = run_test('e2e_test_${TASK_ID}')
print('SUCCESS' if result else 'FAILED')
")

if [[ "$TEST_OUTPUT" == *"SUCCESS"* ]]; then
    log_success "Simple code generation test passed"
else
    log_fail "Simple code generation test failed"
fi

# Test 2: 対話型タスク
log_test "Test 2: Dialog task flow"
DIALOG_ID=$(date +%s)
TEST_OUTPUT=$(cd "$PROJECT_ROOT" && python3 -c "
import sys
sys.path.insert(0, '.')
from tests.e2e.test_dialog_flow import run_test
result = run_test('e2e_dialog_${DIALOG_ID}')
print('SUCCESS' if result else 'FAILED')
")

if [[ "$TEST_OUTPUT" == *"SUCCESS"* ]]; then
    log_success "Dialog task flow test passed"
else
    log_fail "Dialog task flow test failed"
fi

# Test 3: ファイル配置確認
log_test "Test 3: File placement verification"
FILE_TEST_ID=$(date +%s)
TEST_OUTPUT=$(cd "$PROJECT_ROOT" && python3 -c "
import sys
sys.path.insert(0, '.')
from tests.e2e.test_file_placement import run_test
result = run_test('e2e_file_${FILE_TEST_ID}')
print('SUCCESS' if result else 'FAILED')
")

if [[ "$TEST_OUTPUT" == *"SUCCESS"* ]]; then
    log_success "File placement test passed"
else
    log_fail "File placement test failed"
fi

# Test 4: エラーハンドリング
log_test "Test 4: Error handling"
ERROR_TEST_ID=$(date +%s)
TEST_OUTPUT=$(cd "$PROJECT_ROOT" && python3 -c "
import sys
sys.path.insert(0, '.')
from tests.e2e.test_error_handling import run_test
result = run_test('e2e_error_${ERROR_TEST_ID}')
print('SUCCESS' if result else 'FAILED')
")

if [[ "$TEST_OUTPUT" == *"SUCCESS"* ]]; then
    log_success "Error handling test passed"
else
    log_fail "Error handling test failed"
fi

# Test 5: 並行処理
log_test "Test 5: Concurrent task processing"
python3 "$PROJECT_ROOT/tests/e2e/test_concurrent_tasks.py"
if [ $? -eq 0 ]; then
    log_success "Concurrent task processing test passed"
else
    log_fail "Concurrent task processing test failed"
fi

# 4. クリーンアップ
log_test "Cleaning up..."

# システム停止
"$PROJECT_ROOT/scripts/ai-stop" > /dev/null 2>&1

# テスト用ファイルの削除
find "$PROJECT_ROOT/output" -name "e2e_test_*" -type f -delete 2>/dev/null || true
find "$PROJECT_ROOT/workers" -name "e2e_test_*" -type f -delete 2>/dev/null || true

log_success "Cleanup completed"

# 5. 結果サマリー
echo ""
echo "=================================="
echo "E2E Test Results Summary"
echo "=================================="
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All E2E tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some E2E tests failed${NC}"
    exit 1
fi
