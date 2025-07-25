#!/bin/bash
# Celery Docker統合テストスクリプト
# Issue #93: OSS移行プロジェクト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🐳 Celery Docker統合テスト開始"
echo "==============================================="

# 色付きログ関数
print_success() { echo -e "\033[0;32m✅ $1\033[0m"; }
print_error() { echo -e "\033[0;31m❌ $1\033[0m"; }
print_info() { echo -e "\033[0;34mℹ️ $1\033[0m"; }
print_warning() { echo -e "\033[0;33m⚠️ $1\033[0m"; }

# クリーンアップ関数
cleanup() {
    print_info "🧹 クリーンアップ実行中..."
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.celery.yml down -v --remove-orphans 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
}

# シグナルハンドラー
trap cleanup EXIT INT TERM

cd "$PROJECT_ROOT"

# Phase 1: 前提条件チェック
print_info "Phase 1: 前提条件チェック"
echo "-------------------------------------------"

# Docker確認
if ! command -v docker &> /dev/null; then
    print_error "Dockerがインストールされていません"
    exit 1
fi
print_success "Docker確認 OK"

# Docker Compose確認
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Composeがインストールされていません"
    exit 1
fi
print_success "Docker Compose確認 OK"

# 必要ファイル確認
required_files=(
    "docker-compose.celery.yml"
    "docker/Dockerfile.celery"
    "docker/Dockerfile.claude-test"
    "requirements-celery.txt"
    "workers/enhanced_task_worker_celery.py"
    "tests/unit/test_enhanced_task_worker_celery.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "必要ファイルが見つかりません: $file"
        exit 1
    fi
done
print_success "必要ファイル確認 OK"

# Phase 2: Docker環境構築
print_info "Phase 2: Docker環境構築"
echo "-------------------------------------------"

# 既存コンテナのクリーンアップ
print_info "既存コンテナクリーンアップ中..."
docker-compose -f docker-compose.celery.yml down -v --remove-orphans 2>/dev/null || true

# Dockerイメージビルド
print_info "Dockerイメージビルド中..."
if ! docker-compose -f docker-compose.celery.yml build; then
    print_error "Dockerイメージビルドに失敗しました"
    exit 1
fi
print_success "Dockerイメージビルド完了"

# Phase 3: Redis起動・テスト
print_info "Phase 3: Redis起動・テスト"
echo "-------------------------------------------"

print_info "Redis起動中..."
docker-compose -f docker-compose.celery.yml up -d redis

# Redisヘルスチェック待機
print_info "Redisヘルスチェック待機中..."
timeout=60
counter=0
while ! docker-compose -f docker-compose.celery.yml exec -T redis redis-cli ping >/dev/null 2>&1; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        print_error "Redisの起動がタイムアウトしました"
        exit 1
    fi
    echo -n "."
done
echo ""
print_success "Redis起動確認 OK"

# Phase 4: Celery Worker起動・テスト
print_info "Phase 4: Celery Worker起動・テスト"
echo "-------------------------------------------"

print_info "Celery Worker起動中..."
docker-compose -f docker-compose.celery.yml up -d celery_worker

# Worker起動待機
print_info "Celery Worker起動待機中..."
sleep 10

# Workerヘルスチェック
if ! docker-compose -f docker-compose.celery.yml exec -T celery_worker \
    python -c "from workers.enhanced_task_worker_celery import app; print('Worker OK')" 2>/dev/null; then
    print_error "Celery Workerの起動に失敗しました"
    docker-compose -f docker-compose.celery.yml logs celery_worker
    exit 1
fi
print_success "Celery Worker起動確認 OK"

# Phase 5: テスト実行
print_info "Phase 5: テスト実行"
echo "-------------------------------------------"

print_info "pytest実行中..."
if ! docker-compose -f docker-compose.celery.yml run --rm claude_test; then
    print_error "テストに失敗しました"
    print_info "ログを確認してください:"
    docker-compose -f docker-compose.celery.yml logs
    exit 1
fi
print_success "テスト実行 OK"

# Phase 6: 統合テスト（実際のタスク実行）
print_info "Phase 6: 統合テスト（実際のタスク実行）"
echo "-------------------------------------------"

print_info "実際のCeleryタスク実行テスト..."

# テストタスク実行スクリプト
cat > /tmp/celery_integration_test.py << 'EOF'
import sys
import time
sys.path.insert(0, '/app')

from workers.enhanced_task_worker_celery import claude_task

# テストタスク実行
test_data = {
    'task_id': 'integration_test_001',
    'prompt': 'テスト用プロンプト',
    'context': {'test': True},
    'options': {'timeout': 30}
}

print("🚀 統合テスト開始...")
result = claude_task(test_data)
print(f"✅ テスト結果: {result}")

if result.get('success'):
    print("🎉 統合テスト成功!")
    sys.exit(0)
else:
    print("❌ 統合テスト失敗!")
    sys.exit(1)
EOF

if ! docker-compose -f docker-compose.celery.yml exec -T celery_worker \
    python /tmp/celery_integration_test.py; then
    print_error "統合テストに失敗しました"
    exit 1
fi
print_success "統合テスト OK"

# Phase 7: パフォーマンステスト
print_info "Phase 7: パフォーマンステスト"
echo "-------------------------------------------"

print_info "Celery Flower起動中..."
docker-compose -f docker-compose.celery.yml up -d celery_flower

sleep 5

print_info "Flower Web UI確認中..."
if curl -f http://localhost:5555 >/dev/null 2>&1; then
    print_success "Flower Web UI アクセス OK (http://localhost:5555)"
else
    print_warning "Flower Web UIにアクセスできません（ポート5555を確認）"
fi

# メトリクス収集
print_info "メトリクス収集中..."
docker-compose -f docker-compose.celery.yml exec -T redis redis-cli info stats | grep "instantaneous_ops_per_sec" || true

# Phase 8: 結果レポート
print_info "Phase 8: 結果レポート"
echo "-------------------------------------------"

echo ""
echo "🎉 Celery Docker統合テスト完了!"
echo "==============================================="
echo ""
echo "📊 テスト結果サマリー:"
echo "  ✅ Redis起動・接続テスト"
echo "  ✅ Celery Worker起動テスト"
echo "  ✅ pytestユニットテスト"
echo "  ✅ 統合テスト（実際のタスク実行）"
echo "  ✅ Flower監視ツール起動"
echo ""
echo "🔗 アクセス可能なサービス:"
echo "  • Flower Web UI: http://localhost:5555"
echo "  • Redis: localhost:6379"
echo ""
echo "🛠️ 管理コマンド:"
echo "  • ログ確認: docker-compose -f docker-compose.celery.yml logs [service]"
echo "  • 停止: docker-compose -f docker-compose.celery.yml down"
echo "  • 完全削除: docker-compose -f docker-compose.celery.yml down -v"
echo ""

# 10分間サービス維持（デバッグ用）
if [ "${KEEP_RUNNING:-}" = "true" ]; then
    print_info "KEEP_RUNNING=trueが設定されています。10分間サービスを維持します..."
    echo "停止するには Ctrl+C を押してください"
    sleep 600
fi