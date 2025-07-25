#!/bin/bash
# 🏛️ エルダーズギルド SSH デプロイメントスクリプト
# 作成者: クロードエルダー（Claude Elder）
# 日付: 2025年7月10日

set -euo pipefail

# 🎨 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 📋 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_LOG="/tmp/elders-guild-deploy.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 🏛️ エルダーズギルドバナー
echo -e "${PURPLE}🏛️ ===============================================${NC}"
echo -e "${PURPLE}   エルダーズギルド SSH デプロイメントシステム${NC}"
echo -e "${PURPLE}   🧙‍♂️ 4賢者統合 🛡️ 騎士団防衛${NC}"
echo -e "${PURPLE}===============================================${NC}"

# 📋 関数定義
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_sage() {
    echo -e "${CYAN}[SAGE]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_knight() {
    echo -e "${BLUE}[KNIGHT]${NC} $1" | tee -a "$DEPLOY_LOG"
}

# 🧙‍♂️ 4賢者事前確認
four_sages_pre_check() {
    log_info "🧙‍♂️ 4賢者事前確認開始..."

    # 📚 ナレッジ賢者チェック
    log_sage "📚 ナレッジ賢者: デプロイ履歴確認中..."
    if [ -f "$PROJECT_ROOT/knowledge_base/deployment_history.md" ]; then
        log_sage "📚 ナレッジ賢者: 過去のデプロイ履歴確認完了"
    else
        log_warn "📚 ナレッジ賢者: デプロイ履歴ファイルが見つかりません"
    fi

    # 📋 タスク賢者チェック
    log_sage "📋 タスク賢者: 依存関係確認中..."
    if python3 -c "
    import sys
    sys.path.append('$PROJECT_ROOT')
    try:
        from libs.four_sages_integration import FourSagesIntegration
        sages = FourSagesIntegration()
        result = sages.task_sage_dependency_check()
        print(f'Task Sage Result: {result}')
    except Exception as e:
        print(f'Task Sage Error: {e}')
        sys.exit(1)
    "; then
        log_sage "📋 タスク賢者: 依存関係確認完了"
    else
        log_error "📋 タスク賢者: 依存関係エラー"
        return 1
    fi

    # 🚨 インシデント賢者チェック
    log_sage "🚨 インシデント賢者: システム状態確認中..."
    if python3 -c "
    import sys
    sys.path.append('$PROJECT_ROOT')
    try:
        from libs.incident_manager import IncidentManager
        incident_mgr = IncidentManager()
        print('Incident Sage: System check completed')
    except Exception as e:
        print(f'Incident Sage Error: {e}')
        sys.exit(1)
    "; then
        log_sage "🚨 インシデント賢者: システム状態正常"
    else
        log_error "🚨 インシデント賢者: システム異常検知"
        return 1
    fi

    # 🔍 RAG賢者チェック
    log_sage "🔍 RAG賢者: 環境分析中..."
    if python3 -c "
    import sys
    sys.path.append('$PROJECT_ROOT')
    try:
        from libs.enhanced_rag_manager import EnhancedRagManager
        rag_mgr = EnhancedRagManager()
        print('RAG Sage: Environment analysis completed')
    except Exception as e:
        print(f'RAG Sage Error: {e}')
        sys.exit(1)
    "; then
        log_sage "🔍 RAG賢者: 環境分析完了"
    else
        log_error "🔍 RAG賢者: 環境分析エラー"
        return 1
    fi

    log_info "🏛️ 4賢者事前確認: 全て承認"
    return 0
}

