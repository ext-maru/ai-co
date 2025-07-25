#!/usr/bin/env python3
"""
Worker Monitoring Dashboard - ワーカー監視ダッシュボード
四賢者推奨Phase 2最優先タスク

リアルタイム監視・可視化システム
FastAPI + WebSocket + Chart.js による包括的監視ソリューション
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import json
import logging
import sqlite3
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import psutil

# FastAPI関連
try:
    import uvicorn
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI not available, dashboard will run in limited mode")

    # フォールバック用の型定義
    class WebSocket:
        """WebSocketクラス"""
        pass

# 既存システム統合
try:
    from libs.error_classification_system import ErrorClassificationSystem
    from libs.worker_auto_recovery_system import WorkerHealthMonitor

    EXISTING_SYSTEMS_AVAILABLE = True
except ImportError:
    EXISTING_SYSTEMS_AVAILABLE = False
    logging.warning("Existing systems not available")

logger = logging.getLogger(__name__)

@dataclass
class DashboardConfig:
    """ダッシュボード設定"""

    update_interval: int = 5  # 更新間隔（秒）
    web_port: int = 8000
    enable_alerts: bool = True
    alert_thresholds: Dict[str, float] = None
    data_retention_hours: int = 24
    enable_authentication: bool = False

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "cpu_usage": 90.0,
                "memory_usage": 85.0,
                "worker_count_min": 3,
                "disk_usage": 90.0,
            }

@dataclass
class MetricsPoint:
    """メトリクスポイント"""

    timestamp: datetime
    system_metrics: Dict[str, float]
    worker_metrics: List[Dict[str, Any]]
    error_stats: Optional[Dict[str, Any]] = None
    alerts: Optional[List[Dict[str, Any]]] = None

class MetricsCollector:
    """メトリクス収集システム"""

    def __init__(self, config: DashboardConfig):
        """初期化メソッド"""
        self.config = config
        self.db_path = PROJECT_ROOT / "data" / "dashboard_metrics.db"

        # 既存システム統合
        self.health_monitor = None
        self.error_classifier = None

        if EXISTING_SYSTEMS_AVAILABLE:
            try:
                self.health_monitor = WorkerHealthMonitor()
                self.error_classifier = ErrorClassificationSystem()
            except Exception as e:
                logger.warning(f"Failed to initialize existing systems: {e}")

        # データベース初期化
        self._init_database()

        logger.info("Metrics Collector initialized")

    def _init_database(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    worker_count INTEGER,
                    system_data TEXT,
                    worker_data TEXT,
                    error_data TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON metrics(timestamp)
            """
            )

    def collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクス収集"""
        try:
            # 基本システムメトリクス
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # ワーカーメトリクス
            worker_metrics = self._collect_worker_metrics()

            # 既存システム統合
            error_stats = None
            if self.error_classifier:
                try:
                    error_stats = self.error_classifier.get_metrics()
                except Exception as e:
                    logger.warning(f"Failed to get error classification metrics: {e}")

            system_metrics = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "worker_count": len(worker_metrics),
                "timestamp": datetime.now().isoformat(),
                "uptime": self._get_system_uptime(),
                "load_average": self._get_load_average(),
            }

            return {
                "system_metrics": system_metrics,
                "worker_metrics": worker_metrics,
                "error_stats": error_stats,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {
                "system_metrics": {
                    "cpu_usage": 0,
                    "memory_usage": 0,
                    "disk_usage": 0,
                    "worker_count": 0,
                },
                "worker_metrics": [],
                "error_stats": None,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _collect_worker_metrics(self) -> List[Dict[str, Any]]:
        """ワーカーメトリクス収集"""
        worker_metrics = []

        try:
            # Pythonワーカープロセスを検索
            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "cpu_percent", "memory_info", "create_time"]
            ):
                try:
                    cmdline = proc.info.get("cmdline", [])
                    if not cmdline:
                        continue

                    # ワーカープロセスを特定
                    cmdline_str = " ".join(cmdline)
                    if (
                        "python" in cmdline_str
                        and "worker" in cmdline_str
                        and ".py" in cmdline_str
                    ):
                        # ワーカー名を抽出
                        worker_name = "unknown"
                        for arg in cmdline:
                            if "worker" in arg and ".py" in arg:
                                worker_name = Path(arg).stem
                                break

                        # メトリクス収集
                        cpu_percent = proc.info.get("cpu_percent", 0) or 0
                        memory_info = proc.info.get("memory_info")
                        memory_mb = (
                            memory_info.rss / (1024 * 1024) if memory_info else 0
                        )

                        # 稼働時間計算
                        create_time = proc.info.get("create_time")
                        uptime_seconds = time.time() - create_time if create_time else 0

                        worker_metrics.append(
                            {
                                "name": worker_name,
                                "pid": proc.info["pid"],
                                "status": "running",
                                "cpu_percent": float(cpu_percent),
                                "memory_mb": float(memory_mb),
                                "uptime_seconds": float(uptime_seconds),
                                "uptime_human": self._format_uptime(uptime_seconds),
                                "last_seen": datetime.now().isoformat(),
                            }
                        )

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

        except Exception as e:
            logger.error(f"Failed to collect worker metrics: {e}")

        return worker_metrics

    def _get_system_uptime(self) -> float:
        """システム稼働時間取得"""
        try:
            return time.time() - psutil.boot_time()
        except Exception:
            return 0.0

    def _get_load_average(self) -> List[float]:
        """システム負荷平均取得"""
        try:
            return list(psutil.getloadavg())
        except (AttributeError, OSError):
            return [0.0, 0.0, 0.0]

    def _format_uptime(self, seconds: float) -> str:
        """稼働時間の人間可読形式変換"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            return f"{int(seconds/60)}分"
        elif seconds < 86400:
            return f"{int(seconds/3600)}時間"
        else:
            return f"{int(seconds/86400)}日"

    def store_metrics(self, metrics: Dict[str, Any]) -> None:
        """メトリクスをデータベースに保存"""
        try:
            system_metrics = metrics.get("system_metrics", {})
            worker_metrics = metrics.get("worker_metrics", [])
            error_stats = metrics.get("error_stats")

            with sqlite3connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO metrics
                    (cpu_usage, memory_usage, disk_usage, worker_count,
                     system_data, worker_data, error_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        system_metrics.get("cpu_usage", 0),
                        system_metrics.get("memory_usage", 0),
                        system_metrics.get("disk_usage", 0),
                        system_metrics.get("worker_count", 0),
                        json.dumps(system_metrics),
                        json.dumps(worker_metrics),
                        json.dumps(error_stats) if error_stats else None,
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

    def get_historical_data(self, hours: int = 1) -> List[Dict[str, Any]]:
        """履歴データ取得"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)

            with sqlite3connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    """
                    SELECT timestamp, cpu_usage, memory_usage, disk_usage, worker_count,
                           system_data, worker_data, error_data
                    FROM metrics
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                """,
                    (start_time.isoformat(),),
                )

                results = []
                for row in cursor:
                    (
                        timestamp,
                        cpu,
                        memory,
                        disk,
                        worker_count,
                        sys_data,
                        worker_data,
                        error_data,
                    ) = row

                    try:
                        system_data = json.loads(sys_data) if sys_data else {}
                        worker_data_parsed = (
                            json.loads(worker_data) if worker_data else []
                        )
                        error_data_parsed = (
                            json.loads(error_data) if error_data else None
                        )
                    except json.JSONDecodeError:
                        continue

                    results.append(
                        {
                            "timestamp": timestamp,
                            "cpu_usage": cpu,
                            "memory_usage": memory,
                            "disk_usage": disk,
                            "worker_count": worker_count,
                            "system_data": system_data,
                            "worker_data": worker_data_parsed,
                            "error_data": error_data_parsed,
                        }
                    )

                return results

        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return []

    def get_aggregated_metrics(self, interval: str = "5m") -> Dict[str, Any]:
        """集計メトリクス取得"""
        try:
            # 過去1時間のデータを取得
            historical = self.get_historical_data(hours=1)

            if not historical:
                return {}

            # 基本統計計算
            cpu_values = [
                h["cpu_usage"] for h in historical if h["cpu_usage"] is not None
            ]
            memory_values = [
                h["memory_usage"] for h in historical if h["memory_usage"] is not None
            ]
            worker_counts = [
                h["worker_count"] for h in historical if h["worker_count"] is not None
            ]

            return {
                "avg_cpu_usage": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max_cpu_usage": max(cpu_values) if cpu_values else 0,
                "min_cpu_usage": min(cpu_values) if cpu_values else 0,
                "avg_memory_usage": (
                    sum(memory_values) / len(memory_values) if memory_values else 0
                ),
                "max_memory_usage": max(memory_values) if memory_values else 0,
                "avg_worker_count": (
                    sum(worker_counts) / len(worker_counts) if worker_counts else 0
                ),
                "max_worker_count": max(worker_counts) if worker_counts else 0,
                "data_points": len(historical),
                "time_range": interval,
            }

        except Exception as e:
            logger.error(f"Failed to get aggregated metrics: {e}")
            return {}

class WebSocketManager:
    """WebSocket接続管理"""

    def __init__(self):
        """初期化メソッド"""
        self.active_connections: Set[WebSocket] = set()
        self.client_info: Dict[WebSocket, Dict[str, Any]] = {}

        logger.info("WebSocket Manager initialized")

    async def connect(self, websocket: WebSocket) -> None:
        """クライアント接続"""
        await websocket.accept()
        self.active_connections.add(websocket)

        # クライアント情報を記録
        client_id = str(uuid.uuid4())
        self.client_info[websocket] = {
            "client_id": client_id,
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
        }

        logger.info(f"WebSocket client connected: {client_id}")

    def disconnect(self, websocket: WebSocket) -> None:
        """クライアント切断"""
        self.active_connections.discard(websocket)
        client_info = self.client_info.pop(websocket, {})
        client_id = client_info.get("client_id", "unknown")

        logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_to_client(
        self, websocket: WebSocket, message: Dict[str, Any]
    ) -> bool:
        """特定クライアントにメッセージ送信"""
        try:
            await websocket.send_text(json.dumps(message))

            # アクティビティ更新
            if websocket in self.client_info:
                self.client_info[websocket]["last_activity"] = datetime.now()

            return True

        except Exception as e:
            logger.warning(f"Failed to send message to client: {e}")
            self.disconnect(websocket)
            return False

    async def broadcast(self, message: Dict[str, Any]) -> int:
        """全クライアントにブロードキャスト"""
        if not self.active_connections:
            return 0

        success_count = 0
        failed_connections = set()

        for websocket in self.active_connections.copy():
            if await self.send_to_client(websocket, message):
                success_count += 1
            else:
                failed_connections.add(websocket)

        # 失敗した接続を削除
        for websocket in failed_connections:
            self.disconnect(websocket)

        return success_count

    def get_connection_stats(self) -> Dict[str, Any]:
        """接続統計取得"""
        now = datetime.now()

        return {
            "total_connections": len(self.active_connections),
            "client_info": [
                {
                    "client_id": info["client_id"],
                    "connected_duration": (now - info["connected_at"]).total_seconds(),
                    "last_activity": info["last_activity"].isoformat(),
                }
                for info in self.client_info.values()
            ],
        }

class RealtimeUpdater:
    """リアルタイム更新システム"""

    def __init__(
        self,
        config: DashboardConfig,
        metrics_collector: MetricsCollector,
        websocket_manager: WebSocketManager,
    ):
        self.config = config
        self.metrics_collector = metrics_collector
        self.websocket_manager = websocket_manager

        self.is_running = False
        self.update_task = None

        logger.info("Realtime Updater initialized")

    async def start_updates(self) -> None:
        """リアルタイム更新開始"""
        if self.is_running:
            return

        self.is_running = True
        self.update_task = asyncio.create_task(self._update_loop())
        logger.info("Realtime updates started")

    async def stop_updates(self) -> None:
        """リアルタイム更新停止"""
        self.is_running = False

        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        logger.info("Realtime updates stopped")

    async def _update_loop(self) -> None:
        """更新ループ"""
        while self.is_running:
            try:
                # メトリクス収集
                metrics = self.metrics_collector.collect_system_metrics()

                # データベースに保存
                self.metrics_collector.store_metrics(metrics)

                # アラートチェック
                alerts = self._check_alert_conditions(metrics.get("system_metrics", {}))

                # WebSocket更新メッセージ作成
                update_message = {
                    "type": "metrics_update",
                    "data": metrics,
                    "alerts": alerts,
                    "timestamp": datetime.now().isoformat(),
                }

                # ブロードキャスト
                sent_count = await self.websocket_manager.broadcast(update_message)

                if sent_count > 0:

                # 次の更新まで待機
                await asyncio.sleep(self.config.update_interval)

            except Exception as e:
                logger.error(f"Update loop error: {e}")
                await asyncio.sleep(self.config.update_interval)

    def _check_alert_conditions(
        self, system_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """アラート条件チェック"""
        if not self.config.enable_alerts:
            return []

        alerts = []
        thresholds = self.config.alert_thresholds

        # CPU使用率チェック
        cpu_usage = system_metrics.get("cpu_usage", 0)
        if cpu_usage > thresholds["cpu_usage"]:
            alerts.append(
                {
                    "type": "cpu_high",
                    "metric": "cpu_usage",
                    "value": cpu_usage,
                    "threshold": thresholds["cpu_usage"],
                    "severity": "critical" if cpu_usage > 95 else "warning",
                    "message": f"CPU使用率が高すぎます: {cpu_usage:0.1f}%",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # メモリ使用率チェック
        memory_usage = system_metrics.get("memory_usage", 0)
        if memory_usage > thresholds["memory_usage"]:
            alerts.append(
                {
                    "type": "memory_high",
                    "metric": "memory_usage",
                    "value": memory_usage,
                    "threshold": thresholds["memory_usage"],
                    "severity": "critical" if memory_usage > 95 else "warning",
                    "message": f"メモリ使用率が高すぎます: {memory_usage:0.1f}%",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # ワーカー数チェック
        worker_count = system_metrics.get("worker_count", 0)
        if worker_count < thresholds["worker_count_min"]:
            alerts.append(
                {
                    "type": "worker_count_low",
                    "metric": "worker_count",
                    "value": worker_count,
                    "threshold": thresholds["worker_count_min"],
                    "severity": "critical",
                    "message": f"ワーカー数が不足しています: {worker_count}個",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return alerts

class DashboardAPI:
    """ダッシュボードAPI"""

    def __init__(
        self,
        config: DashboardConfig,
        metrics_collector: MetricsCollector,
        websocket_manager: WebSocketManager,
    ):
        self.config = config
        self.metrics_collector = metrics_collector
        self.websocket_manager = websocket_manager

        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI is required for dashboard API")

        self.app = FastAPI(title="Worker Monitoring Dashboard", version="1.0.0")
        self._setup_routes()
        self._setup_static_files()

        logger.info("Dashboard API initialized")

    def _setup_routes(self):
        """ルート設定"""

        @self.app.get("/")
        async def dashboard_home():
            """ダッシュボードホームページ"""
            return HTMLResponse(self._get_dashboard_html())

        @self.app.get("/health")
        async def health_check():
            """ヘルスチェック"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_connections": len(self.websocket_manager.active_connections),
            }

        @self.app.get("/api/metrics/current")
        async def get_current_metrics():
            """現在のメトリクス取得"""
            metrics = self.metrics_collector.collect_system_metrics()
            return metrics

        @self.app.get("/api/metrics/history")
        async def get_historical_metrics(hours: int = 1):
            """履歴メトリクス取得"""
            historical = self.metrics_collector.get_historical_data(hours)
            return {
                "metrics": historical,
                "total_points": len(historical),
                "time_range": f"{hours}h",
            }

        @self.app.get("/api/metrics/aggregated")
        async def get_aggregated_metrics():
            """集計メトリクス取得"""
            aggregated = self.metrics_collector.get_aggregated_metrics()
            return aggregated

        @self.app.get("/api/workers/status")
        async def get_worker_status():
            """ワーカー状態取得"""
            metrics = self.metrics_collector.collect_system_metrics()
            workers = metrics.get("worker_metrics", [])

            return {
                "workers": workers,
                "total_count": len(workers),
                "running_count": len([w for w in workers if w["status"] == "running"]),

                "timestamp": datetime.now().isoformat(),
            }

        @self.app.get("/api/connections")
        async def get_connection_stats():
            """WebSocket接続統計"""
            return self.websocket_manager.get_connection_stats()

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocketエンドポイント"""
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    # クライアントからのメッセージを受信（ハートビート用）
                    data = await websocket.receive_text()
                    # エコーバック（接続確認）
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "timestamp": datetime.now().isoformat()}
                        )
                    )
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)

    def _setup_static_files(self):
        """静的ファイル設定"""
        static_dir = PROJECT_ROOT / "web" / "static"
        static_dir.mkdir(parents=True, exist_ok=True)

        # 静的ファイルが存在しない場合は作成
        self._create_static_files(static_dir)

        # 静的ファイルマウント
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def _get_dashboard_html(self) -> str:
        """ダッシュボードHTML生成"""
        return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Worker Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="/static/dashboard.css" rel="stylesheet">
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <h1>🛠️ Worker Monitoring Dashboard</h1>
            <div class="status-indicator" id="connectionStatus">
                <span class="status-dot"></span>
                <span class="status-text">接続中...</span>
            </div>
        </header>

        <main class="dashboard-main">
            <!-- システムメトリクス -->
            <section class="metrics-section">
                <h2>"📊" システムメトリクス</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>CPU使用率</h3>
                        <div class="metric-value" id="cpuUsage">0%</div>
                        <canvas id="cpuChart" width="300" height="150"></canvas>
                    </div>
                    <div class="metric-card">
                        <h3>メモリ使用率</h3>
                        <div class="metric-value" id="memoryUsage">0%</div>
                        <canvas id="memoryChart" width="300" height="150"></canvas>
                    </div>
                    <div class="metric-card">
                        <h3>ワーカー数</h3>
                        <div class="metric-value" id="workerCount">0</div>
                        <div class="metric-subtitle" id="workerStatus">稼働中</div>
                    </div>
                    <div class="metric-card">
                        <h3>システム稼働時間</h3>
                        <div class="metric-value" id="systemUptime">0日</div>
                        <div class="metric-subtitle">継続稼働中</div>
                    </div>
                </div>
            </section>

            <!-- ワーカー詳細 -->
            <section class="workers-section">
                <h2>👷 ワーカー詳細</h2>
                <div class="workers-table-container">
                    <table class="workers-table" id="workersTable">
                        <thead>
                            <tr>
                                <th>ワーカー名</th>
                                <th>PID</th>
                                <th>状態</th>
                                <th>CPU</th>
                                <th>メモリ</th>
                                <th>稼働時間</th>
                            </tr>
                        </thead>
                        <tbody id="workersTableBody">
                            <tr>
                                <td colspan="6" class="no-data">データを読み込み中...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- アラート -->
            <section class="alerts-section">
                <h2>🚨 アラート</h2>
                <div class="alerts-container" id="alertsContainer">
                    <div class="no-alerts">現在アラートはありません</div>
                </div>
            </section>
        </main>
    </div>

    <script src="/static/dashboard.js"></script>
</body>
</html>
        """

    def _create_static_files(self, static_dir: Path):
        """静的ファイル作成"""
        # CSS ファイル
        css_content = """
/* Dashboard CSS */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f5f5f5;
    color: #333;
}

.dashboard-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #4CAF50;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.metrics-section, .workers-section, .alerts-section {
    background: white;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.metrics-grid {
    display: grid;

    gap: 20px;
    margin-top: 20px;
}

.metric-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    border-left: 4px solid #007bff;
}

.metric-value {
    font-size: 2em;
    font-weight: bold;
    color: #007bff;
    margin: 10px 0;
}

.metric-subtitle {
    color: #666;
    font-size: 0.9em;
}

.workers-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}

.workers-table th,
.workers-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

.workers-table th {
    background-color: #f8f9fa;
    font-weight: 600;
}

.workers-table tbody tr:hover {
    background-color: #f8f9fa;
}

.status-running { color: #28a745; font-weight: bold; }
.status-stopped { color: #dc3545; font-weight: bold; }
.status-warning { color: #ffc107; font-weight: bold; }

.alerts-container {
    margin-top: 20px;
}

.alert {
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 10px;
    border-left: 4px solid;
}

.alert-critical {
    background-color: #f8d7da;
    border-color: #dc3545;
    color: #721c24;
}

.alert-warning {
    background-color: #fff3cd;
    border-color: #ffc107;
    color: #856404;
}

.no-alerts, .no-data {
    text-align: center;
    color: #666;
    padding: 20px;
    font-style: italic;
}

@media (max-width: 768px) {
    .dashboard-header {
        flex-direction: column;
        gap: 15px;
    }

    .metrics-grid {

    }
}
        """

        (static_dir / "dashboard.css").write_text(css_content, encoding="utf-8")

        # JavaScript ファイル
        js_content = """
// Dashboard JavaScript
class WorkerDashboard {
    constructor() {
        this.ws = null;
        this.charts = {};
        this.metricsHistory = {
            cpu: [],
            memory: [],
            timestamps: []
        };
        this.maxDataPoints = 50;

        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupCharts();
        this.loadInitialData();
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
            // ハートビート送信
            setInterval(() => {
                if (this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({type: 'ping'}));
                }
            }, 30000);
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            // 5秒後に再接続を試行
            setTimeout(() => this.setupWebSocket(), 5000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }

    setupCharts() {
        // CPU使用率チャート
        const cpuCtx = document.getElementById('cpuChart').getContext('2d');
        this.charts.cpu = new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU使用率 (%)',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100 }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        // メモリ使用率チャート
        const memoryCtx = document.getElementById('memoryChart').getContext('2d');
        this.charts.memory = new Chart(memoryCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'メモリ使用率 (%)',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100 }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    async loadInitialData() {
        try {
            const response = await fetch('/api/metrics/current');
            const data = await response.json();
            this.updateMetrics(data);
        } catch (error) {
            console.error('Failed to load initial data:', error);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'metrics_update':
                this.updateMetrics(data.data);
                this.updateAlerts(data.alerts || []);
                break;
            case 'pong':
                // ハートビート応答
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    updateMetrics(data) {
        const systemMetrics = data.system_metrics || {};
        const workerMetrics = data.worker_metrics || [];

        // システムメトリクス更新
        this.updateElement('cpuUsage', `${systemMetrics.cpu_usage?.toFixed(1) || 0}%`);
        this.updateElement('memoryUsage', `${systemMetrics.memory_usage?.toFixed(1) || 0}%`);
        this.updateElement('workerCount', systemMetrics.worker_count || 0);

        if (systemMetrics.uptime) {
            const days = Math.floor(systemMetrics.uptime / 86400);
            this.updateElement('systemUptime', `${days}日`);
        }

        // チャート更新
        this.updateCharts(systemMetrics);

        // ワーカーテーブル更新
        this.updateWorkersTable(workerMetrics);
    }

    updateCharts(systemMetrics) {
        const now = new Date().toLocaleTimeString();

        // データ追加
        this.metricsHistory.cpu.push(systemMetrics.cpu_usage || 0);
        this.metricsHistory.memory.push(systemMetrics.memory_usage || 0);
        this.metricsHistory.timestamps.push(now);

        // データ制限
        if (this.metricsHistory.cpu.length > this.maxDataPoints) {
            this.metricsHistory.cpu.shift();
            this.metricsHistory.memory.shift();
            this.metricsHistory.timestamps.shift();
        }

        // チャート更新
        this.charts.cpu.data.labels = [...this.metricsHistory.timestamps];
        this.charts.cpu.data.datasets[0].data = [...this.metricsHistory.cpu];
        this.charts.cpu.update('none');

        this.charts.memory.data.labels = [...this.metricsHistory.timestamps];
        this.charts.memory.data.datasets[0].data = [...this.metricsHistory.memory];
        this.charts.memory.update('none');
    }

    updateWorkersTable(workers) {
        const tbody = document.getElementById('workersTableBody');

        if (!workers || workers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">稼働中のワーカーがありません</td></tr>';
            return;
        }

        tbody.innerHTML = workers.map(worker => `
            <tr>
                <td>${worker.name}</td>
                <td>${worker.pid}</td>
                <td><span class="status-${worker.status}">${worker.status}</span></td>
                <td>${worker.cpu_percent?.toFixed(1) || 0}%</td>
                <td>${worker.memory_mb?.toFixed(0) || 0}MB</td>
                <td>${worker.uptime_human || '-'}</td>
            </tr>
        `).join('');
    }

    updateAlerts(alerts) {
        const container = document.getElementById('alertsContainer');

        if (!alerts || alerts.length === 0) {
            container.innerHTML = '<div class="no-alerts">現在アラートはありません</div>';
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="alert alert-${alert.severity}">
                <strong>${alert.severity === 'critical' ? '🚨' : '⚠️'} ${alert.type}</strong><br>
                ${alert.message}
                <small style="display: block; margin-top: 5px; opacity: 0.8;">
                    ${new Date(alert.timestamp).toLocaleString()}
                </small>
            </div>
        `).join('');
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const dot = statusElement.querySelector('.status-dot');
        const text = statusElement.querySelector('.status-text');

        if (connected) {
            dot.style.backgroundColor = '#4CAF50';
            text.textContent = '接続中';
        } else {
            dot.style.backgroundColor = '#f44336';
            text.textContent = '切断';
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
}

// ダッシュボード初期化
document.addEventListener('DOMContentLoaded', () => {
    new WorkerDashboard();
});
        """

        (static_dir / "dashboard.js").write_text(js_content, encoding="utf-8")

