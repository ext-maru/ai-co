#!/bin/bash
# AI Company TDD環境セットアップスクリプト

set -e

echo "🚀 AI Company TDD環境セットアップを開始します..."

# プロジェクトルートに移動
cd /home/aicompany/ai_co

# 仮想環境をアクティベート
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ 仮想環境が見つかりません。先に仮想環境を作成してください。"
    exit 1
fi

# テスト依存関係のインストール
echo "📦 テスト依存関係をインストールしています..."
pip install -r test-requirements.txt

# pre-commitのインストール
echo "🔧 pre-commitフックをインストールしています..."
pre-commit install
pre-commit install --hook-type commit-msg

# 初回実行（すべてのファイルをチェック）
echo "🔍 既存コードの品質チェックを実行しています..."
pre-commit run --all-files || true

# カバレッジディレクトリの作成
mkdir -p htmlcov
mkdir -p .coverage-reports

# テスト実行スクリプトの作成
cat > scripts/run-tdd-tests.sh << 'EOF'
#!/bin/bash
# TDDテスト実行スクリプト

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# テストモード選択
MODE=${1:-"unit"}

case $MODE in
    "unit")
        echo -e "${GREEN}ユニットテストを実行しています...${NC}"
        pytest tests/unit -v --cov=. --cov-report=html --cov-report=term
        ;;
    "integration")
        echo -e "${GREEN}統合テストを実行しています...${NC}"
        pytest tests/integration -v
        ;;
    "all")
        echo -e "${GREEN}すべてのテストを実行しています...${NC}"
        pytest tests -v --cov=. --cov-report=html --cov-report=term
        ;;
    "watch")
        echo -e "${YELLOW}ファイル変更を監視してテストを自動実行します...${NC}"
        pytest-watch tests/unit -v
        ;;
    *)
        echo -e "${RED}未知のモード: $MODE${NC}"
        echo "使用方法: $0 [unit|integration|all|watch]"
        exit 1
        ;;
esac

# カバレッジレポートの場所を表示
if [ -f "htmlcov/index.html" ]; then
    echo -e "\n${GREEN}カバレッジレポート: file://$(pwd)/htmlcov/index.html${NC}"
fi
EOF

chmod +x scripts/run-tdd-tests.sh

# TDDワークフロースクリプトの作成
cat > scripts/tdd-new-feature.sh << 'EOF'
#!/bin/bash
# 新機能のTDD開発スクリプト

set -e

FEATURE_NAME=$1

if [ -z "$FEATURE_NAME" ]; then
    echo "使用方法: $0 <feature_name>"
    exit 1
fi

echo "🎯 TDD: $FEATURE_NAME の開発を開始します"

# 1. テストファイルの作成
TEST_FILE="tests/unit/test_${FEATURE_NAME}.py"
echo "📝 テストファイルを作成: $TEST_FILE"

cat > $TEST_FILE << EOT
"""${FEATURE_NAME}のテスト"""
import pytest
from unittest.mock import Mock, patch


class Test${FEATURE_NAME^}:
    """${FEATURE_NAME^}のテストクラス"""
    
    def test_should_fail_initially(self):
        """最初は失敗するテスト（TDD: Red）"""
        # TODO: 実装前なので失敗する
        assert False, "実装してください"
    
    # TODO: 追加のテストケースをここに記述
EOT

# 2. テストの実行（失敗することを確認）
echo "🔴 Red: テストが失敗することを確認..."
pytest $TEST_FILE -v || true

echo ""
echo "✅ 次のステップ:"
echo "1. $TEST_FILE にテストケースを追加"
echo "2. テストが失敗することを確認（Red）"
echo "3. 最小限のコードで実装（Green）"
echo "4. リファクタリング（Refactor）"
echo ""
echo "テストの実行: pytest $TEST_FILE -v"
EOF

chmod +x scripts/tdd-new-feature.sh

# GitHub Actions用のワークフロー作成
mkdir -p .github/workflows
cat > .github/workflows/tdd.yml << 'EOF'
name: TDD CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt', '**/test-requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
    
    - name: Run pre-commit
      run: pre-commit run --all-files
    
    - name: Run tests with coverage
      run: |
        pytest tests/unit -v --cov=. --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
    
    - name: Generate coverage badge
      run: |
        coverage-badge -o coverage.svg -f
    
    - name: Archive test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: |
          htmlcov/
          coverage.xml
          .coverage
EOF

echo ""
echo "✅ TDD環境のセットアップが完了しました！"
echo ""
echo "🎯 次のステップ:"
echo "1. テストの実行: ./scripts/run-tdd-tests.sh"
echo "2. 新機能の開発: ./scripts/tdd-new-feature.sh <feature_name>"
echo "3. カバレッジ確認: open htmlcov/index.html"
echo ""
echo "📚 TDDサイクル:"
echo "  Red → Green → Refactor"
echo ""