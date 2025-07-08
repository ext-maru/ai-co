#!/bin/bash
# AI Company Apache セットアップスクリプト

set -e

PROJECT_ROOT="/home/aicompany/ai_co"
APACHE_CONFIG_FILE="$PROJECT_ROOT/config/apache-aicompany.conf"
APACHE_SITES_DIR="/etc/apache2/sites-available"
APACHE_CONF_FILE="$APACHE_SITES_DIR/aicompany.conf"

echo "🌐 AI Company Apache セットアップ開始..."

# Apache、mod_wsgi、Python依存関係のインストール
echo "📦 必要なパッケージをインストール中..."
sudo apt update
sudo apt install -y apache2 libapache2-mod-wsgi-py3 python3-dev

# Flaskのインストール（仮想環境内）
echo "🐍 Flask依存関係をインストール中..."
cd "$PROJECT_ROOT"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install flask gunicorn
else
    echo "⚠️  仮想環境が見つかりません。systemレベルでインストールします..."
    sudo pip3 install flask gunicorn
fi

# Apacheモジュールの有効化
echo "🔧 Apacheモジュールを有効化中..."
sudo a2enmod wsgi
sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod deflate
sudo a2enmod proxy
sudo a2enmod proxy_http

# Apache設定ファイルをコピー
echo "📄 Apache設定ファイルを配置中..."
sudo cp "$APACHE_CONFIG_FILE" "$APACHE_CONF_FILE"

# 権限設定
echo "🔒 ディレクトリ権限を設定中..."
sudo chown -R www-data:www-data "$PROJECT_ROOT/web"
sudo chmod -R 755 "$PROJECT_ROOT/web"
sudo chmod +x "$PROJECT_ROOT/web/app.wsgi"

# Apacheユーザーがプロジェクトディレクトリにアクセスできるように設定
sudo usermod -a -G aicompany www-data

# /etc/hostsに追加（ローカル開発用）
echo "🌐 /etc/hostsにエントリを追加中..."
if ! grep -q "aicompany.local" /etc/hosts; then
    echo "127.0.0.1 aicompany.local www.aicompany.local aicompany-proxy.local" | sudo tee -a /etc/hosts
fi

# サイトを有効化
echo "✅ サイトを有効化中..."
sudo a2ensite aicompany
sudo a2dissite 000-default  # デフォルトサイトを無効化（オプション）

# Apache設定テスト
echo "🧪 Apache設定をテスト中..."
sudo apache2ctl configtest

# Apacheを再起動
echo "🔄 Apacheを再起動中..."
sudo systemctl restart apache2
sudo systemctl enable apache2

# 動作確認
echo "🚀 セットアップ完了！"
echo ""
echo "📍 アクセス可能なURL:"
echo "  🌐 WSGI版: http://aicompany.local"
echo "  🔗 プロキシ版: http://aicompany-proxy.local:8080"
echo "  📊 直接アクセス: http://localhost:5555"
echo ""
echo "🔧 管理コマンド:"
echo "  Apache再起動: sudo systemctl restart apache2"
echo "  ログ確認: sudo tail -f /var/log/apache2/aicompany_*.log"
echo "  設定再読み込み: sudo systemctl reload apache2"
echo ""
echo "⚠️  注意事項:"
echo "  - Pythonアプリケーション（ai-webui）も並行して起動してください"
echo "  - ファイアウォール設定が必要な場合があります"
echo "  - SSL証明書が必要な場合は設定ファイルを修正してください"

# ファイアウォール設定（UFWが有効な場合）
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    echo "🔥 ファイアウォール設定を更新中..."
    sudo ufw allow 80/tcp
    sudo ufw allow 8080/tcp
fi

echo ""
echo "🎉 Apache セットアップが完了しました！"