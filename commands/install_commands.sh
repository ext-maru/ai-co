#!/bin/bash
# AI Company コマンドインストールスクリプト

set -e

echo "🚀 AI Company コマンドインストール"
echo "=================================="

# プロジェクトディレクトリ
PROJECT_DIR="/home/aicompany/ai_co"
BIN_DIR="$PROJECT_DIR/bin"
COMMANDS_DIR="$PROJECT_DIR/commands"

# 実行権限付与
echo "📝 実行権限設定中..."
chmod +x $BIN_DIR/ai-*
chmod +x $COMMANDS_DIR/*.py

# シンボリックリンク作成
echo "🔗 シンボリックリンク作成中..."
for cmd in $BIN_DIR/ai-*; do
    # ai-venvはsource用なので特別処理
    if [[ "$(basename $cmd)" == "ai-venv" ]]; then
        # source用スクリプトは直接コピー
        echo "  - ai-venv (source用)"
        sudo cp $cmd /usr/local/bin/ai-venv
        sudo chmod +x /usr/local/bin/ai-venv
    elif [[ "$(basename $cmd)" == "ai-venv-helper" ]]; then
        # ヘルパーはai-venvコマンドとしてリンク
        echo "  - ai-venv (通常実行用)"
        sudo ln -sf $cmd /usr/local/bin/ai-venv
    elif [[ "$(basename $cmd)" != "ai-venv-cmd" ]]; then
        # その他のコマンド
        cmd_name=$(basename $cmd)
        echo "  - $cmd_name"
        sudo ln -sf $cmd /usr/local/bin/$cmd_name
    fi
done

# 既存の古いコマンドを削除
echo "🧹 古いコマンドをクリーンアップ..."
OLD_COMMANDS=(
    "/usr/local/bin/ai-reply"
    "/usr/local/bin/ai-dialog"
    "/usr/local/bin/ai-logs"
)

for old_cmd in "${OLD_COMMANDS[@]}"; do
    if [ -L "$old_cmd" ] || [ -f "$old_cmd" ]; then
        echo "  - 削除: $old_cmd"
        sudo rm -f "$old_cmd"
    fi
done

# 確認
echo ""
echo "✅ インストール完了！"
echo ""
echo "利用可能なコマンド:"
echo "  [基本コマンド]"
echo "  ai-start   - システム起動"
echo "  ai-stop    - システム停止"
echo "  ai-status  - 状態確認"
echo "  ai-send    - タスク送信"
echo ""
echo "  [新コマンド]"
echo "  ai-dialog  - 対話型タスク開始"
echo "  ai-reply   - 対話応答送信"
echo "  ai-logs    - ログ確認"
echo "  ai-tasks   - タスク一覧・履歴"
echo "  ai-venv    - 仮想環境管理"
echo ""
echo "使用例:"
echo "  ai-send \"Pythonでフィボナッチ数列を生成\" code"
echo "  ai-dialog \"複雑なWebアプリを作成したい\""
echo "  ai-logs task -f --grep ERROR"
echo "  ai-tasks --type code --limit 5"
echo "  ai-venv --info  # 仮想環境情報"
echo "  source /usr/local/bin/ai-venv  # 仮想環境アクティベート"
echo ""
