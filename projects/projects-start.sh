#!/bin/bash
# Elders Guild Projects Portfolio - 起動スクリプト
# projectsフォルダ専用Docker環境管理

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
    echo "Elders Guild Projects Portfolio Management"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start               - 全プロジェクトを起動"
    echo "  stop                - 全プロジェクトを停止"
    echo "  restart             - 全プロジェクトを再起動"
    echo "  status              - 全プロジェクトの状態確認"
    echo "  logs [PROJECT]      - プロジェクトのログを表示"
    echo "  add [PROJECT]       - 新しいプロジェクトを追加"
    echo "  remove [PROJECT]    - プロジェクトを削除"
    echo "  health              - プロジェクト健全性チェック"
    echo "  dashboard           - ダッシュボードURLを表示"
    echo "  cleanup             - 未使用リソースを削除"
    echo ""
    echo "Options:"
    echo "  --build             - イメージを再ビルド"
    echo "  --debug             - デバッグモード"
    echo ""
    echo "Available Projects:"
    echo "  - image-upload-manager"
    echo ""
    echo "Access URLs:"
    echo "  - Portfolio: http://localhost:9000"
    echo "  - Dashboard: http://localhost:9001"
    echo "  - Monitoring: http://localhost:9002"
    echo ""
    echo "Examples:"
    echo "  $0 start --build              # 再ビルドして全プロジェクト起動"
    echo "  $0 logs image-upload-manager  # 特定プロジェクトのログ表示"
    echo "  $0 health                     # 健全性チェック実行"
    echo "  $0 dashboard                  # ダッシュボードURL表示"
}

# プロジェクト起動
start_projects() {
    local build_flag=""

    if [[ "$BUILD" == "true" ]]; then
        build_flag="--build"
        log "Building Docker images..."
    fi

    log "Starting Elders Guild Projects Portfolio..."

    # 必要なディレクトリ作成
    mkdir -p gateway monitoring dashboard

    # プロジェクトポートフォリオ起動
    docker-compose -f docker-compose.projects.yml up -d $build_flag

    success "Projects portfolio started successfully!"
    info "Access URLs:"
    info "  - Portfolio: http://localhost:9000"
    info "  - Dashboard: http://localhost:9001 (admin/projects_admin_2025)"
    info "  - Monitoring: http://localhost:9002"
    info "  - Image Upload Manager: http://localhost:9000/image-upload-manager/"
}

# プロジェクト停止
stop_projects() {
    log "Stopping Elders Guild Projects Portfolio..."
    docker-compose -f docker-compose.projects.yml down
    success "Projects portfolio stopped successfully!"
}

# プロジェクト状態確認
show_status() {
    log "Checking projects status..."
    echo ""
    docker-compose -f docker-compose.projects.yml ps
    echo ""

    log "Network information:"
    docker network ls | grep projects
    echo ""

    log "Volume information:"
    docker volume ls | grep projects
    echo ""

    log "Port usage:"
    netstat -tlnp 2>/dev/null | grep -E ":(9000|9001|9002|5433)" || echo "No ports in use"
}

# ログ表示
show_logs() {
    local project=$1

    if [[ -z "$project" ]]; then
        log "Showing all projects logs..."
        docker-compose -f docker-compose.projects.yml logs -f
    else
        case $project in
            "image-upload-manager")
                log "Showing Image Upload Manager logs..."
                docker-compose -f docker-compose.projects.yml logs -f image-upload-manager
                ;;
            "gateway")
                log "Showing Gateway logs..."
                docker-compose -f docker-compose.projects.yml logs -f projects-gateway
                ;;
            "dashboard")
                log "Showing Dashboard logs..."
                docker-compose -f docker-compose.projects.yml logs -f projects-dashboard
                ;;
            "monitor")
                log "Showing Monitor logs..."
                docker-compose -f docker-compose.projects.yml logs -f projects-monitor
                ;;
            *)
                error "Unknown project: $project"
                echo "Available projects: image-upload-manager, gateway, dashboard, monitor"
                exit 1
                ;;
        esac
    fi
}

