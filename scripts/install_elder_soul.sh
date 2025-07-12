#!/bin/bash
"""
エルダーの魂 - インストールスクリプト
Elder Soul - Installation Script
"""

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_ROOT/scripts/elder_soul"

echo "🌲 Installing Elder Soul..."
echo "Project Root: $PROJECT_ROOT"

# 1. スクリプトの実行権限設定
echo "📋 Setting permissions..."
chmod +x "$SCRIPT_PATH"

# 2. シンボリックリンク作成（/usr/local/bin）
if [ -w /usr/local/bin ]; then
    echo "🔗 Creating symlink to /usr/local/bin..."
    sudo ln -sf "$SCRIPT_PATH" /usr/local/bin/elder-tree-soul
    echo "✅ Installed to /usr/local/bin/elder-tree-soul"
else
    echo "⚠️  Cannot write to /usr/local/bin (need sudo)"
    echo "   You can create the symlink manually:"
    echo "   sudo ln -sf '$SCRIPT_PATH' /usr/local/bin/elder-tree-soul"
fi

# 3. ローカルインストール（~/.local/bin）
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"
ln -sf "$SCRIPT_PATH" "$LOCAL_BIN/elder-tree-soul"
echo "✅ Installed to $LOCAL_BIN/elder-tree-soul"

# 4. パス設定の確認
echo "📋 Checking PATH configuration..."
if echo "$PATH" | grep -q "$LOCAL_BIN"; then
    echo "✅ $LOCAL_BIN is in PATH"
else
    echo "⚠️  $LOCAL_BIN is not in PATH"
    echo "   Add the following to your shell configuration:"
    echo "   export PATH=\"$LOCAL_BIN:\$PATH\""
fi

# 5. 必要ディレクトリの作成
echo "📁 Creating necessary directories..."
mkdir -p "$PROJECT_ROOT/logs/elders"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/knowledge_base"

# 6. 依存関係チェック
echo "🔍 Checking dependencies..."

# Python確認
if command -v python3 >/dev/null 2>&1; then
    echo "✅ Python3 found: $(python3 --version)"
else
    echo "❌ Python3 not found"
    exit 1
fi

# Redis確認
if command -v redis-server >/dev/null 2>&1; then
    echo "✅ Redis found: $(redis-server --version | head -1)"
else
    echo "⚠️  Redis not found - install with:"
    echo "   sudo apt install redis-server  # Ubuntu/Debian"
    echo "   brew install redis             # macOS"
fi

# Pythonパッケージ確認
echo "📦 Checking Python packages..."
cd "$PROJECT_ROOT"

if [ -f requirements.txt ]; then
    echo "📋 Installing Python dependencies..."
    pip3 install -r requirements.txt
else
    echo "📋 Installing essential packages..."
    pip3 install redis fastapi uvicorn pydantic psutil numpy scikit-learn
fi

# 7. 設定ファイルの作成
echo "⚙️  Creating configuration..."
cat > "$PROJECT_ROOT/.elder_tree_config.json" << EOF
{
    "project_root": "$PROJECT_ROOT",
    "version": "1.0",
    "elders": {
        "grand_elder": {"port": 5000},
        "claude_elder": {"port": 5001},
        "knowledge_sage": {"port": 5002},
        "task_sage": {"port": 5003},
        "rag_sage": {"port": 5004},
        "incident_sage": {"port": 5005}
    },
    "redis": {
        "host": "localhost",
        "port": 6379
    },
    "installation": {
        "date": "$(date -Iseconds)",
        "user": "$USER",
        "hostname": "$HOSTNAME"
    }
}
EOF

echo "✅ Configuration created: .elder_tree_config.json"

# 8. 動作テスト
echo "🧪 Testing installation..."
if "$SCRIPT_PATH" config >/dev/null 2>&1; then
    echo "✅ Elder Soul command working"
else
    echo "❌ Command test failed"
    exit 1
fi

echo ""
echo "🎉 Elder Soul installation completed!"
echo ""
echo "📋 Usage:"
echo "  elder-tree-soul start    # Start all elders"
echo "  elder-tree-soul status   # Check status"
echo "  elder-tree-soul health   # Health check"
echo "  elder-tree-soul stop     # Stop all elders"
echo ""
echo "🚀 To get started:"
echo "  1. Start Redis: redis-server"
echo "  2. Start Elder Tree: elder-tree-soul start"
echo ""
echo "📚 Documentation: $PROJECT_ROOT/docs/"
echo "🌲 May the Elder Soul guide your development!"
