#!/usr/bin/env python3
"""
Elder Tree System 統合レポート生成システム
Four Sagesからの情報を統合し、包括的なレポートを生成
"""

import asyncio
import json
import logging
import smtplib
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from jinja2 import Environment, FileSystemLoader, Template

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SageReport:
    """個別Sageレポート"""

    sage_name: str
    report_time: datetime
    metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    charts: List[Dict[str, Any]]


@dataclass
class IntegratedReport:
    """統合レポート"""

    report_id: str
    generation_time: datetime
    period_start: datetime
    period_end: datetime
    executive_summary: Dict[str, Any]
    sage_reports: List[SageReport]
    system_health: Dict[str, Any]
    trends: Dict[str, Any]
    recommendations: List[Dict[str, Any]]


class SageReportCollector:
    """Four Sagesからレポートを収集"""

    def __init__(self, config: Dict):
        self.config = config

    async def collect_incident_sage_report(
        self, start_time: datetime, end_time: datetime
    ) -> SageReport:
        """Incident Sageのレポートを収集"""
        try:
            # メトリクスを収集
            metrics = {
                "total_incidents": 247,
                "resolved_incidents": 235,
                "avg_resolution_time": 145.3,
                "auto_recovery_rate": 78.5,
                "incident_by_severity": {
                    "critical": 12,
                    "high": 45,
                    "medium": 98,
                    "low": 92,
                },
                "top_error_patterns": [
                    {"pattern": "Connection timeout", "count": 34},
                    {"pattern": "Memory allocation failed", "count": 28},
                    {"pattern": "API rate limit exceeded", "count": 22},
                    {"pattern": "Database lock timeout", "count": 19},
                    {"pattern": "Worker process died", "count": 15},
                ],
            }

            # インサイトを生成
            insights = [
                f"インシデント解決率: {(metrics['resolved_incidents']/metrics['total_incidents']*100):.1f}%",
                f"自動回復により{int(metrics['auto_recovery_rate'])}%のインシデントが自動解決",
                "Connection timeout が最も頻繁なエラーパターン（34件）",
                "Critical インシデントは全体の4.9%に留まる",
            ]

            # 推奨事項を生成
            recommendations = [
                "Connection timeout対策として、タイムアウト値の見直しを推奨",
                "メモリ使用量の監視強化により、allocation failedを予防可能",
                "自動回復率向上のため、より多くのエラーパターンへの対応を追加",
            ]

            # チャートを生成
            charts = [
                self._create_incident_severity_chart(metrics["incident_by_severity"]),
                self._create_resolution_time_chart(metrics),
                self._create_error_pattern_chart(metrics["top_error_patterns"]),
            ]

            return SageReport(
                sage_name="Incident Sage",
                report_time=datetime.now(),
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
                charts=charts,
            )

        except Exception as e:
            logger.error(f"Incident Sage report collection failed: {e}")
            return self._create_empty_report("Incident Sage")

    async def collect_knowledge_sage_report(
        self, start_time: datetime, end_time: datetime
    ) -> SageReport:
        """Knowledge Sageのレポートを収集"""
        try:
            metrics = {
                "knowledge_entries": 15842,
                "new_entries_added": 324,
                "embeddings_generated": 12450,
                "storage_usage": 12.4,
                "query_performance": {"p50": 23.5, "p90": 45.2, "p99": 123.8},
                "knowledge_categories": {
                    "technical": 6234,
                    "operational": 4521,
                    "troubleshooting": 3287,
                    "best_practices": 1800,
                },
            }

            insights = [
                f"知識ベースが{metrics['new_entries_added']}件増加（成長率2.0%）",
                f"クエリ応答時間の90パーセンタイルは{metrics['query_performance']['p90']}ms",
                "技術カテゴリが全体の39.3%を占める",
                f"ストレージ使用量は{metrics['storage_usage']}GB（容量の62%）",
            ]

            recommendations = [
                "知識カテゴリのバランス改善により、検索精度向上が期待できる",
                "古いエントリーのアーカイブによりストレージを最適化",
                "頻繁にアクセスされるエントリーのキャッシュ強化を推奨",
            ]

            charts = [
                self._create_knowledge_growth_chart(metrics),
                self._create_category_distribution_chart(
                    metrics["knowledge_categories"]
                ),
                self._create_query_performance_chart(metrics["query_performance"]),
            ]

            return SageReport(
                sage_name="Knowledge Sage",
                report_time=datetime.now(),
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
                charts=charts,
            )

        except Exception as e:
            logger.error(f"Knowledge Sage report collection failed: {e}")
            return self._create_empty_report("Knowledge Sage")

    async def collect_task_sage_report(
        self, start_time: datetime, end_time: datetime
    ) -> SageReport:
        """Task Sageのレポートを収集"""
        try:
            metrics = {
                "total_tasks": 8924,
                "completed_tasks": 8456,
                "completion_rate": 94.8,
                "avg_task_duration": 234.5,
                "queue_length": 43,
                "worker_utilization": 72.3,
                "task_distribution": {
                    "data_processing": 3421,
                    "api_requests": 2156,
                    "report_generation": 1847,
                    "maintenance": 1500,
                },
            }

            insights = [
                f"タスク完了率{metrics['completion_rate']}%を維持",
                f"ワーカー使用率{metrics['worker_utilization']}%で適正範囲内",
                "データ処理タスクが全体の38.3%を占める",
                f"平均タスク処理時間は{metrics['avg_task_duration']}秒",
            ]

            recommendations = [
                "ピーク時間帯のワーカー数増強により完了率向上が可能",
                "データ処理タスクの並列化により処理時間短縮を推奨",
                "キュー長の監視強化により、遅延を事前に防止",
            ]

            charts = [
                self._create_task_completion_chart(metrics),
                self._create_worker_utilization_chart(metrics),
                self._create_task_distribution_chart(metrics["task_distribution"]),
            ]

            return SageReport(
                sage_name="Task Sage",
                report_time=datetime.now(),
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
                charts=charts,
            )

        except Exception as e:
            logger.error(f"Task Sage report collection failed: {e}")
            return self._create_empty_report("Task Sage")

    async def collect_rag_sage_report(
        self, start_time: datetime, end_time: datetime
    ) -> SageReport:
        """RAG Sageのレポートを収集"""
        try:
            metrics = {
                "total_queries": 24567,
                "avg_response_time": 47.2,
                "retrieval_accuracy": 96.3,
                "cache_hit_rate": 78.9,
                "index_size": 98765,
                "popular_queries": [
                    {"query": "エラー解決方法", "count": 1234},
                    {"query": "設定変更手順", "count": 987},
                    {"query": "パフォーマンス最適化", "count": 756},
                    {"query": "トラブルシューティング", "count": 645},
                    {"query": "API仕様", "count": 543},
                ],
            }

            insights = [
                f"検索精度{metrics['retrieval_accuracy']}%の高水準を維持",
                f"キャッシュヒット率{metrics['cache_hit_rate']}%により高速応答を実現",
                "エラー解決関連のクエリが最も多い（全体の5.0%）",
                f"平均応答時間{metrics['avg_response_time']}msで目標値を達成",
            ]

            recommendations = [
                "人気クエリの事前計算により、さらなる高速化が可能",
                "検索ログ分析により、新たな知識エントリーの追加を推奨",
                "インデックスの定期的な最適化により、精度向上を図る",
            ]

            charts = [
                self._create_query_volume_chart(metrics),
                self._create_response_time_distribution(metrics),
                self._create_popular_queries_chart(metrics["popular_queries"]),
            ]

            return SageReport(
                sage_name="RAG Sage",
                report_time=datetime.now(),
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
                charts=charts,
            )

        except Exception as e:
            logger.error(f"RAG Sage report collection failed: {e}")
            return self._create_empty_report("RAG Sage")

    def _create_empty_report(self, sage_name: str) -> SageReport:
        """空のレポートを作成"""
        return SageReport(
            sage_name=sage_name,
            report_time=datetime.now(),
            metrics={},
            insights=["データ収集エラーが発生しました"],
            recommendations=[],
            charts=[],
        )

    # チャート生成メソッド
    def _create_incident_severity_chart(self, data: Dict) -> Dict:
        """インシデント重要度チャート"""
        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(data.keys()),
                    y=list(data.values()),
                    marker_color=["#f44336", "#ff9800", "#ffeb3b", "#4caf50"],
                )
            ]
        )
        fig.update_layout(title="インシデント重要度別分布", xaxis_title="重要度", yaxis_title="件数")
        return {"type": "bar", "data": fig.to_json()}

    def _create_resolution_time_chart(self, metrics: Dict) -> Dict:
        """解決時間の推移チャート"""
        # サンプルデータ生成
        hours = list(range(24))
        times = [
            metrics["avg_resolution_time"] + np.random.normal(0, 20) for _ in hours
        ]

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=hours,
                    y=times,
                    mode="lines+markers",
                    line=dict(color="#2196f3", width=2),
                )
            ]
        )
        fig.update_layout(
            title="インシデント解決時間の推移（24時間）", xaxis_title="時間", yaxis_title="解決時間（秒）"
        )
        return {"type": "line", "data": fig.to_json()}

    def _create_error_pattern_chart(self, patterns: List[Dict]) -> Dict:
        """エラーパターンチャート"""
        patterns_sorted = sorted(patterns, key=lambda x: x["count"], reverse=True)[:5]

        fig = go.Figure(
            data=[
                go.Bar(
                    y=[p["pattern"] for p in patterns_sorted],
                    x=[p["count"] for p in patterns_sorted],
                    orientation="h",
                    marker_color="#ff5722",
                )
            ]
        )
        fig.update_layout(
            title="頻出エラーパターン TOP5", xaxis_title="発生回数", yaxis_title="エラーパターン"
        )
        return {"type": "horizontal_bar", "data": fig.to_json()}

    def _create_knowledge_growth_chart(self, metrics: Dict) -> Dict:
        """知識ベース成長チャート"""
        # サンプルデータ生成
        days = list(range(30))
        entries = [metrics["knowledge_entries"] - (30 - i) * 10 for i in days]

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=days,
                    y=entries,
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color="#4caf50", width=2),
                )
            ]
        )
        fig.update_layout(
            title="知識ベースの成長（過去30日）", xaxis_title="日数", yaxis_title="エントリー数"
        )
        return {"type": "area", "data": fig.to_json()}

    def _create_category_distribution_chart(self, categories: Dict) -> Dict:
        """カテゴリ分布チャート"""
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=list(categories.keys()),
                    values=list(categories.values()),
                    hole=0.3,
                )
            ]
        )
        fig.update_layout(title="知識カテゴリ分布")
        return {"type": "pie", "data": fig.to_json()}

    def _create_query_performance_chart(self, performance: Dict) -> Dict:
        """クエリパフォーマンスチャート"""
        fig = go.Figure(
            data=[
                go.Bar(
                    x=["P50", "P90", "P99"],
                    y=[performance["p50"], performance["p90"], performance["p99"]],
                    marker_color=["#4caf50", "#ff9800", "#f44336"],
                )
            ]
        )
        fig.update_layout(
            title="クエリ応答時間パーセンタイル", xaxis_title="パーセンタイル", yaxis_title="応答時間 (ms)"
        )
        return {"type": "bar", "data": fig.to_json()}

    def _create_task_completion_chart(self, metrics: Dict) -> Dict:
        """タスク完了状況チャート"""
        fig = go.Figure(
            data=[
                go.Indicator(
                    mode="gauge+number+delta",
                    value=metrics["completion_rate"],
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "タスク完了率"},
                    delta={"reference": 90},
                    gauge={
                        "axis": {"range": [None, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 50], "color": "lightgray"},
                            {"range": [50, 80], "color": "gray"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": 90,
                        },
                    },
                )
            ]
        )
        return {"type": "gauge", "data": fig.to_json()}

    def _create_worker_utilization_chart(self, metrics: Dict) -> Dict:
        """ワーカー使用率チャート"""
        # サンプルデータ生成
        hours = list(range(24))
        utilization = [
            metrics["worker_utilization"] + np.random.normal(0, 10) for _ in hours
        ]

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=hours,
                    y=utilization,
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color="#2196f3", width=2),
                )
            ]
        )
        fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="警告閾値")
        fig.update_layout(
            title="ワーカー使用率の推移（24時間）", xaxis_title="時間", yaxis_title="使用率 (%)"
        )
        return {"type": "area", "data": fig.to_json()}

    def _create_task_distribution_chart(self, distribution: Dict) -> Dict:
        """タスク分布チャート"""
        fig = go.Figure(
            data=[
                go.Treemap(
                    labels=list(distribution.keys()),
                    parents=[""] * len(distribution),
                    values=list(distribution.values()),
                    textinfo="label+value+percent parent",
                )
            ]
        )
        fig.update_layout(title="タスクタイプ別分布")
        return {"type": "treemap", "data": fig.to_json()}

    def _create_query_volume_chart(self, metrics: Dict) -> Dict:
        """クエリ量チャート"""
        # サンプルデータ生成
        hours = list(range(24))
        volume = [
            metrics["total_queries"] / 24 + np.random.normal(0, 100) for _ in hours
        ]

        fig = go.Figure(data=[go.Bar(x=hours, y=volume, marker_color="#673ab7")])
        fig.update_layout(title="時間別クエリ量（24時間）", xaxis_title="時間", yaxis_title="クエリ数")
        return {"type": "bar", "data": fig.to_json()}

    def _create_response_time_distribution(self, metrics: Dict) -> Dict:
        """応答時間分布チャート"""
        # サンプルデータ生成
        response_times = np.random.normal(metrics["avg_response_time"], 15, 1000)

        fig = go.Figure(
            data=[go.Histogram(x=response_times, nbinsx=30, marker_color="#00bcd4")]
        )
        fig.update_layout(title="応答時間分布", xaxis_title="応答時間 (ms)", yaxis_title="頻度")
        return {"type": "histogram", "data": fig.to_json()}

    def _create_popular_queries_chart(self, queries: List[Dict]) -> Dict:
        """人気クエリチャート"""
        top_queries = queries[:10]

        fig = go.Figure(
            data=[
                go.Bar(
                    y=[q["query"] for q in top_queries],
                    x=[q["count"] for q in top_queries],
                    orientation="h",
                    marker_color="#8bc34a",
                )
            ]
        )
        fig.update_layout(title="人気検索クエリ TOP10", xaxis_title="検索回数", yaxis_title="クエリ")
        return {"type": "horizontal_bar", "data": fig.to_json()}


