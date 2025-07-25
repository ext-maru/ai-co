#!/bin/bash
# Elders Guild - Docker Orchestration Script
# プロジェクト別Docker環境起動スクリプト

set -e

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 使用方法
usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [PROJECT]     - プロジェクトを起動"
    echo "  stop [PROJECT]      - プロジェクトを停止"
    echo "  restart [PROJECT]   - プロジェクトを再起動"
    echo "  status              - 全サービスの状態確認"
    echo "  logs [PROJECT]      - プロジェクトのログを表示"
    echo "  cleanup             - 未使用リソースを削除"
    echo ""
    echo "Projects:"
    echo "  core                - 基盤インフラ（DB、Redis、監視）"
    echo "  web-portal          - Web Portal プロジェクト"
    echo "  workers             - 4賢者・ワーカーシステム"
    echo "  ai-commands         - AI統合コマンドシステム"
    echo "  all                 - 全プロジェクト"
    echo ""
    echo "Options:"
    echo "  --debug             - デバッグモード（pgAdmin、Redis Commander起動）"
    echo "  --build             - イメージを再ビルド"
    echo "  --detach            - バックグラウンドで実行"
    echo ""
    echo "Examples:"
    echo "  $0 start core                    # 基盤インフラのみ起動"
    echo "  $0 start web-portal --build      # Web Portalを再ビルドして起動"
    echo "  $0 start all --debug             # 全プロジェクトをデバッグモードで起動"
    echo "  $0 logs workers                  # Workersのログを表示"
    echo "  $0 stop all                      # 全プロジェクトを停止"
}

# ネットワーク作成
create_network() {
    if ! docker network ls | grep -q "elders-network"; then
        log "Creating Docker network: elders-network"
        docker network create elders-network --subnet=172.20.0.0/16
        success "Network created successfully"
    else
        log "Network elders-network already exists"
    fi
}

# プロジェクト起動
start_project() {
    local project=$1
    local build_flag=""
    local detach_flag="-d"
    local debug_profile=""

    if [[ "$BUILD" == "true" ]]; then
        build_flag="--build"
    fi

    if [[ "$DEBUG" == "true" ]]; then
        debug_profile="--profile debug"
    fi

    create_network

    case $project in
        "core")
            log "Starting core infrastructure..."
            docker compose -f docker-compose.core.yml up $detach_flag $build_flag $debug_profile
            ;;
        "web-portal")
            log "Starting Web Portal project..."
            docker compose -f docker-compose.core.yml -f docker-compose.web-portal.yml up $detach_flag $build_flag
            ;;
        "workers")
            log "Starting Workers system..."
            docker compose -f docker-compose.core.yml -f docker-compose.workers.yml up $detach_flag $build_flag
            ;;
        "ai-commands")
            log "Starting AI Commands system..."
            docker compose -f docker-compose.core.yml -f docker-compose.ai-commands.yml up $detach_flag $build_flag
            ;;
        "all")
            log "Starting all projects..."
            docker compose -f docker-compose.core.yml -f docker-compose.web-portal.yml -f docker-compose.workers.yml -f docker-compose.ai-commands.yml up $detach_flag $build_flag $debug_profile
            ;;
        *)
            error "Unknown project: $project"
            usage
            exit 1
            ;;
    esac

    success "Project $project started successfully"
}

# プロジェクト停止
stop_project() {
    local project=$1

    case $project in
        "core")
            log "Stopping core infrastructure..."
            docker compose -f docker-compose.core.yml down
            ;;
        "web-portal")
            log "Stopping Web Portal project..."
            docker compose -f docker-compose.web-portal.yml down
            ;;
        "workers")
            log "Stopping Workers system..."
            docker compose -f docker-compose.workers.yml down
            ;;
        "ai-commands")
            log "Stopping AI Commands system..."
            docker compose -f docker-compose.ai-commands.yml down
            ;;
        "all")
            log "Stopping all projects..."
            docker compose -f docker-compose.core.yml -f docker-compose.web-portal.yml -f docker-compose.workers.yml -f docker-compose.ai-commands.yml down
            ;;
        *)
            error "Unknown project: $project"
            usage
            exit 1
            ;;
    esac

    success "Project $project stopped successfully"
}

# ログ表示
show_logs() {
    local project=$1

    case $project in
        "core")
            docker compose -f docker-compose.core.yml logs -f
            ;;
        "web-portal")
            docker compose -f docker-compose.web-portal.yml logs -f
            ;;
        "workers")
            docker compose -f docker-compose.workers.yml logs -f
            ;;
        "ai-commands")
            docker compose -f docker-compose.ai-commands.yml logs -f
            ;;
        "all")
            docker compose -f docker-compose.core.yml -f docker-compose.web-portal.yml -f docker-compose.workers.yml -f docker-compose.ai-commands.yml logs -f
            ;;
        *)
            error "Unknown project: $project"
            usage
            exit 1
            ;;
    esac
}

# 状態確認
show_status() {
    log "Checking Docker services status..."
    echo ""
    docker compose -f docker-compose.core.yml -f docker-compose.web-portal.yml -f docker-compose.workers.yml -f docker-compose.ai-commands.yml ps
    echo ""
    docker network ls | grep elders
    echo ""
    docker volume ls | grep elders
}

# クリーンアップ
cleanup() {
    log "Cleaning up unused Docker resources..."
    docker system prune -f
    docker volume prune -f
    success "Cleanup completed"
}

# メイン処理
main() {
    local command=$1
    shift

    # オプション解析
    BUILD=false
    DEBUG=false
    DETACH=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --build)
                BUILD=true
                shift
                ;;
            --debug)
                DEBUG=true
                shift
                ;;
            --detach)
                DETACH=true
                shift
                ;;
            --no-detach)
                DETACH=false
                shift
                ;;
            *)
                PROJECT=$1
                shift
                ;;
        esac
    done

    case $command in
        "start")
            if [[ -z "$PROJECT" ]]; then
                error "Project name is required"
                usage
                exit 1
            fi
            start_project $PROJECT
            ;;
        "stop")
            if [[ -z "$PROJECT" ]]; then
                error "Project name is required"
                usage
                exit 1
            fi
            stop_project $PROJECT
            ;;
        "restart")
            if [[ -z "$PROJECT" ]]; then
                error "Project name is required"
                usage
                exit 1
            fi
            stop_project $PROJECT
            start_project $PROJECT
            ;;
        "status")
            show_status
            ;;
        "logs")
            if [[ -z "$PROJECT" ]]; then
                error "Project name is required"
                usage
                exit 1
            fi
            show_logs $PROJECT
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            usage
            ;;
        *)
            error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# スクリプト実行
if [[ $# -eq 0 ]]; then
    usage
    exit 1
fi

main "$@"
