#!/usr/bin/env python3
"""
🚨 Real-time Monitoring Enhancement System
リアルタイム監視強化システム

Incident Sageの叡智による異常検知・予測的インシデント防止システム
pgvectorを活用した多次元異常検知とプロアクティブな問題解決

Author: Claude Elder
Date: 2025-07-10
Phase: 1 (リアルタイム監視強化)
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
import warnings
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import aiohttp
import numpy as np
import websockets
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent


class AnomalyType(Enum):
    """異常タイプ定義"""

    PERFORMANCE = "performance"  # パフォーマンス異常
    RESOURCE = "resource"  # リソース異常
    ERROR_RATE = "error_rate"  # エラー率異常
    BEHAVIOR = "behavior"  # 挙動異常
    SECURITY = "security"  # セキュリティ異常
    AVAILABILITY = "availability"  # 可用性異常


class SeverityLevel(Enum):
    """重要度レベル"""

    INFO = "info"  # 情報
    WARNING = "warning"  # 警告
    ERROR = "error"  # エラー
    CRITICAL = "critical"  # 緊急


class MonitoringTarget(Enum):
    """監視対象"""

    SYSTEM = "system"  # システム全体
    SERVICE = "service"  # 個別サービス
    ENDPOINT = "endpoint"  # APIエンドポイント
    DATABASE = "database"  # データベース
    NETWORK = "network"  # ネットワーク
    CUSTOM = "custom"  # カスタム


@dataclass
class MetricPoint:
    """メトリクスポイント"""

    timestamp: datetime
    target: MonitoringTarget
    metric_name: str
    value: float
    tags: Dict[str, str]
    metadata: Dict[str, Any]


@dataclass
class AnomalyEvent:
    """異常イベント"""

    event_id: str
    detected_at: datetime
    anomaly_type: AnomalyType
    severity: SeverityLevel
    target: MonitoringTarget
    metric_name: str
    current_value: float
    expected_range: Tuple[float, float]
    anomaly_score: float
    context: Dict[str, Any]
    suggested_actions: List[str]
    auto_resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class IncidentPrediction:
    """インシデント予測"""

    prediction_id: str
    predicted_at: datetime
    incident_type: str
    probability: float
    expected_time: datetime
    impact_assessment: Dict[str, Any]
    prevention_actions: List[Dict[str, Any]]
    confidence: float


@dataclass
class SystemHealthReport:
    """システム健全性レポート"""

    timestamp: datetime
    overall_health: float
    component_health: Dict[str, float]
    active_anomalies: List[AnomalyEvent]
    predicted_incidents: List[IncidentPrediction]
    recommendations: List[str]


class RealtimeMonitoringEnhancement:
    """リアルタイム監視強化システム"""

    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or self._default_config()

        # メトリクスストア
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.baseline_stats = {}

        # 異常検知モデル
        self.isolation_forest = IsolationForest(
            n_estimators=100, contamination=0.1, random_state=42
        )
        self.scaler = StandardScaler()

        # 異常イベント管理
        self.active_anomalies = {}
        self.anomaly_history = deque(maxlen=10000)

        # 予測モデル
        self.incident_predictions = {}
        self.prediction_accuracy = defaultdict(float)

        # WebSocketクライアント管理
        self.ws_clients = set()

        # 監視スレッド
        self.monitoring_active = False
        self.monitoring_thread = None

        # 統計情報
        self.stats = {
            "total_metrics_processed": 0,
            "total_anomalies_detected": 0,
            "total_incidents_prevented": 0,
            "false_positive_rate": 0.0,
            "mean_detection_time": 0.0,
        }

        # データベース初期化
        self._init_database()

        # ベースライン学習
        self._load_baseline_data()

        self.logger.info("🚨 Real-time Monitoring Enhancement System initialized")

    def _default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            "monitoring_interval": 5,  # 秒
            "anomaly_threshold": 0.7,
            "prediction_horizon": 300,  # 5分先まで予測
            "baseline_window": 86400,  # 24時間
            "alert_cooldown": 300,  # 5分
            "auto_resolve_timeout": 1800,  # 30分
            "websocket_port": 8765,
            "database_path": str(PROJECT_ROOT / "data" / "monitoring.db"),
        }

    def _init_database(self):
        """データベース初期化"""
        try:
            db_path = self.config["database_path"]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # メトリクステーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    target TEXT,
                    metric_name TEXT,
                    value REAL,
                    tags TEXT,
                    metadata TEXT
                );
            """
            )

            # 異常イベントテーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS anomaly_events (
                    event_id TEXT PRIMARY KEY,
                    detected_at TEXT,
                    anomaly_type TEXT,
                    severity TEXT,
                    target TEXT,
                    metric_name TEXT,
                    current_value REAL,
                    expected_min REAL,
                    expected_max REAL,
                    anomaly_score REAL,
                    context TEXT,
                    suggested_actions TEXT,
                    auto_resolved BOOLEAN,
                    resolved_at TEXT
                );
            """
            )

            # インシデント予測テーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_predictions (
                    prediction_id TEXT PRIMARY KEY,
                    predicted_at TEXT,
                    incident_type TEXT,
                    probability REAL,
                    expected_time TEXT,
                    impact_assessment TEXT,
                    prevention_actions TEXT,
                    confidence REAL,
                    actual_occurred BOOLEAN,
                    accuracy_score REAL
                );
            """
            )

            # システム健全性履歴テーブル
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    overall_health REAL,
                    component_health TEXT,
                    active_anomalies INTEGER,
                    predicted_incidents INTEGER,
                    recommendations TEXT
                );
            """
            )

            conn.commit()
            conn.close()

            self.logger.info("📊 Monitoring database initialized")

        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")

    async def start_monitoring(self):
        """監視開始"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return

        self.monitoring_active = True

        # 監視タスク開始
        tasks = [
            asyncio.create_task(self._metric_collection_loop()),
            asyncio.create_task(self._anomaly_detection_loop()),
            asyncio.create_task(self._incident_prediction_loop()),
            asyncio.create_task(self._auto_resolution_loop()),
            asyncio.create_task(self._websocket_server()),
        ]

        self.logger.info("🚀 Real-time monitoring started")

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
            self.monitoring_active = False

    async def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        self.logger.info("🛑 Real-time monitoring stopped")

    async def ingest_metric(self, metric: MetricPoint):
        """メトリクス取り込み"""
        try:
            # バッファに追加
            key = f"{metric.target.value}:{metric.metric_name}"
            self.metrics_buffer[key].append(metric)

            # 統計更新
            self.stats["total_metrics_processed"] += 1

            # リアルタイム異常検知
            anomaly = await self._detect_anomaly(metric)
            if anomaly:
                await self._handle_anomaly(anomaly)

            # データベース保存（バッチ処理用）
            if self.stats["total_metrics_processed"] % 100 == 0:
                await self._persist_metrics()

        except Exception as e:
            self.logger.error(f"Metric ingestion failed: {e}")

    async def _metric_collection_loop(self):
        """メトリクス収集ループ"""
        while self.monitoring_active:
            try:
                # システムメトリクス収集
                system_metrics = await self._collect_system_metrics()
                for metric in system_metrics:
                    await self.ingest_metric(metric)

                # サービスメトリクス収集
                service_metrics = await self._collect_service_metrics()
                for metric in service_metrics:
                    await self.ingest_metric(metric)

                await asyncio.sleep(self.config["monitoring_interval"])

            except Exception as e:
                self.logger.error(f"Metric collection error: {e}")
                await asyncio.sleep(10)

    async def _anomaly_detection_loop(self):
        """異常検知ループ"""
        while self.monitoring_active:
            try:
                # 各メトリクスの異常検知
                for key, buffer in self.metrics_buffer.items():
                    if len(buffer) >= 10:  # 十分なデータがある場合
                        await self._analyze_metric_stream(key, buffer)

                # 複合異常検知
                await self._detect_complex_anomalies()

                await asyncio.sleep(self.config["monitoring_interval"] * 2)

            except Exception as e:
                self.logger.error(f"Anomaly detection error: {e}")
                await asyncio.sleep(10)

    async def _incident_prediction_loop(self):
        """インシデント予測ループ"""
        while self.monitoring_active:
            try:
                # 現在の状態分析
                current_state = await self._analyze_current_state()

                # インシデント予測
                predictions = await self._predict_incidents(current_state)

                # 予測結果処理
                for prediction in predictions:
                    await self._handle_prediction(prediction)

                await asyncio.sleep(60)  # 1分毎

            except Exception as e:
                self.logger.error(f"Incident prediction error: {e}")
                await asyncio.sleep(60)

    async def _auto_resolution_loop(self):
        """自動解決ループ"""
        while self.monitoring_active:
            try:
                # アクティブな異常チェック
                for event_id, anomaly in list(self.active_anomalies.items()):
                    if await self._can_auto_resolve(anomaly):
                        await self._auto_resolve_anomaly(anomaly)

                await asyncio.sleep(30)  # 30秒毎

            except Exception as e:
                self.logger.error(f"Auto resolution error: {e}")
                await asyncio.sleep(30)

    async def _websocket_server(self):
        """WebSocketサーバー"""
        try:

            async def handle_client(websocket, path):
                self.ws_clients.add(websocket)
                try:
                    await websocket.wait_closed()
                finally:
                    self.ws_clients.remove(websocket)

            server = await websockets.serve(
                handle_client, "localhost", self.config["websocket_port"]
            )

            self.logger.info(
                f"📡 WebSocket server started on port {self.config['websocket_port']}"
            )
            await server.wait_closed()

        except Exception as e:
            self.logger.error(f"WebSocket server error: {e}")

    async def _collect_system_metrics(self) -> List[MetricPoint]:
        """システムメトリクス収集"""
        metrics = []
        now = datetime.now()

        # CPU使用率（ダミーデータ）
        metrics.append(
            MetricPoint(
                timestamp=now,
                target=MonitoringTarget.SYSTEM,
                metric_name="cpu_usage",
                value=np.random.normal(50, 10),
                tags={"host": "elders-guild-01"},
                metadata={"unit": "percent"},
            )
        )

        # メモリ使用率
        metrics.append(
            MetricPoint(
                timestamp=now,
                target=MonitoringTarget.SYSTEM,
                metric_name="memory_usage",
                value=np.random.normal(60, 15),
                tags={"host": "elders-guild-01"},
                metadata={"unit": "percent"},
            )
        )

        # ディスクI/O
        metrics.append(
            MetricPoint(
                timestamp=now,
                target=MonitoringTarget.SYSTEM,
                metric_name="disk_io",
                value=np.random.normal(100, 30),
                tags={"host": "elders-guild-01", "device": "sda"},
                metadata={"unit": "MB/s"},
            )
        )

        # ネットワークトラフィック
        metrics.append(
            MetricPoint(
                timestamp=now,
                target=MonitoringTarget.NETWORK,
                metric_name="network_traffic",
                value=np.random.normal(200, 50),
                tags={"interface": "eth0"},
                metadata={"unit": "MB/s"},
            )
        )

        return metrics

    async def _collect_service_metrics(self) -> List[MetricPoint]:
        """サービスメトリクス収集"""
        metrics = []
        now = datetime.now()

        # APIレスポンスタイム
        metrics.append(
            MetricPoint(
                timestamp=now,
                target=MonitoringTarget.ENDPOINT,
                metric_name="response_time",
                value=np.random.normal(100, 20),
                tags={"endpoint": "/api/v1/search", "method": "GET"},
                metadata={"unit": "ms"},
            )
        )

        # エラー率
        metrics.append(
            MetricPoint(
                timestamp=now,
                target=MonitoringTarget.SERVICE,
                metric_name="error_rate",
                value=np.random.normal(0.01, 0.005),
                tags={"service": "elder-api"},
                metadata={"unit": "ratio"},
            )
        )

        # データベース接続数
        metrics.append(
            MetricPoint(
                timestamp=now,
                target=MonitoringTarget.DATABASE,
                metric_name="connection_count",
                value=np.random.normal(50, 10),
                tags={"database": "pgvector_db"},
                metadata={"unit": "connections"},
            )
        )

        return metrics

    async def _detect_anomaly(self, metric: MetricPoint) -> Optional[AnomalyEvent]:
        """単一メトリクス異常検知"""
        key = f"{metric.target.value}:{metric.metric_name}"

        # ベースライン取得
        baseline = self.baseline_stats.get(key)
        if not baseline:
            return None

        # Zスコア計算
        z_score = (
            abs((metric.value - baseline["mean"]) / baseline["std"])
            if baseline["std"] > 0
            else 0
        )

        # 異常判定
        if z_score > 3:  # 3σ以上
            anomaly_score = min(1.0, z_score / 5)

            return AnomalyEvent(
                event_id=f"anomaly_{datetime.now(
                    ).strftime('%Y%m%d_%H%M%S')}_{key.replace(':',
                    '_'
                )}",
                detected_at=datetime.now(),
                anomaly_type=self._determine_anomaly_type(metric),
                severity=self._determine_severity(anomaly_score),
                target=metric.target,
                metric_name=metric.metric_name,
                current_value=metric.value,
                expected_range=(
                    baseline["mean"] - 3 * baseline["std"],
                    baseline["mean"] + 3 * baseline["std"],
                ),
                anomaly_score=anomaly_score,
                context={"tags": metric.tags, "metadata": metric.metadata},
                suggested_actions=await self._generate_suggested_actions(
                    metric, anomaly_score
                ),
            )

        return None

    async def _analyze_metric_stream(self, key: str, buffer: deque):
        """メトリクスストリーム分析"""
        if len(buffer) < 10:
            return

        # 最近のデータ取得
        recent_values = [m.value for m in list(buffer)[-30:]]

        # 統計計算
        mean = np.mean(recent_values)
        std = np.std(recent_values)

        # ベースライン更新
        self.baseline_stats[key] = {
            "mean": mean,
            "std": std,
            "min": min(recent_values),
            "max": max(recent_values),
            "updated_at": datetime.now(),
        }

        # トレンド検出
        if len(recent_values) >= 20:
            trend = np.polyfit(range(len(recent_values)), recent_values, 1)[0]
            if abs(trend) > std * 0.1:  # 有意なトレンド
                self.logger.info(f"📈 Trend detected in {key}: {trend:.3f}")

    async def _detect_complex_anomalies(self):
        """複合異常検知"""
        # 複数メトリクスの相関分析
        correlations = await self._analyze_metric_correlations()

        # 異常パターン検出
        for pattern in correlations:
            if pattern["anomaly_score"] > self.config["anomaly_threshold"]:
                await self._handle_complex_anomaly(pattern)

    async def _analyze_metric_correlations(self) -> List[Dict[str, Any]]:
        """メトリクス相関分析"""
        patterns = []

        # CPU と メモリの相関チェック
        cpu_key = "system:cpu_usage"
        memory_key = "system:memory_usage"

        if cpu_key in self.metrics_buffer and memory_key in self.metrics_buffer:
            cpu_values = [m.value for m in list(self.metrics_buffer[cpu_key])[-20:]]
            memory_values = [
                m.value for m in list(self.metrics_buffer[memory_key])[-20:]
            ]

            if len(cpu_values) == len(memory_values) and len(cpu_values) >= 10:
                correlation = np.corrcoef(cpu_values, memory_values)[0, 1]

                # 異常な相関
                if abs(correlation) > 0.9:
                    patterns.append(
                        {
                            "type": "high_correlation",
                            "metrics": [cpu_key, memory_key],
                            "correlation": correlation,
                            "anomaly_score": abs(correlation),
                        }
                    )

        return patterns

    async def _predict_incidents(
        self, current_state: Dict[str, Any]
    ) -> List[IncidentPrediction]:
        """インシデント予測"""
        predictions = []

        # リソース枯渇予測
        for key, buffer in self.metrics_buffer.items():
            if "usage" in key and len(buffer) >= 20:
                values = [m.value for m in list(buffer)[-20:]]

                # トレンド分析
                x = np.arange(len(values))
                slope, intercept = np.polyfit(x, values, 1)

                # 将来値予測
                future_steps = (
                    self.config["prediction_horizon"]
                    // self.config["monitoring_interval"]
                )
                predicted_value = slope * (len(values) + future_steps) + intercept

                # リソース枯渇リスク
                if predicted_value > 90:  # 90%以上
                    prediction = IncidentPrediction(
                        prediction_id=f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{key}",
                        predicted_at=datetime.now(),
                        incident_type="resource_exhaustion",
                        probability=min(1.0, predicted_value / 100),
                        expected_time=datetime.now()
                        + timedelta(seconds=self.config["prediction_horizon"]),
                        impact_assessment={
                            "affected_services": ["all"],
                            "severity": "high",
                            "estimated_downtime": 300,
                        },
                        prevention_actions=[
                            {
                                "action": "scale_resources",
                                "target": key,
                                "urgency": "high",
                            },
                            {
                                "action": "clear_cache",
                                "target": "system",
                                "urgency": "medium",
                            },
                        ],
                        confidence=0.7 + (0.3 * min(1.0, abs(slope) / 10)),
                    )
                    predictions.append(prediction)

        return predictions

    async def _analyze_current_state(self) -> Dict[str, Any]:
        """現在状態分析"""
        state = {
            "timestamp": datetime.now(),
            "metrics_summary": {},
            "active_anomalies": len(self.active_anomalies),
            "system_load": 0.0,
        }

        # 各メトリクスのサマリー
        for key, buffer in self.metrics_buffer.items():
            if buffer:
                recent_values = [m.value for m in list(buffer)[-10:]]
                state["metrics_summary"][key] = {
                    "mean": np.mean(recent_values),
                    "std": np.std(recent_values),
                    "last": recent_values[-1],
                }

        # システム負荷計算
        cpu_key = "system:cpu_usage"
        if cpu_key in state["metrics_summary"]:
            state["system_load"] = state["metrics_summary"][cpu_key]["mean"] / 100

        return state

    async def _handle_anomaly(self, anomaly: AnomalyEvent):
        """異常処理"""
        # アクティブ異常に追加
        self.active_anomalies[anomaly.event_id] = anomaly
        self.anomaly_history.append(anomaly)

        # 統計更新
        self.stats["total_anomalies_detected"] += 1

        # アラート送信
        await self._send_alert(anomaly)

        # 自動対応実行
        if anomaly.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]:
            await self._execute_auto_response(anomaly)

        # WebSocket通知
        await self._broadcast_anomaly(anomaly)

        # データベース保存
        await self._persist_anomaly(anomaly)

        self.logger.warning(
            f"🚨 Anomaly detected: {anomaly.event_id} - {anomaly.anomaly_type.value}"
        )

    async def _handle_prediction(self, prediction: IncidentPrediction):
        """予測処理"""
        # 予測記録
        self.incident_predictions[prediction.prediction_id] = prediction

        # 高確率予測の場合は予防アクション実行
        if prediction.probability > 0.7 and prediction.confidence > 0.8:
            await self._execute_prevention_actions(prediction)
            self.stats["total_incidents_prevented"] += 1

        # 通知
        await self._send_prediction_alert(prediction)

        # データベース保存
        await self._persist_prediction(prediction)

        self.logger.info(
            f"🔮 Incident predicted: {prediction.incident_type} - Probability: {prediction.probability:.2f}"
        )

    async def _execute_auto_response(self, anomaly: AnomalyEvent):
        """自動対応実行"""
        for action in anomaly.suggested_actions:
            if "restart" in action.lower():
                self.logger.info(
                    f"♻️ Auto-response: Restarting service for {anomaly.metric_name}"
                )
                # 実際のサービス再起動コード
            elif "scale" in action.lower():
                self.logger.info(
                    f"📈 Auto-response: Scaling resources for {anomaly.metric_name}"
                )
                # 実際のスケーリングコード
            elif "cache" in action.lower():
                self.logger.info(
                    f"🧹 Auto-response: Clearing cache for {anomaly.metric_name}"
                )
                # 実際のキャッシュクリアコード

    async def _execute_prevention_actions(self, prediction: IncidentPrediction):
        """予防アクション実行"""
        for action in prediction.prevention_actions:
            if action["urgency"] == "high":
                self.logger.info(
                    f"⚡ Prevention: Executing {action['action']} on {action['target']}"
                )
                # 実際の予防アクション実行

    async def _can_auto_resolve(self, anomaly: AnomalyEvent) -> bool:
        """自動解決可能判定"""
        if anomaly.auto_resolved:
            return False

        # タイムアウトチェック
        elapsed = (datetime.now() - anomaly.detected_at).total_seconds()
        if elapsed > self.config["auto_resolve_timeout"]:
            return True

        # メトリクス正常化チェック
        key = f"{anomaly.target.value}:{anomaly.metric_name}"
        if key in self.metrics_buffer:
            recent_values = [m.value for m in list(self.metrics_buffer[key])[-5:]]
            if recent_values:
                current_value = recent_values[-1]
                if (
                    anomaly.expected_range[0]
                    <= current_value
                    <= anomaly.expected_range[1]
                ):
                    return True

        return False

    async def _auto_resolve_anomaly(self, anomaly: AnomalyEvent):
        """異常自動解決"""
        anomaly.auto_resolved = True
        anomaly.resolved_at = datetime.now()

        # アクティブ異常から削除
        if anomaly.event_id in self.active_anomalies:
            del self.active_anomalies[anomaly.event_id]

        # 通知
        await self._send_resolution_notification(anomaly)

        self.logger.info(f"✅ Auto-resolved: {anomaly.event_id}")

    def _determine_anomaly_type(self, metric: MetricPoint) -> AnomalyType:
        """異常タイプ判定"""
        if "cpu" in metric.metric_name or "memory" in metric.metric_name:
            return AnomalyType.RESOURCE
        elif "response_time" in metric.metric_name:
            return AnomalyType.PERFORMANCE
        elif "error" in metric.metric_name:
            return AnomalyType.ERROR_RATE
        elif "security" in metric.metric_name:
            return AnomalyType.SECURITY
        else:
            return AnomalyType.BEHAVIOR

    def _determine_severity(self, anomaly_score: float) -> SeverityLevel:
        """重要度判定"""
        if anomaly_score >= 0.9:
            return SeverityLevel.CRITICAL
        elif anomaly_score >= 0.7:
            return SeverityLevel.ERROR
        elif anomaly_score >= 0.5:
            return SeverityLevel.WARNING
        else:
            return SeverityLevel.INFO

    async def _generate_suggested_actions(
        self, metric: MetricPoint, anomaly_score: float
    ) -> List[str]:
        """推奨アクション生成"""
        actions = []

        if "cpu" in metric.metric_name and anomaly_score > 0.8:
            actions.extend(
                [
                    "Scale up compute resources",
                    "Identify and optimize CPU-intensive processes",
                    "Enable CPU throttling for non-critical services",
                ]
            )
        elif "memory" in metric.metric_name and anomaly_score > 0.8:
            actions.extend(
                [
                    "Increase memory allocation",
                    "Clear application caches",
                    "Restart memory-leaking services",
                ]
            )
        elif "error_rate" in metric.metric_name and anomaly_score > 0.7:
            actions.extend(
                [
                    "Review recent deployments",
                    "Check dependency services",
                    "Enable detailed error logging",
                ]
            )
        elif "response_time" in metric.metric_name and anomaly_score > 0.7:
            actions.extend(
                [
                    "Scale application instances",
                    "Optimize database queries",
                    "Enable caching layers",
                ]
            )

        return actions

    async def _send_alert(self, anomaly: AnomalyEvent):
        """アラート送信"""
        alert_message = {
            "type": "anomaly_alert",
            "event_id": anomaly.event_id,
            "severity": anomaly.severity.value,
            "message": f"{anomaly.anomaly_type.value} anomaly detected in {anomaly.metric_name}",
            "current_value": anomaly.current_value,
            "expected_range": anomaly.expected_range,
            "suggested_actions": anomaly.suggested_actions,
        }

        # WebSocket送信
        await self._broadcast_message(alert_message)

        # その他の通知チャネル（メール、Slack等）への送信もここで実装

    async def _send_prediction_alert(self, prediction: IncidentPrediction):
        """予測アラート送信"""
        alert_message = {
            "type": "prediction_alert",
            "prediction_id": prediction.prediction_id,
            "incident_type": prediction.incident_type,
            "probability": prediction.probability,
            "expected_time": prediction.expected_time.isoformat(),
            "prevention_actions": prediction.prevention_actions,
        }

        await self._broadcast_message(alert_message)

    async def _send_resolution_notification(self, anomaly: AnomalyEvent):
        """解決通知送信"""
        notification = {
            "type": "anomaly_resolved",
            "event_id": anomaly.event_id,
            "resolved_at": (
                anomaly.resolved_at.isoformat() if anomaly.resolved_at else None
            ),
            "auto_resolved": anomaly.auto_resolved,
        }

        await self._broadcast_message(notification)

    async def _broadcast_anomaly(self, anomaly: AnomalyEvent):
        """異常情報ブロードキャスト"""
        message = {
            "type": "anomaly_update",
            "anomaly": {
                "event_id": anomaly.event_id,
                "detected_at": anomaly.detected_at.isoformat(),
                "anomaly_type": anomaly.anomaly_type.value,
                "severity": anomaly.severity.value,
                "metric_name": anomaly.metric_name,
                "current_value": anomaly.current_value,
                "anomaly_score": anomaly.anomaly_score,
            },
        }

        await self._broadcast_message(message)

    async def _broadcast_message(self, message: Dict[str, Any]):
        """WebSocketメッセージブロードキャスト"""
        if self.ws_clients:
            message_json = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_json) for client in self.ws_clients],
                return_exceptions=True,
            )

    async def _persist_metrics(self):
        """メトリクス永続化"""
        try:
            conn = sqlite3.connect(self.config["database_path"])
            cursor = conn.cursor()

            metrics_to_save = []
            for key, buffer in self.metrics_buffer.items():
                for metric in list(buffer)[-100:]:  # 最新100件
                    metrics_to_save.append(
                        (
                            metric.timestamp.isoformat(),
                            metric.target.value,
                            metric.metric_name,
                            metric.value,
                            json.dumps(metric.tags),
                            json.dumps(metric.metadata),
                        )
                    )

            cursor.executemany(
                """
                INSERT INTO metrics (timestamp, target, metric_name, value, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                metrics_to_save,
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Metrics persistence failed: {e}")

    async def _persist_anomaly(self, anomaly: AnomalyEvent):
        """異常イベント永続化"""
        try:
            conn = sqlite3.connect(self.config["database_path"])
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO anomaly_events
                (event_id, detected_at, anomaly_type, severity, target, metric_name,
                 current_value, expected_min, expected_max, anomaly_score, context,
                 suggested_actions, auto_resolved, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    anomaly.event_id,
                    anomaly.detected_at.isoformat(),
                    anomaly.anomaly_type.value,
                    anomaly.severity.value,
                    anomaly.target.value,
                    anomaly.metric_name,
                    anomaly.current_value,
                    anomaly.expected_range[0],
                    anomaly.expected_range[1],
                    anomaly.anomaly_score,
                    json.dumps(anomaly.context),
                    json.dumps(anomaly.suggested_actions),
                    anomaly.auto_resolved,
                    anomaly.resolved_at.isoformat() if anomaly.resolved_at else None,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Anomaly persistence failed: {e}")

    async def _persist_prediction(self, prediction: IncidentPrediction):
        """予測結果永続化"""
        try:
            conn = sqlite3.connect(self.config["database_path"])
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO incident_predictions
                (prediction_id, predicted_at, incident_type, probability, expected_time,
                 impact_assessment, prevention_actions, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    prediction.prediction_id,
                    prediction.predicted_at.isoformat(),
                    prediction.incident_type,
                    prediction.probability,
                    prediction.expected_time.isoformat(),
                    json.dumps(prediction.impact_assessment),
                    json.dumps(prediction.prevention_actions),
                    prediction.confidence,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Prediction persistence failed: {e}")

    def _load_baseline_data(self):
        """ベースラインデータ読み込み"""
        # 初期ベースライン設定
        self.baseline_stats = {
            "system:cpu_usage": {"mean": 50, "std": 10, "min": 0, "max": 100},
            "system:memory_usage": {"mean": 60, "std": 15, "min": 0, "max": 100},
            "system:disk_io": {"mean": 100, "std": 30, "min": 0, "max": 500},
            "network:network_traffic": {"mean": 200, "std": 50, "min": 0, "max": 1000},
            "endpoint:response_time": {"mean": 100, "std": 20, "min": 10, "max": 500},
            "service:error_rate": {"mean": 0.01, "std": 0.005, "min": 0, "max": 0.1},
            "database:connection_count": {"mean": 50, "std": 10, "min": 0, "max": 200},
        }

    async def get_system_health(self) -> SystemHealthReport:
        """システム健全性レポート取得"""
        # コンポーネント健全性計算
        component_health = {}

        for key, buffer in self.metrics_buffer.items():
            if buffer and key in self.baseline_stats:
                recent_values = [m.value for m in list(buffer)[-10:]]
                baseline = self.baseline_stats[key]

                # 正常範囲内の割合
                normal_count = sum(
                    1
                    for v in recent_values
                    if baseline["mean"] - 3 * baseline["std"]
                    <= v
                    <= baseline["mean"] + 3 * baseline["std"]
                )
                health_score = normal_count / len(recent_values) if recent_values else 0

                component_health[key] = health_score

        # 全体健全性
        overall_health = (
            np.mean(list(component_health.values())) if component_health else 1.0
        )

        # 推奨事項生成
        recommendations = []
        if overall_health < 0.8:
            recommendations.append(
                "System health is degraded. Review active anomalies."
            )
        if len(self.active_anomalies) > 5:
            recommendations.append(
                "Multiple active anomalies detected. Consider scaling resources."
            )
        if any(p.probability > 0.8 for p in self.incident_predictions.values()):
            recommendations.append(
                "High probability incidents predicted. Execute prevention actions."
            )

        return SystemHealthReport(
            timestamp=datetime.now(),
            overall_health=overall_health,
            component_health=component_health,
            active_anomalies=list(self.active_anomalies.values()),
            predicted_incidents=list(self.incident_predictions.values()),
            recommendations=recommendations,
        )

    async def handle_complex_anomaly(self, pattern: Dict[str, Any]):
        """複合異常処理"""
        # 複合異常イベント作成
        anomaly = AnomalyEvent(
            event_id=f"complex_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            detected_at=datetime.now(),
            anomaly_type=AnomalyType.BEHAVIOR,
            severity=SeverityLevel.ERROR,
            target=MonitoringTarget.SYSTEM,
            metric_name="complex_pattern",
            current_value=pattern["anomaly_score"],
            expected_range=(0, 0.5),
            anomaly_score=pattern["anomaly_score"],
            context=pattern,
            suggested_actions=[
                "Investigate correlated metrics",
                "Check for cascading failures",
                "Review system dependencies",
            ],
        )

        await self._handle_anomaly(anomaly)


# 使用例
async def main():
    """メイン実行関数"""
    try:
        # システム初期化
        monitoring = RealtimeMonitoringEnhancement()

        print("🚨 Starting Real-time Monitoring Enhancement System...")

        # 監視開始（バックグラウンド）
        monitoring_task = asyncio.create_task(monitoring.start_monitoring())

        # テストメトリクス送信
        print("\n📊 Sending test metrics...")

        for i in range(5):
            # 正常メトリクス
            await monitoring.ingest_metric(
                MetricPoint(
                    timestamp=datetime.now(),
                    target=MonitoringTarget.SYSTEM,
                    metric_name="cpu_usage",
                    value=50 + np.random.normal(0, 5),
                    tags={"host": "test-host"},
                    metadata={"unit": "percent"},
                )
            )

            # 異常メトリクス（高CPU）
            if i == 3:
                await monitoring.ingest_metric(
                    MetricPoint(
                        timestamp=datetime.now(),
                        target=MonitoringTarget.SYSTEM,
                        metric_name="cpu_usage",
                        value=95,  # 異常値
                        tags={"host": "test-host"},
                        metadata={"unit": "percent"},
                    )
                )

            await asyncio.sleep(1)

        # システム健全性確認
        print("\n🏥 Checking system health...")
        health_report = await monitoring.get_system_health()
        print(f"Overall Health: {health_report.overall_health:.2f}")
        print(f"Active Anomalies: {len(health_report.active_anomalies)}")
        print(f"Predicted Incidents: {len(health_report.predicted_incidents)}")

        # 統計情報
        print("\n📈 Monitoring Statistics:")
        print(f"Total Metrics Processed: {monitoring.stats['total_metrics_processed']}")
        print(
            f"Total Anomalies Detected: {monitoring.stats['total_anomalies_detected']}"
        )
        print(
            f"Total Incidents Prevented: {monitoring.stats['total_incidents_prevented']}"
        )

        # 停止
        await monitoring.stop_monitoring()
        monitoring_task.cancel()

        print("\n🎉 Real-time Monitoring Enhancement System Phase 1 testing completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
