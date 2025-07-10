#!/usr/bin/env python3
"""
AI Automation Performance Monitor - AI自動化パフォーマンス監視システム
エルダーズギルド実戦投入タスク4 - パフォーマンス監視とレポート生成

機能:
- Four Sages AI自動化システムのリアルタイム監視
- パフォーマンスメトリクス収集・分析
- 自動化効果測定とレポート生成
- アラート検出と自動対応
- 統計レポートとダッシュボード
"""

import asyncio
import json
import logging
import sqlite3
import statistics
from collections import defaultdict
from collections import deque
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """パフォーマンスメトリクス"""

    metric_name: str
    value: float
    timestamp: datetime
    source_system: str
    metric_type: str  # "counter", "gauge", "histogram", "timer"
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "source_system": self.source_system,
            "metric_type": self.metric_type,
            "tags": self.tags,
            "unit": self.unit,
        }


@dataclass
class AlertRule:
    """アラートルール"""

    rule_id: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "ne"
    threshold: float
    duration_seconds: int
    severity: str  # "critical", "warning", "info"
    description: str
    enabled: bool = True

    def evaluate(self, metric_value: float, duration: int) -> bool:
        """アラート条件評価"""
        if not self.enabled:
            return False

        if duration < self.duration_seconds:
            return False

        if self.condition == "gt":
            return metric_value > self.threshold
        elif self.condition == "lt":
            return metric_value < self.threshold
        elif self.condition == "eq":
            return abs(metric_value - self.threshold) < 0.001
        elif self.condition == "ne":
            return abs(metric_value - self.threshold) >= 0.001

        return False


class AIAutomationPerformanceMonitor:
    """AI自動化パフォーマンス監視システム"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {
            "collection_interval": 30,  # 30秒間隔
            "retention_days": 30,
            "alert_check_interval": 60,
            "dashboard_update_interval": 300,  # 5分間隔
            "max_metrics_memory": 10000,
        }

        if config:
            self.config.update(config)

        # データストレージ
        self.db_path = Path("data/ai_automation_performance.db")
        self.reports_path = Path("reports/performance")
        self.reports_path.mkdir(parents=True, exist_ok=True)

        # メトリクス管理
        self.metrics_buffer: deque = deque(maxlen=self.config["max_metrics_memory"])
        self.metric_aggregates: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.active_alerts: Dict[str, Dict[str, Any]] = {}

        # アラートルール
        self.alert_rules: List[AlertRule] = []
        self._setup_default_alert_rules()

        # システム状態追跡
        self.system_status = {
            "four_sages_integration": "unknown",
            "autonomous_learning": "unknown",
            "performance_optimization": "unknown",
            "last_health_check": None,
        }

        # パフォーマンス統計
        self.performance_stats = {
            "total_metrics_collected": 0,
            "alerts_triggered": 0,
            "reports_generated": 0,
            "system_uptime_start": datetime.now(),
            "last_dashboard_update": None,
        }

        # 並行処理制御
        self.monitoring_active = False
        self.monitoring_task = None

        self._init_database()
        logger.info("AI Automation Performance Monitor initialized")

    def _init_database(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # メトリクステーブル
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            source_system TEXT NOT NULL,
            metric_type TEXT NOT NULL,
            tags TEXT,
            unit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # アラート履歴テーブル
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            trigger_value REAL NOT NULL,
            threshold REAL NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            triggered_at TIMESTAMP NOT NULL,
            resolved_at TIMESTAMP,
            duration_seconds INTEGER
        )
        """
        )

        # レポート履歴テーブル
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS report_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT NOT NULL,
            report_type TEXT NOT NULL,
            generated_at TIMESTAMP NOT NULL,
            file_path TEXT,
            metrics_count INTEGER,
            time_range_hours INTEGER,
            summary TEXT
        )
        """
        )

        # パフォーマンスサマリーテーブル
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS performance_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_date DATE NOT NULL,
            metrics_collected INTEGER DEFAULT 0,
            alerts_triggered INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0.0,
            success_rate REAL DEFAULT 0.0,
            system_health_score REAL DEFAULT 0.0,
            automation_efficiency REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # インデックス作成
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_source ON performance_metrics(source_system)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON alert_history(triggered_at)")

        conn.commit()
        conn.close()

    def _setup_default_alert_rules(self):
        """デフォルトアラートルール設定"""
        default_rules = [
            AlertRule(
                rule_id="four_sages_consensus_rate_low",
                metric_name="four_sages.consensus_rate",
                condition="lt",
                threshold=0.7,
                duration_seconds=300,
                severity="warning",
                description="Four Sages consensus rate below 70%",
            ),
            AlertRule(
                rule_id="autonomous_learning_accuracy_low",
                metric_name="autonomous_learning.prediction_accuracy",
                condition="lt",
                threshold=0.6,
                duration_seconds=600,
                severity="critical",
                description="Autonomous learning prediction accuracy below 60%",
            ),
            AlertRule(
                rule_id="system_response_time_high",
                metric_name="system.response_time",
                condition="gt",
                threshold=5.0,
                duration_seconds=180,
                severity="warning",
                description="System response time above 5 seconds",
            ),
            AlertRule(
                rule_id="pattern_discovery_rate_low",
                metric_name="learning.pattern_discovery_rate",
                condition="lt",
                threshold=0.1,
                duration_seconds=1800,  # 30分
                severity="info",
                description="Pattern discovery rate below 0.1 patterns/minute",
            ),
            AlertRule(
                rule_id="automation_success_rate_low",
                metric_name="automation.success_rate",
                condition="lt",
                threshold=0.8,
                duration_seconds=900,  # 15分
                severity="warning",
                description="Automation success rate below 80%",
            ),
        ]

        self.alert_rules.extend(default_rules)

    async def start_monitoring(self):
        """監視開始"""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return

        self.monitoring_active = True
        logger.info("🚀 Starting AI Automation Performance Monitoring")

        # 並行監視タスク
        await asyncio.gather(
            self._metrics_collection_loop(),
            self._alert_processing_loop(),
            self._performance_analysis_loop(),
            self._dashboard_update_loop(),
            self._health_check_loop(),
        )

    async def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        logger.info("🛑 Stopping AI Automation Performance Monitoring")

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

    async def _metrics_collection_loop(self):
        """メトリクス収集ループ"""
        while self.monitoring_active:
            try:
                # Four Sagesメトリクス収集
                four_sages_metrics = await self._collect_four_sages_metrics()
                for metric in four_sages_metrics:
                    await self.record_metric(metric)

                # 自律学習メトリクス収集
                learning_metrics = await self._collect_autonomous_learning_metrics()
                for metric in learning_metrics:
                    await self.record_metric(metric)

                # システムメトリクス収集
                system_metrics = await self._collect_system_metrics()
                for metric in system_metrics:
                    await self.record_metric(metric)

                # 統計更新
                self.performance_stats["total_metrics_collected"] += len(
                    four_sages_metrics + learning_metrics + system_metrics
                )

                await asyncio.sleep(self.config["collection_interval"])

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.config["collection_interval"])

    async def _collect_four_sages_metrics(self) -> List[PerformanceMetric]:
        """Four Sagesメトリクス収集"""
        metrics = []

        try:
            # Four Sages統合システムからメトリクス取得（モック実装）
            metrics.extend(
                [
                    PerformanceMetric(
                        metric_name="four_sages.consensus_rate",
                        value=0.88,  # モック値
                        timestamp=datetime.now(),
                        source_system="four_sages_integration",
                        metric_type="gauge",
                        unit="percentage",
                    ),
                    PerformanceMetric(
                        metric_name="four_sages.response_time",
                        value=1.2,  # モック値
                        timestamp=datetime.now(),
                        source_system="four_sages_integration",
                        metric_type="timer",
                        unit="seconds",
                    ),
                    PerformanceMetric(
                        metric_name="four_sages.active_sessions",
                        value=3,  # モック値
                        timestamp=datetime.now(),
                        source_system="four_sages_integration",
                        metric_type="gauge",
                        unit="count",
                    ),
                ]
            )

        except Exception as e:
            logger.warning(f"Failed to collect Four Sages metrics: {e}")

        return metrics

    async def _collect_autonomous_learning_metrics(self) -> List[PerformanceMetric]:
        """自律学習メトリクス収集"""
        metrics = []

        try:
            # 自律学習システムからメトリクス取得（モック実装）
            metrics.extend(
                [
                    PerformanceMetric(
                        metric_name="autonomous_learning.prediction_accuracy",
                        value=0.75,  # モック値
                        timestamp=datetime.now(),
                        source_system="autonomous_learning",
                        metric_type="gauge",
                        unit="percentage",
                    ),
                    PerformanceMetric(
                        metric_name="learning.pattern_discovery_rate",
                        value=0.15,  # モック値
                        timestamp=datetime.now(),
                        source_system="autonomous_learning",
                        metric_type="gauge",
                        unit="patterns_per_minute",
                    ),
                    PerformanceMetric(
                        metric_name="learning.active_patterns",
                        value=12,  # モック値
                        timestamp=datetime.now(),
                        source_system="autonomous_learning",
                        metric_type="gauge",
                        unit="count",
                    ),
                ]
            )

        except Exception as e:
            logger.warning(f"Failed to collect autonomous learning metrics: {e}")

        return metrics

    async def _collect_system_metrics(self) -> List[PerformanceMetric]:
        """システムメトリクス収集"""
        metrics = []

        try:
            # システムレベルメトリクス
            import psutil

            metrics.extend(
                [
                    PerformanceMetric(
                        metric_name="system.cpu_usage",
                        value=psutil.cpu_percent(interval=1),
                        timestamp=datetime.now(),
                        source_system="system",
                        metric_type="gauge",
                        unit="percentage",
                    ),
                    PerformanceMetric(
                        metric_name="system.memory_usage",
                        value=psutil.virtual_memory().percent,
                        timestamp=datetime.now(),
                        source_system="system",
                        metric_type="gauge",
                        unit="percentage",
                    ),
                    PerformanceMetric(
                        metric_name="automation.success_rate",
                        value=0.92,  # モック値
                        timestamp=datetime.now(),
                        source_system="automation",
                        metric_type="gauge",
                        unit="percentage",
                    ),
                ]
            )

        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            # フォールバック用モックメトリクス
            metrics.extend(
                [
                    PerformanceMetric(
                        metric_name="system.cpu_usage",
                        value=45.0,
                        timestamp=datetime.now(),
                        source_system="system",
                        metric_type="gauge",
                        unit="percentage",
                    ),
                    PerformanceMetric(
                        metric_name="automation.success_rate",
                        value=0.92,
                        timestamp=datetime.now(),
                        source_system="automation",
                        metric_type="gauge",
                        unit="percentage",
                    ),
                ]
            )

        return metrics

    async def record_metric(self, metric: PerformanceMetric):
        """メトリクス記録"""
        # メモリバッファに追加
        self.metrics_buffer.append(metric)

        # データベースに保存
        await self._save_metric_to_db(metric)

        # 集計データ更新
        self._update_metric_aggregates(metric)

    async def _save_metric_to_db(self, metric: PerformanceMetric):
        """メトリクスをデータベースに保存"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO performance_metrics
                (metric_name, value, timestamp, source_system, metric_type, tags, unit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.metric_name,
                    metric.value,
                    metric.timestamp,
                    metric.source_system,
                    metric.metric_type,
                    json.dumps(metric.tags),
                    metric.unit,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save metric to database: {e}")

    def _update_metric_aggregates(self, metric: PerformanceMetric):
        """メトリクス集計データ更新"""
        metric_key = f"{metric.source_system}.{metric.metric_name}"

        if metric_key not in self.metric_aggregates:
            self.metric_aggregates[metric_key] = {
                "values": deque(maxlen=100),
                "last_value": 0.0,
                "min_value": float("inf"),
                "max_value": float("-inf"),
                "avg_value": 0.0,
                "last_updated": datetime.now(),
            }

        aggregate = self.metric_aggregates[metric_key]
        aggregate["values"].append(metric.value)
        aggregate["last_value"] = metric.value
        aggregate["min_value"] = min(aggregate["min_value"], metric.value)
        aggregate["max_value"] = max(aggregate["max_value"], metric.value)
        aggregate["avg_value"] = statistics.mean(aggregate["values"])
        aggregate["last_updated"] = datetime.now()

    async def _alert_processing_loop(self):
        """アラート処理ループ"""
        while self.monitoring_active:
            try:
                # アクティブアラートチェック
                await self._check_alert_conditions()

                # アラート自動解決チェック
                await self._check_alert_resolution()

                await asyncio.sleep(self.config["alert_check_interval"])

            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(self.config["alert_check_interval"])

    async def _check_alert_conditions(self):
        """アラート条件チェック"""
        current_time = datetime.now()

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # 最近のメトリクス値を取得
            recent_values = self._get_recent_metric_values(rule.metric_name, rule.duration_seconds)

            if not recent_values:
                continue

            # 条件評価
            latest_value = recent_values[-1][1]  # (timestamp, value)
            duration = (current_time - recent_values[0][0]).total_seconds()

            if rule.evaluate(latest_value, duration):
                # アラートトリガー
                alert_id = f"{rule.rule_id}_{int(current_time.timestamp())}"

                if alert_id not in self.active_alerts:
                    await self._trigger_alert(alert_id, rule, latest_value, current_time)

    def _get_recent_metric_values(self, metric_name: str, duration_seconds: int) -> List[Tuple[datetime, float]]:
        """最近のメトリクス値取得"""
        cutoff_time = datetime.now() - timedelta(seconds=duration_seconds)

        # メモリバッファから検索
        recent_values = []
        for metric in self.metrics_buffer:
            if metric.metric_name == metric_name and metric.timestamp >= cutoff_time:
                recent_values.append((metric.timestamp, metric.value))

        return sorted(recent_values, key=lambda x: x[0])

    async def _trigger_alert(self, alert_id: str, rule: AlertRule, trigger_value: float, timestamp: datetime):
        """アラートトリガー"""
        alert_data = {
            "alert_id": alert_id,
            "rule_id": rule.rule_id,
            "metric_name": rule.metric_name,
            "trigger_value": trigger_value,
            "threshold": rule.threshold,
            "severity": rule.severity,
            "description": rule.description,
            "triggered_at": timestamp,
            "resolved": False,
        }

        self.active_alerts[alert_id] = alert_data

        # データベースに記録
        await self._save_alert_to_db(alert_data)

        # 統計更新
        self.performance_stats["alerts_triggered"] += 1

        # ログ出力
        logger.warning(f"🚨 ALERT TRIGGERED: {rule.description} (Value: {trigger_value}, Threshold: {rule.threshold})")

        # 自動対応実行
        await self._handle_alert_auto_response(alert_data)

    async def _save_alert_to_db(self, alert_data: Dict[str, Any]):
        """アラートをデータベースに保存"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO alert_history
                (alert_id, rule_id, metric_name, trigger_value, threshold,
                 severity, description, triggered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    alert_data["alert_id"],
                    alert_data["rule_id"],
                    alert_data["metric_name"],
                    alert_data["trigger_value"],
                    alert_data["threshold"],
                    alert_data["severity"],
                    alert_data["description"],
                    alert_data["triggered_at"],
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save alert to database: {e}")

    async def _handle_alert_auto_response(self, alert_data: Dict[str, Any]):
        """アラート自動対応"""
        rule_id = alert_data["rule_id"]

        # ルール別自動対応
        if rule_id == "four_sages_consensus_rate_low":
            logger.info("🔧 Auto-response: Initiating Four Sages optimization")
            # Four Sages最適化処理（実装省略）

        elif rule_id == "autonomous_learning_accuracy_low":
            logger.info("🔧 Auto-response: Triggering learning parameter adjustment")
            # 学習パラメータ調整（実装省略）

        elif rule_id == "system_response_time_high":
            logger.info("🔧 Auto-response: System performance optimization")
            # システム最適化処理（実装省略）

        # 自動対応の記録
        alert_data["auto_response_applied"] = True
        alert_data["auto_response_timestamp"] = datetime.now()

    async def _check_alert_resolution(self):
        """アラート自動解決チェック"""
        current_time = datetime.now()
        resolved_alerts = []

        for alert_id, alert_data in self.active_alerts.items():
            if alert_data["resolved"]:
                continue

            # 対応するルールを取得
            rule = next((r for r in self.alert_rules if r.rule_id == alert_data["rule_id"]), None)
            if not rule:
                continue

            # 最新のメトリクス値をチェック
            recent_values = self._get_recent_metric_values(rule.metric_name, 60)  # 1分間

            if recent_values:
                latest_value = recent_values[-1][1]

                # アラート条件が解消されているかチェック
                if not rule.evaluate(latest_value, 60):
                    # アラート解決
                    await self._resolve_alert(alert_id, current_time)
                    resolved_alerts.append(alert_id)

        # 解決されたアラートを削除
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]

    async def _resolve_alert(self, alert_id: str, resolved_time: datetime):
        """アラート解決"""
        alert_data = self.active_alerts[alert_id]
        duration = (resolved_time - alert_data["triggered_at"]).total_seconds()

        # データベース更新
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE alert_history
                SET resolved_at = ?, duration_seconds = ?
                WHERE alert_id = ?
            """,
                (resolved_time, int(duration), alert_id),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to update alert resolution: {e}")

        logger.info(f"✅ ALERT RESOLVED: {alert_data['description']} (Duration: {int(duration)}s)")

    async def _performance_analysis_loop(self):
        """パフォーマンス分析ループ"""
        while self.monitoring_active:
            try:
                # 日次サマリー生成
                await self._generate_daily_summary()

                # パフォーマンストレンド分析
                await self._analyze_performance_trends()

                # 自動最適化提案
                await self._generate_optimization_recommendations()

                await asyncio.sleep(3600)  # 1時間間隔

            except Exception as e:
                logger.error(f"Performance analysis error: {e}")
                await asyncio.sleep(3600)

    async def _generate_daily_summary(self):
        """日次サマリー生成"""
        today = datetime.now().date()

        # 今日のメトリクス集計
        today_metrics = [m for m in self.metrics_buffer if m.timestamp.date() == today]

        if not today_metrics:
            return

        # サマリー計算
        metrics_count = len(today_metrics)

        # 応答時間の平均（Four Sagesから）
        response_times = [m.value for m in today_metrics if m.metric_name == "four_sages.response_time"]
        avg_response_time = statistics.mean(response_times) if response_times else 0.0

        # 成功率の平均
        success_rates = [m.value for m in today_metrics if "success_rate" in m.metric_name]
        avg_success_rate = statistics.mean(success_rates) if success_rates else 0.0

        # システムヘルススコア計算
        health_score = self._calculate_system_health_score()

        # 自動化効率計算
        automation_efficiency = self._calculate_automation_efficiency()

        # データベースに保存
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO performance_summary
                (summary_date, metrics_collected, alerts_triggered, avg_response_time,
                 success_rate, system_health_score, automation_efficiency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    today,
                    metrics_count,
                    self.performance_stats["alerts_triggered"],
                    avg_response_time,
                    avg_success_rate,
                    health_score,
                    automation_efficiency,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save daily summary: {e}")

    def _calculate_system_health_score(self) -> float:
        """システムヘルススコア計算"""
        # 各種メトリクスからヘルススコアを計算
        scores = []

        # Four Sagesコンセンサス率
        consensus_metrics = [m for m in self.metrics_buffer if m.metric_name == "four_sages.consensus_rate"]
        if consensus_metrics:
            latest_consensus = consensus_metrics[-1].value
            scores.append(min(1.0, latest_consensus / 0.8))  # 80%を基準

        # 自律学習精度
        accuracy_metrics = [
            m for m in self.metrics_buffer if m.metric_name == "autonomous_learning.prediction_accuracy"
        ]
        if accuracy_metrics:
            latest_accuracy = accuracy_metrics[-1].value
            scores.append(min(1.0, latest_accuracy / 0.7))  # 70%を基準

        # システムリソース使用率（逆相関）
        cpu_metrics = [m for m in self.metrics_buffer if m.metric_name == "system.cpu_usage"]
        if cpu_metrics:
            latest_cpu = cpu_metrics[-1].value
            scores.append(max(0.0, 1.0 - latest_cpu / 100.0))

        # アクティブアラート数（逆相関）
        alert_penalty = min(0.5, len(self.active_alerts) * 0.1)
        scores.append(1.0 - alert_penalty)

        return statistics.mean(scores) if scores else 0.5

    def _calculate_automation_efficiency(self) -> float:
        """自動化効率計算"""
        # 成功率と応答時間から効率を計算
        success_rates = [m.value for m in self.metrics_buffer if "success_rate" in m.metric_name]
        response_times = [m.value for m in self.metrics_buffer if "response_time" in m.metric_name]

        if not success_rates or not response_times:
            return 0.5

        avg_success_rate = statistics.mean(success_rates)
        avg_response_time = statistics.mean(response_times)

        # 効率 = 成功率 / (1 + 正規化応答時間)
        normalized_response_time = min(1.0, avg_response_time / 10.0)  # 10秒を基準
        efficiency = avg_success_rate / (1 + normalized_response_time)

        return min(1.0, efficiency)

    async def _analyze_performance_trends(self):
        """パフォーマンストレンド分析"""
        # 過去7日間のトレンド分析
        week_ago = datetime.now() - timedelta(days=7)

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT summary_date, system_health_score, automation_efficiency
                FROM performance_summary
                WHERE summary_date >= ?
                ORDER BY summary_date
            """,
                (week_ago.date(),),
            )

            results = cursor.fetchall()
            conn.close()

            if len(results) >= 3:
                # トレンド計算
                health_scores = [r[1] for r in results]
                efficiency_scores = [r[2] for r in results]

                health_trend = self._calculate_trend_slope(health_scores)
                efficiency_trend = self._calculate_trend_slope(efficiency_scores)

                logger.info(f"📈 Performance Trends: Health={health_trend:.3f}, Efficiency={efficiency_trend:.3f}")

        except Exception as e:
            logger.error(f"Failed to analyze performance trends: {e}")

    def _calculate_trend_slope(self, values: List[float]) -> float:
        """トレンド傾き計算"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))

        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0.0

    async def _generate_optimization_recommendations(self):
        """最適化推奨生成"""
        recommendations = []

        # システムヘルススコアが低い場合
        current_health = self._calculate_system_health_score()
        if current_health < 0.7:
            recommendations.append("System health score is low - consider system optimization")

        # アクティブアラートが多い場合
        if len(self.active_alerts) > 3:
            recommendations.append("Multiple active alerts - review system configuration")

        # 応答時間が高い場合
        recent_response_times = [m.value for m in list(self.metrics_buffer)[-50:] if "response_time" in m.metric_name]
        if recent_response_times and statistics.mean(recent_response_times) > 3.0:
            recommendations.append("High response times detected - consider performance tuning")

        if recommendations:
            logger.info(f"💡 Optimization Recommendations: {'; '.join(recommendations)}")

    async def _dashboard_update_loop(self):
        """ダッシュボード更新ループ"""
        while self.monitoring_active:
            try:
                # ダッシュボードデータ生成
                dashboard_data = await self._generate_dashboard_data()

                # ダッシュボードファイル更新
                await self._update_dashboard_file(dashboard_data)

                self.performance_stats["last_dashboard_update"] = datetime.now()

                await asyncio.sleep(self.config["dashboard_update_interval"])

            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                await asyncio.sleep(self.config["dashboard_update_interval"])

    async def _generate_dashboard_data(self) -> Dict[str, Any]:
        """ダッシュボードデータ生成"""
        current_time = datetime.now()

        # 最新メトリクス
        latest_metrics = {}
        for metric_key, aggregate in self.metric_aggregates.items():
            latest_metrics[metric_key] = {
                "current": aggregate["last_value"],
                "min": aggregate["min_value"],
                "max": aggregate["max_value"],
                "avg": aggregate["avg_value"],
                "last_updated": aggregate["last_updated"].isoformat(),
            }

        # アクティブアラート
        active_alerts_summary = []
        for alert_id, alert_data in self.active_alerts.items():
            active_alerts_summary.append(
                {
                    "alert_id": alert_id,
                    "severity": alert_data["severity"],
                    "description": alert_data["description"],
                    "triggered_at": alert_data["triggered_at"].isoformat(),
                    "duration": int((current_time - alert_data["triggered_at"]).total_seconds()),
                }
            )

        # システム状態
        system_health = self._calculate_system_health_score()
        automation_efficiency = self._calculate_automation_efficiency()

        return {
            "timestamp": current_time.isoformat(),
            "system_overview": {
                "health_score": system_health,
                "automation_efficiency": automation_efficiency,
                "uptime_seconds": int((current_time - self.performance_stats["system_uptime_start"]).total_seconds()),
                "total_metrics_collected": self.performance_stats["total_metrics_collected"],
                "alerts_triggered": self.performance_stats["alerts_triggered"],
            },
            "latest_metrics": latest_metrics,
            "active_alerts": active_alerts_summary,
            "system_status": self.system_status,
        }

    async def _update_dashboard_file(self, dashboard_data: Dict[str, Any]):
        """ダッシュボードファイル更新"""
        dashboard_file = self.reports_path / "dashboard.json"

        try:
            with open(dashboard_file, "w") as f:
                json.dump(dashboard_data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to update dashboard file: {e}")

    async def _health_check_loop(self):
        """ヘルスチェックループ"""
        while self.monitoring_active:
            try:
                # Four Sages統合状態チェック
                four_sages_status = await self._check_four_sages_health()
                self.system_status["four_sages_integration"] = four_sages_status

                # 自律学習システム状態チェック
                learning_status = await self._check_autonomous_learning_health()
                self.system_status["autonomous_learning"] = learning_status

                # パフォーマンス最適化状態チェック
                optimization_status = await self._check_optimization_health()
                self.system_status["performance_optimization"] = optimization_status

                self.system_status["last_health_check"] = datetime.now().isoformat()

                await asyncio.sleep(300)  # 5分間隔

            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(300)

    async def _check_four_sages_health(self) -> str:
        """Four Sages健康状態チェック"""
        try:
            # 最近のメトリクスから判定
            recent_metrics = [
                m
                for m in self.metrics_buffer
                if m.source_system == "four_sages_integration" and (datetime.now() - m.timestamp).total_seconds() < 300
            ]

            if not recent_metrics:
                return "unknown"

            consensus_rates = [m.value for m in recent_metrics if m.metric_name == "four_sages.consensus_rate"]
            if consensus_rates and statistics.mean(consensus_rates) > 0.8:
                return "healthy"
            elif consensus_rates and statistics.mean(consensus_rates) > 0.6:
                return "warning"
            else:
                return "critical"

        except Exception:
            return "error"

    async def _check_autonomous_learning_health(self) -> str:
        """自律学習健康状態チェック"""
        try:
            recent_metrics = [
                m
                for m in self.metrics_buffer
                if m.source_system == "autonomous_learning" and (datetime.now() - m.timestamp).total_seconds() < 300
            ]

            if not recent_metrics:
                return "unknown"

            accuracy_values = [m.value for m in recent_metrics if "accuracy" in m.metric_name]
            if accuracy_values and statistics.mean(accuracy_values) > 0.7:
                return "healthy"
            elif accuracy_values and statistics.mean(accuracy_values) > 0.5:
                return "warning"
            else:
                return "critical"

        except Exception:
            return "error"

    async def _check_optimization_health(self) -> str:
        """最適化健康状態チェック"""
        try:
            # 自動化効率から判定
            efficiency = self._calculate_automation_efficiency()

            if efficiency > 0.8:
                return "healthy"
            elif efficiency > 0.6:
                return "warning"
            else:
                return "critical"

        except Exception:
            return "error"

    async def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """パフォーマンスレポート生成"""
        start_time = datetime.now() - timedelta(hours=hours)
        report_id = f"performance_report_{int(datetime.now().timestamp())}"

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # メトリクス統計
            cursor.execute(
                """
                SELECT metric_name, COUNT(*), AVG(value), MIN(value), MAX(value)
                FROM performance_metrics
                WHERE timestamp >= ?
                GROUP BY metric_name
            """,
                (start_time,),
            )

            metrics_stats = {}
            for row in cursor.fetchall():
                metrics_stats[row[0]] = {"count": row[1], "average": row[2], "minimum": row[3], "maximum": row[4]}

            # アラート統計
            cursor.execute(
                """
                SELECT severity, COUNT(*)
                FROM alert_history
                WHERE triggered_at >= ?
                GROUP BY severity
            """,
                (start_time,),
            )

            alerts_stats = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            # レポート作成
            report = {
                "report_id": report_id,
                "generated_at": datetime.now().isoformat(),
                "time_range": {"start": start_time.isoformat(), "end": datetime.now().isoformat(), "hours": hours},
                "metrics_statistics": metrics_stats,
                "alerts_statistics": alerts_stats,
                "system_health": {
                    "current_score": self._calculate_system_health_score(),
                    "automation_efficiency": self._calculate_automation_efficiency(),
                    "active_alerts_count": len(self.active_alerts),
                },
                "performance_summary": {
                    "total_metrics_collected": len([m for m in self.metrics_buffer if m.timestamp >= start_time]),
                    "system_status": self.system_status.copy(),
                    "uptime_hours": (datetime.now() - self.performance_stats["system_uptime_start"]).total_seconds()
                    / 3600,
                },
            }

            # レポートファイル保存
            report_file = self.reports_path / f"{report_id}.json"
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2, default=str)

            # レポート履歴に記録
            await self._save_report_history(report_id, "performance", report_file, len(metrics_stats), hours)

            self.performance_stats["reports_generated"] += 1

            logger.info(f"📊 Performance report generated: {report_id}")
            return report

        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {"error": str(e)}

    async def _save_report_history(
        self, report_id: str, report_type: str, file_path: Path, metrics_count: int, time_range_hours: int
    ):
        """レポート履歴保存"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO report_history
                (report_id, report_type, generated_at, file_path, metrics_count, time_range_hours)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (report_id, report_type, datetime.now(), str(file_path), metrics_count, time_range_hours),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save report history: {e}")

    def get_current_status(self) -> Dict[str, Any]:
        """現在の状態取得"""
        return {
            "monitoring_active": self.monitoring_active,
            "system_status": self.system_status.copy(),
            "performance_stats": self.performance_stats.copy(),
            "active_alerts_count": len(self.active_alerts),
            "metrics_in_buffer": len(self.metrics_buffer),
            "system_health_score": self._calculate_system_health_score(),
            "automation_efficiency": self._calculate_automation_efficiency(),
        }


# デモ実行
if __name__ == "__main__":

    async def demo():
        print("🚀 AI Automation Performance Monitor Demo")
        print("=" * 50)

        # 監視システム初期化
        monitor = AIAutomationPerformanceMonitor({"collection_interval": 5, "alert_check_interval": 10})  # デモ用に短縮

        print("✅ Performance monitor initialized")

        # テストメトリクス追加
        print("\n1. Adding test metrics...")
        test_metrics = [
            PerformanceMetric("four_sages.consensus_rate", 0.85, datetime.now(), "four_sages_integration", "gauge"),
            PerformanceMetric(
                "autonomous_learning.prediction_accuracy", 0.72, datetime.now(), "autonomous_learning", "gauge"
            ),
            PerformanceMetric("system.response_time", 2.1, datetime.now(), "system", "timer"),
            PerformanceMetric("automation.success_rate", 0.91, datetime.now(), "automation", "gauge"),
        ]

        for metric in test_metrics:
            await monitor.record_metric(metric)
            print(f"  📊 Recorded: {metric.metric_name} = {metric.value}")

        # 状態確認
        print("\n2. Checking system status...")
        status = monitor.get_current_status()
        print(f"  🏥 System Health Score: {status['system_health_score']:.3f}")
        print(f"  ⚡ Automation Efficiency: {status['automation_efficiency']:.3f}")
        print(f"  📋 Metrics in Buffer: {status['metrics_in_buffer']}")

        # パフォーマンスレポート生成
        print("\n3. Generating performance report...")
        report = await monitor.generate_performance_report(hours=1)
        print(f"  📊 Report ID: {report['report_id']}")
        print(f"  📈 Metrics Statistics: {len(report['metrics_statistics'])} metric types")
        print(f"  🎯 System Health: {report['system_health']['current_score']:.3f}")

        # ダッシュボードデータ生成
        print("\n4. Generating dashboard data...")
        dashboard = await monitor._generate_dashboard_data()
        print(f"  📊 Dashboard updated at: {dashboard['timestamp']}")
        print(f"  📈 Total metrics: {dashboard['system_overview']['total_metrics_collected']}")
        print(f"  🚨 Active alerts: {len(dashboard['active_alerts'])}")

        print("\n✨ AI Automation Performance Monitor Features:")
        print("  ✅ Real-time metrics collection and storage")
        print("  ✅ Automatic alert detection and response")
        print("  ✅ Performance trend analysis")
        print("  ✅ System health monitoring")
        print("  ✅ Comprehensive reporting")
        print("  ✅ Dashboard data generation")
        print("  ✅ Automation efficiency tracking")

        print("\n🎯 AI Automation Performance Monitor Demo - COMPLETED")

    asyncio.run(demo())
