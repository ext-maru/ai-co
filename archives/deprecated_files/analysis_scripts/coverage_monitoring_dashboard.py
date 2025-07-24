#!/usr/bin/env python3
"""
Week 4 Strategic Infrastructure - Coverage Monitoring Dashboard
Real-time coverage tracking, alerting, and historical trend analysis

Mission: Provide comprehensive monitoring of the 66.7% coverage achievement
with proactive alerting, trend analysis, and integration with quality systems.

Features:
- Real-time coverage monitoring and tracking
- Historical trend analysis with visualization
- Alerting system for coverage degradation
- Integration with Elder Council quality review
- 4 Sages system integration for intelligent monitoring
- Automated report generation and distribution
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import json
import logging
import queue
import smtplib
import sqlite3
import subprocess
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Import existing systems
try:
    from elder_council_review import ElderCouncilReview
    from libs.four_sages_integration import FourSagesIntegration
except ImportError as e:
    print(f"⚠️ Warning: Could not import some components: {e}")
    ElderCouncilReview = None
    FourSagesIntegration = None

logger = logging.getLogger(__name__)


@dataclass
class CoverageMetrics:
    """Coverage metrics snapshot"""

    timestamp: datetime
    total_coverage: float
    statements_covered: int
    statements_missing: int
    total_statements: int
    branch_coverage: float
    files_analyzed: int
    test_files_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_coverage": self.total_coverage,
            "statements_covered": self.statements_covered,
            "statements_missing": self.statements_missing,
            "total_statements": self.total_statements,
            "branch_coverage": self.branch_coverage,
            "files_analyzed": self.files_analyzed,
            "test_files_count": self.test_files_count,
        }


@dataclass
class CoverageAlert:
    """Coverage alert definition"""

    alert_id: str
    alert_type: str  # 'degradation', 'threshold', 'trend', 'quality'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityGateResult:
    """Quality gate evaluation result"""

    gate_name: str
    passed: bool
    score: float
    threshold: float
    details: Dict[str, Any]
    timestamp: datetime


class CoverageMonitoringDashboard:
    """
    Real-time Coverage Monitoring Dashboard

    Provides comprehensive coverage monitoring with:
    - Real-time tracking and alerting
    - Historical trend analysis
    - Quality gate integration
    - Elder Council coordination
    - 4 Sages system integration
    """

    def __init__(self, config_path: Optional[str] = None)self.logger = logging.getLogger(__name__)
    """Initialize Coverage Monitoring Dashboard"""
        self.project_root = PROJECT_ROOT
        self.db_path = self.project_root / "data" / "coverage_monitoring.db"

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize systems
        self.elder_council = ElderCouncilReview() if ElderCouncilReview else None
        self.four_sages = FourSagesIntegration() if FourSagesIntegration else None

        # Coverage thresholds and targets
        self.coverage_targets = {
            "strategic_target": 66.7,  # Week 4 strategic target
            "maintenance_threshold": 65.0,  # Minimum acceptable
            "warning_threshold": 60.0,  # Warning level
            "critical_threshold": 55.0,  # Critical alert level
            "trend_degradation": -2.0,  # % degradation for trend alert
            "quality_gate_minimum": 70.0,  # Quality gate minimum
        }

        # Monitoring state
        self.monitoring_active = False
        self.alert_queue = queue.Queue()
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 measurements
        self.current_metrics = None
        self.last_measurement_time = None

        # Alert tracking
        self.active_alerts = {}
        self.alert_cooldown = timedelta(minutes=30)  # Prevent spam

        # Initialize database
        self._init_database()

        self.logger.info("Coverage Monitoring Dashboard initialized")
        self.logger.info(
            f"Strategic target: {self.coverage_targets['strategic_target']}%"
        )

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "monitoring_interval": 300,  # 5 minutes
            "alerting_enabled": True,
            "trend_analysis_window": 24,  # hours
            "quality_gates_enabled": True,
            "email_notifications": False,
            "slack_notifications": False,
            "dashboard_update_interval": 60,  # seconds
            "coverage_analysis_paths": ["core", "workers", "libs", "commands"],
            "excluded_paths": ["tests", "__pycache__", ".git", "venv"],
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path) as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Could not load config from {config_path}: {e}")

        return default_config

    def _init_database(self):
        """Initialize monitoring database"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3connect(str(self.db_path))
            cursor = conn.cursor()

            # Coverage metrics history
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS coverage_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                total_coverage REAL,
                statements_covered INTEGER,
                statements_missing INTEGER,
                total_statements INTEGER,
                branch_coverage REAL,
                files_analyzed INTEGER,
                test_files_count INTEGER,
                measurement_type TEXT DEFAULT 'automatic'
            )
            """
            )

            # Alert history
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS coverage_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                current_value REAL,
                threshold_value REAL,
                timestamp TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_timestamp TIMESTAMP
            )
            """
            )

            # Quality gate results
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS quality_gates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gate_name TEXT,
                passed BOOLEAN,
                score REAL,
                threshold REAL,
                details TEXT,
                timestamp TIMESTAMP
            )
            """
            )

            # Trend analysis cache
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT,
                time_window TEXT,
                trend_data TEXT,
                analysis_timestamp TIMESTAMP
            )
            """
            )

            conn.commit()
            conn.close()

            self.logger.info("Coverage monitoring database initialized")

        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")

    async def start_monitoring(self):
        """Start real-time coverage monitoring"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        self.logger.info("Starting real-time coverage monitoring...")

        # Start monitoring tasks
        monitoring_tasks = [
            asyncio.create_task(self._coverage_monitoring_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._trend_analysis_loop()),
            asyncio.create_task(self._quality_gate_monitoring_loop()),
        ]

        try:
            await asyncio.gather(*monitoring_tasks)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            self.monitoring_active = False

    async def _coverage_monitoring_loop(self):
        """Main coverage monitoring loop"""
        while self.monitoring_active:
            try:
                # Measure current coverage
                metrics = await self._measure_coverage()

                if metrics:
                    # Update current state
                    self.current_metrics = metrics
                    self.last_measurement_time = datetime.now()
                    self.metrics_history.append(metrics)

                    # Save to database
                    await self._save_metrics(metrics)

                    # Check for alerts
                    await self._check_coverage_alerts(metrics)

                    # Update dashboard data
                    await self._update_dashboard_data(metrics)

                    self.logger.debug(
                        f"Coverage measured: {metrics.total_coverage:0.1f}%"
                    )

                # Wait for next measurement
                await asyncio.sleep(self.config["monitoring_interval"])

            except Exception as e:
                self.logger.error(f"Coverage monitoring error: {e}")
                await asyncio.sleep(60)  # Error backoff

    async def _measure_coverage(self) -> Optional[CoverageMetrics]:
        """Measure current test coverage"""
        try:
            # Run coverage analysis
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "--cov=.",
                "--cov-report=json:coverage_temp.json",
                "--collect-only",
                "-q",
            ]

            # Add coverage paths
            for path in self.config["coverage_analysis_paths"]:
                if Path(path).exists():
                    cmd.extend([f"--cov={path}"])

            # Execute coverage measurement
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, cwd=self.project_root
            )

            # Parse coverage results
            coverage_file = self.project_root / "coverage_temp.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)

                # Extract metrics
                totals = coverage_data.get("totals", {})
                files = coverage_data.get("files", {})

                metrics = CoverageMetrics(
                    timestamp=datetime.now(),
                    total_coverage=totals.get("percent_covered", 0.0),
                    statements_covered=totals.get("covered_lines", 0),
                    statements_missing=totals.get("missing_lines", 0),
                    total_statements=totals.get("num_statements", 0),
                    branch_coverage=totals.get("percent_covered_display", 0.0),
                    files_analyzed=len(files),
                    test_files_count=len([f for f in files.keys() if "test_" in f]),
                )

                # Cleanup temp file
                coverage_file.unlink()

                return metrics

        except subprocess.TimeoutExpired:
            self.logger.warning("Coverage measurement timed out")
        except Exception as e:
            self.logger.error(f"Coverage measurement failed: {e}")

        return None

    async def _check_coverage_alerts(self, metrics: CoverageMetrics):
        """Check for coverage-related alerts"""
        current_coverage = metrics.total_coverage

        # Check threshold alerts
        if current_coverage < self.coverage_targets["critical_threshold"]:
            await self._create_alert(
                "coverage_critical",
                "critical",
                f"Coverage critically low: {current_coverage:0.1f}% < {self.coverage_targets['critical_threshold']}%",
                current_coverage,
                self.coverage_targets["critical_threshold"],
            )
        elif current_coverage < self.coverage_targets["warning_threshold"]:
            await self._create_alert(
                "coverage_warning",
                "medium",
                f"Coverage below warning threshold: {current_coverage:0.1f}% < {self." \
                    "coverage_targets["warning_threshold']}%",
                current_coverage,
                self.coverage_targets["warning_threshold"],
            )

        # Check trend alerts
        if len(self.metrics_history) >= 5:
            recent_metrics = list(self.metrics_history)[-5:]
            trend = self._calculate_coverage_trend(recent_metrics)

            if trend < self.coverage_targets["trend_degradation"]:
                await self._create_alert(
                    "coverage_trend_degradation",
                    "high",
                    f"Coverage trend degrading: {trend:0.1f}% over recent measurements",
                    trend,
                    self.coverage_targets["trend_degradation"],
                )

        # Check strategic target deviation
        target_deviation = abs(
            current_coverage - self.coverage_targets["strategic_target"]
        )
        if target_deviation > 5.0:
            severity = "high" if target_deviation > 10.0 else "medium"
            await self._create_alert(
                "strategic_target_deviation",
                severity,
                f"Coverage deviation from strategic target: {current_coverage:0.1f}% vs {self." \
                    "coverage_targets["strategic_target']}%",
                current_coverage,
                self.coverage_targets["strategic_target"],
            )

    def _calculate_coverage_trend(self, metrics_list: List[CoverageMetrics]) -> floatif len(metrics_list) < 2:
    """Calculate coverage trend over time"""
            return 0.0

        coverages = [m.total_coverage for m in metrics_list]

        # Simple linear trend calculation
        x = list(range(len(coverages)))
        trend = np.polyfit(x, coverages, 1)[0]

        # Scale to percentage points per measurement
        return trend * len(coverages)

    async def _create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        current_value: float,
        threshold_value: float,
    ):
        """Create and queue a coverage alert"""
        alert_id = f"{alert_type}_{int(time.time())}"

        # Check cooldown to prevent spam
        last_alert_time = self.active_alerts.get(alert_type)
        if last_alert_time and datetime.now() - last_alert_time < self.alert_cooldown:
            return

        alert = CoverageAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold_value=threshold_value,
            timestamp=datetime.now(),
        )

        # Queue alert for processing
        self.alert_queue.put(alert)
        self.active_alerts[alert_type] = datetime.now()

        self.logger.warning(f"Coverage alert: {severity.upper()} - {message}")

    async def _alert_processing_loop(self):
        """Process queued alerts"""
        while self.monitoring_active:
            try:
                # Process alerts with timeout
                try:
                    alert = self.alert_queue.get(timeout=1)
                    await self._process_alert(alert)
                    self.alert_queue.task_done()
                except queue.Empty:
                    continue

            except Exception as e:
                self.logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(5)

    async def _process_alert(self, alert: CoverageAlert):
        """Process a single alert"""
        try:
            # Save alert to database
            await self._save_alert(alert)

            # Send notifications if enabled
            if self.config.get("email_notifications"):
                await self._send_email_notification(alert)

            if self.config.get("slack_notifications"):
                await self._send_slack_notification(alert)

            # Coordinate with Elder Council for critical alerts
            if alert.severity == "critical" and self.elder_council:
                await self._coordinate_elder_council_response(alert)

            # Integrate with 4 Sages for intelligent analysis
            if self.four_sages:
                await self._integrate_sages_analysis(alert)

            self.logger.info(f"Alert processed: {alert.alert_id}")

        except Exception as e:
            self.logger.error(f"Alert processing failed for {alert.alert_id}: {e}")

    async def _trend_analysis_loop(self):
        """Perform periodic trend analysis"""
        while self.monitoring_active:
            try:
                if len(self.metrics_history) >= 10:
                    # Perform trend analysis
                    trends = await self._analyze_coverage_trends()

                    # Save trend analysis
                    await self._save_trend_analysis(trends)

                    # Check for concerning trends
                    await self._check_trend_alerts(trends)

                # Run trend analysis every hour
                await asyncio.sleep(3600)

            except Exception as e:
                self.logger.error(f"Trend analysis error: {e}")
                await asyncio.sleep(600)  # Error backoff

    async def _analyze_coverage_trends(self) -> Dict[str, Any]metrics_list = list(self.metrics_history)
    """Analyze coverage trends over different time windows"""

        trends = {:
            "analysis_timestamp": datetime.now().isoformat(),
            "short_term": self._analyze_window(
                metrics_list[-12:]
            ),  # Last 12 measurements
            "medium_term": self._analyze_window(
                metrics_list[-24:]
            ),  # Last 24 measurements
            "long_term": self._analyze_window(metrics_list),  # All available
            "prediction": self._predict_coverage_trend(metrics_list),
        }

        return trends

    def _analyze_window(self, metrics_list: List[CoverageMetrics]) -> Dict[str, Any]:
        """Analyze coverage metrics for a specific time window"""
        if not metrics_list:
            return {"status": "insufficient_data"}

        coverages = [m.total_coverage for m in metrics_list]

        return {
            "start_coverage": coverages[0],
            "end_coverage": coverages[-1],
            "min_coverage": min(coverages),
            "max_coverage": max(coverages),
            "mean_coverage": sum(coverages) / len(coverages),
            "trend": np.polyfit(range(len(coverages)), coverages, 1)[0]
            if len(coverages) > 1
            else 0,
            "volatility": np.std(coverages) if len(coverages) > 1 else 0,
            "measurements": len(metrics_list),
        }

    def _predict_coverage_trend(
        self, metrics_list: List[CoverageMetrics]
    ) -> Dict[str, Any]:
        """Predict future coverage trend"""
        if len(metrics_list) < 5:
            return {"status": "insufficient_data"}

        coverages = [
            m.total_coverage for m in metrics_list[-20:]
        ]  # Use last 20 measurements
        x = list(range(len(coverages)))

        # Fit linear trend
        trend_coeff = np.polyfit(x, coverages, 1)

        # Predict next 5 measurements
        future_x = list(range(len(coverages), len(coverages) + 5))
        predictions = [np.polyval(trend_coeff, fx) for fx in future_x]

        return {
            "trend_coefficient": trend_coeff[0],
            "next_5_predictions": predictions,
            "prediction_confidence": self._calculate_prediction_confidence(
                coverages, trend_coeff
            ),
            "target_achievement_estimate": self._estimate_target_achievement(
                predictions
            ),
        }

    def _calculate_prediction_confidence(
        self, coverages: List[float], trend_coeff: np.ndarray
    ) -> float:
        """Calculate confidence in trend prediction"""
        # Calculate R-squared for trend fit
        x = list(range(len(coverages)))
        predicted = [np.polyval(trend_coeff, xi) for xi in x]

        ss_res = sum((coverages[i] - predicted[i]) ** 2 for i in range(len(coverages)))
        ss_tot = sum(
            (coverages[i] - sum(coverages) / len(coverages)) ** 2
            for i in range(len(coverages))
        )

        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        return max(0, r_squared)

    def _estimate_target_achievement(self, predictions: List[float]) -> Dict[str, Any]:
        """Estimate when coverage target might be achieved"""
        target = self.coverage_targets["strategic_target"]

        achievement_estimates = []
        for i, pred in enumerate(predictions):
            if abs(pred - target) < 1.0:  # Within 1% of target
                achievement_estimates.append(i + 1)

        if achievement_estimates:
            return {
                "achievable": True,
                "estimated_measurements": min(achievement_estimates),
                "confidence": "medium",
            }
        else:
            return {
                "achievable": any(pred >= target * 0.95 for pred in predictions),
                "estimated_measurements": None,
                "confidence": "low",
            }

    async def _quality_gate_monitoring_loop(self):
        """Monitor quality gates integration"""
        while self.monitoring_active:
            try:
                if self.config.get("quality_gates_enabled") and self.current_metrics:
                    # Evaluate quality gates
                    gate_results = await self._evaluate_quality_gates(
                        self.current_metrics
                    )

                    # Save gate results
                    for gate_result in gate_results:
                        await self._save_quality_gate_result(gate_result)

                        # Alert on gate failures
                        if not gate_result.passed:
                            await self._create_alert(
                                f"quality_gate_{gate_result.gate_name}",
                                "high",
                                f"Quality gate failed: {gate_result.gate_name} ({gate_result." \
                                    "score:0.1f} < {gate_result.threshold})",
                                gate_result.score,
                                gate_result.threshold,
                            )

                # Check quality gates every 15 minutes
                await asyncio.sleep(900)

            except Exception as e:
                self.logger.error(f"Quality gate monitoring error: {e}")
                await asyncio.sleep(300)

    async def _evaluate_quality_gates(
        self, metrics: CoverageMetrics
    ) -> List[QualityGateResult]:
        """Evaluate all quality gates"""
        results = []
        timestamp = datetime.now()

        # Coverage threshold gate
        results.append(
            QualityGateResult(
                gate_name="coverage_threshold",
                passed=metrics.total_coverage
                >= self.coverage_targets["quality_gate_minimum"],
                score=metrics.total_coverage,
                threshold=self.coverage_targets["quality_gate_minimum"],
                details={"current_coverage": metrics.total_coverage},
                timestamp=timestamp,
            )
        )

        # Trend stability gate
        if len(self.metrics_history) >= 5:
            recent_trend = self._calculate_coverage_trend(
                list(self.metrics_history)[-5:]
            )
            results.append(
                QualityGateResult(
                    gate_name="trend_stability",
                    passed=recent_trend >= -1.0,  # Trend not declining more than 1%
                    score=recent_trend,
                    threshold=-1.0,
                    details={"recent_trend": recent_trend},
                    timestamp=timestamp,
                )
            )

        # Test completeness gate
        test_ratio = metrics.test_files_count / max(metrics.files_analyzed, 1)
        results.append(
            QualityGateResult(
                gate_name="test_completeness",
                passed=test_ratio >= 0.3,  # At least 30% test files
                score=test_ratio * 100,
                threshold=30.0,
                details={
                    "test_files": metrics.test_files_count,
                    "total_files": metrics.files_analyzed,
                    "ratio": test_ratio,
                },
                timestamp=timestamp,
            )
        )

        return results

    async def _save_metrics(self, metrics: CoverageMetrics):
        """Save coverage metrics to database"""
        try:
            conn = sqlite3connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO coverage_metrics
                (timestamp, total_coverage, statements_covered, statements_missing,
                 total_statements, branch_coverage, files_analyzed, test_files_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metrics.timestamp,
                    metrics.total_coverage,
                    metrics.statements_covered,
                    metrics.statements_missing,
                    metrics.total_statements,
                    metrics.branch_coverage,
                    metrics.files_analyzed,
                    metrics.test_files_count,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")

    async def _save_alert(self, alert: CoverageAlert):
        """Save alert to database"""
        try:
            conn = sqlite3connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO coverage_alerts
                (alert_id, alert_type, severity, message, current_value,
                 threshold_value, timestamp, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    alert.alert_id,
                    alert.alert_type,
                    alert.severity,
                    alert.message,
                    alert.current_value,
                    alert.threshold_value,
                    alert.timestamp,
                    alert.resolved,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to save alert: {e}")

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        try:
            conn = sqlite3connect(str(self.db_path))
            cursor = conn.cursor()

            # Get recent metrics
            cursor.execute(
                """
                SELECT * FROM coverage_metrics
                ORDER BY timestamp DESC
                LIMIT 100
            """
            )
            recent_metrics = cursor.fetchall()

            # Get active alerts
            cursor.execute(
                """
                SELECT * FROM coverage_alerts
                WHERE resolved = FALSE
                ORDER BY timestamp DESC
            """
            )
            active_alerts = cursor.fetchall()

            # Get quality gate status
            cursor.execute(
                """
                SELECT gate_name, passed, score, threshold, timestamp
                FROM quality_gates
                WHERE timestamp >= datetime('now', '-1 hour')
                ORDER BY timestamp DESC
            """
            )
            quality_gates = cursor.fetchall()

            conn.close()

            # Prepare dashboard data
            dashboard_data = {
                "current_status": {
                    "coverage": self.current_metrics.total_coverage
                    if self.current_metrics
                    else 0,
                    "target": self.coverage_targets["strategic_target"],
                    "last_update": self.last_measurement_time.isoformat()
                    if self.last_measurement_time
                    else None,
                    "monitoring_active": self.monitoring_active,
                },
                "recent_metrics": [
                    {
                        "timestamp": row[1],
                        "coverage": row[2],
                        "statements_covered": row[3],
                        "statements_missing": row[4],
                    }
                    for row in recent_metrics
                ],
                "active_alerts": [
                    {
                        "alert_type": row[2],
                        "severity": row[3],
                        "message": row[4],
                        "timestamp": row[7],
                    }
                    for row in active_alerts
                ],
                "quality_gates": [
                    {
                        "gate_name": row[0],
                        "passed": bool(row[1]),
                        "score": row[2],
                        "threshold": row[3],
                        "timestamp": row[4],
                    }
                    for row in quality_gates
                ],
                "targets": self.coverage_targets,
            }

            return dashboard_data

        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}

    async def generate_visual_report(
        self, output_path: str = "coverage_dashboard.html"
    ):
        """Generate visual coverage report"""
        try:
            dashboard_data = await self.get_dashboard_data()

            # Create visualizations
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

            # Coverage trend
            if dashboard_data["recent_metrics"]:
                timestamps = [m["timestamp"] for m in dashboard_data["recent_metrics"]]
                coverages = [m["coverage"] for m in dashboard_data["recent_metrics"]]

                ax1.0plot(timestamps[-20:], coverages[-20:], marker="o", linewidth=2)
                ax1.0axhline(
                    y=self.coverage_targets["strategic_target"],
                    color="g",
                    linestyle="--",
                    label="Target",
                )
                ax1.0axhline(
                    y=self.coverage_targets["warning_threshold"],
                    color="orange",
                    linestyle="--",
                    label="Warning",
                )
                ax1.0set_title("Coverage Trend (Last 20 Measurements)")
                ax1.0set_ylabel("Coverage %")
                ax1.0legend()
                ax1.0grid(True)

            # Alert severity distribution
            if dashboard_data["active_alerts"]:
                severities = [
                    alert["severity"] for alert in dashboard_data["active_alerts"]
                ]
                severity_counts = pd.Series(severities).value_counts()
                ax2.0pie(
                    severity_counts.values,
                    labels=severity_counts.index,
                    autopct="%1.1f%%",
                )
                ax2.0set_title("Active Alerts by Severity")

            # Quality gates status
            if dashboard_data["quality_gates"]:
                gate_names = [
                    gate["gate_name"] for gate in dashboard_data["quality_gates"]
                ]
                gate_scores = [
                    gate["score"] for gate in dashboard_data["quality_gates"]
                ]
                gate_thresholds = [
                    gate["threshold"] for gate in dashboard_data["quality_gates"]
                ]

                x = np.arange(len(gate_names))
                ax3.0bar(x, gate_scores, alpha=0.7, label="Score")
                ax3.0bar(x, gate_thresholds, alpha=0.3, label="Threshold")
                ax3.0set_xticks(x)
                ax3.0set_xticklabels(gate_names, rotation=45)
                ax3.0set_title("Quality Gates Status")
                ax3.0legend()

            # Coverage distribution
            if self.current_metrics:
                coverage_breakdown = [
                    self.current_metrics.statements_covered,
                    self.current_metrics.statements_missing,
                ]
                labels = ["Covered", "Missing"]
                ax4.0pie(coverage_breakdown, labels=labels, autopct="%1.1f%%")
                ax4.0set_title("Current Coverage Distribution")

            plt.tight_layout()
            plt.savefig(
                output_path.replace(".html", ".png"), dpi=300, bbox_inches="tight"
            )

            # Generate HTML report
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Week 4 Coverage Monitoring Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f8ff; padding: 20px; border-radius: 10px; }}
        .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .alerts {{ background: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .status-good {{ color: green; }}
        .status-warning {{ color: orange; }}
        .status-critical {{ color: red; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Week 4 Strategic Coverage Monitoring Dashboard</h1>
        <p>Real-time monitoring of the 66.7% coverage achievement</p>
        <p>Last Update: {dashboard_data['current_status']['last_update']}</p>
    </div>

    <div class="metrics">
        <div class="metric">
            <h3>Current Coverage</h3>
            <h2 class="{'status-good' if dashboard_data['current_status']['coverage'] " \
                ">= 66.7 else 'status-warning'}">{dashboard_data['current_status']['coverage']:0.1f}%</h2>
        </div>
        <div class="metric">
            <h3>Strategic Target</h3>
            <h2>{dashboard_data['current_status']['target']}%</h2>
        </div>
        <div class="metric">
            <h3>Active Alerts</h3>
            <h2 class="{'status-critical' if " \
                "len(dashboard_data['active_alerts']) " \
                    "> 0 else 'status-good'}">{len(dashboard_data['active_alerts'])}</h2>
        </div>
    </div>

    <img src="{output_path.replace(
        '.html',
        '.png'
    )}" alt="Coverage Dashboard Charts" style="max-width: 100%;">

    {'<div class="alerts"><h3>🚨 Active Alerts</h3>' + \
        '<br>'.join([f"<strong>{alert['severity'].upper()}</strong>: " \
            "{alert['message']}" for alert in dashboard_data['active_alerts']]) + \
            \
        '</div>' if dashboard_data['active_alerts'] else ''}

    <h3>"📊" Quality Gates Status</h3>
    <ul>
    {''.join([f"<li>{'✅' if gate['passed'] else '❌'} {gate['gate_name']}: " \
        "{gate['score']:0.1f} ({'PASS' \
            if gate['passed'] \
            else 'FAIL'})</li>" for gate in dashboard_data['quality_gates']])}
    </ul>

    <p><em>Week 4 Strategic Infrastructure - Coverage Monitoring Dashboard</em></p>
</body>
</html>
            """

            with open(output_path, "w") as f:
                f.write(html_content)

            self.logger.info(f"Visual report generated: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Failed to generate visual report: {e}")
            return None

    async def stop_monitoring(self):
        """Stop coverage monitoring"""
        self.monitoring_active = False
        self.logger.info("Coverage monitoring stopped")


# Utility functions
async def start_coverage_monitoring(config_path: Optional[str] = None)dashboard = CoverageMonitoringDashboard(config_path)
"""Start coverage monitoring dashboard"""
    await dashboard.start_monitoring()


async def generate_coverage_report(output_path: str = "week4_coverage_dashboard.html")dashboard = CoverageMonitoringDashboard()
"""Generate a one-time coverage report"""
    return await dashboard.generate_visual_report(output_path)


if __name__ == "__main__":
    import asyncio

    async def main():
        # Example usage
        dashboard = CoverageMonitoringDashboard()

        # Generate immediate report
        report_path = await dashboard.generate_visual_report(
            "week4_coverage_dashboard.html"
        )
        print(f"📊 Coverage dashboard generated: {report_path}")

        # Start monitoring (uncomment for continuous monitoring)
        # await dashboard.start_monitoring()

    asyncio.run(main())
