"""
"📊" Elder Servants統合監視システム
Phase 3 プロダクション対応：包括的ログ・監視・メトリクス

EldersServiceLegacy統合: Iron Will品質基準とエルダー評議会令第27号完全準拠
目標: リアルタイム監視・Prometheus統合・構造化ログ
"""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import socket
import threading
import time
import uuid
import weakref
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

import psutil

# EldersLegacy統合インポート
from elders_guild.elder_tree.core.elders_legacy import (
    EldersLegacyDomain,
    EldersServiceLegacy,
    IronWillCriteria,
    enforce_boundary,
)


class LogLevel(Enum):
    """ログレベル"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """メトリクスタイプ"""

    COUNTER = "counter"  # カウンター（増加のみ）
    GAUGE = "gauge"  # ゲージ（任意値）
    HISTOGRAM = "histogram"  # ヒストグラム（分布）
    SUMMARY = "summary"  # サマリー（分位数）


class AlertSeverity(Enum):
    """アラート重要度"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class StructuredLogEntry:
    """構造化ログエントリ"""

    timestamp: datetime
    level: LogLevel
    service_name: str
    logger_name: str
    message: str
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)

    def to_json(self) -> str:
        """JSON文字列として出力"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["level"] = self.level.value
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


@dataclass
class MetricEntry:
    """メトリクスエントリ"""

    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    help_text: str = ""
    unit: str = ""

    def to_prometheus_format(self) -> str:
        """Prometheus形式で出力"""
        labels_str = ""
        if self.labels:
            label_pairs = [f'{k}="{v}"' for k, v in self.labels.items()]
            labels_str = "{" + ",".join(label_pairs) + "}"

        # メトリクス名の正規化
        metric_name = self.name.replace("-", "_").replace(".", "_")

        lines = []
        if self.help_text:
            lines.append(f"# HELP {metric_name} {self.help_text}")
        lines.append(f"# TYPE {metric_name} {self.metric_type.value}")
        lines.append(f"{metric_name}{labels_str} {self.value}")

        return "\n".join(lines)


@dataclass
class AlertRule:
    """アラートルール"""

    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    message_template: str
    cooldown_seconds: int = 300  # 5分間のクールダウン
    enabled: bool = True
    last_triggered: Optional[datetime] = None


class StructuredLogger:
    """構造化ログシステム"""

    def __init__(self, service_name: str, log_file_path: Optional[str] = None):
        """初期化メソッド"""
        self.service_name = service_name
        self.log_file_path = log_file_path
        self.correlation_id_stack: List[str] = []
        self.context_stack: List[Dict[str, Any]] = []

        # ログファイルハンドラー
        if log_file_path:
            self.log_file = open(log_file_path, "a", encoding="utf-8")
        else:
            self.log_file = None

        # バッファリング（パフォーマンス向上）
        self.log_buffer = deque(maxlen=1000)
        self.buffer_lock = threading.Lock()

        # 非同期フラッシュ
        self.flush_task: Optional[asyncio.Task] = None

    def _create_log_entry(
        self, level: LogLevel, message: str, logger_name: str = "default", **kwargs
    ) -> StructuredLogEntry:
        """ログエントリ作成"""
        # コンテキスト情報統合
        context = {}
        for ctx in self.context_stack:
            context.update(ctx)
        context.update(kwargs)

        return StructuredLogEntry(
            timestamp=datetime.now(),
            level=level,
            service_name=self.service_name,
            logger_name=logger_name,
            message=message,
            correlation_id=(
                self.correlation_id_stack[-1] if self.correlation_id_stack else None
            ),
            **context,
        )

    def debug(self, message: str, logger_name: str = "default", **kwargs):
        """デバッグログ"""
        entry = self._create_log_entry(LogLevel.DEBUG, message, logger_name, **kwargs)
        self._write_log(entry)

    def info(self, message: str, logger_name: str = "default", **kwargs):
        """情報ログ"""
        entry = self._create_log_entry(LogLevel.INFO, message, logger_name, **kwargs)
        self._write_log(entry)

    def warning(self, message: str, logger_name: str = "default", **kwargs):
        """警告ログ"""
        entry = self._create_log_entry(LogLevel.WARNING, message, logger_name, **kwargs)
        self._write_log(entry)

    def error(self, message: str, logger_name: str = "default", **kwargs):
        """エラーログ"""
        entry = self._create_log_entry(LogLevel.ERROR, message, logger_name, **kwargs)
        self._write_log(entry)

    def critical(self, message: str, logger_name: str = "default", **kwargs):
        """クリティカルログ"""
        entry = self._create_log_entry(
            LogLevel.CRITICAL, message, logger_name, **kwargs
        )
        self._write_log(entry)

    def _write_log(self, entry: StructuredLogEntry):
        """ログ書き込み"""
        log_json = entry.to_json()

        # 標準出力
        print(log_json)

        # ファイル出力
        if self.log_file:
            with self.buffer_lock:
                self.log_buffer.append(log_json)

        # 非同期フラッシュ開始
        if not self.flush_task or self.flush_task.done():
            # Complex condition - consider breaking down
            try:
                loop = asyncio.get_event_loop()
                self.flush_task = loop.create_task(self._async_flush())
            except RuntimeError:
                # イベントループが無い場合は同期書き込み
                self._sync_flush()

    async def _async_flush(self):
        """非同期フラッシュ"""
        await asyncio.sleep(0.1)  # 少し待機してバッファリング効果を得る
        self._sync_flush()

    def _sync_flush(self):
        """同期フラッシュ"""
        if not self.log_file:
            return

        with self.buffer_lock:
            while self.log_buffer:
                log_line = self.log_buffer.popleft()
                self.log_file.write(log_line + "\n")
            self.log_file.flush()

    @asynccontextmanager
    async def correlation_context(self, correlation_id: str = None):
        """相関IDコンテキスト"""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())

        self.correlation_id_stack.append(correlation_id)
        try:
            yield correlation_id
        finally:
            self.correlation_id_stack.pop()

    @asynccontextmanager
    async def log_context(self, **context):
        """ログコンテキスト"""
        self.context_stack.append(context)
        try:
            yield
        finally:
            self.context_stack.pop()

    def close(self):
        """クリーンアップ"""
        self._sync_flush()
        if self.log_file:
            self.log_file.close()


class PrometheusMetricsCollector:
    """Prometheusメトリクス収集"""

    def __init__(self, service_name: str):
        """初期化メソッド"""
        self.service_name = service_name
        self.metrics: Dict[str, MetricEntry] = {}
        self.metrics_lock = threading.Lock()

        # 履歴保持（メモリ効率考慮）
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

    def counter_inc(
        self,
        name: str,
        value: float = 1.0,
        labels: Dict[str, str] = None,
        help_text: str = "",
    ):
        """カウンター増加"""
        with self.metrics_lock:
            metric_key = f"{name}_{hash(str(sorted((labels or {}).items())))}"

            if metric_key in self.metrics:
                self.metrics[metric_key].value += value
                self.metrics[metric_key].timestamp = datetime.now()
            else:
                self.metrics[metric_key] = MetricEntry(
                    name=name,
                    metric_type=MetricType.COUNTER,
                    value=value,
                    timestamp=datetime.now(),
                    labels=labels or {},
                    help_text=help_text,
                )

    def gauge_set(
        self,
        name: str,
        value: float,
        labels: Dict[str, str] = None,
        help_text: str = "",
    ):
        """ゲージ設定"""
        with self.metrics_lock:
            metric_key = f"{name}_{hash(str(sorted((labels or {}).items())))}"

            self.metrics[metric_key] = MetricEntry(
                name=name,
                metric_type=MetricType.GAUGE,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {},
                help_text=help_text,
            )

            # 履歴保存
            self.metrics_history[metric_key].append(
                {"value": value, "timestamp": datetime.now()}
            )

    def histogram_observe(
        self,
        name: str,
        value: float,
        labels: Dict[str, str] = None,
        help_text: str = "",
    ):
        """ヒストグラム観測"""
        # 簡易ヒストグラム実装（buckets固定）
        buckets = [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")]

        with self.metrics_lock:
            for bucket in buckets:
                # Process each item in collection
                if value <= bucket:
                    bucket_labels = dict(labels or {})
                    bucket_labels["le"] = str(bucket)

                    bucket_key = (
                        f"{name}_bucket_{hash(str(sorted(bucket_labels.items())))}"
                    )

                    if bucket_key in self.metrics:
                        self.metrics[bucket_key].value += 1
                    else:
                        self.metrics[bucket_key] = MetricEntry(
                            name=f"{name}_bucket",
                            metric_type=MetricType.COUNTER,
                            value=1,
                            timestamp=datetime.now(),
                            labels=bucket_labels,
                            help_text=help_text,
                        )

    def get_prometheus_metrics(self) -> str:
        """Prometheus形式メトリクス取得"""
        with self.metrics_lock:
            lines = []
            for metric in self.metrics.values():
                # Process each item in collection
                lines.append(metric.to_prometheus_format())
            return "\n\n".join(lines)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """メトリクスサマリー取得"""
        with self.metrics_lock:
            summary = {
                "total_metrics": len(self.metrics),
                "counters": len(
                    [
                        m
                        for m in self.metrics.values()
                        if m.metric_type == MetricType.COUNTER
                    ]
                ),
                "gauges": len(
                    [
                        m
                        for m in self.metrics.values()
                        if m.metric_type == MetricType.GAUGE
                    ]
                ),
                "histograms": len(
                    [
                        m
                        for m in self.metrics.values()
                        if m.metric_type == MetricType.HISTOGRAM
                    ]
                ),
                "last_update": (
                    max([m.timestamp for m in self.metrics.values()]).isoformat()
                    if self.metrics
                    else None
                ),
            }

            # 最近のメトリクス（上位10件）
            recent_metrics = sorted(
                self.metrics.values(), key=lambda m: m.timestamp, reverse=True
            )[:10]

            summary["recent_metrics"] = [
                {
                    "name": m.name,
                    "type": m.metric_type.value,
                    "value": m.value,
                    "labels": m.labels,
                }
                for m in recent_metrics
            ]

            return summary


class AlertingSystem:
    """アラートシステム"""

    def __init__(self, notification_handlers: List[Callable] = None):
        """初期化メソッド"""
        self.rules: Dict[str, AlertRule] = {}
        self.notification_handlers = notification_handlers or []
        self.alert_history: List[Dict[str, Any]] = []
        self.rules_lock = threading.Lock()

    def add_rule(self, rule: AlertRule):
        """アラートルール追加"""
        with self.rules_lock:
            self.rules[rule.name] = rule

    def remove_rule(self, rule_name: str):
        """アラートルール削除"""
        with self.rules_lock:
            if rule_name in self.rules:
                del self.rules[rule_name]

    async def evaluate_rules(self, context: Dict[str, Any]):
        """ルール評価・アラート発火"""
        triggered_alerts = []

        with self.rules_lock:
            for rule in self.rules.values():
                # Process each item in collection
                if not rule.enabled:
                    continue

                # クールダウンチェック
                if (
                    rule.last_triggered
                    and (datetime.now() - rule.last_triggered).total_seconds()
                    < rule.cooldown_seconds
                ):
                    continue

                try:
                    if rule.condition(context):
                        # アラート発火
                        alert = {
                            "rule_name": rule.name,
                            "severity": rule.severity.value,
                            "message": rule.message_template.format(**context),
                            "timestamp": datetime.now().isoformat(),
                            "context": context,
                        }

                        triggered_alerts.append(alert)
                        rule.last_triggered = datetime.now()
                        self.alert_history.append(alert)

                        # 履歴サイズ制限
                        if not (len(self.alert_history) > 1000):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if len(self.alert_history) > 1000:
                            self.alert_history = self.alert_history[-1000:]

                except Exception as e:
                    # ルール評価エラーはログに記録
                    print(f"Alert rule evaluation failed: {rule.name}, {str(e)}")

        # 通知送信
        for alert in triggered_alerts:
            await self._send_notification(alert)

        return triggered_alerts

    async def _send_notification(self, alert: Dict[str, Any]):
        """通知送信"""
        for handler in self.notification_handlers:
            # Process each item in collection
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                # Handle specific exception case
                print(f"Notification handler failed: {str(e)}")


class ElderIntegrationMonitor(EldersServiceLegacy[Dict[str, Any], Dict[str, Any]]):
    """
    "📊" Elder Servants統合監視システム

    EldersServiceLegacyから継承し、Iron Will品質基準に完全準拠。
    構造化ログ・Prometheus統合・リアルタイム監視を提供。
    """

    def __init__(self, service_name: str = "elder_integration"):
        """初期化メソッド"""
        # EldersServiceLegacy初期化 (MONITORING域)
        super().__init__("elder_integration_monitor")

        self.service_name = service_name
        self.logger_impl = logging.getLogger("elder_servants.monitor")

        # 構造化ログシステム
        log_dir = Path("logs/elder_integration")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{service_name}_{datetime.now().strftime('%Y%m%d')}.jsonl"

        self.structured_logger = StructuredLogger(service_name, str(log_file))

        # Prometheusメトリクス
        self.metrics_collector = PrometheusMetricsCollector(service_name)

        # アラートシステム
        self.alerting_system = AlertingSystem()

        # システム監視タスク
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_enabled = True

        # パフォーマンス追跡
        self.performance_tracker = PerformanceTracker()

        # 統計情報
        self.statistics = {
            "total_logs": 0,
            "total_metrics": 0,
            "total_alerts": 0,
            "start_time": datetime.now(),
            "last_health_check": None,
        }

        # デフォルトアラートルール設定
        self._setup_default_alert_rules()

        # システム監視開始
        self._start_system_monitoring()

        # Iron Will品質基準
        self.quality_threshold = 99.9  # 99.9%可用性

        self.structured_logger.info("Elder Integration Monitor initialized")

    def _setup_default_alert_rules(self):
        """デフォルトアラートルール設定"""
        # CPU使用率アラート
        cpu_rule = AlertRule(
            name="high_cpu_usage",
            condition=lambda ctx: ctx.get("cpu_percent", 0) > 80,
            severity=AlertSeverity.WARNING,
            message_template="High CPU usage detected: {cpu_percent}%",
            cooldown_seconds=300,
        )
        self.alerting_system.add_rule(cpu_rule)

        # メモリ使用率アラート
        memory_rule = AlertRule(
            name="high_memory_usage",
            condition=lambda ctx: ctx.get("memory_percent", 0) > 85,
            severity=AlertSeverity.CRITICAL,
            message_template="High memory usage detected: {memory_percent}%",
            cooldown_seconds=300,
        )
        self.alerting_system.add_rule(memory_rule)

        # エラー率アラート
        error_rate_rule = AlertRule(
            name="high_error_rate",
            condition=lambda ctx: ctx.get("error_rate_percent", 0) > 5,
            severity=AlertSeverity.CRITICAL,
            message_template="High error rate detected: {error_rate_percent}%",
            cooldown_seconds=600,
        )
        self.alerting_system.add_rule(error_rate_rule)

    def _start_system_monitoring(self):
        """システム監視開始"""
        try:
            loop = asyncio.get_event_loop()
            self.monitoring_task = loop.create_task(self._system_monitoring_loop())
        except RuntimeError:
            # イベントループが無い場合はスキップ
            pass

    async def _system_monitoring_loop(self):
        """システム監視ループ"""
        while self.monitoring_enabled:
            try:
                # システムメトリクス収集
                await self._collect_system_metrics()

                # ヘルスチェック実行
                health_status = await self._perform_health_check()

                # アラート評価
                await self.alerting_system.evaluate_rules(health_status)

                # 統計更新
                self.statistics["last_health_check"] = datetime.now()

                # 30秒間隔
                await asyncio.sleep(30)

            except Exception as e:
                # Handle specific exception case
                self.structured_logger.error(f"System monitoring error: {str(e)}")
                await asyncio.sleep(60)  # エラー時は1分待機

    async def _collect_system_metrics(self):
        """システムメトリクス収集"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.gauge_set(
                "system_cpu_usage_percent",
                cpu_percent,
                {"service": self.service_name},
                "System CPU usage percentage",
            )

            # メモリ使用率
            memory = psutil.virtual_memory()
            self.metrics_collector.gauge_set(
                "system_memory_usage_percent",
                memory.percent,
                {"service": self.service_name},
                "System memory usage percentage",
            )

            # ディスク使用率
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            self.metrics_collector.gauge_set(
                "system_disk_usage_percent",
                disk_percent,
                {"service": self.service_name},
                "System disk usage percentage",
            )

            # プロセス数
            process_count = len(psutil.pids())
            self.metrics_collector.gauge_set(
                "system_process_count",
                process_count,
                {"service": self.service_name},
                "Number of running processes",
            )

            # ログカウンター更新
            self.metrics_collector.counter_inc(
                "logs_total",
                1,
                {"service": self.service_name, "level": "info"},
                "Total number of log entries",
            )

        except Exception as e:
            # Handle specific exception case
            self.structured_logger.error(f"Failed to collect system metrics: {str(e)}")

    async def _perform_health_check(self) -> Dict[str, Any]:
        """ヘルスチェック実行"""
        try:
            # システム情報取得
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            uptime = datetime.now() - self.statistics["start_time"]

            health_status = {
                "healthy": True,
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime.total_seconds(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "process_count": len(psutil.pids()),
                "log_count": self.statistics["total_logs"],
                "metrics_count": len(self.metrics_collector.metrics),
                "alert_count": len(self.alerting_system.alert_history),
            }

            # 健全性判定
            if (
                cpu_percent > 90
                or memory.percent > 90
                or (disk.used / disk.total) * 100 > 95
            ):
                health_status["healthy"] = False
                health_status["issues"] = []

                if cpu_percent > 90:
                    health_status["issues"].append("High CPU usage")
                if memory.percent > 90:
                    health_status["issues"].append("High memory usage")
                if (disk.used / disk.total) * 100 > 95:
                    health_status["issues"].append("High disk usage")

            return health_status

        except Exception as e:
            # Handle specific exception case
            self.structured_logger.error(f"Health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @enforce_boundary("monitoring")
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        EldersServiceLegacy統一リクエスト処理

        Args:
            request: 監視リクエスト

        Returns:
            Dict[str, Any]: 監視結果
        """
        start_time = time.time()

        try:
            request_type = request.get("type", "unknown")

            if request_type == "log":
                return await self._handle_log_request(request)
            elif request_type == "metric":
                return await self._handle_metric_request(request)
            elif request_type == "alert":
                return await self._handle_alert_request(request)
            elif request_type == "health_check":
                return await self._perform_health_check()
            elif request_type == "metrics_export":
                return {"metrics": self.metrics_collector.get_prometheus_metrics()}
            else:
                return {"error": f"Unknown request type: {request_type}"}

        except Exception as e:
            # Handle specific exception case
            self.structured_logger.error(f"Request processing failed: {str(e)}")
            return {"error": str(e)}
        finally:
            # パフォーマンス追跡
            execution_time = (time.time() - start_time) * 1000
            self.metrics_collector.histogram_observe(
                "request_duration_ms",
                execution_time,
                {"type": request.get("type", "unknown")},
                "Request processing duration in milliseconds",
            )

    async def _handle_log_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ログリクエスト処理"""
        level = LogLevel(request.get("level", "info"))
        message = request.get("message", "")
        logger_name = request.get("logger", "default")
        context = request.get("context", {})

        # ログ出力
        if level == LogLevel.DEBUG:
            self.structured_logger.debug(message, logger_name, **context)
        elif level == LogLevel.INFO:
            self.structured_logger.info(message, logger_name, **context)
        elif level == LogLevel.WARNING:
            self.structured_logger.warning(message, logger_name, **context)
        elif level == LogLevel.ERROR:
            self.structured_logger.error(message, logger_name, **context)
        elif level == LogLevel.CRITICAL:
            self.structured_logger.critical(message, logger_name, **context)

        self.statistics["total_logs"] += 1

        return {"success": True, "logged": True}

    async def _handle_metric_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスリクエスト処理"""
        metric_type = request.get("metric_type", "gauge")
        name = request.get("name", "")
        value = request.get("value", 0.0)
        labels = request.get("labels", {})
        help_text = request.get("help", "")

        if metric_type == "counter":
            self.metrics_collector.counter_inc(name, value, labels, help_text)
        elif metric_type == "gauge":
            self.metrics_collector.gauge_set(name, value, labels, help_text)
        elif metric_type == "histogram":
            self.metrics_collector.histogram_observe(name, value, labels, help_text)

        self.statistics["total_metrics"] += 1

        return {"success": True, "metric_recorded": True}

    async def _handle_alert_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """アラートリクエスト処理"""
        action = request.get("action", "trigger")

        if action == "trigger":
            # 手動アラート発火
            alert = {
                "rule_name": "manual_alert",
                "severity": request.get("severity", "info"),
                "message": request.get("message", "Manual alert triggered"),
                "timestamp": datetime.now().isoformat(),
                "context": request.get("context", {}),
            }

            await self.alerting_system._send_notification(alert)
            self.statistics["total_alerts"] += 1

            return {"success": True, "alert_triggered": True}

        elif action == "list":
            # アラート履歴取得
            return {
                "alerts": self.alerting_system.alert_history[-100:],  # 最新100件
                "total_alerts": len(self.alerting_system.alert_history),
            }

        return {"error": f"Unknown alert action: {action}"}

    def validate_request(self, request: Dict[str, Any]) -> bool:
        """EldersServiceLegacyリクエスト検証"""
        if not isinstance(request, dict):
            return False
        if "type" not in request:
            return False
        return True

    def get_capabilities(self) -> List[str]:
        """EldersServiceLegacy能力取得"""
        return [
            "structured_logging",
            "prometheus_metrics",
            "real_time_monitoring",
            "alerting_system",
            "health_checking",
            "performance_tracking",
            "system_monitoring",
        ]

    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """監視ダッシュボードデータ取得"""
        health_status = await self._perform_health_check()
        metrics_summary = self.metrics_collector.get_metrics_summary()

        return {
            "service_name": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "health_status": health_status,
            "metrics_summary": metrics_summary,
            "statistics": self.statistics,
            "alert_summary": {
                "total_alerts": len(self.alerting_system.alert_history),
                "recent_alerts": self.alerting_system.alert_history[-10:],
                "active_rules": len(self.alerting_system.rules),
            },
            "performance": {
                "uptime_seconds": (
                    datetime.now() - self.statistics["start_time"]
                ).total_seconds(),
                "logs_per_minute": self._calculate_logs_per_minute(),
                "metrics_per_minute": self._calculate_metrics_per_minute(),
            },
        }

    def _calculate_logs_per_minute(self) -> float:
        """1分あたりのログ数計算"""
        uptime_minutes = (
            datetime.now() - self.statistics["start_time"]
        ).total_seconds() / 60
        if uptime_minutes > 0:
            return self.statistics["total_logs"] / uptime_minutes
        return 0.0

    def _calculate_metrics_per_minute(self) -> float:
        """1分あたりのメトリクス数計算"""
        uptime_minutes = (
            datetime.now() - self.statistics["start_time"]
        ).total_seconds() / 60
        if uptime_minutes > 0:
            return self.statistics["total_metrics"] / uptime_minutes
        return 0.0

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # 基本ヘルスチェック
            base_health = await super().health_check()

            # 監視システム固有ヘルス
            system_health = await self._perform_health_check()

            # 総合判定
            overall_healthy = base_health.get("success", False) and system_health.get(
                "healthy", False
            )

            return {
                **base_health,
                "monitor_status": "healthy" if overall_healthy else "degraded",
                "system_health": system_health,
                "monitoring_enabled": self.monitoring_enabled,
                "iron_will_compliance": overall_healthy,
            }

        except Exception as e:
            # Handle specific exception case
            self.structured_logger.error(f"Health check failed: {str(e)}")
            return {"success": False, "status": "error", "error": str(e)}

    async def shutdown(self):
        """システムシャットダウン"""
        self.monitoring_enabled = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                # Handle specific exception case
                pass

        self.structured_logger.info("Elder Integration Monitor shutting down")
        self.structured_logger.close()


class PerformanceTracker:
    """パフォーマンス追跡"""

    def __init__(self):
        """初期化メソッド"""
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    @asynccontextmanager
    async def track_operation(self, operation_name: str):
        """操作時間追跡"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # ミリ秒
            with self.lock:
                self.operation_times[operation_name].append(duration)
                # 履歴サイズ制限
                if len(self.operation_times[operation_name]) > 1000:
                    self.operation_times[operation_name] = self.operation_times[
                        operation_name
                    ][-1000:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンスサマリー取得"""
        with self.lock:
            summary = {}
            for operation, times in self.operation_times.items():
                # Process each item in collection
                if times:
                    summary[operation] = {
                        "count": len(times),
                        "avg_ms": sum(times) / len(times),
                        "min_ms": min(times),
                        "max_ms": max(times),
                        "p95_ms": (
                            sorted(times)[int(len(times) * 0.95)]
                            if len(times) > 20
                            else max(times)
                        ),
                    }
            return summary


# グローバル監視インスタンス
_global_monitor: Optional[ElderIntegrationMonitor] = None


async def get_global_monitor() -> ElderIntegrationMonitor:
    """グローバル監視システム取得"""
    global _global_monitor

    if _global_monitor is None:
        # Complex condition - consider breaking down
        _global_monitor = ElderIntegrationMonitor()

    return _global_monitor


# 便利関数群
async def log_info(message: str, **context):
    """情報ログ（便利関数）"""
    monitor = await get_global_monitor()
    await monitor.process_request(
        {"type": "log", "level": "info", "message": message, "context": context}
    )


async def log_error(message: str, **context):
    """エラーログ（便利関数）"""
    monitor = await get_global_monitor()
    await monitor.process_request(
        {"type": "log", "level": "error", "message": message, "context": context}
    )


async def record_metric(
    name: str, value: float, metric_type: str = "gauge", labels: Dict[str, str] = None
):
    """メトリクス記録（便利関数）"""
    monitor = await get_global_monitor()
    await monitor.process_request(
        {
            "type": "metric",
            "name": name,
            "value": value,
            "metric_type": metric_type,
            "labels": labels or {},
        }
    )


async def trigger_alert(message: str, severity: str = "warning", **context):
    """アラート発火（便利関数）"""
    monitor = await get_global_monitor()
    await monitor.process_request(
        {
            "type": "alert",
            "action": "trigger",
            "message": message,
            "severity": severity,
            "context": context,
        }
    )


# パフォーマンス追跡デコレータ
def track_performance(operation_name: str = None):
    """パフォーマンス追跡デコレータ"""

    def decorator(func):
        """decoratorメソッド"""
        async def wrapper(*args, **kwargs):
            """wrapperメソッド"""
            monitor = await get_global_monitor()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            async with monitor.performance_tracker.track_operation(op_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator