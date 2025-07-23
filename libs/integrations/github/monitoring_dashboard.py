#!/usr/bin/env python3
"""
📊 Enhanced Auto Issue Processor - 運用監視とメトリクス収集
Issue #92 最終実装: リアルタイム監視ダッシュボード
"""

import asyncio
import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AutoIssueMonitoring")


@dataclass
class ProcessingMetrics:
    """処理メトリクス"""

    timestamp: str
    issue_number: int
    issue_title: str
    priority: str
    processing_status: str  # 'started', 'completed', 'failed', 'skipped'
    processing_time_seconds: float
    sage_consultation_time: float
    pr_creation_time: float
    error_message: Optional[str] = None
    pr_url: Optional[str] = None
    four_sages_availability: bool = True
    overall_confidence: float = 0.0
    implementation_recommended: bool = False


@dataclass
class SystemHealthMetrics:
    """システムヘルスメトリクス"""

    timestamp: str
    github_api_status: str
    four_sages_status: Dict[str, str]
    git_operations_status: str
    pr_creation_success_rate: float
    avg_processing_time: float
    active_processes: int
    queue_size: int


class MetricsDatabase:
    """メトリクス専用データベース"""

    def __init__(self, db_path:
        """初期化メソッド"""
    str = "logs/auto_issue_metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
        self._lock = threading.Lock()

    def _init_database(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            # 処理メトリクステーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processing_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    issue_number INTEGER NOT NULL,
                    issue_title TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    processing_status TEXT NOT NULL,
                    processing_time_seconds REAL NOT NULL,
                    sage_consultation_time REAL NOT NULL,
                    pr_creation_time REAL NOT NULL,
                    error_message TEXT,
                    pr_url TEXT,
                    four_sages_availability BOOLEAN NOT NULL,
                    overall_confidence REAL NOT NULL,
                    implementation_recommended BOOLEAN NOT NULL
                )
            """
            )

            # システムヘルスメトリクステーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS system_health_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    github_api_status TEXT NOT NULL,
                    four_sages_knowledge_status TEXT NOT NULL,
                    four_sages_task_status TEXT NOT NULL,
                    four_sages_incident_status TEXT NOT NULL,
                    four_sages_rag_status TEXT NOT NULL,
                    git_operations_status TEXT NOT NULL,
                    pr_creation_success_rate REAL NOT NULL,
                    avg_processing_time REAL NOT NULL,
                    active_processes INTEGER NOT NULL,
                    queue_size INTEGER NOT NULL
                )
            """
            )

            # インデックス作成
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_processing_timestamp ON " \
                    "processing_metrics(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_health_timestamp ON " \
                    "system_health_metrics(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_issue_number ON processing_metrics(issue_number)"
            )

    def insert_processing_metrics(self, metrics: ProcessingMetrics):
        """処理メトリクスを挿入"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO processing_metrics (
                        timestamp, issue_number, issue_title, priority, processing_status,
                        processing_time_seconds, sage_consultation_time, pr_creation_time,
                        error_message, pr_url, four_sages_availability, overall_confidence,
                        implementation_recommended
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.timestamp,
                        metrics.issue_number,
                        metrics.issue_title,
                        metrics.priority,
                        metrics.processing_status,
                        metrics.processing_time_seconds,
                        metrics.sage_consultation_time,
                        metrics.pr_creation_time,
                        metrics.error_message,
                        metrics.pr_url,
                        metrics.four_sages_availability,
                        metrics.overall_confidence,
                        metrics.implementation_recommended,
                    ),
                )

    def insert_system_health_metrics(self, metrics: SystemHealthMetrics):
        """システムヘルスメトリクスを挿入"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO system_health_metrics (
                        timestamp, github_api_status, four_sages_knowledge_status,
                        four_sages_task_status, four_sages_incident_status, four_sages_rag_status,
                        git_operations_status, pr_creation_success_rate, avg_processing_time,
                        active_processes, queue_size
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.timestamp,
                        metrics.github_api_status,
                        metrics.four_sages_status.get("knowledge", "unknown"),
                        metrics.four_sages_status.get("task", "unknown"),
                        metrics.four_sages_status.get("incident", "unknown"),
                        metrics.four_sages_status.get("rag", "unknown"),
                        metrics.git_operations_status,
                        metrics.pr_creation_success_rate,
                        metrics.avg_processing_time,
                        metrics.active_processes,
                        metrics.queue_size,
                    ),
                )

    def get_processing_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """処理メトリクスを取得"""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM processing_metrics
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (since,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_system_health_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """システムヘルスメトリクスを取得"""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM system_health_metrics
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (since,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_summary_stats(self, hours: int = 24) -> Dict[str, Any]:
        """サマリー統計を取得"""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 処理統計
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_processed,
                    SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN processing_status = 'skipped' THEN 1 ELSE 0 END) as skipped,
                    AVG(processing_time_seconds) as avg_processing_time,
                    AVG(sage_consultation_time) as avg_consultation_time,
                    AVG(pr_creation_time) as avg_pr_creation_time,
                    AVG(overall_confidence) as avg_confidence
                FROM processing_metrics
                WHERE timestamp >= ?
            """,
                (since,),
            )

            stats = dict(cursor.fetchone())

            # 成功率計算
            if stats["total_processed"] > 0:
                stats["success_rate"] = (
                    stats["successful"] / stats["total_processed"]
                ) * 100
            else:
                stats["success_rate"] = 0.0

            return stats


class AlertingSystem:
    """アラートシステム"""

    def __init__(self, alert_config:
        """初期化メソッド"""
    Dict[str, Any] = None):
        self.alert_config = alert_config or {
            "success_rate_threshold": 80.0,  # 成功率80%未満でアラート
            "avg_processing_time_threshold": 300.0,  # 平均処理時間5分以上でアラート
            "consecutive_failures_threshold": 3,  # 連続失敗3回でアラート
            "four_sages_down_threshold": 2,  # 2つ以上の賢者がダウンでアラート
        }
        self.alert_log = Path("logs/auto_issue_alerts.log")
        self.alert_log.parent.mkdir(exist_ok=True)

    def check_and_alert(self, metrics_db: MetricsDatabase) -> List[Dict[str, Any]]:
        """メトリクスをチェックしてアラートを生成"""
        alerts = []

        # 過去24時間の統計を取得
        stats = metrics_db.get_summary_stats(24)

        # 成功率チェック
        if stats["success_rate"] < self.alert_config["success_rate_threshold"]:
            alerts.append(
                {
                    "type": "low_success_rate",
                    "severity": "warning",
                    "message": f"Success rate is {stats['success_rate']:.1f}% " \
                        "(threshold: {self.alert_config['success_rate_threshold']}%)",
                    "timestamp": datetime.now().isoformat(),
                    "details": {
                        "current_rate": stats["success_rate"],
                        "threshold": self.alert_config["success_rate_threshold"],
                    },
                }
            )

        # 平均処理時間チェック
        if (
            stats["avg_processing_time"]
            and stats["avg_processing_time"]
            > self.alert_config["avg_processing_time_threshold"]
        ):
            alerts.append(
                {
                    "type": "high_processing_time",
                    "severity": "warning",
                    "message": f"Average processing time is 
                        f"{stats['avg_processing_time']:.1f}s (threshold: {self.alert_config['avg_processing_time_threshold']}s)",
                    "timestamp": datetime.now().isoformat(),
                    "details": {
                        "current_time": stats["avg_processing_time"],
                        "threshold": self.alert_config["avg_processing_time_threshold"],
                    },
                }
            )

        # 連続失敗チェック
        recent_failures = self._check_consecutive_failures(metrics_db)
        if recent_failures >= self.alert_config["consecutive_failures_threshold"]:
            alerts.append(
                {
                    "type": "consecutive_failures",
                    "severity": "critical",
                    "message": f"Consecutive failures detected: 
                        f"{recent_failures} (threshold: {self.alert_config['consecutive_failures_threshold']})",
                    "timestamp": datetime.now().isoformat(),
                    "details": {
                        "consecutive_failures": recent_failures,
                        "threshold": self.alert_config[
                            "consecutive_failures_threshold"
                        ],
                    },
                }
            )

        # アラートをログに記録
        if alerts:
            self._log_alerts(alerts)

        return alerts

    def _check_consecutive_failures(self, metrics_db: MetricsDatabase) -> int:
        """連続失敗数をチェック"""
        recent_metrics = metrics_db.get_processing_metrics(hours=1)
        consecutive_failures = 0

        for metric in recent_metrics:
            if metric["processing_status"] == "failed":
                consecutive_failures += 1
            else:
                break

        return consecutive_failures

    def _log_alerts(self, alerts: List[Dict[str, Any]]):
        """アラートをログに記録"""
        with open(self.alert_log, "a", encoding="utf-8") as f:
            for alert in alerts:
                f.write(f"{json.dumps(alert, ensure_ascii=False)}\n")


class AutoIssueMonitoringDashboard:
    """Auto Issue Processor監視ダッシュボード"""

    def __init__(self):
        """初期化メソッド"""
        self.metrics_db = MetricsDatabase()
        self.alerting = AlertingSystem()
        self.is_monitoring = False
        self.monitoring_thread = None

    def record_processing_start(
        self, issue_number: int, issue_title: str, priority: str
    ) -> str:
        """処理開始を記録"""
        processing_id = f"proc_{issue_number}_{int(time.time())}"

        metrics = ProcessingMetrics(
            timestamp=datetime.now().isoformat(),
            issue_number=issue_number,
            issue_title=issue_title,
            priority=priority,
            processing_status="started",
            processing_time_seconds=0.0,
            sage_consultation_time=0.0,
            pr_creation_time=0.0,
        )

        self.metrics_db.insert_processing_metrics(metrics)

        logger.info(f"📊 Processing started: Issue #{issue_number}")
        return processing_id

    def record_processing_completion(
        self,
        issue_number: int,
        issue_title: str,
        priority: str,
        processing_time: float,
        sage_consultation_time: float,
        pr_creation_time: float,
        success: bool,
        pr_url: Optional[str] = None,
        error_message: Optional[str] = None,
        overall_confidence: float = 0.0,
        implementation_recommended: bool = False,
    ):
        """処理完了を記録"""
        status = "completed" if success else "failed"

        metrics = ProcessingMetrics(
            timestamp=datetime.now().isoformat(),
            issue_number=issue_number,
            issue_title=issue_title,
            priority=priority,
            processing_status=status,
            processing_time_seconds=processing_time,
            sage_consultation_time=sage_consultation_time,
            pr_creation_time=pr_creation_time,
            error_message=error_message,
            pr_url=pr_url,
            overall_confidence=overall_confidence,
            implementation_recommended=implementation_recommended,
        )

        self.metrics_db.insert_processing_metrics(metrics)

        logger.info(
            f"📊 Processing {status}: Issue #{issue_number} (Time: {processing_time:.2f}s)"
        )

    def record_system_health(
        self,
        github_api_status: str = "healthy",
        four_sages_status: Dict[str, str] = None,
        git_operations_status: str = "healthy",
        active_processes: int = 0,
        queue_size: int = 0,
    ):
        """システムヘルスを記録"""
        if four_sages_status is None:
            four_sages_status = {
                "knowledge": "healthy",
                "task": "healthy",
                "incident": "healthy",
                "rag": "healthy",
            }

        # 過去1時間の統計を計算
        stats = self.metrics_db.get_summary_stats(hours=1)

        metrics = SystemHealthMetrics(
            timestamp=datetime.now().isoformat(),
            github_api_status=github_api_status,
            four_sages_status=four_sages_status,
            git_operations_status=git_operations_status,
            pr_creation_success_rate=stats.get("success_rate", 0.0),
            avg_processing_time=stats.get("avg_processing_time", 0.0),
            active_processes=active_processes,
            queue_size=queue_size,
        )

        self.metrics_db.insert_system_health_metrics(metrics)

    def get_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """ダッシュボード用データを取得"""
        processing_metrics = self.metrics_db.get_processing_metrics(hours)
        health_metrics = self.metrics_db.get_system_health_metrics(hours)
        summary_stats = self.metrics_db.get_summary_stats(hours)
        alerts = self.alerting.check_and_alert(self.metrics_db)

        return {
            "summary": summary_stats,
            "processing_metrics": processing_metrics[:50],  # 最新50件
            "health_metrics": health_metrics[:50],  # 最新50件
            "alerts": alerts,
            "timestamp": datetime.now().isoformat(),
            "monitoring_period_hours": hours,
        }

    def start_continuous_monitoring(self, interval_seconds: int = 60):
        """継続監視を開始"""
        if self.is_monitoring:
            logger.warning("Monitoring is already running")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval_seconds,), daemon=True
        )
        self.monitoring_thread.start()

        logger.info(f"📊 Continuous monitoring started (interval: {interval_seconds}s)")

    def stop_continuous_monitoring(self):
        """継続監視を停止"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        logger.info("📊 Continuous monitoring stopped")

    def _monitoring_loop(self, interval_seconds: int):
        """監視ループ"""
        while self.is_monitoring:
            try:
                # システムヘルスを記録
                self.record_system_health()

                # アラートチェック
                alerts = self.alerting.check_and_alert(self.metrics_db)
                if alerts:
                    logger.warning(f"🚨 {len(alerts)} alerts generated")

                time.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval_seconds)

    def generate_report(self, hours: int = 24) -> str:
        """レポートを生成"""
        data = self.get_dashboard_data(hours)

        report = f"""
# Auto Issue Processor 監視レポート

**生成時刻**: {data['timestamp']}
**監視期間**: 過去{hours}時間

## 📊 サマリー統計

- **総処理数**: {data['summary']['total_processed']}
- **成功数**: {data['summary']['successful']}
- **失敗数**: {data['summary']['failed']}
- **スキップ数**: {data['summary']['skipped']}
- **成功率**: {data['summary']['success_rate']:.1f}%
- **平均処理時間**: {data['summary']['avg_processing_time']:.1f}秒
- **平均相談時間**: {data['summary']['avg_consultation_time']:.1f}秒
- **平均PR作成時間**: {data['summary']['avg_pr_creation_time']:.1f}秒
- **平均信頼度**: {data['summary']['avg_confidence']:.1f}%

## 🚨 アクティブアラート

"""

        if data["alerts"]:
            for alert in data["alerts"]:
                report += f"- **{alert['severity'].upper()}**: {alert['message']}\n"
        else:
            report += "- アラートなし ✅\n"

        report += f"""

## 📈 最近の処理状況

"""

        for metric in data["processing_metrics"][:10]:
            status_emoji = (
                "✅"
                if metric["processing_status"] == "completed"
                else "❌" if metric["processing_status"] == "failed" else "⏭️"
            )
            report += f"- {status_emoji} Issue #{metric['issue_number']}: " \
                "{metric['issue_title']} ({metric['processing_time_seconds']:.1f}s)\n"

        return report

    def export_metrics(self, hours: int = 24, format: str = "json") -> str:
        """メトリクスをエクスポート"""
        data = self.get_dashboard_data(hours)

        if format == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format == "csv":
            # CSV形式での出力（簡略版）
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # ヘッダー
            writer.writerow(
                [
                    "timestamp",
                    "issue_number",
                    "issue_title",
                    "status",
                    "processing_time",
                ]
            )

            # データ
            for metric in data["processing_metrics"]:
                writer.writerow(
                    [
                        metric["timestamp"],
                        metric["issue_number"],
                        metric["issue_title"],
                        metric["processing_status"],
                        metric["processing_time_seconds"],
                    ]
                )

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


