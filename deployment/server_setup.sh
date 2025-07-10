#!/bin/bash
# Image Upload Manager デプロイ環境構築スクリプト
# Target: Ubuntu Server 57.181.4.111

set -e

SERVER_IP="57.181.4.111"
SSH_KEY="/home/aicompany/ai_co/deployment/server-private.pem"
SSH_USER="ubuntu"

echo "🏛️ エルダーズギルド Image Upload Manager デプロイ環境構築"
echo "🌟 グランドエルダーmaru 承認済みサーバセットアップ"
echo "📍 対象サーバ: ${SERVER_IP}"
echo "=" * 60

# SSH接続テスト
echo "🔍 SSH接続確認中..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${SSH_USER}@${SERVER_IP} "echo 'SSH接続成功'"

# サーバ環境構築
echo "🚀 リモートサーバ環境構築開始..."

ssh -i "$SSH_KEY" ${SSH_USER}@${SERVER_IP} << 'REMOTE_SETUP'
#!/bin/bash
set -e

echo "📋 システム情報確認"
echo "OS: $(lsb_release -d | cut -f2)"
echo "カーネル: $(uname -r)"
echo "アーキテクチャ: $(uname -m)"
echo "メモリ: $(free -h | grep Mem | awk '{print $2}')"
echo "ディスク: $(df -h / | tail -1 | awk '{print $4}' )"

echo "🔄 パッケージリスト更新"
sudo apt update -y

echo "🛠️ 基本パッケージインストール"
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    htop \
    nginx \
    ufw \
    fail2ban

echo "🐳 Docker インストール"
# Docker公式GPGキー追加
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Dockerリポジトリ追加
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker インストール
sudo apt update -y
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Dockerサービス開始・自動起動設定
sudo systemctl start docker
sudo systemctl enable docker

# ubuntuユーザーをdockerグループに追加
sudo usermod -aG docker ubuntu

echo "🐳 Docker Compose インストール"
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Docker バージョン確認
echo "📊 Docker インストール確認"
docker --version
docker compose version

echo "🔥 ファイアウォール設定"
# UFW基本設定
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH許可
sudo ufw allow ssh
sudo ufw allow 22

# HTTP/HTTPS許可
sudo ufw allow 80
sudo ufw allow 443

# 開発用ポート (必要に応じて)
sudo ufw allow 5000  # Flask開発サーバ
sudo ufw allow 8080  # 代替HTTPポート

echo "🛡️ Fail2Ban設定"
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

echo "🌐 Nginx基本設定"
# Nginxデフォルト設定削除
sudo rm -f /etc/nginx/sites-enabled/default

# 基本Nginx設定
sudo tee /etc/nginx/sites-available/elders-guild-image-upload > /dev/null << 'NGINX_CONFIG'
server {
    listen 80;
    server_name 57.181.4.111;

    # プロキシ設定
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静的ファイル
    location /static/ {
        alias /opt/elders-guild/image-upload-manager/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # アップロードファイル
    location /uploads/ {
        alias /opt/elders-guild/image-upload-manager/uploads/;
        expires 7d;
    }

    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # ファイルアップロードサイズ制限
    client_max_body_size 100M;
}
NGINX_CONFIG

# Nginx設定有効化
sudo ln -sf /etc/nginx/sites-available/elders-guild-image-upload /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "📁 デプロイ用ディレクトリ作成"
sudo mkdir -p /opt/elders-guild
sudo chown ubuntu:ubuntu /opt/elders-guild

echo "🔒 セキュリティ強化"
# SSHセキュリティ設定
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

echo "📊 環境構築完了確認"
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker compose version)"
echo "Nginx: $(nginx -v 2>&1)"
echo "UFW: $(sudo ufw status | head -1)"

echo "✅ サーバ環境構築完了"
echo "🏛️ エルダーズギルド Image Upload Manager 受け入れ準備完了"

REMOTE_SETUP

echo ""
echo "✅ リモートサーバ環境構築完了"
echo "📋 構築された環境:"
echo "   - Docker & Docker Compose"
echo "   - Nginx (リバースプロキシ設定済み)"
echo "   - ファイアウォール (UFW)"
echo "   - Fail2Ban (セキュリティ)"
echo "   - デプロイディレクトリ (/opt/elders-guild)"
echo ""
echo "🚀 次のステップ: Image Upload Manager デプロイ実行"