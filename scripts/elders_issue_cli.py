#!/usr/bin/env python3
"""
エルダーズギルド Issue管理 CLI
GitHub Issue完全自動化のためのコマンドラインツール
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.integrations.github.elders_issue_manager import EldersIssueManager


class EldersIssueCLI:
    """エルダーズギルド Issue管理CLI"""

    def __init__(self):
        self.manager = None

    async def initialize(self, repo_name: str):
        """マネージャーを初期化"""
        self.manager = EldersIssueManager()
        self.manager.set_repository(repo_name)

    async def create_epic_structure(self, args):
        """Epic構造を作成"""
        issue = self.manager.repo.get_issue(args.issue)

        # チェックリストを含むテンプレートを作成
        if not issue.body or "- [ ]" not in issue.body:
            template = """
## 📋 Tasks

- [ ] 要件定義と設計
- [ ] 基本実装
- [ ] テスト作成
- [ ] ドキュメント作成
- [ ] レビューと修正

## 📊 Progress: 0%
[░░░░░░░░░░] 0/5 completed
"""
            issue.edit(body=(issue.body or "") + template)
            print(f"✅ Added task checklist to Issue #{args.issue}")

        # Sub Issue作成
        sub_issues = await self.manager.create_sub_issues_from_epic(issue)
        print(f"📋 Created {len(sub_issues)} sub-issues from Epic #{args.issue}")

        for sub in sub_issues:
            print(f"  → #{sub.number}: {sub.title}")

    async def sync_all_issues(self, args):
        """全Issueを4賢者と同期"""
        issues = list(self.manager.repo.get_issues(state="open"))
        total = len(issues)

        print(f"🔄 Syncing {total} open issues with 4 Sages...")

        for i, issue in enumerate(issues, 1):
            await self.manager.sync_with_four_sages(issue)
            print(f"  [{i}/{total}] Synced Issue #{issue.number}: {issue.title}")

        print("✅ Sync completed!")

    async def generate_report(self, args):
        """レポートを生成"""
        report = await self.manager.generate_daily_report()

        if args.format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            # Markdown形式で出力
            print(f"# 📊 Issue Management Report - {report['date']}")
            print()
            print("## 📈 Summary")
            print(f"- **Opened Issues**: {report['summary']['opened_issues']}")
            print(f"- **Closed Issues**: {report['summary']['closed_issues']}")
            print(f"- **Active Issues**: {report['summary']['active_issues']}")
            print(f"- **Completion Rate**: {report['metrics']['completion_rate']:.1f}%")
            print()

            if report.get("sage_insights"):
                print("## 🧙‍♂️ 4賢者の洞察")
                for sage, insights in report["sage_insights"].items():
                    print(f"\n### {sage.title()} Sage")
                    print(json.dumps(insights, indent=2, ensure_ascii=False))

    async def auto_assign(self, args):
        """自動アサイン"""
        if args.issue:
            # 特定のIssue
            issue = self.manager.repo.get_issue(args.issue)
            await self.manager.auto_assign_to_servants(issue)
            print(f"✅ Auto-assigned Issue #{args.issue}")
        else:
            # 全ての未アサインIssue
            unassigned = [
                i
                for i in self.manager.repo.get_issues(state="open")
                if not any(
                    l.name.endswith("-workshop")
                    or l.name.endswith("-knights")
                    or l.name.endswith("-wizards")
                    or l.name.endswith("-forest")
                    for l in i.labels
                )
            ]

            print(f"🤖 Auto-assigning {len(unassigned)} unassigned issues...")

            for issue in unassigned:
                await self.manager.auto_assign_to_servants(issue)
                print(f"  → Assigned Issue #{issue.number}")

    async def update_progress(self, args):
        """進捗を更新"""
        issue = self.manager.repo.get_issue(args.issue)
        await self.manager.update_progress_chart(issue)
        print(f"📊 Updated progress for Issue #{args.issue}")

    async def check_pr_issues(self, args):
        """PRの関連Issueをチェック"""
        pr = self.manager.repo.get_pull(args.pr)

        if pr.merged:
            await self.manager.handle_pr_merge(pr)
            print(f"✅ Processed merged PR #{args.pr}")
        else:
            print(f"ℹ️ PR #{args.pr} is not merged yet")

    async def interactive_mode(self, args):
        """対話モード"""
        print("🤖 Elders Guild Issue Manager - Interactive Mode")
        print("Type 'help' for available commands, 'exit' to quit")

        while True:
            try:
                command = input("\n> ").strip()

                if command == "exit":
                    break
                elif command == "help":
                    print(
                        """
