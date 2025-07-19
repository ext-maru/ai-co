#!/bin/bash
# Plan Projects Sync サービス設定スクリプト

echo "🔧 Plan Projects Sync サービス設定開始"

# サービスファイルの作成
cat > /tmp/plan-projects-sync.service << EOF
[Unit]
Description=Plan Projects Sync Service
After=network.target

[Service]
Type=simple
User=aicompany
WorkingDirectory=/home/aicompany/ai_co
Environment="PYTHONPATH=/home/aicompany/ai_co/libs"
ExecStart=/usr/bin/python3 /home/aicompany/ai_co/scripts/plan_sync_daemon.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# デーモンスクリプトの作成
cat > /home/aicompany/ai_co/scripts/plan_sync_daemon.py << 'EOF'
#!/usr/bin/env python3
"""Plan Projects Sync デーモン"""

import sys
sys.path.insert(0, '/home/aicompany/ai_co/libs')

import asyncio
import logging
import os
from datetime import datetime
from task_elder.plan_projects_sync import PlanProjectsSync

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/aicompany/ai_co/logs/plan_sync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """メインループ"""
    logger.info("Plan Projects Sync デーモン開始")
    
    # GitHub トークンの確認
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        logger.warning("GITHUB_TOKEN が設定されていません。機能が制限されます。")
    
    sync_system = PlanProjectsSync(github_token)
    
    # 初回同期
    logger.info("初回同期を実行...")
    await sync_system.auto_sync_all_changes()
    
    # 継続的同期（30分間隔）
    await sync_system.enable_continuous_sync(interval_minutes=30)

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x /home/aicompany/ai_co/scripts/plan_sync_daemon.py

echo "✅ 設定ファイル作成完了"
echo ""
echo "🚀 サービスを有効化するには以下を実行してください:"
echo "   sudo cp /tmp/plan-projects-sync.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable plan-projects-sync"
echo "   sudo systemctl start plan-projects-sync"
echo ""
echo "📊 ログを確認するには:"
echo "   tail -f /home/aicompany/ai_co/logs/plan_sync.log"