#!/bin/bash
# 🔗 GitHub Hooks 設定スクリプト
# Quality Pipeline 自動実行設定

set -e

echo "🔗 GitHub Hooks 設定開始"

# 色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 関数定義
log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Git hooks ディレクトリ作成
setup_git_hooks() {
    log_info "Git hooks ディレクトリ設定中..."
    
    HOOKS_DIR=".git/hooks"
    
    if [[ ! -d "$HOOKS_DIR" ]]; then
        log_error "Git リポジトリが見つかりません"
        exit 1
    fi
    
    # Pre-commit hook
    cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Quality Pipeline Pre-commit Hook

echo "🔍 Pre-commit quality check..."

# ステージされたPythonファイルをチェック
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | grep -E '^(libs/quality|tests/integration/test_quality)' || true)

if [[ -z "$STAGED_FILES" ]]; then
    echo "✅ Quality Pipeline関連ファイルの変更なし"
    exit 0
fi

echo "📁 対象ファイル: $STAGED_FILES"

# Black フォーマットチェック
echo "🎨 Black フォーマットチェック..."
if ! black --check $STAGED_FILES; then
    echo "❌ フォーマットエラーが見つかりました"
    echo "💡 修正: black $STAGED_FILES"
    exit 1
fi

# isort チェック
echo "📦 isort チェック..."
if ! isort --check-only $STAGED_FILES; then
    echo "❌ import順序エラーが見つかりました"
    echo "💡 修正: isort $STAGED_FILES"
    exit 1
fi

# 基本的な構文チェック
echo "🔍 構文チェック..."
for file in $STAGED_FILES; do
    if ! python3 -m py_compile "$file"; then
        echo "❌ 構文エラー: $file"
        exit 1
    fi
done

echo "✅ Pre-commit チェック完了"
EOF

    chmod +x "$HOOKS_DIR/pre-commit"
    log_success "Pre-commit hook 設定完了"
    
    # Pre-push hook
    cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# Quality Pipeline Pre-push Hook

echo "🚀 Pre-push quality validation..."

# Quality Pipeline関連の変更があるかチェック
CHANGED_FILES=$(git diff HEAD~1 --name-only | grep -E '^(libs/quality|tests/integration/test_quality)' || true)

if [[ -z "$CHANGED_FILES" ]]; then
    echo "✅ Quality Pipeline関連ファイルの変更なし"
    exit 0
fi

echo "🧪 統合テスト実行..."
if ! python3 -m pytest tests/integration/test_quality_servants_mock.py -v --tb=short; then
    echo "❌ 統合テストが失敗しました"
    echo "💡 修正後に再度プッシュしてください"
    exit 1
fi

echo "✅ Pre-push チェック完了"
EOF

    chmod +x "$HOOKS_DIR/pre-push"
    log_success "Pre-push hook 設定完了"
}

# GitHub Actions secrets確認
check_github_secrets() {
    log_info "GitHub Actions 設定確認..."
    
    # GitHub CLI がインストールされているかチェック
    if ! command -v gh &> /dev/null; then
        log_warn "GitHub CLI (gh) がインストールされていません"
        log_info "インストール: https://cli.github.com/"
        return
    fi
    
    # リポジトリの認証状態確認
    if ! gh auth status &> /dev/null; then
        log_warn "GitHub認証が必要です"
        log_info "認証: gh auth login"
        return
    fi
    
    log_success "GitHub CLI 認証済み"
    
    # 必要なSecretsの確認
    echo "🔑 推奨GitHub Secrets:"
    echo "  - SLACK_WEBHOOK_URL: Slack通知用"
    echo "  - DOCKERHUB_USERNAME: Docker Hub認証用"
    echo "  - DOCKERHUB_TOKEN: Docker Hub認証用"
    echo ""
    echo "設定方法:"
    echo "  gh secret set SLACK_WEBHOOK_URL"
    echo "  gh secret set DOCKERHUB_USERNAME"
    echo "  gh secret set DOCKERHUB_TOKEN"
}

# Quality Pipeline GitHub Action テスト
test_github_action() {
    log_info "GitHub Action 構文テスト..."
    
    # yamllint がインストールされているかチェック
    if command -v yamllint &> /dev/null; then
        if yamllint .github/workflows/quality-pipeline.yml; then
            log_success "GitHub Action YAML構文チェック完了"
        else
            log_error "GitHub Action YAML構文エラー"
            return 1
        fi
    else
        log_warn "yamllint がインストールされていません"
        log_info "インストール: pip install yamllint"
    fi
    
    # act がインストールされているかチェック (ローカルテスト用)
    if command -v act &> /dev/null; then
        log_info "act でローカルテスト実行可能"
        echo "ローカルテスト実行: act -j test"
    else
        log_info "act をインストールするとローカルでGitHub Actionsをテストできます"
        echo "インストール: https://github.com/nektos/act"
    fi
}

# メイン実行
main() {
    log_info "Quality Pipeline GitHub 統合設定開始"
    
    # 現在のディレクトリがプロジェクトルートかチェック
    if [[ ! -f "CLAUDE.md" ]]; then
        log_error "プロジェクトルートディレクトリで実行してください"
        exit 1
    fi
    
    setup_git_hooks
    check_github_secrets
    test_github_action
    
    echo ""
    log_success "🎉 GitHub統合設定完了！"
    echo ""
    echo "次のステップ:"
    echo "1. GitHub Actionsが有効であることを確認"
    echo "2. 必要なSecretsを設定"
    echo "3. Quality Pipeline関連ファイルを変更してプッシュテスト"
    echo ""
    echo "関連コマンド:"
    echo "  git add libs/quality/"
    echo "  git commit -m 'feat: quality pipeline update'"
    echo "  git push"
}

# 実行
main "$@"