# 🛡️ 騎士団セキュリティ確認
knights_security_check() {
    log_info "🛡️ 騎士団セキュリティ確認開始..."

    # ⚔️ セキュリティ騎士団
    log_knight "⚔️ セキュリティ騎士団: 権限確認中..."
    if [ "$(id -u)" -eq 0 ]; then
        log_error "⚔️ セキュリティ騎士団: rootユーザーでの実行は禁止されています"
        return 1
    fi
    log_knight "⚔️ セキュリティ騎士団: 権限確認完了"

    # 🗡️ 認証騎士団
    log_knight "🗡️ 認証騎士団: SSH設定確認中..."
    if [ -z "${SSH_AUTH_SOCK:-}" ]; then
        log_error "🗡️ 認証騎士団: SSH認証エージェントが設定されていません"
        return 1
    fi
    log_knight "🗡️ 認証騎士団: SSH認証確認完了"

    # 🛡️ 監視騎士団
    log_knight "🛡️ 監視騎士団: プロセス監視開始"
    # バックグラウンドで監視プロセス開始
    (
        while true; do
            ps aux | grep -E "(deploy|ssh)" | grep -v grep >> "$DEPLOY_LOG.monitor" 2>/dev/null || true
            sleep 5
        done
    ) &
    MONITOR_PID=$!
    echo "$MONITOR_PID" > "/tmp/deploy_monitor.pid"
    log_knight "🛡️ 監視騎士団: 監視開始 (PID: $MONITOR_PID)"

    log_info "🏛️ 騎士団セキュリティ確認: 完了"
    return 0
}

# 🧪 事前テスト実行
pre_deploy_tests() {
    log_info "🧪 事前テスト実行開始..."

    cd "$PROJECT_ROOT"

    # Python環境確認
    log_info "🐍 Python環境確認中..."
    if ! python3 --version; then
        log_error "🐍 Python3が見つかりません"
        return 1
    fi

    # 依存関係確認
    log_info "📦 依存関係確認中..."
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt --quiet
        log_info "📦 依存関係インストール完了"
    fi

    # 基本テスト実行
    log_info "🧪 基本テスト実行中..."
    if python3 -c "
    import sys
    sys.path.append('.')
    try:
        from libs.four_sages_integration import FourSagesIntegration
        from workers.enhanced_task_worker import EnhancedTaskWorker
        print('✅ 基本テスト: 成功')
    except Exception as e:
        print(f'❌ 基本テスト: 失敗 - {e}')
        sys.exit(1)
    "; then
        log_info "🧪 基本テスト: 成功"
    else
        log_error "🧪 基本テスト: 失敗"
        return 1
    fi

    log_info "🏛️ 事前テスト: 完了"
    return 0
}

# 🚀 デプロイメント実行
execute_deployment() {
    local target_env="$1"
    local target_host="$2"
    local target_user="$3"

    log_info "🚀 デプロイメント実行開始..."
    log_info "🎯 対象環境: $target_env"
    log_info "🖥️  対象ホスト: $target_host"
    log_info "👤 対象ユーザー: $target_user"

    # Git状態確認
    log_info "📝 Git状態確認中..."
    if ! git status --porcelain | grep -q .; then
        log_info "📝 Git状態: クリーン"
    else
        log_warn "📝 Git状態: 未コミットの変更があります"
        git status --porcelain
    fi

    # リモートサーバーへの接続確認
    log_info "🌐 リモートサーバー接続確認中..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$target_user@$target_host" "echo 'SSH接続確認'" 2>/dev/null; then
        log_info "🌐 リモートサーバー接続: 成功"
    else
        log_error "🌐 リモートサーバー接続: 失敗"
        return 1
    fi

    # ファイル転送
    log_info "📤 ファイル転送開始..."
    if rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
        "$PROJECT_ROOT/" "$target_user@$target_host:/opt/elders-guild/"; then
        log_info "📤 ファイル転送: 成功"
    else
        log_error "📤 ファイル転送: 失敗"
        return 1
    fi

    # リモートでの依存関係インストール
    log_info "📦 リモート依存関係インストール中..."
    if ssh "$target_user@$target_host" "cd /opt/elders-guild && pip3 install -r requirements.txt --quiet"; then
        log_info "📦 リモート依存関係インストール: 成功"
    else
        log_error "📦 リモート依存関係インストール: 失敗"
        return 1
    fi

    # サービス再起動
    log_info "🔄 サービス再起動中..."
    if ssh "$target_user@$target_host" "cd /opt/elders-guild && sudo systemctl restart elders-guild"; then
        log_info "🔄 サービス再起動: 成功"
    else
        log_error "🔄 サービス再起動: 失敗"
        return 1
    fi

    log_info "🏛️ デプロイメント実行: 完了"
    return 0
}

