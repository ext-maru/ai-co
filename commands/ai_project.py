#!/usr/bin/env python3
"""
ai-project - プロジェクト管理コマンド
既存のタスクエルダーシステムを活用したプロジェクト管理
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand
from libs.project_manager_elder import ElderGuildIntegration, ProjectManagerElder


class ProjectCommand(BaseCommand):
    """プロジェクト管理コマンド"""

    def __init__(self):
        super().__init__()
        self.pm = ProjectManagerElder()
        self.guild = ElderGuildIntegration(self.pm)

    def setup_parser(self):
        """パーサーのセットアップ"""
        parser = argparse.ArgumentParser(
            description="🏛️ エルダーズギルド プロジェクト管理システム",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用例:
  ai-project list                           # プロジェクト一覧
  ai-project create "Web Portal" --epic     # EPICプロジェクト作成
  ai-project show 1                         # プロジェクト詳細表示
  ai-project task 1 "認証システム実装"       # タスク追加
  ai-project status 1                       # プロジェクトステータス
  ai-project gantt 1                        # ガントチャート表示
  ai-project dashboard                      # Webダッシュボード起動
            """,
        )

        subparsers = parser.add_subparsers(dest="subcommand", help="サブコマンド")

        # list - プロジェクト一覧
        list_parser = subparsers.add_parser("list", help="プロジェクト一覧表示")
        list_parser.add_argument("--active", action="store_true", help="アクティブなプロジェクトのみ")
        list_parser.add_argument("--json", action="store_true", help="JSON形式で出力")

        # create - プロジェクト作成
        create_parser = subparsers.add_parser("create", help="新規プロジェクト作成")
        create_parser.add_argument("name", help="プロジェクト名")
        create_parser.add_argument("--desc", help="プロジェクトの説明")
        create_parser.add_argument("--epic", action="store_true", help="EPICランク (1ヶ月以上)")
        create_parser.add_argument("--high", action="store_true", help="HIGHランク (1-4週間)")
        create_parser.add_argument("--medium", action="store_true", help="MEDIUMランク (3-7日)")
        create_parser.add_argument("--start", help="開始日 (YYYY-MM-DD)")
        create_parser.add_argument("--end", help="終了予定日 (YYYY-MM-DD)")

        # show - プロジェクト詳細
        show_parser = subparsers.add_parser("show", help="プロジェクト詳細表示")
        show_parser.add_argument("project_id", type=int, help="プロジェクトID")

        # task - タスク管理
        task_parser = subparsers.add_parser("task", help="タスク追加")
        task_parser.add_argument("project_id", type=int, help="プロジェクトID")
        task_parser.add_argument("task_name", help="タスク名")
        task_parser.add_argument("--desc", help="タスクの説明")
        task_parser.add_argument("--priority", type=int, default=5, help="優先度 (1-10)")
        task_parser.add_argument("--hours", type=float, help="見積工数")
        task_parser.add_argument("--team", help="担当チーム")
        task_parser.add_argument("--due", help="期限 (YYYY-MM-DD)")
        task_parser.add_argument("--milestone", type=int, help="マイルストーンID")

        # milestone - マイルストーン作成
        milestone_parser = subparsers.add_parser("milestone", help="マイルストーン作成")
        milestone_parser.add_argument("project_id", type=int, help="プロジェクトID")
        milestone_parser.add_argument("name", help="マイルストーン名")
        milestone_parser.add_argument("--desc", help="説明")
        milestone_parser.add_argument("--due", help="期限 (YYYY-MM-DD)")

        # update - タスクステータス更新
        update_parser = subparsers.add_parser("update", help="タスクステータス更新")
        update_parser.add_argument("task_id", type=int, help="タスクID")
        update_parser.add_argument(
            "status", choices=["pending", "in_progress", "completed"], help="新しいステータス"
        )
        update_parser.add_argument("--comment", help="コメント")

        # status - プロジェクトステータス
        status_parser = subparsers.add_parser("status", help="プロジェクトステータス表示")
        status_parser.add_argument("project_id", type=int, help="プロジェクトID")

        # gantt - ガントチャート
        gantt_parser = subparsers.add_parser("gantt", help="ガントチャート表示")
        gantt_parser.add_argument("project_id", type=int, help="プロジェクトID")

        # stats - 統計情報
        stats_parser = subparsers.add_parser("stats", help="統計情報表示")

        # dashboard - Webダッシュボード
        dashboard_parser = subparsers.add_parser("dashboard", help="Webダッシュボード起動")
        dashboard_parser.add_argument("--port", type=int, default=5000, help="ポート番号")

        # consult - 4賢者に相談
        consult_parser = subparsers.add_parser("consult", help="4賢者に相談")
        consult_parser.add_argument("project_id", type=int, help="プロジェクトID")
        consult_parser.add_argument("--knowledge", action="store_true", help="ナレッジ賢者に相談")
        consult_parser.add_argument("--task", action="store_true", help="タスク賢者に相談")
        consult_parser.add_argument("--incident", action="store_true", help="インシデント賢者に相談")
        consult_parser.add_argument("--rag", help="RAG賢者に質問")

        return parser

    def run(self, args):
        """コマンド実行"""
        parser = self.setup_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.subcommand:
            parser.print_help()
            return 0

        # サブコマンド実行
        if parsed_args.subcommand == "list":
            return self.list_projects(parsed_args)
        elif parsed_args.subcommand == "create":
            return self.create_project(parsed_args)
        elif parsed_args.subcommand == "show":
            return self.show_project(parsed_args)
        elif parsed_args.subcommand == "task":
            return self.add_task(parsed_args)
        elif parsed_args.subcommand == "milestone":
            return self.add_milestone(parsed_args)
        elif parsed_args.subcommand == "update":
            return self.update_task(parsed_args)
        elif parsed_args.subcommand == "status":
            return self.show_status(parsed_args)
        elif parsed_args.subcommand == "gantt":
            return self.show_gantt(parsed_args)
        elif parsed_args.subcommand == "stats":
            return self.show_stats()
        elif parsed_args.subcommand == "dashboard":
            return self.start_dashboard(parsed_args)
        elif parsed_args.subcommand == "consult":
            return self.consult_sages(parsed_args)

    def list_projects(self, args):
        """プロジェクト一覧表示"""
        # 実装省略（実際にはデータベースから取得）
        self.info("📋 プロジェクト一覧")
        self.info("=" * 60)
        self.info(f"{'ID':<5} {'名前':<30} {'状態':<10} {'進捗':<10}")
        self.info("-" * 60)
        # サンプル出力
        self.info(f"1     {'エルダーズギルド Web Portal':<30} {'active':<10} {'45.5%':<10}")
        self.info(f"2     {'AI自己進化システム':<30} {'active':<10} {'82.0%':<10}")
        return 0

    def create_project(self, args):
        """プロジェクト作成"""
        # ファンタジーランクの決定
        if args.epic:
            fantasy_rank = "🏆 EPIC"
        elif args.high:
            fantasy_rank = "⭐ HIGH"
        elif args.medium:
            fantasy_rank = "🌟 MEDIUM"
        else:
            fantasy_rank = "✨ LOW"

        try:
            project_id = self.pm.create_project(
                name=args.name,
                description=args.desc,
                start_date=args.start,
                end_date=args.end,
                fantasy_rank=fantasy_rank,
            )

            self.success(f"✅ プロジェクト '{args.name}' を作成しました (ID: {project_id})")

            # 4賢者からの助言
            self.info("\n🧙‍♂️ 4賢者からの助言:")
            knowledge = self.guild.consult_knowledge_sage(project_id)
            for advice in knowledge[:2]:
                self.info(f"  📚 {advice}")

            return 0

        except Exception as e:
            self.error(f"プロジェクト作成エラー: {e}")
            return 1

    def add_task(self, args):
        """タスク追加"""
        try:
            task_id = self.pm.create_task(
                project_id=args.project_id,
                task_name=args.task_name,
                description=args.desc,
                priority=args.priority,
                estimated_hours=args.hours,
                assigned_team=args.team,
                due_date=args.due,
                milestone_id=args.milestone,
            )

            self.success(f"✅ タスク '{args.task_name}' を作成しました (ID: {task_id})")

            # インシデント賢者からのリスク警告
            if args.priority >= 7:
                self.warning("\n🚨 インシデント賢者からの警告:")
                risks = self.guild.consult_incident_sage(task_id)
                for risk in risks[:2]:
                    self.warning(f"  ⚠️  {risk['risk']} - 影響: {risk['impact']}")

            return 0

        except Exception as e:
            self.error(f"タスク作成エラー: {e}")
            return 1

    def show_gantt(self, args):
        """ガントチャート表示（簡易版）"""
        try:
            gantt_data = self.pm.get_project_gantt_data(args.project_id)

            if not gantt_data:
                self.error("プロジェクトが見つかりません")
                return 1

            self.info(f"\n📊 ガントチャート: {gantt_data['project']['name']}")
            self.info("=" * 80)

            # 簡易的なテキストベースガントチャート
            for task in gantt_data["tasks"]:
                progress_bar = self._create_progress_bar(task["completion_rate"])
                self.info(
                    f"{task['fantasy_classification']} {task['name']:<30} {progress_bar} {task['completion_rate']}%"
                )

            return 0

        except Exception as e:
            self.error(f"ガントチャート表示エラー: {e}")
            return 1

    def _create_progress_bar(self, percentage, width=20):
        """プログレスバー作成"""
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    def show_stats(self):
        """統計情報表示"""
        try:
            stats = self.pm.get_dashboard_stats()

            self.info("\n📊 エルダーズギルド プロジェクト統計")
            self.info("=" * 50)

            self.info(f"\n🏰 プロジェクト:")
            self.info(f"  総数: {stats['projects']['total']}")
            self.info(f"  アクティブ: {stats['projects']['active']}")
            self.info(f"  完了: {stats['projects']['completed']}")
            self.info(f"  平均進捗: {stats['projects']['avg_progress']:.1f}%")

            self.info(f"\n📋 タスク:")
            self.info(f"  総数: {stats['tasks']['total']}")
            self.info(f"  保留中: {stats['tasks']['pending']}")
            self.info(f"  進行中: {stats['tasks']['in_progress']}")
            self.info(f"  完了: {stats['tasks']['completed']}")
            self.info(f"  高優先度: {stats['tasks']['high_priority']}")

            self.info(f"\n🎭 ファンタジー分類 TOP5:")
            for classification, count in stats["fantasy_distribution"][:5]:
                self.info(f"  {classification}: {count}件")

            return 0

        except Exception as e:
            self.error(f"統計情報取得エラー: {e}")
            return 1

    def start_dashboard(self, args):
        """Webダッシュボード起動"""
        self.info("🌐 Webダッシュボードを起動しています...")

        try:
            import subprocess

            dashboard_path = PROJECT_ROOT / "web" / "project_dashboard.py"

            subprocess.run([sys.executable, str(dashboard_path)])

            return 0

        except Exception as e:
            self.error(f"ダッシュボード起動エラー: {e}")
            return 1

    def consult_sages(self, args):
        """4賢者に相談"""
        self.info("🧙‍♂️ 4賢者への相談")
        self.info("=" * 50)

        if args.knowledge:
            self.info("\n📚 ナレッジ賢者の助言:")
            advice = self.guild.consult_knowledge_sage(args.project_id)
            for item in advice:
                self.info(f"  • {item}")

        if args.task:
            self.info("\n📋 タスク賢者の提案:")
            plan = self.guild.consult_task_sage(args.project_id)
            self.info(f"  クリティカルパス: {' → '.join(plan['critical_path'])}")
            self.info(f"  推定期間: {plan['estimated_duration']}")

        if args.incident:
            self.info("\n🚨 インシデント賢者のリスク分析:")
            risks = self.guild.consult_incident_sage(0)  # プロジェクト全体のリスク
            for risk in risks:
                self.info(
                    f"  • {risk['risk']} (確率: {risk['probability']*100:.0f}%, 影響: {risk['impact']})"
                )
                self.info(f"    対策: {risk['mitigation']}")

        if args.rag:
            self.info(f"\n🔍 RAG賢者への質問: {args.rag}")
            answer = self.guild.consult_rag_sage(args.rag)
            self.info(f"  {answer}")

        return 0


def main():
    """メインエントリーポイント"""
    command = ProjectCommand()
    return command.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