# 健全性チェック
health_check() {
    log "Performing health check..."
    echo ""

    # Gateway チェック
    if curl -s -f http://localhost:9000/health > /dev/null; then
        success "✓ Projects Gateway is healthy"
    else
        error "✗ Projects Gateway is not responding"
    fi

    # Image Upload Manager チェック
    if curl -s -f http://localhost:9000/image-upload-manager/ > /dev/null; then
        success "✓ Image Upload Manager is healthy"
    else
        error "✗ Image Upload Manager is not responding"
    fi

    # Dashboard チェック
    if curl -s -f http://localhost:9001/api/health > /dev/null; then
        success "✓ Projects Dashboard is healthy"
    else
        warn "△ Projects Dashboard may not be ready yet"
    fi

    # Monitor チェック
    if curl -s -f http://localhost:9002/-/ready > /dev/null; then
        success "✓ Projects Monitor is healthy"
    else
        warn "△ Projects Monitor may not be ready yet"
    fi
}

# ダッシュボード情報表示
show_dashboard() {
    echo ""
    info "🏛️ Elders Guild Projects Portfolio Dashboard"
    echo ""
    info "📊 統合ダッシュボード:"
    info "   URL: http://localhost:9001"
    info "   Login: admin / projects_admin_2025"
    echo ""
    info "📈 監視システム:"
    info "   URL: http://localhost:9002"
    echo ""
    info "🌐 プロジェクトポートフォリオ:"
    info "   URL: http://localhost:9000"
    echo ""
    info "📸 Image Upload Manager:"
    info "   URL: http://localhost:9000/image-upload-manager/"
    echo ""
}

# クリーンアップ
cleanup() {
    log "Cleaning up projects resources..."
    docker-compose -f docker-compose.projects.yml down --volumes --remove-orphans
    docker system prune -f
    success "Cleanup completed"
}

# 新しいプロジェクト追加テンプレート
add_project() {
    local project_name=$1

    if [[ -z "$project_name" ]]; then
        error "Project name is required"
        exit 1
    fi

    if [[ -d "$project_name" ]]; then
        error "Project directory already exists: $project_name"
        exit 1
    fi

    log "Creating new project: $project_name"

    mkdir -p "$project_name"
    cd "$project_name"

    # プロジェクトテンプレート作成
    cat > Dockerfile << EOF
# $project_name - Dockerfile
FROM python:3.11-slim

WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をコピー
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY app/ ./app/

# 非rootユーザー作成
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ポート公開
EXPOSE 5000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:5000/ || exit 1

# アプリケーション起動
CMD ["python", "app/main.py"]
EOF

    cat > requirements.txt << EOF
flask==2.3.3
requests==2.31.0
EOF

    mkdir -p app
    cat > app/main.py << EOF
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'project': '$project_name',
        'status': 'running',
        'version': '1.0.0'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

    cat > README.md << EOF
# $project_name

## Overview
新しいElders Guildプロジェクト

## Development
\`\`\`bash
# プロジェクト起動
../projects-start.sh start

# アクセス
http://localhost:9000/$project_name/
\`\`\`

## API Endpoints
- \`GET /\` - プロジェクト情報
- \`GET /health\` - ヘルスチェック
EOF

    cd ..
    success "Project $project_name created successfully!"
    info "Please update docker-compose.projects.yml to include the new project"
}

# メイン処理
main() {
    local command=$1
    shift

    # オプション解析
    BUILD=false
    DEBUG=false

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
            *)
                PROJECT=$1
                shift
                ;;
        esac
    done

    case $command in
        "start")
            start_projects
            ;;
        "stop")
            stop_projects
            ;;
        "restart")
            stop_projects
            sleep 2
            start_projects
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs $PROJECT
            ;;
        "health")
            health_check
            ;;
        "dashboard")
            show_dashboard
            ;;
        "add")
            add_project $PROJECT
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
