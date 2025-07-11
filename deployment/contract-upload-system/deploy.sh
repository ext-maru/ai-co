#!/bin/bash
# 契約書類アップロードシステム デプロイスクリプト

set -e

echo "🏛️ エルダーズギルド 契約書類アップロードシステム デプロイ開始"

# 必要ディレクトリ作成
sudo mkdir -p /opt/elders-guild/contract-upload-system/{data,uploads,logs,config}
sudo chown -R ubuntu:ubuntu /opt/elders-guild

# アプリケーションファイルコピー
cp -r ./* /opt/elders-guild/contract-upload-system/
cd /opt/elders-guild/contract-upload-system

# 権限設定
chmod +x deploy.sh
chmod 644 .env.production 2>/dev/null || true

# Secret keys生成
if [ ! -f config/secret_key.txt ]; then
    python3 -c "import secrets; print(secrets.token_hex(32))" > config/secret_key.txt
    chmod 600 config/secret_key.txt
fi

if [ ! -f config/jwt_secret_key.txt ]; then
    python3 -c "import secrets; print(secrets.token_hex(32))" > config/jwt_secret_key.txt
    chmod 600 config/jwt_secret_key.txt
fi

# Docker イメージビルド
echo "🐳 Docker イメージビルド中..."
docker compose -f docker-compose.production.yml build

# Nginx設定適用
echo "🌐 Nginx設定更新..."
sudo cp nginx.production.conf /etc/nginx/sites-available/elders-guild-contract-upload
sudo ln -sf /etc/nginx/sites-available/elders-guild-contract-upload /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo nginx -t
sudo systemctl reload nginx

# アプリケーション起動
echo "🚀 アプリケーション起動..."
docker compose -f docker-compose.production.yml up -d

# デプロイ検証
echo "✅ デプロイ検証中..."
sleep 15

# ヘルスチェック
echo "🔍 Backend ヘルスチェック..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend: 正常"
else
    echo "⚠️ Backend: 応答なし"
fi

echo "🔍 Frontend ヘルスチェック..."
if curl -f http://localhost:3000/ >/dev/null 2>&1; then
    echo "✅ Frontend: 正常"
else
    echo "⚠️ Frontend: 応答なし"
fi

echo "🔍 Nginx経由アクセステスト..."
if curl -f http://localhost/ >/dev/null 2>&1; then
    echo "✅ 契約書類アップロードシステム デプロイ成功"
    echo "🌐 アクセス URL: http://57.181.4.111/"
    echo "📊 コンテナ状態:"
    docker ps | grep elders-guild
else
    echo "❌ デプロイ検証失敗"
    echo "📋 Backend ログ:"
    docker compose -f docker-compose.production.yml logs contract-upload-backend --tail=10
    echo "📋 Frontend ログ:"
    docker compose -f docker-compose.production.yml logs contract-upload-frontend --tail=10
    exit 1
fi

echo "🎉 エルダーズギルド 契約書類アップロードシステム 本番デプロイ完了"
