#!/bin/bash
# Image Upload Manager デプロイパッケージ作成
# エルダーズギルド プロジェクト2 本番デプロイ準備

set -e

echo "🏛️ エルダーズギルド Image Upload Manager デプロイパッケージ作成"
echo "📦 プロジェクト2: Image Upload Manager"
echo "=" * 60

# デプロイパッケージディレクトリ作成
DEPLOY_DIR="/home/aicompany/ai_co/deployment/image-upload-manager"
mkdir -p "$DEPLOY_DIR"

echo "📁 デプロイディレクトリ作成: $DEPLOY_DIR"

# プロジェクトファイルコピー
echo "📋 プロジェクトファイルコピー中..."
cd /home/aicompany/ai_co/projects/image-upload-manager

# 必要ファイルのみをコピー（効率的デプロイ）
cp -r app/ "$DEPLOY_DIR/"
cp requirements.txt "$DEPLOY_DIR/"
cp Dockerfile "$DEPLOY_DIR/"

# 本番用Docker設定作成
echo "🐳 本番用Docker設定作成..."
cat > "$DEPLOY_DIR/docker-compose.production.yml" << 'EOF'
version: '3.8'

services:
  image-upload-manager:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: elders-guild-image-upload-manager
    restart: always
    environment:
      - FLASK_ENV=production
      - FLASK_APP=app/app.py
      - PYTHONPATH=/app
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    ports:
      - "5000:5000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    networks:
      - elders-guild-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  elders-guild-network:
    driver: bridge

volumes:
  upload_data:
    driver: local
EOF

# 本番用環境設定
echo "⚙️ 本番環境設定作成..."
cat > "$DEPLOY_DIR/.env.production" << 'EOF'
# エルダーズギルド Image Upload Manager 本番環境設定
FLASK_ENV=production
FLASK_APP=app/app.py
PYTHONPATH=/app

# データベース設定
DATABASE_PATH=/app/data/image_upload.db

# アップロード設定
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=104857600  # 100MB

# Google Drive 設定 (オプション)
GOOGLE_DRIVE_ENABLED=false
GOOGLE_DRIVE_FOLDER_ID=""

# セキュリティ設定
SECRET_KEY_FILE=/app/config/secret_key.txt
SECURITY_PASSWORD_SALT="elders_guild_security_salt_2025"

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=/app/logs/image_upload.log
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
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    # メインアプリケーション
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # プロキシタイムアウト
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静的ファイル
    location /static/ {
        alias /opt/elders-guild/image-upload-manager/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        
        # セキュリティ
        location ~* \.(php|pl|py|jsp|asp|sh|cgi)$ {
            deny all;
        }
    }

    # アップロードファイル（認証必要）
    location /uploads/ {
        alias /opt/elders-guild/image-upload-manager/uploads/;
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

    # ファイルアップロードサイズ制限
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    # ログ設定
    access_log /var/log/nginx/elders-guild-image-upload.access.log;
    error_log /var/log/nginx/elders-guild-image-upload.error.log;
}
EOF

# デプロイスクリプト作成
echo "🚀 デプロイスクリプト作成..."
cat > "$DEPLOY_DIR/deploy.sh" << 'EOF'
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
EOF

chmod +x "$DEPLOY_DIR/deploy.sh"

# デプロイ用README作成
echo "📖 デプロイ用README作成..."
cat > "$DEPLOY_DIR/README.md" << 'EOF'
# エルダーズギルド Image Upload Manager デプロイ

## 📋 デプロイ手順

### 1. サーバにファイル転送
```bash
scp -i server-private.pem -r image-upload-manager ubuntu@57.181.4.111:/tmp/
```

### 2. デプロイ実行
```bash
ssh -i server-private.pem ubuntu@57.181.4.111
cd /tmp/image-upload-manager
./deploy.sh
```

### 3. 動作確認
```bash
curl http://57.181.4.111/
```

## 🛠️ 管理コマンド

### アプリケーション管理
```bash
cd /opt/elders-guild/image-upload-manager

# 停止
docker compose -f docker-compose.production.yml down

# 起動
docker compose -f docker-compose.production.yml up -d

# ログ確認
docker compose -f docker-compose.production.yml logs -f

# 再起動
docker compose -f docker-compose.production.yml restart
```

### システム監視
```bash
# コンテナ状態確認
docker ps

# リソース使用量
docker stats

# ログ確認
tail -f /var/log/nginx/elders-guild-image-upload.access.log
```

## 🔧 トラブルシューティング

### コンテナ起動失敗
```bash
docker compose -f docker-compose.production.yml logs
docker system prune -f
```

### Nginx設定エラー
```bash
sudo nginx -t
sudo systemctl status nginx
```

### ポート競合
```bash
sudo netstat -tulpn | grep :5000
sudo netstat -tulpn | grep :80
```

## 📊 監視・メンテナンス

- **アクセスログ**: `/var/log/nginx/elders-guild-image-upload.access.log`
- **エラーログ**: `/var/log/nginx/elders-guild-image-upload.error.log`
- **アプリログ**: `docker compose logs -f`
- **データ**: `/opt/elders-guild/image-upload-manager/data/`
- **アップロード**: `/opt/elders-guild/image-upload-manager/uploads/`
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