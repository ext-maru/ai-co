#!/usr/bin/env python3
"""
Elders Guild - 統計情報表示コマンド
"""

import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# プロジェクトルートをsys.pathに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand, CommandResult

sys.path.insert(0, "/root/ai_co")
import sqlite3

from features.database.task_history_db import TaskHistoryDB

console = Console()


class AIStatsCommand(BaseCommand):
    """統計情報表示コマンド"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="stats", description="Elders Guild システムの統計情報を表示")

    def setup_arguments(self):
        """引数定義"""
        self.parser.add_argument(
            "--period",
            "-p",
            choices=["today", "week", "month", "all"],
            default="all",
            help="統計期間",
        )
        self.parser.add_argument(
            "--format", "-f", choices=["table", "json"], default="table", help="出力形式"
        )
        self.parser.add_argument("--debug", action="store_true", help="デバッグモード")

    def execute(self, args):
        """コマンド実行"""
        try:
            # DB接続
            db = TaskHistoryDB()

            # 期間のフィルタリング用の日付を計算
            now = datetime.now()
            if args.period == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif args.period == "week":
                start_date = now - timedelta(days=7)
            elif args.period == "month":
                start_date = now - timedelta(days=30)
            else:  # all
                start_date = None

            # 統計情報取得
            stats = self._get_period_stats(db, start_date)

            if args.format == "json":
                import json

                print(json.dumps(stats, indent=2, ensure_ascii=False))
            else:
                self._display_stats_table(stats, args.period)

            return CommandResult(success=True)

        except Exception as e:
            # Handle specific exception case
            if args.debug:
                import traceback

                traceback.print_exc()
            return CommandResult(success=False, message=f"統計情報の取得に失敗: {str(e)}")

    def _get_period_stats(self, db, start_date):
        """期間別の統計情報を取得"""
        try:
            with sqlite3.connect(db.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # 基本的なクエリ
                query = "SELECT * FROM task_history"
                params = []

                if start_date:
                    query += " WHERE created_at >= ?"
                    params.append(start_date.isoformat())

                cursor = conn.execute(query, params)
                tasks = [dict(row) for row in cursor.fetchall()]

                # 統計計算
                total_tasks = len(tasks)
                completed_tasks = sum(
                    1 for t in tasks if t.get("status") == "completed"
                )
                failed_tasks = sum(1 for t in tasks if t.get("status") == "failed")

                # ワーカー別統計
                worker_counts = Counter(t.get("worker", "unknown") for t in tasks)

                # タスクタイプ別統計
                type_counts = Counter(t.get("task_type", "general") for t in tasks)

                # モデル別統計
                model_counts = Counter(t.get("model", "unknown") for t in tasks)

                # 要約済みタスク数
                summarized_tasks = sum(1 for t in tasks if t.get("summary"))

                # 平均応答長
                response_lengths = [len(t.get("response", "")) for t in tasks]
                avg_response_length = (
                    sum(response_lengths) / len(response_lengths)
                    if response_lengths
                    else 0
                )

                return {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "success_rate": (completed_tasks / total_tasks * 100)
                    if total_tasks > 0
                    else 0,
                    "summarized_tasks": summarized_tasks,
                    "avg_response_length": avg_response_length,
                    "worker_stats": dict(worker_counts),
                    "type_stats": dict(type_counts),
                    "model_stats": dict(model_counts),
                    "tasks": tasks,
                }

        except Exception as e:
            # Handle specific exception case
            console.print(f"[yellow]⚠️  統計取得エラー: {str(e)}[/yellow]")
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "success_rate": 0,
                "summarized_tasks": 0,
                "avg_response_length": 0,
                "worker_stats": {},
                "type_stats": {},
                "model_stats": {},
                "tasks": [],
            }

    def _display_stats_table(self, stats, period):
        """統計情報をテーブル形式で表示"""
        period_text = {"today": "今日", "week": "過去7日間", "month": "過去30日間", "all": "全期間"}[
            period
        ]

        # サマリーパネル
        summary = f"""
[cyan]期間:[/cyan] {period_text}
[cyan]総タスク数:[/cyan] {stats['total_tasks']}
[cyan]完了タスク:[/cyan] {stats['completed_tasks']}
[cyan]失敗タスク:[/cyan] {stats['failed_tasks']}
[cyan]成功率:[/cyan] {stats['success_rate']:.1f}%
[cyan]要約済み:[/cyan] {stats['summarized_tasks']}
[cyan]平均応答長:[/cyan] {stats['avg_response_length']:.0f} 文字
"""
        console.print(Panel(summary.strip(), title="📊 Elders Guild 統計情報", expand=False))

        # ワーカー別統計
        if stats["worker_stats"]:
            worker_table = Table(title="👷 ワーカー別統計")
            worker_table.add_column("ワーカー", style="cyan")
            worker_table.add_column("タスク数", justify="right")
            worker_table.add_column("割合", justify="right")

            total = stats["total_tasks"]
            for worker, count in sorted(
                stats["worker_stats"].items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (count / total * 100) if total > 0 else 0
                worker_table.add_row(worker, str(count), f"{percentage:.1f}%")

            console.print(worker_table)

        # タスクタイプ別統計
        if stats["type_stats"]:
            type_table = Table(title="📝 タスクタイプ別統計")
            type_table.add_column("タイプ", style="green")
            type_table.add_column("タスク数", justify="right")
            type_table.add_column("割合", justify="right")

            total = stats["total_tasks"]
            for task_type, count in sorted(
                stats["type_stats"].items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (count / total * 100) if total > 0 else 0
                type_table.add_row(task_type, str(count), f"{percentage:.1f}%")

            console.print(type_table)


def main():
    """メイン関数"""
    command = AIStatsCommand()
    return command.run()


if __name__ == "__main__":
    sys.exit(main())
