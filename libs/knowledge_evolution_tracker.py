#!/usr/bin/env python3
"""
Elders Guild Knowledge Evolution Tracker
ナレッジベースの進化を追跡・可視化するシステム
"""

import difflib
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging

from core import EMOJI, BaseManager, get_config
from libs.slack_notifier import SlackNotifier


class KnowledgeEvolutionTracker(BaseManager):
    """ナレッジベースの進化追跡システム"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(manager_name="knowledge_evolution")
        self.config = get_config()
        self.project_root = Path("/home/aicompany/ai_co")
        self.knowledge_base = self.project_root / "knowledge_base"
        self.evolution_db = self.knowledge_base / "evolution_tracking"
        self.ensure_directories()

    def initialize(self):
        """BaseManagerの抽象メソッドを実装"""
        self.logger.info(
            f"{EMOJI['evolution']} Knowledge Evolution Tracker initialized"
        )

    def ensure_directories(self):
        """必要なディレクトリを作成"""
        self.evolution_db.mkdir(parents=True, exist_ok=True)

    def capture_snapshot(self) -> Dict[str, Any]:
        """現在の状態のスナップショット取得"""
        self.logger.info(f"{EMOJI['image']} Capturing knowledge snapshot...")

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "git_commit": self._get_current_git_commit(),
            "files": {},
            "statistics": {},
            "changes": [],
        }

        # 全ファイルのハッシュ値を計算
        for category in ["workers", "libs", "core", "knowledge_base"]:
            category_path = self.project_root / category
            if category_path.exists():
                snapshot["files"][category] = self._scan_files(category_path)

        # 統計情報の収集
        snapshot["statistics"] = self._collect_statistics()

        return snapshot

    def _scan_files(self, path: Path) -> Dict[str, str]:
        """ディレクトリ内のファイルをスキャン"""
        files = {}

        for file_path in path.rglob("*.py"):
            if "__pycache__" not in str(file_path):
                try:
                    content = file_path.read_bytes()
                    file_hash = hashlib.sha256(content).hexdigest()
                    relative_path = str(file_path.relative_to(self.project_root))
                    files[relative_path] = file_hash
                except Exception as e:
                    self.logger.warning(f"Error reading {file_path}: {e}")

        for file_path in path.rglob("*.md"):
            try:
                content = file_path.read_bytes()
                file_hash = hashlib.sha256(content).hexdigest()
                relative_path = str(file_path.relative_to(self.project_root))
                files[relative_path] = file_hash
            except Exception as e:
                self.logger.warning(f"Error reading {file_path}: {e}")

        return files

    def _collect_statistics(self) -> Dict[str, Any]:
        """統計情報の収集"""
        stats = {
            "worker_count": len(
                list((self.project_root / "workers").glob("*_worker.py"))
            ),
            "manager_count": len(
                list((self.project_root / "libs").glob("*_manager.py"))
            ),
            "command_count": len(
                list((self.project_root / "commands").glob("ai_*.py"))
            ),
            "knowledge_docs": len(list(self.knowledge_base.glob("*.md"))),
            "total_python_files": len(list(self.project_root.rglob("*.py"))),
            "total_lines": self._count_total_lines(),
        }

        return stats

    def _count_total_lines(self) -> int:
        """全体の行数をカウント"""
        total = 0
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                try:
                    with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                        total += sum(1 for _ in f)
                except:
                    pass
        return total

    def _get_current_git_commit(self) -> Optional[str]:
        """現在のGitコミットハッシュを取得"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    def compare_snapshots(
        self, snapshot1: Dict[str, Any], snapshot2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """2つのスナップショットを比較"""
        self.logger.info(f"{EMOJI['info']} Comparing snapshots...")

        comparison = {
            "time_diff": self._calculate_time_diff(
                snapshot1["timestamp"], snapshot2["timestamp"]
            ),
            "added_files": [],
            "modified_files": [],
            "deleted_files": [],
            "statistics_changes": {},
            "summary": "",
        }

        # ファイルの変更を検出
        files1 = self._flatten_files(snapshot1["files"])
        files2 = self._flatten_files(snapshot2["files"])

        all_files = set(files1.keys()) | set(files2.keys())

        for file_path in all_files:
            if file_path not in files1:
                comparison["added_files"].append(file_path)
            elif file_path not in files2:
                comparison["deleted_files"].append(file_path)
            elif files1[file_path] != files2[file_path]:
                comparison["modified_files"].append(file_path)

        # 統計の変更
        for key in snapshot2["statistics"]:
            if key in snapshot1["statistics"]:
                old_val = snapshot1["statistics"][key]
                new_val = snapshot2["statistics"][key]
                if old_val != new_val:
                    comparison["statistics_changes"][key] = {
                        "old": old_val,
                        "new": new_val,
                        "change": new_val - old_val,
                    }

        # サマリー生成
        comparison["summary"] = self._generate_comparison_summary(comparison)

        return comparison

    def _flatten_files(self, files_dict: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        """ネストされたファイル辞書をフラット化"""
        flat = {}
        for category, files in files_dict.items():
        # 繰り返し処理
            for file_path, file_hash in files.items():
                flat[file_path] = file_hash
        return flat

    def _calculate_time_diff(self, time1: str, time2: str) -> str:
        """時間差を計算"""
        dt1 = datetime.fromisoformat(time1)
        dt2 = datetime.fromisoformat(time2)
        diff = dt2 - dt1

        if diff.days > 0:
            return f"{diff.days} days"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hours"
        else:
            return f"{diff.seconds // 60} minutes"

    def _generate_comparison_summary(self, comparison: Dict[str, Any]) -> str:
        """比較結果のサマリー生成"""
        summary_parts = []

        if comparison["added_files"]:
            summary_parts.append(f"Added {len(comparison['added_files'])} files")
        if comparison["modified_files"]:
            summary_parts.append(f"Modified {len(comparison['modified_files'])} files")
        if comparison["deleted_files"]:
            summary_parts.append(f"Deleted {len(comparison['deleted_files'])} files")

        for key, change in comparison["statistics_changes"].items():
            if change["change"] > 0:
                summary_parts.append(f"{key}: +{change['change']}")
            elif change["change"] < 0:
                summary_parts.append(f"{key}: {change['change']}")

        return " | ".join(summary_parts) if summary_parts else "No changes"

    def track_evolution(self, interval_hours: int = 24):
        """進化を追跡"""
        self.logger.info(f"{EMOJI['monitor']} Starting evolution tracking...")

        # 現在のスナップショットを取得
        current_snapshot = self.capture_snapshot()

        # スナップショットを保存
        snapshot_file = (
            self.evolution_db
            / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(current_snapshot, f, indent=2, ensure_ascii=False)

        # 過去のスナップショットと比較
        self._compare_with_history(current_snapshot, interval_hours)

        # 進化レポート生成
        report_path = self._generate_evolution_report()

        # 通知
        self._notify_evolution_status(current_snapshot, report_path)

        self.logger.info(f"{EMOJI['success']} Evolution tracking completed")

    def _compare_with_history(
        self, current_snapshot: Dict[str, Any], interval_hours: int
    ):
        """過去のスナップショットと比較"""
        # 過去のスナップショットを読み込み
        snapshots = []
        for snapshot_file in sorted(self.evolution_db.glob("snapshot_*.json")):
            try:
                with open(snapshot_file, "r", encoding="utf-8") as f:
                    snapshot = json.load(f)
                    snapshots.append((snapshot_file, snapshot))
            except:
                pass

        if not snapshots:
            self.logger.info("No historical snapshots found")
            return

        # 最新のスナップショットと比較
        latest_file, latest_snapshot = snapshots[-1]
        if (
            latest_file.name
            != f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ):
            comparison = self.compare_snapshots(latest_snapshot, current_snapshot)

            # 比較結果を保存
            comparison_file = (
                self.evolution_db
                / f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(comparison_file, "w", encoding="utf-8") as f:
                json.dump(comparison, f, indent=2, ensure_ascii=False)

    def _generate_evolution_report(self) -> Path:
        """進化レポートの生成"""
        self.logger.info(f"{EMOJI['file']} Generating evolution report...")

        report_path = (
            self.evolution_db
            / f"evolution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# 🌱 Elders Guild Knowledge Evolution Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # 最近の変更履歴
            f.write("## 📈 Recent Changes\n\n")

            comparisons = sorted(
                self.evolution_db.glob("comparison_*.json"), reverse=True
            )[:5]
            # 繰り返し処理
            for comp_file in comparisons:
                try:
                    with open(comp_file, "r", encoding="utf-8") as cf:
                        comp = json.load(cf)
                        f.write(f"### {comp['time_diff']} ago\n")
                        f.write(f"{comp['summary']}\n\n")

                        if not (comp["added_files"]):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if comp["added_files"]:
                            f.write("**Added Files:**\n")
                            # Deep nesting detected (depth: 6) - consider refactoring
                            for file in comp["added_files"][:5]:
                                f.write(f"- {file}\n")
                            if not (len(comp["added_files"]) > 5):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if len(comp["added_files"]) > 5:
                                f.write(
                                    f"- ... and {len(comp['added_files']) - 5} more\n"
                                )
                            f.write("\n")

                        if not (comp["modified_files"]):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if comp["modified_files"]:
                            f.write("**Modified Files:**\n")
                            # Deep nesting detected (depth: 6) - consider refactoring
                            for file in comp["modified_files"][:5]:
                                f.write(f"- {file}\n")
                            if not (len(comp["modified_files"]) > 5):
                                continue  # Early return to reduce nesting
                            # Reduced nesting - original condition satisfied
                            if len(comp["modified_files"]) > 5:
                                f.write(
                                    f"- ... and {len(comp['modified_files']) - 5} more\n"
                                )
                            f.write("\n")
                except:
                    pass

            # 成長トレンド
            f.write("## 📊 Growth Trends\n\n")
            snapshots = []
            for snapshot_file in sorted(self.evolution_db.glob("snapshot_*.json")):
                try:
                    with open(snapshot_file, "r", encoding="utf-8") as sf:
                        snapshot = json.load(sf)
                        snapshots.append(snapshot)
                except:
                    pass

            if len(snapshots) > 1:
                f.write("| Date | Workers | Managers | Commands | Total Lines |\n")
                f.write("|------|---------|----------|----------|-------------|\n")

                for snapshot in snapshots[-10:]:  # 最近10件
                    date = datetime.fromisoformat(snapshot["timestamp"]).strftime(
                        "%Y-%m-%d"
                    )
                    stats = snapshot["statistics"]
                    f.write(
                        f"| {date} | {stats.get(
                            'worker_count',
                            0)} | {stats.get('manager_count',
                            0)} | {stats.get('command_count',
                            0)} | {stats.get('total_lines',
                            0
                        ):,} |\n"
                    )

        return report_path

    def _notify_evolution_status(self, snapshot: Dict[str, Any], report_path: Path):
        """進化状況の通知"""
        try:
            from libs.slack_notifier import SlackNotifier

            notifier = SlackNotifier()

            stats = snapshot["statistics"]
            message = f"""
{EMOJI['evolution']} Elders Guild Evolution Update

📊 Current Status:
- Workers: {stats['worker_count']}
- Managers: {stats['manager_count']}
- Commands: {stats['command_count']}
- Knowledge Docs: {stats['knowledge_docs']}
- Total Lines: {stats['total_lines']:,}

📈 Evolution Report: {report_path.name}
"""
            notifier.send_message(message)

        except Exception as e:
            self.logger.warning(f"Failed to send notification: {e}")

    def visualize_evolution(self) -> Path:
        """進化の可視化（HTMLグラフ）"""
        self.logger.info(f"{EMOJI['monitor']} Creating evolution visualization...")

        # スナップショットデータの収集
        data_points = []
        for snapshot_file in sorted(self.evolution_db.glob("snapshot_*.json")):
            try:
                with open(snapshot_file, "r", encoding="utf-8") as f:
                    snapshot = json.load(f)
                    data_points.append(
                        {"date": snapshot["timestamp"], "stats": snapshot["statistics"]}
                    )
            except:
                pass

        # HTMLグラフ生成
        viz_path = (
            self.project_root
            / "web"
            / f"evolution_viz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )

        html_content = self._generate_evolution_viz_html(data_points)
        viz_path.write_text(html_content, encoding="utf-8")

        self.logger.info(f"{EMOJI['success']} Visualization created: {viz_path}")
        return viz_path

    def _generate_evolution_viz_html(self, data_points: List[Dict[str, Any]]) -> str:
        """進化可視化HTMLの生成"""
        dates = [dp["date"][:10] for dp in data_points]
        workers = [dp["stats"].get("worker_count", 0) for dp in data_points]
        managers = [dp["stats"].get("manager_count", 0) for dp in data_points]
        lines = [dp["stats"].get("total_lines", 0) for dp in data_points]

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Elders Guild Evolution Visualization</title>
    <meta charset="utf-8">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        h1 {{ color: #2c3e50; }}
        .chart {{ height: 400px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌱 Elders Guild Evolution</h1>

        <div id="componentsChart" class="chart"></div>
        <div id="linesChart" class="chart"></div>

        <script>
            // Components Chart
            var componentsData = [
                {{
                    x: {json.dumps(dates)},
                    y: {json.dumps(workers)},
                    name: 'Workers',
                    type: 'scatter',
                    mode: 'lines+markers'
                }},
                {{
                    x: {json.dumps(dates)},
                    y: {json.dumps(managers)},
                    name: 'Managers',
                    type: 'scatter',
                    mode: 'lines+markers'
                }}
            ];

            var componentsLayout = {{
                title: 'Components Growth',
                xaxis: {{ title: 'Date' }},
                yaxis: {{ title: 'Count' }}
            }};

            Plotly.newPlot('componentsChart', componentsData, componentsLayout);

            // Lines of Code Chart
            var linesData = [{{
                x: {json.dumps(dates)},
                y: {json.dumps(lines)},
                type: 'bar',
                marker: {{ color: '#3498db' }}
            }}];

            var linesLayout = {{
                title: 'Total Lines of Code',
                xaxis: {{ title: 'Date' }},
                yaxis: {{ title: 'Lines' }}
            }};

            Plotly.newPlot('linesChart', linesData, linesLayout);
        </script>
    </div>
</body>
</html>"""


if __name__ == "__main__":
    tracker = KnowledgeEvolutionTracker()
    tracker.track_evolution()
    tracker.visualize_evolution()
