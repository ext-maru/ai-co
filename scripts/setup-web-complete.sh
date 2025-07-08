#!/bin/bash
# AI Company Web完全セットアップスクリプト
# Phase 1 + Phase 2 + Phase 3 を統合

set -e

PROJECT_ROOT="/home/aicompany/ai_co"
SCRIPT_DIR="$PROJECT_ROOT/scripts"

echo "🚀 AI Company Web 完全セットアップ開始..."
echo "========================================"

# Phase 1: 即座の改善（完了済み）
echo "✅ Phase 1: 即座の改善 - 完了済み"
echo "  - dashboard_server.py ポート5555対応"
echo "  - ai-webui コマンド実装"
echo "  - ai-start --web オプション追加"
echo ""

# Phase 2: Apache化
echo "🌐 Phase 2: Apache化を開始..."
read -p "Apache設定を実行しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Apache設定を実行中..."
    bash "$SCRIPT_DIR/setup-apache.sh"
    echo "✅ Apache設定完了"
else
    echo "⏭️  Apache設定をスキップしました"
fi
echo ""

# Phase 3: systemd サービス化
echo "🔧 Phase 3: systemd サービス化を開始..."
read -p "systemdサービス設定を実行しますか？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 systemdサービス設定を実行中..."
    bash "$SCRIPT_DIR/setup-systemd.sh"
    echo "✅ systemdサービス設定完了"
else
    echo "⏭️  systemdサービス設定をスキップしました"
fi
echo ""

# 最終確認とテスト
echo "🧪 セットアップ確認とテスト"
echo "=========================="

# 設定ファイルの存在確認
echo "📄 設定ファイル確認:"
files_to_check=(
    "web/dashboard_server.py"
    "web/flask_app.py"
    "web/app.wsgi"
    "config/apache-aicompany.conf"
    "config/aicompany.service"
    "scripts/ai-webui"
    "bin/ai-start"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - 見つかりません"
    fi
done
echo ""

# 権限確認
echo "🔒 実行権限確認:"
executable_files=(
    "scripts/ai-webui"
    "scripts/setup-apache.sh"
    "scripts/setup-systemd.sh"
    "bin/ai-start"
    "web/app.wsgi"
)

for file in "${executable_files[@]}"; do
    if [ -x "$PROJECT_ROOT/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ⚠️  $file - 実行権限なし"
        chmod +x "$PROJECT_ROOT/$file" 2>/dev/null || true
    fi
done
echo ""

# サービス可用性確認
echo "🔍 サービス可用性確認:"

# Python依存関係
if python3 -c "import flask" 2>/dev/null; then
    echo "  ✅ Flask"
else
    echo "  ❌ Flask - pip install flask"
fi

if python3 -c "import psutil" 2>/dev/null; then
    echo "  ✅ psutil"
else
    echo "  ❌ psutil - pip install psutil"
fi

if python3 -c "import pika" 2>/dev/null; then
    echo "  ✅ pika"
else
    echo "  ❌ pika - pip install pika"
fi

# Apache
if command -v apache2 >/dev/null 2>&1; then
    echo "  ✅ Apache2"
else
    echo "  ❌ Apache2 - sudo apt install apache2"
fi

# RabbitMQ
if systemctl is-active --quiet rabbitmq-server 2>/dev/null; then
    echo "  ✅ RabbitMQ (動作中)"
elif systemctl is-enabled --quiet rabbitmq-server 2>/dev/null; then
    echo "  ⚠️  RabbitMQ (停止中)"
else
    echo "  ❌ RabbitMQ - インストールまたは有効化が必要"
fi
echo ""

# 使用方法ガイド
echo "📚 使用方法ガイド"
echo "================"
echo ""
echo "🎯 起動方法:"
echo "  1. 標準起動: ai-start"
echo "  2. Web付き起動: ai-start --web"
echo "  3. Webのみ起動: ai-webui"
echo "  4. systemdサービス: sudo systemctl start aicompany"
echo ""
echo "🌐 アクセス方法:"
echo "  - 直接アクセス: http://localhost:5555"
echo "  - Apache WSGI: http://aicompany.local"
echo "  - Apacheプロキシ: http://aicompany-proxy.local:8080"
echo ""
echo "🔧 管理コマンド:"
echo "  - システム状態: ai-status"
echo "  - ログ確認: ai-logs"
echo "  - サービス状態: sudo systemctl status aicompany"
echo "  - Apacheログ: sudo tail -f /var/log/apache2/aicompany_*.log"
echo ""
echo "🆘 トラブルシューティング:"
echo "  - ポート競合: sudo netstat -tulpn | grep :5555"
echo "  - Apache設定テスト: sudo apache2ctl configtest"
echo "  - Python環境確認: which python3 && python3 --version"
echo "  - 仮想環境確認: source venv/bin/activate && which python"
echo ""

echo "🎉 AI Company Web 完全セットアップ完了！"
echo ""
echo "📋 次のステップ:"
echo "  1. 'ai-start --web' でシステムを起動"
echo "  2. http://localhost:5555 でダッシュボードにアクセス"
echo "  3. 必要に応じてApache設定やSSL証明書を追加"
echo "  4. systemdサービスで自動起動を設定"