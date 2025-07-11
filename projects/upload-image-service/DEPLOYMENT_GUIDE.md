# Upload Image Service デプロイメントガイド

## 1. 本番環境へのデプロイ方法

### 前提条件
- Linux サーバー（Ubuntu 20.04以上推奨）
- Python 3.8以上
- Node.js 16以上
- Nginx（リバースプロキシ用）
- PM2（Node.jsプロセス管理）
- SSL証明書（Let's Encrypt推奨）

## 2. サーバー初期設定

### 2.1 必要なパッケージのインストール
```bash
# システムパッケージの更新
sudo apt update && sudo apt upgrade -y

# 必要なパッケージのインストール
sudo apt install -y python3-pip python3-venv nodejs npm nginx certbot python3-certbot-nginx git

# PM2のインストール（グローバル）
sudo npm install -g pm2
```

### 2.2 アプリケーション用ユーザーの作成
```bash
# アプリケーション用ユーザー作成
sudo useradd -m -s /bin/bash appuser
sudo passwd appuser

# 必要なディレクトリ作成
sudo mkdir -p /var/www/upload-image-service
sudo chown -R appuser:appuser /var/www/upload-image-service
```

## 3. アプリケーションのデプロイ

### 3.1 コードのアップロード
```bash
# appuserでログイン
su - appuser
cd /var/www/upload-image-service

# Gitからクローン（またはSCP/rsyncでアップロード）
git clone https://github.com/your-repo/upload-image-service.git .

# または、ローカルからアップロード
# ローカルマシンから実行:
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '__pycache__' \
  ./upload-image-service/ user@your-server:/var/www/upload-image-service/
```

### 3.2 バックエンドのセットアップ
```bash
cd /var/www/upload-image-service/backend

# Python仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
pip install gunicorn

# 環境変数の設定
cat > .env << EOF
DATABASE_URL=postgresql://dbuser:dbpass@localhost/upload_service_db
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=/var/www/upload-image-service/uploads
GOOGLE_DRIVE_CREDENTIALS_PATH=/var/www/upload-image-service/credentials.json
GOOGLE_DRIVE_PARENT_FOLDER_ID=your_folder_id_here
EOF

# アップロードディレクトリの作成
mkdir -p /var/www/upload-image-service/uploads
chmod 755 /var/www/upload-image-service/uploads

# データベースの初期化
python init_db.py
```

### 3.3 フロントエンドのビルド
```bash
cd /var/www/upload-image-service/frontend

# 依存関係のインストール
npm install

# 本番用環境変数の設定
cat > .env.production << EOF
REACT_APP_API_URL=https://your-domain.com/api
REACT_APP_UPLOAD_URL=https://your-domain.com
EOF

# 本番用ビルド
npm run build

# ビルドファイルを配信用ディレクトリにコピー
sudo mkdir -p /var/www/html/upload-service
sudo cp -r build/* /var/www/html/upload-service/
```

## 4. サービスの設定

### 4.1 Gunicornサービスの作成
```bash
# Systemdサービスファイルの作成
sudo nano /etc/systemd/system/upload-backend.service
```

```ini
[Unit]
Description=Upload Image Service Backend
After=network.target

[Service]
User=appuser
Group=appuser
WorkingDirectory=/var/www/upload-image-service/backend
Environment="PATH=/var/www/upload-image-service/backend/venv/bin"
ExecStart=/var/www/upload-image-service/backend/venv/bin/gunicorn \
          --workers 4 \
          --worker-class uvicorn.workers.UvicornWorker \
          --bind unix:/var/www/upload-image-service/backend/app.sock \
          app.main:app

[Install]
WantedBy=multi-user.target
```

```bash
# サービスの有効化と起動
sudo systemctl daemon-reload
sudo systemctl enable upload-backend
sudo systemctl start upload-backend
sudo systemctl status upload-backend
```

### 4.2 Nginxの設定
```bash
sudo nano /etc/nginx/sites-available/upload-service
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 静的ファイル（React）
    location / {
        root /var/www/html/upload-service;
        try_files $uri $uri/ /index.html;
    }

    # APIリクエスト
    location /api {
        proxy_pass http://unix:/var/www/upload-image-service/backend/app.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # アップロードファイルへのアクセス
    location /uploads {
        alias /var/www/upload-image-service/uploads;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 100M;
}
```

