#!/usr/bin/env python3
"""
Simple Elder Council Monitor
シンプルなエルダー評議会モニター（依存関係最小限）
"""

import os
import sys
import json
import time
import logging
import threading
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
LOG_DIR = PROJECT_ROOT / 'logs'
KNOWLEDGE_BASE = PROJECT_ROOT / 'knowledge_base'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ElderMonitor] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleElderMonitor:
    """シンプルなエルダーモニター"""
    
    def __init__(self):
        self.monitoring_active = False
        self.check_interval = 300  # 5分
        self.critical_thresholds = {
            'worker_count': 3,
            'memory_percent': 90,
            'error_count': 10
        }
        
    def check_workers(self):
        """ワーカーチェック"""
        try:
            result = subprocess.run(
                ['ps', 'aux'], 
                capture_output=True, 
                text=True
            )
            
            worker_types = [
                'enhanced_task_worker',
                'intelligent_pm_worker',
                'async_result_worker'
            ]
            
            worker_status = {}
            for worker in worker_types:
                count = result.stdout.count(worker)
                worker_status[worker] = count > 0
                
            healthy_count = sum(worker_status.values())
            return healthy_count, worker_status
            
        except Exception as e:
            logger.error(f"ワーカーチェックエラー: {e}")
            return 0, {}
            
    def check_system_resources(self):
        """システムリソースチェック"""
        try:
            # メモリ使用率
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                total = int(lines[0].split()[1])
                available = int(lines[2].split()[1])
                memory_percent = int((1 - available/total) * 100)
                
            # CPU使用率（簡易版）
            cpu_percent = 0
            try:
                result = subprocess.run(
                    ['top', '-bn1'], 
                    capture_output=True, 
                    text=True,
                    timeout=5
                )
                for line in result.stdout.split('\n'):
                    if 'Cpu(s)' in line:
                        idle = float(line.split()[4].replace('%id,', ''))
                        cpu_percent = int(100 - idle)
                        break
            except:
                pass
                
            return {
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent
            }
            
        except Exception as e:
            logger.error(f"リソースチェックエラー: {e}")
            return {'memory_percent': 0, 'cpu_percent': 0}
            
    def create_alert(self, title, description, severity='HIGH'):
        """アラート作成"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'description': description,
            'severity': severity,
            'status': 'ACTIVE'
        }
        
        # ファイルに保存
        alert_file = KNOWLEDGE_BASE / f'elder_alert_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(alert_file, 'w') as f:
            json.dump(alert, f, indent=2)
            
        logger.warning(f"🚨 アラート: {title} - {description}")
        
    def monitoring_loop(self):
        """監視ループ"""
        logger.info("🏛️ エルダー監視開始")
        
        while self.monitoring_active:
            try:
                # 1. ワーカーチェック
                worker_count, worker_status = self.check_workers()
                
                if worker_count < self.critical_thresholds['worker_count']:
                    self.create_alert(
                        "ワーカー不足",
                        f"稼働ワーカー数: {worker_count}/{self.critical_thresholds['worker_count']}",
                        "CRITICAL"
                    )
                    
                    # 自動復旧試行
                    logger.info("🔧 ワーカー自動復旧開始...")
                    subprocess.run([
                        'python3',
                        str(PROJECT_ROOT / 'check_and_fix_workers.py')
                    ])
                    
                # 2. システムリソースチェック
                resources = self.check_system_resources()
                
                if resources['memory_percent'] > self.critical_thresholds['memory_percent']:
                    self.create_alert(
                        "メモリ使用率過大",
                        f"メモリ使用率: {resources['memory_percent']}%",
                        "HIGH"
                    )
                    
                # 3. 定期レポート（1時間ごと）
                if int(time.time()) % 3600 < self.check_interval:
                    logger.info(
                        f"📊 定期レポート - "
                        f"ワーカー: {worker_count}/3, "
                        f"メモリ: {resources['memory_percent']}%, "
                        f"CPU: {resources['cpu_percent']}%"
                    )
                    
            except Exception as e:
                logger.error(f"監視ループエラー: {e}")
                
            time.sleep(self.check_interval)
            
    def start(self):
        """監視開始"""
        self.monitoring_active = True
        monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        monitor_thread.start()
        logger.info("✅ シンプルエルダーモニター起動完了")
        
    def stop(self):
        """監視停止"""
        self.monitoring_active = False
        logger.info("🛑 エルダーモニター停止")

def main():
    """メイン実行"""
    monitor = SimpleElderMonitor()
    
    try:
        monitor.start()
        logger.info("エルダーモニターは継続実行されます。停止: Ctrl+C")
        
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("停止シグナル受信")
        monitor.stop()
        
if __name__ == "__main__":
    main()