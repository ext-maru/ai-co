#!/bin/bash
# AI Company テストシステム - 依存関係インストールスクリプト

set -e

echo "🔧 AI Company テストシステムの依存関係をインストールします..."

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# プロジェクトディレクトリ
PROJECT_DIR="/home/aicompany/ai_co"
cd "$PROJECT_DIR"

# 仮想環境のチェックと有効化
echo -e "${BLUE}1. Python環境の準備${NC}"
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    echo "仮想環境を有効化しています..."
    source "$PROJECT_DIR/venv/bin/activate"
else
    echo -e "${YELLOW}仮想環境が見つかりません。システムPythonを使用します。${NC}"
fi

# 現在のPython環境を表示
echo "Python: $(which python3)"
echo "pip: $(which pip3)"

# 必要なパッケージのインストール
echo -e "\n${BLUE}2. テスト関連パッケージのインストール${NC}"

# pipのアップグレード
echo "pipをアップグレード中..."
pip3 install --upgrade pip

# テスト関連パッケージ
echo -e "\n${YELLOW}pytest関連パッケージをインストール中...${NC}"
pip3 install pytest pytest-cov pytest-mock pytest-asyncio pytest-timeout

# コード品質ツール（オプション）
echo -e "\n${YELLOW}コード品質ツールをインストール中...${NC}"
pip3 install flake8 black isort mypy || echo "一部のツールのインストールに失敗しましたが、続行します"

# インストール確認
echo -e "\n${BLUE}3. インストール確認${NC}"
python3 -c "
import sys
packages = {
    'pytest': 'pytest',
    'pytest-cov': 'pytest_cov',
    'pytest-mock': 'pytest_mock',
    'requests': 'requests'
}

print('インストール済みパッケージ:')
for display_name, import_name in packages.items():
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f'  ✅ {display_name}: {version}')
    except ImportError:
        print(f'  ❌ {display_name}: 未インストール')
"

# pytest設定の確認
echo -e "\n${BLUE}4. pytest設定の確認${NC}"
if [ -f "$PROJECT_DIR/pytest.ini" ]; then
    echo -e "${GREEN}✅ pytest.ini が存在します${NC}"
else
    echo -e "${YELLOW}⚠️  pytest.ini が見つかりません${NC}"
fi

# テストディレクトリの確認
echo -e "\n${BLUE}5. テストディレクトリの確認${NC}"
if [ -d "$PROJECT_DIR/tests" ]; then
    echo -e "${GREEN}✅ tests/ ディレクトリが存在します${NC}"
    echo "テストファイル:"
    find "$PROJECT_DIR/tests" -name "*.py" -type f | head -10
else
    echo -e "${YELLOW}⚠️  tests/ ディレクトリが見つかりません${NC}"
    mkdir -p "$PROJECT_DIR/tests/unit" "$PROJECT_DIR/tests/integration" "$PROJECT_DIR/tests/e2e"
    echo "ディレクトリを作成しました"
fi

echo -e "\n${GREEN}✅ 依存関係のインストールが完了しました！${NC}"
echo ""
echo "次のステップ:"
echo "  1. cd $PROJECT_DIR"
echo "  2. python3 -m pytest tests/test_mock_system.py -v"
echo "  3. ai-test"
