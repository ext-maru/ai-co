#!/usr/bin/env python3
"""
Worker Restart - AI Companyワーカー自動再起動
インシデント賢者のワーカー治癒術
"""

import subprocess
import time
import psutil
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class WorkerRestart:
    """AI Companyワーカー自動再起動システム"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_co_path = Path("/home/aicompany/ai_co")
        self.log_file = self.ai_co_path / "logs" / "worker_recovery.log"
        
        # ワーカー定義
        self.worker_types = {
            'task_worker': {
                'script': 'workers/async_task_worker_simple.py',
                'description': 'Main task processing worker',
                'critical': True
            },
            'result_worker': {
                'script': 'workers/async_result_worker_simple.py', 
                'description': 'Result processing worker',
                'critical': True
            },
            'pm_worker': {
                'script': 'workers/async_pm_worker_simple.py',
                'description': 'Project management worker',
                'critical': False
            },
            'dialog_worker': {
                'script': 'workers/dialog_task_worker.py',
                'description': 'Dialog processing worker',
                'critical': False
            }
        }
        
        self.restart_history = []
        self._setup_logging()
    
    def _setup_logging(self):
        """ログ設定"""
        self.log_file.parent.mkdir(exist_ok=True)
        
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def diagnose_workers(self) -> Dict:
        """ワーカー診断"""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'worker_status': {},
            'system_health': {},
            'issues_found': [],
            'recommendations': []
        }
        
        # 各ワーカーの状態確認
        for worker_name, config in self.worker_types.items():
            status = self._check_worker_status(worker_name, config)
            diagnosis['worker_status'][worker_name] = status
            
            if not status['is_running']:
                diagnosis['issues_found'].append(f"{worker_name} is not running")
            elif status['high_cpu']:
                diagnosis['issues_found'].append(f"{worker_name} has high CPU usage")
            elif status['high_memory']:
                diagnosis['issues_found'].append(f"{worker_name} has high memory usage")
        
        # システムヘルス
        diagnosis['system_health'] = self._check_system_health()
        
        # 推奨事項生成
        diagnosis['recommendations'] = self._generate_recommendations(diagnosis)
        
        return diagnosis
    
    def _check_worker_status(self, worker_name: str, config: Dict) -> Dict:
        """個別ワーカー状態確認"""
        status = {
            'is_running': False,
            'process_count': 0,
            'pids': [],
            'cpu_usage': 0,
            'memory_usage': 0,
            'high_cpu': False,
            'high_memory': False,
            'last_activity': None
        }
        
        script_name = config['script']
        
        # プロセス検索
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if script_name in cmdline:
                    status['is_running'] = True
                    status['process_count'] += 1
                    status['pids'].append(proc.info['pid'])
                    status['cpu_usage'] += proc.info['cpu_percent'] or 0
                    status['memory_usage'] += proc.info['memory_percent'] or 0
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 異常値判定
        status['high_cpu'] = status['cpu_usage'] > 80
        status['high_memory'] = status['memory_usage'] > 80
        
        # ログファイルから最終活動確認
        log_path = self.ai_co_path / "logs" / f"{worker_name}.log"
        if log_path.exists():
            try:
                mtime = log_path.stat().st_mtime
                status['last_activity'] = datetime.fromtimestamp(mtime).isoformat()
            except:
                pass
        
        return status
    
    def _check_system_health(self) -> Dict:
        """システム全体ヘルス確認"""
        health = {}
        
        try:
            # CPU・メモリ・ディスク
            health['cpu_percent'] = psutil.cpu_percent(interval=1)
            health['memory_percent'] = psutil.virtual_memory().percent
            health['disk_percent'] = psutil.disk_usage('/').percent
            
            # ロードアベレージ
            load_avg = psutil.getloadavg()
            health['load_average'] = load_avg[0]  # 1分平均
            
            # AI Companyプロセス数
            ai_process_count = 0
            for proc in psutil.process_iter(['cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'ai_co' in cmdline:
                        ai_process_count += 1
                except:
                    continue
            
            health['ai_process_count'] = ai_process_count
            
            # RabbitMQ 接続確認
            health['rabbitmq_available'] = self._check_rabbitmq()
            
        except Exception as e:
            health['error'] = str(e)
        
        return health
    
    def _check_rabbitmq(self) -> bool:
        """RabbitMQ 可用性確認"""
        try:
            result = subprocess.run(['systemctl', 'is-active', 'rabbitmq-server'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _generate_recommendations(self, diagnosis: Dict) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        # 停止中のワーカー
        stopped_workers = [name for name, status in diagnosis['worker_status'].items() 
                          if not status['is_running']]
        
        if stopped_workers:
            critical_stopped = [name for name in stopped_workers 
                              if self.worker_types[name]['critical']]
            if critical_stopped:
                recommendations.append(f"Critical workers stopped: {', '.join(critical_stopped)} - Immediate restart required")
            
            recommendations.append(f"Restart stopped workers: {', '.join(stopped_workers)}")
        
        # 高負荷ワーカー
        high_load_workers = [name for name, status in diagnosis['worker_status'].items() 
                           if status['high_cpu'] or status['high_memory']]
        
        if high_load_workers:
            recommendations.append(f"High resource usage workers: {', '.join(high_load_workers)} - Consider restart")
        
        # システムレベル
        system_health = diagnosis['system_health']
        if system_health.get('cpu_percent', 0) > 90:
            recommendations.append("High system CPU usage - Check for runaway processes")
        
        if system_health.get('memory_percent', 0) > 90:
            recommendations.append("High system memory usage - Memory cleanup recommended")
        
        if not system_health.get('rabbitmq_available', True):
            recommendations.append("RabbitMQ unavailable - Check message queue service")
        
        return recommendations
    
    def restart_worker(self, worker_name: str, force: bool = False) -> Dict:
        """個別ワーカー再起動"""
        restart_result = {
            'worker_name': worker_name,
            'start_time': datetime.now().isoformat(),
            'steps_completed': [],
            'success': False,
            'error': None
        }
        
        if worker_name not in self.worker_types:
            restart_result['error'] = f"Unknown worker type: {worker_name}"
            return restart_result
        
        config = self.worker_types[worker_name]
        script_path = self.ai_co_path / config['script']
        
        try:
            # Step 1: 現在のプロセス確認・停止
            restart_result['steps_completed'].append('process_check')
            current_status = self._check_worker_status(worker_name, config)
            
            if current_status['is_running']:
                restart_result['steps_completed'].append('process_termination')
                self._terminate_worker_processes(current_status['pids'], force)
                time.sleep(2)
            
            # Step 2: 環境確認
            restart_result['steps_completed'].append('environment_check')
            if not script_path.exists():
                restart_result['error'] = f"Worker script not found: {script_path}"
                return restart_result
            
            # Step 3: ワーカー開始
            restart_result['steps_completed'].append('worker_start')
            success = self._start_worker(script_path, worker_name)
            
            if success:
                # Step 4: 開始確認
                restart_result['steps_completed'].append('start_verification')
                time.sleep(3)
                
                new_status = self._check_worker_status(worker_name, config)
                if new_status['is_running']:
                    restart_result['success'] = True
                    restart_result['new_pid'] = new_status['pids'][0] if new_status['pids'] else None
                else:
                    restart_result['error'] = "Worker failed to start properly"
            else:
                restart_result['error'] = "Failed to start worker process"
        
        except Exception as e:
            restart_result['error'] = str(e)
        
        restart_result['end_time'] = datetime.now().isoformat()
        self.restart_history.append(restart_result)
        
        return restart_result
    
    def _terminate_worker_processes(self, pids: List[int], force: bool = False):
        """ワーカープロセス終了"""
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                if force:
                    proc.kill()
                else:
                    proc.terminate()
                    
                # 終了確認
                try:
                    proc.wait(timeout=5)
                except psutil.TimeoutExpired:
                    if not force:
                        proc.kill()
                        
            except psutil.NoSuchProcess:
                pass  # 既に終了済み
    
    def _start_worker(self, script_path: Path, worker_name: str) -> bool:
        """ワーカー開始"""
        try:
            # 仮想環境のpython を使用
            python_path = self.ai_co_path / "venv" / "bin" / "python"
            if not python_path.exists():
                python_path = "python3"  # フォールバック
            
            # バックグラウンドで開始
            cmd = [str(python_path), str(script_path)]
            
            process = subprocess.Popen(
                cmd,
                cwd=str(self.ai_co_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # プロセス開始確認
            time.sleep(1)
            return process.poll() is None
            
        except Exception as e:
            self.logger.error(f"Failed to start {worker_name}: {str(e)}")
            return False
    
    def restart_all_workers(self, only_critical: bool = False, force: bool = False) -> Dict:
        """全ワーカー再起動"""
        restart_all_result = {
            'start_time': datetime.now().isoformat(),
            'workers_restarted': [],
            'successful_restarts': [],
            'failed_restarts': [],
            'overall_success': False
        }
        
        workers_to_restart = []
        for worker_name, config in self.worker_types.items():
            if only_critical and not config['critical']:
                continue
            workers_to_restart.append(worker_name)
        
        # 各ワーカーを順次再起動
        for worker_name in workers_to_restart:
            restart_all_result['workers_restarted'].append(worker_name)
            
            restart_result = self.restart_worker(worker_name, force)
            
            if restart_result['success']:
                restart_all_result['successful_restarts'].append(worker_name)
                self.logger.info(f"✅ {worker_name} restarted successfully")
            else:
                restart_all_result['failed_restarts'].append({
                    'worker': worker_name,
                    'error': restart_result['error']
                })
                self.logger.error(f"❌ {worker_name} restart failed: {restart_result['error']}")
            
            # 短い間隔をあける
            time.sleep(1)
        
        # 全体成功判定
        success_count = len(restart_all_result['successful_restarts'])
        total_count = len(workers_to_restart)
        restart_all_result['overall_success'] = success_count == total_count
        
        restart_all_result['end_time'] = datetime.now().isoformat()
        
        return restart_all_result
    
    def emergency_recovery(self) -> Dict:
        """緊急時復旧"""
        recovery_result = {
            'start_time': datetime.now().isoformat(),
            'steps_executed': [],
            'recovery_actions': []
        }
        
        self.logger.info("🚨 Starting emergency worker recovery...")
        
        # Step 1: 診断
        recovery_result['steps_executed'].append('diagnosis')
        diagnosis = self.diagnose_workers()
        recovery_result['initial_diagnosis'] = diagnosis
        
        # Step 2: 重要ワーカーの強制再起動
        if diagnosis['issues_found']:
            recovery_result['steps_executed'].append('critical_restart')
            restart_result = self.restart_all_workers(only_critical=True, force=True)
            recovery_result['recovery_actions'].append({
                'action': 'critical_worker_restart',
                'result': restart_result
            })
        
        # Step 3: システムリソース確認
        recovery_result['steps_executed'].append('resource_check')
        system_health = diagnosis['system_health']
        
        if system_health.get('memory_percent', 0) > 95:
            # メモリクリーンアップ
            recovery_result['recovery_actions'].append({
                'action': 'memory_cleanup',
                'result': self._emergency_memory_cleanup()
            })
        
        # Step 4: RabbitMQ確認
        if not system_health.get('rabbitmq_available', True):
            recovery_result['steps_executed'].append('rabbitmq_recovery')
            rabbitmq_result = self._attempt_rabbitmq_recovery()
            recovery_result['recovery_actions'].append({
                'action': 'rabbitmq_recovery',
                'result': rabbitmq_result
            })
        
        # Step 5: 最終確認
        recovery_result['steps_executed'].append('final_verification')
        final_diagnosis = self.diagnose_workers()
        recovery_result['final_diagnosis'] = final_diagnosis
        
        # 復旧成功判定
        critical_workers_running = all(
            status['is_running'] for name, status in final_diagnosis['worker_status'].items()
            if self.worker_types[name]['critical']
        )
        
        recovery_result['recovery_successful'] = critical_workers_running
        recovery_result['end_time'] = datetime.now().isoformat()
        
        return recovery_result
    
    def _emergency_memory_cleanup(self) -> Dict:
        """緊急メモリクリーンアップ"""
        try:
            # ページキャッシュクリア
            subprocess.run(['sudo', 'sync'], timeout=10)
            subprocess.run(['sudo', 'sh', '-c', 'echo 1 > /proc/sys/vm/drop_caches'], timeout=5)
            
            return {'success': True, 'action': 'page_cache_cleared'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _attempt_rabbitmq_recovery(self) -> Dict:
        """RabbitMQ復旧試行"""
        try:
            # RabbitMQ再起動スクリプト実行
            rabbitmq_script = self.ai_co_path / "knowledge_base" / "incident_management" / "auto_fix" / "rabbitmq_recovery.sh"
            
            if rabbitmq_script.exists():
                result = subprocess.run(['bash', str(rabbitmq_script), 'full'], 
                                      capture_output=True, text=True, timeout=120)
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else None
                }
            else:
                # 基本的な再起動
                result = subprocess.run(['sudo', 'systemctl', 'restart', 'rabbitmq-server'], 
                                      capture_output=True, timeout=60)
                return {'success': result.returncode == 0}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_restart_statistics(self) -> Dict:
        """再起動統計"""
        if not self.restart_history:
            return {'total_restarts': 0}
        
        total_restarts = len(self.restart_history)
        successful_restarts = sum(1 for restart in self.restart_history if restart['success'])
        
        worker_restart_counts = {}
        for restart in self.restart_history:
            worker = restart['worker_name']
            worker_restart_counts[worker] = worker_restart_counts.get(worker, 0) + 1
        
        return {
            'total_restarts': total_restarts,
            'successful_restarts': successful_restarts,
            'success_rate': successful_restarts / total_restarts if total_restarts > 0 else 0,
            'worker_restart_counts': worker_restart_counts,
            'most_problematic_worker': max(worker_restart_counts.items(), key=lambda x: x[1])[0] if worker_restart_counts else None
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Company Worker Restart System")
    parser.add_argument('action', choices=['diagnose', 'restart', 'restart_all', 'emergency', 'stats'],
                       help="Action to perform")
    parser.add_argument('--worker', help="Specific worker name for restart action")
    parser.add_argument('--force', action='store_true', help="Force restart (kill instead of terminate)")
    parser.add_argument('--critical-only', action='store_true', help="Only restart critical workers")
    
    args = parser.parse_args()
    
    worker_restart = WorkerRestart()
    
    if args.action == 'diagnose':
        diagnosis = worker_restart.diagnose_workers()
        print(json.dumps(diagnosis, indent=2))
    
    elif args.action == 'restart':
        if not args.worker:
            print("Error: --worker required for restart action")
            return 1
        
        result = worker_restart.restart_worker(args.worker, args.force)
        print(json.dumps(result, indent=2))
        return 0 if result['success'] else 1
    
    elif args.action == 'restart_all':
        result = worker_restart.restart_all_workers(args.critical_only, args.force)
        print(json.dumps(result, indent=2))
        return 0 if result['overall_success'] else 1
    
    elif args.action == 'emergency':
        result = worker_restart.emergency_recovery()
        print(json.dumps(result, indent=2))
        return 0 if result['recovery_successful'] else 1
    
    elif args.action == 'stats':
        stats = worker_restart.get_restart_statistics()
        print(json.dumps(stats, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())