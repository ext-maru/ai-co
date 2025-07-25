#!/bin/bash
"""
Knights Autonomous Service Setup
騎士団自律運用サービス設定スクリプト

このスクリプトは騎士団を完全自律的に運用するためのシステムサービスを設定します
"""

set -e

# 色付きメッセージ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛡️ Knights Autonomous Service Setup${NC}"
echo "=================================================="

# プロジェクトディレクトリの確認
PROJECT_DIR="/home/aicompany/ai_co"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR"

# 1. ログディレクトリ作成
echo -e "${YELLOW}📁 Creating log directories...${NC}"
mkdir -p logs
mkdir -p /var/log/knights-guardian
sudo chown $USER:$USER /var/log/knights-guardian

# 2. systemd サービスファイル作成
echo -e "${YELLOW}🔧 Creating systemd service...${NC}"

sudo tee /etc/systemd/system/knights-guardian.service > /dev/null <<EOF
[Unit]
Description=Knights Autonomous Guardian Service
After=network.target rabbitmq-server.service
Wants=rabbitmq-server.service

[Service]
Type=simple
User=aicompany
Group=aicompany
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$PROJECT_DIR/venv/bin/python scripts/knights_autonomous_guardian.py --interval 60
Restart=always
RestartSec=10
StandardOutput=append:/var/log/knights-guardian/stdout.log
StandardError=append:/var/log/knights-guardian/stderr.log

# セキュリティ設定
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$PROJECT_DIR/logs /var/log/knights-guardian
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
EOF

# 3. ログローテーション設定
echo -e "${YELLOW}📋 Setting up log rotation...${NC}"

sudo tee /etc/logrotate.d/knights-guardian > /dev/null <<EOF
/var/log/knights-guardian/*.log $PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 aicompany aicompany
    postrotate
        systemctl reload knights-guardian || true
    endscript
}
EOF

# 4. Cron設定（バックアップ監視）
echo -e "${YELLOW}⏰ Setting up cron jobs...${NC}"

(crontab -l 2>/dev/null || echo "") | grep -v "knights-guardian" | crontab -
(crontab -l 2>/dev/null || echo "") | {
    cat
    echo "# Knights Guardian Health Check - every 5 minutes"
    echo "*/5 * * * * $PROJECT_DIR/venv/bin/python $PROJECT_DIR/scripts/knights_autonomous_guardian.py --report > /var/log/knights-guardian/health_$(date +\\%Y\\%m\\%d_\\%H\\%M).log 2>&1"
    echo ""
    echo "# Knights Guardian Service Monitor - every minute"
    echo "* * * * * systemctl is-active --quiet knights-guardian || systemctl start knights-guardian"
} | crontab -

# 5. sudoers設定（必要最小限の権限）
echo -e "${YELLOW}🔐 Configuring sudo permissions...${NC}"

sudo tee /etc/sudoers.d/knights-guardian > /dev/null <<EOF
# Knights Guardian - minimal required permissions
aicompany ALL=(root) NOPASSWD: /bin/systemctl restart rabbitmq-server
aicompany ALL=(root) NOPASSWD: /bin/systemctl status rabbitmq-server
aicompany ALL=(root) NOPASSWD: /bin/systemctl reload knights-guardian
EOF

# 6. 仮想環境とパッケージの確認
echo -e "${YELLOW}🐍 Checking virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet schedule  # 追加パッケージ

# 7. サービス有効化・開始
echo -e "${YELLOW}🚀 Enabling and starting service...${NC}"

sudo systemctl daemon-reload
sudo systemctl enable knights-guardian.service
sudo systemctl start knights-guardian.service

# 8. 状態確認
echo -e "${GREEN}✅ Service Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
sudo systemctl status knights-guardian.service --no-pager -l

echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo "  Start:   sudo systemctl start knights-guardian"
echo "  Stop:    sudo systemctl stop knights-guardian"
echo "  Restart: sudo systemctl restart knights-guardian"
echo "  Status:  sudo systemctl status knights-guardian"
echo "  Logs:    sudo journalctl -u knights-guardian -f"
echo ""

echo -e "${BLUE}📋 Log Files:${NC}"
echo "  Service:     /var/log/knights-guardian/"
echo "  Application: $PROJECT_DIR/logs/knights_autonomous.log"
echo "  Health:      /var/log/knights-guardian/health_*.log"
echo ""

echo -e "${GREEN}🎉 Knights Autonomous Guardian is now running!${NC}"
echo -e "${GREEN}The system will automatically monitor and repair itself 24/7.${NC}"

# 9. 初期ヘルスチェック実行
echo -e "${YELLOW}🔍 Running initial health check...${NC}"
sleep 5
$PROJECT_DIR/venv/bin/python $PROJECT_DIR/scripts/knights_autonomous_guardian.py --report
