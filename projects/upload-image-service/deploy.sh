#!/bin/bash
# Upload Image Service デプロイスクリプト

echo "🚀 Upload Image Service のデプロイを開始します..."

# バックエンドのセットアップ
echo "🐍 バックエンドをセットアップ中..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 環境変数の設定
cat > .env << EOF
DATABASE_URL=postgresql://elder_admin:sage_wisdom_2025@172.29.65.239:5432/upload_image_service
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=/var/www/upload-image-service/uploads
EOF

# データベースの初期化
python init_db.py

# フロントエンドのビルド
echo "⚛️ フロントエンドをビルド中..."
cd ../frontend
npm install
npm run build

# Nginxの設定
echo "🔧 Nginxを設定中..."
sudo tee /etc/nginx/sites-available/upload-image-service << EOF
server {
    listen 9001;
    server_name 172.29.65.239;

    location / {
        root /var/www/upload-image-service/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    client_max_body_size 100M;
}
EOF

sudo ln -sf /etc/nginx/sites-available/upload-image-service /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# サービスの起動
echo "🎯 サービスを起動中..."
cd ../backend
source venv/bin/activate
nohup gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001 app.main:app > app.log 2>&1 &

echo "✅ デプロイが完了しました！"
echo "📍 アクセスURL: http://172.29.65.239:9001"
echo "📍 管理画面: http://172.29.65.239:9001/admin"
