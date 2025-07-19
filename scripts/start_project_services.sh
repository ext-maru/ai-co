#!/bin/bash
# Elders Guild - Project Services Startup Script
# 根本解決: Docker権限問題の解決とサービス自動化

set -e

PROJECT_DIR="/home/aicompany/ai_co/projects"
LOG_FILE="/home/aicompany/ai_co/logs/project_services.log"

# ログディレクトリ作成
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🏛️ エルダーズギルド プロジェクトサービス起動開始"

# Docker権限確認
if ! sg docker -c "docker ps" >/dev/null 2>&1; then
    log "❌ Docker権限エラー: aicompanyユーザーがdockerグループにアクセスできません"
    log "解決方法: ログアウト→ログインまたは以下のコマンド実行"
    log "sudo usermod -aG docker aicompany && newgrp docker"
    exit 1
fi

log "✅ Docker権限確認完了"

# Docker Composeでサービス起動
cd "$PROJECT_DIR"

log "🚀 Docker Composeサービス起動中..."
sg docker -c "docker compose -f docker-compose.projects.yml up -d"

# サービス状態確認
log "📊 サービス状態確認中..."
sg docker -c "docker compose -f docker-compose.projects.yml ps"

# ポート確認
log "🔍 ポート確認:"
log "  - 9000: Projects Gateway"
log "  - 9001: Projects Dashboard (Grafana)"
log "  - 9002: Projects Monitor (Prometheus)"
log "  - 9003: Elders Guild Web Frontend"
log "  - 9004: Elders Guild Web Backend"
log "  - 9005: Frontend Project Manager"
log "  - 9007: Web Monitoring Dashboard"
log "  - 9008: Test Calculator"

# ヘルスチェック
sleep 10
log "🩺 ヘルスチェック実行中..."

services=(
    "9005:Frontend Project Manager"
    "9007:Web Monitoring"
    "9008:Test Calculator"
)

for service in "${services[@]}"; do
    port="${service%%:*}"
    name="${service##*:}"

    if curl -sf "http://localhost:$port/" >/dev/null 2>&1; then
        log "✅ $name (Port $port): 正常"
    else
        log "⚠️ $name (Port $port): 応答なし"
    fi
done

log "🎉 プロジェクトサービス起動完了"
log "アクセス先: http://localhost:9005 (Frontend Project Manager)"
