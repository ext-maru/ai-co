"""
Health Checker Component

ワーカーの健康状態を監視し、異常を検出するコンポーネント
"""

import os
import psutil
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import subprocess

logger = logging.getLogger(__name__)


class HealthChecker:
    """ワーカーの健康状態をチェックするクラス"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config or self._get_default_config()
        self.worker_configs = self._load_worker_configs()
        self.health_history = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            'thresholds': {
                'cpu_percent': 90.0,
                'memory_mb': 1024,
                'error_rate': 0.1,
                'queue_size': 100,
                'response_timeout': 30  # seconds
            },
            'check_interval': 30,  # seconds
            'history_size': 100,   # 履歴保持数
        }
    
    def _load_worker_configs(self) -> Dict[str, Dict[str, Any]]:
        """ワーカー設定を読み込み"""
        return {
            'task_worker': {
                'process_name': 'enhanced_task_worker.py',
                'queue_name': 'worker_tasks',
                'critical': True
            },
            'pm_worker': {
                'process_name': 'intelligent_pm_worker_simple.py',
                'queue_name': 'ai_tasks',
                'critical': True
            },
            'result_worker': {
                'process_name': 'async_result_worker_simple.py',
                'queue_name': 'results',
                'critical': True
            },
            'error_intelligence_worker': {
                'process_name': 'error_intelligence_worker.py',
                'queue_name': 'error_intelligence',
                'critical': False
            },
            'slack_polling_worker': {
                'process_name': 'slack_polling_worker.py',
                'queue_name': None,
                'critical': False
            }
        }
    
    def check_all_workers(self) -> Dict[str, Dict[str, Any]]:
        """
        全ワーカーの健康状態をチェック
        
        Returns:
            ワーカー名をキーとした健康状態辞書
        """
        results = {}
        
        for worker_name, worker_config in self.worker_configs.items():
            results[worker_name] = self.check_worker_health(worker_name)
            
        return results
    
    def check_worker_health(self, worker_name: str) -> Dict[str, Any]:
        """
        特定ワーカーの健康状態をチェック
        
        Args:
            worker_name: ワーカー名
            
        Returns:
            健康状態を表す辞書
        """
        if worker_name not in self.worker_configs:
            return {
                'status': 'unknown',
                'healthy': False,
                'error': f'Unknown worker: {worker_name}'
            }
        
        config = self.worker_configs[worker_name]
        health_data = {
            'worker_name': worker_name,
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # プロセスチェック
        process_check = self._check_process(config['process_name'])
        health_data['checks']['process'] = process_check
        
        if process_check['exists']:
            # リソースチェック
            health_data['checks']['resources'] = self._check_resources(
                process_check['pid']
            )
            
            # キューチェック（該当する場合）
            if config.get('queue_name'):
                health_data['checks']['queue'] = self._check_queue(
                    config['queue_name']
                )
            
            # エラー率チェック
            health_data['checks']['errors'] = self._check_error_rate(
                worker_name
            )
        
        # 総合的な健康状態を判定
        health_data['healthy'] = self._evaluate_health(health_data['checks'])
        health_data['status'] = 'healthy' if health_data['healthy'] else 'unhealthy'
        health_data['health_score'] = self._calculate_health_score(health_data['checks'])
        
        # 履歴に追加
        self._add_to_history(worker_name, health_data)
        
        return health_data
    
    def _check_process(self, process_name: str) -> Dict[str, Any]:
        """プロセスの存在をチェック"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and process_name in ' '.join(cmdline):
                    return {
                        'exists': True,
                        'pid': proc.info['pid'],
                        'status': 'running'
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return {
            'exists': False,
            'pid': None,
            'status': 'not_found'
        }
    
    def _check_resources(self, pid: int) -> Dict[str, Any]:
        """プロセスのリソース使用状況をチェック"""
        try:
            proc = psutil.Process(pid)
            
            # CPU使用率（1秒間の平均）
            cpu_percent = proc.cpu_percent(interval=1.0)
            
            # メモリ使用量
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            thresholds = self.config['thresholds']
            
            return {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'cpu_ok': cpu_percent < thresholds['cpu_percent'],
                'memory_ok': memory_mb < thresholds['memory_mb']
            }
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {
                'cpu_percent': 0,
                'memory_mb': 0,
                'cpu_ok': False,
                'memory_ok': False,
                'error': 'Process access failed'
            }
    
    def _check_queue(self, queue_name: str) -> Dict[str, Any]:
        """キューの状態をチェック"""
        try:
            # RabbitMQのキュー状態を確認
            cmd = f"sudo rabbitmqctl list_queues name messages consumers | grep {queue_name}"
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split()
                if len(parts) >= 3:
                    messages = int(parts[1])
                    consumers = int(parts[2])
                    
                    return {
                        'queue_name': queue_name,
                        'messages': messages,
                        'consumers': consumers,
                        'healthy': messages < self.config['thresholds']['queue_size']
                    }
            
            return {
                'queue_name': queue_name,
                'messages': 0,
                'consumers': 0,
                'healthy': True,
                'warning': 'Could not get queue stats'
            }
            
        except Exception as e:
            logger.error(f"Queue check failed: {e}")
            return {
                'queue_name': queue_name,
                'healthy': False,
                'error': str(e)
            }
    
    def _check_error_rate(self, worker_name: str) -> Dict[str, Any]:
        """エラー率をチェック"""
        # 最近の履歴からエラー率を計算
        history = self.health_history.get(worker_name, [])
        if len(history) < 5:
            return {
                'error_rate': 0.0,
                'healthy': True,
                'sample_size': len(history)
            }
        
        recent_history = history[-10:]  # 最近10件
        error_count = sum(1 for h in recent_history if not h.get('healthy', True))
        error_rate = error_count / len(recent_history)
        
        return {
            'error_rate': error_rate,
            'healthy': error_rate < self.config['thresholds']['error_rate'],
            'sample_size': len(recent_history)
        }
    
    def _evaluate_health(self, checks: Dict[str, Any]) -> bool:
        """チェック結果から総合的な健康状態を判定"""
        # プロセスが存在しない場合は不健康
        if not checks.get('process', {}).get('exists', False):
            return False
        
        # リソースチェック
        resources = checks.get('resources', {})
        if not (resources.get('cpu_ok', True) and resources.get('memory_ok', True)):
            return False
        
        # キューチェック
        queue = checks.get('queue', {})
        if 'healthy' in queue and not queue['healthy']:
            return False
        
        # エラー率チェック
        errors = checks.get('errors', {})
        if not errors.get('healthy', True):
            return False
        
        return True
    
    def _calculate_health_score(self, checks: Dict[str, Any]) -> float:
        """健康スコアを計算（0-100）"""
        score = 100.0
        
        # プロセス存在チェック
        if not checks.get('process', {}).get('exists', False):
            return 0.0
        
        # リソースチェック
        resources = checks.get('resources', {})
        if resources:
            cpu_percent = resources.get('cpu_percent', 0)
            memory_mb = resources.get('memory_mb', 0)
            
            # CPU使用率によるスコア減点
            if cpu_percent > 50:
                score -= min((cpu_percent - 50) * 0.5, 25)
            
            # メモリ使用量によるスコア減点
            if memory_mb > 512:
                score -= min((memory_mb - 512) / 512 * 20, 20)
        
        # キューチェック
        queue = checks.get('queue', {})
        if queue and not queue.get('healthy', True):
            score -= 20
        
        # エラー率チェック
        errors = checks.get('errors', {})
        if errors:
            error_rate = errors.get('error_rate', 0)
            score -= min(error_rate * 100, 30)
        
        return max(score, 0.0)
    
    def _add_to_history(self, worker_name: str, health_data: Dict[str, Any]):
        """健康状態を履歴に追加"""
        if worker_name not in self.health_history:
            self.health_history[worker_name] = []
        
        history = self.health_history[worker_name]
        history.append(health_data)
        
        # 履歴サイズを制限
        max_size = self.config.get('history_size', 100)
        if len(history) > max_size:
            self.health_history[worker_name] = history[-max_size:]
    
    def get_worker_trend(self, worker_name: str, minutes: int = 30) -> Dict[str, Any]:
        """ワーカーの健康状態トレンドを取得"""
        history = self.health_history.get(worker_name, [])
        if not history:
            return {'trend': 'unknown', 'data_points': 0}
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_history = [
            h for h in history 
            if datetime.fromisoformat(h['timestamp']) > cutoff_time
        ]
        
        if len(recent_history) < 2:
            return {'trend': 'insufficient_data', 'data_points': len(recent_history)}
        
        # 健康スコアのトレンドを計算
        scores = [h['health_score'] for h in recent_history]
        avg_first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
        avg_second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        
        if avg_second_half > avg_first_half + 5:
            trend = 'improving'
        elif avg_second_half < avg_first_half - 5:
            trend = 'degrading'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'data_points': len(recent_history),
            'current_score': scores[-1] if scores else 0,
            'average_score': sum(scores) / len(scores) if scores else 0
        }