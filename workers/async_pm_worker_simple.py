#!/usr/bin/env python3
"""
簡易版非同期PM Worker
移行テスト用の最小実装
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import sys

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.async_base_worker_v2 import AsyncBaseWorkerV2

class AsyncPMWorkerSimple(AsyncBaseWorkerV2):
    """簡易版非同期PM Worker"""
    
    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        super().__init__(
            worker_name="async_pm_worker_simple",
            config=config,
            input_queues=['ai_pm'],
            output_queues=['ai_results']
        )
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """PMメッセージ処理の実装"""
        task_id = message.get('task_id', 'unknown')
        
        # 簡単なPM処理のシミュレーション
        await asyncio.sleep(0.1)
        
        result = {
            'task_id': task_id,
            'status': 'pm_processed',
            'processed_at': datetime.utcnow().isoformat(),
            'worker': self.worker_name,
            'pm_summary': f"PM processing for {task_id} completed"
        }
        
        self.logger.info("PM task processed", task_id=task_id)
        return result

# メイン実行部分
async def main():
    """ワーカーのメイン実行"""
    config = {
        'circuit_breaker_threshold': 5,
        'circuit_breaker_timeout': 60
    }
    
    worker = AsyncPMWorkerSimple(config)
    
    print("🚀 AsyncPMWorkerSimple started")
    
    try:
        while True:
            await asyncio.sleep(10)
            print("💓 PM Worker heartbeat")
    except KeyboardInterrupt:
        print("\n🛑 PM Worker stopping...")
        await worker.shutdown()
        print("✅ PM Worker stopped")

if __name__ == "__main__":
    asyncio.run(main())