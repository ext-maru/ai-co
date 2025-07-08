#!/usr/bin/env python3
"""
System Recovery - システム全体の復旧機能
インシデント賢者の高度な治癒能力
"""

import subprocess
import time
import psutil
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class SystemRecovery:
    """システム復旧の専門クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_co_path = Path("/home/aicompany/ai_co")
        self.recovery_log = []
        
        # 重要なシステムコンポーネント
        self.critical_components = {
            'rabbitmq': {'service': 'rabbitmq-server', 'port': 5672},
            'postgresql': {'service': 'postgresql', 'port': 5432},
            'nginx': {'service': 'nginx', 'port': 80},
            'redis': {'service': 'redis-server', 'port': 6379}
        }
        
        self.logger.info("🏥 SystemRecovery initialized - システム復旧システム起動")
    
    def full_system_diagnosis(self) -> Dict:
        """システム全体の診断"""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'system_health': {},
            'service_status': {},
            'resource_usage': {},
            'network_connectivity': {},
            'critical_issues': [],
            'recovery_recommendations': []
        }
        
        # システムヘルス
        diagnosis['system_health'] = self._check_system_health()
        
        # サービス状態
        diagnosis['service_status'] = self._check_services()
        
        # リソース使用状況
        diagnosis['resource_usage'] = self._check_resource_usage()
        
        # ネットワーク接続
        diagnosis['network_connectivity'] = self._check_network()
        
        # 問題分析
        diagnosis['critical_issues'] = self._analyze_critical_issues(diagnosis)
        
        # 復旧推奨
        diagnosis['recovery_recommendations'] = self._generate_recovery_plan(diagnosis)
        
        return diagnosis
    
    def emergency_recovery(self, severity: str = 'high') -> Dict:
        """緊急時復旧プロセス"""
        recovery_result = {
            'start_time': datetime.now().isoformat(),
            'severity': severity,
            'steps_executed': [],
            'success_steps': [],
            'failed_steps': [],
            'final_status': 'unknown'
        }
        
        # 重要度に応じた復旧手順
        if severity == 'critical':
            steps = self._get_critical_recovery_steps()
        elif severity == 'high':
            steps = self._get_high_recovery_steps()
        else:
            steps = self._get_standard_recovery_steps()
        
        for step_name, step_func in steps:
            recovery_result['steps_executed'].append(step_name)
            self.logger.info(f"🔧 Executing recovery step: {step_name}")
            
            try:
                success = step_func()
                if success:
                    recovery_result['success_steps'].append(step_name)
                    self.logger.info(f"✅ {step_name} completed successfully")
                else:
                    recovery_result['failed_steps'].append(step_name)
                    self.logger.warning(f"⚠️ {step_name} failed")
                
                # クリティカルステップが失敗した場合は停止
                if not success and severity == 'critical':
                    break
                    
            except Exception as e:
                recovery_result['failed_steps'].append(step_name)
                self.logger.error(f"❌ {step_name} error: {str(e)}")
        
        # 最終状態評価
        recovery_result['final_status'] = self._evaluate_recovery_success(recovery_result)
        recovery_result['end_time'] = datetime.now().isoformat()
        
        # ログ記録
        self.recovery_log.append(recovery_result)
        
        return recovery_result
    
    def _check_system_health(self) -> Dict:
        """システムヘルスチェック"""
        health = {}
        
        try:
            # CPU使用率
            health['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            health['memory_percent'] = memory.percent
            health['memory_available_gb'] = memory.available / (1024**3)
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            health['disk_percent'] = (disk.used / disk.total) * 100
            health['disk_free_gb'] = disk.free / (1024**3)
            
            # ロードアベレージ
            load_avg = psutil.getloadavg()
            health['load_average'] = {
                '1min': load_avg[0],
                '5min': load_avg[1],
                '15min': load_avg[2]
            }
            
            # アップタイム
            boot_time = psutil.boot_time()
            health['uptime_hours'] = (time.time() - boot_time) / 3600
            
        except Exception as e:
            health['error'] = str(e)
        
        return health
    
    def _check_services(self) -> Dict:
        """重要サービスの状態確認"""
        services = {}
        
        for service_name, config in self.critical_components.items():
            try:
                # サービス状態確認
                result = subprocess.run(['systemctl', 'is-active', config['service']], 
                                      capture_output=True, text=True, timeout=5)
                
                services[service_name] = {
                    'service_status': result.stdout.strip(),
                    'is_running': result.returncode == 0,
                    'port_check': self._check_port(config['port'])
                }
                
            except Exception as e:
                services[service_name] = {
                    'error': str(e),
                    'is_running': False
                }
        
        return services
    
    def _check_resource_usage(self) -> Dict:
        """リソース使用状況詳細"""
        resources = {}
        
        try:
            # プロセス別CPU/メモリ使用量
            ai_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'ai_co' in cmdline or 'worker' in cmdline.lower():
                        ai_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent'],
                            'cmdline': cmdline[:100]  # 制限
                        })
                except:
                    continue
            
            resources['ai_processes'] = ai_processes
            resources['total_ai_processes'] = len(ai_processes)
            
            # ネットワーク統計
            net_io = psutil.net_io_counters()
            resources['network_io'] = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
            
        except Exception as e:
            resources['error'] = str(e)
        
        return resources
    
    def _check_network(self) -> Dict:
        """ネットワーク接続確認"""
        network = {}
        
        # 重要な接続先テスト
        test_hosts = [
            ('localhost', 'localhost'),
            ('rabbitmq', '127.0.0.1'),
            ('external', '8.8.8.8')
        ]
        
        for name, host in test_hosts:
            try:
                result = subprocess.run(['ping', '-c', '1', '-W', '3', host], 
                                      capture_output=True, timeout=5)
                network[name] = {
                    'reachable': result.returncode == 0,
                    'host': host
                }
            except:
                network[name] = {
                    'reachable': False,
                    'host': host,
                    'error': 'timeout'
                }
        
        return network
    
    def _check_port(self, port: int) -> bool:
        """ポート接続確認"""
        try:
            result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
            return f":{port}" in result.stdout
        except:
            return False
    
    def _analyze_critical_issues(self, diagnosis: Dict) -> List[Dict]:
        """クリティカルな問題を分析"""
        issues = []
        
        # CPU使用率チェック
        cpu_percent = diagnosis['system_health'].get('cpu_percent', 0)
        if cpu_percent > 90:
            issues.append({
                'type': 'high_cpu',
                'severity': 'critical',
                'description': f'CPU使用率が危険レベル: {cpu_percent}%',
                'recommendation': 'プロセス確認と不要プロセス終了'
            })
        
        # メモリ使用率チェック
        memory_percent = diagnosis['system_health'].get('memory_percent', 0)
        if memory_percent > 95:
            issues.append({
                'type': 'high_memory',
                'severity': 'critical',
                'description': f'メモリ使用率が危険レベル: {memory_percent}%',
                'recommendation': 'メモリリーク確認とプロセス再起動'
            })
        
        # ディスク容量チェック
        disk_percent = diagnosis['system_health'].get('disk_percent', 0)
        if disk_percent > 90:
            issues.append({
                'type': 'low_disk_space',
                'severity': 'high',
                'description': f'ディスク使用率が高い: {disk_percent}%',
                'recommendation': 'ログファイルクリーンアップ'
            })
        
        # サービス停止チェック
        for service_name, status in diagnosis['service_status'].items():
            if not status.get('is_running', False):
                issues.append({
                    'type': 'service_down',
                    'severity': 'high',
                    'description': f'{service_name}サービスが停止中',
                    'recommendation': f'{service_name}サービス再起動'
                })
        
        return issues
    
    def _generate_recovery_plan(self, diagnosis: Dict) -> List[str]:
        """復旧計画生成"""
        recommendations = []
        
        issues = diagnosis.get('critical_issues', [])
        for issue in issues:
            recommendations.append(issue['recommendation'])
        
        # 一般的な推奨事項
        if not issues:
            recommendations.append('システムは正常に動作しています')
        else:
            recommendations.append('定期的なシステム監視を継続')
            recommendations.append('ログファイルの定期クリーンアップ')
        
        return recommendations
    
    def _get_critical_recovery_steps(self) -> List[Tuple[str, callable]]:
        """クリティカル復旧手順"""
        return [
            ('kill_hung_processes', self._kill_hung_processes),
            ('restart_critical_services', self._restart_critical_services),
            ('clear_system_cache', self._clear_system_cache),
            ('restart_ai_workers', self._restart_ai_workers),
            ('verify_system_health', self._verify_system_health)
        ]
    
    def _get_high_recovery_steps(self) -> List[Tuple[str, callable]]:
        """高優先度復旧手順"""
        return [
            ('restart_ai_workers', self._restart_ai_workers),
            ('restart_critical_services', self._restart_critical_services),
            ('clear_queues', self._clear_queues),
            ('verify_connectivity', self._verify_connectivity)
        ]
    
    def _get_standard_recovery_steps(self) -> List[Tuple[str, callable]]:
        """標準復旧手順"""
        return [
            ('clear_logs', self._clear_old_logs),
            ('restart_workers', self._restart_ai_workers),
            ('health_check', self._verify_system_health)
        ]
    
    # === 復旧アクション実装 ===
    
    def _kill_hung_processes(self) -> bool:
        """ハングしたプロセスの強制終了"""
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'cmdline']):
                try:
                    # 長時間CPU使用率が100%のプロセスを対象
                    if proc.info['cpu_percent'] > 95:
                        cmdline = ' '.join(proc.info.get('cmdline', []))
                        if 'ai_co' in cmdline:
                            proc.terminate()
                            time.sleep(2)
                            if proc.is_running():
                                proc.kill()
                            killed_count += 1
                except:
                    continue
            
            self.logger.info(f"Killed {killed_count} hung processes")
            return True
        except:
            return False
    
    def _restart_critical_services(self) -> bool:
        """重要サービス再起動"""
        success_count = 0
        for service_name, config in self.critical_components.items():
            try:
                result = subprocess.run(['sudo', 'systemctl', 'restart', config['service']], 
                                      capture_output=True, timeout=30)
                if result.returncode == 0:
                    success_count += 1
                time.sleep(2)
            except:
                continue
        
        return success_count > 0
    
    def _clear_system_cache(self) -> bool:
        """システムキャッシュクリア"""
        try:
            # ページキャッシュクリア
            subprocess.run(['sudo', 'sync'], timeout=10)
            subprocess.run(['sudo', 'sh', '-c', 'echo 1 > /proc/sys/vm/drop_caches'], timeout=5)
            return True
        except:
            return False
    
    def _restart_ai_workers(self) -> bool:
        """AI ワーカー再起動"""
        try:
            # ai-stop
            subprocess.run([str(self.ai_co_path / 'commands' / 'ai_stop.py')], 
                          capture_output=True, timeout=30)
            time.sleep(3)
            
            # ai-start
            result = subprocess.run([str(self.ai_co_path / 'commands' / 'ai_start.py')], 
                                  capture_output=True, timeout=60)
            return result.returncode == 0
        except:
            return False
    
    def _clear_queues(self) -> bool:
        """キュークリア"""
        try:
            result = subprocess.run([str(self.ai_co_path / 'commands' / 'ai_queue_clear.py')], 
                                  capture_output=True, timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def _clear_old_logs(self) -> bool:
        """古いログファイルクリア"""
        try:
            logs_dir = self.ai_co_path / 'logs'
            if logs_dir.exists():
                # 7日より古いログファイルを削除
                subprocess.run(['find', str(logs_dir), '-name', '*.log', '-mtime', '+7', '-delete'], 
                              capture_output=True, timeout=30)
            return True
        except:
            return False
    
    def _verify_system_health(self) -> bool:
        """システムヘルス検証"""
        try:
            health = self._check_system_health()
            cpu_ok = health.get('cpu_percent', 100) < 80
            memory_ok = health.get('memory_percent', 100) < 80
            disk_ok = health.get('disk_percent', 100) < 80
            
            return cpu_ok and memory_ok and disk_ok
        except:
            return False
    
    def _verify_connectivity(self) -> bool:
        """接続確認"""
        try:
            network = self._check_network()
            return all(host_info.get('reachable', False) for host_info in network.values())
        except:
            return False
    
    def _evaluate_recovery_success(self, recovery_result: Dict) -> str:
        """復旧成功度評価"""
        total_steps = len(recovery_result['steps_executed'])
        success_steps = len(recovery_result['success_steps'])
        
        if total_steps == 0:
            return 'no_action'
        
        success_rate = success_steps / total_steps
        
        if success_rate >= 0.8:
            return 'success'
        elif success_rate >= 0.5:
            return 'partial_success'
        else:
            return 'failed'
    
    def generate_recovery_report(self) -> str:
        """復旧レポート生成"""
        if not self.recovery_log:
            return "復旧履歴がありません"
        
        report = ["# 🏥 システム復旧レポート\n"]
        
        for i, recovery in enumerate(self.recovery_log[-5:], 1):  # 最新5件
            report.append(f"## 復旧セッション {i}")
            report.append(f"- 開始時刻: {recovery['start_time']}")
            report.append(f"- 重要度: {recovery['severity']}")
            report.append(f"- 最終状態: {recovery['final_status']}")
            report.append(f"- 実行ステップ: {len(recovery['steps_executed'])}")
            report.append(f"- 成功ステップ: {len(recovery['success_steps'])}")
            report.append(f"- 失敗ステップ: {len(recovery['failed_steps'])}\n")
        
        return "\n".join(report)