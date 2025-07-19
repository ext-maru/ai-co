#!/usr/bin/env python3
"""
Coverage Trend Monitoring System
Part of Week 4 Strategic Infrastructure
"""

import datetime
import json
import sqlite3
from pathlib import Path
from typing import Dict
from typing import List

import matplotlib.pyplot as plt
import pandas as pd


class CoverageTrendMonitor:
    """Monitor and analyze coverage trends over time"""

    def __init__(self, db_path: str = "data/coverage_trends.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the coverage trends database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coverage_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_coverage REAL NOT NULL,
                    unit_coverage REAL,
                    integration_coverage REAL,
                    generated_coverage REAL,
                    lines_covered INTEGER,
                    lines_total INTEGER,
                    branches_covered INTEGER,
                    branches_total INTEGER,
                    commit_hash TEXT,
                    branch_name TEXT,
                    pipeline_run_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coverage_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    coverage_drop REAL,
                    threshold REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_coverage_timestamp
                ON coverage_metrics(timestamp)
            """
            )

    def record_coverage(self, coverage_data: Dict) -> None:
        """Record coverage metrics to the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO coverage_metrics (
                    timestamp, total_coverage, unit_coverage, integration_coverage,
                    generated_coverage, lines_covered, lines_total, branches_covered,
                    branches_total, commit_hash, branch_name, pipeline_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    coverage_data.get("timestamp", datetime.datetime.now().isoformat()),
                    coverage_data.get("total_coverage", 0),
                    coverage_data.get("unit_coverage", 0),
                    coverage_data.get("integration_coverage", 0),
                    coverage_data.get("generated_coverage", 0),
                    coverage_data.get("lines_covered", 0),
                    coverage_data.get("lines_total", 0),
                    coverage_data.get("branches_covered", 0),
                    coverage_data.get("branches_total", 0),
                    coverage_data.get("commit_hash", ""),
                    coverage_data.get("branch_name", ""),
                    coverage_data.get("pipeline_run_id", ""),
                ),
            )

    def get_trend_data(self, days: int = 30) -> pd.DataFrame:
        """Get coverage trend data for the specified number of days"""
        cutoff_date = (
            datetime.datetime.now() - datetime.timedelta(days=days)
        ).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(
                """
                SELECT timestamp, total_coverage, unit_coverage,
                       integration_coverage, generated_coverage,
                       lines_covered, lines_total, branch_name
                FROM coverage_metrics
                WHERE timestamp > ?
                ORDER BY timestamp ASC
            """,
                conn,
                params=(cutoff_date,),
            )

        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        return df

    def analyze_trends(self, days: int = 30) -> Dict:
        """Analyze coverage trends and detect significant changes"""
        df = self.get_trend_data(days)

        if df.empty:
            return {"status": "no_data", "message": "No coverage data available"}

        # Calculate trend metrics
        latest_coverage = df["total_coverage"].iloc[-1]
        earliest_coverage = df["total_coverage"].iloc[0]
        coverage_change = latest_coverage - earliest_coverage

        # Calculate moving averages
        df["ma_7"] = df["total_coverage"].rolling(window=7, min_periods=1).mean()
        df["ma_14"] = df["total_coverage"].rolling(window=14, min_periods=1).mean()

        # Detect significant drops (>5% in single day)
        df["daily_change"] = df["total_coverage"].diff()
        significant_drops = df[df["daily_change"] < -5.0]

        # Calculate volatility
        volatility = df["total_coverage"].std()

        return {
            "status": "analyzed",
            "period_days": days,
            "latest_coverage": latest_coverage,
            "coverage_change": coverage_change,
            "trend": (
                "increasing"
                if coverage_change > 1
                else "decreasing" if coverage_change < -1 else "stable"
            ),
            "volatility": volatility,
            "significant_drops": len(significant_drops),
            "data_points": len(df),
            "ma_7_latest": df["ma_7"].iloc[-1] if not df.empty else 0,
            "ma_14_latest": df["ma_14"].iloc[-1] if not df.empty else 0,
        }

    def check_coverage_alerts(
        self, current_coverage: float, threshold: float = 66.7
    ) -> List[Dict]:
        """Check for coverage alerts and record them"""
        alerts = []

        # Get recent coverage data
        df = self.get_trend_data(days=7)

        if not df.empty:
            recent_avg = df["total_coverage"].tail(3).mean()
            coverage_drop = recent_avg - current_coverage

            # Alert if coverage drops below threshold
            if current_coverage < threshold:
                alert = {
                    "type": "threshold_breach",
                    "severity": "high",
                    "message": f"Coverage {current_coverage:.1f}% below threshold {threshold}%",
                    "coverage_drop": threshold - current_coverage,
                    "threshold": threshold,
                }
                alerts.append(alert)
                self._record_alert(alert)

            # Alert if significant drop from recent average
            if coverage_drop > 5.0:
                alert = {
                    "type": "significant_drop",
                    "severity": "medium",
                    "message": f"Coverage dropped {coverage_drop:.1f}% from recent average",
                    "coverage_drop": coverage_drop,
                    "threshold": recent_avg,
                }
                alerts.append(alert)
                self._record_alert(alert)

        return alerts

    def _record_alert(self, alert: Dict) -> None:
        """Record an alert to the database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO coverage_alerts (
                    timestamp, alert_type, message, severity,
                    coverage_drop, threshold
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.datetime.now().isoformat(),
                    alert.get("type", "unknown"),
                    alert["message"],
                    alert["severity"],
                    alert.get("coverage_drop", 0),
                    alert.get("threshold", 0),
                ),
            )

    def generate_trend_chart(
        self, output_path: str = "reports/coverage_trend.png", days: int = 30
    ) -> bool:
        """Generate a coverage trend chart"""
        try:
            df = self.get_trend_data(days)

            if df.empty:
                print("No data available for trend chart")
                return False

            plt.figure(figsize=(12, 6))
            plt.plot(
                df["timestamp"],
                df["total_coverage"],
                "b-",
                label="Total Coverage",
                linewidth=2,
            )

            if "unit_coverage" in df.columns:
                plt.plot(
                    df["timestamp"],
                    df["unit_coverage"],
                    "g--",
                    label="Unit Tests",
                    alpha=0.7,
                )
            if "integration_coverage" in df.columns:
                plt.plot(
                    df["timestamp"],
                    df["integration_coverage"],
                    "r--",
                    label="Integration Tests",
                    alpha=0.7,
                )
            if "generated_coverage" in df.columns:
                plt.plot(
                    df["timestamp"],
                    df["generated_coverage"],
                    "orange",
                    linestyle="--",
                    label="Generated Tests",
                    alpha=0.7,
                )

            # Add 66.7% target line
            plt.axhline(
                y=66.7, color="red", linestyle=":", alpha=0.5, label="Target (66.7%)"
            )

            plt.title(f"Coverage Trends - Last {days} Days")
            plt.xlabel("Date")
            plt.ylabel("Coverage Percentage")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            Path(output_path).parent.mkdir(exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()

            return True

        except Exception as e:
            print(f"Error generating trend chart: {e}")
            return False

    def generate_report(
        self, output_path: str = "reports/coverage_trend_report.json"
    ) -> Dict:
        """Generate comprehensive coverage trend report"""
        analysis = self.analyze_trends()

        # Get recent alerts
        with sqlite3.connect(self.db_path) as conn:
            recent_alerts = pd.read_sql_query(
                """
                SELECT alert_type, message, severity, created_at
                FROM coverage_alerts
                WHERE created_at > datetime('now', '-7 days')
                ORDER BY created_at DESC
                LIMIT 10
            """,
                conn,
            )

        report = {
            "generated_at": datetime.datetime.now().isoformat(),
            "trend_analysis": analysis,
            "recent_alerts": (
                recent_alerts.to_dict("records") if not recent_alerts.empty else []
            ),
            "chart_generated": self.generate_trend_chart(),
            "recommendations": self._generate_recommendations(analysis),
        }

        # Save report
        Path(output_path).parent.mkdir(exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on trend analysis"""
        recommendations = []

        if analysis.get("latest_coverage", 0) < 66.7:
            recommendations.append(
                "Coverage below 66.7% target - prioritize test generation"
            )

        if analysis.get("trend") == "decreasing":
            recommendations.append("Coverage trending downward - review recent changes")

        if analysis.get("volatility", 0) > 10:
            recommendations.append(
                "High coverage volatility - stabilize test infrastructure"
            )

        if analysis.get("significant_drops", 0) > 0:
            recommendations.append(
                "Recent significant drops detected - investigate causes"
            )

        if not recommendations:
            recommendations.append(
                "Coverage trends are healthy - maintain current practices"
            )

        return recommendations


