#!/usr/bin/env python3
from pathlib import Path
"""
会話リカバリデーモン
"""
import sys
import time
import logging
sys.path.append(str(Path(__file__).parent.parent))
from libs.conversation_recovery import ConversationRecoveryManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [RecoveryDaemon] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    recovery = ConversationRecoveryManager()
    check_interval = 300  # 5分ごと
    
    logger.info("🔄 リカバリデーモン起動")
    
    while True:
        try:
            # リカバリチェック実行
            result = recovery.auto_recovery_check()
            
            if result['stalled'] > 0 or result['orphaned'] > 0:
                logger.warning(f"異常検出: {result}")
            
            # 次回まで待機
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("リカバリデーモン停止")
            break
        except Exception as e:
            logger.error(f"リカバリエラー: {e}")
            time.sleep(60)  # エラー時は1分後に再試行

if __name__ == "__main__":
    main()
