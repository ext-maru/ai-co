#!/bin/bash
# Image Upload Manager デプロイスクリプト

set -e

echo "🏛️ エルダーズギルド Image Upload Manager デプロイ開始"

# 必要ディレクトリ作成
sudo mkdir -p /opt/elders-guild/image-upload-manager/{data,uploads,logs,config}
sudo chown -R ubuntu:ubuntu /opt/elders-guild

# アプリケーションファイルコピー
cp -r ./* /opt/elders-guild/image-upload-manager/
cd /opt/elders-guild/image-upload-manager

# 権限設定
chmod +x deploy.sh
chmod 644 .env.production

# Secret key生成
if [ ! -f config/secret_key.txt ]; then
    python3 -c "import secrets; print(secrets.token_hex(32))" > config/secret_key.txt
    chmod 600 config/secret_key.txt
fi

# Docker イメージビルド
echo "🐳 Docker イメージビルド中..."
docker compose -f docker-compose.production.yml build

# Nginx設定適用
echo "🌐 Nginx設定更新..."
sudo cp nginx.production.conf /etc/nginx/sites-available/elders-guild-image-upload
sudo ln -sf /etc/nginx/sites-available/elders-guild-image-upload /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# アプリケーション起動
echo "🚀 アプリケーション起動..."
docker compose -f docker-compose.production.yml up -d

# デプロイ検証
echo "✅ デプロイ検証中..."
sleep 10

# ヘルスチェック
if curl -f http://localhost:5000/ >/dev/null 2>&1; then
    echo "✅ Image Upload Manager デプロイ成功"
    echo "🌐 アクセス URL: http://57.181.4.111/"
else
    echo "❌ デプロイ検証失敗"
    docker compose -f docker-compose.production.yml logs
    exit 1
fi

echo "🎉 エルダーズギルド Image Upload Manager 本番デプロイ完了"