# CLI機能
async def main():
    """メイン関数（CLI使用）"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Auto Issue Processor Monitoring Dashboard"
    )
    parser.add_argument("--dashboard", action="store_true", help="Show dashboard data")
    parser.add_argument(
        "--report", action="store_true", help="Generate monitoring report"
    )
    parser.add_argument("--export", choices=["json", "csv"], help="Export metrics")
    parser.add_argument("--hours", type=int, default=24, help="Time period in hours")
    parser.add_argument(
        "--monitor", action="store_true", help="Start continuous monitoring"
    )
    parser.add_argument(
        "--test-record", action="store_true", help="Record test metrics"
    )

    args = parser.parse_args()

    dashboard = AutoIssueMonitoringDashboard()

    try:
        if args.test_record:
            # テストメトリクスを記録
            dashboard.record_processing_start(999, "Test Issue", "medium")
            time.sleep(1)
            dashboard.record_processing_completion(
                999,
                "Test Issue",
                "medium",
                1.5,
                0.5,
                0.8,
                True,
                "https://github.com/test/repo/pull/999",
                None,
                0.85,
                True,
            )
            print("Test metrics recorded")

        elif args.dashboard:
            # ダッシュボードデータ表示
            data = dashboard.get_dashboard_data(args.hours)
            print(json.dumps(data, indent=2, ensure_ascii=False))

        elif args.report:
            # レポート生成
            report = dashboard.generate_report(args.hours)
            print(report)

        elif args.export:
            # メトリクスエクスポート
            exported = dashboard.export_metrics(args.hours, args.export)
            print(exported)

        elif args.monitor:
            # 継続監視開始
            dashboard.start_continuous_monitoring(60)
            print("Continuous monitoring started. Press Ctrl+C to stop.")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                dashboard.stop_continuous_monitoring()
                print("\nMonitoring stopped.")

        else:
            print("使用方法:")
            print("  python monitoring_dashboard.py --dashboard --hours 24")
            print("  python monitoring_dashboard.py --report --hours 12")
            print("  python monitoring_dashboard.py --export json --hours 6")
            print("  python monitoring_dashboard.py --monitor")
            print("  python monitoring_dashboard.py --test-record")

    except Exception as e:
        logger.error(f"実行エラー: {e}")
        print(f"エラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
