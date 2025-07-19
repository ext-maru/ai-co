#!/usr/bin/env python3
"""
RAG検索
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from commands.base_command import BaseCommand, CommandResult
from libs.github_aware_rag import GitHubAwareRAGManager
from libs.process_monitor import ProcessMonitor


class AIRAGSearchCommand(BaseCommand):
    """RAG検索コマンド"""

    def __init__(self):
        super().__init__(name="ai-rag-search", description="RAG検索", version="1.0.0")
        self.console = Console()

    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument("query", help="検索クエリ")
        self.parser.add_argument(
            "--limit", "-l", type=int, default=5, help="検索結果数（デフォルト: 5）"
        )
        self.parser.add_argument(
            "--include-code", "-c", action="store_true", help="GitHubコードも含める"
        )
        self.parser.add_argument("--json", action="store_true", help="JSON形式で出力")

    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            # プロセス監視による安全性チェック
            monitor = ProcessMonitor(max_processes=8, max_memory_mb=800)
            health = monitor.check_system_health()
            if not health["healthy"]:
                return CommandResult(
                    success=False, message=f"システム異常検出: {health['issues']}"
                )

            rag = GitHubAwareRAGManager()

            # 検索実行
            if args.include_code:
                context = rag.build_context_with_github(
                    args.query, include_code=True, max_tasks=args.limit
                )
            else:
                similar_tasks = rag.search_similar_tasks(args.query, limit=args.limit)
                context = rag._format_similar_tasks(similar_tasks)

            if args.json:
                import json

                return CommandResult(
                    success=True,
                    message=json.dumps(
                        {
                            "query": args.query,
                            "context": context,
                            "result_count": context.count("Task ID:"),
                        },
                        indent=2,
                    ),
                )

            # リッチ表示
            self.console.print(
                Panel(
                    f"[bold cyan]検索クエリ:[/bold cyan] {args.query}",
                    title="🔍 RAG検索",
                    border_style="blue",
                )
            )

            if context:
                # 各タスクをパネルで表示
                tasks = context.split("\n\n")
                for i, task in enumerate(tasks):
                    if task.strip():
                        # コード部分をハイライト
                        if "```" in task:
                            parts = task.split("```")
                            self.console.print(parts[0])
                            if len(parts) > 1:
                                code = parts[1].strip()
                                lang = code.split("\n")[0] if "\n" in code else "python"
                                code_content = (
                                    "\n".join(code.split("\n")[1:])
                                    if "\n" in code
                                    else code
                                )
                                self.console.print(
                                    Syntax(code_content, lang, theme="monokai")
                                )
                        else:
                            self.console.print(task)

                        if i < len(tasks) - 1:
                            self.console.print("─" * 40, style="dim")
            else:
                self.console.print("[yellow]関連するタスクが見つかりませんでした[/yellow]")

            return CommandResult(success=True)

        except Exception as e:
            return CommandResult(success=False, message=f"RAG検索エラー: {str(e)}")


def main():
    command = AIRAGSearchCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
