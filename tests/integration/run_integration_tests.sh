#!/bin/bash
# Elder Flow統合テスト実行スクリプト

set -euo pipefail

# カラー定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# プロジェクトルート
PROJECT_ROOT="/home/aicompany/ai_co"
cd "$PROJECT_ROOT"

# テスト結果ディレクトリ作成
RESULTS_DIR="$PROJECT_ROOT/reports/integration/test_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

log_info "Elder Flow統合テスト実行開始"
log_info "結果ディレクトリ: $RESULTS_DIR"

# Pythonパス設定
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 統合テスト実行
log_info "統合テストを実行中..."

# pytestの実行
pytest_cmd="python3 -m pytest tests/integration/ -v --tb=short --junit-xml=$RESULTS_DIR/junit.xml --html=$RESULTS_DIR/report.html --self-contained-html"

if $pytest_cmd 2>&1 | tee "$RESULTS_DIR/test_output.log"; then
    log_info "統合テスト成功"
    test_status="SUCCESS"
else
    log_error "統合テスト失敗"
    test_status="FAILED"
fi

# テスト結果サマリー作成
cat > "$RESULTS_DIR/summary.json" << EOF
{
  "test_run": {
    "date": "$(date -Iseconds)",
    "status": "$test_status",
    "results_directory": "$RESULTS_DIR",
    "command": "$pytest_cmd"
  },
  "environment": {
    "python_version": "$(python3 --version 2>&1)",
    "project_root": "$PROJECT_ROOT",
    "user": "$(whoami)"
  }
}
EOF

# 結果表示
echo ""
echo "================================"
echo "統合テスト実行完了"
echo "================================"
echo "ステータス: $test_status"
echo "結果ディレクトリ: $RESULTS_DIR"
echo "詳細レポート: $RESULTS_DIR/report.html"
echo "================================"

# 終了コード
if [ "$test_status" = "SUCCESS" ]; then
    exit 0
else
    exit 1
fi