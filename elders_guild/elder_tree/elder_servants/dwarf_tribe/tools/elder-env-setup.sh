#!/bin/bash
# 🏛️ Elder Tree Environment Setup
# 綺麗で保守性の高いパス管理システム（シンボリックリンク不使用）

set -e

ELDER_ROOT="/home/aicompany/ai_co/elders_guild/elder_tree"
BASHRC_FILE="$HOME/.bashrc"
SETUP_MARKER="# Elder Tree Environment Setup"

echo "🏛️ Elder Tree Environment Setup"
echo "================================="

# Elder Tree環境変数とPATH設定
setup_environment() {
    echo "📝 環境変数設定を追加中..."
    
    # 既存設定をチェック
    if grep -q "$SETUP_MARKER" "$BASHRC_FILE"; then
        echo "⚠️ Elder Tree環境設定が既に存在します。更新中..."
        # 既存設定を削除
        sed -i "/$SETUP_MARKER/,/# End Elder Tree Setup/d" "$BASHRC_FILE"
    fi
    
    # 新しい設定を追加
    cat >> "$BASHRC_FILE" << EOF

$SETUP_MARKER
# Elder Tree Paths
export ELDER_HOME="$ELDER_ROOT"
export ELDER_TOOLS="\$ELDER_HOME/elder_servants/dwarf_tribe/tools"
export ELDER_SAGES="\$ELDER_HOME/four_sages"
export ELDER_SERVANTS="\$ELDER_HOME/elder_servants"
export ELDER_CLAUDE="\$ELDER_HOME/claude_elder"
export ELDER_ANCIENT="\$ELDER_HOME/ancient_elder"

# PATH additions
export PATH="\$PATH:\$ELDER_TOOLS"

# Elder Tree Aliases
alias elder-home='cd \$ELDER_HOME'
alias elder-tools='cd \$ELDER_TOOLS && ls -la'
alias elder-sages='cd \$ELDER_SAGES'
alias elder-servants='cd \$ELDER_SERVANTS'

# Quality System Shortcuts
alias quality-check='\$ELDER_TOOLS/auto-install-quality-system'
alias git-feature='\$ELDER_TOOLS/git-feature'
alias pr-quality='\$ELDER_TOOLS/pr-quality-check' 
alias elder-health='\$ELDER_TOOLS/health_check.sh'

# Elder Flow Shortcuts
alias elder-flow='elder-flow execute'
alias elder-status='elder-flow active'

# Development Shortcuts
alias elder-test='cd \$ELDER_HOME && pytest \$ELDER_SERVANTS/quality_tribe/tests/'
alias elder-migrate='\$ELDER_TOOLS/complete_elder_tree_migration.py'

# Elder CLI Function
elder() {
    case "\$1" in
        "tools")
            shift
            "\$ELDER_TOOLS/\$@"
            ;;
        "sages")
            shift
            cd "\$ELDER_SAGES"
            python3 -m "\$@"
            ;;
        "test")
            shift
            cd "\$ELDER_HOME"
            pytest "\$ELDER_SERVANTS/quality_tribe/tests/\$@"
            ;;
        "quality")
            shift
            "\$ELDER_TOOLS/\$@"
            ;;
        *)
            echo "Elder CLI Usage:"
            echo "  elder tools <command> [args...]    - Run dwarf tribe tools"
            echo "  elder sages <sage> [args...]       - Run four sages"
            echo "  elder test [test_path]             - Run tests"
            echo "  elder quality <command> [args...]  - Run quality tools"
            echo ""
            echo "Available shortcuts:"
            echo "  elder-home, elder-tools, elder-sages"
            echo "  quality-check, git-feature, pr-quality"
            echo "  elder-flow, elder-status, elder-test"
            ;;
    esac
}

# End Elder Tree Setup
EOF

    echo "✅ 環境設定を追加しました"
}

# 設定をテスト
test_setup() {
    echo "🧪 設定をテスト中..."
    
    # 新しいシェルで設定をテスト
    bash -c "
        source '$BASHRC_FILE'
        echo 'ELDER_HOME: \$ELDER_HOME'
        echo 'ELDER_TOOLS: \$ELDER_TOOLS'
        echo 'PATH includes Elder Tools: '
        echo \$PATH | grep -q '\$ELDER_TOOLS' && echo '✅ Yes' || echo '❌ No'
    "
}

# インストールガイド表示
show_usage_guide() {
    echo ""
    echo "🎯 使用方法ガイド"
    echo "================="
    echo ""
    echo "1. 新しいターミナルを開くか、以下を実行:"
    echo "   source ~/.bashrc"
    echo ""
    echo "2. 基本コマンド:"
    echo "   elder tools git-feature 17 data-model"
    echo "   elder tools auto-install-quality-system"  
    echo "   elder test"
    echo "   quality-check"
    echo "   git-feature 17 data-model"
    echo ""
    echo "3. ディレクトリ移動:"
    echo "   elder-home    # Elder Tree ルートへ"
    echo "   elder-tools   # ツールディレクトリへ"
    echo "   elder-sages   # 4賢者ディレクトリへ"
    echo ""
    echo "4. 開発作業:"
    echo "   elder-flow 'タスク名'"
    echo "   elder-test"
    echo "   elder-health"
    echo ""
}

# メイン実行
main() {
    echo "Elder Tree ディレクトリ存在確認..."
    if [[ ! -d "$ELDER_ROOT" ]]; then
        echo "❌ Elder Tree ディレクトリが存在しません: $ELDER_ROOT"
        echo "💡 先にElder Tree移行を実行してください"
        exit 1
    fi
    
    echo "✅ Elder Tree ディレクトリ確認完了"
    
    setup_environment
    test_setup
    show_usage_guide
    
    echo ""
    echo "🎉 Elder Tree Environment Setup 完了！"
    echo "💡 新しいターミナルを開くか 'source ~/.bashrc' を実行してください"
}

main "$@"