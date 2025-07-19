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
