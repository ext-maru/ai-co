#!/bin/bash
# AI Command System - エイリアス設定スクリプト
# エルダー評議会承認済み (2025年7月9日)

echo "🚀 AI Command System エイリアス設定"
echo "=================================="

# Detect shell
SHELL_RC=""
SHELL_NAME=""

if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo "❌ Unsupported shell. Please manually add aliases."
    exit 1
fi

echo "📄 検出されたシェル: $SHELL_NAME"
echo "📝 設定ファイル: $SHELL_RC"

# Backup existing rc file
if [ -f "$SHELL_RC" ]; then
    cp "$SHELL_RC" "$SHELL_RC.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ バックアップ作成完了"
fi

# Add aliases section
cat >> "$SHELL_RC" << 'EOF'

# ===========================================
# AI Command System Aliases
# Elder Council Approved - 2025-07-09
# ===========================================

# Core shortcuts
alias ais='ai status'
alias aih='ai help'
alias aist='ai start'
alias aisp='ai stop'

# Elder shortcuts
alias aie='ai elder'
alias aies='ai elder status'
alias aiec='ai elder council'
alias aiet='ai elder tree'
alias aieset='ai elder settings'

# Worker shortcuts
alias aiw='ai worker'
alias aiws='ai worker status'
alias aiwr='ai worker recovery'

# Development shortcuts
alias aid='ai dev'
alias aidc='ai dev codegen'
alias aidd='ai dev document'
alias aidt='ai dev tdd'

# Test shortcuts
alias ait='ai test'
alias aitc='ai test coverage'
alias aitq='ai test quality'
alias aitr='ai test runner'

# Operations shortcuts
alias aio='ai ops'
alias aiod='ai ops dashboard'
alias aios='ai ops api-status'

# Monitor shortcuts
alias aim='ai monitor'
alias aiml='ai monitor logs'

# Quick access functions
aif() {
    # AI Find shortcut
    ai find "$@"
}

# Legacy compatibility with warnings
ai-elder() {
    echo "⚠️  Please use: ai elder" >&2
    ai elder "$@"
}

ai-worker() {
    echo "⚠️  Please use: ai worker" >&2
    ai worker "$@"
}

ai-test() {
    echo "⚠️  Please use: ai test" >&2
    ai test "$@"
}

# Show available AI commands
ai-shortcuts() {
    echo "🚀 AI Command System Shortcuts:"
    echo ""
    echo "Core:"
    echo "  ais    → ai status"
    echo "  aist   → ai start"
    echo "  aisp   → ai stop"
    echo ""
    echo "Elder:"
    echo "  aie    → ai elder"
    echo "  aies   → ai elder status"
    echo "  aiec   → ai elder council"
    echo ""
    echo "Worker:"
    echo "  aiw    → ai worker"
    echo "  aiws   → ai worker status"
    echo ""
    echo "Dev/Test:"
    echo "  aid    → ai dev"
    echo "  ait    → ai test"
    echo ""
    echo "Search:"
    echo "  aif <query> → ai find <query>"
}

EOF

echo ""
echo "✅ エイリアス設定完了!"
echo ""
echo "📋 設定を有効にするには:"
echo "   source $SHELL_RC"
echo ""
echo "または新しいターミナルを開いてください。"
echo ""
echo "💡 利用可能なショートカットを確認:"
echo "   ai-shortcuts"
echo ""
echo "🔍 例:"
echo "   ais     # ai status"
echo "   aies    # ai elder status"
echo "   aif test # ai find test"