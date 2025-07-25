#!/bin/bash
# 🚀 自動イシュー処理システム - リアルタイム監視ダッシュボード起動スクリプト
# エルダーズギルド評議会承認済み

set -e

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🏛️ エルダーズギルド - 自動イシュー処理監視ダッシュボード"
echo "🚀 Starting Realtime Monitoring Dashboard..."

# 仮想環境確認
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating a virtual environment first"
fi

# 必要なパッケージ確認
echo "📦 Checking required packages..."
python3 -c "
import sys
required_packages = ['flask', 'flask_socketio', 'sqlite3']
missing = []

for package in required_packages:
    try:
        __import__(package)
        print(f'✅ {package}: OK')
    except ImportError:
        missing.append(package)
        print(f'❌ {package}: Missing')

if missing:
    print(f'\\n📥 Install missing packages:')
    if 'flask' in missing or 'flask_socketio' in missing:
        print('pip install flask flask-socketio')
    sys.exit(1)
else:
    print('✅ All required packages are available')
"

# 環境変数確認
echo "🔧 Checking environment variables..."
if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "❌ GITHUB_TOKEN not set"
    exit 1
else
    echo "✅ GITHUB_TOKEN: Set"
fi

if [[ -z "$GITHUB_REPO_OWNER" ]]; then
    echo "⚠️  GITHUB_REPO_OWNER not set, using default: ext-maru"
    export GITHUB_REPO_OWNER="ext-maru"
else
    echo "✅ GITHUB_REPO_OWNER: $GITHUB_REPO_OWNER"
fi

if [[ -z "$GITHUB_REPO_NAME" ]]; then
    echo "⚠️  GITHUB_REPO_NAME not set, using default: ai-co"
    export GITHUB_REPO_NAME="ai-co"
else
    echo "✅ GITHUB_REPO_NAME: $GITHUB_REPO_NAME"
fi

# ログディレクトリ作成
mkdir -p "$PROJECT_ROOT/logs"

# Host and Port configuration
DASHBOARD_HOST="${DASHBOARD_HOST:-0.0.0.0}"
DASHBOARD_PORT="${DASHBOARD_PORT:-5000}"

echo "🌐 Dashboard will be available at:"
echo "   http://localhost:$DASHBOARD_PORT"
echo "   http://$DASHBOARD_HOST:$DASHBOARD_PORT"
echo ""

# ダッシュボード起動
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo "🚀 Starting dashboard..."
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from libs.integrations.github.realtime_dashboard import run_dashboard

print('🏛️ エルダーズギルド リアルタイム監視ダッシュボード')
print('📊 Auto Issue Processor Monitoring System')
print('⏰ Real-time metrics updating every 5 seconds')
print('')
print('💡 Usage:')
print('   - F5 or Ctrl+R: Manual refresh')
print('   - Ctrl+C: Stop dashboard')
print('')

try:
    run_dashboard(host='$DASHBOARD_HOST', port=$DASHBOARD_PORT, debug=False)
except KeyboardInterrupt:
    print('\\n🛑 Dashboard stopped by user')
except Exception as e:
    print(f'❌ Dashboard error: {e}')
    sys.exit(1)
"