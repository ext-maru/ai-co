#!/usr/bin/env python3
"""
Elder Council Monitoring Auto-Start System
エルダー評議会監視自動起動システム
"""

import sys
import time
import logging
import subprocess
import threading
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_council_summoner import ElderCouncilSummoner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class ElderMonitoringManager:
    """エルダー監視マネージャー"""
    
    def __init__(self):
        self.summoner = ElderCouncilSummoner()
        self.monitoring_active = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """監視開始"""
        logger.info("🏛️ エルダー評議会監視システム起動")
        
        # 初回チェック
        self._perform_initial_check()
        
        # 監視開始
        self.summoner.start_monitoring()
        self.monitoring_active = True
        
        # 定期的な状態チェック
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("✅ エルダー監視が正常に開始されました")
        
    def _perform_initial_check(self):
        """初回チェック"""
        logger.info("🔍 システム初回チェック実行中...")
        
        # 強制的にトリガー評価
        status = self.summoner.force_trigger_evaluation()
        
        logger.info(f"📊 システム状態:")
        logger.info(f"  - トリガー数: {status['total_triggers']}")
        logger.info(f"  - 保留中の評議会: {status['pending_councils']}")
        logger.info(f"  - 緊急度分布: {status['urgency_distribution']}")
        
        if status['recent_metrics']:
            metrics = status['recent_metrics']
            logger.info(f"  - ワーカー健全性: {metrics['worker_health_score']:.1%}")
            logger.info(f"  - テストカバレッジ: {metrics['test_coverage']:.1%}")
            logger.info(f"  - メモリ使用率: {metrics['memory_usage']:.1%}")
            logger.info(f"  - 4賢者合意率: {metrics['four_sages_consensus_rate']:.1%}")
            
    def _monitoring_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # 30分ごとに状態レポート
                time.sleep(1800)
                
                status = self.summoner.get_system_status()
                logger.info(f"📊 定期レポート - トリガー: {status['total_triggers']}, 評議会: {status['pending_councils']}")
                
            except Exception as e:
                logger.error(f"監視ループエラー: {e}")
                time.sleep(60)
                
    def stop_monitoring(self):
        """監視停止"""
        logger.info("🛑 エルダー監視を停止します...")
        self.monitoring_active = False
        self.summoner.stop_monitoring()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        logger.info("✅ エルダー監視が停止されました")

def ensure_not_already_running():
    """既に実行中でないことを確認"""
    try:
        result = subprocess.run(['pgrep', '-f', 'start_elder_monitoring.py'], 
                              capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        pids = [pid for pid in pids if pid]
        
        if len(pids) > 1:  # 自身以外のプロセスが存在
            logger.warning("⚠️ エルダー監視は既に実行中です")
            return False
            
    except Exception as e:
        logger.error(f"プロセスチェックエラー: {e}")
        
    return True

def main():
    """メイン実行"""
    logger.info("=" * 60)
    logger.info("🏛️ AI Company Elder Council Monitoring System")
    logger.info(f"開始時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    logger.info("=" * 60)
    
    # 既存プロセスチェック
    if not ensure_not_already_running():
        return
    
    manager = ElderMonitoringManager()
    
    try:
        # 監視開始
        manager.start_monitoring()
        
        # 永続的に実行
        logger.info("🏛️ エルダー監視は継続的に実行されます...")
        logger.info("停止するには Ctrl+C を押してください")
        
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️ 停止シグナルを受信しました")
        manager.stop_monitoring()
        
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        manager.stop_monitoring()
        
    logger.info("🏛️ エルダー監視システムを終了しました")

if __name__ == "__main__":
    main()