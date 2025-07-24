#!/usr/bin/env python3
"""
"📊" Auto Issue Processor A2A Monitoring & Observability System
監視・可観測性・運用ダッシュボード構築システム

Issue #193対応: リアルタイム処理ダッシュボード・包括的ログシステム・メトリクス監視
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import threading
from urllib.parse import quote
import weakref

logger = logging.getLogger("MonitoringSystem")


class MetricType(Enum):
    """MetricTypeクラス"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """AlertSeverityクラス"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """HealthStatusクラス"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class MetricPoint:
    """メトリクスポイント"""
    value: Union[int, float]
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """アラート"""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    component: str
    metric_name: str
    current_value: Union[int, float]
    threshold: Union[int, float]
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """ヘルスチェック"""
    component: str
    status: HealthStatus
    message: str
    last_check: datetime = field(default_factory=datetime.now)
    response_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """メトリクス収集システム"""
    
    def __init__(self)self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
    """初期化メソッド"""
        self.metric_types: Dict[str, MetricType] = {}
        self.metric_metadata: Dict[str, Dict[str, Any]] = {}
        
        # システムメトリクス
        self._setup_system_metrics()
    
    def _setup_system_metrics(self):
        """システムメトリクス設定"""
        system_metrics = [
            ("system.cpu_percent", MetricType.GAUGE),
            ("system.memory_percent", MetricType.GAUGE),
            ("system.disk_io_read", MetricType.COUNTER),
            ("system.disk_io_write", MetricType.COUNTER),
            ("a2a.total_issues_processed", MetricType.COUNTER),
            ("a2a.successful_issues", MetricType.COUNTER),
            ("a2a.failed_issues", MetricType.COUNTER),
            ("a2a.queue_size", MetricType.GAUGE),
            ("a2a.processing_time", MetricType.HISTOGRAM),
            ("claude_cli.execution_time", MetricType.HISTOGRAM),
            ("claude_cli.active_workers", MetricType.GAUGE),
            ("github_api.requests_total", MetricType.COUNTER),
            ("github_api.response_time", MetricType.HISTOGRAM),
        ]
        
        for metric_name, metric_type in system_metrics:
            self.metric_types[metric_name] = metric_type
    
    def record_metric(
        self, 
        name: str, 
        value: Union[int, float], 
        labels: Dict[str, str] = None,
        metric_type: MetricType = MetricType.GAUGE
    ):
        """メトリクス記録"""
        try:
            if name not in self.metric_types:
                self.metric_types[name] = metric_type
            
            point = MetricPoint(
                value=value,
                labels=labels or {}
            )
            
            self.metrics[name].append(point)
            
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {str(e)}")
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None)self.record_metric(name, value, labels, MetricType.COUNTER)
    """カウンター増加"""
    
    def set_gauge(self, name: str, value: Union[int, float], labels: Dict[str, str] = None)self.record_metric(name, value, labels, MetricType.GAUGE)
    """ゲージ設定"""
    
    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None)self.record_metric(name, duration, labels, MetricType.TIMER)
    """タイマー記録"""
    
    def get_metric_values(
        self, 
        name: str, 
        duration_minutes: int = 10
    ) -> List[MetricPoint]:
        """メトリクス値取得"""
        if name not in self.metrics:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [
            point for point in self.metrics[name]
            if point.timestamp > cutoff_time
        ]
    
    def get_latest_value(self, name: str) -> Optional[MetricPoint]:
        """最新値取得"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        return self.metrics[name][-1]
    
    def get_average_value(self, name: str, duration_minutes: int = 5) -> Optional[float]values = self.get_metric_values(name, duration_minutes):
    """均値取得""":
        if not values:
            return None
        
        return sum(point.value for point in values) / len(values)
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """全メトリクス概要取得"""
        summary = {}
        
        for name in self.metrics:
            latest = self.get_latest_value(name)
            average = self.get_average_value(name, 5)
            
            summary[name] = {
                "type": self.metric_types.get(name, MetricType.GAUGE).value,
                "latest_value": latest.value if latest else None,
                "latest_timestamp": latest.timestamp.isoformat() if latest else None,
                "average_5min": average,
                "total_points": len(self.metrics[name])
            }
        
        return summary


class AlertManager:
    """アラート管理システム"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        """初期化メソッド"""
        self.metrics_collector = metrics_collector
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.notification_handlers: List[Callable[[Alert], None]] = []
        
        # デフォルトアラートルール設定
        self._setup_default_alert_rules()
    
    def _setup_default_alert_rules(self):
        """デフォルトアラートルール設定"""
        self.alert_rules = {
            "high_cpu_usage": {
                "metric": "system.cpu_percent",
                "operator": ">",
                "threshold": 90.0,
                "severity": AlertSeverity.WARNING,
                "description": "High CPU usage detected"
            },
            "high_memory_usage": {
                "metric": "system.memory_percent",
                "operator": ">",
                "threshold": 90.0,
                "severity": AlertSeverity.WARNING,
                "description": "High memory usage detected"
            },
            "issue_processing_failure_rate": {
                "metric": "a2a.failed_issues",
                "operator": ">",
                "threshold": 5,
                "severity": AlertSeverity.ERROR,
                "description": "High issue processing failure rate"
            },
            "claude_cli_slow_response": {
                "metric": "claude_cli.execution_time",
                "operator": ">",
                "threshold": 60.0,
                "severity": AlertSeverity.WARNING,
                "description": "Claude CLI slow response time"
            },
            "large_queue_size": {
                "metric": "a2a.queue_size",
                "operator": ">",
                "threshold": 50,
                "severity": AlertSeverity.WARNING,
                "description": "Large issue processing queue"
            }
        }
    
    def add_alert_rule(
        self, 
        rule_name: str, 
        metric: str, 
        operator: str, 
        threshold: Union[int, float],
        severity: AlertSeverity,
        description: str
    ):
        """アラートルール追加"""
        self.alert_rules[rule_name] = {
            "metric": metric,
            "operator": operator,
            "threshold": threshold,
            "severity": severity,
            "description": description
        }
    
    def check_alerts(self):
        """アラートチェック実行"""
        try:
            for rule_name, rule in self.alert_rules.items():
                self._check_single_rule(rule_name, rule)
                
        except Exception as e:
            logger.error(f"Alert check failed: {str(e)}")
    
    def _check_single_rule(self, rule_name: str, rule: Dict[str, Any]):
        """単一ルールチェック"""
        try:
            metric_name = rule["metric"]
            operator = rule["operator"]
            threshold = rule["threshold"]
            severity = rule["severity"]
            description = rule["description"]
            
            # メトリクス値取得
            latest_value = self.metrics_collector.get_latest_value(metric_name)
            if not latest_value:
                return
            
            current_value = latest_value.value
            
            # しきい値チェック
            is_triggered = False
            if operator == ">":
                is_triggered = current_value > threshold
            elif operator == "<":
                is_triggered = current_value < threshold
            elif operator == ">=":
                is_triggered = current_value >= threshold
            elif operator == "<=":
                is_triggered = current_value <= threshold
            elif operator == "==":
                is_triggered = current_value == threshold
            
            alert_id = f"{rule_name}_{metric_name}"
            
            if is_triggered:
                # アラート発火
                if alert_id not in self.active_alerts:
                    alert = Alert(
                        alert_id=alert_id,
                        severity=severity,
                        title=f"Alert: {rule_name}",
                        description=description,
                        component="a2a_processor",
                        metric_name=metric_name,
                        current_value=current_value,
                        threshold=threshold,
                        metadata={
                            "rule_name": rule_name,
                            "operator": operator
                        }
                    )
                    
                    self.active_alerts[alert_id] = alert
                    self.alert_history.append(alert)
                    self._send_notification(alert)
                    
                    logger.warning(f"Alert triggered: {alert.title} - {alert.description}")
            
            else:
                # アラート解除
                if alert_id in self.active_alerts:
                    alert = self.active_alerts[alert_id]
                    alert.resolved_at = datetime.now()
                    del self.active_alerts[alert_id]
                    
                    logger.info(f"Alert resolved: {alert.title}")
                    
        except Exception as e:
            logger.error(f"Single rule check failed for {rule_name}: {str(e)}")
    
    def _send_notification(self, alert: Alert):
        """通知送信"""
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Notification handler failed: {str(e)}")
    
    def add_notification_handler(self, handler: Callable[[Alert], None])self.notification_handlers.append(handler)
    """通知ハンドラー追加"""
    
    def get_active_alerts(self) -> List[Alert]return list(self.active_alerts.values()):
    """クティブアラート取得"""
    :
    def get_alert_history(self, hours: int = 24) -> List[Alert]cutoff_time = datetime.now() - timedelta(hours=hours):
    """ラート履歴取得"""
        return [
            alert for alert in self.alert_history
            if alert.triggered_at > cutoff_time
        ]

:
class HealthMonitor:
    """ヘルスモニター"""
    
    def __init__(self):
        """初期化メソッド"""
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_functions: Dict[str, Callable[[], Tuple[HealthStatus, str, Dict[str, Any]]]] = {}
        
        # デフォルトヘルスチェック設定
        self._setup_default_health_checks()
    
    def _setup_default_health_checks(self):
        """デフォルトヘルスチェック設定"""
        self.check_functions = {
            "a2a_processor": self._check_a2a_processor_health,
            "claude_cli": self._check_claude_cli_health,
            "github_api": self._check_github_api_health,
            "security_manager": self._check_security_manager_health,
            "error_recovery": self._check_error_recovery_health
        }
    
    async def run_health_checks(self) -> Dict[str, HealthCheck]:
        """ヘルスチェック実行"""
        results = {}
        
        for component, check_func in self.check_functions.items():
            try:
                start_time = time.time()
                status, message, metadata = check_func()
                response_time = time.time() - start_time
                
                health_check = HealthCheck(
                    component=component,
                    status=status,
                    message=message,
                    response_time=response_time,
                    metadata=metadata
                )
                
                self.health_checks[component] = health_check
                results[component] = health_check
                
            except Exception as e:
                logger.error(f"Health check failed for {component}: {str(e)}")
                
                health_check = HealthCheck(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check error: {str(e)}",
                    metadata={"error": str(e)}
                )
                
                self.health_checks[component] = health_check
                results[component] = health_check
        
        return results
    
    def _check_a2a_processor_health(self) -> Tuple[HealthStatus, str, Dict[str, Any]]:
        """A2Aプロセッサーヘルスチェック"""
        try:
            # 簡単なヘルスチェック実装
            from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
            
            # プロセッサーインスタンス作成テスト
            processor = AutoIssueProcessor()
            capabilities = processor.get_capabilities()
            
            if capabilities and capabilities.get("service") == "AutoIssueProcessor":
                return HealthStatus.HEALTHY, "A2A processor is operational", {"capabilities": capabilities}
            else:
                return HealthStatus.DEGRADED, "A2A processor capabilities issue", {}
                
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"A2A processor error: {str(e)}", {"error": str(e)}
    
    def _check_claude_cli_health(self) -> Tuple[HealthStatus, str, Dict[str, Any]]:
        """Claude CLIヘルスチェック"""
        try:
            # Claude CLI実行プールの状態確認
            from libs.integrations.github.performance_optimizer import get_performance_optimizer
            
            optimizer = get_performance_optimizer()
            pool_stats = optimizer.execution_pool.get_pool_stats()
            
            current_workers = pool_stats["current_workers"]
            active_executions = pool_stats["active_executions"]
            
            if current_workers > 0:
                return HealthStatus.HEALTHY, f"Claude CLI pool healthy ({current_workers} workers)" \
                    "Claude CLI pool healthy ({current_workers} workers)", pool_stats
            else:
                return HealthStatus.DEGRADED, "No Claude CLI workers available", pool_stats
                
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Claude CLI health check error: {str(e)}", {"error": str(e)}
    
    def _check_github_api_health(self) -> Tuple[HealthStatus, str, Dict[str, Any]]:
        """GitHub APIヘルスチェック"""
        try:
            from libs.env_manager import EnvManager
            import requests
            
            github_token = EnvManager.get_github_token()
            if not github_token:
                return HealthStatus.UNHEALTHY, "GitHub token not configured", {}
            
            # GitHub API接続テスト
            headers = {"Authorization": f"token {github_token}"}
            # Security: Validate URL before making request
            response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            
            if response.status_code == 200:
                rate_limit = response.headers.get("X-RateLimit-Remaining", "unknown")
                return HealthStatus.HEALTHY, "GitHub API accessible", {"rate_limit_remaining": rate_limit}
            else:
                return HealthStatus.DEGRADED, f"GitHub API error: {
                    response.status_code}",
                    {"status_code": response.status_code
                }
                
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"GitHub API health check error: {str(e)}", {"error": str(e)}
    
    def _check_security_manager_health(self) -> Tuple[HealthStatus, str, Dict[str, Any]]:
        """セキュリティマネージャーヘルスチェック"""
        try:
            from libs.integrations.github.security_manager import get_security_manager
            
            security_manager = get_security_manager()
            
            # 簡単なセキュリティチェック
            test_input = {"test": "safe_data"}
            validation_result = security_manager.input_validator.validate_input(test_input)
            
            if validation_result["valid"]:
                return HealthStatus.HEALTHY, "Security manager operational", {"validation_test": "passed"}
            else:
                return HealthStatus.DEGRADED, "Security manager validation issue", validation_result
                
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Security manager health check error: {str(e)}", {"error": str(e)}
    
    def _check_error_recovery_health(self) -> Tuple[HealthStatus, str, Dict[str, Any]]:
        """エラー回復システムヘルスチェック"""
        try:
            from libs.integrations.github.error_recovery_system import get_error_recovery_system
            
            recovery_system = get_error_recovery_system()
            error_stats = recovery_system.get_error_statistics()
            
            total_errors = error_stats.get("total_errors", 0)
            recent_errors = error_stats.get("recent_errors", 0)
            
            if recent_errors < 10:  # 過去1時間で10件未満
                return HealthStatus.HEALTHY, "Error recovery system healthy", error_stats
            elif recent_errors < 50:
                return HealthStatus.DEGRADED, f"High error rate: {recent_errors} recent errors" \
                    "High error rate: {recent_errors} recent errors", error_stats
            else:
                return HealthStatus.UNHEALTHY, f"Very high error rate: {recent_errors} recent errors" \
                    "Very high error rate: {recent_errors} recent errors", error_stats
                
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Error recovery health check error: {str(e)}", {"error": str(e)}
    
    def get_overall_health(self) -> HealthStatus:
        """全体ヘルス状態取得"""
        if not self.health_checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in self.health_checks.values()]
        
        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED


class LogSystem:
    """包括的ログシステム"""
    
    def __init__(self)self.log_directory.mkdir(parents=True, exist_ok=True)
    """初期化メソッド"""
        
        # ログレベル別ファイル
        self.log_files = {
            "info": self.log_directory / "info.log",
            "warning": self.log_directory / "warning.log",
            "error": self.log_directory / "error.log",
            "metrics": self.log_directory / "metrics.log",
            "alerts": self.log_directory / "alerts.log",
            "health": self.log_directory / "health.log"
        }
        
        # ログローテーション設定
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.max_backup_count = 5
    
    def log_metric(self, metric_name: str, value: Union[int, float], labels: Dict[str, str] = None):
        """メトリクスログ"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "metric",
            "metric_name": metric_name,
            "value": value,
            "labels": labels or {}
        }
        
        self._write_log("metrics", json.dumps(log_entry))
    
    def log_alert(self, alert: Alert):
        """アラートログ"""
        log_entry = {
            "timestamp": alert.triggered_at.isoformat(),
            "type": "alert",
            "alert_id": alert.alert_id,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "component": alert.component,
            "current_value": alert.current_value,
            "threshold": alert.threshold
        }
        
        self._write_log("alerts", json.dumps(log_entry))
    
    def log_health_check(self, health_check: HealthCheck):
        """ヘルスチェックログ"""
        log_entry = {
            "timestamp": health_check.last_check.isoformat(),
            "type": "health_check",
            "component": health_check.component,
            "status": health_check.status.value,
            "message": health_check.message,
            "response_time": health_check.response_time
        }
        
        self._write_log("health", json.dumps(log_entry))
    
    def _write_log(self, log_type: str, message: str):
        """ログ書き込み"""
        try:
            log_file = self.log_files[log_type]
            
            # ログローテーションチェック
            if log_file.exists() and log_file.stat().st_size > self.max_log_size:
                self._rotate_log(log_file)
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{message}\n")
                
        except Exception as e:
            logger.error(f"Failed to write log: {str(e)}")
    
    def _rotate_log(self, log_file: Path):
        """ログローテーション"""
        try:
            # 既存のバックアップファイルをシフト
            for i in range(self.max_backup_count - 1, 0, -1):
                old_backup = log_file.with_suffix(f"{log_file.suffix}.{i}")
                new_backup = log_file.with_suffix(f"{log_file.suffix}.{i + 1}")
                
                if old_backup.exists():
                    if new_backup.exists():
                        new_backup.unlink()
                    old_backup.rename(new_backup)
            
            # 現在のログファイルを0.1にリネーム
            backup_file = log_file.with_suffix(f"{log_file.suffix}0.1")
            if backup_file.exists():
                backup_file.unlink()
            log_file.rename(backup_file)
            
        except Exception as e:
            logger.error(f"Log rotation failed: {str(e)}")