```bash
# サイトを有効化
sudo ln -s /etc/nginx/sites-available/upload-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4.3 SSL証明書の設定
```bash
# Let's Encryptで証明書取得
sudo certbot --nginx -d your-domain.com
```

## 5. 監視とメンテナンス

### 5.1 ログの確認
```bash
# バックエンドログ
sudo journalctl -u upload-backend -f

# Nginxアクセスログ
sudo tail -f /var/log/nginx/access.log

# Nginxエラーログ
sudo tail -f /var/log/nginx/error.log
```

### 5.2 バックアップスクリプト
```bash
# 日次バックアップスクリプトの作成
sudo nano /opt/backup-upload-service.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/upload-service"
DATE=$(date +%Y%m%d_%H%M%S)

# バックアップディレクトリ作成
mkdir -p $BACKUP_DIR

# データベースのバックアップ
cd /var/www/upload-image-service/backend
source venv/bin/activate
python -c "
from app.core.database import engine
import pandas as pd
from sqlalchemy import MetaData, Table

metadata = MetaData()
metadata.reflect(bind=engine)

for table_name in metadata.tables:
    table = Table(table_name, metadata, autoload_with=engine)
    df = pd.read_sql_table(table_name, engine)
    df.to_csv(f'$BACKUP_DIR/{table_name}_$DATE.csv', index=False)
"

# アップロードファイルのバックアップ
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /var/www/upload-image-service/uploads

# 30日以上古いバックアップを削除
find $BACKUP_DIR -type f -mtime +30 -delete
```

```bash
# 実行権限を付与
sudo chmod +x /opt/backup-upload-service.sh

# Cronジョブに追加
sudo crontab -e
# 追加: 0 2 * * * /opt/backup-upload-service.sh
```

## 6. デプロイ自動化スクリプト

### 6.1 デプロイスクリプト
```bash
# deploy.sh をローカルに作成
#!/bin/bash

SERVER="user@your-server.com"
APP_DIR="/var/www/upload-image-service"

echo "🚀 デプロイを開始します..."

# コードの同期
echo "📦 コードを同期中..."
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '__pycache__' \
  --exclude '.env' --exclude '*.db' --exclude 'uploads/*' \
  ./ $SERVER:$APP_DIR/

# バックエンドのデプロイ
echo "🐍 バックエンドを更新中..."
ssh $SERVER << 'EOF'
cd /var/www/upload-image-service/backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart upload-backend
EOF

# フロントエンドのビルドとデプロイ
echo "⚛️ フロントエンドをビルド中..."
cd frontend
npm run build
rsync -avz --delete build/ $SERVER:/var/www/html/upload-service/

echo "✅ デプロイが完了しました！"
```

## 7. 環境別設定

### 7.1 開発環境
```bash
# backend/.env.development
DATABASE_URL=sqlite:///./dev_upload_service.db
DEBUG=True
```

### 7.2 ステージング環境
```bash
# backend/.env.staging
DATABASE_URL=postgresql://dbuser:dbpass@localhost/upload_service_staging
DEBUG=False
```

### 7.3 本番環境
```bash
# backend/.env.production
DATABASE_URL=postgresql://dbuser:dbpass@localhost/upload_service_prod
DEBUG=False
SECURE_SSL_REDIRECT=True
```

## 8. トラブルシューティング

### よくある問題と解決方法

1. **502 Bad Gateway**
   ```bash
   # Gunicornが起動しているか確認
   sudo systemctl status upload-backend
   # ソケットファイルの権限確認
   ls -la /var/www/upload-image-service/backend/app.sock
   ```

2. **アップロードエラー**
   ```bash
   # ディレクトリの権限確認
   ls -la /var/www/upload-image-service/uploads
   # Nginxのclient_max_body_sizeを確認
   ```

3. **データベース接続エラー**
   ```bash
   # PostgreSQLサービスの確認
   sudo systemctl status postgresql
   # 接続テスト
   psql -U dbuser -d upload_service_db
   ```

## 9. セキュリティ対策

1. **ファイアウォール設定**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **定期的なアップデート**
   ```bash
   # 自動アップデートの設定
   sudo apt install unattended-upgrades
   sudo dpkg-reconfigure unattended-upgrades
   ```

3. **ファイルアップロードの検証**
   - ウイルススキャン（ClamAV）の導入
   - ファイルタイプの厳密な検証
   - アップロードサイズの制限

## まとめ

このガイドに従って設定することで、Upload Image Serviceを本番環境にデプロイできます。
セキュリティとパフォーマンスに注意を払い、定期的なメンテナンスを行ってください。
