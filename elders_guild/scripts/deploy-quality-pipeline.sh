#!/bin/bash
# 🚀 Quality Pipeline デプロイメントスクリプト

set -e

echo "🚀 Quality Pipeline Docker デプロイメント開始"

# 色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デプロイメントディレクトリ
DEPLOY_DIR="/home/aicompany/ai_co/elders_guild/deployment/quality-pipeline"
cd "$DEPLOY_DIR"

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

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件チェック中..."
    
    # Docker確認
    if ! command -v docker &> /dev/null; then
        log_error "Docker がインストールされていません"
        exit 1
    fi
    
    # Docker Compose確認
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose がインストールされていません"
        exit 1
    fi
    
    # ディレクトリの存在確認
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "docker-compose.yml が見つかりません"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# 既存コンテナ停止・削除
cleanup_existing() {
    log_info "既存コンテナのクリーンアップ中..."
    
    # 関連コンテナ停止
    docker-compose down --remove-orphans || true
    
    # 関連イメージ削除（オプション）
    if [[ "$1" == "--clean-images" ]]; then
        docker images | grep -E "(quality-watcher|test-forge|comprehensive-guardian)" | awk '{print $3}' | xargs -r docker rmi || true
        log_info "関連イメージを削除しました"
    fi
    
    log_success "クリーンアップ完了"
}

# 必要ディレクトリ作成
setup_directories() {
    log_info "必要ディレクトリ作成中..."
    
    mkdir -p ../../logs/quality-servants
    mkdir -p ../../data/quality-pipeline/certificates
    mkdir -p ../../data/quality-pipeline/reports
    mkdir -p ./grafana/dashboards
    mkdir -p ./grafana/datasources
    
    log_success "ディレクトリ作成完了"
}

# Grafana設定ファイル作成
setup_grafana() {
    log_info "Grafana設定ファイル作成中..."
    
    # データソース設定
    cat > ./grafana/datasources/prometheus.yaml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    basicAuth: false
    isDefault: true
    editable: true
EOF

    # ダッシュボード設定
    cat > ./grafana/dashboards/dashboard.yaml << EOF
apiVersion: 1

providers:
  - name: 'quality-pipeline'
    orgId: 1
    folder: 'Quality Pipeline'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    log_success "Grafana設定完了"
}

# メイン デプロイメント
deploy() {
    log_info "Quality Pipeline デプロイメント開始..."
    
    # ビルドとサービス起動
    docker-compose up -d --build
    
    log_success "デプロイメント完了"
}

# ヘルスチェック
health_check() {
    log_info "サービス健全性チェック中..."
    
    # 待機時間
    sleep 10
    
    # 各サーバントのヘルスチェック
    services=(
        "quality-watcher:8810"
        "test-forge:8811"
        "comprehensive-guardian:8812"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        
        if curl -f -s "http://localhost:${port}/health" > /dev/null; then
            log_success "${name} is healthy"
        else
            log_warn "${name} health check failed"
        fi
    done
    
    # Prometheus チェック
    if curl -f -s "http://localhost:9090/-/healthy" > /dev/null; then
        log_success "Prometheus is healthy"
    else
        log_warn "Prometheus health check failed"
    fi
    
    # Grafana チェック
    if curl -f -s "http://localhost:3000/api/health" > /dev/null; then
        log_success "Grafana is healthy"
    else
        log_warn "Grafana health check failed"
    fi
}

# 使用方法表示
show_usage() {
    echo "使用方法: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  --clean-images    既存イメージも削除"
    echo "  --no-health       ヘルスチェックをスキップ"
    echo "  --help           このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0                # 通常デプロイメント"
    echo "  $0 --clean-images # イメージクリーンアップ付きデプロイメント"
}

# メイン処理
main() {
    # 引数解析
    CLEAN_IMAGES=""
    SKIP_HEALTH=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean-images)
                CLEAN_IMAGES="--clean-images"
                shift
                ;;
            --no-health)
                SKIP_HEALTH="true"
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "不明なオプション: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # デプロイメント実行
    check_prerequisites
    cleanup_existing $CLEAN_IMAGES
    setup_directories
    setup_grafana
    deploy
    
    if [[ -z "$SKIP_HEALTH" ]]; then
        health_check
    fi
    
    # 完了メッセージ
    echo ""
    log_success "🎉 Quality Pipeline デプロイメント完了！"
    echo ""
    echo "アクセス先:"
    echo "  Quality Watcher:        http://localhost:8810"
    echo "  Test Forge:             http://localhost:8811"
    echo "  Comprehensive Guardian: http://localhost:8812"
    echo "  Prometheus:             http://localhost:9090"
    echo "  Grafana:               http://localhost:3000 (admin/elder-council)"
    echo ""
    echo "ログ確認:"
    echo "  docker-compose logs -f"
    echo ""
    echo "停止:"
    echo "  docker-compose down"
}

# 実行
main "$@"