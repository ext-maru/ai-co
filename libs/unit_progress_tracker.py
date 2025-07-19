#!/usr/bin/env python3
"""
Unit Progress Tracker - 騎士団、ウィザーズ、ドワーフ工房の進捗追跡システム
Daily progress tracking for Knights, Wizards, and Dwarf Workshop
"""

import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class UnitActivity:
    """ユニットの活動記録"""

    timestamp: datetime
    unit_type: str  # knights, wizards, dwarf
    action_type: str  # detected, repaired, collected, optimized, etc.
    details: str
    metrics: Dict[str, Any]
    auto_generated: bool = False


@dataclass
class DailyProgress:
    """日次進捗レポート"""

    date: str
    knights: Dict[str, Any]
    wizards: Dict[str, Any]
    dwarf_workshop: Dict[str, Any]
    summary: Dict[str, Any]


class UnitProgressTracker:
    """ユニット進捗追跡システム"""

    def __init__(self):
        """初期化"""
        self.progress_dir = Path("knowledge_base/unit_progress")
        self.progress_dir.mkdir(parents=True, exist_ok=True)

        self.log_patterns = {
            "knights": {
                "detected": r"(?:Detected|Found|Identified)\s+(\d+)\s+(?:issues?|problems?|errors?)",
                "repaired": r"(?:Fixed|Repaired|Resolved|Restored)\s+(\d+)\s+(?:issues?|problems?|errors?)",
                "auto_action": r"(?:Automatically|Auto)\s+(?:created|fixed|restored)\s+(.+)",
            },
            "wizards": {
                "knowledge_gap": r"Knowledge gap detected:\s+(.+)",
                "enrichment": r"Enriched knowledge base with:\s+(.+)",
                "rag_query": r"RAG query processed:\s+(.+)",
                "idle_learning": r"Idle time learning:\s+(.+)",
            },
            "dwarf": {
                "optimization": r"Optimization opportunity:\s+(.+)",
                "tool_crafted": r"Crafted tool:\s+(.+)",
                "resource_saved": r"Resource saved:\s+(.+)",
                "monitoring": r"Monitoring:\s+CPU\s*(\d+)%.*Memory\s*(\d+)%",
            },
        }

    def analyze_logs(
        self, start_date: datetime, end_date: datetime
    ) -> List[UnitActivity]:
        """ログファイルから活動を分析"""
        activities = []

        # Analyze various log files
        log_files = [
            ("logs/incident_knights.log", "knights"),
            ("logs/rag_wizards_worker.log", "wizards"),
            ("logs/dwarf_workshop.log", "dwarf"),
            ("logs/worker_health_monitor.log", "all"),
            ("logs/ai_company.log", "all"),
        ]

        for log_file, unit_type in log_files:
            log_path = Path(log_file)
            if log_path.exists():
                activities.extend(
                    self._parse_log_file(log_path, unit_type, start_date, end_date)
                )

        # Also check for auto-generated activities from system monitoring
        activities.extend(self._detect_auto_activities(start_date, end_date))

        return sorted(activities, key=lambda x: x.timestamp)

    def _parse_log_file(
        self, log_path: Path, unit_type: str, start_date: datetime, end_date: datetime
    ) -> List[UnitActivity]:
        """ログファイルを解析"""
        activities = []

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    # Parse timestamp
                    timestamp_match = re.match(
                        r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", line
                    )
                    if not timestamp_match:
                        continue

                    timestamp = datetime.strptime(
                        timestamp_match.group(1), "%Y-%m-%d %H:%M:%S"
                    )

                    # Check if within date range
                    if not (start_date <= timestamp <= end_date):
                        continue

                    # Detect unit-specific patterns
                    if unit_type == "knights" or unit_type == "all":
                        activities.extend(
                            self._detect_knights_activity(line, timestamp)
                        )

                    if unit_type == "wizards" or unit_type == "all":
                        activities.extend(
                            self._detect_wizards_activity(line, timestamp)
                        )

                    if unit_type == "dwarf" or unit_type == "all":
                        activities.extend(self._detect_dwarf_activity(line, timestamp))

        except Exception as e:
            print(f"Error parsing {log_path}: {e}")

        return activities

    def _detect_knights_activity(
        self, line: str, timestamp: datetime
    ) -> List[UnitActivity]:
        """騎士団の活動を検出"""
        activities = []

        # Detect issues found
        match = re.search(self.log_patterns["knights"]["detected"], line, re.IGNORECASE)
        if match:
            count = int(match.group(1))
            activities.append(
                UnitActivity(
                    timestamp=timestamp,
                    unit_type="knights",
                    action_type="detected",
                    details=f"Detected {count} issues",
                    metrics={"count": count},
                    auto_generated=False,
                )
            )

        # Detect repairs
        match = re.search(self.log_patterns["knights"]["repaired"], line, re.IGNORECASE)
        if match:
            count = int(match.group(1))
            activities.append(
                UnitActivity(
                    timestamp=timestamp,
                    unit_type="knights",
                    action_type="repaired",
                    details=f"Repaired {count} issues",
                    metrics={"count": count},
                    auto_generated=False,
                )
            )

        # Detect auto actions
        match = re.search(
            self.log_patterns["knights"]["auto_action"], line, re.IGNORECASE
        )
        if match:
            action = match.group(1)
            activities.append(
                UnitActivity(
                    timestamp=timestamp,
                    unit_type="knights",
                    action_type="auto_action",
                    details=f"Auto action: {action}",
                    metrics={"action": action},
                    auto_generated=True,
                )
            )

        return activities

    def _detect_wizards_activity(
        self, line: str, timestamp: datetime
    ) -> List[UnitActivity]:
        """ウィザーズの活動を検出"""
        activities = []

        # Detect knowledge gaps
        match = re.search(
            self.log_patterns["wizards"]["knowledge_gap"], line, re.IGNORECASE
        )
        if match:
            gap = match.group(1)
            activities.append(
                UnitActivity(
                    timestamp=timestamp,
                    unit_type="wizards",
                    action_type="knowledge_gap",
                    details=f"Knowledge gap: {gap}",
                    metrics={"gap": gap},
                    auto_generated=False,
                )
            )

        # Detect enrichment
        match = re.search(
            self.log_patterns["wizards"]["enrichment"], line, re.IGNORECASE
        )
        if match:
            enrichment = match.group(1)
            activities.append(
                UnitActivity(
                    timestamp=timestamp,
                    unit_type="wizards",
                    action_type="enrichment",
                    details=f"Enriched: {enrichment}",
                    metrics={"enrichment": enrichment},
                    auto_generated=False,
                )
            )

        return activities

    def _detect_dwarf_activity(
        self, line: str, timestamp: datetime
    ) -> List[UnitActivity]:
        """ドワーフ工房の活動を検出"""
        activities = []

        # Detect optimization opportunities
        match = re.search(
            self.log_patterns["dwarf"]["optimization"], line, re.IGNORECASE
        )
        if match:
            opportunity = match.group(1)
            activities.append(
                UnitActivity(
                    timestamp=timestamp,
                    unit_type="dwarf",
                    action_type="optimization",
                    details=f"Optimization: {opportunity}",
                    metrics={"opportunity": opportunity},
                    auto_generated=False,
                )
            )

        # Detect resource monitoring
        match = re.search(self.log_patterns["dwarf"]["monitoring"], line)
        if match:
            cpu = int(match.group(1))
            memory = int(match.group(2))
            activities.append(
                UnitActivity(
                    timestamp=timestamp,
                    unit_type="dwarf",
                    action_type="monitoring",
                    details=f"Resource monitoring: CPU {cpu}%, Memory {memory}%",
                    metrics={"cpu": cpu, "memory": memory},
                    auto_generated=True,
                )
            )

        return activities

    def _detect_auto_activities(
        self, start_date: datetime, end_date: datetime
    ) -> List[UnitActivity]:
        """自動生成された活動を検出"""
        activities = []

        # Check for automatic module creation, worker restarts, etc.
        # This would analyze system state changes and infer activities

        return activities

    def generate_daily_report(self, date: datetime) -> DailyProgress:
        """日次進捗レポートを生成"""
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        # Analyze activities for the day
        activities = self.analyze_logs(start_date, end_date)

        # Aggregate by unit type
        knights_stats = self._aggregate_unit_stats(activities, "knights")
        wizards_stats = self._aggregate_unit_stats(activities, "wizards")
        dwarf_stats = self._aggregate_unit_stats(activities, "dwarf")

        # Calculate summary statistics
        summary = {
            "total_activities": len(activities),
            "auto_generated_count": sum(1 for a in activities if a.auto_generated),
            "knights_efficiency": self._calculate_efficiency(knights_stats),
            "wizards_productivity": self._calculate_productivity(wizards_stats),
            "dwarf_optimization_rate": self._calculate_optimization_rate(dwarf_stats),
            "overall_health": self._calculate_overall_health(
                knights_stats, wizards_stats, dwarf_stats
            ),
        }

        report = DailyProgress(
            date=date.strftime("%Y-%m-%d"),
            knights=knights_stats,
            wizards=wizards_stats,
            dwarf_workshop=dwarf_stats,
            summary=summary,
        )

        # Save report
        self._save_report(report)

        return report

    def _aggregate_unit_stats(
        self, activities: List[UnitActivity], unit_type: str
    ) -> Dict[str, Any]:
        """ユニット別の統計を集計"""
        unit_activities = [a for a in activities if a.unit_type == unit_type]

        stats = {
            "total_activities": len(unit_activities),
            "auto_generated": sum(1 for a in unit_activities if a.auto_generated),
            "by_action": defaultdict(int),
            "metrics": defaultdict(list),
        }

        for activity in unit_activities:
            stats["by_action"][activity.action_type] += 1
            for key, value in activity.metrics.items():
                if isinstance(value, (int, float)):
                    stats["metrics"][key].append(value)

        # Calculate averages for numeric metrics
        for key, values in stats["metrics"].items():
            if values:
                stats["metrics"][key] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "total": sum(values),
                }

        return dict(stats)

    def _calculate_efficiency(self, knights_stats: Dict[str, Any]) -> float:
        """騎士団の効率を計算"""
        detected = knights_stats["by_action"].get("detected", 0)
        repaired = knights_stats["by_action"].get("repaired", 0)

        if detected == 0:
            return 100.0  # No issues detected means 100% efficiency

        return (repaired / detected) * 100 if detected > 0 else 0

    def _calculate_productivity(self, wizards_stats: Dict[str, Any]) -> float:
        """ウィザーズの生産性を計算"""
        enrichments = wizards_stats["by_action"].get("enrichment", 0)
        gaps = wizards_stats["by_action"].get("knowledge_gap", 0)

        # Base productivity on enrichments and gap filling
        return (enrichments + gaps) * 10  # Arbitrary scaling factor

    def _calculate_optimization_rate(self, dwarf_stats: Dict[str, Any]) -> float:
        """ドワーフ工房の最適化率を計算"""
        optimizations = dwarf_stats["by_action"].get("optimization", 0)
        monitoring = dwarf_stats["by_action"].get("monitoring", 0)

        if monitoring == 0:
            return 0

        return (optimizations / monitoring) * 100

    def _calculate_overall_health(
        self, knights: Dict, wizards: Dict, dwarf: Dict
    ) -> float:
        """全体的な健康度を計算"""
        # Weighted average of unit performances
        knights_weight = 0.4
        wizards_weight = 0.3
        dwarf_weight = 0.3

        knights_score = self._calculate_efficiency(knights) / 100
        wizards_score = min(self._calculate_productivity(wizards) / 100, 1.0)
        dwarf_score = self._calculate_optimization_rate(dwarf) / 100

        return (
            knights_score * knights_weight
            + wizards_score * wizards_weight
            + dwarf_score * dwarf_weight
        ) * 100

    def _save_report(self, report: DailyProgress):
        """レポートを保存"""
        # Save as JSON
        json_path = self.progress_dir / f"daily_progress_{report.date}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2, default=str)

        # Save as Markdown
        md_path = self.progress_dir / f"daily_progress_{report.date}.md"
        md_content = self._generate_markdown_report(report)
        md_path.write_text(md_content, encoding="utf-8")

    def _generate_markdown_report(self, report: DailyProgress) -> str:
        """Markdownレポートを生成"""
        return f"""# 🏰 Unit Progress Report - {report.date}

## 📊 Executive Summary
- **Total Activities**: {report.summary['total_activities']}
- **Auto-Generated**: {report.summary['auto_generated_count']}
- **Overall Health**: {report.summary['overall_health']:.1f}%

## ⚔️ Knights (騎士団)
- **Activities**: {report.knights['total_activities']}
- **Efficiency**: {report.summary['knights_efficiency']:.1f}%
- **Actions**:
  - Detected: {report.knights['by_action'].get('detected', 0)}
  - Repaired: {report.knights['by_action'].get('repaired', 0)}
  - Auto Actions: {report.knights['by_action'].get('auto_action', 0)}

## 🧙‍♂️ Wizards (ウィザーズ)
- **Activities**: {report.wizards['total_activities']}
- **Productivity**: {report.summary['wizards_productivity']:.1f}
- **Actions**:
  - Knowledge Gaps: {report.wizards['by_action'].get('knowledge_gap', 0)}
  - Enrichments: {report.wizards['by_action'].get('enrichment', 0)}

## 🔨 Dwarf Workshop (ドワーフ工房)
- **Activities**: {report.dwarf_workshop['total_activities']}
- **Optimization Rate**: {report.summary['dwarf_optimization_rate']:.1f}%
- **Actions**:
  - Optimizations: {report.dwarf_workshop['by_action'].get('optimization', 0)}
  - Monitoring: {report.dwarf_workshop['by_action'].get('monitoring', 0)}

---
Generated: {datetime.now().isoformat()}
"""


def main():
    """メイン関数 - 日次レポート生成"""
    tracker = UnitProgressTracker()

    # Generate report for today
    today = datetime.now()
    report = tracker.generate_daily_report(today)

    print(f"✅ Daily progress report generated for {report.date}")
    print(f"📊 Overall health: {report.summary['overall_health']:.1f}%")
    print(
        f"📁 Report saved to: knowledge_base/unit_progress/daily_progress_{report.date}.md"
    )


if __name__ == "__main__":
    main()
