#!/bin/bash
"""
AI Evolution Cron Commands Installer
AI進化システムのCron関連コマンドをシステムに登録する

使用方法:
  sudo bash scripts/install_cron_commands.sh
"""

set -e

PROJECT_ROOT="/home/aicompany/ai_co"
BIN_DIR="/usr/local/bin"

echo "🔧 AI Evolution Cron Commands インストール開始"

# 実行権限確認
if [ "$EUID" -ne 0 ]; then
    echo "❌ このスクリプトはroot権限で実行してください"
    echo "使用方法: sudo bash $0"
    exit 1
fi

# コマンドファイルの存在確認
commands_to_install=(
    "ai-evolution-cron"
)

echo "📋 インストール対象コマンド確認中..."
for cmd in "${commands_to_install[@]}"; do
    if [ -f "$PROJECT_ROOT/scripts/$cmd" ]; then
        echo "  ✅ $cmd - 見つかりました"
    else
        echo "  ❌ $cmd - 見つかりません"
        exit 1
    fi
done

# シンボリックリンク作成
echo "🔗 シンボリックリンク作成中..."
for cmd in "${commands_to_install[@]}"; do
    source_path="$PROJECT_ROOT/scripts/$cmd"
    target_path="$BIN_DIR/$cmd"

    # 既存のリンクがあれば削除
    if [ -L "$target_path" ]; then
        rm "$target_path"
        echo "  🗑️ 既存のリンクを削除: $target_path"
    fi

    # 新しいシンボリックリンク作成
    ln -sf "$source_path" "$target_path"
    echo "  🔗 シンボリックリンク作成: $cmd"

    # 実行権限確認
    chmod +x "$source_path"
done

# インストール確認
echo ""
echo "✅ インストール完了確認:"
for cmd in "${commands_to_install[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "  ✅ $cmd - インストール成功"
        echo "     場所: $(which $cmd)"
    else
        echo "  ❌ $cmd - インストール失敗"
    fi
done

echo ""
echo "🎉 AI Evolution Cron Commands インストール完了！"
echo ""
echo "📋 利用可能なコマンド:"
echo "  ai-evolution-cron setup    # Cron設定セットアップ"
echo "  ai-evolution-cron status   # システム状況確認"
echo "  ai-evolution-cron logs     # ログ確認"
echo "  ai-evolution-cron test     # システムテスト"
echo "  ai-evolution-cron monitor  # リアルタイム監視"
echo ""
echo "🚀 次のステップ:"
echo "  1. ai-evolution-cron setup  # Cron設定を行う"
echo "  2. ai-evolution-cron status # 設定確認"
echo "  3. ai-evolution-cron test   # システムテスト"
echo ""
echo "⚡ AI Company完全自律運用の準備が整いました！"
