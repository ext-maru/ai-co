#!/bin/bash
#
# AI Company Commands インストールスクリプト
#

set -e

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 AI Company Commands セットアップ${NC}"
echo "=================================="

# プロジェクトディレクトリ確認
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo -e "プロジェクトディレクトリ: ${YELLOW}$PROJECT_DIR${NC}"

# 実行権限付与
echo -e "\n${YELLOW}1. 実行権限を設定中...${NC}"
chmod +x "$PROJECT_DIR/bin/"*
chmod +x "$PROJECT_DIR/commands/"*.py
echo -e "${GREEN}✅ 完了${NC}"

# シンボリックリンク作成
echo -e "\n${YELLOW}2. コマンドをインストール中...${NC}"

# インストール先
INSTALL_DIR="/usr/local/bin"

# 既存のコマンドをバックアップ（存在する場合）
for cmd in "$PROJECT_DIR/bin/"*; do
    cmd_name=$(basename "$cmd")
    if [ -L "$INSTALL_DIR/$cmd_name" ] || [ -f "$INSTALL_DIR/$cmd_name" ]; then
        echo -e "  ${YELLOW}既存の $cmd_name をバックアップ${NC}"
        sudo mv "$INSTALL_DIR/$cmd_name" "$INSTALL_DIR/$cmd_name.bak" 2>/dev/null || true
    fi
done

# 新しいシンボリックリンク作成
for cmd in "$PROJECT_DIR/bin/"*; do
    cmd_name=$(basename "$cmd")
    sudo ln -sf "$cmd" "$INSTALL_DIR/$cmd_name"
    echo -e "  ${GREEN}✅${NC} $cmd_name"
done

# 追加の便利なエイリアス
echo -e "\n${YELLOW}3. エイリアスを設定中...${NC}"

# ai コマンド（メインエントリーポイント）
cat > "$PROJECT_DIR/bin/ai" << 'EOF'
#!/bin/bash
# AI Company メインコマンド

if [ $# -eq 0 ]; then
    echo "AI Company Command Line Interface"
    echo "=================================="
    echo ""
    echo "使用方法: ai <command> [options]"
    echo ""
    echo "基本コマンド:"
    echo "  status    - システム状態確認"
    echo "  send      - タスク送信"
    echo "  code      - コード生成タスク（sendのショートカット）"
    echo "  tasks     - タスク一覧・履歴"
    echo "  workers   - ワーカー管理"
    echo ""
    echo "詳細: ai <command> --help"
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    status|send|code|tasks|workers)
        exec ai-$COMMAND "$@"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run 'ai' for help"
        exit 1
        ;;
esac
EOF

chmod +x "$PROJECT_DIR/bin/ai"
sudo ln -sf "$PROJECT_DIR/bin/ai" "$INSTALL_DIR/ai"
echo -e "  ${GREEN}✅${NC} ai (メインコマンド)"

# 短縮エイリアス
echo -e "\n${YELLOW}4. 短縮エイリアスを作成中...${NC}"

# aic = ai code
cat > "$PROJECT_DIR/bin/aic" << 'EOF'
#!/bin/bash
exec ai-code "$@"
EOF
chmod +x "$PROJECT_DIR/bin/aic"
sudo ln -sf "$PROJECT_DIR/bin/aic" "$INSTALL_DIR/aic"
echo -e "  ${GREEN}✅${NC} aic → ai-code"

# ais = ai status  
cat > "$PROJECT_DIR/bin/ais" << 'EOF'
#!/bin/bash
exec ai-status "$@"
EOF
chmod +x "$PROJECT_DIR/bin/ais"
sudo ln -sf "$PROJECT_DIR/bin/ais" "$INSTALL_DIR/ais"
echo -e "  ${GREEN}✅${NC} ais → ai-status"

# ait = ai tasks
cat > "$PROJECT_DIR/bin/ait" << 'EOF'
#!/bin/bash
exec ai-tasks "$@"
EOF
chmod +x "$PROJECT_DIR/bin/ait"
sudo ln -sf "$PROJECT_DIR/bin/ait" "$INSTALL_DIR/ait"
echo -e "  ${GREEN}✅${NC} ait → ai-tasks"

# aiw = ai workers
cat > "$PROJECT_DIR/bin/aiw" << 'EOF'
#!/bin/bash
exec ai-workers "$@"
EOF
chmod +x "$PROJECT_DIR/bin/aiw"
sudo ln -sf "$PROJECT_DIR/bin/aiw" "$INSTALL_DIR/aiw"
echo -e "  ${GREEN}✅${NC} aiw → ai-workers"

# コマンド一覧表示
echo -e "\n${GREEN}✨ インストール完了！${NC}"
echo -e "\n利用可能なコマンド:"
echo -e "  ${YELLOW}ai${NC}         - メインコマンド（ヘルプ表示）"
echo -e "  ${YELLOW}ai-status${NC}  - システム状態確認"
echo -e "  ${YELLOW}ai-send${NC}    - タスク送信" 
echo -e "  ${YELLOW}ai-code${NC}    - コード生成タスク"
echo -e "  ${YELLOW}ai-tasks${NC}   - タスク一覧・履歴"
echo -e "  ${YELLOW}ai-workers${NC} - ワーカー管理"
echo -e "\n短縮エイリアス:"
echo -e "  ${YELLOW}aic${NC} = ai-code"
echo -e "  ${YELLOW}ais${NC} = ai-status"
echo -e "  ${YELLOW}ait${NC} = ai-tasks"
echo -e "  ${YELLOW}aiw${NC} = ai-workers"

echo -e "\n${GREEN}試してみましょう:${NC}"
echo -e "  ${YELLOW}ai${NC}          # ヘルプ表示"
echo -e "  ${YELLOW}ais${NC}         # システム状態"
echo -e "  ${YELLOW}aic \"Hello World を出力するPythonコード\"${NC}"
