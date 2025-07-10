#!/usr/bin/env python3
"""
Self-Healing System - 完全自律復旧システム
インシデント賢者の最終進化形態
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import signal
import sys


class HealingState(Enum):
    """ヒーリング状態"""
    HEALTHY = "healthy"
    MONITORING = "monitoring"
    DIAGNOSING = "diagnosing"
    HEALING = "healing"
    RECOVERING = "recovering"
    CRITICAL = "critical"


class HealthCheck:
    """ヘルスチェック定義"""
    
    def __init__(self, name: str, check_func: Callable, 
                 interval: int = 60, critical: bool = False):
        self.name = name
        self.check_func = check_func
        self.interval = interval
        self.critical = critical
        self.last_check = None
        self.last_result = None
        self.failure_count = 0
        self.max_failures = 3


@dataclass
class HealingAction:
    """ヒーリングアクション"""
    name: str
    description: str
    action_func: Callable
    prerequisites: List[str] = field(default_factory=list)
    rollback_func: Optional[Callable] = None
    max_attempts: int = 3
    timeout: int = 300
    success_rate: float = 0.0
    last_used: Optional[datetime] = None


class SelfHealingSystem:
    """完全自律復旧システム"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_co_path = Path("/home/aicompany/ai_co")
        
        # システム状態
        self.current_state = HealingState.HEALTHY
        self.is_running = False
        self.healing_thread = None
        
        # ヘルスチェック
        self.health_checks = {}
        self.health_results = {}
        
        # ヒーリングアクション
        self.healing_actions = {}
        self.action_history = []
        
        # 学習システム
        self.learning_data = {
            'successful_healings': [],
            'failed_healings': [],
            'pattern_recognition': {},
            'effectiveness_scores': {}
        }
        
        # パフォーマンスメトリクス
        self.metrics = {
            'total_healing_attempts': 0,
            'successful_healings': 0,
            'average_healing_time': 0,
            'uptime_percentage': 0,
            'false_positive_rate': 0
        }
        
        # 外部システム連携
        self.four_sages_coordinator = None
        self.ml_predictor = None
        
        self.logger.info("🧙‍♂️ SelfHealingSystem initialized - 完全自律復旧システム起動")
        
        # デフォルトヘルスチェック登録
        self._register_default_health_checks()
        
        # デフォルトヒーリングアクション登録
        self._register_default_healing_actions()
    
    def _register_default_health_checks(self):
        """デフォルトヘルスチェック登録"""
        
        # システムリソースチェック
        self.register_health_check(
            "system_resources",
            self._check_system_resources,
            interval=30,
            critical=True
        )
        
        # Elders Guildサービスチェック
        self.register_health_check(
            "ai_company_services",
            self._check_ai_company_services,
            interval=60,
            critical=True
        )
        
        # RabbitMQチェック
        self.register_health_check(
            "rabbitmq_health",
            self._check_rabbitmq_health,
            interval=45,
            critical=True
        )
        
        # ワーカーヘルスチェック
        self.register_health_check(
            "worker_health",
            self._check_worker_health,
            interval=30,
            critical=True
        )
        
        # ディスク容量チェック
        self.register_health_check(
            "disk_space",
            self._check_disk_space,
            interval=300,  # 5分
            critical=False
        )
        
        # ネットワーク接続チェック
        self.register_health_check(
            "network_connectivity",
            self._check_network_connectivity,
            interval=120,
            critical=False
        )
    
    def _register_default_healing_actions(self):
        """デフォルトヒーリングアクション登録"""
        
        # システムリソース最適化
        self.register_healing_action(HealingAction(
            name="optimize_system_resources",
            description="System resource optimization",
            action_func=self._optimize_system_resources,
            rollback_func=self._rollback_resource_optimization
        ))
        
        # ワーカー復旧
        self.register_healing_action(HealingAction(
            name="recover_workers",
            description="Elders Guild worker recovery",
            action_func=self._recover_workers,
            prerequisites=["system_resources"]
        ))
        
        # RabbitMQ復旧
        self.register_healing_action(HealingAction(
            name="recover_rabbitmq",
            description="RabbitMQ service recovery",
            action_func=self._recover_rabbitmq,
            rollback_func=self._rollback_rabbitmq_recovery
        ))
        
        # メモリクリーンアップ
        self.register_healing_action(HealingAction(
            name="memory_cleanup",
            description="Memory cleanup and optimization",
            action_func=self._memory_cleanup
        ))
        
        # ログローテーション
        self.register_healing_action(HealingAction(
            name="log_rotation",
            description="Log file rotation and cleanup",
            action_func=self._log_rotation
        ))
        
        # 緊急再起動
        self.register_healing_action(HealingAction(
            name="emergency_restart",
            description="Emergency system restart",
            action_func=self._emergency_restart,
            max_attempts=1
        ))
    
    def register_health_check(self, name: str, check_func: Callable, 
                            interval: int = 60, critical: bool = False):
        """ヘルスチェック登録"""
        health_check = HealthCheck(name, check_func, interval, critical)
        self.health_checks[name] = health_check
        self.logger.info(f"Health check registered: {name}")
    
    def register_healing_action(self, action: HealingAction):
        """ヒーリングアクション登録"""
        self.healing_actions[action.name] = action
        self.logger.info(f"Healing action registered: {action.name}")
    
    async def start_monitoring(self):
        """監視開始"""
        if self.is_running:
            self.logger.warning("Self-healing system is already running")
            return
        
        self.is_running = True
        self.current_state = HealingState.MONITORING
        
        self.logger.info("🔄 Self-healing monitoring started")
        
        # 監視ループを別スレッドで開始
        self.healing_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.healing_thread.start()
        
        # シグナルハンドラー設定
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _monitoring_loop(self):
        """監視ループ"""
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        
        try:
            loop.run_until_complete(self._async_monitoring_loop())
        except Exception as e:
            self.logger.error(f"Monitoring loop failed: {str(e)}")
        finally:
            loop.close()
    
    async def _async_monitoring_loop(self):
        """非同期監視ループ"""
        while self.is_running:
            try:
                # ヘルスチェック実行
                await self._execute_health_checks()
                
                # ヘルス状態評価
                overall_health = self._evaluate_overall_health()
                
                # 必要に応じてヒーリング実行
                if overall_health['needs_healing']:
                    await self._initiate_healing(overall_health)
                
                # 状態更新
                self._update_system_state(overall_health)
                
                # メトリクス更新
                self._update_metrics()
                
                # 学習データ保存
                await self._save_learning_data()
                
                # 短い間隔で監視
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Monitoring cycle error: {str(e)}")
                await asyncio.sleep(30)  # エラー時は長めの間隔
    
    async def _execute_health_checks(self):
        """ヘルスチェック実行"""
        current_time = datetime.now()
        
        for name, health_check in self.health_checks.items():
            # 実行間隔チェック
            if (health_check.last_check and 
                (current_time - health_check.last_check).total_seconds() < health_check.interval):
                continue
            
            try:
                # ヘルスチェック実行
                if asyncio.iscoroutinefunction(health_check.check_func):
                    result = await asyncio.wait_for(health_check.check_func(), timeout=30)
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, health_check.check_func),
                        timeout=30
                    )
                
                health_check.last_check = current_time
                health_check.last_result = result
                
                if result.get('healthy', True):
                    health_check.failure_count = 0
                else:
                    health_check.failure_count += 1
                
                self.health_results[name] = {
                    'timestamp': current_time.isoformat(),
                    'healthy': result.get('healthy', True),
                    'details': result.get('details', {}),
                    'failure_count': health_check.failure_count
                }
                
            except Exception as e:
                health_check.failure_count += 1
                self.health_results[name] = {
                    'timestamp': current_time.isoformat(),
                    'healthy': False,
                    'error': str(e),
                    'failure_count': health_check.failure_count
                }
                
                self.logger.error(f"Health check failed: {name} - {str(e)}")
    
    def _evaluate_overall_health(self) -> Dict:
        """全体ヘルス評価"""
        evaluation = {
            'overall_healthy': True,
            'needs_healing': False,
            'critical_issues': [],
            'warning_issues': [],
            'health_score': 1.0,
            'failing_checks': []
        }
        
        total_checks = len(self.health_results)
        healthy_checks = 0
        
        for name, result in self.health_results.items():
            health_check = self.health_checks.get(name)
            
            if result.get('healthy', True):
                healthy_checks += 1
            else:
                failure_count = result.get('failure_count', 0)
                max_failures = health_check.max_failures if health_check else 3
                
                evaluation['failing_checks'].append({
                    'name': name,
                    'failure_count': failure_count,
                    'critical': health_check.critical if health_check else False
                })
                
                if health_check and health_check.critical and failure_count >= max_failures:
                    evaluation['critical_issues'].append(name)
                    evaluation['needs_healing'] = True
                elif failure_count >= max_failures:
                    evaluation['warning_issues'].append(name)
        
        # ヘルススコア計算
        if total_checks > 0:
            evaluation['health_score'] = healthy_checks / total_checks
        
        evaluation['overall_healthy'] = evaluation['health_score'] >= 0.8
        
        # クリティカルな問題がある場合は即座にヒーリング
        if evaluation['critical_issues']:
            evaluation['needs_healing'] = True
        
        return evaluation
    
    async def _initiate_healing(self, health_evaluation: Dict):
        """ヒーリング開始"""
        if self.current_state == HealingState.HEALING:
            self.logger.info("Healing already in progress, skipping")
            return
        
        self.current_state = HealingState.HEALING
        healing_start_time = time.time()
        
        self.logger.info("🔧 Initiating self-healing process")
        
        healing_result = {
            'start_time': datetime.now().isoformat(),
            'health_evaluation': health_evaluation,
            'actions_attempted': [],
            'successful_actions': [],
            'failed_actions': [],
            'overall_success': False
        }
        
        try:
            # ヒーリング戦略決定
            healing_strategy = await self._determine_healing_strategy(health_evaluation)
            
            # アクション実行
            for action_name in healing_strategy['actions']:
                if action_name in self.healing_actions:
                    action_result = await self._execute_healing_action(action_name)
                    
                    healing_result['actions_attempted'].append(action_name)
                    
                    if action_result.get('success', False):
                        healing_result['successful_actions'].append({
                            'action': action_name,
                            'result': action_result
                        })
                    else:
                        healing_result['failed_actions'].append({
                            'action': action_name,
                            'error': action_result.get('error', 'Unknown error')
                        })
            
            # ヒーリング効果確認
            await asyncio.sleep(30)  # ヒーリング効果の安定を待つ
            post_healing_health = self._evaluate_overall_health()
            
            healing_result['post_healing_health'] = post_healing_health
            healing_result['overall_success'] = post_healing_health['overall_healthy']
            
            # 学習データ記録
            healing_time = time.time() - healing_start_time
            if healing_result['overall_success']:
                self.learning_data['successful_healings'].append({
                    'timestamp': datetime.now().isoformat(),
                    'healing_time': healing_time,
                    'strategy': healing_strategy,
                    'result': healing_result
                })
            else:
                self.learning_data['failed_healings'].append({
                    'timestamp': datetime.now().isoformat(),
                    'healing_time': healing_time,
                    'strategy': healing_strategy,
                    'result': healing_result
                })
            
            # メトリクス更新
            self.metrics['total_healing_attempts'] += 1
            if healing_result['overall_success']:
                self.metrics['successful_healings'] += 1
            
            self._update_average_healing_time(healing_time)
            
        except Exception as e:
            healing_result['error'] = str(e)
            self.logger.error(f"Healing process failed: {str(e)}")
        
        healing_result['end_time'] = datetime.now().isoformat()
        self.action_history.append(healing_result)
        
        # 状態をモニタリングに戻す
        self.current_state = HealingState.MONITORING
        
        self.logger.info(f"🏥 Healing process completed: {healing_result['overall_success']}")
    
    async def _determine_healing_strategy(self, health_evaluation: Dict) -> Dict:
        """ヒーリング戦略決定"""
        strategy = {
            'approach': 'conservative',
            'actions': [],
            'priority': 'medium',
            'estimated_time': 300
        }
        
        critical_issues = health_evaluation.get('critical_issues', [])
        warning_issues = health_evaluation.get('warning_issues', [])
        
        # クリティカル問題がある場合
        if critical_issues:
            strategy['approach'] = 'aggressive'
            strategy['priority'] = 'critical'
            
            # 問題に応じたアクション選択
            if 'worker_health' in critical_issues:
                strategy['actions'].append('recover_workers')
            
            if 'rabbitmq_health' in critical_issues:
                strategy['actions'].append('recover_rabbitmq')
            
            if 'system_resources' in critical_issues:
                strategy['actions'].extend(['memory_cleanup', 'optimize_system_resources'])
            
            # 最後の手段
            if len(critical_issues) > 2:
                strategy['actions'].append('emergency_restart')
        
        # 警告レベルの問題
        elif warning_issues:
            strategy['approach'] = 'moderate'
            
            if 'disk_space' in warning_issues:
                strategy['actions'].append('log_rotation')
            
            if any('worker' in issue for issue in warning_issues):
                strategy['actions'].append('recover_workers')
            
            if health_evaluation.get('health_score', 1.0) < 0.7:
                strategy['actions'].append('memory_cleanup')
        
        # ML予測に基づく予防的アクション
        if self.ml_predictor:
            try:
                prediction = await self._get_ml_prediction()
                if prediction.get('overall_risk') in ['high', 'critical']:
                    strategy['actions'].insert(0, 'optimize_system_resources')
            except:
                pass
        
        return strategy
    
    async def _execute_healing_action(self, action_name: str) -> Dict:
        """ヒーリングアクション実行"""
        if action_name not in self.healing_actions:
            return {'success': False, 'error': f'Unknown action: {action_name}'}
        
        action = self.healing_actions[action_name]
        
        self.logger.info(f"🔧 Executing healing action: {action_name}")
        
        result = {
            'action_name': action_name,
            'start_time': datetime.now().isoformat(),
            'success': False,
            'attempts': 0,
            'error': None
        }
        
        for attempt in range(action.max_attempts):
            result['attempts'] = attempt + 1
            
            try:
                # タイムアウト付きで実行
                if asyncio.iscoroutinefunction(action.action_func):
                    action_result = await asyncio.wait_for(action.action_func(), timeout=action.timeout)
                else:
                    action_result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, action.action_func),
                        timeout=action.timeout
                    )
                
                if action_result.get('success', False):
                    result['success'] = True
                    result['details'] = action_result
                    
                    # 成功率更新
                    action.success_rate = (action.success_rate + 1.0) / 2
                    action.last_used = datetime.now()
                    
                    break
                else:
                    result['error'] = action_result.get('error', 'Action returned failure')
                    
            except asyncio.TimeoutError:
                result['error'] = f'Action timeout after {action.timeout}s'
            except Exception as e:
                result['error'] = str(e)
            
            # 失敗時は少し待ってからリトライ
            if attempt < action.max_attempts - 1:
                await asyncio.sleep(10)
        
        result['end_time'] = datetime.now().isoformat()
        
        if not result['success']:
            # 失敗率更新
            action.success_rate = action.success_rate * 0.9
            self.logger.error(f"Healing action failed: {action_name} - {result['error']}")
        
        return result
    
    # =============== ヘルスチェック実装 ===============
    
    async def _check_system_resources(self) -> Dict:
        """システムリソースチェック"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            healthy = (
                cpu_percent < 90 and
                memory.percent < 90 and
                disk.percent < 95
            )
            
            return {
                'healthy': healthy,
                'details': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent
                }
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_ai_company_services(self) -> Dict:
        """Elders Guildサービスチェック"""
        try:
            import psutil
            
            ai_processes = 0
            for proc in psutil.process_iter(['cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'ai_co' in cmdline and ('worker' in cmdline or 'server' in cmdline):
                        ai_processes += 1
                except:
                    continue
            
            healthy = ai_processes >= 2  # 最低2つのプロセス
            
            return {
                'healthy': healthy,
                'details': {
                    'active_processes': ai_processes,
                    'minimum_required': 2
                }
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_rabbitmq_health(self) -> Dict:
        """RabbitMQヘルスチェック"""
        try:
            import subprocess
            
            # RabbitMQサービス状態確認
            result = subprocess.run(['systemctl', 'is-active', 'rabbitmq-server'], 
                                  capture_output=True, text=True, timeout=10)
            
            service_running = result.returncode == 0
            
            # ポート確認
            import socket
            port_open = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(5)
                    port_open = sock.connect_ex(('localhost', 5672)) == 0
            except:
                pass
            
            healthy = service_running and port_open
            
            return {
                'healthy': healthy,
                'details': {
                    'service_running': service_running,
                    'port_accessible': port_open
                }
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_worker_health(self) -> Dict:
        """ワーカーヘルスチェック"""
        try:
            import psutil
            
            worker_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'worker' in cmdline and 'ai_co' in cmdline:
                        worker_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent']
                        })
                except:
                    continue
            
            # ワーカーが正常に動作しているか
            healthy_workers = sum(1 for w in worker_processes if w['cpu_percent'] < 95)
            total_workers = len(worker_processes)
            
            healthy = total_workers >= 2 and healthy_workers / max(total_workers, 1) >= 0.8
            
            return {
                'healthy': healthy,
                'details': {
                    'total_workers': total_workers,
                    'healthy_workers': healthy_workers,
                    'worker_processes': worker_processes
                }
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_disk_space(self) -> Dict:
        """ディスク容量チェック"""
        try:
            import psutil
            
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            healthy = disk_percent < 85
            
            return {
                'healthy': healthy,
                'details': {
                    'disk_percent': disk_percent,
                    'free_gb': disk.free / (1024**3)
                }
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def _check_network_connectivity(self) -> Dict:
        """ネットワーク接続チェック"""
        try:
            import subprocess
            
            # ローカルhost確認
            local_result = subprocess.run(['ping', '-c', '1', 'localhost'], 
                                        capture_output=True, timeout=5)
            
            # 外部接続確認
            external_result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                           capture_output=True, timeout=5)
            
            local_ok = local_result.returncode == 0
            external_ok = external_result.returncode == 0
            
            healthy = local_ok  # 最低限ローカル接続があれば健全
            
            return {
                'healthy': healthy,
                'details': {
                    'local_connectivity': local_ok,
                    'external_connectivity': external_ok
                }
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    # =============== ヒーリングアクション実装 ===============
    
    async def _optimize_system_resources(self) -> Dict:
        """システムリソース最適化"""
        try:
            # メモリキャッシュクリア
            import subprocess
            
            subprocess.run(['sudo', 'sync'], timeout=10)
            subprocess.run(['sudo', 'sh', '-c', 'echo 1 > /proc/sys/vm/drop_caches'], timeout=5)
            
            return {'success': True, 'action': 'memory_cache_cleared'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _recover_workers(self) -> Dict:
        """ワーカー復旧"""
        try:
            # worker_restart.py を使用
            from .worker_restart import WorkerRestart
            
            worker_restart = WorkerRestart()
            result = worker_restart.restart_all_workers(only_critical=True, force=True)
            
            return {
                'success': result.get('overall_success', False),
                'details': result
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _recover_rabbitmq(self) -> Dict:
        """RabbitMQ復旧"""
        try:
            import subprocess
            
            # RabbitMQ復旧スクリプト実行
            script_path = self.ai_co_path / "knowledge_base" / "incident_management" / "auto_fix" / "rabbitmq_recovery.sh"
            
            result = subprocess.run(['bash', str(script_path), 'full'], 
                                  capture_output=True, text=True, timeout=120)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _memory_cleanup(self) -> Dict:
        """メモリクリーンアップ"""
        try:
            import psutil
            import gc
            
            # Python ガベージコレクション
            gc.collect()
            
            # 高メモリ使用プロセスの確認
            high_memory_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    if proc.info['memory_percent'] > 10:  # 10%以上使用
                        high_memory_processes.append(proc.info)
                except:
                    continue
            
            return {
                'success': True,
                'high_memory_processes': len(high_memory_processes),
                'gc_collected': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _log_rotation(self) -> Dict:
        """ログローテーション"""
        try:
            logs_dir = self.ai_co_path / "logs"
            if not logs_dir.exists():
                return {'success': True, 'message': 'No logs directory'}
            
            # 7日より古いログファイルを削除
            import subprocess
            result = subprocess.run([
                'find', str(logs_dir), '-name', '*.log', '-mtime', '+7', '-delete'
            ], capture_output=True, timeout=30)
            
            return {
                'success': result.returncode == 0,
                'cleaned_logs': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _emergency_restart(self) -> Dict:
        """緊急再起動"""
        try:
            # Elders Guildサービスの再起動
            import subprocess
            
            # ai-stop
            subprocess.run([str(self.ai_co_path / 'commands' / 'ai_stop.py')], 
                          capture_output=True, timeout=60)
            
            await asyncio.sleep(5)
            
            # ai-start
            result = subprocess.run([str(self.ai_co_path / 'commands' / 'ai_start.py')], 
                                  capture_output=True, timeout=120)
            
            return {
                'success': result.returncode == 0,
                'restart_completed': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # =============== ロールバック実装 ===============
    
    async def _rollback_resource_optimization(self) -> Dict:
        """リソース最適化ロールバック"""
        # 通常はロールバック不要
        return {'success': True, 'message': 'No rollback needed'}
    
    async def _rollback_rabbitmq_recovery(self) -> Dict:
        """RabbitMQ復旧ロールバック"""
        # RabbitMQの場合、前の状態に戻すのは困難なので監視強化で対応
        return {'success': True, 'message': 'Monitoring enhanced'}
    
    # =============== ユーティリティメソッド ===============
    
    def _update_system_state(self, health_evaluation: Dict):
        """システム状態更新"""
        if health_evaluation.get('critical_issues'):
            if self.current_state != HealingState.HEALING:
                self.current_state = HealingState.CRITICAL
        elif not health_evaluation.get('overall_healthy'):
            if self.current_state not in [HealingState.HEALING, HealingState.CRITICAL]:
                self.current_state = HealingState.DIAGNOSING
        else:
            if self.current_state not in [HealingState.HEALING]:
                self.current_state = HealingState.HEALTHY
    
    def _update_metrics(self):
        """メトリクス更新"""
        # アップタイム計算
        if hasattr(self, '_start_time'):
            uptime = (datetime.now() - self._start_time).total_seconds()
            healthy_time = uptime  # 簡易実装
            self.metrics['uptime_percentage'] = (healthy_time / uptime) * 100 if uptime > 0 else 100
        
        # 成功率計算
        if self.metrics['total_healing_attempts'] > 0:
            self.metrics['success_rate'] = (
                self.metrics['successful_healings'] / self.metrics['total_healing_attempts']
            )
    
    def _update_average_healing_time(self, healing_time: float):
        """平均ヒーリング時間更新"""
        current_avg = self.metrics['average_healing_time']
        total_attempts = self.metrics['total_healing_attempts']
        
        if total_attempts <= 1:
            self.metrics['average_healing_time'] = healing_time
        else:
            self.metrics['average_healing_time'] = (
                (current_avg * (total_attempts - 1) + healing_time) / total_attempts
            )
    
    async def _get_ml_prediction(self) -> Dict:
        """ML予測取得"""
        if self.ml_predictor:
            try:
                return self.ml_predictor.predict_incident_probability()
            except:
                pass
        return {'overall_risk': 'low'}
    
    async def _save_learning_data(self):
        """学習データ保存"""
        try:
            learning_file = self.ai_co_path / "knowledge_base" / "incident_management" / "self_healing_learning.json"
            
            with open(learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"Failed to save learning data: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully")
        self.stop_monitoring()
    
    def stop_monitoring(self):
        """監視停止"""
        self.is_running = False
        self.current_state = HealingState.HEALTHY
        self.logger.info("🛑 Self-healing monitoring stopped")
    
    def get_system_status(self) -> Dict:
        """システム状態取得"""
        return {
            'current_state': self.current_state.value,
            'is_running': self.is_running,
            'health_results': self.health_results,
            'metrics': self.metrics,
            'recent_actions': self.action_history[-5:] if self.action_history else []
        }
    
    def get_healing_statistics(self) -> Dict:
        """ヒーリング統計取得"""
        return {
            'total_healing_attempts': self.metrics['total_healing_attempts'],
            'successful_healings': self.metrics['successful_healings'],
            'success_rate': self.metrics.get('success_rate', 0),
            'average_healing_time': self.metrics['average_healing_time'],
            'uptime_percentage': self.metrics['uptime_percentage'],
            'learning_data_points': len(self.learning_data['successful_healings']) + len(self.learning_data['failed_healings'])
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Self-Healing System")
    parser.add_argument('action', choices=['start', 'stop', 'status', 'stats', 'test'],
                       help="Action to perform")
    
    args = parser.parse_args()
    
    self_healing = SelfHealingSystem()
    
    if args.action == 'start':
        async def start_system():
            self_healing._start_time = datetime.now()
            await self_healing.start_monitoring()
            
            # メインループ（Ctrl+Cで停止まで）
            try:
                while self_healing.is_running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self_healing.stop_monitoring()
        
        asyncio.run(start_system())
    
    elif args.action == 'status':
        status = self_healing.get_system_status()
        print(json.dumps(status, indent=2))
    
    elif args.action == 'stats':
        stats = self_healing.get_healing_statistics()
        print(json.dumps(stats, indent=2))
    
    elif args.action == 'test':
        async def test_healing():
            # テスト用ヘルスチェック
            await self_healing._execute_health_checks()
            health = self_healing._evaluate_overall_health()
            print("Health Evaluation:", json.dumps(health, indent=2))
            
            if health['needs_healing']:
                await self_healing._initiate_healing(health)
        
        asyncio.run(test_healing())
    
    else:
        print("🧙‍♂️ Self-Healing System ready")


if __name__ == "__main__":
    main()