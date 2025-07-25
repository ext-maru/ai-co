#!/bin/bash
# AI Company テストシステム初期設定スクリプト

set -e

echo "🧪 AI Company テストシステムをセットアップしています..."

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# プロジェクトディレクトリ
PROJECT_DIR="/home/aicompany/ai_co"
cd "$PROJECT_DIR"

# 仮想環境をアクティベート
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# 1. 必要なPythonパッケージをインストール
echo -e "${BLUE}📦 テスト関連パッケージをインストール中...${NC}"
pip install pytest pytest-cov pytest-asyncio pytest-timeout pytest-mock \
            flake8 black isort mypy \
            requests

# 2. スクリプトに実行権限を付与
echo -e "${BLUE}🔧 実行権限を設定中...${NC}"
chmod +x scripts/ai-test
chmod +x scripts/generate_tests.py

# 3. シンボリックリンクを作成
echo -e "${BLUE}🔗 コマンドリンクを作成中...${NC}"
sudo ln -sf "$PROJECT_DIR/scripts/ai-test" /usr/local/bin/ai-test

# 4. 初期ディレクトリ作成
echo -e "${BLUE}📁 必要なディレクトリを作成中...${NC}"
mkdir -p coverage
mkdir -p htmlcov
mkdir -p junit

# 5. テストワーカーをキューに追加
echo -e "${BLUE}🚀 TestGeneratorWorkerを起動設定に追加中...${NC}"
cat >> "$PROJECT_DIR/scripts/ai-start" << 'EOF'

# TestGeneratorWorker
echo "Starting TestGeneratorWorker..."
tmux new-window -t $SESSION_NAME -n test_generator
tmux send-keys -t $SESSION_NAME:test_generator "cd $PROJECT_DIR && source venv/bin/activate && python workers/test_generator_worker.py" C-m
EOF

# 6. RabbitMQキューを作成
echo -e "${BLUE}🐰 RabbitMQキューを作成中...${NC}"
sudo rabbitmqctl add_queue ai_test_generation durable=true || true

# 7. 初回テスト実行
echo -e "${BLUE}🧪 初回テストを実行中...${NC}"
pytest --collect-only || true

# 8. サンプルテスト結果生成
echo -e "${BLUE}📊 サンプルカバレッジレポートを生成中...${NC}"
pytest tests/unit/test_task_worker.py --cov=workers --cov-report=html --cov-report=json -v || true

echo -e "${GREEN}✅ テストシステムのセットアップが完了しました！${NC}"
echo ""
echo "使用可能なコマンド:"
echo "  ai-test              - テスト実行"
echo "  ai-test coverage     - カバレッジ確認"
echo "  ai-test generate     - AIテスト生成"
echo "  ai-test --help       - ヘルプ表示"
echo ""
echo "GitHub連携:"
echo "  1. リポジトリの Settings → Secrets → Actions で以下を設定:"
echo "     - CLAUDE_API_KEY"
echo "     - SLACK_WEBHOOK"
echo "  2. mainブランチにプッシュすると自動でCIが実行されます"