class MonitoringDashboard:
    """リアルタイム監視ダッシュボード"""
    
    def __init__(self)self.alert_manager = AlertManager(self.metrics_collector)
    """初期化メソッド"""
        self.health_monitor = HealthMonitor()
        self.log_system = LogSystem()
        
        # 監視設定
        self.monitoring_enabled = False
        self.monitoring_interval = 10.0  # 10秒間隔
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # 通知設定
        self._setup_notification_handlers()
    
    def _setup_notification_handlers(self)def log_alert_handler(alert: Alert):
    """通知ハンドラー設定"""
        """log_alert_handlerメソッド"""
            self.log_system.log_alert(alert)
        
        def console_alert_handler(alert: Alert)print(f"🚨 ALERT: {alert.title} - {alert.description}")
    """console_alert_handlerメソッド"""
        
        self.alert_manager.add_notification_handler(log_alert_handler)
        self.alert_manager.add_notification_handler(console_alert_handler)
    
    async def start_monitoring(self):
        """監視開始"""
        try:
            self.monitoring_enabled = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("Monitoring dashboard started")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {str(e)}")
    
    async def stop_monitoring(self):
        """監視停止"""
        try:
            self.monitoring_enabled = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Monitoring dashboard stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {str(e)}")
    
    async def _monitoring_loop(self):
        """監視ループ"""
        try:
            while self.monitoring_enabled:
                # システムメトリクス収集
                await self._collect_system_metrics()
                
                # A2Aメトリクス収集
                await self._collect_a2a_metrics()
                
                # アラートチェック
                self.alert_manager.check_alerts()
                
                # ヘルスチェック
                health_results = await self.health_monitor.run_health_checks()
                for health_check in health_results.values():
                    self.log_system.log_health_check(health_check)
                
                await asyncio.sleep(self.monitoring_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Monitoring loop error: {str(e)}")
    
    async def _collect_system_metrics(self):
        """システムメトリクス収集"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=None)
            self.metrics_collector.set_gauge("system.cpu_percent", cpu_percent)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            self.metrics_collector.set_gauge("system.memory_percent", memory.percent)
            
            # ディスクI/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self.metrics_collector.set_gauge(
                    "system.disk_io_read",
                    disk_io.read_bytes / (1024 * 1024)
                )
                self.metrics_collector.set_gauge(
                    "system.disk_io_write",
                    disk_io.write_bytes / (1024 * 1024)
                )
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {str(e)}")
    
    async def _collect_a2a_metrics(self):
        """A2Aメトリクス収集"""
        try:
            # パフォーマンス最適化システムからメトリクス取得
            from libs.integrations.github.performance_optimizer import get_performance_optimizer
            
            optimizer = get_performance_optimizer()
            pool_stats = optimizer.execution_pool.get_pool_stats()
            
            # Claude CLI関連メトリクス
            self.metrics_collector.set_gauge(
                "claude_cli.active_workers",
                pool_stats["current_workers"]
            )
            self.metrics_collector.set_gauge(
                "claude_cli.active_executions",
                pool_stats["active_executions"]
            )
            self.metrics_collector.set_gauge("claude_cli.queue_size", pool_stats["queue_size"])
            
            execution_stats = pool_stats["execution_stats"]
            self.metrics_collector.set_gauge(
                "claude_cli.total_executions",
                execution_stats["total_executions"]
            )
            self.metrics_collector.set_gauge(
                "claude_cli.successful_executions",
                execution_stats["successful_executions"]
            )
            self.metrics_collector.set_gauge(
                "claude_cli.failed_executions",
                execution_stats["failed_executions"]
            )
            
            if execution_stats["average_execution_time"] > 0:
                self.metrics_collector.record_timer(
                    "claude_cli.execution_time",
                    execution_stats["average_execution_time"]
                )
            
        except Exception as e:
            logger.error(f"A2A metrics collection failed: {str(e)}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """ダッシュボードデータ取得"""
        try:
            # メトリクス概要
            metrics_summary = self.metrics_collector.get_all_metrics_summary()
            
            # アクティブアラート
            active_alerts = [
                {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "description": alert.description,
                    "component": alert.component,
                    "triggered_at": alert.triggered_at.isoformat()
                }
                for alert in self.alert_manager.get_active_alerts()
            ]
            
            # ヘルス状態
            overall_health = self.health_monitor.get_overall_health()
            component_health = {
                component: {
                    "status": check.status.value,
                    "message": check.message,
                    "response_time": check.response_time,
                    "last_check": check.last_check.isoformat()
                }
                for component, check in self.health_monitor.health_checks.items()
            }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_health": overall_health.value,
                "component_health": component_health,
                "active_alerts": active_alerts,
                "metrics_summary": metrics_summary,
                "monitoring_status": {
                    "enabled": self.monitoring_enabled,
                    "interval": self.monitoring_interval
                }
            }
            
        except Exception as e:
            logger.error(f"Dashboard data generation failed: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def generate_monitoring_report(self) -> strdashboard_data = self.get_dashboard_data()alert_history = self.alert_manager.get_alert_history(24)
    """視レポート生成"""
        
        report_lines = [
            "# A2A Monitoring Report",:
            f"Generated at: {dashboard_data['timestamp']}",
            "",
            f"## Overall Health: {dashboard_data.get('overall_health', 'Unknown')}",
            "",
            "## Component Health"
        ]
        
        for component, health in dashboard_data.get('component_health', {}).items():
            status_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌',
                'unknown': '❓'
            }.get(health['status'], '❓')
            
            report_lines.extend([
                f"### {component} {status_emoji}",
                f"- Status: {health['status']}",
                f"- Message: {health['message']}",
                f"- Response Time: {health['response_time']:0.2f}s",
                ""
            ])
        
        report_lines.extend([
            f"## Active Alerts ({len(dashboard_data.get('active_alerts', []))})",
            ""
        ])
        
        for alert in dashboard_data.get('active_alerts', []):
            severity_emoji = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🚨'
            }.get(alert['severity'], '❓')
            
            report_lines.extend([
                f"### {alert['title']} {severity_emoji}",
                f"- Severity: {alert['severity']}",
                f"- Component: {alert['component']}",
                f"- Description: {alert['description']}",
                f"- Triggered: {alert['triggered_at']}",
                ""
            ])
        
        report_lines.extend([
            f"## Recent Alert History ({len(alert_history)} alerts in 24h)",
            ""
        ])
        
        for alert in alert_history[-10:]:  # 最近10件
            report_lines.append(f"- {alert.triggered_at.strftime('%H:%M')} - {alert.severity.value} - {alert.title}")
        
        return "\n".join(report_lines)


# シングルトンインスタンス
_monitoring_dashboard = None

def get_monitoring_dashboard() -> MonitoringDashboard:
    """監視ダッシュボードシングルトン取得"""
    global _monitoring_dashboard
    if _monitoring_dashboard is None:
        _monitoring_dashboard = MonitoringDashboard()
    return _monitoring_dashboard