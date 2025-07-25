#!/bin/bash
# 🏛️ Elder Command セットアップスクリプト
# ai-* コマンドを elder に移行

set -e

echo "🏛️ Elder Command システムセットアップ開始"

# 色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# プロジェクトルート
PROJECT_ROOT="/home/aicompany/ai_co"
BIN_DIR="/usr/local/bin"

# ヘルパー関数
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

# Elder CLI インストール
install_elder_cli() {
    log_info "Elder CLI をインストール中..."
    
    # シンボリックリンク作成
    if [ -f "$BIN_DIR/elder" ]; then
        log_warn "既存の elder コマンドを上書きします"
        sudo rm -f "$BIN_DIR/elder"
    fi
    
    sudo ln -s "$PROJECT_ROOT/elders_guild/cli/elder_cli.py" "$BIN_DIR/elder"
    sudo chmod +x "$BIN_DIR/elder"
    
    log_success "Elder CLI インストール完了"
}

# エイリアス作成（移行期間用）
create_aliases() {
    log_info "レガシーコマンドのエイリアス作成中..."
    
    # ai-* コマンドのマッピング
    declare -A command_mapping=(
        ["ai-send"]="elder send"
        ["ai-status"]="elder status"
        ["ai-start"]="elder start"
        ["ai-stop"]="elder stop"
        ["ai-test"]="elder test run"
        ["ai-elder-flow"]="elder flow execute"
        ["ai-elder-council"]="elder council consult"
        ["ai-commit-auto"]="elder commit auto"
        ["ai-commit-lightning"]="elder commit lightning"
        ["ai-logs"]="elder logs"
        ["ai-monitor"]="elder monitor"
        ["ai-config"]="elder config edit"
        ["ai-worker-scale"]="elder worker scale"
        ["ai-rag"]="elder sage rag search"
        ["ai-prophecy"]="elder prophecy"
    )
    
    # エイリアススクリプト作成
    for old_cmd in "${!command_mapping[@]}"; do
        new_cmd="${command_mapping[$old_cmd]}"
        
        if [ -f "$BIN_DIR/$old_cmd" ]; then
            # バックアップ
            sudo mv "$BIN_DIR/$old_cmd" "$BIN_DIR/$old_cmd.bak" 2>/dev/null || true
        fi
        
        # エイリアススクリプト作成
        sudo tee "$BIN_DIR/$old_cmd" > /dev/null << EOF
#!/bin/bash
# 自動生成されたエイリアススクリプト
echo -e "${YELLOW}⚠️ '$old_cmd' は非推奨です。'$new_cmd' を使用してください。${NC}" >&2
echo "" >&2
exec $new_cmd "\$@"
EOF
        
        sudo chmod +x "$BIN_DIR/$old_cmd"
        log_success "エイリアス作成: $old_cmd → $new_cmd"
    done
}

# Bash補完設定
setup_completion() {
    log_info "Bash補完を設定中..."
    
    # 補完スクリプト作成
    cat > /tmp/elder-completion.bash << 'EOF'
# Elder CLI bash completion
_elder_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # メインコマンド
    if [ $COMP_CWORD -eq 1 ]; then
        opts="send status start stop flow sage council test commit help"
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
    
    # サブコマンド
    case "${COMP_WORDS[1]}" in
        flow)
            opts="execute status fix"
            ;;
        sage)
            opts="knowledge task incident rag"
            ;;
        council)
            opts="consult compliance approve"
            ;;
        test)
            opts="run coverage"
            ;;
        commit)
            opts="auto lightning"
            ;;
    esac
    
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
}

complete -F _elder_completion elder
EOF
    
    # システム全体の補完ディレクトリにコピー
    if [ -d "/etc/bash_completion.d" ]; then
        sudo cp /tmp/elder-completion.bash /etc/bash_completion.d/
        log_success "Bash補完設定完了"
    else
        log_warn "Bash補完ディレクトリが見つかりません"
    fi
    
    rm -f /tmp/elder-completion.bash
}

# クイックスタートガイド表示
show_quickstart() {
    cat << EOF

${GREEN}🎉 Elder Command システムセットアップ完了！${NC}

${BLUE}📚 基本的な使い方:${NC}
  elder send "メッセージ"           # AIにメッセージ送信
  elder flow execute "タスク"        # Elder Flow 実行
  elder sage knowledge search "質問" # ナレッジ検索
  elder council consult "相談内容"   # 評議会に相談
  elder help                        # ヘルプ表示

${YELLOW}💡 ヒント:${NC}
  - Tab補完が使えます（新しいシェルで有効）
  - 'elder help [コマンド]' で詳細ヘルプ
  - レガシーコマンド (ai-*) はまだ使えますが非推奨です

${BLUE}📖 詳細ドキュメント:${NC}
  docs/proposals/ELDER_COMMAND_UNIFICATION_PLAN.md

EOF
}

# メイン処理
main() {
    log_info "セットアップ開始..."
    
    # 権限チェック
    if [ "$EUID" -eq 0 ]; then
        log_error "rootユーザーでは実行しないでください"
        exit 1
    fi
    
    # Elder CLI インストール
    install_elder_cli
    
    # エイリアス作成
    create_aliases
    
    # 補完設定
    setup_completion
    
    # 完了メッセージ
    show_quickstart
    
    log_success "セットアップ完了！"
    echo "新しいシェルを開いて 'elder help' を試してください。"
}

# 実行
main "$@"