#!/usr/bin/env python3
"""
Health Checker - ワーカーの健康状態監視と自動復旧
"""
import psutil
import subprocess
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger('HealthChecker')

class HealthChecker:
    def __init__(self, config_file=None):
        """ヘルスチェッカーの初期化"""
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "scaling.conf"
        self.config = self._load_config(config_file)
        self.unhealthy_workers = {}  # worker_id: {count, first_seen}
        
    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        config = {
            'HEALTH_CHECK_INTERVAL': 60,
            'MAX_CPU_PERCENT': 80,
            'MAX_MEMORY_PERCENT': 80,
            'UNHEALTHY_THRESHOLD': 3,  # 連続して不健康と判定される回数
            'RESTART_COOLDOWN': 300    # 再起動後の待機時間（秒）
        }
        
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        try:
                            config[key] = int(value)
                        except ValueError:
                            config[key] = value
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
            
        return config
    
    def check_worker_health(self, worker_info):
        """個別ワーカーの健康状態をチェック"""
        worker_id = worker_info['worker_id']
        pid = worker_info['pid']
        
        try:
            # プロセスの詳細情報を取得
            process = psutil.Process(pid)
            
            # CPU使用率（1秒間の平均）
            cpu_percent = process.cpu_percent(interval=1)
            
            # メモリ情報
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # スレッド数
            num_threads = process.num_threads()
            
            # 応答性チェック（プロセスが生きているか）
            is_running = process.is_running() and process.status() != psutil.STATUS_ZOMBIE
            
            # 健康判定
            health_issues = []
            
            if cpu_percent > self.config['MAX_CPU_PERCENT']:
                health_issues.append(f"高CPU使用率: {cpu_percent:.1f}%")
                
            if memory_percent > self.config['MAX_MEMORY_PERCENT']:
                health_issues.append(f"高メモリ使用率: {memory_percent:.1f}%")
                
            if not is_running:
                health_issues.append("プロセス応答なし")
                
            # RabbitMQ接続チェック（netstatを使用）
            has_rabbitmq_connection = self._check_rabbitmq_connection(pid)
            if not has_rabbitmq_connection:
                health_issues.append("RabbitMQ接続なし")
            
            is_healthy = len(health_issues) == 0
            
            health_status = {
                'worker_id': worker_id,
                'pid': pid,
                'healthy': is_healthy,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_rss': memory_info.rss / 1024 / 1024,  # MB
                'num_threads': num_threads,
                'issues': health_issues,
                'has_rabbitmq_connection': has_rabbitmq_connection,
                'timestamp': datetime.now().isoformat()
            }
            
            # 不健康な場合の記録
            if not is_healthy:
                self._record_unhealthy(worker_id, health_status)
            else:
                # 健康になったらカウントリセット
                if worker_id in self.unhealthy_workers:
                    del self.unhealthy_workers[worker_id]
                    logger.info(f"✅ {worker_id} が健康状態に回復")
            
            return health_status
            
        except psutil.NoSuchProcess:
            return {
                'worker_id': worker_id,
                'pid': pid,
                'healthy': False,
                'issues': ['プロセスが存在しません'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"ヘルスチェックエラー: {worker_id} - {e}")
            return {
                'worker_id': worker_id,
                'pid': pid,
                'healthy': False,
                'issues': [f'チェックエラー: {str(e)}'],
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_rabbitmq_connection(self, pid):
        """RabbitMQ接続の確認"""
        try:
            # netstatでPIDの接続を確認
            cmd = f"netstat -tnp 2>/dev/null | grep {pid} | grep :5672"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return len(result.stdout.strip()) > 0
        except:
            return True  # エラー時は接続ありと仮定
    
    def _record_unhealthy(self, worker_id, health_status):
        """不健康なワーカーを記録"""
        if worker_id not in self.unhealthy_workers:
            self.unhealthy_workers[worker_id] = {
                'count': 1,
                'first_seen': datetime.now(),
                'issues': health_status['issues']
            }
        else:
            self.unhealthy_workers[worker_id]['count'] += 1
            self.unhealthy_workers[worker_id]['issues'] = health_status['issues']
        
        logger.warning(f"⚠️ {worker_id} 不健康: {health_status['issues']} "
                      f"(連続{self.unhealthy_workers[worker_id]['count']}回)")
    
    def should_restart_worker(self, worker_id):
        """ワーカーを再起動すべきか判断"""
        if worker_id not in self.unhealthy_workers:
            return False
            
        unhealthy_info = self.unhealthy_workers[worker_id]
        
        # 連続不健康回数が閾値を超えた場合
        if unhealthy_info['count'] >= self.config['UNHEALTHY_THRESHOLD']:
            # クールダウン期間をチェック
            if 'last_restart' in unhealthy_info:
                elapsed = (datetime.now() - unhealthy_info['last_restart']).seconds
                if elapsed < self.config['RESTART_COOLDOWN']:
                    logger.info(f"⏳ {worker_id} 再起動クールダウン中 (残り{self.config['RESTART_COOLDOWN'] - elapsed}秒)")
                    return False
            
            return True
            
        return False
    
    def record_restart(self, worker_id):
        """再起動を記録"""
        if worker_id in self.unhealthy_workers:
            self.unhealthy_workers[worker_id]['last_restart'] = datetime.now()
            self.unhealthy_workers[worker_id]['count'] = 0

if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    checker = HealthChecker()
    
    # テストワーカー情報
    test_worker = {
        'worker_id': 'worker-1',
        'pid': 12345,  # 実際のPIDに置き換えてテスト
    }
    
    health = checker.check_worker_health(test_worker)
    print(f"ヘルスチェック結果: {health}")