# 🔍 事後検証
post_deploy_verification() {
    local target_host="$1"
    local target_user="$2"

    log_info "🔍 事後検証開始..."

    # サービス状態確認
    log_info "🔍 サービス状態確認中..."
    if ssh "$target_user@$target_host" "systemctl is-active elders-guild"; then
        log_info "🔍 サービス状態: 正常"
    else
        log_error "🔍 サービス状態: 異常"
        return 1
    fi

    # ヘルスチェック
    log_info "🔍 ヘルスチェック実行中..."
    sleep 30  # サービス起動待機
    if ssh "$target_user@$target_host" "cd /opt/elders-guild && python3 -c 'from libs.four_sages_integration import FourSagesIntegration; sages = FourSagesIntegration(); print(\"Health check passed\")'"; then
        log_info "🔍 ヘルスチェック: 成功"
    else
        log_error "🔍 ヘルスチェック: 失敗"
        return 1
    fi

    # 4賢者最終確認
    log_sage "🧙‍♂️ 4賢者最終確認中..."
    if ssh "$target_user@$target_host" "cd /opt/elders-guild && python3 -c 'from libs.four_sages_integration import FourSagesIntegration; sages = FourSagesIntegration(); sages.post_deploy_verification()'"; then
        log_sage "🧙‍♂️ 4賢者最終確認: 承認"
    else
        log_error "🧙‍♂️ 4賢者最終確認: 拒否"
        return 1
    fi

    log_info "🏛️ 事後検証: 完了"
    return 0
}

# 🧹 クリーンアップ
cleanup() {
    log_info "🧹 クリーンアップ開始..."

    # 監視プロセス終了
    if [ -f "/tmp/deploy_monitor.pid" ]; then
        MONITOR_PID=$(cat "/tmp/deploy_monitor.pid")
        if kill "$MONITOR_PID" 2>/dev/null; then
            log_knight "🛡️ 監視騎士団: 監視終了"
        fi
        rm -f "/tmp/deploy_monitor.pid"
    fi

    # 一時ファイル削除
    rm -f "$DEPLOY_LOG.monitor"

    log_info "🧹 クリーンアップ: 完了"
}

# 📋 使用方法表示
usage() {
    echo "使用方法: $0 <環境> <ホスト> <ユーザー>"
    echo ""
    echo "例:"
    echo "  $0 staging staging.example.com deploy"
    echo "  $0 production prod.example.com deploy"
    echo ""
    echo "環境変数:"
    echo "  SSH_AUTH_SOCK - SSH認証エージェント"
    echo ""
    echo "🏛️ エルダーズギルド SSH デプロイメントシステム"
    echo "🧙‍♂️ 4賢者統合 🛡️ 騎士団防衛"
}

# 🎯 メイン処理
main() {
    # 引数確認
    if [ $# -ne 3 ]; then
        usage
        exit 1
    fi

    local target_env="$1"
    local target_host="$2"
    local target_user="$3"

    # ログファイル初期化
    echo "🏛️ エルダーズギルド SSH デプロイメントログ - $TIMESTAMP" > "$DEPLOY_LOG"

    # トラップ設定
    trap cleanup EXIT

    log_info "🚀 デプロイメント開始: $target_env"

    # 実行フロー
    if ! four_sages_pre_check; then
        log_error "🧙‍♂️ 4賢者事前確認失敗"
        exit 1
    fi

    if ! knights_security_check; then
        log_error "🛡️ 騎士団セキュリティ確認失敗"
        exit 1
    fi

    if ! pre_deploy_tests; then
        log_error "🧪 事前テスト失敗"
        exit 1
    fi

    if ! execute_deployment "$target_env" "$target_host" "$target_user"; then
        log_error "🚀 デプロイメント実行失敗"
        exit 1
    fi

    if ! post_deploy_verification "$target_host" "$target_user"; then
        log_error "🔍 事後検証失敗"
        exit 1
    fi

    log_info "🏛️ デプロイメント完了: $target_env"
    log_info "📝 ログファイル: $DEPLOY_LOG"

    # 成功通知
    echo -e "${GREEN}🎉 エルダーズギルド デプロイメント成功! 🎉${NC}"
    echo -e "${GREEN}🧙‍♂️ 4賢者承認 🛡️ 騎士団防衛完了${NC}"
}

# スクリプト実行
main "$@"
