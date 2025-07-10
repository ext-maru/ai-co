#!/usr/bin/env python3
"""
レポート自動生成システム API
分析結果の多様な形式でのレポート化
"""

import json
import logging
import sys
import uuid
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from jinja2 import Environment
from jinja2 import FileSystemLoader

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Blueprint
from flask import Flask
from flask import jsonify
from flask import request
from flask import send_file

from libs.report_exporters import ExcelExporter
from libs.report_exporters import MarkdownExporter
from libs.report_exporters import PDFExporter

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint作成
report_api = Blueprint("report_api", __name__, url_prefix="/api/reports")


class ReportGenerationEngine:
    """レポート生成エンジン"""

    def __init__(self):
        # テンプレートディレクトリ
        self.template_dir = Path(__file__).parent.parent / "templates" / "reports"
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 出力ディレクトリ
        self.output_dir = Path(__file__).parent.parent / "generated_reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # テンプレートエンジン
        self.jinja_env = Environment(loader=FileSystemLoader(str(self.template_dir)), autoescape=True)

        # エクスポーター
        self.exporters = {
            "pdf": PDFExporter(),
            "excel": ExcelExporter(),
            "markdown": MarkdownExporter(),
            "html": self._export_html,
            "json": self._export_json,
        }

        # スケジュール済みレポート
        self.scheduled_reports = []

        # レポートテンプレート定義
        self.report_templates = {
            "daily_summary": {
                "name": "日次サマリーレポート",
                "description": "システム全体の日次パフォーマンスサマリー",
                "sections": ["overview", "sage_performance", "incidents", "tasks"],
            },
            "weekly_analysis": {
                "name": "週次分析レポート",
                "description": "週間のトレンド分析と洞察",
                "sections": ["trends", "correlations", "predictions", "recommendations"],
            },
            "incident_report": {
                "name": "インシデントレポート",
                "description": "インシデントの詳細分析",
                "sections": ["incident_details", "root_cause", "resolution", "prevention"],
            },
            "performance_report": {
                "name": "パフォーマンスレポート",
                "description": "システムパフォーマンスの詳細分析",
                "sections": ["metrics", "bottlenecks", "optimization", "capacity"],
            },
            "custom": {"name": "カスタムレポート", "description": "ユーザー定義のレポート", "sections": []},
        }

        # デフォルトテンプレート作成
        self._create_default_templates()

    def generate_report(
        self, report_type: str, data: Dict[str, Any], format: str = "pdf", options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """レポート生成"""
        try:
            # レポートID生成
            report_id = f"report_{uuid.uuid4().hex[:8]}"

            # テンプレート取得
            template_info = self.report_templates.get(report_type, self.report_templates["custom"])

            # レポートデータ準備
            report_data = self._prepare_report_data(report_type, data)

            # HTMLレンダリング
            html_content = self._render_template(report_type, report_data)

            # 指定形式でエクスポート
            if format in self.exporters:
                if format in ["pdf", "excel", "markdown"]:
                    file_path = self.exporters[format].export(html_content, report_data, report_id, self.output_dir)
                else:
                    file_path = self.exporters[format](html_content, report_data, report_id)
            else:
                raise ValueError(f"Unsupported format: {format}")

            # メタデータ作成
            metadata = {
                "report_id": report_id,
                "type": report_type,
                "format": format,
                "generated_at": datetime.now().isoformat(),
                "file_path": str(file_path),
                "template": template_info["name"],
                "data_summary": self._create_data_summary(report_data),
            }

            # メタデータ保存
            self._save_metadata(report_id, metadata)

            return {"success": True, "report_id": report_id, "file_path": str(file_path), "metadata": metadata}

        except Exception as e:
            logger.error(f"レポート生成エラー: {e}")
            return {"success": False, "error": str(e)}

    def schedule_report(
        self, report_type: str, schedule: Dict[str, Any], data_source: Dict[str, Any], format: str = "pdf"
    ) -> Dict[str, Any]:
        """レポートスケジューリング"""
        try:
            schedule_id = f"schedule_{uuid.uuid4().hex[:8]}"

            scheduled_report = {
                "schedule_id": schedule_id,
                "report_type": report_type,
                "schedule": schedule,
                "data_source": data_source,
                "format": format,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "next_run": self._calculate_next_run(schedule),
            }

            self.scheduled_reports.append(scheduled_report)

            return {"success": True, "schedule_id": schedule_id, "scheduled_report": scheduled_report}

        except Exception as e:
            logger.error(f"スケジューリングエラー: {e}")
            return {"success": False, "error": str(e)}

    def get_report_list(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """生成済みレポート一覧取得"""
        reports = []

        # メタデータファイル検索
        for meta_file in self.output_dir.glob("*.meta.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                    # フィルタ適用
                    if filters:
                        if "type" in filters and metadata["type"] != filters["type"]:
                            continue
                        if "format" in filters and metadata["format"] != filters["format"]:
                            continue
                        if "start_date" in filters:
                            if metadata["generated_at"] < filters["start_date"]:
                                continue
                        if "end_date" in filters:
                            if metadata["generated_at"] > filters["end_date"]:
                                continue

                    reports.append(metadata)

            except Exception as e:
                logger.error(f"メタデータ読み込みエラー: {e}")

        # 日付でソート（新しい順）
        reports.sort(key=lambda x: x["generated_at"], reverse=True)

        return reports

    def get_report_templates(self) -> Dict[str, Any]:
        """利用可能なレポートテンプレート取得"""
        return self.report_templates

    # プライベートメソッド
    def _create_default_templates(self):
        """デフォルトテンプレート作成"""
        # 基本テンプレート
        base_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { color: #2c3e50; margin-top: 30px; }
        .section { margin-bottom: 30px; }
        .metric { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .chart { margin: 20px 0; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #3498db; color: white; }
        .summary-box { background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .alert { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .alert-warning { background: #fff3cd; color: #856404; }
        .alert-danger { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <div class="summary-box">
        <p><strong>生成日時:</strong> {{ generated_at }}</p>
        <p><strong>期間:</strong> {{ period.start }} - {{ period.end }}</p>
    </div>

    {% block content %}
    {% endblock %}
</body>
</html>
"""

        # 日次サマリーテンプレート
        daily_template = """
{% extends "base.html" %}

{% block content %}
<div class="section">
    <h2>概要</h2>
    <div class="metric">
        <h3>システムヘルススコア: {{ health_score }}%</h3>
        <p>前日比: {% if health_change > 0 %}+{% endif %}{{ health_change }}%</p>
    </div>
</div>

<div class="section">
    <h2>4賢者パフォーマンス</h2>
    <table>
        <tr>
            <th>賢者</th>
            <th>応答時間 (ms)</th>
            <th>精度 (%)</th>
            <th>可用性 (%)</th>
        </tr>
        {% for sage in sages %}
        <tr>
            <td>{{ sage.name }}</td>
            <td>{{ sage.response_time }}</td>
            <td>{{ sage.accuracy }}</td>
            <td>{{ sage.availability }}</td>
        </tr>
        {% endfor %}
    </table>
</div>

<div class="section">
    <h2>インシデント</h2>
    {% if incidents %}
        {% for incident in incidents %}
        <div class="alert alert-{{ incident.severity }}">
            <strong>{{ incident.title }}</strong><br>
            発生時刻: {{ incident.time }}<br>
            ステータス: {{ incident.status }}
        </div>
        {% endfor %}
    {% else %}
        <p>本日のインシデントはありません。</p>
    {% endif %}
</div>

<div class="section">
    <h2>タスク完了状況</h2>
    <div class="metric">
        <p>完了タスク: {{ tasks.completed }}</p>
        <p>進行中タスク: {{ tasks.in_progress }}</p>
        <p>完了率: {{ tasks.completion_rate }}%</p>
    </div>
</div>
{% endblock %}
"""

        # テンプレート保存
        templates = {"base.html": base_template, "daily_summary.html": daily_template}

        for filename, content in templates.items():
            template_path = self.template_dir / filename
            if not template_path.exists():
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(content)

    def _prepare_report_data(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """レポートデータ準備"""
        # 共通データ
        report_data = {
            "title": self.report_templates[report_type]["name"],
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "period": data.get(
                "period",
                {
                    "start": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "end": datetime.now().strftime("%Y-%m-%d"),
                },
            ),
        }

        # レポートタイプ別のデータ処理
        if report_type == "daily_summary":
            report_data.update(self._prepare_daily_summary_data(data))
        elif report_type == "weekly_analysis":
            report_data.update(self._prepare_weekly_analysis_data(data))
        elif report_type == "incident_report":
            report_data.update(self._prepare_incident_report_data(data))
        elif report_type == "performance_report":
            report_data.update(self._prepare_performance_report_data(data))
        else:
            report_data.update(data)

        return report_data

    def _prepare_daily_summary_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """日次サマリーデータ準備"""
        return {
            "health_score": data.get("health_score", 95),
            "health_change": data.get("health_change", 2.5),
            "sages": data.get(
                "sages",
                [
                    {"name": "ナレッジ賢者", "response_time": 45, "accuracy": 98, "availability": 99.5},
                    {"name": "タスク賢者", "response_time": 55, "accuracy": 96, "availability": 99.0},
                    {"name": "インシデント賢者", "response_time": 30, "accuracy": 99, "availability": 99.9},
                    {"name": "RAG賢者", "response_time": 65, "accuracy": 94, "availability": 98.5},
                ],
            ),
            "incidents": data.get("incidents", []),
            "tasks": data.get("tasks", {"completed": 45, "in_progress": 12, "completion_rate": 78.9}),
        }

    def _prepare_weekly_analysis_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """週次分析データ準備"""
        return {
            "trends": data.get("trends", {}),
            "correlations": data.get("correlations", {}),
            "predictions": data.get("predictions", {}),
            "recommendations": data.get("recommendations", []),
        }

    def _prepare_incident_report_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """インシデントレポートデータ準備"""
        return {
            "incident": data.get("incident", {}),
            "timeline": data.get("timeline", []),
            "root_cause": data.get("root_cause", {}),
            "resolution": data.get("resolution", {}),
            "prevention": data.get("prevention", []),
        }

    def _prepare_performance_report_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンスレポートデータ準備"""
        return {
            "metrics": data.get("metrics", {}),
            "bottlenecks": data.get("bottlenecks", []),
            "optimization": data.get("optimization", {}),
            "capacity": data.get("capacity", {}),
        }

    def _render_template(self, report_type: str, data: Dict[str, Any]) -> str:
        """テンプレートレンダリング"""
        try:
            template_name = f"{report_type}.html"

            # テンプレートが存在しない場合はベーステンプレート使用
            if not (self.template_dir / template_name).exists():
                template = self.jinja_env.from_string(
                    """
                {% extends "base.html" %}
                {% block content %}
                <div class="section">
                    <h2>レポート内容</h2>
                    <pre>{{ data | tojson(indent=2) }}</pre>
                </div>
                {% endblock %}
                """
                )
                return template.render(data=data, **data)

            template = self.jinja_env.get_template(template_name)
            return template.render(**data)

        except Exception as e:
            logger.error(f"テンプレートレンダリングエラー: {e}")
            # フォールバック
            return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"

    def _export_html(self, html_content: str, data: Dict[str, Any], report_id: str) -> Path:
        """HTML形式でエクスポート"""
        file_path = self.output_dir / f"{report_id}.html"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return file_path

    def _export_json(self, html_content: str, data: Dict[str, Any], report_id: str) -> Path:
        """JSON形式でエクスポート"""
        file_path = self.output_dir / f"{report_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path

    def _create_data_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データサマリー作成"""
        summary = {
            "data_points": self._count_data_points(data),
            "keys": list(data.keys()),
            "has_metrics": "metrics" in data,
            "has_charts": any(k.endswith("_chart") for k in data.keys()),
        }
        return summary

    def _count_data_points(self, data: Any) -> int:
        """データポイント数カウント"""
        if isinstance(data, dict):
            return sum(self._count_data_points(v) for v in data.values())
        elif isinstance(data, list):
            return len(data) + sum(self._count_data_points(item) for item in data)
        else:
            return 1

    def _save_metadata(self, report_id: str, metadata: Dict[str, Any]):
        """メタデータ保存"""
        meta_path = self.output_dir / f"{report_id}.meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _calculate_next_run(self, schedule: Dict[str, Any]) -> str:
        """次回実行時刻計算"""
        # 簡略版実装
        if schedule.get("frequency") == "daily":
            next_run = datetime.now() + timedelta(days=1)
        elif schedule.get("frequency") == "weekly":
            next_run = datetime.now() + timedelta(weeks=1)
        elif schedule.get("frequency") == "monthly":
            next_run = datetime.now() + timedelta(days=30)
        else:
            next_run = datetime.now() + timedelta(hours=1)

        return next_run.isoformat()


# エンジンインスタンス
report_engine = ReportGenerationEngine()

# API エンドポイント


@report_api.route("/generate", methods=["POST"])
def generate_report():
    """レポート生成エンドポイント"""
    try:
        data = request.json
        report_type = data.get("type", "custom")
        report_data = data.get("data", {})
        format = data.get("format", "pdf")
        options = data.get("options", {})

        result = report_engine.generate_report(report_type, report_data, format, options)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@report_api.route("/schedule", methods=["POST"])
def schedule_report():
    """レポートスケジューリングエンドポイント"""
    try:
        data = request.json
        report_type = data.get("type")
        schedule = data.get("schedule")
        data_source = data.get("data_source")
        format = data.get("format", "pdf")

        if not all([report_type, schedule, data_source]):
            return jsonify({"error": "Missing required fields"}), 400

        result = report_engine.schedule_report(report_type, schedule, data_source, format)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@report_api.route("/list")
def list_reports():
    """レポート一覧取得エンドポイント"""
    try:
        filters = {}
        if request.args.get("type"):
            filters["type"] = request.args.get("type")
        if request.args.get("format"):
            filters["format"] = request.args.get("format")
        if request.args.get("start_date"):
            filters["start_date"] = request.args.get("start_date")
        if request.args.get("end_date"):
            filters["end_date"] = request.args.get("end_date")

        reports = report_engine.get_report_list(filters)

        return jsonify({"success": True, "reports": reports, "count": len(reports)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@report_api.route("/templates")
def get_templates():
    """レポートテンプレート一覧取得"""
    try:
        templates = report_engine.get_report_templates()
        return jsonify({"success": True, "templates": templates})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@report_api.route("/download/<report_id>")
def download_report(report_id):
    """レポートダウンロード"""
    try:
        # メタデータ読み込み
        meta_path = report_engine.output_dir / f"{report_id}.meta.json"
        if not meta_path.exists():
            return jsonify({"error": "Report not found"}), 404

        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        file_path = Path(metadata["file_path"])
        if not file_path.exists():
            return jsonify({"error": "Report file not found"}), 404

        return send_file(str(file_path), as_attachment=True, download_name=file_path.name)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@report_api.route("/schedules")
def get_schedules():
    """スケジュール済みレポート一覧"""
    try:
        return jsonify(
            {
                "success": True,
                "schedules": report_engine.scheduled_reports,
                "count": len(report_engine.scheduled_reports),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # テスト用実行
    app = Flask(__name__)
    app.register_blueprint(report_api)

    print("=== レポート生成システム API ===")
    print("エンドポイント:")
    print("- POST /api/reports/generate")
    print("- POST /api/reports/schedule")
    print("- GET  /api/reports/list")
    print("- GET  /api/reports/templates")
    print("- GET  /api/reports/download/<report_id>")
    print("- GET  /api/reports/schedules")

    app.run(debug=True, port=5006)
