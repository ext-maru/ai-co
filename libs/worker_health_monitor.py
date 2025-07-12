#!/usr/bin/env python3
"""
Worker Health Monitor - ワーカー健全性監視システム
Created: 2025-07-12
Author: Claude Elder (Emergency Implementation)
Priority: CRITICAL
"""

import asyncio
import json
import logging
import os
import psutil
import socket
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class WorkerStatus(Enum):
    """ワーカー状態"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    STOPPED = "stopped"
    UNKNOWN = "unknown"

class HealthMetric(Enum):
    """健全性メトリック"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    UPTIME = "uptime"
    QUEUE_LENGTH = "queue_length"

@dataclass
class WorkerHealthData:
    """ワーカー健全性データ"""
    worker_id: str
    worker_type: str
    status: WorkerStatus
    pid: Optional[int]
    cpu_percent: float
    memory_mb: float
    uptime_seconds: float
    response_time_ms: float
    error_count: int
    success_count: int
    queue_length: int
    last_activity: datetime
    health_score: float
    issues: List[str]

    @property
    def error_rate(self) -> float:
        total_requests = self.error_count + self.success_count
        if total_requests == 0:
            return 0.0
        return (self.error_count / total_requests) * 100

@dataclass
class SystemHealthSummary:
    """システム健全性サマリー"""
    total_workers: int
    healthy_workers: int
    warning_workers: int
    critical_workers: int
    stopped_workers: int
    overall_health_score: float
    system_load: float
    memory_usage_percent: float
    critical_issues: List[str]
    recommendations: List[str]
