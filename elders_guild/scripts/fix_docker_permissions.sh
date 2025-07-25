#!/bin/bash
# Docker権限問題の根本解決スクリプト

set -e

echo "🛠️ Docker権限問題の根本解決を開始します"

# 現在のグループ確認
echo "現在のグループ:"
groups

# Docker グループ確認
if getent group docker >/dev/null 2>&1; then
    echo "✅ dockerグループが存在します"
else
    echo "❌ dockerグループが存在しません"
    exit 1
fi

# ユーザーがdockerグループに所属しているか確認
if groups | grep -q docker; then
    echo "✅ ユーザーは既にdockerグループに所属しています"
else
    echo "❌ ユーザーがdockerグループに所属していません"
    echo "以下のコマンドを管理者権限で実行してください:"
    echo "sudo usermod -aG docker $USER"
    exit 1
fi

# Docker socket権限確認
echo "Docker socket権限:"
ls -la /var/run/docker.sock

# Docker デーモン確認
if systemctl is-active --quiet docker; then
    echo "✅ Docker デーモンが実行中です"
else
    echo "❌ Docker デーモンが停止しています"
    echo "以下のコマンドで起動してください:"
    echo "sudo systemctl start docker"
    exit 1
fi

# sg コマンドでテスト
echo "🧪 Docker アクセステスト (sg使用):"
if sg docker -c "docker ps" >/dev/null 2>&1; then
    echo "✅ sg docker で Docker にアクセス可能"
    echo "✨ 今後は 'sg docker -c \"docker コマンド\"' 形式で使用してください"
else
    echo "❌ sg docker でもアクセスできません"
    exit 1
fi

echo ""
echo "🎉 Docker権限設定が完了しました！"
echo ""
echo "📋 使用方法:"
echo "  通常のdockerコマンド: sg docker -c \"docker ps\""
echo "  Docker Compose: sg docker -c \"docker compose up -d\""
echo ""
echo "💡 新しいシェルセッションでは通常のdockerコマンドが使用可能になる場合があります"
echo "   ログアウト→ログインまたは 'newgrp docker' を試してください"
