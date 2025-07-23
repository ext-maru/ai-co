"""
Elders Guild Database Monitoring System - 包括的監視・アラートシステム
Created: 2025-07-11
Author: Claude Elder
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import statistics
import psutil
import time

import asyncpg
import redis.asyncio as redis
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    start_http_server,
    CollectorRegistry,
)

from .elders_guild_db_manager import EldersGuildDatabaseManager, DatabaseConfig
from .elders_guild_connection_manager import (
    ConnectionManager,
    ConnectionPoolConfig,
    DatabaseNode,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================


class AlertLevel(Enum):
    """アラートレベル"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """通知チャネル"""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class AlertRule:
    """アラートルール"""

    name: str
    description: str
    metric_name: str
    threshold: float
    comparison: str  # >, <, >=, <=, ==, !=
    alert_level: AlertLevel
    duration: int = 300  # 5分間継続で発火
    cooldown: int = 1800  # 30分間のクールダウン
    enabled: bool = True

    # 通知設定
    notification_channels: List[NotificationChannel] = field(default_factory=list)

    # 状態管理
    last_triggered: Optional[datetime] = None
    is_active: bool = False
    trigger_count: int = 0


@dataclass
class NotificationConfig:
    """通知設定"""

    # メール設定
    smtp_server: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    admin_email: str = "admin@eldersguild.com"

    # Slack設定
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"

    # Webhook設定
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """監視設定"""

    # 基本設定
    collection_interval: int = 30  # 30秒間隔
    retention_days: int = 30

    # Prometheus設定
    prometheus_port: int = 9090
    prometheus_enabled: bool = True

    # アラート設定
    alert_evaluation_interval: int = 60  # 1分間隔
    notification_config: NotificationConfig = field(default_factory=NotificationConfig)

    # 監視項目
    monitor_connections: bool = True
    monitor_performance: bool = True
    monitor_disk_usage: bool = True
    monitor_memory_usage: bool = True
    monitor_replication: bool = True
    monitor_slow_queries: bool = True


# ============================================================================
# Metrics Collector
# ============================================================================


class DatabaseMetrics:
    """データベースメトリクス"""

    def __init__(self):
        """初期化メソッド"""
        # Prometheus メトリクス
        self.registry = CollectorRegistry()

        # 接続メトリクス
        self.active_connections = Gauge(
            "elders_guild_active_connections",
            "Active database connections",
            ["node", "database"],
            registry=self.registry,
        )

        self.max_connections = Gauge(
            "elders_guild_max_connections",
            "Maximum database connections",
            ["node", "database"],
            registry=self.registry,
        )

        self.connection_usage = Gauge(
            "elders_guild_connection_usage_percent",
            "Database connection usage percentage",
            ["node", "database"],
            registry=self.registry,
        )

        # パフォーマンスメトリクス
        self.query_duration = Histogram(
            "elders_guild_query_duration_seconds",
            "Query execution time",
            ["node", "database", "query_type"],
            registry=self.registry,
        )

        self.transactions_total = Counter(
            "elders_guild_transactions_total",
            "Total database transactions",
            ["node", "database", "result"],
            registry=self.registry,
        )

        # システムメトリクス
        self.disk_usage = Gauge(
            "elders_guild_disk_usage_percent",
            "Disk usage percentage",
            ["node", "mount_point"],
            registry=self.registry,
        )

        self.memory_usage = Gauge(
            "elders_guild_memory_usage_percent",
            "Memory usage percentage",
            ["node"],
            registry=self.registry,
        )

        self.cpu_usage = Gauge(
            "elders_guild_cpu_usage_percent",
            "CPU usage percentage",
            ["node"],
            registry=self.registry,
        )

        # レプリケーションメトリクス
        self.replication_lag = Gauge(
            "elders_guild_replication_lag_seconds",
            "Replication lag in seconds",
            ["master", "slave"],
            registry=self.registry,
        )

        # 4賢者メトリクス
        self.knowledge_entities_count = Gauge(
            "elders_guild_knowledge_entities_total",
            "Total knowledge entities",
            registry=self.registry,
        )

        self.tasks_by_status = Gauge(
            "elders_guild_tasks_by_status",
            "Tasks by status",
            ["status"],
            registry=self.registry,
        )

        self.incidents_by_severity = Gauge(
            "elders_guild_incidents_by_severity",
            "Incidents by severity",
            ["severity"],
            registry=self.registry,
        )

        self.rag_queries_total = Counter(
            "elders_guild_rag_queries_total",
            "Total RAG queries",
            ["status"],
            registry=self.registry,
        )


class MetricsCollector:
    """メトリクス収集器"""

    def __init__(
        self,
        db_manager: EldersGuildDatabaseManager,
        connection_manager: ConnectionManager,
    ):
        self.db_manager = db_manager
        self.connection_manager = connection_manager
        self.metrics = DatabaseMetrics()
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        """メトリクス収集器の初期化"""
        self.redis_client = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )

        logger.info("Metrics collector initialized")

    async def collect_all_metrics(self):
        """全メトリクスの収集"""
        await self._collect_connection_metrics()
        await self._collect_performance_metrics()
        await self._collect_system_metrics()
        await self._collect_replication_metrics()
        await self._collect_sage_metrics()

    async def _collect_connection_metrics(self):
        """接続メトリクスの収集"""
        try:
            for node in self.connection_manager.nodes:
                if not node.is_active:
                    continue

                # 接続数の取得
                async with self.connection_manager.get_connection() as conn:
                    result = await conn.fetchrow(
                        """
                        SELECT
                            count(*) as active_connections,
                            current_setting('max_connections')::int as max_connections
                        FROM pg_stat_activity
                        WHERE state = 'active'
                    """
                    )

                    active_conn = result["active_connections"]
                    max_conn = result["max_connections"]

                    self.metrics.active_connections.labels(
                        node=node.host, database=node.database
                    ).set(active_conn)

                    self.metrics.max_connections.labels(
                        node=node.host, database=node.database
                    ).set(max_conn)

                    usage_percent = (
                        (active_conn / max_conn) * 100 if max_conn > 0 else 0
                    )
                    self.metrics.connection_usage.labels(
                        node=node.host, database=node.database
                    ).set(usage_percent)

        except Exception as e:
            logger.error(f"Error collecting connection metrics: {e}")

    async def _collect_performance_metrics(self):
        """パフォーマンスメトリクスの収集"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # スロークエリの取得
                slow_queries = await conn.fetch(
                    """
                    SELECT
                        query,
                        calls,
                        total_time / 1000 as total_seconds,
                        mean_time / 1000 as mean_seconds,
                        max_time / 1000 as max_seconds
                    FROM pg_stat_statements
                    WHERE mean_time > 1000  -- 1秒以上
                    ORDER BY total_time DESC
                    LIMIT 10
                """
                )

                # トランザクション統計
                tx_stats = await conn.fetchrow(
                    """
                    SELECT
                        xact_commit + xact_rollback as total_transactions,
                        xact_commit,
                        xact_rollback
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """
                )

                if tx_stats:
                    self.metrics.transactions_total.labels(
                        node="master",
                        database=self.db_manager.config.database,
                        result="commit",
                    ).inc(tx_stats["xact_commit"])

                    self.metrics.transactions_total.labels(
                        node="master",
                        database=self.db_manager.config.database,
                        result="rollback",
                    ).inc(tx_stats["xact_rollback"])

        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")

    async def _collect_system_metrics(self):
        """システムメトリクスの収集"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.cpu_usage.labels(node="localhost").set(cpu_percent)

            # メモリ使用率
            memory = psutil.virtual_memory()
            self.metrics.memory_usage.labels(node="localhost").set(memory.percent)

            # ディスク使用率
            disk_usage = psutil.disk_usage("/")
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            self.metrics.disk_usage.labels(node="localhost", mount_point="/").set(
                disk_percent
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _collect_replication_metrics(self):
        """レプリケーションメトリクスの収集"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # レプリケーション状態の確認
                replication_stats = await conn.fetch(
                    """
                    SELECT
                        client_addr,
                        state,
                        sent_lsn,
                        write_lsn,
                        flush_lsn,
                        replay_lsn,
                        sync_state
                    FROM pg_stat_replication
                """
                )

                for stat in replication_stats:
                    # レプリケーション遅延の計算
                    if stat["sent_lsn"] and stat["replay_lsn"]:
                        lag = 0  # 実際の計算はより複雑
                        self.metrics.replication_lag.labels(
                            master="master", slave=stat["client_addr"]
                        ).set(lag)

        except Exception as e:
            logger.error(f"Error collecting replication metrics: {e}")

    async def _collect_sage_metrics(self):
        """4賢者メトリクスの収集"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # Knowledge Sage
                knowledge_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM knowledge_sage.knowledge_entities"
                )
                self.metrics.knowledge_entities_count.set(knowledge_count)

                # Task Sage
                task_stats = await conn.fetch(
                    """
                    SELECT status, COUNT(*) as count
                    FROM task_sage.tasks
                    GROUP BY status
                """
                )

                for stat in task_stats:
                    self.metrics.tasks_by_status.labels(status=stat["status"]).set(
                        stat["count"]
                    )

                # Incident Sage
                incident_stats = await conn.fetch(
                    """
                    SELECT severity, COUNT(*) as count
                    FROM incident_sage.incidents
                    WHERE status != 'closed'
                    GROUP BY severity
                """
                )

                for stat in incident_stats:
                    self.metrics.incidents_by_severity.labels(
                        severity=stat["severity"]
                    ).set(stat["count"])

        except Exception as e:
            logger.error(f"Error collecting sage metrics: {e}")

    async def store_metrics(self, metrics: Dict[str, Any]):
        """メトリクスの保存"""
        if not self.redis_client:
            return

        timestamp = int(time.time())

        # Redis に時系列データとして保存
        await self.redis_client.setex(
            f"elders_guild:metrics:{timestamp}",
            86400,  # 24時間保持
            json.dumps(metrics),
        )

        # 最新メトリクスの更新
        await self.redis_client.set("elders_guild:metrics:latest", json.dumps(metrics))

    async def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """メトリクス履歴の取得"""
        if not self.redis_client:
            return []

        end_time = int(time.time())
        start_time = end_time - (hours * 3600)

        metrics_history = []

        # 5分間隔でサンプリング
        for timestamp in range(start_time, end_time, 300):
            key = f"elders_guild:metrics:{timestamp}"
            data = await self.redis_client.get(key)
            if data:
                metrics_history.append(json.loads(data))

        return metrics_history


# ============================================================================
# Alert Manager
# ============================================================================


class AlertManager:
    """アラートマネージャー"""

    def __init__(self, config:
        """初期化メソッド"""
    NotificationConfig):
        self.config = config
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, AlertRule] = {}

    def add_alert_rule(self, rule: AlertRule):
        """アラートルールの追加"""
        self.alert_rules.append(rule)

    def add_default_rules(self):
        """デフォルトアラートルールの追加"""
        default_rules = [
            AlertRule(
                name="high_connection_usage",
                description="Database connection usage is high",
                metric_name="connection_usage",
                threshold=80.0,
                comparison=">=",
                alert_level=AlertLevel.WARNING,
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.LOG,
                ],
            ),
            AlertRule(
                name="critical_connection_usage",
                description="Database connection usage is critical",
                metric_name="connection_usage",
                threshold=95.0,
                comparison=">=",
                alert_level=AlertLevel.CRITICAL,
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                ],
            ),
            AlertRule(
                name="high_memory_usage",
                description="System memory usage is high",
                metric_name="memory_usage",
                threshold=85.0,
                comparison=">=",
                alert_level=AlertLevel.WARNING,
                notification_channels=[NotificationChannel.EMAIL],
            ),
            AlertRule(
                name="high_disk_usage",
                description="Disk usage is high",
                metric_name="disk_usage",
                threshold=90.0,
                comparison=">=",
                alert_level=AlertLevel.ERROR,
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                ],
            ),
            AlertRule(
                name="replication_lag",
                description="Replication lag is high",
                metric_name="replication_lag",
                threshold=60.0,
                comparison=">=",
                alert_level=AlertLevel.WARNING,
                notification_channels=[NotificationChannel.EMAIL],
            ),
            AlertRule(
                name="slow_queries",
                description="Slow queries detected",
                metric_name="slow_query_count",
                threshold=10.0,
                comparison=">=",
                alert_level=AlertLevel.WARNING,
                notification_channels=[NotificationChannel.LOG],
            ),
        ]

        for rule in default_rules:
            self.add_alert_rule(rule)

    async def evaluate_alerts(self, metrics: Dict[str, Any]):
        """アラートの評価"""
        current_time = datetime.now()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # メトリクス値の取得
            metric_value = self._get_metric_value(metrics, rule.metric_name)
            if metric_value is None:
                continue

            # 閾値の評価
            should_trigger = self._evaluate_threshold(
                metric_value, rule.threshold, rule.comparison
            )

            if should_trigger:
                # クールダウン期間のチェック
                if rule.last_triggered:
                    time_since_last = (
                        current_time - rule.last_triggered
                    ).total_seconds()
                    if time_since_last < rule.cooldown:
                        continue

                # アラートの発火
                await self._trigger_alert(rule, metric_value, current_time)

            else:
                # アラートの解除
                if rule.is_active:
                    await self._resolve_alert(rule, current_time)

    def _get_metric_value(
        self, metrics: Dict[str, Any], metric_name: str
    ) -> Optional[float]:
        """メトリクス値の取得"""
        try:
            # ネストした辞書から値を取得
            keys = metric_name.split(".")
            value = metrics
            for key in keys:
                value = value[key]
            return float(value)
        except (KeyError, ValueError, TypeError):
            return None

    def _evaluate_threshold(
        self, value: float, threshold: float, comparison: str
    ) -> bool:
        """閾値の評価"""
        if comparison == ">":
            return value > threshold
        elif comparison == "<":
            return value < threshold
        elif comparison == ">=":
            return value >= threshold
        elif comparison == "<=":
            return value <= threshold
        elif comparison == "==":
            return value == threshold
        elif comparison == "!=":
            return value != threshold
        else:
            return False

    async def _trigger_alert(self, rule: AlertRule, value: float, timestamp: datetime):
        """アラートの発火"""
        rule.is_active = True
        rule.last_triggered = timestamp
        rule.trigger_count += 1

        self.active_alerts[rule.name] = rule

        # 通知の送信
        await self._send_notifications(rule, value, "TRIGGERED")

        logger.warning(
            f"Alert triggered: {rule.name} - {rule.description} (value: {value})"
        )

    async def _resolve_alert(self, rule: AlertRule, timestamp: datetime):
        """アラートの解除"""
        rule.is_active = False

        if rule.name in self.active_alerts:
            del self.active_alerts[rule.name]

        # 通知の送信
        await self._send_notifications(rule, None, "RESOLVED")

        logger.info(f"Alert resolved: {rule.name}")

    async def _send_notifications(
        self, rule: AlertRule, value: Optional[float], status: str
    ):
        """通知の送信"""
        for channel in rule.notification_channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    await self._send_email_notification(rule, value, status)
                elif channel == NotificationChannel.SLACK:
                    await self._send_slack_notification(rule, value, status)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook_notification(rule, value, status)
                elif channel == NotificationChannel.LOG:
                    await self._send_log_notification(rule, value, status)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel.value}: {e}")

    async def _send_email_notification(
        self, rule: AlertRule, value: Optional[float], status: str
    ):
        """メール通知の送信"""
        if not self.config.admin_email:
            return

        subject = f"[Elders Guild] {status}: {rule.name}"

        body = f"""
        Alert: {rule.name}
        Description: {rule.description}
        Status: {status}
        Level: {rule.alert_level.value.upper()}

        """

        if value is not None:
            body += f"Current Value: {value}\n"
            body += f"Threshold: {rule.threshold}\n"

        body += f"Timestamp: {datetime.now().isoformat()}\n"

        # メール送信の実装（実際の環境に合わせて調整）
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.smtp_username
            msg["To"] = self.config.admin_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            if self.config.smtp_use_tls:
                server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.send_message(msg)
            server.quit()

        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    async def _send_slack_notification(
        self, rule: AlertRule, value: Optional[float], status: str
    ):
        """Slack通知の送信"""
        # Slack webhook実装（実際の環境に合わせて調整）
        pass

    async def _send_webhook_notification(
        self, rule: AlertRule, value: Optional[float], status: str
    ):
        """Webhook通知の送信"""
        # Webhook実装（実際の環境に合わせて調整）
        pass

    async def _send_log_notification(
        self, rule: AlertRule, value: Optional[float], status: str
    ):
        """ログ通知の送信"""
        log_level = getattr(logging, rule.alert_level.value.upper(), logging.INFO)

        message = f"Alert {status}: {rule.name} - {rule.description}"
        if value is not None:
            message += f" (value: {value}, threshold: {rule.threshold})"

        logger.log(log_level, message)

    def get_active_alerts(self) -> List[AlertRule]:
        """アクティブなアラートの取得"""
        return list(self.active_alerts.values())

    def get_alert_statistics(self) -> Dict[str, Any]:
        """アラート統計の取得"""
        total_rules = len(self.alert_rules)
        active_alerts = len(self.active_alerts)

        level_counts = {}
        for rule in self.alert_rules:
            level = rule.alert_level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "total_rules": total_rules,
            "active_alerts": active_alerts,
            "level_distribution": level_counts,
            "total_triggers": sum(rule.trigger_count for rule in self.alert_rules),
        }


# ============================================================================
# Main Monitoring System
# ============================================================================


class ElderGuildMonitoring:
    """エルダーズギルド監視システム"""

    def __init__(
        self,
        config: MonitoringConfig,
        db_manager: EldersGuildDatabaseManager,
        connection_manager: ConnectionManager,
    ):
        self.config = config
        self.db_manager = db_manager
        self.connection_manager = connection_manager
        self.metrics_collector = MetricsCollector(db_manager, connection_manager)
        self.alert_manager = AlertManager(config.notification_config)

        self.collection_task: Optional[asyncio.Task] = None
        self.alert_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def initialize(self):
        """監視システムの初期化"""
        await self.metrics_collector.initialize()

        # デフォルトアラートルールの追加
        self.alert_manager.add_default_rules()

        # Prometheus サーバーの開始
        if self.config.prometheus_enabled:
            start_http_server(
                self.config.prometheus_port,
                registry=self.metrics_collector.metrics.registry,
            )

        logger.info("Monitoring system initialized")

    async def start(self):
        """監視開始"""
        if self.is_running:
            return

        self.is_running = True

        # メトリクス収集タスク
        self.collection_task = asyncio.create_task(self._collection_loop())

        # アラート評価タスク
        self.alert_task = asyncio.create_task(self._alert_loop())

        logger.info("Monitoring system started")

    async def stop(self):
        """監視停止"""
        self.is_running = False

        if self.collection_task:
            self.collection_task.cancel()

        if self.alert_task:
            self.alert_task.cancel()

        logger.info("Monitoring system stopped")

    async def _collection_loop(self):
        """メトリクス収集ループ"""
        while self.is_running:
            try:
                await self.metrics_collector.collect_all_metrics()
                await asyncio.sleep(self.config.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(self.config.collection_interval)

    async def _alert_loop(self):
        """アラート評価ループ"""
        while self.is_running:
            try:
                # 最新メトリクスの取得
                latest_metrics = await self.get_latest_metrics()
                if latest_metrics:
                    await self.alert_manager.evaluate_alerts(latest_metrics)

                await asyncio.sleep(self.config.alert_evaluation_interval)
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(self.config.alert_evaluation_interval)

    async def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """最新メトリクスの取得"""
        try:
            if not self.metrics_collector.redis_client:
                return None

            data = await self.metrics_collector.redis_client.get(
                "elders_guild:metrics:latest"
            )
            if data:
                return json.loads(data)

            return None
        except Exception as e:
            logger.error(f"Error getting latest metrics: {e}")
            return None

    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """監視ダッシュボードデータの取得"""
        try:
            # 基本統計
            connection_stats = await self.connection_manager.get_connection_statistics()

            # アラート統計
            alert_stats = self.alert_manager.get_alert_statistics()

            # アクティブアラート
            active_alerts = self.alert_manager.get_active_alerts()

            # メトリクス履歴
            metrics_history = await self.metrics_collector.get_metrics_history(24)

            dashboard = {
                "timestamp": datetime.now().isoformat(),
                "connection_stats": connection_stats,
                "alert_stats": alert_stats,
                "active_alerts": [
                    {
                        "name": alert.name,
                        "description": alert.description,
                        "level": alert.alert_level.value,
                        "triggered_at": (
                            alert.last_triggered.isoformat()
                            if alert.last_triggered
                            else None
                        ),
                    }
                    for alert in active_alerts
                ],
                "metrics_history": metrics_history[-100:],  # 最新100件
                "system_health": {
                    "database_nodes": len(
                        [n for n in self.connection_manager.nodes if n.is_active]
                    ),
                    "total_nodes": len(self.connection_manager.nodes),
                    "monitoring_active": self.is_running,
                },
            }

            return dashboard

        except Exception as e:
            logger.error(f"Error generating monitoring dashboard: {e}")
            return {"error": str(e)}


# ============================================================================
# Usage Example
# ============================================================================


async def main():
    """使用例"""
    # 設定
    monitoring_config = MonitoringConfig(
        collection_interval=30, prometheus_enabled=True, prometheus_port=9090
    )

    # データベース管理
    db_config = DatabaseConfig()
    db_manager = EldersGuildDatabaseManager(db_config)

    # 接続管理
    connection_config = ConnectionPoolConfig()
    connection_manager = ConnectionManager(connection_config)

    # 監視システム
    monitoring = ElderGuildMonitoring(monitoring_config, db_manager, connection_manager)

    try:
        await monitoring.initialize()
        await monitoring.start()

        # 監視実行（実際の運用では永続的に実行）
        await asyncio.sleep(300)  # 5分間監視

        # ダッシュボードデータの取得
        dashboard = await monitoring.get_monitoring_dashboard()
        print(f"Monitoring dashboard: {json.dumps(dashboard, indent=2)}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await monitoring.stop()


if __name__ == "__main__":
    asyncio.run(main())
