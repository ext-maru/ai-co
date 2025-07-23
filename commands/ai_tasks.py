#!/usr/bin/env python3
"""
Elders Guild - タスク管理コマンド
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# プロジェクトルートをsys.pathに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand, CommandResult

# PostgreSQL移行対応: 新しいタスクトラッカーを使用
try:
    # 新しいPostgreSQLタスクトラッカーを優先使用
    from libs.claude_task_tracker import ClaudeTaskTracker
    USE_POSTGRES = True
except ImportError:
    # フォールバック: 旧SQLite版
    sys.path.insert(0, "/root/ai_co")
    from features.database.task_history_db import TaskHistoryDB
    USE_POSTGRES = False

console = Console()


class AITasksCommand(BaseCommand):
    """タスク管理コマンド"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="tasks", description="Elders Guild タスクの管理")

    def setup_arguments(self):
        """引数定義"""
        self.parser.add_argument("--limit", "-l", type=int, default=10, help="表示件数")
        self.parser.add_argument(
            "--type",
            "-t",
            choices=["all", "code", "general", "dialog"],
            default="all",
            help="タスクタイプ",
        )
        self.parser.add_argument("--search", "-s", help="検索キーワード")
        self.parser.add_argument("--id", help="タスクIDで詳細表示")
        self.parser.add_argument(
            "--format",
            "-f",
            choices=["table", "json", "detail"],
            default="table",
            help="出力形式",
        )
        self.parser.add_argument("--debug", action="store_true", help="デバッグモード")

    def execute(self, args):
        """コマンド実行"""
        try:
            if USE_POSTGRES:
                # PostgreSQL版タスクトラッカー使用
                return self._execute_postgres(args)
            else:
                # 旧SQLite版タスクトラッカー使用
                return self._execute_sqlite(args)
        except Exception as e:
            # Handle specific exception case
            console.print(f"❌ エラー: {e}", style="red")
            return CommandResult(success=False, message=str(e))

    def _execute_postgres(self, args):
        """PostgreSQL版での実行"""
        import asyncio
        
        async def async_execute():
            # Core functionality implementation
            from libs.postgres_claude_task_tracker import create_postgres_task_tracker
            
            tracker = await create_postgres_task_tracker()
            
            try:
                if args.id:
                    # 特定タスクの詳細表示
                    task = await tracker.get_task(args.id)
                    if task:
                        self._show_postgres_task_detail(task, args.format)
                    else:
                        console.print(f"❌ タスクが見つかりません: {args.id}", style="red")
                    return CommandResult(success=True)
                else:
                    # タスクリスト取得
                    tasks = await tracker.list_tasks(limit=args.limit)
                    
                    # 検索フィルタ
                    if args.search:
                        tasks = [t for t in tasks if args.search.lower(
                            ) in t.get('name',
                            '').lower(
                        ) 
                                or args.search.lower() in t.get('description', '').lower()]
                    
                    # タイプフィルタ
                    if args.type != "all":
                        tasks = [t for t in tasks if t.get("task_type") == args.type]
                    
                    self._display_postgres_tasks(tasks, args.format)
                    return CommandResult(success=True)
            finally:
                await tracker.close()
        
        return asyncio.run(async_execute())

    def _execute_sqlite(self, args):
        """SQLite版での実行（レガシー）"""
        db = TaskHistoryDB()

        if args.id:
            # 特定タスクの詳細表示
            return self._show_task_detail(db, args.id, args.format)
        elif args.search:
            # 検索
            tasks = db.search_tasks(keyword=args.search, limit=args.limit)
        else:
            # 最新タスク取得
            tasks = db.get_recent_tasks(limit=args.limit)

            # タイプでフィルタリング
            if args.type != "all":
                tasks = [t for t in tasks if t.get("task_type") == args.type]

        # 表示
        if args.format == "json":
            import json
            print(json.dumps(tasks, indent=2, ensure_ascii=False, default=str))
        elif args.format == "detail":
            self._show_tasks_detail(tasks)
        else:
            self._show_tasks_table(tasks)

        return CommandResult(success=True)

    def _show_tasks_table(self, tasks):
        """タスク一覧をテーブル表示"""
        table = Table(title="📋 Elders Guild タスク履歴")
        table.add_column("タスクID", style="cyan", width=25)
        table.add_column("タイプ", style="magenta", width=10)
        table.add_column("ワーカー", style="green", width=15)
        table.add_column("状態", justify="center", width=10)
        table.add_column("作成日時", style="white", width=20)
        table.add_column("プロンプト", style="white", width=40)

        for task in tasks:
            # Process each item in collection
            status = task.get("status", "unknown")
            if status == "completed":
                status_text = "[green]✅[/green]"
            elif status == "failed":
                status_text = "[red]❌[/red]"
            else:
                status_text = "[yellow]⏳[/yellow]"

            # プロンプトを短縮
            prompt = task.get("prompt", "")
            if len(prompt) > 37:
                prompt = prompt[:37] + "..."

            # 作成日時をフォーマット
            created_at = task.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace("T", " "))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass

            table.add_row(
                task.get("task_id", ""),
                task.get("task_type", "general"),
                task.get("worker", ""),
                status_text,
                created_at,
                prompt,
            )

        console.print(table)

        if not tasks:
            console.print("[yellow]📭 タスクが見つかりません[/yellow]")

    def _display_postgres_tasks(self, tasks, format_type):
        """PostgreSQL版タスク表示"""
        if format_type == "json":
            import json
            print(json.dumps(tasks, indent=2, ensure_ascii=False, default=str))
            return

        # テーブル表示
        table = Table(title="🏛️ エルダーズギルド PostgreSQL タスク管理")
        table.add_column("タスクID", style="cyan", width=25)
        table.add_column("タイトル", style="bright_white", width=30)
        table.add_column("タイプ", style="magenta", width=12)
        table.add_column("優先度", style="yellow", width=8)
        table.add_column("状態", justify="center", width=10)
        table.add_column("担当者", style="green", width=15)
        table.add_column("作成日時", style="white", width=16)

        for task in tasks:
            # Process each item in collection
            status = task.get("status", "unknown")
            if status == "completed":
                status_text = "[green]✅ 完了[/green]"
            elif status == "failed":
                status_text = "[red]❌ 失敗[/red]"
            elif status == "in_progress":
                status_text = "[blue]🔄 実行中[/blue]"
            else:
                status_text = "[yellow]⏳ 待機[/yellow]"

            # タイトルを短縮
            title = task.get("name", "")
            if len(title) > 27:
                title = title[:27] + "..."

            # 作成日時をフォーマット
            created_at = task.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.fromisoformat(str(created_at).replace("T", " "))
                    created_at = dt.strftime("%m-%d %H:%M")
                except:
                    created_at = str(created_at)[:16]

            # 優先度の色付け
            priority = task.get("priority", "medium")
            if priority == "critical":
                priority_text = "[red bold]🔥 CRIT[/red bold]"
            elif priority == "high":
                priority_text = "[orange3]⬆️ HIGH[/orange3]"
            elif priority == "low":
                priority_text = "[dim]⬇️ LOW[/dim]"
            else:
                priority_text = "[white]➡️ MED[/white]"

            table.add_row(
                task.get("task_id", "")[:8] + "...",
                title,
                task.get("task_type", "unknown"),
                priority_text,
                status_text,
                task.get("assignee", "-"),
                created_at,
            )

        console.print(table)

        if not tasks:
            console.print("[yellow]📭 PostgreSQLタスクが見つかりません[/yellow]")

    def _show_postgres_task_detail(self, task, format_type):
        """PostgreSQL版タスク詳細表示"""
        if format_type == "json":
            import json
            print(json.dumps(task, indent=2, ensure_ascii=False, default=str))
            return

        # 詳細パネル表示
        status = task.get("status", "unknown")
        if status == "completed":
            status_emoji = "✅"
            status_color = "green"
        elif status == "failed":
            status_emoji = "❌"
            status_color = "red"
        elif status == "in_progress":
            status_emoji = "🔄"
            status_color = "blue"
        else:
            status_emoji = "⏳"
            status_color = "yellow"

        panel_content = f"""
[bright_white]📋 タスク名:[/bright_white] {task.get('name', 'N/A')}
[bright_white]🆔 タスクID:[/bright_white] {task.get('task_id', 'N/A')}
[bright_white]📝 説明:[/bright_white] {task.get('description', 'なし')}
[bright_white]🏷️  タイプ:[/bright_white] {task.get('task_type', 'unknown')}
[bright_white]⭐ 優先度:[/bright_white] {task.get('priority', 'medium')}
[bright_white]👤 担当者:[/bright_white] {task.get('assignee', '未割当')}
[bright_white]📊 進捗:[/bright_white] {task.get('progress', 0)*100:.1f}%
[bright_white]📅 作成日時:[/bright_white] {task.get('created_at', 'N/A')}
[bright_white]🔄 更新日時:[/bright_white] {task.get('updated_at', 'N/A')}
"""

        if task.get('result'):
            panel_content += f"[bright_white]💾 結果:[/bright_white] {task.get('result')}\n"

        if task.get('tags'):
            tags = ", ".join(task.get('tags', []))
            panel_content += f"[bright_white]🏷️  タグ:[/bright_white] {tags}\n"

        panel = Panel(
            panel_content.strip(),
            title=f"{status_emoji} タスク詳細",
            border_style=status_color,
            expand=False
        )

        console.print(panel)

    def _show_tasks_detail(self, tasks):
        """タスク詳細表示"""
        for task in tasks:
            # Process each item in collection
            self._display_task_panel(task)
            console.print()

    def _show_task_detail(self, db, task_id, format):
        """特定タスクの詳細表示"""
        task = db.get_task_by_id(task_id)

        if not task:
            return CommandResult(success=False, message=f"タスクID '{task_id}' が見つかりません")

        if format == "json":
            print(json.dumps(task, indent=2, ensure_ascii=False, default=str))
        else:
            self._display_task_panel(task)

        return CommandResult(success=True)

    def _display_task_panel(self, task):
        """タスク情報をパネル表示"""
        status = task.get("status", "unknown")
        if status == "completed":
            status_icon = "✅"
            status_color = "green"
        elif status == "failed":
            status_icon = "❌"
            status_color = "red"
        else:
            status_icon = "⏳"
            status_color = "yellow"

        # 要約があれば表示
        summary = task.get("summary", "要約なし")
        if summary == "None" or not summary:
            # Complex condition - consider breaking down
            summary = "要約なし"

        # 応答を短縮
        response = task.get("response", "")
        if len(response) > 500:
            response = response[:500] + "\n... (省略)"

        content = f"""
[cyan]タスクID:[/cyan] {task.get('task_id', '')}
[cyan]タイプ:[/cyan] {task.get('task_type', 'general')}
[cyan]ワーカー:[/cyan] {task.get('worker', '')}
[cyan]モデル:[/cyan] {task.get('model', '')}
[cyan]状態:[/cyan] [{status_color}]{status_icon} {status}[/{status_color}]
[cyan]作成日時:[/cyan] {task.get('created_at', '')}

[yellow]【プロンプト】[/yellow]
{task.get('prompt', '')}

[yellow]【要約】[/yellow]
{summary}

[yellow]【応答】[/yellow]
{response}
"""

        console.print(
            Panel(
                content.strip(),
                title=f"📋 タスク詳細: {task.get('task_id', '')}",
                expand=False,
            )
        )


def main():
    """メイン関数"""
    command = AITasksCommand()
    return command.run()


if __name__ == "__main__":
    sys.exit(main())
