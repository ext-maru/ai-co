#!/bin/bash
# Docker自動起動設定スクリプト

echo "🐳 Docker自動起動設定を開始します..."

# systemdサービスファイルのコピー
echo "📝 systemdサービスファイルをコピー中..."
sudo cp /home/aicompany/ai_co/scripts/docker-auto-start.service /etc/systemd/system/

# systemdデーモンのリロード
echo "🔄 systemdデーモンをリロード中..."
sudo systemctl daemon-reload

# サービスの有効化
echo "✅ 自動起動サービスを有効化中..."
sudo systemctl enable docker-auto-start.service

# サービスの開始
echo "🚀 サービスを開始中..."
sudo systemctl start docker-auto-start.service

# 状態確認
echo "📊 サービス状態確認:"
sudo systemctl status docker-auto-start.service

echo "✨ 設定完了！システム再起動時にDockerコンテナが自動的に起動します。"
