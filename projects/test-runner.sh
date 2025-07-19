#!/bin/bash
# Elders Guild Projects - Test Runner Script
# プロジェクトテスト実行スクリプト

set -e

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

# 使用方法
usage() {
    echo "Elders Guild Projects - Test Runner"
    echo ""
    echo "Usage: $0 [PROJECT] [TEST_TYPE] [OPTIONS]"
    echo ""
    echo "Projects:"
    echo "  image-upload-manager    - 画像アップロード管理システム"
    echo "  all                     - 全プロジェクト"
    echo ""
    echo "Test Types:"
    echo "  all                     - 全テスト実行"
    echo "  unit                    - ユニットテストのみ"
    echo "  integration             - 統合テストのみ"
    echo "  coverage                - カバレッジ分析"
    echo "  quick                   - 高速テスト（カバレッジなし）"
    echo "  lint                    - コード品質チェック"
    echo "  format                  - コードフォーマット"
    echo "  specific                - 特定テストファイル"
    echo ""
    echo "Options:"
    echo "  --build                 - テストイメージを再ビルド"
    echo "  --viewer                - テスト結果ビューアを起動"
    echo "  --interactive           - インタラクティブシェル"
    echo "  --cleanup               - テスト環境をクリーンアップ"
    echo ""
    echo "Examples:"
    echo "  $0 image-upload-manager all                    # 全テスト実行"
    echo "  $0 image-upload-manager coverage --build       # カバレッジ分析（再ビルド）"
    echo "  $0 image-upload-manager unit --viewer          # ユニットテスト + ビューア起動"
    echo "  $0 image-upload-manager specific tests/unit/test_models.py"
    echo "  $0 image-upload-manager lint                   # コード品質チェック"
    echo "  $0 image-upload-manager --interactive          # インタラクティブシェル"
    echo ""
    echo "Test Results:"
    echo "  - Coverage Report: http://localhost:9003"
    echo "  - Results Directory: ./image-upload-manager/test_results/"
}

# テスト環境の準備
prepare_test_env() {
    local project=$1

    log "Preparing test environment for $project..."

    # テスト結果ディレクトリを作成
    mkdir -p "$project/test_results" "$project/test_data"

    # 既存のテスト結果をバックアップ
    if [[ -d "$project/test_results" ]] && [[ "$(ls -A $project/test_results)" ]]; then
        local backup_dir="$project/test_results_backup_$(date +%Y%m%d_%H%M%S)"
        mv "$project/test_results" "$backup_dir"
        mkdir -p "$project/test_results"
        info "Previous test results backed up to: $backup_dir"
    fi
}

# テストイメージのビルド
build_test_image() {
    local project=$1

    log "Building test image for $project..."
    docker-compose -f docker-compose.test.yml build "${project}-test"
    success "Test image built successfully!"
}

# テスト実行
run_tests() {
    local project=$1
    local test_type=$2
    local specific_test=$3

    log "Running $test_type tests for $project..."

    # テスト実行
    if [[ "$test_type" == "specific" && -n "$specific_test" ]]; then
        docker-compose -f docker-compose.test.yml run --rm "${project}-test" specific "$specific_test"
    else
        docker-compose -f docker-compose.test.yml run --rm "${project}-test" "$test_type"
    fi

    # テスト結果の確認
    if [[ $? -eq 0 ]]; then
        success "Tests passed for $project!"
    else
        error "Tests failed for $project!"
        return 1
    fi
}

# テスト結果ビューアを起動
start_viewer() {
    log "Starting test results viewer..."

    # nginx設定ディレクトリ作成
    mkdir -p test-viewer

    # nginx設定ファイル作成
    cat > test-viewer/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    keepalive_timeout 65;

    server {
        listen 80;
        server_name localhost;

        location / {
            root /usr/share/nginx/html;
            index index.html;
            autoindex on;
            autoindex_exact_size off;
            autoindex_localtime on;
        }

        location ~ \.html$ {
            root /usr/share/nginx/html;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }
    }
}
EOF

    docker-compose -f docker-compose.test.yml --profile viewer up -d test-viewer

    success "Test results viewer started at: http://localhost:9003"
}

# インタラクティブシェル
interactive_shell() {
    local project=$1

    log "Starting interactive shell for $project..."
    docker-compose -f docker-compose.test.yml run --rm "${project}-test" interactive
}

# クリーンアップ
cleanup() {
    log "Cleaning up test environment..."

    docker-compose -f docker-compose.test.yml down --volumes --remove-orphans
    docker system prune -f

    success "Test environment cleaned up!"
}

# メイン処理
main() {
    local project=$1
    local test_type=$2
    shift 2

    # オプション解析
    BUILD=false
    VIEWER=false
    INTERACTIVE=false
    CLEANUP=false
    SPECIFIC_TEST=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --build)
                BUILD=true
                shift
                ;;
            --viewer)
                VIEWER=true
                shift
                ;;
            --interactive)
                INTERACTIVE=true
                shift
                ;;
            --cleanup)
                CLEANUP=true
                shift
                ;;
            *)
                SPECIFIC_TEST=$1
                shift
                ;;
        esac
    done

    # バリデーション
    if [[ -z "$project" ]]; then
        error "Project name is required"
        usage
        exit 1
    fi

    if [[ "$project" != "image-upload-manager" && "$project" != "all" ]]; then
        error "Unknown project: $project"
        usage
        exit 1
    fi

    # クリーンアップのみの場合
    if [[ "$CLEANUP" == "true" ]]; then
        cleanup
        exit 0
    fi

    # インタラクティブシェルの場合
    if [[ "$INTERACTIVE" == "true" ]]; then
        interactive_shell "$project"
        exit 0
    fi

    # テストタイプが指定されていない場合
    if [[ -z "$test_type" ]]; then
        test_type="all"
    fi

    # テスト環境準備
    prepare_test_env "$project"

    # ビルドが必要な場合
    if [[ "$BUILD" == "true" ]]; then
        build_test_image "$project"
    fi

    # テスト実行
    run_tests "$project" "$test_type" "$SPECIFIC_TEST"

    # ビューア起動が必要な場合
    if [[ "$VIEWER" == "true" ]]; then
        start_viewer
    fi

    info "Test execution completed for $project"
    info "Results available in: ./$project/test_results/"

    if [[ "$VIEWER" == "true" ]]; then
        info "View results at: http://localhost:9003"
    fi
}

# スクリプト実行
if [[ $# -eq 0 ]]; then
    usage
    exit 1
fi

main "$@"
