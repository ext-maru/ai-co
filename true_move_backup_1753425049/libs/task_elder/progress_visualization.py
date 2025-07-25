#!/usr/bin/env python3
"""
"📊" 進捗追跡・可視化システム
Progress Tracking and Visualization System

計画書とプロジェクトの進捗を追跡し、可視化レポートを生成する
"""

import asyncio
import base64
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from task_elder.github_projects_client import GitHubProjectsClient
from task_elder.plan_projects_sync import PlanProjectsSync
from task_elder.project_board_manager import ProjectBoardManager

logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """可視化タイプ"""

    PROGRESS_CHART = "progress_chart"
    BURNDOWN_CHART = "burndown_chart"
    VELOCITY_CHART = "velocity_chart"
    STATUS_DISTRIBUTION = "status_distribution"
    PRIORITY_ANALYSIS = "priority_analysis"
    TIMELINE_GANTT = "timeline_gantt"
    HEALTH_DASHBOARD = "health_dashboard"


class ReportFormat(Enum):
    """レポート形式"""

    HTML = "html"
    JSON = "json"
    PDF = "pdf"
    MARKDOWN = "markdown"


@dataclass
class ProgressMetrics:
    """進捗メトリクス"""

    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    todo_tasks: int
    blocked_tasks: int
    completion_rate: float
    velocity: float
    estimated_completion: Optional[str] = None

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.total_tasks > 0:
            self.completion_rate = (self.completed_tasks / self.total_tasks) * 100
        else:
            self.completion_rate = 0.0


@dataclass
class ProjectHealth:
    """プロジェクト健全性"""

    health_score: float
    risk_level: str
    issues: List[str]
    recommendations: List[str]
    last_updated: str

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


@dataclass
class VisualizationConfig:
    """可視化設定"""

    chart_style: str = "seaborn"
    color_scheme: str = "viridis"
    font_size: int = 10
    figure_size: Tuple[int, int] = (12, 8)
    dpi: int = 300
    include_grid: bool = True
    show_trends: bool = True


