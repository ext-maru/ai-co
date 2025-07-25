#!/usr/bin/env python3
"""
🏛️ プロジェクト知能システム
日次自動学習・改善システム
"""

import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import subprocess
import sys

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.project_automation_engine import ProjectAutomationEngine

logger = logging.getLogger(__name__)

class ProjectIntelligenceSystem:
    """プロジェクト知能システム - 自動学習・改善"""

    def __init__(self):
        """初期化メソッド"""

        self.automation_engine = ProjectAutomationEngine()
        self.db_path = PROJECT_ROOT / "project_intelligence.db"
        self.reports_dir = PROJECT_ROOT / "reports" / "daily_intelligence"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """データベース初期化"""
        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        # 学習データテーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                project_id TEXT,

                phase_name TEXT,
                metric_type TEXT,
                metric_value REAL,
                improvement_suggestion TEXT,
                confidence_score REAL,
                applied BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 改善履歴テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS improvement_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                improvement_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                effectiveness_score REAL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated_at TIMESTAMP,
                elder_approval TEXT
            )
        """
        )

        # エルダー評議会報告テーブル
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS elder_council_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date DATE NOT NULL,
                report_type TEXT NOT NULL,
                content TEXT NOT NULL,
                elder_responses TEXT,
                approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    async def daily_intelligence_cycle(self):
        """日次知能サイクル"""
        today = datetime.now().date()

        logger.info(f"🧠 日次知能サイクル開始: {today}")

        # 1.0 プロジェクトデータ収集
        project_data = await self._collect_project_data()

        # 2.0 パターン分析
        patterns = await self._analyze_patterns(project_data)

        # 3.0 改善提案生成
        improvements = await self._generate_improvements(patterns)

        # 4.0 エルダー評議会への報告
        report = await self._generate_elder_council_report(improvements)

        # 5.0 承認された改善の自動適用
        await self._apply_approved_improvements()

        # 6.0 日次レポート生成
        await self._generate_daily_report(today, project_data, patterns, improvements)

        logger.info("🧠 日次知能サイクル完了")

        return {
            "success": True,
            "date": today,
            "projects_analyzed": len(project_data),
            "patterns_found": len(patterns),
            "improvements_suggested": len(improvements),
            "elder_council_report": report["id"] if report else None,
        }

    async def _collect_project_data(self) -> List[Dict[str, Any]]:
        """プロジェクトデータ収集"""
        project_data = []

        # 既存プロジェクトの分析
        projects_dir = PROJECT_ROOT / "projects"
        if projects_dir.exists():
            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir() and project_dir.name.startswith("project_"):
                    try:

                            project_dir.name
                        )
                        if not (context):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if context:
                            # プロジェクトメトリクス収集
                            metrics = await self._collect_project_metrics(project_dir)

                            project_data.append(
                                {
                                    "project_id": project_dir.name,
                                    "context": context,
                                    "metrics": metrics,
                                    "files": self._analyze_project_files(project_dir),
                                }
                            )
                    except Exception as e:
                        logger.error(f"プロジェクト分析エラー {project_dir.name}: {e}")

        return project_data

    async def _collect_project_metrics(self, project_dir: Path) -> Dict[str, Any]:
        """プロジェクトメトリクス収集"""
        metrics = {
            "file_count": 0,
            "code_lines": 0,
            "test_coverage": 0.0,
            "completion_rate": 0.0,
            "quality_score": 0.0,
            "automation_efficiency": 0.0,
        }

        # ファイル数カウント
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                metrics["file_count"] += 1

                # コード行数カウント
                if file_path.suffix in [".py", ".js", ".ts", ".sql"]:
                    try:
                        # Deep nesting detected (depth: 5) - consider refactoring
                        with open(file_path, "r", encoding="utf-8") as f:
                            metrics["code_lines"] += len(f.readlines())
                    except:
                        pass

        # テストカバレッジ推定
        test_files = list(project_dir.glob("**/test_*.py"))
        if test_files:
            metrics["test_coverage"] = min(
                len(test_files) / max(1, metrics["file_count"] * 0.3), 1.0
            )

        # 完成度推定
        required_files = ["requirements.md", "architecture.md"]
        existing_files = [f for f in required_files if (project_dir / f).exists()]
        metrics["completion_rate"] = len(existing_files) / len(required_files)

        return metrics

    def _analyze_project_files(self, project_dir: Path) -> Dict[str, Any]:
        """プロジェクトファイル分析"""
        file_analysis = {
            "total_files": 0,
            "documentation_files": 0,
            "code_files": 0,
            "test_files": 0,
            "config_files": 0,
            "missing_files": [],
            "quality_issues": [],
        }

        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                file_analysis["total_files"] += 1

                if file_path.suffix in [".md", ".txt", ".rst"]:
                    file_analysis["documentation_files"] += 1
                elif file_path.suffix in [".py", ".js", ".ts", ".java", ".cpp"]:
                    file_analysis["code_files"] += 1
                elif file_path.name.startswith("test_"):
                    file_analysis["test_files"] += 1
                elif file_path.suffix in [".json", ".yaml", ".yml", ".ini"]:
                    file_analysis["config_files"] += 1

        # 欠落ファイル検出
        expected_files = ["README.md", "requirements.md", ".gitignore"]
        for expected in expected_files:
            if not (project_dir / expected).exists():
                file_analysis["missing_files"].append(expected)

        return file_analysis

    async def _analyze_patterns(
        self, project_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """パターン分析"""
        patterns = []

        # 成功パターン分析
        successful_projects = [
            p for p in project_data if p["metrics"]["completion_rate"] > 0.7
        ]
        if successful_projects:
            patterns.append(
                {
                    "type": "success_pattern",
                    "description": "高完成度プロジェクトの共通点",
                    "data": self._extract_common_patterns(successful_projects),
                    "confidence": 0.8,
                }
            )

        # 効率性パターン分析
        efficient_projects = [
            p for p in project_data if p["metrics"]["automation_efficiency"] > 0.6
        ]
        if efficient_projects:
            patterns.append(
                {
                    "type": "efficiency_pattern",
                    "description": "高効率プロジェクトの特徴",
                    "data": self._extract_efficiency_patterns(efficient_projects),
                    "confidence": 0.7,
                }
            )

        # 問題パターン分析
        problematic_projects = [
            p for p in project_data if p["metrics"]["quality_score"] < 0.5
        ]
        if problematic_projects:
            patterns.append(
                {
                    "type": "problem_pattern",
                    "description": "品質問題の共通要因",
                    "data": self._extract_problem_patterns(problematic_projects),
                    "confidence": 0.6,
                }
            )

        return patterns

    def _extract_common_patterns(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """共通パターンの抽出"""

        # テンプレート使用頻度
        for project in projects:

            )

        # 共通ファイル
        all_files = set()
        for project in projects:
            files = project["files"]
            all_files.update(files.keys())

        for file_type in all_files:
            count = sum(1 for p in projects if file_type in p["files"])
            if count > len(projects) * 0.7:  # 70%以上で共通
                patterns["common_files"][file_type] = count / len(projects)

        return patterns

    def _extract_efficiency_patterns(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """効率性パターンの抽出"""
        return {
            "average_file_count": sum(p["metrics"]["file_count"] for p in projects)
            / len(projects),
            "average_completion_time": "推定値",  # 実際の完成時間データがあれば使用
            "common_automation_rules": "分析結果",
        }

    def _extract_problem_patterns(
        self, projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """問題パターンの抽出"""
        return {
            "common_missing_files": {},
            "quality_issues": [],
            "completion_bottlenecks": [],
        }

    async def _generate_improvements(
        self, patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """改善提案生成"""
        improvements = []

        for pattern in patterns:
            if pattern["type"] == "success_pattern":
                # 成功パターンに基づく改善提案
                improvements.extend(self._generate_success_improvements(pattern))
            elif pattern["type"] == "efficiency_pattern":
                # 効率性改善提案
                improvements.extend(self._generate_efficiency_improvements(pattern))
            elif pattern["type"] == "problem_pattern":
                # 問題解決提案
                improvements.extend(self._generate_problem_solutions(pattern))

        return improvements

    def _generate_success_improvements(
        self, pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """成功パターンに基づく改善提案"""
        improvements = []

        # 成功プロジェクトの共通ファイルを新規テンプレートに追加
        common_files = pattern["data"].get("common_files", {})
        for file_type, frequency in common_files.items():
            if frequency > 0.8:  # 80%以上で共通
                improvements.append(
                    {

                        "description": f"テンプレートに{file_type}を追加",

                        "confidence": frequency,
                        "priority": "medium",
                    }
                )

        return improvements

    def _generate_efficiency_improvements(
        self, pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """効率性改善提案"""
        improvements = []

        # 自動化ルールの改善
        improvements.append(
            {
                "type": "automation_rule",
                "description": "自動化ルールの最適化",
                "action": "optimize_automation_rules",
                "confidence": 0.7,
                "priority": "high",
            }
        )

        return improvements

    def _generate_problem_solutions(
        self, pattern: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """問題解決提案"""
        improvements = []

        # 品質チェック強化
        improvements.append(
            {
                "type": "quality_check",
                "description": "品質チェック項目の追加",
                "action": "add_quality_checks",
                "confidence": 0.6,
                "priority": "medium",
            }
        )

        return improvements

    async def _generate_elder_council_report(
        self, improvements: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """エルダー評議会レポート生成"""
        if not improvements:
            return None

        report_id = f"intelligence_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        report_content = {
            "report_id": report_id,
            "date": datetime.now().date().isoformat(),
            "summary": {
                "total_improvements": len(improvements),
                "high_priority": len(
                    [i for i in improvements if i["priority"] == "high"]
                ),
                "medium_priority": len(
                    [i for i in improvements if i["priority"] == "medium"]
                ),
                "low_priority": len(
                    [i for i in improvements if i["priority"] == "low"]
                ),
            },
            "improvements": improvements,
            "recommendations": [
                "高優先度の改善を優先実装",
                "テンプレートの継続的改善",
                "自動化ルールの最適化",
            ],
            "elder_consultation": {
                "knowledge_sage": "過去の成功事例との比較分析",
                "task_sage": "実装優先順位の決定",
                "incident_sage": "リスク評価と予防策",
                "rag_sage": "最新技術動向の調査",
            },
        }

        # データベースに保存
        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO elder_council_reports (report_date, report_type, content)
            VALUES (?, ?, ?)
        """,
            (
                datetime.now().date(),
                "daily_intelligence",
                json.dumps(report_content, ensure_ascii=False),
            ),
        )

        conn.commit()
        conn.close()

        # エルダー評議会レポートファイル作成
        report_file = self.reports_dir / f"{report_id}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_content, f, indent=2, ensure_ascii=False)

        return {"id": report_id, "file": str(report_file)}

    async def _apply_approved_improvements(self):
        """承認された改善の自動適用"""
        # 承認済み改善の取得
        conn = sqlite3connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM elder_council_reports
            WHERE approved = TRUE AND report_type = 'daily_intelligence'
            ORDER BY created_at DESC LIMIT 5
        """
        )

        approved_reports = cursor.fetchall()
        conn.close()

        for report in approved_reports:
            try:
                content = json.loads(report[3])  # content column
                await self._apply_improvements(content["improvements"])
            except Exception as e:
                logger.error(f"改善適用エラー: {e}")

    async def _apply_improvements(self, improvements: List[Dict[str, Any]]):
        """改善の適用"""
        for improvement in improvements:
            try:

                elif improvement["type"] == "automation_rule":
                    await self._apply_automation_rule(improvement)
                elif improvement["type"] == "quality_check":
                    await self._apply_quality_check(improvement)

                # 適用履歴記録
                conn = sqlite3connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO improvement_history
                    (improvement_type, old_value, new_value, applied_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (improvement["type"], "旧値", "新値", datetime.now()),
                )

                conn.commit()
                conn.close()

            except Exception as e:
                logger.error(f"改善適用エラー {improvement['type']}: {e}")

        """テンプレート改善の適用"""
        # テンプレートファイルの更新
        logger.info(f"テンプレート改善適用: {improvement['description']}")

    async def _apply_automation_rule(self, improvement: Dict[str, Any]):
        """自動化ルール改善の適用"""
        # 自動化ルールの更新
        logger.info(f"自動化ルール改善適用: {improvement['description']}")

    async def _apply_quality_check(self, improvement: Dict[str, Any]):
        """品質チェック改善の適用"""
        # 品質チェックの追加
        logger.info(f"品質チェック改善適用: {improvement['description']}")

    async def _generate_daily_report(self, date, project_data, patterns, improvements):
        """日次レポート生成"""
        report = {
            "date": date.isoformat(),
            "summary": {
                "projects_analyzed": len(project_data),
                "patterns_identified": len(patterns),
                "improvements_suggested": len(improvements),
                "overall_health": self._calculate_overall_health(project_data),
            },
            "projects": [
                {
                    "id": p["project_id"],
                    "completion_rate": p["metrics"]["completion_rate"],
                    "quality_score": p["metrics"]["quality_score"],
                }
                for p in project_data
            ],
            "patterns": patterns,
            "improvements": improvements,
        }

        # レポートファイル作成
        report_file = self.reports_dir / f"daily_report_{date.strftime('%Y%m%d')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report_file

    def _calculate_overall_health(self, project_data: List[Dict[str, Any]]) -> float:
        """全体健康度計算"""
        if not project_data:
            return 0.0

        total_health = sum(
            p["metrics"]["completion_rate"] * 0.4
            + p["metrics"]["quality_score"] * 0.3
            + p["metrics"]["test_coverage"] * 0.3
            for p in project_data
        )

        return total_health / len(project_data)

class DailyIntelligenceScheduler:
    """日次知能スケジューラー"""

    def __init__(self):
        """初期化メソッド"""
        self.intelligence_system = ProjectIntelligenceSystem()

    async def start_daily_cycle(self):
        """日次サイクル開始"""
        while True:
            try:
                # 毎日午前6時に実行
                now = datetime.now()
                next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)

                if next_run <= now:
                    next_run += timedelta(days=1)

                # 次回実行までの待機時間計算
                wait_seconds = (next_run - now).total_seconds()

                logger.info(f"📅 次回実行予定: {next_run}")
                await asyncio.sleep(wait_seconds)

                # 日次知能サイクル実行
                result = await self.intelligence_system.daily_intelligence_cycle()
                logger.info(f"📊 日次知能サイクル結果: {result}")

            except Exception as e:
                logger.error(f"日次知能サイクルエラー: {e}")
                await asyncio.sleep(3600)  # エラー時は1時間後に再試行

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="プロジェクト知能システム")
    parser.add_argument("--daily", action="store_true", help="日次サイクル実行")
    parser.add_argument("--schedule", action="store_true", help="スケジューラー開始")
    parser.add_argument("--report", help="レポート生成 (日付: YYYY-MM-DD)")

    args = parser.parse_args()

    system = ProjectIntelligenceSystem()

    if args.daily:
        # 日次サイクルを即座に実行
        asyncio.run(system.daily_intelligence_cycle())
    elif args.schedule:
        # スケジューラー開始
        scheduler = DailyIntelligenceScheduler()
        asyncio.run(scheduler.start_daily_cycle())
    elif args.report:
        # 指定日のレポート生成
        print(f"指定日のレポート生成: {args.report}")
    else:
        parser.print_help()
