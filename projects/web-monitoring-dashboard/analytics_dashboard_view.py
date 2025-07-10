#!/usr/bin/env python3
"""
データアナリティクスダッシュボードビュー
高度データアナリティクスプラットフォームの結果を可視化

設計: クロードエルダー
実装日: 2025年7月9日
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from flask import Blueprint
from flask import jsonify
from flask import render_template

logger = logging.getLogger(__name__)

# Blueprintの作成
analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


class AnalyticsDashboardView:
    """アナリティクスダッシュボードビュー"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "analytics_reports"

    def get_latest_report(self):
        """最新のレポートを取得"""
        try:
            report_files = list(self.reports_dir.glob("analytics_report_*.json"))
            if not report_files:
                return None

            # 最新ファイルを取得
            latest_file = max(report_files, key=lambda f: f.stat().st_mtime)

            with open(latest_file, "r", encoding="utf-8") as f:
                report = json.load(f)

            # NaN値を処理
            report = self._clean_nan_values(report)

            return report

        except Exception as e:
            logger.error(f"❌ レポート取得エラー: {e}")
            return None

    def _clean_nan_values(self, obj):
        """NaN値をNoneに変換"""
        if isinstance(obj, dict):
            return {k: self._clean_nan_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_nan_values(item) for item in obj]
        elif isinstance(obj, float) and str(obj) == "nan":
            return None
        else:
            return obj

    def format_report_for_display(self, report):
        """表示用にレポートをフォーマット"""
        if not report:
            return None

        formatted = {
            "generated_at": self._format_timestamp(report.get("generated_at")),
            "summary": report.get("summary", {}),
            "insights": report.get("executive_insights", []),
            "action_items": report.get("action_items", []),
            "analyses": [],
        }

        # 各分析結果をフォーマット
        for result in report.get("detailed_results", []):
            analysis = {
                "type": self._translate_analysis_type(result["type"]),
                "confidence": result["confidence"],
                "metrics": self._format_metrics(result["type"], result["metrics"]),
                "insights": result["insights"],
                "predictions": result["predictions"],
                "recommendations": result["recommendations"],
            }
            formatted["analyses"].append(analysis)

        return formatted

    def _format_timestamp(self, timestamp_str):
        """タイムスタンプをフォーマット"""
        try:
            dt = datetime.fromisoformat(timestamp_str)
            return dt.strftime("%Y年%m月%d日 %H:%M")
        except:
            return timestamp_str

    def _translate_analysis_type(self, analysis_type):
        """分析タイプを日本語に変換"""
        translations = {
            "commit_pattern": "コミットパターン分析",
            "sage_performance": "4賢者パフォーマンス分析",
            "system_health": "システムヘルス予測",
            "protocol_efficiency": "プロトコル効率分析",
            "error_prediction": "エラー予測",
            "bottleneck_detection": "ボトルネック検出",
        }
        return translations.get(analysis_type, analysis_type)

    def _format_metrics(self, analysis_type, metrics):
        """メトリクスを表示用にフォーマット"""
        formatted = []

        if analysis_type == "commit_pattern":
            formatted.append({"label": "総コミット数", "value": metrics.get("total_commits", 0), "unit": "件"})
            formatted.append({"label": "承認率", "value": f"{metrics.get('approval_rate', 0):.1f}", "unit": "%"})
            formatted.append(
                {"label": "平均実行時間", "value": f"{metrics.get('avg_execution_time', 0):.1f}", "unit": "秒"}
            )

        elif analysis_type == "sage_performance":
            sage_perf = metrics.get("sage_performance", {})
            for sage_name, stats in sage_perf.items():
                formatted.append(
                    {"label": f"{sage_name}承認率", "value": f"{stats.get('approval_rate', 0) * 100:.1f}", "unit": "%"}
                )

        elif analysis_type == "system_health":
            formatted.append(
                {"label": "ヘルススコア", "value": f"{metrics.get('current_health_score', 0):.0f}", "unit": "点"}
            )
            formatted.append({"label": "エラー率", "value": f"{metrics.get('error_rate', 0) * 100:.1f}", "unit": "%"})

        return formatted


# Viewインスタンスの作成
dashboard_view = AnalyticsDashboardView(Path("/home/aicompany/ai_co"))


# ルート定義
@analytics_bp.route("/")
def analytics_dashboard():
    """アナリティクスダッシュボードメインページ"""
    return render_template("analytics_dashboard.html")


@analytics_bp.route("/api/latest-report")
def get_latest_analytics():
    """最新の分析レポートを取得"""
    report = dashboard_view.get_latest_report()
    formatted = dashboard_view.format_report_for_display(report)
    return jsonify(formatted)


@analytics_bp.route("/api/run-analysis", methods=["POST"])
async def run_new_analysis():
    """新しい分析を実行"""
    try:
        from libs.data_analytics_platform import DataAnalyticsPlatform

        platform = DataAnalyticsPlatform(Path("/home/aicompany/ai_co"))
        report_path = await platform.run_full_analysis()

        return jsonify({"success": True, "report_path": str(report_path), "message": "分析が正常に完了しました"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "message": "分析中にエラーが発生しました"}), 500
