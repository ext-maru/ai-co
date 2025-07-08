#!/usr/bin/env python3
"""
Elf Forest Startup Script
エルフの森起動スクリプト
"""

import sys
import asyncio
import logging
from pathlib import Path

# Python 3.6以下の互換性
if sys.version_info >= (3, 7):
    from libs.elf_forest_worker_manager import ElfForestWorkerManager
else:
    # Python 3.6以下用の代替実装
    print("Python 3.7以降が推奨されています")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ElfForest] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def run_elf_forest():
    """エルフの森を実行"""
    logger.info("🌲 エルフの森を起動しています...")
    
    try:
        manager = ElfForestWorkerManager()
        
        # タスクエルダーとの協力メッセージ
        logger.info("🏛️ タスクエルダーと協力してワーカー管理を開始します")
        
        # リマインダーのサンプル設定
        from datetime import datetime, timedelta
        
        # 夜間メンテナンスリマインダー
        manager.time_elf.add_reminder(
            'enhanced_task_worker',
            datetime.now().replace(hour=23, minute=0, second=0),
            '夜間メンテナンス: ログローテーション実行'
        )
        
        # 朝の日次レポートリマインダー
        manager.time_elf.add_reminder(
            'intelligent_pm_worker',
            datetime.now().replace(hour=9, minute=0, second=0) + timedelta(days=1),
            '朝の日次レポート生成を開始'
        )
        
        # 非同期ランナー
        if hasattr(asyncio, 'run'):
            asyncio.run(manager.start())
        else:
            # Python 3.6以下
            loop = asyncio.get_event_loop()
            loop.run_until_complete(manager.start())
            
    except KeyboardInterrupt:
        logger.info("🌙 エルフの森を停止しています...")
    except Exception as e:
        logger.error(f"エルフの森でエラーが発生: {e}")

if __name__ == "__main__":
    run_elf_forest()