class ProgressVisualization:
    """進捗追跡・可視化システム"""

    def __init__(self, github_token: Optional[str] = None)self.base_path = Path("/home/aicompany/ai_co")
    """初期化メソッド"""
        self.data_path = self.base_path / "data" / "progress_tracking"
        self.reports_path = self.base_path / "reports" / "progress"
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.reports_path.mkdir(parents=True, exist_ok=True)

        # コンポーネント
        self.board_manager = ProjectBoardManager(github_token)
        self.sync_system = PlanProjectsSync(github_token)
        self.github_client = GitHubProjectsClient(github_token)

        # 可視化設定
        self.viz_config = VisualizationConfig()

        # データストレージ
        self.metrics_history_file = self.data_path / "metrics_history.json"
        self.health_history_file = self.data_path / "health_history.json"

        # 履歴データ
        self.metrics_history = self._load_metrics_history()
        self.health_history = self._load_health_history()

        # Matplotlib設定
        plt.style.use(self.viz_config.chart_style)
        sns.set_palette(self.viz_config.color_scheme)

        # 統計
        self.stats = {
            "total_visualizations": 0,
            "reports_generated": 0,
            "last_update": None,
            "tracked_projects": 0,
        }

    def _load_metrics_history(self) -> List[Dict]if not self.metrics_history_file.exists():
    """メトリクス履歴を読み込み"""
            return []

        try:
            with open(self.metrics_history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"メトリクス履歴読み込みエラー: {e}")
            return []

    def _save_metrics_history(self):
        """メトリクス履歴を保存"""
        try:
            with open(self.metrics_history_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"メトリクス履歴保存エラー: {e}")

    def _load_health_history(self) -> List[Dict]if not self.health_history_file.exists():
    """健全性履歴を読み込み"""
            return []

        try:
            with open(self.health_history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"健全性履歴読み込みエラー: {e}")
            return []

    def _save_health_history(self):
        """健全性履歴を保存"""
        try:
            with open(self.health_history_file, "w", encoding="utf-8") as f:
                json.dump(self.health_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"健全性履歴保存エラー: {e}")

    async def collect_project_metrics(self, project_id: str) -> ProgressMetrics:
        """プロジェクトメトリクスを収集"""
        try:
            # プロジェクトの概要を取得
            progress = await self.board_manager.get_board_progress(project_id)

            if "error" in progress:
                logger.error(f"プロジェクト進捗取得エラー: {progress['error']}")
                return ProgressMetrics(0, 0, 0, 0, 0, 0.0, 0.0)

            status_breakdown = progress.get("status_breakdown", {})

            # ベロシティを計算（簡易版）
            velocity = self._calculate_velocity(project_id)

            # 完了予定日を推定
            estimated_completion = self._estimate_completion_date(
                status_breakdown.get("todo", 0)
                + status_breakdown.get("in_progress", 0),
                velocity,
            )

            metrics = ProgressMetrics(
                total_tasks=progress.get("total_items", 0),
                completed_tasks=status_breakdown.get("completed", 0),
                in_progress_tasks=status_breakdown.get("in_progress", 0),
                todo_tasks=status_breakdown.get("todo", 0),
                blocked_tasks=status_breakdown.get("blocked", 0),
                completion_rate=progress.get("progress_rate", 0.0),
                velocity=velocity,
                estimated_completion=estimated_completion,
            )

            return metrics

        except Exception as e:
            logger.error(f"メトリクス収集エラー: {e}")
            return ProgressMetrics(0, 0, 0, 0, 0, 0.0, 0.0)

    def _calculate_velocity(self, project_id: str) -> float:
        """ベロシティを計算"""
        # 過去7日間の完了タスク数を基準に計算
        recent_metrics = [
            m
            for m in self.metrics_history
            if m.get("project_id") == project_id
            and datetime.fromisoformat(m.get("timestamp", "2000-01-01"))
            > datetime.now() - timedelta(days=7)
        ]

        if len(recent_metrics) < 2:
            return 0.0

        # 完了タスク数の変化を計算
        recent_metrics.sort(key=lambda x: x.get("timestamp", ""))
        first_completed = recent_metrics[0].get("metrics", {}).get("completed_tasks", 0)
        last_completed = recent_metrics[-1].get("metrics", {}).get("completed_tasks", 0)

        days_diff = (
            datetime.fromisoformat(recent_metrics[-1]["timestamp"])
            - datetime.fromisoformat(recent_metrics[0]["timestamp"])
        ).days

        if days_diff > 0:
            return (last_completed - first_completed) / days_diff

        return 0.0

    def _estimate_completion_date(
        self, remaining_tasks: int, velocity: float
    ) -> Optional[str]:
        """完了予定日を推定"""
        if velocity <= 0 or remaining_tasks <= 0:
            return None

        days_to_complete = remaining_tasks / velocity
        completion_date = datetime.now() + timedelta(days=days_to_complete)

        return completion_date.isoformat()

    async def analyze_project_health(self, project_id: str) -> ProjectHealth:
        """プロジェクトの健全性を分析"""
        try:
            # 現在のメトリクスを取得
            metrics = await self.collect_project_metrics(project_id)

            # 健全性スコアを計算
            health_score = self._calculate_health_score(metrics)

            # リスクレベルを判定
            risk_level = self._determine_risk_level(health_score, metrics)

            # 問題点を特定
            issues = self._identify_issues(metrics)

            # 推奨事項を生成
            recommendations = self._generate_recommendations(metrics, issues)

            health = ProjectHealth(
                health_score=health_score,
                risk_level=risk_level,
                issues=issues,
                recommendations=recommendations,
                last_updated=datetime.now().isoformat(),
            )

            return health

        except Exception as e:
            logger.error(f"健全性分析エラー: {e}")
            return ProjectHealth(
                health_score=0.0,
                risk_level="不明",
                issues=["分析エラー"],
                recommendations=["システム管理者に連絡してください"],
                last_updated=datetime.now().isoformat(),
            )

    def _calculate_health_score(self, metrics: ProgressMetrics) -> float:
        """健全性スコアを計算"""
        score = 100.0

        # 進捗率による評価
        if metrics.completion_rate < 20:
            score -= 20
        elif metrics.completion_rate < 50:
            score -= 10

        # ブロックされたタスクの影響
        if metrics.total_tasks > 0:
            blocked_ratio = metrics.blocked_tasks / metrics.total_tasks
            score -= blocked_ratio * 30

        # ベロシティの影響
        if metrics.velocity < 0.5:
            score -= 15
        elif metrics.velocity < 1.0:
            score -= 10

        # 進行中タスクの過多
        if metrics.total_tasks > 0:
            in_progress_ratio = metrics.in_progress_tasks / metrics.total_tasks
            if in_progress_ratio > 0.5:
                score -= 10

        return max(0.0, min(100.0, score))

    def _determine_risk_level(
        self, health_score: float, metrics: ProgressMetrics
    ) -> str:
        """リスクレベルを判定"""
        if health_score >= 80:
            return "低"
        elif health_score >= 60:
            return "中"
        elif health_score >= 40:
            return "高"
        else:
            return "危険"

    def _identify_issues(self, metrics: ProgressMetrics) -> List[str]:
        """問題点を特定"""
        issues = []

        if metrics.completion_rate < 20:
            issues.append("進捗率が低い（20%未満）")

        if metrics.blocked_tasks > 0:
            issues.append(f"ブロックされたタスクが{metrics.blocked_tasks}件存在")

        if metrics.velocity < 0.5:
            issues.append("ベロシティが低い（0.5未満）")

        if metrics.total_tasks > 0:
            in_progress_ratio = metrics.in_progress_tasks / metrics.total_tasks
            if in_progress_ratio > 0.5:
                issues.append("進行中タスクが多すぎる（50%超）")

        return issues

    def _generate_recommendations(
        self, metrics: ProgressMetrics, issues: List[str]
    ) -> List[str]:
        """推奨事項を生成"""
        recommendations = []

        if "進捗率が低い" in str(issues):
            recommendations.append("タスクの優先度を見直し、重要なタスクに集中する")

        if "ブロックされたタスク" in str(issues):
            recommendations.append("ブロックされたタスクの解決策を検討する")

        if "ベロシティが低い" in str(issues):
            recommendations.append("チームのリソース配分を見直す")

        if "進行中タスクが多すぎる" in str(issues):
            recommendations.append("WIP（Work In Progress）制限を設ける")

        if not recommendations:
            recommendations.append("現在の進捗は良好です")

        return recommendations

    async def generate_progress_chart(self, project_id: str) -> str:
        """進捗チャートを生成"""
        try:
            # プロジェクトの履歴データを取得
            project_history = [
                m for m in self.metrics_history if m.get("project_id") == project_id
            ]

            if not project_history:
                logger.warning(f"プロジェクト履歴がありません: {project_id}")
                return ""

            # データを準備
            dates = [datetime.fromisoformat(m["timestamp"]) for m in project_history]
            completion_rates = [
                m["metrics"]["completion_rate"] for m in project_history
            ]

            # チャートを作成
            fig, ax = plt.subplots(figsize=self.viz_config.figure_size)

            ax.plot(dates, completion_rates, marker="o", linewidth=2, markersize=6)
            ax.set_title(
                f"プロジェクト進捗推移 (ID: {project_id})",
                fontsize=self.viz_config.font_size + 2,
            )
            ax.set_xlabel("日付", fontsize=self.viz_config.font_size)
            ax.set_ylabel("完了率 (%)", fontsize=self.viz_config.font_size)
            ax.grid(self.viz_config.include_grid, alpha=0.3)

            # 日付の形式を設定
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            ax.xaxis.set_major_locator(
                mdates.DayLocator(interval=max(1, len(dates) // 10))
            )
            plt.xticks(rotation=45)

            # Y軸の範囲を設定
            ax.set_ylim(0, 100)

            # レイアウトを調整
            plt.tight_layout()

            # ファイルに保存
            chart_filename = f"progress_chart_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            chart_path = self.reports_path / chart_filename

            plt.savefig(chart_path, dpi=self.viz_config.dpi, bbox_inches="tight")
            plt.close()

            self.stats["total_visualizations"] += 1
            logger.info(f"進捗チャート生成完了: {chart_path}")

            return str(chart_path)

        except Exception as e:
            logger.error(f"進捗チャート生成エラー: {e}")
            return ""

    async def generate_status_distribution(self, project_id: str) -> str:
        """ステータス分布チャートを生成"""
        try:
            # 最新のメトリクスを取得
            metrics = await self.collect_project_metrics(project_id)

            # データを準備
            labels = ["完了", "進行中", "Todo", "ブロック"]
            sizes = [
                metrics.completed_tasks,
                metrics.in_progress_tasks,
                metrics.todo_tasks,
                metrics.blocked_tasks,
            ]

            # 空のカテゴリを除外
            filtered_data = [
                (label, size) for label, size in zip(labels, sizes) if size > 0
            ]
            if not filtered_data:
                logger.warning(f"表示するデータがありません: {project_id}")
                return ""

            labels, sizes = zip(*filtered_data)

            # 色を設定
            colors = ["#28a745", "#ffc107", "#6c757d", "#dc3545"][: len(labels)]

            # 円グラフを作成
            fig, ax = plt.subplots(figsize=self.viz_config.figure_size)

            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90
            )

            ax.set_title(
                f"タスクステータス分布 (ID: {project_id})",
                fontsize=self.viz_config.font_size + 2,
            )

            # テキストの設定
            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontweight("bold")

            # ファイルに保存
            chart_filename = f"status_distribution_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            chart_path = self.reports_path / chart_filename

            plt.savefig(chart_path, dpi=self.viz_config.dpi, bbox_inches="tight")
            plt.close()

            self.stats["total_visualizations"] += 1
            logger.info(f"ステータス分布チャート生成完了: {chart_path}")

            return str(chart_path)

        except Exception as e:
            logger.error(f"ステータス分布チャート生成エラー: {e}")
            return ""

    async def generate_comprehensive_report(
        self, project_id: str, format_type: ReportFormat = ReportFormat.HTML
    ) -> str:
        """包括的レポートを生成"""
        try:
            # データを収集
            metrics = await self.collect_project_metrics(project_id)
            health = await self.analyze_project_health(project_id)

            # チャートを生成
            progress_chart = await self.generate_progress_chart(project_id)
            status_chart = await self.generate_status_distribution(project_id)

            # レポートデータを準備
            report_data = {
                "project_id": project_id,
                "generated_at": datetime.now().isoformat(),
                "metrics": asdict(metrics),
                "health": asdict(health),
                "charts": {
                    "progress_chart": progress_chart,
                    "status_distribution": status_chart,
                },
            }

            # フォーマットに応じてレポートを生成
            if format_type == ReportFormat.HTML:
                return await self._generate_html_report(report_data)
            elif format_type == ReportFormat.JSON:
                return await self._generate_json_report(report_data)
            elif format_type == ReportFormat.MARKDOWN:
                return await self._generate_markdown_report(report_data)
            else:
                logger.warning(f"未対応のフォーマット: {format_type}")
                return await self._generate_json_report(report_data)

        except Exception as e:
            logger.error(f"包括的レポート生成エラー: {e}")
            return ""

    async def _generate_html_report(self, report_data: Dict) -> str:
        """HTMLレポートを生成"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>プロジェクト進捗レポート</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .metrics { display: flex; gap: 20px; margin: 20px 0; }
                .metric-card { background-color: #e9ecef; padding: 15px; border-radius: 5px; flex: 1; }
                .health-score { font-size: 24px; font-weight: bold; }
                .health-low { color: #28a745; }
                .health-medium { color: #ffc107; }
                .health-high { color: #fd7e14; }
                .health-critical { color: #dc3545; }
                .charts { margin: 20px 0; }
                .chart-container { margin: 20px 0; text-align: center; }
                .recommendations { background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .issues { background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>プロジェクト進捗レポート</h1>
                <p><strong>プロジェクトID:</strong> {project_id}</p>
                <p><strong>生成日時:</strong> {generated_at}</p>
            </div>

            <h2>"📊" 進捗メトリクス</h2>
            <div class="metrics">
                <div class="metric-card">
                    <h3>総タスク数</h3>
                    <p>{total_tasks}</p>
                </div>
                <div class="metric-card">
                    <h3>完了率</h3>
                    <p>{completion_rate:0.1f}%</p>
                </div>
                <div class="metric-card">
                    <h3>ベロシティ</h3>
                    <p>{velocity:0.2f} タスク/日</p>
                </div>
            </div>

            <h2>🏥 プロジェクト健全性</h2>
            <div class="health-score health-{risk_class}">
                健全性スコア: {health_score:0.1f}/100 (リスクレベル: {risk_level})
            </div>

            {issues_section}
            {recommendations_section}

            <h2>"📈" 可視化チャート</h2>
            <div class="charts">
                {charts_section}
            </div>
        </body>
        </html>
        """

        # リスクレベルに対応するCSSクラス
        risk_class_map = {"低": "low", "中": "medium", "高": "high", "危険": "critical"}
        risk_class = risk_class_map.get(report_data["health"]["risk_level"], "medium")

        # 問題点セクション
        issues_section = ""
        if report_data["health"]["issues"]:
            issues_html = (
                "<ul>"
                + "".join(
                    f"<li>{issue}</li>" for issue in report_data["health"]["issues"]
                )
                + "</ul>"
            )
            issues_section = f'<div class="issues"><h3>⚠️ 問題点</h3>{issues_html}</div>'

        # 推奨事項セクション
        recommendations_section = ""
        if report_data["health"]["recommendations"]:
            recommendations_html = (
                "<ul>"
                + "".join(
                    f"<li>{rec}</li>"
                    for rec in report_data["health"]["recommendations"]
                )
                + "</ul>"
            )
            recommendations_section = f'<div class="recommendations"><h3>💡 推奨事項</h3>{recommendations_html}</div>'

        # チャートセクション
        charts_section = ""
        for chart_name, chart_path in report_data["charts"].items():
            if chart_path:
                charts_section += f'<div class="chart-container"><h3>
                    f"{chart_name}</h3><img src="{chart_path}" alt="{chart_name}" style="max-width: 100%;"></div>'

        # HTMLを生成
        html_content = html_template.format(
            project_id=report_data["project_id"],
            generated_at=report_data["generated_at"],
            total_tasks=report_data["metrics"]["total_tasks"],
            completion_rate=report_data["metrics"]["completion_rate"],
            velocity=report_data["metrics"]["velocity"],
            health_score=report_data["health"]["health_score"],
            risk_level=report_data["health"]["risk_level"],
            risk_class=risk_class,
            issues_section=issues_section,
            recommendations_section=recommendations_section,
            charts_section=charts_section,
        )

        # ファイルに保存
        report_filename = f"progress_report_{report_data['project_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_path = self.reports_path / report_filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.stats["reports_generated"] += 1
        logger.info(f"HTMLレポート生成完了: {report_path}")

        return str(report_path)

    async def _generate_json_report(self, report_data: Dict) -> strreport_filename = f"progress_report_{report_data['project_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json":
    """SONレポートを生成"""
        report_path = self.reports_path / report_filename
:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        self.stats["reports_generated"] += 1
        logger.info(f"JSONレポート生成完了: {report_path}")

        return str(report_path)

    async def _generate_markdown_report(self, report_data: Dict) -> str:
        """Markdownレポートを生成"""
        markdown_template = """
# プロジェクト進捗レポート

**プロジェクトID:** {project_id}
**生成日時:** {generated_at}

## 📊 進捗メトリクス

| 項目 | 値 |
|------|------|
| 総タスク数 | {total_tasks} |
| 完了タスク数 | {completed_tasks} |
| 進行中タスク数 | {in_progress_tasks} |
| Todoタスク数 | {todo_tasks} |
| ブロックタスク数 | {blocked_tasks} |
| 完了率 | {completion_rate:0.1f}% |
| ベロシティ | {velocity:0.2f} タスク/日 |

## 🏥 プロジェクト健全性

**健全性スコア:** {health_score:0.1f}/100
**リスクレベル:** {risk_level}

{issues_section}

{recommendations_section}

## 📈 可視化チャート

{charts_section}
        """

        # 問題点セクション
        issues_section = ""
        if report_data["health"]["issues"]:
            issues_list = "\n".join(
                f"- {issue}" for issue in report_data["health"]["issues"]
            )
            issues_section = f"### ⚠️ 問題点\n\n{issues_list}"

        # 推奨事項セクション
        recommendations_section = ""
        if report_data["health"]["recommendations"]:
            recommendations_list = "\n".join(
                f"- {rec}" for rec in report_data["health"]["recommendations"]
            )
            recommendations_section = f"### 💡 推奨事項\n\n{recommendations_list}"

        # チャートセクション
        charts_section = ""
        for chart_name, chart_path in report_data["charts"].items():
            if chart_path:
                charts_section += (
                    f"### {chart_name}\n\n![{chart_name}]({chart_path})\n\n"
                )

        # Markdownを生成
        markdown_content = markdown_template.format(
            project_id=report_data["project_id"],
            generated_at=report_data["generated_at"],
            total_tasks=report_data["metrics"]["total_tasks"],
            completed_tasks=report_data["metrics"]["completed_tasks"],
            in_progress_tasks=report_data["metrics"]["in_progress_tasks"],
            todo_tasks=report_data["metrics"]["todo_tasks"],
            blocked_tasks=report_data["metrics"]["blocked_tasks"],
            completion_rate=report_data["metrics"]["completion_rate"],
            velocity=report_data["metrics"]["velocity"],
            health_score=report_data["health"]["health_score"],
            risk_level=report_data["health"]["risk_level"],
            issues_section=issues_section,
            recommendations_section=recommendations_section,
            charts_section=charts_section,
        )

        # ファイルに保存
        report_filename = f"progress_report_{report_data['project_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = self.reports_path / report_filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        self.stats["reports_generated"] += 1
        logger.info(f"Markdownレポート生成完了: {report_path}")

        return str(report_path)

    async def update_metrics_history(self, project_id: str):
        """メトリクス履歴を更新"""
        try:
            metrics = await self.collect_project_metrics(project_id)

            history_entry = {
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": asdict(metrics),
            }

            self.metrics_history.append(history_entry)

            # 履歴を最新100件に制限
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]

            self._save_metrics_history()
            self.stats["last_update"] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"メトリクス履歴更新エラー: {e}")

    async def get_visualization_summary(self) -> Dict:
        """可視化システムの概要を取得"""
        return {
            "stats": self.stats,
            "tracked_projects": len(
                set(m.get("project_id") for m in self.metrics_history)
            ),
            "available_visualizations": [vt.value for vt in VisualizationType],
            "supported_formats": [rf.value for rf in ReportFormat],
            "recent_metrics": self.metrics_history[-5:] if self.metrics_history else [],
        }


# 使用例
async def main()viz_system = ProgressVisualization()
"""メイン実行関数"""

    # システム概要を取得
    summary = await viz_system.get_visualization_summary()
    print(f"📊 進捗可視化システム概要:")
    print(f"   📈 総可視化数: {summary['stats']['total_visualizations']}")
    print(f"   📋 生成レポート数: {summary['stats']['reports_generated']}")
    print(f"   🎯 追跡プロジェクト数: {summary['tracked_projects']}")
    print(f"   🔄 最終更新: {summary['stats']['last_update']}")


if __name__ == "__main__":
    asyncio.run(main())
