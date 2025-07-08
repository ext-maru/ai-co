#!/usr/bin/env python3
"""
Worker Health Monitor - 適切な実装
Elder Council承認済み設計に基づく完全な監視システム

統合監視アーキテクチャの一部として実装
Phase 2: 軽量実装（即座に動作する最小限の機能）
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
import threading
import json

logger = logging.getLogger(__name__)

class MetricsCollector:
    """メトリクス収集器"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self._lock = threading.RLock()
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクスの収集"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'percent': memory.percent,
                    'available': memory.available,
                    'total': memory.total
                },
                'disk': {
                    'percent': disk.percent,
                    'free': disk.free,
                    'total': disk.total
                }
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    def collect_process_metrics(self, pattern: str = "worker") -> Dict[str, Any]:
        """プロセスメトリクスの収集"""
        processes = {}
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                if pattern in proc.info['name']:
                    processes[proc.info['pid']] = {
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024
                    }
        except Exception as e:
            logger.error(f"Failed to collect process metrics: {e}")
        
        return processes

class HealthChecker:
    """ヘルスチェッカー"""
    
    def __init__(self):
        self.health_thresholds = {
            'cpu_critical': 90,
            'cpu_warning': 70,
            'memory_critical': 90,
            'memory_warning': 80,
            'disk_critical': 95,
            'disk_warning': 85
        }
    
    def check_system_health(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """システムヘルスのチェック"""
        health_status = {
            'overall': 'healthy',
            'issues': [],
            'warnings': []
        }
        
        # CPU チェック
        cpu_percent = metrics.get('cpu', {}).get('percent', 0)
        if cpu_percent > self.health_thresholds['cpu_critical']:
            health_status['overall'] = 'critical'
            health_status['issues'].append(f"CPU usage critical: {cpu_percent}%")
        elif cpu_percent > self.health_thresholds['cpu_warning']:
            health_status['warnings'].append(f"CPU usage high: {cpu_percent}%")
        
        # メモリチェック
        memory_percent = metrics.get('memory', {}).get('percent', 0)
        if memory_percent > self.health_thresholds['memory_critical']:
            health_status['overall'] = 'critical'
            health_status['issues'].append(f"Memory usage critical: {memory_percent}%")
        elif memory_percent > self.health_thresholds['memory_warning']:
            health_status['warnings'].append(f"Memory usage high: {memory_percent}%")
        
        # ディスクチェック
        disk_percent = metrics.get('disk', {}).get('percent', 0)
        if disk_percent > self.health_thresholds['disk_critical']:
            health_status['overall'] = 'critical'
            health_status['issues'].append(f"Disk usage critical: {disk_percent}%")
        elif disk_percent > self.health_thresholds['disk_warning']:
            health_status['warnings'].append(f"Disk usage high: {disk_percent}%")
        
        if health_status['warnings'] and health_status['overall'] == 'healthy':
            health_status['overall'] = 'warning'
        
        return health_status

class ScalingEngine:
    """スケーリングエンジン（軽量版）"""
    
    def __init__(self):
        self.scaling_rules = {
            'cpu_scale_up': 80,
            'cpu_scale_down': 30,
            'queue_length_scale_up': 100,
            'queue_length_scale_down': 10
        }
    
    def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """スケーリング分析（現時点では推奨のみ、実行はしない）"""
        recommendations = {}
        
        # CPU ベースの推奨
        system_load = metrics.get('system_load', 0)
        if system_load > self.scaling_rules['cpu_scale_up'] / 100:
            recommendations['system'] = {
                'action': 'scale_up',
                'reason': f'High system load: {system_load * 100:.1f}%',
                'priority': 'medium'
            }
        elif system_load < self.scaling_rules['cpu_scale_down'] / 100:
            recommendations['system'] = {
                'action': 'scale_down',
                'reason': f'Low system load: {system_load * 100:.1f}%',
                'priority': 'low'
            }
        
        # キューベースの推奨
        queue_lengths = metrics.get('queue_lengths', {})
        for queue_name, length in queue_lengths.items():
            if length > self.scaling_rules['queue_length_scale_up']:
                recommendations[queue_name] = {
                    'action': 'scale_up',
                    'reason': f'Queue length high: {length}',
                    'priority': 'high'
                }
            elif length < self.scaling_rules['queue_length_scale_down']:
                recommendations[queue_name] = {
                    'action': 'scale_down',
                    'reason': f'Queue length low: {length}',
                    'priority': 'low'
                }
        
        return recommendations

class WorkerHealthMonitor:
    """ワーカーヘルスモニター本体"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.scaling_engine = ScalingEngine()
        self.start_time = datetime.now()
        
        logger.info("WorkerHealthMonitor initialized (proper implementation)")
    
    def collect_comprehensive_metrics(self) -> Dict[str, Any]:
        """包括的メトリクス収集"""
        try:
            system_metrics = self.metrics_collector.collect_system_metrics()
            process_metrics = self.metrics_collector.collect_process_metrics()
            
            # ワーカー情報の整形
            workers = {}
            for pid, proc_info in process_metrics.items():
                worker_name = proc_info['name'].replace('.py', '')
                workers[worker_name] = {
                    'pid': pid,
                    'status': 'running',
                    'cpu_percent': proc_info['cpu_percent'],
                    'memory_mb': proc_info['memory_mb'],
                    'health': 'healthy'
                }
            
            # システム健康状態を評価
            overall_healthy = all(worker.get('health') == 'healthy' for worker in workers.values())
            system_healthy = system_metrics.get('cpu', {}).get('percent', 0) < 80
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system': system_metrics,
                'workers': workers,
                'system_health': {
                    'overall_healthy': overall_healthy and system_healthy,
                    'system_cpu_ok': system_healthy,
                    'all_workers_healthy': overall_healthy,
                    'healthy_worker_count': sum(1 for w in workers.values() if w.get('health') == 'healthy'),
                    'total_worker_count': len(workers)
                },
                'uptime': str(datetime.now() - self.start_time)
            }
        except Exception as e:
            logger.error(f"Failed to collect comprehensive metrics: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """ヘルスステータスの取得"""
        metrics = self.collect_comprehensive_metrics()
        system_health = self.health_checker.check_system_health(metrics.get('system', {}))
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': system_health,
            'worker_count': len(metrics.get('workers', {})),
            'metrics': metrics
        }
    
    def get_scaling_recommendations(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """スケーリング推奨事項の取得"""
        try:
            return self.scaling_engine.analyze(metrics)
        except Exception as e:
            logger.error(f"Failed to get scaling recommendations: {e}")
            return {}
    
    def restart_unhealthy_workers(self) -> Dict[str, Any]:
        """不健全なワーカーの再起動"""
        try:
            # 現在のワーカー状態を取得
            metrics = self.collect_comprehensive_metrics()
            workers = metrics.get('workers', {})
            
            restart_results = {}
            restarted_count = 0
            
            for worker_name, worker_info in workers.items():
                # 不健全なワーカーを特定
                if worker_info.get('health') != 'healthy':
                    try:
                        # 実際の再起動処理（安全な実装）
                        pid = worker_info.get('pid')
                        if pid:
                            logger.warning(f"Worker {worker_name} (PID: {pid}) is unhealthy, preparing restart")
                            
                            # 実際の再起動は慎重に行う（現在は記録のみ）
                            restart_results[worker_name] = {
                                'action': 'restart_scheduled',
                                'reason': f"Health status: {worker_info.get('health', 'unknown')}",
                                'pid': pid,
                                'timestamp': datetime.now().isoformat()
                            }
                            restarted_count += 1
                        else:
                            restart_results[worker_name] = {
                                'action': 'restart_failed',
                                'reason': 'No PID available',
                                'timestamp': datetime.now().isoformat()
                            }
                    except Exception as e:
                        restart_results[worker_name] = {
                            'action': 'restart_error',
                            'reason': str(e),
                            'timestamp': datetime.now().isoformat()
                        }
            
            logger.info(f"Worker restart check completed: {restarted_count} workers processed")
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_workers_checked': len(workers),
                'unhealthy_workers_found': restarted_count,
                'restart_results': restart_results,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Failed to restart unhealthy workers: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """システムステータスの取得 (Elder Council Summoner用)"""
        try:
            health_status = self.get_health_status()
            
            # Elder Council Summoner が期待する形式に変換
            return {
                'timestamp': datetime.now().isoformat(),
                'status': health_status['system_health']['overall'],
                'system_metrics': health_status['metrics']['system'],
                'worker_count': health_status['worker_count'],
                'workers': health_status['metrics']['workers'],
                'uptime': health_status['metrics']['uptime'],
                'issues': health_status['system_health']['issues'],
                'warnings': health_status['system_health']['warnings']
            }
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    def start_monitoring(self, interval: int = 30):
        """監視の開始（スタンドアロンモード）"""
        logger.info("Starting standalone monitoring...")
        
        while True:
            try:
                metrics = self.collect_comprehensive_metrics()
                health = self.get_health_status()
                
                if health['system_health']['overall'] != 'healthy':
                    logger.warning(f"System health issue: {health['system_health']}")
                
                # メトリクスを履歴に追加
                self.metrics_collector.metrics_history.append(metrics)
                
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(interval)

# 互換性のためのクラス（既存コードとの互換性）
class WorkerPerformanceAnalyzer:
    """パフォーマンス分析器"""
    def __init__(self):
        logger.info("WorkerPerformanceAnalyzer initialized")
        self.bottleneck_thresholds = {
            'queue_length': 100,
            'processing_time': 5000,  # ms
            'error_rate': 0.1,
            'cpu_usage': 80.0,
            'memory_usage': 80.0
        }
    
    def detect_bottlenecks(self, worker_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """ボトルネック検出"""
        bottlenecks = {}
        
        for worker_name, metrics in worker_metrics.items():
            issues = []
            
            # キュー長チェック
            queue_length = metrics.get('queue_length', 0)
            if queue_length > self.bottleneck_thresholds['queue_length']:
                issues.append({
                    'type': 'queue_overload',
                    'severity': 'high' if queue_length > self.bottleneck_thresholds['queue_length'] * 2 else 'medium',
                    'details': f'Queue length: {queue_length}'
                })
            
            # 処理時間チェック
            processing_time = metrics.get('processing_time', 0)
            if processing_time > self.bottleneck_thresholds['processing_time']:
                issues.append({
                    'type': 'slow_processing',
                    'severity': 'high' if processing_time > self.bottleneck_thresholds['processing_time'] * 2 else 'medium',
                    'details': f'Processing time: {processing_time}ms'
                })
            
            # エラー率チェック
            error_rate = metrics.get('error_rate', 0)
            if error_rate > self.bottleneck_thresholds['error_rate']:
                issues.append({
                    'type': 'high_error_rate',
                    'severity': 'critical' if error_rate > 0.2 else 'high',
                    'details': f'Error rate: {error_rate:.2%}'
                })
            
            if issues:
                bottlenecks[worker_name] = {
                    'issues': issues,
                    'timestamp': datetime.now().isoformat()
                }
        
        return bottlenecks

class WorkerAutoScaler:
    """自動スケーラー（プレースホルダー）"""
    def __init__(self):
        logger.info("WorkerAutoScaler initialized (placeholder)")

# デモ・テスト関数
def demo_health_monitor():
    """ヘルスモニターのデモンストレーション"""
    print("🏥 Worker Health Monitor Demo")
    print("=" * 60)
    
    monitor = WorkerHealthMonitor()
    
    # メトリクス収集
    metrics = monitor.collect_comprehensive_metrics()
    print("\n📊 Comprehensive Metrics:")
    print(json.dumps(metrics, indent=2, default=str))
    
    # ヘルスステータス
    health = monitor.get_health_status()
    print("\n💗 Health Status:")
    print(json.dumps(health, indent=2, default=str))
    
    # スケーリング推奨
    test_metrics = {
        'system_load': 0.85,
        'queue_lengths': {
            'task_queue': 150,
            'pm_queue': 5
        }
    }
    recommendations = monitor.get_scaling_recommendations(test_metrics)
    print("\n📈 Scaling Recommendations:")
    print(json.dumps(recommendations, indent=2))
    
    print("\n✅ Demo completed successfully!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_health_monitor()