class WorkerMonitoringDashboard:
    """ワーカー監視ダッシュボード統合クラス"""

    def __init__(self, config: Optional[DashboardConfig] = None):
        """初期化メソッド"""
        self.config = config or DashboardConfig()

        # コンポーネント初期化
        self.metrics_collector = MetricsCollector(self.config)
        self.websocket_manager = WebSocketManager()
        self.realtime_updater = RealtimeUpdater(
            self.config, self.metrics_collector, self.websocket_manager
        )

        if FASTAPI_AVAILABLE:
            self.api = DashboardAPI(
                self.config, self.metrics_collector, self.websocket_manager
            )
        else:
            self.api = None

        # システム状態
        self.is_running = False
        self.server_task = None

        logger.info("Worker Monitoring Dashboard initialized")

    async def start(self) -> Dict[str, Any]:
        """ダッシュボード開始"""
        try:
            if not FASTAPI_AVAILABLE:
                return {"success": False, "error": "FastAPI not available"}

            # リアルタイム更新開始
            await self.realtime_updater.start_updates()

            # Webサーバー開始（バックグラウンド）
            config = uvicorn.Config(
                self.api.app,
                host="0.0.0.0",
                port=self.config.web_port,
                log_level="info",
            )
            server = uvicorn.Server(config)
            self.server_task = asyncio.create_task(server.serve())

            self.is_running = True

            logger.info(f"Dashboard started on http://localhost:{self.config.web_port}")

            return {
                "success": True,
                "web_server_port": self.config.web_port,
                "websocket_endpoint": f"ws://localhost:{self.config.web_port}/ws",
                "dashboard_url": f"http://localhost:{self.config.web_port}",
                "update_interval": self.config.update_interval,
            }

        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")
            return {"success": False, "error": str(e)}

    async def stop(self) -> Dict[str, Any]:
        """ダッシュボード停止"""
        try:
            # リアルタイム更新停止
            await self.realtime_updater.stop_updates()

            # Webサーバー停止
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass

            self.is_running = False

            logger.info("Dashboard stopped")

            return {"success": True, "cleanup_completed": True}

        except Exception as e:
            logger.error(f"Failed to stop dashboard: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """ダッシュボード状態取得"""
        return {
            "is_running": self.is_running,
            "config": asdict(self.config),
            "connections": self.websocket_manager.get_connection_stats(),
            "components": {
                "metrics_collector": "active",
                "websocket_manager": "active",
                "realtime_updater": (
                    "active" if self.realtime_updater.is_running else "inactive"
                ),
                "api": "active" if self.api else "unavailable",
            },
        }

    async def collect_and_broadcast_metrics(self) -> Dict[str, Any]:
        """メトリクス収集とブロードキャスト"""
        try:
            # メトリクス収集
            metrics = self.metrics_collector.collect_system_metrics()

            # WebSocket ブロードキャスト
            sent_count = await self.websocket_manager.broadcast(
                {
                    "type": "metrics_update",
                    "data": metrics,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "success": True,
                "metrics_collected": True,
                "clients_notified": sent_count,
            }

        except Exception as e:
            logger.error(f"Failed to collect and broadcast metrics: {e}")
            return {"success": False, "error": str(e)}
