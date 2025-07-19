#!/bin/bash
# AI Company コマンドシステムセットアップスクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMMANDS_DIR="$PROJECT_ROOT/commands"
BIN_DIR="$PROJECT_ROOT/bin"

echo "🚀 AI Company コマンドシステムセットアップ"
echo "=========================================="

# 1. 実行権限付与
echo "📝 実行権限を設定中..."
chmod +x "$BIN_DIR/ai_launcher.py"

# 2. コマンドリスト定義
COMMANDS=(
    "ai-start"
    "ai-stop"
    "ai-restart"
    "ai-status"
    "ai-health"
    "ai-send"
    "ai-code"
    "ai-dialog"
    "ai-reply"
    "ai-logs"
    "ai-monitor"
    "ai-workers"
    "ai-worker-add"
    "ai-worker-rm"
    "ai-worker-scale"
    "ai-worker-restart"
    "ai-tasks"
    "ai-task-info"
    "ai-task-cancel"
    "ai-task-retry"
    "ai-queue"
    "ai-queue-clear"
    "ai-rag"
    "ai-rag-search"
    "ai-evolve"
    "ai-evolve-test"
    "ai-learn"
    "ai-config"
    "ai-config-edit"
    "ai-config-reload"
    "ai-conversations"
    "ai-conv-info"
    "ai-conv-resume"
    "ai-conv-export"
    "ai-stats"
    "ai-report"
    "ai-export"
    "ai-backup"
    "ai-clean"
    "ai-debug"
    "ai-test"
    "ai-shell"
    "ai-simulate"
    "ai"
    "ai-help"
    "ai-version"
    "ai-update"
)

# 3. シンボリックリンク作成
echo "🔗 コマンドリンクを作成中..."
for cmd in "${COMMANDS[@]}"; do
    # binディレクトリにラッパー作成
    cat > "$BIN_DIR/$cmd" << EOF
#!/bin/bash
exec "$BIN_DIR/ai_launcher.py" "\$@"
EOF
    chmod +x "$BIN_DIR/$cmd"

    # /usr/local/binにシンボリックリンク
    if [ -w /usr/local/bin ]; then
        sudo ln -sf "$BIN_DIR/$cmd" "/usr/local/bin/$cmd"
        echo "  ✅ $cmd"
    fi
done

# 4. エイリアス設定
echo ""
echo "📝 エイリアス設定..."
ALIAS_FILE="$PROJECT_ROOT/commands/aliases.sh"
cat > "$ALIAS_FILE" << 'EOF'
# AI Company コマンドエイリアス
alias aic='ai-code'
alias aid='ai-dialog'
alias ais='ai-status'
alias ail='ai-logs'
alias aiw='ai-workers'
alias ai-quick='ai-send "$@" code'
alias ai-chat='ai-dialog'
alias ai-check='ai-health'
EOF

# bashrcに追加
if ! grep -q "AI Company aliases" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# AI Company aliases" >> ~/.bashrc
    echo "source $ALIAS_FILE" >> ~/.bashrc
    echo "  ✅ ~/.bashrc にエイリアス追加"
fi

# 5. 基本コマンドの実装状況確認
echo ""
echo "📊 実装状況確認..."
IMPLEMENTED=(
    "ai_status.py"
    "ai_tasks.py"
)

NEEDED=(
    "ai_start.py"
    "ai_stop.py"
    "ai_send.py"
    "ai_workers.py"
    "ai_health.py"
    "ai_rag.py"
    "ai_config.py"
)

echo "  実装済み:"
for impl in "${IMPLEMENTED[@]}"; do
    if [ -f "$COMMANDS_DIR/$impl" ]; then
        echo "    ✅ $impl"
    fi
done

echo "  未実装（作成予定）:"
for need in "${NEEDED[@]}"; do
    if [ ! -f "$COMMANDS_DIR/$need" ]; then
        echo "    ⏳ $need"
    fi
done

# 6. テスト実行
echo ""
echo "🧪 動作テスト..."
if command -v ai-status &> /dev/null; then
    echo "  ✅ コマンドパスOK"
else
    echo "  ❌ コマンドパスNG - 'source ~/.bashrc' を実行してください"
fi

echo ""
echo "✨ セットアップ完了！"
echo ""
echo "使用方法:"
echo "  ai-status    - システム状態確認"
echo "  ai-tasks     - タスク一覧"
echo "  ai-help      - ヘルプ表示"
echo ""
echo "新しいターミナルを開くか、以下を実行してください:"
echo "  source ~/.bashrc"