class WorkerHealthMonitor:
    """ワーカー健全性監視システム"""

    def __init__(self, config_path: Optional[str] = None):
        """初期化"""
        self.config = self._load_config(config_path)
        self.worker_data: Dict[str, WorkerHealthData] = {}
        self.health_history: deque = deque(maxlen=1000)

        # 閾値設定
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'response_time_warning': 1000.0,  # ms
            'response_time_critical': 5000.0,  # ms
            'error_rate_warning': 5.0,  # %
            'error_rate_critical': 15.0,  # %
            'min_uptime': 300.0,  # 5分
        }

        # 監視設定
        self.monitoring_active = False
        self.monitor_thread = None
        self.monitor_interval = 30  # 30秒間隔

        # Worker discovery
        self.known_workers = self._discover_workers()

        logger.info("WorkerHealthMonitor initialized")

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """設定読み込み"""
        default_config = {
            'monitor_interval': 30,
            'health_retention_hours': 24,
            'worker_discovery_enabled': True,
            'auto_recovery_enabled': False
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

        return default_config

    def _discover_workers(self) -> Dict[str, Dict]:
        """ワーカー自動発見"""
        workers = {}

        try:
            # Dockerコンテナベースのワーカー発見
            containers = self._get_docker_containers()
            for container in containers:
                if any(keyword in container['name'].lower()
                      for keyword in ['worker', 'task', 'job', 'processor']):
                    workers[container['name']] = {
                        'type': 'docker_container',
                        'container_id': container['id'],
                        'status': container['status']
                    }

            # プロセスベースのワーカー発見
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    cmdline = ' '.join(proc_info.get('cmdline', []))

                    # Python worker processes
                    if ('python' in proc_info['name'] and
                        any(keyword in cmdline.lower()
                            for keyword in ['worker', 'celery', 'rq', 'dramatiq'])):

                        worker_id = f"proc_{proc_info['pid']}"
                        workers[worker_id] = {
                            'type': 'process',
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline': cmdline
                        }

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # RabbitMQ Queue workers (推定)
            rabbitmq_queues = self._get_rabbitmq_queues()
            for queue_name in rabbitmq_queues:
                worker_id = f"queue_{queue_name}"
                workers[worker_id] = {
                    'type': 'queue_worker',
                    'queue_name': queue_name,
                    'estimated': True
                }

        except Exception as e:
            logger.error(f"Worker discovery failed: {e}")

        logger.info(f"Discovered {len(workers)} workers")
        return workers

    def _get_docker_containers(self) -> List[Dict]:
        """Dockerコンテナ一覧取得"""
        containers = []
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.ID}}\t{{.Names}}\t{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            containers.append({
                                'id': parts[0],
                                'name': parts[1],
                                'status': parts[2]
                            })

        except Exception as e:
            logger.warning(f"Failed to get docker containers: {e}")

        return containers

    def _get_rabbitmq_queues(self) -> List[str]:
        """RabbitMQキュー一覧取得"""
        queues = []
        try:
            # 既知のキュー名
            known_queues = [
                'ai_tasks', 'ai_pm', 'ai_results',
                'dialog_task_queue', 'worker_tasks'
            ]

            # RabbitMQ Management APIで確認（実装簡略化）
            queues.extend(known_queues)

        except Exception as e:
            logger.warning(f"Failed to get RabbitMQ queues: {e}")

        return queues

    def start_monitoring(self):
        """監視開始"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("Worker health monitoring started")

    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("Worker health monitoring stopped")

    def _monitoring_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # ワーカー健全性データ収集
                self._collect_worker_health_data()

                # 健全性評価
                self._evaluate_worker_health()

                # 履歴保存
                self._save_health_snapshot()

                # 自動回復（有効な場合）
                if self.config.get('auto_recovery_enabled', False):
                    self._attempt_auto_recovery()

                time.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)

    def _collect_worker_health_data(self):
        """ワーカー健全性データ収集"""
        current_time = datetime.now()

        for worker_id, worker_info in self.known_workers.items():
            try:
                health_data = self._get_worker_health(worker_id, worker_info)
                self.worker_data[worker_id] = health_data

            except Exception as e:
                logger.warning(f"Failed to collect health data for {worker_id}: {e}")
                # エラー時はSTOPPED状態として記録
                self.worker_data[worker_id] = WorkerHealthData(
                    worker_id=worker_id,
                    worker_type=worker_info.get('type', 'unknown'),
                    status=WorkerStatus.STOPPED,
                    pid=None,
                    cpu_percent=0.0,
                    memory_mb=0.0,
                    uptime_seconds=0.0,
                    response_time_ms=0.0,
                    error_count=0,
                    success_count=0,
                    queue_length=0,
                    last_activity=current_time,
                    health_score=0.0,
                    issues=['Failed to collect health data']
                )

    def _get_worker_health(self, worker_id: str, worker_info: Dict) -> WorkerHealthData:
        """個別ワーカー健全性取得"""
        worker_type = worker_info.get('type', 'unknown')
        current_time = datetime.now()

        if worker_type == 'docker_container':
            return self._get_container_health(worker_id, worker_info)
        elif worker_type == 'process':
            return self._get_process_health(worker_id, worker_info)
        elif worker_type == 'queue_worker':
            return self._get_queue_worker_health(worker_id, worker_info)
        else:
            # 不明な種類のワーカー
            return WorkerHealthData(
                worker_id=worker_id,
                worker_type=worker_type,
                status=WorkerStatus.UNKNOWN,
                pid=None,
                cpu_percent=0.0,
                memory_mb=0.0,
                uptime_seconds=0.0,
                response_time_ms=0.0,
                error_count=0,
                success_count=0,
                queue_length=0,
                last_activity=current_time,
                health_score=0.0,
                issues=['Unknown worker type']
            )

    def _get_container_health(self, worker_id: str, worker_info: Dict) -> WorkerHealthData:
        """Dockerコンテナ健全性取得"""
        container_id = worker_info.get('container_id')
        current_time = datetime.now()

        try:
            # Docker stats取得
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format',
                 '{{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.PIDs}}',
                 container_id],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split('\t')
                if len(parts) >= 3:
                    cpu_str = parts[1].replace('%', '')
                    memory_str = parts[2].split('/')[0].strip()

                    cpu_percent = float(cpu_str) if cpu_str != '--' else 0.0

                    # メモリをMBに変換
                    memory_mb = self._parse_memory_string(memory_str)

                    # コンテナ稼働時間取得
                    uptime = self._get_container_uptime(container_id)

                    # 健全性スコア計算
                    health_score = self._calculate_health_score(
                        cpu_percent, memory_mb, 0.0, 0.0
                    )

                    # 状態判定
                    status = self._determine_status(cpu_percent, memory_mb, 0.0, 0.0)

                    return WorkerHealthData(
                        worker_id=worker_id,
                        worker_type='docker_container',
                        status=status,
                        pid=None,
                        cpu_percent=cpu_percent,
                        memory_mb=memory_mb,
                        uptime_seconds=uptime,
                        response_time_ms=0.0,
                        error_count=0,
                        success_count=1,
                        queue_length=0,
                        last_activity=current_time,
                        health_score=health_score,
                        issues=self._identify_issues(cpu_percent, memory_mb, 0.0, 0.0)
                    )

        except Exception as e:
            logger.warning(f"Failed to get container health for {worker_id}: {e}")

        # エラー時のデフォルト
        return WorkerHealthData(
            worker_id=worker_id,
            worker_type='docker_container',
            status=WorkerStatus.UNKNOWN,
            pid=None,
            cpu_percent=0.0,
            memory_mb=0.0,
            uptime_seconds=0.0,
            response_time_ms=0.0,
            error_count=1,
            success_count=0,
            queue_length=0,
            last_activity=current_time,
            health_score=0.0,
            issues=['Failed to get container stats']
        )

    def _get_process_health(self, worker_id: str, worker_info: Dict) -> WorkerHealthData:
        """プロセス健全性取得"""
        pid = worker_info.get('pid')
        current_time = datetime.now()

        try:
            proc = psutil.Process(pid)

            # CPU・メモリ使用量
            cpu_percent = proc.cpu_percent()
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # 稼働時間
            create_time = proc.create_time()
            uptime = time.time() - create_time

            # 健全性スコア計算
            health_score = self._calculate_health_score(
                cpu_percent, memory_mb, 0.0, 0.0
            )

            # 状態判定
            status = self._determine_status(cpu_percent, memory_mb, 0.0, 0.0)

            return WorkerHealthData(
                worker_id=worker_id,
                worker_type='process',
                status=status,
                pid=pid,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                uptime_seconds=uptime,
                response_time_ms=0.0,
                error_count=0,
                success_count=1,
                queue_length=0,
                last_activity=current_time,
                health_score=health_score,
                issues=self._identify_issues(cpu_percent, memory_mb, 0.0, 0.0)
            )

        except psutil.NoSuchProcess:
            return WorkerHealthData(
                worker_id=worker_id,
                worker_type='process',
                status=WorkerStatus.STOPPED,
                pid=pid,
                cpu_percent=0.0,
                memory_mb=0.0,
                uptime_seconds=0.0,
                response_time_ms=0.0,
                error_count=1,
                success_count=0,
                queue_length=0,
                last_activity=current_time,
                health_score=0.0,
                issues=['Process not found']
            )
        except Exception as e:
            logger.warning(f"Failed to get process health for {worker_id}: {e}")
            return WorkerHealthData(
                worker_id=worker_id,
                worker_type='process',
                status=WorkerStatus.UNKNOWN,
                pid=pid,
                cpu_percent=0.0,
                memory_mb=0.0,
                uptime_seconds=0.0,
                response_time_ms=0.0,
                error_count=1,
                success_count=0,
                queue_length=0,
                last_activity=current_time,
                health_score=0.0,
                issues=[f'Error: {str(e)}']
            )

    def _get_queue_worker_health(self, worker_id: str, worker_info: Dict) -> WorkerHealthData:
        """キューワーカー健全性取得"""
        queue_name = worker_info.get('queue_name')
        current_time = datetime.now()

        try:
            # キューの長さを推定（実装簡略化）
            queue_length = 0  # 実際にはRabbitMQ APIで取得

            # キューが存在することをもって健全とみなす
            health_score = 80.0 if queue_length < 100 else 40.0
            status = WorkerStatus.HEALTHY if queue_length < 100 else WorkerStatus.WARNING

            return WorkerHealthData(
                worker_id=worker_id,
                worker_type='queue_worker',
                status=status,
                pid=None,
                cpu_percent=0.0,
                memory_mb=0.0,
                uptime_seconds=0.0,
                response_time_ms=0.0,
                error_count=0,
                success_count=1,
                queue_length=queue_length,
                last_activity=current_time,
                health_score=health_score,
                issues=[]
            )

        except Exception as e:
            return WorkerHealthData(
                worker_id=worker_id,
                worker_type='queue_worker',
                status=WorkerStatus.UNKNOWN,
                pid=None,
                cpu_percent=0.0,
                memory_mb=0.0,
                uptime_seconds=0.0,
                response_time_ms=0.0,
                error_count=1,
                success_count=0,
                queue_length=0,
                last_activity=current_time,
                health_score=0.0,
                issues=[f'Queue health check failed: {str(e)}']
            )

    def _parse_memory_string(self, memory_str: str) -> float:
        """メモリ文字列をMBに変換"""
        try:
            memory_str = memory_str.upper().strip()

            if 'GB' in memory_str:
                return float(memory_str.replace('GB', '')) * 1024
            elif 'MB' in memory_str:
                return float(memory_str.replace('MB', ''))
            elif 'KB' in memory_str:
                return float(memory_str.replace('KB', '')) / 1024
            elif 'B' in memory_str:
                return float(memory_str.replace('B', '')) / 1024 / 1024
            else:
                return float(memory_str)
        except:
            return 0.0

    def _get_container_uptime(self, container_id: str) -> float:
        """コンテナ稼働時間取得"""
        try:
            result = subprocess.run(
                ['docker', 'inspect', '--format', '{{.State.StartedAt}}', container_id],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                started_at_str = result.stdout.strip()
                # ISO形式の時刻をパース
                started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                return (datetime.now(started_at.tzinfo) - started_at).total_seconds()
        except:
            pass

        return 0.0

    def _calculate_health_score(self, cpu_percent: float, memory_mb: float,
                               response_time: float, error_rate: float) -> float:
        """健全性スコア計算"""
        score = 100.0

        # CPU使用率による減点
        if cpu_percent > self.thresholds['cpu_critical']:
            score -= 40
        elif cpu_percent > self.thresholds['cpu_warning']:
            score -= 20

        # メモリ使用率による減点（1GB以上を基準）
        if memory_mb > 1024:  # 1GB
            score -= min(30, (memory_mb - 1024) / 1024 * 10)

        # レスポンス時間による減点
        if response_time > self.thresholds['response_time_critical']:
            score -= 30
        elif response_time > self.thresholds['response_time_warning']:
            score -= 15

        # エラー率による減点
        if error_rate > self.thresholds['error_rate_critical']:
            score -= 25
        elif error_rate > self.thresholds['error_rate_warning']:
            score -= 10

        return max(0.0, score)

    def _determine_status(self, cpu_percent: float, memory_mb: float,
                         response_time: float, error_rate: float) -> WorkerStatus:
        """状態判定"""
        critical_conditions = [
            cpu_percent > self.thresholds['cpu_critical'],
            memory_mb > 2048,  # 2GB
            response_time > self.thresholds['response_time_critical'],
            error_rate > self.thresholds['error_rate_critical']
        ]

        warning_conditions = [
            cpu_percent > self.thresholds['cpu_warning'],
            memory_mb > 1024,  # 1GB
            response_time > self.thresholds['response_time_warning'],
            error_rate > self.thresholds['error_rate_warning']
        ]

        if any(critical_conditions):
            return WorkerStatus.CRITICAL
        elif any(warning_conditions):
            return WorkerStatus.WARNING
        else:
            return WorkerStatus.HEALTHY

    def _identify_issues(self, cpu_percent: float, memory_mb: float,
                        response_time: float, error_rate: float) -> List[str]:
        """問題特定"""
        issues = []

        if cpu_percent > self.thresholds['cpu_critical']:
            issues.append(f'Critical CPU usage: {cpu_percent:.1f}%')
        elif cpu_percent > self.thresholds['cpu_warning']:
            issues.append(f'High CPU usage: {cpu_percent:.1f}%')

        if memory_mb > 2048:
            issues.append(f'Critical memory usage: {memory_mb:.1f}MB')
        elif memory_mb > 1024:
            issues.append(f'High memory usage: {memory_mb:.1f}MB')

        if response_time > self.thresholds['response_time_critical']:
            issues.append(f'Critical response time: {response_time:.1f}ms')
        elif response_time > self.thresholds['response_time_warning']:
            issues.append(f'Slow response time: {response_time:.1f}ms')

        if error_rate > self.thresholds['error_rate_critical']:
            issues.append(f'Critical error rate: {error_rate:.1f}%')
        elif error_rate > self.thresholds['error_rate_warning']:
            issues.append(f'High error rate: {error_rate:.1f}%')

        return issues

    def _evaluate_worker_health(self):
        """ワーカー健全性評価"""
        # 全体評価ロジック
        pass

    def _save_health_snapshot(self):
        """健全性スナップショット保存"""
        snapshot = {
            'timestamp': datetime.now(),
            'worker_data': {
                worker_id: asdict(data)
                for worker_id, data in self.worker_data.items()
            }
        }
        self.health_history.append(snapshot)

    def _attempt_auto_recovery(self):
        """自動回復試行"""
        # 自動回復ロジック（実装簡略化）
        pass

    def get_system_status(self) -> Dict[str, Any]:
        """システム状況取得"""
        if not self.worker_data:
            # データがない場合は再発見を試行
            self.known_workers = self._discover_workers()
            self._collect_worker_health_data()

        total_workers = len(self.worker_data)

        # 状態別集計
        status_counts = defaultdict(int)
        total_health_score = 0.0

        for worker_data in self.worker_data.values():
            status_counts[worker_data.status.value] += 1
            total_health_score += worker_data.health_score

        avg_health_score = total_health_score / total_workers if total_workers > 0 else 0.0

        # システムリソース
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        return {
            'total_workers': total_workers,
            'health_summary': dict(status_counts),
            'overall_health_score': avg_health_score,
            'system_cpu_percent': cpu_percent,
            'system_memory_percent': memory.percent,
            'monitoring_active': self.monitoring_active,
            'last_update': datetime.now().isoformat(),
            'worker_details': {
                worker_id: {
                    'status': data.status.value,
                    'health_score': data.health_score,
                    'issues': data.issues
                }
                for worker_id, data in self.worker_data.items()
            }
        }

    def get_worker_details(self, worker_id: str) -> Optional[Dict]:
        """個別ワーカー詳細取得"""
        if worker_id in self.worker_data:
            return asdict(self.worker_data[worker_id])
        return None

    def force_health_check(self) -> Dict[str, Any]:
        """強制健全性チェック"""
        logger.info("Forcing health check...")

        # ワーカー再発見
        self.known_workers = self._discover_workers()

        # 健全性データ収集
        self._collect_worker_health_data()

        # 評価実行
        self._evaluate_worker_health()

        return self.get_system_status()

# グローバルインスタンス
_health_monitor = None

def get_health_monitor() -> WorkerHealthMonitor:
    """ヘルスモニターインスタンス取得"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = WorkerHealthMonitor()
    return _health_monitor

# エクスポート
__all__ = ['WorkerHealthMonitor', 'WorkerStatus', 'HealthMetric', 'get_health_monitor']

if __name__ == "__main__":
    # テスト実行
    monitor = WorkerHealthMonitor()
    monitor.start_monitoring()

    try:
        import time
        while True:
            status = monitor.get_system_status()
            print(f"System Status: {json.dumps(status, indent=2, default=str)}")
            time.sleep(30)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("Monitoring stopped")
