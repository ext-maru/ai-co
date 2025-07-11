#!/usr/bin/env python3
"""
ai-project-template - プロジェクトテンプレート管理コマンド
エルダーズギルド プロジェクトテンプレートシステムのCLIインターフェース
"""

import argparse
import json
import sys
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand
from libs.project_template_system import ProjectTemplateSystem, ProjectTemplateCLI


class ProjectTemplateCommand(BaseCommand):
    """プロジェクトテンプレート管理コマンド"""

    def __init__(self):
        super().__init__()
        self.cli = ProjectTemplateCLI()

    def setup_parser(self):
        """パーサーのセットアップ"""
        parser = argparse.ArgumentParser(
            description="🏛️ エルダーズギルド プロジェクトテンプレートシステム",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用例:
  ai-project-template templates                    # テンプレート一覧
  ai-project-template create "新プロジェクト" web_development  # プロジェクト作成
  ai-project-template list                         # プロジェクト一覧
  ai-project-template status project_20250710_123456  # 状況確認
  ai-project-template advance project_20250710_123456  # フェーズ進行
  ai-project-template context project_20250710_123456  # コンテキスト表示
            """,
        )

        subparsers = parser.add_subparsers(dest="subcommand", help="サブコマンド")

        # templates - テンプレート一覧
        templates_parser = subparsers.add_parser("templates", help="利用可能なテンプレート一覧")

        # create - プロジェクト作成
        create_parser = subparsers.add_parser("create", help="テンプレートからプロジェクト作成")
        create_parser.add_argument("project_name", help="プロジェクト名")
        create_parser.add_argument("template_name", help="テンプレート名")
        create_parser.add_argument("--context", help="初期コンテキスト（JSON形式）")

        # list - プロジェクト一覧
        list_parser = subparsers.add_parser("list", help="プロジェクト一覧")

        # status - プロジェクト状況
        status_parser = subparsers.add_parser("status", help="プロジェクト状況表示")
        status_parser.add_argument("project_id", help="プロジェクトID")

        # advance - フェーズ進行
        advance_parser = subparsers.add_parser("advance", help="フェーズ進行")
        advance_parser.add_argument("project_id", help="プロジェクトID")
        advance_parser.add_argument("--context", help="進行時のコンテキスト（JSON形式）")

        # context - コンテキスト表示
        context_parser = subparsers.add_parser("context", help="プロジェクトコンテキスト表示")
        context_parser.add_argument("project_id", help="プロジェクトID")
        context_parser.add_argument("--format", choices=["text", "json"], default="text", help="出力形式")

        # consult - 4賢者への相談
        consult_parser = subparsers.add_parser("consult", help="4賢者への相談")
        consult_parser.add_argument("project_id", help="プロジェクトID")
        consult_parser.add_argument("--knowledge", action="store_true", help="ナレッジ賢者に相談")
        consult_parser.add_argument("--task", action="store_true", help="タスク賢者に相談")
        consult_parser.add_argument("--incident", action="store_true", help="インシデント賢者に相談")
        consult_parser.add_argument("--rag", help="RAG賢者に質問")

        # checklist - チェックリスト管理
        checklist_parser = subparsers.add_parser("checklist", help="チェックリスト管理")
        checklist_parser.add_argument("project_id", help="プロジェクトID")
        checklist_parser.add_argument("--check", type=int, help="チェック項目番号")
        checklist_parser.add_argument("--uncheck", type=int, help="チェック解除項目番号")

        return parser

    def run(self, args):
        """コマンド実行"""
        parser = self.setup_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.subcommand:
            parser.print_help()
            return 0

        # サブコマンド実行
        if parsed_args.subcommand == "templates":
            return self.list_templates()
        elif parsed_args.subcommand == "create":
            return self.create_project(parsed_args)
        elif parsed_args.subcommand == "list":
            return self.list_projects()
        elif parsed_args.subcommand == "status":
            return self.show_project_status(parsed_args)
        elif parsed_args.subcommand == "advance":
            return self.advance_project_phase(parsed_args)
        elif parsed_args.subcommand == "context":
            return self.show_project_context(parsed_args)
        elif parsed_args.subcommand == "consult":
            return self.consult_sages(parsed_args)
        elif parsed_args.subcommand == "checklist":
            return self.manage_checklist(parsed_args)

    def list_templates(self):
        """テンプレート一覧表示"""
        self.info("🏛️ エルダーズギルド プロジェクトテンプレート一覧")
        self.info("=" * 60)

        self.cli.list_templates()

        self.info("\n💡 使用方法:")
        self.info("  ai-project-template create \"プロジェクト名\" template_name")
        self.info("\n例:")
        self.info("  ai-project-template create \"新しいWebアプリ\" web_development")
        return 0

    def create_project(self, args):
        """プロジェクト作成"""
        context_data = None
        if args.context:
            try:
                context_data = json.loads(args.context)
            except json.JSONDecodeError:
                self.error("無効なJSON形式です")
                return 1

        self.info("🏛️ プロジェクトテンプレートからプロジェクトを作成中...")
        project_id = self.cli.create_project(args.project_name, args.template_name)

        if project_id:
            self.success(f"✅ プロジェクト作成完了！")
            self.info(f"📋 プロジェクトID: {project_id}")
            self.info(f"💡 状況確認: ai-project-template status {project_id}")
            self.info(f"🚀 フェーズ進行: ai-project-template advance {project_id}")
            return 0
        else:
            self.error("❌ プロジェクト作成に失敗しました")
            return 1

    def list_projects(self):
        """プロジェクト一覧表示"""
        self.info("🏛️ プロジェクト一覧")
        self.cli.list_projects()
        return 0

    def show_project_status(self, args):
        """プロジェクト状況表示"""
        self.info("🏛️ プロジェクト状況レポート")
        self.info("=" * 60)
        self.cli.show_project_status(args.project_id)
        return 0

    def advance_project_phase(self, args):
        """フェーズ進行"""
        context_data = None
        if args.context:
            try:
                context_data = json.loads(args.context)
            except json.JSONDecodeError:
                self.error("無効なJSON形式です")
                return 1

        self.info(f"🚀 フェーズを進行中: {args.project_id}")
        self.cli.advance_project_phase(args.project_id)
        return 0

    def show_project_context(self, args):
        """プロジェクトコンテキスト表示"""
        context = self.cli.system.get_project_context(args.project_id)

        if not context:
            self.error("プロジェクトが見つかりません")
            return 1

        if args.format == "json":
            # JSON形式で出力（継続性のため）
            print(json.dumps(context, indent=2, default=str, ensure_ascii=False))
        else:
            # 人間が読みやすい形式で出力
            self.info("🏛️ プロジェクトコンテキスト")
            self.info("=" * 60)

            project_info = context['project_info']
            self.info(f"📋 プロジェクト: {project_info['project_name']}")
            self.info(f"🆔 ID: {project_info['project_id']}")
            self.info(f"📄 テンプレート: {project_info['template_name']}")
            self.info(f"📊 現在のフェーズ: {project_info['current_phase']}")
            self.info(f"⏰ 最終更新: {project_info['updated_at']}")

            # 現在のタスク
            current_tasks = context['current_phase_tasks']
            if current_tasks:
                self.info(f"\n🎯 現在のタスク:")
                for i, task in enumerate(current_tasks, 1):
                    self.info(f"  {i}. {task}")

            # チェックリスト
            checklist = context['checklist']
            if checklist:
                self.info(f"\n✅ チェックリスト:")
                for i, item in enumerate(checklist, 1):
                    self.info(f"  {i}. [ ] {item}")

            # エルダー相談
            consultations = context['elder_consultations']
            if consultations:
                self.info(f"\n🧙‍♂️ エルダー相談事項:")
                for consul in consultations:
                    self.info(f"  • {consul['sage_type']}: {consul['prompt']}")

            # 継続性ログ
            continuity_log = context['continuity_log']
            if continuity_log:
                self.info(f"\n📈 最近のアクティビティ:")
                for log in continuity_log[:3]:
                    self.info(f"  • {log['timestamp']}: {log['action']}")

        return 0

    def consult_sages(self, args):
        """4賢者への相談"""
        context = self.cli.system.get_project_context(args.project_id)

        if not context:
            self.error("プロジェクトが見つかりません")
            return 1

        self.info("🧙‍♂️ 4賢者への相談")
        self.info("=" * 50)

        project_info = context['project_info']
        self.info(f"📋 プロジェクト: {project_info['project_name']}")
        self.info(f"📊 現在のフェーズ: {project_info['current_phase']}")

        # 自動相談事項を表示
        consultations = context['elder_consultations']
        if consultations:
            self.info(f"\n🤖 自動相談事項:")
            for consul in consultations:
                self.info(f"  🧙‍♂️ {consul['sage_type']}: {consul['prompt']}")

        # 手動相談
        if args.knowledge:
            self.info("\n📚 ナレッジ賢者への相談:")
            self.info("  • 過去の類似プロジェクトの経験を参考にしてください")
            self.info("  • 技術選定の判断材料を提供します")

        if args.task:
            self.info("\n📋 タスク賢者への相談:")
            self.info("  • 現在のフェーズに最適なタスク実行順序を提案します")
            self.info("  • 並列実行可能なタスクを特定します")

        if args.incident:
            self.info("\n🚨 インシデント賢者への相談:")
            self.info("  • 潜在的なリスクを予測し、対策を提案します")
            self.info("  • 過去のインシデントから学習した注意点を共有します")

        if args.rag:
            self.info(f"\n🔍 RAG賢者への質問: {args.rag}")
            self.info("  • 最新の技術情報とベストプラクティスを調査します")
            self.info("  • 具体的な実装方法を提案します")

        return 0

    def manage_checklist(self, args):
        """チェックリスト管理"""
        context = self.cli.system.get_project_context(args.project_id)

        if not context:
            self.error("プロジェクトが見つかりません")
            return 1

        checklist = context['checklist']
        if not checklist:
            self.info("現在のフェーズにはチェックリストがありません")
            return 0

        self.info("✅ チェックリスト管理")
        self.info("=" * 50)

        # チェックリストを表示
        for i, item in enumerate(checklist, 1):
            status = "☑️" if args.check == i else "☐"
            self.info(f"  {i}. {status} {item}")

        if args.check:
            self.success(f"✅ 項目 {args.check} をチェックしました")
        elif args.uncheck:
            self.info(f"☐ 項目 {args.uncheck} のチェックを解除しました")

        return 0


def main():
    """メインエントリーポイント"""
    command = ProjectTemplateCommand()
    return command.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