Available commands:
  sync          - Sync all issues with 4 Sages
  report        - Generate daily report
  assign        - Auto-assign unassigned issues
  epic <#>      - Create sub-issues from epic
  progress <#>  - Update issue progress
  pr <#>        - Check PR related issues
  status        - Show current status
  exit          - Exit interactive mode
"""
                    )
                elif command == "sync":
                    await self.sync_all_issues(args)
                elif command == "report":
                    await self.generate_report(args)
                elif command == "assign":
                    await self.auto_assign(args)
                elif command.startswith("epic "):
                    issue_num = int(command.split()[1].strip("#"))
                    args.issue = issue_num
                    await self.create_epic_structure(args)
                elif command.startswith("progress "):
                    issue_num = int(command.split()[1].strip("#"))
                    args.issue = issue_num
                    await self.update_progress(args)
                elif command.startswith("pr "):
                    pr_num = int(command.split()[1].strip("#"))
                    args.pr = pr_num
                    await self.check_pr_issues(args)
                elif command == "status":
                    # 簡易ステータス表示
                    open_issues = self.manager.repo.get_issues(state="open").totalCount
                    print(f"📊 Repository: {args.repo}")
                    print(f"📋 Open Issues: {open_issues}")
                else:
                    print(f"❌ Unknown command: {command}")

            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


async def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="🤖 Elders Guild Issue Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --repo owner/repo sync
  %(prog)s --repo owner/repo report --format markdown
  %(prog)s --repo owner/repo epic --issue 123
  %(prog)s --repo owner/repo auto-assign
  %(prog)s --repo owner/repo interactive
""",
    )

    parser.add_argument(
        "--repo", "-r", required=True, help="GitHub repository (owner/repo format)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # sync コマンド
    sync_parser = subparsers.add_parser("sync", help="Sync issues with 4 Sages")

    # report コマンド
    report_parser = subparsers.add_parser("report", help="Generate daily report")
    report_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format",
    )

    # epic コマンド
    epic_parser = subparsers.add_parser("epic", help="Create sub-issues from epic")
    epic_parser.add_argument(
        "--issue", "-i", type=int, required=True, help="Epic issue number"
    )

    # auto-assign コマンド
    assign_parser = subparsers.add_parser("auto-assign", help="Auto-assign to servants")
    assign_parser.add_argument(
        "--issue", "-i", type=int, help="Specific issue number (optional)"
    )

    # progress コマンド
    progress_parser = subparsers.add_parser("progress", help="Update issue progress")
    progress_parser.add_argument(
        "--issue", "-i", type=int, required=True, help="Issue number"
    )

    # pr-check コマンド
    pr_parser = subparsers.add_parser("pr-check", help="Check PR related issues")
    pr_parser.add_argument(
        "--pr", "-p", type=int, required=True, help="Pull request number"
    )

    # interactive コマンド
    interactive_parser = subparsers.add_parser("interactive", help="Interactive mode")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # CLIを初期化
    cli = EldersIssueCLI()
    await cli.initialize(args.repo)

    # コマンドを実行
    if args.command == "sync":
        await cli.sync_all_issues(args)
    elif args.command == "report":
        await cli.generate_report(args)
    elif args.command == "epic":
        await cli.create_epic_structure(args)
    elif args.command == "auto-assign":
        await cli.auto_assign(args)
    elif args.command == "progress":
        await cli.update_progress(args)
    elif args.command == "pr-check":
        await cli.check_pr_issues(args)
    elif args.command == "interactive":
        await cli.interactive_mode(args)


if __name__ == "__main__":
    asyncio.run(main())