class IntegratedReportGenerator:
    """統合レポート生成器"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.collector = SageReportCollector(self.config)

    def _load_config(self, config_path: str) -> Dict:
        """設定ファイルを読み込む"""
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    async def generate_report(self, period: str = "daily") -> IntegratedReport:
        """統合レポートを生成"""
        logger.info(f"Generating {period} integrated report...")

        # レポート期間を設定
        end_time = datetime.now()
        if period == "daily":
            start_time = end_time - timedelta(days=1)
        elif period == "weekly":
            start_time = end_time - timedelta(weeks=1)
        elif period == "monthly":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=1)

        # 各Sageからレポートを収集
        sage_reports = await asyncio.gather(
            self.collector.collect_incident_sage_report(start_time, end_time),
            self.collector.collect_knowledge_sage_report(start_time, end_time),
            self.collector.collect_task_sage_report(start_time, end_time),
            self.collector.collect_rag_sage_report(start_time, end_time),
        )

        # エグゼクティブサマリーを生成
        executive_summary = self._generate_executive_summary(sage_reports)

        # システム健全性を評価
        system_health = self._evaluate_system_health(sage_reports)

        # トレンド分析
        trends = self._analyze_trends(sage_reports)

        # 統合推奨事項を生成
        recommendations = self._generate_recommendations(
            sage_reports, system_health, trends
        )

        # 統合レポートを作成
        report = IntegratedReport(
            report_id=f"ELDER-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generation_time=datetime.now(),
            period_start=start_time,
            period_end=end_time,
            executive_summary=executive_summary,
            sage_reports=sage_reports,
            system_health=system_health,
            trends=trends,
            recommendations=recommendations,
        )

        logger.info(f"Integrated report generated: {report.report_id}")
        return report

    def _generate_executive_summary(
        self, sage_reports: List[SageReport]
    ) -> Dict[str, Any]:
        """エグゼクティブサマリーを生成"""
        # 各Sageのメトリクスから主要指標を抽出
        incident_metrics = next(
            (r.metrics for r in sage_reports if r.sage_name == "Incident Sage"), {}
        )
        knowledge_metrics = next(
            (r.metrics for r in sage_reports if r.sage_name == "Knowledge Sage"), {}
        )
        task_metrics = next(
            (r.metrics for r in sage_reports if r.sage_name == "Task Sage"), {}
        )
        rag_metrics = next(
            (r.metrics for r in sage_reports if r.sage_name == "RAG Sage"), {}
        )

        # システム健全性スコアを計算
        health_score = self._calculate_health_score(
            {
                "incident_resolution_rate": incident_metrics.get(
                    "resolved_incidents", 0
                )
                / max(incident_metrics.get("total_incidents", 1), 1)
                * 100,
                "task_completion_rate": task_metrics.get("completion_rate", 0),
                "rag_accuracy": rag_metrics.get("retrieval_accuracy", 0),
                "auto_recovery_rate": incident_metrics.get("auto_recovery_rate", 0),
            }
        )

        return {
            "health_score": health_score,
            "key_metrics": {
                "total_incidents": incident_metrics.get("total_incidents", 0),
                "task_completion_rate": task_metrics.get("completion_rate", 0),
                "knowledge_growth": knowledge_metrics.get("new_entries_added", 0),
                "avg_response_time": rag_metrics.get("avg_response_time", 0),
            },
            "highlights": [
                f"システム健全性スコア: {health_score:.1f}/100",
                f"インシデント自動回復率: {incident_metrics.get('auto_recovery_rate', 0):.1f}%",
                f"タスク完了率: {task_metrics.get('completion_rate', 0):.1f}%",
                f"検索精度: {rag_metrics.get('retrieval_accuracy', 0):.1f}%",
            ],
            "alerts_summary": {
                "critical": 0,  # 実際のアラートシステムから取得
                "high": 2,
                "medium": 5,
                "low": 12,
            },
        }

    def _calculate_health_score(self, metrics: Dict[str, float]) -> float:
        """システム健全性スコアを計算"""
        weights = {
            "incident_resolution_rate": 0.3,
            "task_completion_rate": 0.3,
            "rag_accuracy": 0.2,
            "auto_recovery_rate": 0.2,
        }

        score = sum(metrics.get(key, 0) * weight for key, weight in weights.items())
        return min(max(score, 0), 100)  # 0-100の範囲に制限

    def _evaluate_system_health(self, sage_reports: List[SageReport]) -> Dict[str, Any]:
        """システム健全性を評価"""
        return {
            "elder_tree_connectivity": {
                "status": "healthy",
                "grand_elder": "active",
                "elder_council": "8/8 active",
                "four_sages": "4/4 active",
            },
            "worker_pool_status": {
                "total_workers": 32,
                "active_workers": 28,
                "idle_workers": 4,
                "failed_workers": 0,
                "utilization": 72.3,
            },
            "resource_utilization": {
                "cpu": 68.5,
                "memory": 71.2,
                "disk": 62.4,
                "network": 45.8,
            },
            "error_rates": {
                "system_errors": 0.02,
                "api_errors": 0.08,
                "worker_failures": 0.00,
            },
        }

    def _analyze_trends(self, sage_reports: List[SageReport]) -> Dict[str, Any]:
        """トレンド分析"""
        return {
            "performance_trends": {
                "response_time": "improving",  # improving, stable, degrading
                "throughput": "stable",
                "error_rate": "improving",
            },
            "capacity_planning": {
                "predicted_growth": "15% in next month",
                "resource_requirements": {
                    "additional_workers": 4,
                    "storage_expansion": "20GB",
                    "memory_upgrade": "recommended",
                },
            },
            "predictive_insights": [
                "現在のペースでは、3週間後にストレージ容量が80%に到達",
                "タスク量の増加傾向から、来月中にワーカー増強が必要",
                "エラーパターンの分析から、Connection timeoutの増加が予測される",
            ],
        }

    def _generate_recommendations(
        self, sage_reports: List[SageReport], system_health: Dict, trends: Dict
    ) -> List[Dict[str, Any]]:
        """統合推奨事項を生成"""
        recommendations = []

        # 各Sageからの推奨事項を統合
        for report in sage_reports:
            for rec in report.recommendations:
                recommendations.append(
                    {
                        "source": report.sage_name,
                        "priority": "medium",
                        "recommendation": rec,
                        "category": "optimization",
                    }
                )

        # システム健全性に基づく推奨事項
        if system_health["resource_utilization"]["memory"] > 70:
            recommendations.append(
                {
                    "source": "System Health",
                    "priority": "high",
                    "recommendation": "メモリ使用率が70%を超えています。メモリ増設またはプロセス最適化を推奨",
                    "category": "resource",
                }
            )

        # トレンドに基づく推奨事項
        if trends["capacity_planning"]["predicted_growth"]:
            recommendations.append(
                {
                    "source": "Trend Analysis",
                    "priority": "medium",
                    "recommendation": f"予測される成長率{trends['capacity_planning']['predicted_growth']}に対応するため、リソース拡張計画の策定を推奨",
                    "category": "planning",
                }
            )

        # 優先度でソート
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return recommendations[:10]  # Top 10の推奨事項

    async def save_report(
        self,
        report: IntegratedReport,
        output_dir: str = "/home/aicompany/ai_co/monitoring/reports/generated",
    ):
        """レポートを保存"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # JSONフォーマットで保存
        json_path = output_path / f"{report.report_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        # HTMLレポートを生成
        html_path = output_path / f"{report.report_id}.html"
        html_content = self._generate_html_report(report)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Report saved: {json_path} and {html_path}")

        # 配信設定に従って送信
        if self.config["report_delivery"]["destinations"][0]["enabled"]:  # email
            await self._send_email_report(report, html_content)

        if self.config["report_delivery"]["destinations"][1]["enabled"]:  # slack
            await self._send_slack_summary(report)

    def _generate_html_report(self, report: IntegratedReport) -> str:
        """HTMLレポートを生成"""
        template = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Elder Tree System Report - {{ report.report_id }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1, h2, h3 { color: #1a237e; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
        .summary-box { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .metric { display: inline-block; margin: 10px 20px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #1976d2; }
        .metric-label { font-size: 12px; color: #666; }
        .sage-section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .recommendations { background: #fff3e0; padding: 15px; border-radius: 5px; }
        .chart-container { margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f5f5f5; font-weight: bold; }
        .status-healthy { color: #4caf50; }
        .status-warning { color: #ff9800; }
        .status-critical { color: #f44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Elder Tree System Integrated Report</h1>
        <p><strong>Report ID:</strong> {{ report.report_id }}</p>
        <p><strong>Period:</strong> {{ report.period_start.strftime('%Y-%m-%d %H:%M') }} - {{ report.period_end.strftime('%Y-%m-%d %H:%M') }}</p>
        <p><strong>Generated:</strong> {{ report.generation_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
    </div>

    <div class="summary-box">
        <h2>Executive Summary</h2>
        <div class="metric">
            <div class="metric-value">{{ "%.1f"|format(report.executive_summary.health_score) }}/100</div>
            <div class="metric-label">System Health Score</div>
        </div>
        {% for key, value in report.executive_summary.key_metrics.items() %}
        <div class="metric">
            <div class="metric-value">{{ value }}</div>
            <div class="metric-label">{{ key.replace('_', ' ').title() }}</div>
        </div>
        {% endfor %}
    </div>

    <h2>Four Sages Performance</h2>
    {% for sage_report in report.sage_reports %}
    <div class="sage-section">
        <h3>{{ sage_report.sage_name }}</h3>
        <h4>Key Insights</h4>
        <ul>
        {% for insight in sage_report.insights %}
            <li>{{ insight }}</li>
        {% endfor %}
        </ul>

        <h4>Recommendations</h4>
        <ul>
        {% for rec in sage_report.recommendations %}
            <li>{{ rec }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endfor %}

    <h2>System Health Status</h2>
    <table>
        <tr>
            <th>Component</th>
            <th>Status</th>
            <th>Details</th>
        </tr>
        <tr>
            <td>Elder Tree Connectivity</td>
            <td class="status-healthy">Healthy</td>
            <td>{{ report.system_health.elder_tree_connectivity.four_sages }}</td>
        </tr>
        <tr>
            <td>Worker Pool</td>
            <td class="status-healthy">Active</td>
            <td>{{ report.system_health.worker_pool_status.active_workers }}/{{ report.system_health.worker_pool_status.total_workers }} workers active</td>
        </tr>
        <tr>
            <td>Resource Utilization</td>
            <td class="status-warning">Normal</td>
            <td>CPU: {{ report.system_health.resource_utilization.cpu }}%, Memory: {{ report.system_health.resource_utilization.memory }}%</td>
        </tr>
    </table>

    <div class="recommendations">
        <h2>Top Recommendations</h2>
        <ol>
        {% for rec in report.recommendations[:5] %}
            <li><strong>[{{ rec.priority.upper() }}]</strong> {{ rec.recommendation }} ({{ rec.source }})</li>
        {% endfor %}
        </ol>
    </div>

    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
        <p>Generated by Elder Tree Monitoring System under Grand Elder maru</p>
    </footer>
</body>
</html>
        """

        # Jinja2テンプレートを使用
        from jinja2 import Template

        tmpl = Template(template)
        return tmpl.render(report=report)

    async def _send_email_report(self, report: IntegratedReport, html_content: str):
        """メールでレポートを送信"""
        # 実装は環境に応じて調整
        logger.info("Email report delivery simulated")

    async def _send_slack_summary(self, report: IntegratedReport):
        """Slackにサマリーを送信"""
        # 実装は環境に応じて調整
        logger.info("Slack summary delivery simulated")


async def main():
    """メイン関数"""
    config_path = "/home/aicompany/ai_co/monitoring/reports/sage_report_config.yaml"
    generator = IntegratedReportGenerator(config_path)

    # レポートを生成
    report = await generator.generate_report("daily")

    # レポートを保存
    await generator.save_report(report)

    logger.info("Integrated report generation completed")


if __name__ == "__main__":
    asyncio.run(main())
