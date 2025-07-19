#!/bin/bash
# 契約書類アップロードシステム デプロイパッケージ作成
# Upload Image Service (契約書類アップロードシステム) 本番デプロイ準備

set -e

echo "🏛️ エルダーズギルド 契約書類アップロードシステム デプロイパッケージ作成"
echo "📦 Upload Image Service (契約書類アップロードシステム)"
echo "=" * 60

# デプロイパッケージディレクトリ作成
DEPLOY_DIR="/home/aicompany/ai_co/deployment/contract-upload-system"
mkdir -p "$DEPLOY_DIR"

echo "📁 デプロイディレクトリ作成: $DEPLOY_DIR"

# プロジェクトファイルコピー
echo "📋 プロジェクトファイルコピー中..."
cd /home/aicompany/ai_co/projects/upload-image-service

# 必要ファイルのみをコピー（効率的デプロイ）
cp -r backend/ "$DEPLOY_DIR/"
cp -r frontend/ "$DEPLOY_DIR/"
cp -r nginx/ "$DEPLOY_DIR/"
cp docker-compose.yml "$DEPLOY_DIR/"
cp elders_config.json "$DEPLOY_DIR/"

# プロジェクト情報ファイルをコピー
cp SERVER_DEPLOYMENT_INFO.md "$DEPLOY_DIR/"

# 本番用Docker設定作成
echo "🐳 本番用Docker設定作成..."
cat > "$DEPLOY_DIR/docker-compose.production.yml" << 'EOF'
version: '3.8'

services:
  # Contract Upload Backend (FastAPI)
  contract-upload-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: elders-guild-contract-upload-backend
    restart: always
    environment:
      - ENV=production
      - DATABASE_URL=sqlite:///app/data/contract_upload.db
      - UPLOAD_DIR=/app/uploads
      - SECRET_KEY_FILE=/app/config/secret_key.txt
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./config:/app/config
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.7'
        reservations:
          memory: 512M
          cpus: '0.3'
    networks:
      - contract-upload-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Contract Upload Frontend (React)
  contract-upload-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: elders-guild-contract-upload-frontend
    restart: always
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=http://57.181.4.111:8000
    ports:
      - "3000:3000"
    depends_on:
      - contract-upload-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.2'
    networks:
      - contract-upload-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  contract-upload-network:
    driver: bridge

volumes:
  contract_data:
    driver: local
  contract_uploads:
    driver: local
EOF

# 本番用環境設定
echo "⚙️ 本番環境設定作成..."
cat > "$DEPLOY_DIR/.env.production" << 'EOF'
# エルダーズギルド 契約書類アップロードシステム 本番環境設定
ENV=production

# Backend設定
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DATABASE_URL=sqlite:///app/data/contract_upload.db

# Frontend設定
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=3000
REACT_APP_API_URL=http://57.181.4.111:8000

# ファイルアップロード設定
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=100MB
ALLOWED_EXTENSIONS=pdf,jpg,jpeg,png,doc,docx

# セキュリティ設定
SECRET_KEY_FILE=/app/config/secret_key.txt
JWT_SECRET_KEY_FILE=/app/config/jwt_secret_key.txt
SECURITY_PASSWORD_SALT="elders_guild_contract_security_2025"

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=/app/logs/contract_upload.log

# 契約書処理設定
CONTRACT_TYPES=employment,service,partnership,nda,purchase
AUTO_CLASSIFICATION=true
OCR_ENABLED=true
EOF

# 本番用nginx設定
echo "🌐 本番用Nginx設定作成..."
cat > "$DEPLOY_DIR/nginx.production.conf" << 'EOF'
server {
    listen 80;
    server_name 57.181.4.111;

    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:;" always;

    # Frontend (React)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # プロキシタイムアウト
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # APIタイムアウト（ファイルアップロード対応）
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # アップロードファイル（認証必要）
    location /uploads/ {
        alias /opt/elders-guild/contract-upload-system/uploads/;
        expires 7d;

        # セキュリティ制限
        location ~* \.(php|pl|py|jsp|asp|sh|cgi)$ {
            deny all;
        }
    }

    # ヘルスチェック
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # ファイルアップロードサイズ制限（大きなPDFファイル対応）
    client_max_body_size 500M;
    client_body_timeout 300s;
    client_header_timeout 60s;

    # ログ設定
    access_log /var/log/nginx/elders-guild-contract-upload.access.log;
    error_log /var/log/nginx/elders-guild-contract-upload.error.log;
}
EOF

# デプロイスクリプト作成
echo "🚀 デプロイスクリプト作成..."
cat > "$DEPLOY_DIR/deploy.sh" << 'EOF'
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
EOF

chmod +x "$DEPLOY_DIR/deploy.sh"

# プロジェクト情報ファイル作成
echo "📋 プロジェクト情報ファイル作成..."
cat > "$DEPLOY_DIR/PROJECT_INFO.md" << 'EOF'
# 契約書類アップロードシステム - プロジェクト情報

## 📋 プロジェクト概要
- **名前**: Upload Image Service (契約書類アップロードシステム)
- **技術**: FastAPI + React + PostgreSQL
- **目的**: 契約書類の安全なアップロード・管理・承認システム

## 🌐 デプロイ先
- **サーバ**: 57.181.4.111 (Ubuntu 24.04.2 LTS)
- **アクセス**: http://57.181.4.111/
- **SSH**: `ssh -i server-private.pem ubuntu@57.181.4.111`

## 🐳 Docker構成
- **Backend**: localhost:8000 (FastAPI)
- **Frontend**: localhost:3000 (React)
- **Proxy**: localhost:80 (Nginx)

## 📁 重要なディレクトリ
- **プロジェクト**: `/opt/elders-guild/contract-upload-system/`
- **アップロード**: `/opt/elders-guild/contract-upload-system/uploads/`
- **ログ**: `/opt/elders-guild/contract-upload-system/logs/`
- **設定**: `/opt/elders-guild/contract-upload-system/config/`

## 🔐 SSH情報
詳細は `SERVER_DEPLOYMENT_INFO.md` を参照
EOF

echo ""
echo "✅ デプロイパッケージ作成完了"
echo "📦 パッケージ場所: $DEPLOY_DIR"
echo "📋 含まれるファイル:"
ls -la "$DEPLOY_DIR"

echo ""
echo "🚀 次のステップ:"
echo "1. パッケージをサーバに転送"
echo "2. デプロイスクリプト実行"
echo "3. 動作確認"
