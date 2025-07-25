#!/usr/bin/env python3
"""
高度監視ダッシュボード
リアルタイムメトリクス、アラート、可視化の包括的なダッシュボードシステム
"""
import asyncio
import json
import logging
import sqlite3
import threading
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import aiohttp
import psutil
import websockets

class WidgetType(Enum):
    """ウィジェットタイプ"""

    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    GAUGE = "gauge"
    TABLE = "table"
    HEATMAP = "heatmap"
    COUNTER = "counter"

class AlertSeverity(Enum):
    """アラート重要度"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"

@dataclass
class Widget:
    """ダッシュボードウィジェット"""

    id: str
    type: str
    title: str
    data_source: str
    refresh_interval: int = 30
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)

@dataclass
class AlertRule:
    """アラートルール"""

    id: str
    name: str
    metric: str
    condition: str
    threshold: float
    severity: str
    notification_channels: List[str] = field(default_factory=list)
    enabled: bool = True

@dataclass
class MetricData:
    """メトリクスデータ"""

    value: float
    timestamp: datetime
    unit: str
    labels: Dict[str, str] = field(default_factory=dict)

class MonitoringDashboard:
    """監視ダッシュボード"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.widgets = {}
        self.dashboards = {}
        self.metrics_collector = MetricsCollector()
        self.alerting_system = AlertingSystem()
        self.visualization_engine = VisualizationEngine()

    def create_widget(
        self,
        widget_type: str,
        title: str,
        data_source: str,
        refresh_interval: int = 30,
        **kwargs,
    ) -> Dict[str, Any]:
        """ウィジェット作成"""
        widget_id = str(uuid.uuid4())

        widget = Widget(
            id=widget_id,
            type=widget_type,
            title=title,
            data_source=data_source,
            refresh_interval=refresh_interval,
            config=kwargs,
            position=kwargs.get("position", {}),
        )

        self.widgets[widget_id] = widget

        return {
            "id": widget.id,
            "type": widget.type,
            "title": widget.title,
            "data_source": widget.data_source,
            "refresh_interval": widget.refresh_interval,
            "config": widget.config,
            "position": widget.position,
        }

    async def get_metrics(self, metric_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """メトリクス取得"""
        metrics = {}

        for metric_name in metric_names:
            try:
                # メトリクス収集
                if metric_name.startswith("system."):
                    value = await self._get_system_metric(metric_name)
                elif metric_name.startswith("application."):
                    value = await self._get_application_metric(metric_name)
                elif metric_name.startswith("database."):
                    value = await self._get_database_metric(metric_name)
                else:
                    value = await self._get_custom_metric(metric_name)

                metrics[metric_name] = {
                    "value": value,
                    "timestamp": datetime.now(),
                    "unit": self._get_metric_unit(metric_name),
                }

            except Exception as e:
                self.logger.error(f"Error collecting metric {metric_name}: {e}")
                metrics[metric_name] = {
                    "value": 0,
                    "timestamp": datetime.now(),
                    "unit": "unknown",
                    "error": str(e),
                }

        return metrics

    def render_dashboard(self, dashboard_config: Dict[str, Any]) -> str:
        """ダッシュボード描画"""
        # HTML生成（簡易実装）
        html = f"""
        <html>
        <head>
            <title>{dashboard_config.get('name', 'Dashboard')}</title>
            <style>

                    auto-fit,
                    minmax(300px, 1fr)
                ); gap: 20px; }}
                .widget {{ border: 1px solid #ccc; padding: 20px; border-radius: 5px; }}
                .{dashboard_config.get(
                    'theme',
                    'light')} {{ background: {'#333' if dashboard_config.get('theme'
                ) == 'dark' else '#fff'}; }}
            </style>
        </head>
        <body class="{dashboard_config.get('theme', 'light')}">
            <div class="dashboard">
        """

        for widget in dashboard_config.get("widgets", []):
            html += f"""
                <div class="widget">
                    <h3>{widget.get('title', 'Untitled Widget')}</h3>
                    <div id="widget-{widget.get('id', 'unknown')}">
                        <!-- Widget content goes here -->
                    </div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def configure_alerts(self, alert_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """アラート設定"""
        configured_rules = []

        for rule_config in alert_rules:
            rule = self.alerting_system.create_alert_rule(**rule_config)
            configured_rules.append(rule)

        return {
            "status": "configured",
            "rules_count": len(configured_rules),
            "rules": configured_rules,
        }

    def configure_dashboard(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """ダッシュボード設定"""
        dashboard_id = str(uuid.uuid4())

        dashboard = {
            "id": dashboard_id,
            "name": config["name"],
            "layout": config.get("layout", "grid"),
            "refresh_rate": config.get("refresh_rate", 30),
            "theme": config.get("theme", "light"),
            "widgets": [],
            "created_at": datetime.now(),
        }

        # ウィジェット作成
        for widget_config in config.get("widgets", []):
            widget = self.create_widget(
                widget_type=widget_config["type"],
                title=widget_config.get("title", "Untitled"),
                data_source=widget_config.get("metric", "unknown"),
                position=widget_config.get("position", {}),
            )
            dashboard["widgets"].append(widget)

        self.dashboards[dashboard_id] = dashboard

        return dashboard

    async def _get_system_metric(self, metric_name: str) -> float:
        """システムメトリクス取得"""
        if metric_name == "system.cpu_usage":
            return psutil.cpu_percent(interval=1)
        elif metric_name == "system.memory_usage":
            return psutil.virtual_memory().percent
        elif metric_name == "system.disk_usage":
            return psutil.disk_usage("/").percent
        return 0.0

    async def _get_application_metric(self, metric_name: str) -> float:
        """アプリケーションメトリクス取得"""
        if metric_name == "application.requests_per_second":
            return 150.5  # モック値
        elif metric_name == "application.response_time":
            return 245.0  # モック値
        return 0.0

    async def _get_database_metric(self, metric_name: str) -> float:
        """データベースメトリクス取得"""
        if metric_name == "database.connections":
            return 25  # モック値
        elif metric_name == "database.queries_per_second":
            return 500.0  # モック値
        return 0.0

    async def _get_custom_metric(self, metric_name: str) -> float:
        """カスタムメトリクス取得"""
        return 42.0  # モック値

    def _get_metric_unit(self, metric_name: str) -> str:
        """メトリクス単位取得"""
        if "percent" in metric_name or "usage" in metric_name:
            return "%"
        elif "time" in metric_name:
            return "ms"
        elif "per_second" in metric_name:
            return "/sec"
        elif "connections" in metric_name:
            return "count"
        return "value"

class MetricsCollector:
    """メトリクス収集器"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.custom_collectors = {}
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集"""

        def _collect():
            """collect（内部メソッド）"""
            cpu_info = {
                "usage_percent": psutil.cpu_percent(interval=1),
                "cores": psutil.cpu_count(),
            }

            memory = psutil.virtual_memory()
            memory_info = {
                "used_gb": memory.used / (1024**3),
                "total_gb": memory.total / (1024**3),
                "usage_percent": memory.percent,
            }

            disk = psutil.disk_usage("/")
            disk_info = {
                "used_gb": disk.used / (1024**3),
                "total_gb": disk.total / (1024**3),
                "usage_percent": (disk.used / disk.total) * 100,
            }

            network = psutil.net_io_counters()
            network_info = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            }

            return {
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
            }

        # 非同期実行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _collect)

    async def collect_application_metrics(
        self, app_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """アプリケーションメトリクス収集"""
        metrics = {"endpoints": {}, "services": {}, "performance": {}}

        # エンドポイントメトリクス
        for endpoint in app_config.get("endpoints", []):
            try:
                start_time = time.time()
                # HTTP リクエスト（モック）
                response_time = (time.time() - start_time) * 1000

                metrics["endpoints"][endpoint] = {
                    "response_time": response_time,
                    "status_code": 200,
                    "requests_count": 150,
                }
            except Exception as e:
                metrics["endpoints"][endpoint] = {
                    "response_time": 0,
                    "status_code": 500,
                    "error": str(e),
                }

        # サービスメトリクス
        for service in app_config.get("services", []):
            metrics["services"][service] = {
                "status": "running",
                "uptime": "24h 15m",
                "memory_usage": 85.2,
                "cpu_usage": 12.5,
            }

        # パフォーマンスメトリクス
        metrics["performance"] = {
            "avg_response_time": 245,
            "throughput": 450,
            "error_rate": 0.02,
        }

        return metrics

    def register_collector(self, name: str, collector_func: Callable) -> bool:
        """カスタムコレクター登録"""
        try:
            self.custom_collectors[name] = collector_func
            return True
        except Exception as e:
            self.logger.error(f"Failed to register collector {name}: {e}")
            return False

    def get_registered_collectors(self) -> List[str]:
        """登録済みコレクター一覧取得"""
        return list(self.custom_collectors.keys())

    def collect_custom_metrics(self, collector_name: str) -> Dict[str, Any]:
        """カスタムメトリクス収集"""
        if collector_name not in self.custom_collectors:
            raise ValueError(f"Collector {collector_name} not found")

        try:
            return self.custom_collectors[collector_name]()
        except Exception as e:
            self.logger.error(
                f"Error collecting custom metrics for {collector_name}: {e}"
            )
            return {}

class AlertingSystem:
    """アラートシステム"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.alert_rules = {}
        self.alert_history = deque(maxlen=1000)

    def create_alert_rule(
        self,
        name: str,
        metric: str,
        condition: str,
        threshold: float,
        severity: str,
        notification_channels: List[str] = None,
    ) -> Dict[str, Any]:
        """アラートルール作成"""
        rule_id = str(uuid.uuid4())

        rule = AlertRule(
            id=rule_id,
            name=name,
            metric=metric,
            condition=condition,
            threshold=threshold,
            severity=severity,
            notification_channels=notification_channels or [],
        )

        self.alert_rules[rule_id] = rule

        return {
            "id": rule.id,
            "name": rule.name,
            "metric": rule.metric,
            "condition": rule.condition,
            "threshold": rule.threshold,
            "severity": rule.severity,
            "notification_channels": rule.notification_channels,
        }

    async def evaluate_alerts(
        self, alert_rules: List[Dict[str, Any]], current_metrics: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """アラート評価"""
        triggered_alerts = []

        for rule in alert_rules:
            metric_value = current_metrics.get(rule["metric"])
            if metric_value is None:
                continue

            triggered = False
            if rule["condition"] == "greater_than" and metric_value > rule["threshold"]:
                triggered = True
            elif rule["condition"] == "less_than" and metric_value < rule["threshold"]:
                triggered = True
            elif rule["condition"] == "equals" and metric_value == rule["threshold"]:
                triggered = True

            if triggered:
                alert = {
                    "rule_id": rule["id"],
                    "name": rule.get("name", "Unnamed Alert"),
                    "severity": rule["severity"],
                    "metric": rule["metric"],
                    "current_value": metric_value,
                    "threshold": rule["threshold"],
                    "condition": rule["condition"],
                    "timestamp": datetime.now(),
                }

                triggered_alerts.append(alert)
                self.alert_history.append(alert)

        return triggered_alerts

    async def send_notification(
        self, alert: Dict[str, Any], channels: List[str], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """通知送信"""
        results = {}

        for channel in channels:
            try:
                if channel == "slack":
                    result = await self._send_slack_notification(
                        alert, config.get("slack", {})
                    )
                elif channel == "email":
                    result = await self._send_email_notification(
                        alert, config.get("email", {})
                    )
                else:
                    result = {"status": "unsupported_channel"}

                results[channel] = result

            except Exception as e:
                results[channel] = {"status": "error", "error": str(e)}

        return results

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """アラート履歴取得"""
        return list(self.alert_history)[-limit:]

    async def _send_slack_notification(
        self, alert: Dict[str, Any], slack_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Slack通知送信"""
        # 実際の実装ではSlack APIを使用
        await asyncio.sleep(0.1)  # API呼び出しシミュレーション
        return {"status": "sent", "channel": slack_config.get("channel", "#alerts")}

    async def _send_email_notification(
        self, alert: Dict[str, Any], email_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """メール通知送信"""
        # 実際の実装ではSMTPを使用
        await asyncio.sleep(0.1)  # SMTP送信シミュレーション
        return {"status": "sent", "recipients": email_config.get("recipients", [])}

class VisualizationEngine:
    """可視化エンジン"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)

    def render_chart(
        self, data: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """チャート描画"""
        chart_type = config.get("type", "line")
        title = config.get("title", "Untitled Chart")

        # SVGコンテンツ生成（簡易実装）
        svg_content = f"""
        <svg width="400" height="300">
            <title>{title}</title>
            <g>
                <!-- Chart elements would be rendered here -->
                <text x="200" y="150" text-anchor="middle">{title}</text>
            </g>
        </svg>
        """

        return {
            "type": chart_type,
            "title": title,
            "svg_content": svg_content,
            "data_points": data,
            "config": config,
        }

    def render_gauge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """ゲージ描画"""
        title = config.get("title", "Gauge")
        value = config.get("value", 0)
        min_val = config.get("min", 0)
        max_val = config.get("max", 100)
        thresholds = config.get("thresholds", [])

        # 現在の色を決定
        current_color = "gray"
        for threshold in sorted(thresholds, key=lambda x: x["value"], reverse=True):
            if value >= threshold["value"]:
                current_color = threshold["color"]
                break

        # SVGコンテンツ生成（簡易実装）
        svg_content = f"""
        <svg width="200" height="200">
            <title>{title}</title>
            <circle cx="100" cy="100" r="80" fill="none" stroke="{current_color}" stroke-width="10"/>
            <text x="100" y="105" text-anchor="middle" font-size="24">{value}</text>
        </svg>
        """

        return {
            "title": title,
            "value": value,
            "current_color": current_color,
            "svg_content": svg_content,
            "thresholds": thresholds,
        }

    def render_heatmap(
        self, data: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ヒートマップ描画"""
        title = config.get("title", "Heatmap")
        color_scheme = config.get("color_scheme", "blues")

        # SVGコンテンツ生成（簡易実装）
        svg_content = f"""
        <svg width="600" height="400">
            <title>{title}</title>
            <g>
                <!-- Heatmap cells would be rendered here -->
                <text x="300" y="200" text-anchor="middle">{title}</text>
            </g>
        </svg>
        """

        # カラースケール
        color_scale = {
            "min": min(item["value"] for item in data) if data else 0,
            "max": max(item["value"] for item in data) if data else 100,
            "scheme": color_scheme,
        }

        return {
            "title": title,
            "data": data,
            "svg_content": svg_content,
            "color_scale": color_scale,
            "config": config,
        }

    def render_table(
        self, data: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """テーブル描画"""
        title = config.get("title", "Table")
        columns = config.get("columns", [])

        # HTMLテーブル生成
        html_content = f"""
        <table>
            <caption>{title}</caption>
            <thead>
                <tr>
                    {''.join(f'<th>{col}</th>' for col in columns)}
                </tr>
            </thead>
            <tbody>
                {''.join('<tr>' + ''.join(f'<td>{row.get(col, "")}</td>' for col in columns) + '</tr>' for row in data)}
            </tbody>
        </table>
        """

        return {
            "title": title,
            "html_content": html_content,
            "rows": len(data),
            "columns": columns,
        }

class DashboardPersistence:
    """ダッシュボード永続化"""

    def __init__(self, db_path: str = "dashboards.db"):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """データベース初期化"""
        with sqlite3connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dashboards (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    config TEXT NOT NULL,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    def save_dashboard(self, dashboard_config: Dict[str, Any]) -> Dict[str, str]:
        """ダッシュボード保存"""
        try:
            dashboard_id = dashboard_config.get("id", str(uuid.uuid4()))

            with sqlite3connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO dashboards
                    (id, name, config, created_by, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (
                        dashboard_id,
                        dashboard_config.get("name", "Untitled"),
                        json.dumps(dashboard_config),
                        dashboard_config.get("created_by", "unknown"),
                    ),
                )

            return {"status": "success", "dashboard_id": dashboard_id}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def load_dashboard(self, dashboard_id: str) -> Dict[str, Any]:
        """ダッシュボード読み込み"""
        with sqlite3connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT config FROM dashboards WHERE id = ?", (dashboard_id,)
            )
            row = cursor.fetchone()

            if row:
                return json.loads(row[0])
            else:
                raise ValueError(f"Dashboard {dashboard_id} not found")

    def list_dashboards(self) -> List[Dict[str, Any]]:
        """ダッシュボード一覧取得"""
        with sqlite3connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, name, created_by, created_at, updated_at
                FROM dashboards
                ORDER BY updated_at DESC
            """
            )

            dashboards = []
            for row in cursor.fetchall():
                dashboards.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "created_by": row[2],
                        "created_at": row[3],
                        "updated_at": row[4],
                    }
                )

            return dashboards

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """ダッシュボード削除"""
        try:
            with sqlite3connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM dashboards WHERE id = ?", (dashboard_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error deleting dashboard {dashboard_id}: {e}")
            return False

class RealTimeUpdates:
    """リアルタイム更新"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.subscribers = defaultdict(set)  # metric -> set of client_ids
        self.client_websockets = {}  # client_id -> websocket
        self.websocket_server = None

    async def start_websocket_server(self, host: str = "localhost", port: int = 8765):
        """WebSocketサーバー開始"""

        async def handle_client(websocket, path):
            """handle_clientメソッド"""
            client_id = str(uuid.uuid4())
            self.client_websockets[client_id] = websocket

            try:
                async for message in websocket:
                    data = json.loads(message)

                    if data.get("action") == "subscribe":
                        metrics = data.get("metrics", [])
                        await self.subscribe_to_metrics(client_id, metrics)
                    elif data.get("action") == "unsubscribe":
                        metrics = data.get("metrics", [])
                        await self.unsubscribe_from_metrics(client_id, metrics)

            except Exception as e:
                self.logger.error(f"WebSocket error for client {client_id}: {e}")
            finally:
                # クライアント削除
                if client_id in self.client_websockets:
                    del self.client_websockets[client_id]

                # 購読からも削除
                for metric_subscribers in self.subscribers.values():
                    metric_subscribers.discard(client_id)

        self.websocket_server = await websockets.serve(handle_client, host, port)
        self.logger.info(f"WebSocket server started on {host}:{port}")

    async def subscribe_to_metrics(
        self, client_id: str, metrics: List[str]
    ) -> Dict[str, Any]:
        """メトリクス購読"""
        for metric in metrics:
            self.subscribers[metric].add(client_id)

        return {"status": "subscribed", "client_id": client_id, "metrics": metrics}

    async def unsubscribe_from_metrics(
        self, client_id: str, metrics: List[str]
    ) -> Dict[str, Any]:
        """メトリクス購読解除"""
        for metric in metrics:
            self.subscribers[metric].discard(client_id)

        return {"status": "unsubscribed", "client_id": client_id, "metrics": metrics}

    async def broadcast_update(self, metric_update: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクス更新配信"""
        metric_name = metric_update["metric"]
        subscribers = self.subscribers.get(metric_name, set())

        clients_notified = 0
        message = json.dumps(metric_update)

        for client_id in subscribers:
            if client_id in self.client_websockets:
                try:
                    websocket = self.client_websockets[client_id]
                    await websocket.send(message)
                    clients_notified += 1
                except Exception as e:
                    self.logger.error(
                        f"Failed to send update to client {client_id}: {e}"
                    )

        return {
            "status": "broadcasted",
            "metric": metric_name,
            "clients_notified": clients_notified,
        }

class DashboardAPI:
    """ダッシュボードAPI"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.persistence = DashboardPersistence()
        self.dashboard = MonitoringDashboard()

    async def create_dashboard(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ダッシュボード作成"""
        try:
            dashboard_id = str(uuid.uuid4())

            dashboard_config = {
                "id": dashboard_id,
                "name": request["name"],
                "description": request.get("description", ""),
                "widgets": request.get("widgets", []),
                "layout": request.get("layout", "grid"),
                "theme": request.get("theme", "light"),
                "created_at": datetime.now().isoformat(),
            }

            # 保存
            save_result = self.persistence.save_dashboard(dashboard_config)

            if save_result["status"] == "success":
                return {
                    "status": "created",
                    "dashboard_id": dashboard_id,
                    "message": "Dashboard created successfully",
                }
            else:
                return {
                    "status": "error",
                    "error": save_result.get("error", "Unknown error"),
                }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_dashboard(self, dashboard_id: str) -> Dict[str, Any]:
        """ダッシュボード取得"""
        try:
            return self.persistence.load_dashboard(dashboard_id)
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def update_dashboard(
        self, dashboard_id: str, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ダッシュボード更新"""
        try:
            # 既存のダッシュボードを取得
            existing = self.persistence.load_dashboard(dashboard_id)

            # 更新
            updated_config = {**existing, **request}
            updated_config["id"] = dashboard_id
            updated_config["updated_at"] = datetime.now().isoformat()

            # 保存
            save_result = self.persistence.save_dashboard(updated_config)

            if save_result["status"] == "success":
                return {"status": "updated", "dashboard_id": dashboard_id}
            else:
                return {"status": "error", "error": save_result.get("error")}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def delete_dashboard(self, dashboard_id: str) -> Dict[str, Any]:
        """ダッシュボード削除"""
        try:
            success = self.persistence.delete_dashboard(dashboard_id)

            if success:
                return {"status": "deleted", "dashboard_id": dashboard_id}
            else:
                return {"status": "error", "error": "Dashboard not found"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