def main():
    """CLI interface for coverage trend monitoring"""
    import argparse

    parser = argparse.ArgumentParser(description="Coverage Trend Monitoring")
    parser.add_argument("--record", help="Record coverage from JSON file")
    parser.add_argument("--analyze", action="store_true", help="Analyze trends")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--chart", action="store_true", help="Generate trend chart")
    parser.add_argument("--days", type=int, default=30, help="Days to analyze")
    parser.add_argument("--output", help="Output path for reports")

    args = parser.parse_args()

    monitor = CoverageTrendMonitor()

    if args.record:
        with open(args.record) as f:
            coverage_data = json.load(f)
        monitor.record_coverage(coverage_data)
        print(f"✅ Coverage data recorded from {args.record}")

    if args.analyze:
        analysis = monitor.analyze_trends(args.days)
        print(f"📊 Coverage Analysis (last {args.days} days):")
        print(json.dumps(analysis, indent=2))

    if args.chart:
        output = args.output or "reports/coverage_trend.png"
        if monitor.generate_trend_chart(output, args.days):
            print(f"📈 Trend chart generated: {output}")
        else:
            print("❌ Failed to generate trend chart")

    if args.report:
        output = args.output or "reports/coverage_trend_report.json"
        report = monitor.generate_report(output)
        print(f"📋 Trend report generated: {output}")
        print(
            f"Latest coverage: {report['trend_analysis'].get('latest_coverage', 'N/A')}%"
        )


if __name__ == "__main__":
    main()
