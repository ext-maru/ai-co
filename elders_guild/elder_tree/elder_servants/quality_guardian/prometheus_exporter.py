#!/usr/bin/env python3
"""
Prometheusエクスポーター
既存のadvanced_monitoring_dashboardとの互換性を保ちながら
Prometheus形式でメトリクスをエクスポート
"""
import logging
import time
from typing import Any, Dict, Optional

import psutil
from libs.env_manager import EnvManager
from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
    start_http_server,
)

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# メトリクス定義
# アプリケーションメトリクス
app_requests_total = Counter(
    "app_requests_total", "Total number of requests", ["method", "endpoint", "status"]
)

app_response_time_seconds = Histogram(
    "app_response_time_seconds",
    "Response time in seconds",
    ["endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

app_active_users = Gauge("app_active_users", "Number of active users")

app_errors_total = Counter(
    "app_errors_total", "Total number of errors", ["error_type", "component"]
)

app_queue_size = Gauge("app_queue_size", "Current queue size", ["queue_name"])

# システムメトリクス
system_cpu_usage_percent = Gauge("system_cpu_usage_percent", "CPU usage percentage")

system_memory_usage_bytes = Gauge("system_memory_usage_bytes", "Memory usage in bytes")

system_disk_usage_percent = Gauge(
    "system_disk_usage_percent", "Disk usage percentage", ["mountpoint"]
)

# 4賢者メトリクス
sage_processing_time_seconds = Histogram(
    "sage_processing_time_seconds",
    "Processing time for sage requests",
    ["sage_type"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

sage_queue_size = Gauge("sage_queue_size", "Queue size for sage", ["sage_type"])

sage_errors_total = Counter(
    "sage_errors_total", "Total errors in sage", ["sage_type", "error_type"]
)

sage_memory_usage_bytes = Gauge(
    "sage_memory_usage_bytes", "Memory usage by sage", ["sage_type"]
)

# Elder Flowメトリクス
elder_flow_executions_total = Counter(
    "elder_flow_executions_total", "Total Elder Flow executions", ["priority", "status"]
)

elder_flow_execution_time_seconds = Histogram(
    "elder_flow_execution_time_seconds",
    "Elder Flow execution time",
    ["phase"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

elder_flow_quality_gate_pass_rate = Gauge(
    "elder_flow_quality_gate_pass_rate", "Quality gate pass rate percentage"
)

elder_flow_execution_failures_total = Counter(
    "elder_flow_execution_failures_total",
    "Total Elder Flow execution failures",
    ["phase", "reason"],
)

# アプリケーション情報
app_info = Info("app_info", "Application information")


class PrometheusExporter:
    """Prometheusエクスポーター"""

    def __init__(self, port: int = 8000):
        """初期化メソッド"""
        self.port = port
        self.metrics: Dict[str, Any] = {}

        # アプリケーション情報設定
        app_info.info(
            {"version": "1.0.0", "name": EnvManager.get_github_repo_name(), "environment": EnvManager.get_env()}
        )

    def start(self):
        """メトリクスサーバー起動"""
        try:
            start_http_server(self.port)
            logger.info(f"Prometheus metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise

    def update_system_metrics(self):
        """システムメトリクス更新"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_usage_percent.set(cpu_percent)

        # メモリ使用量
        memory = psutil.virtual_memory()
        system_memory_usage_bytes.set(memory.used)

        # ディスク使用率
        for disk in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(disk.mountpoint)
                system_disk_usage_percent.labels(mountpoint=disk.mountpoint).set(
                    usage.percent
                )
            except:
                pass

    def track_request(
        self, method: str, endpoint: str, status: int, response_time: float
    ):
        """リクエストトラッキング"""
        app_requests_total.labels(
            method=method, endpoint=endpoint, status=str(status)
        ).inc()

        app_response_time_seconds.labels(endpoint=endpoint).observe(response_time)

    def track_error(self, error_type: str, component: str):
        """エラートラッキング"""
        app_errors_total.labels(error_type=error_type, component=component).inc()

    def update_active_users(self, count: int):
        """アクティブユーザー数更新"""
        app_active_users.set(count)

    def update_queue_size(self, queue_name: str, size: int):
        """キューサイズ更新"""
        app_queue_size.labels(queue_name=queue_name).set(size)

    def track_sage_request(self, sage_type: str, processing_time: float):
        """賢者リクエストトラッキング"""
        sage_processing_time_seconds.labels(sage_type=sage_type).observe(
            processing_time
        )

    def update_sage_metrics(self, sage_type: str, queue_size: int, memory_usage: int):
        """賢者メトリクス更新"""
        sage_queue_size.labels(sage_type=sage_type).set(queue_size)
        sage_memory_usage_bytes.labels(sage_type=sage_type).set(memory_usage)

    def track_sage_error(self, sage_type: str, error_type: str):
        """賢者エラートラッキング"""
        sage_errors_total.labels(sage_type=sage_type, error_type=error_type).inc()

    def track_elder_flow_execution(
        self, priority: str, status: str, execution_time: float, phase: str
    ):
        """Elder Flow実行トラッキング"""
        elder_flow_executions_total.labels(priority=priority, status=status).inc()

        elder_flow_execution_time_seconds.labels(phase=phase).observe(execution_time)

        if status == "failed":
            elder_flow_execution_failures_total.labels(
                phase=phase, reason="execution_error"
            ).inc()

    def update_quality_gate_pass_rate(self, rate: float):
        """品質ゲート通過率更新"""
        elder_flow_quality_gate_pass_rate.set(rate * 100)

    def export_custom_metric(
        self,
        name: str,
        value: float,
        metric_type: str = "gauge",
        labels: Dict[str, str] = None,
    ):
        """カスタムメトリクスエクスポート"""
        if metric_type == "gauge":
            gauge = Gauge(
                f"app_custom_{name}",
                f"Custom metric: {name}",
                list(labels.keys()) if labels else [],
            )
            if labels:
                gauge.labels(**labels).set(value)
            else:
                gauge.set(value)
        elif metric_type == "counter":
            counter = Counter(
                f"app_custom_{name}",
                f"Custom metric: {name}",
                list(labels.keys()) if labels else [],
            )
            if labels:
                counter.labels(**labels).inc(value)
            else:
                counter.inc(value)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """メトリクスサマリー取得（互換性用）"""
        return {
            "cpu_usage": system_cpu_usage_percent._value.get(),
            "memory_usage": system_memory_usage_bytes._value.get(),
            "active_users": app_active_users._value.get(),
            "total_requests": sum(
                sample.value for sample in app_requests_total.collect()[0].samples
            ),
            "error_rate": sum(
                sample.value for sample in app_errors_total.collect()[0].samples
            ),
        }


# 既存のadvanced_monitoring_dashboardとの互換性ラッパー
class MonitoringDashboardAdapter:
    """既存のMonitoringDashboardとの互換性アダプター"""

    def __init__(self):
        """初期化メソッド"""
        self.exporter = PrometheusExporter()
        self.exporter.start()

    def add_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """メトリクス追加（互換性）"""
        self.exporter.export_custom_metric(name, value, "gauge", labels)

    def increment_counter(self, name: str, labels: Dict[str, str] = None):
        """カウンター増加（互換性）"""
        self.exporter.export_custom_metric(name, 1, "counter", labels)

    def update_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """ゲージ更新（互換性）"""
        self.exporter.export_custom_metric(name, value, "gauge", labels)

    def get_metrics(self) -> Dict[str, Any]:
        """メトリクス取得（互換性）"""
        return self.exporter.get_metrics_summary()


if __name__ == "__main__":
    # サンプル実行
    exporter = PrometheusExporter(port=8000)
    exporter.start()

    # メトリクス更新ループ
    while True:
        exporter.update_system_metrics()

        # サンプルメトリクス
        exporter.update_active_users(42)
        exporter.track_request("GET", "/api/users", 200, 0.123)
        exporter.update_queue_size("default", 10)

        time.sleep(15)
