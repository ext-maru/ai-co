#!/usr/bin/env python3
"""
Elders Guild - タスク管理コマンド
"""

import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

# プロジェクトルートをsys.pathに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand, CommandResult
sys.path.insert(0, '/root/ai_co')
from features.database.task_history_db import TaskHistoryDB

console = Console()

class AITasksCommand(BaseCommand):
    """タスク管理コマンド"""
    
    def __init__(self):
        super().__init__(
            name="tasks",
            description="Elders Guild タスクの管理"
        )
    
    def setup_arguments(self):
        """引数定義"""
        self.parser.add_argument(
            "--limit", "-l",
            type=int,
            default=10,
            help="表示件数"
        )
        self.parser.add_argument(
            "--type", "-t",
            choices=["all", "code", "general", "dialog"],
            default="all",
            help="タスクタイプ"
        )
        self.parser.add_argument(
            "--search", "-s",
            help="検索キーワード"
        )
        self.parser.add_argument(
            "--id",
            help="タスクIDで詳細表示"
        )
        self.parser.add_argument(
            "--format", "-f",
            choices=["table", "json", "detail"],
            default="table",
            help="出力形式"
        )
        self.parser.add_argument(
            "--debug",
            action="store_true",
            help="デバッグモード"
        )
    
    def execute(self, args):
        """コマンド実行"""
        try:
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
                    tasks = [t for t in tasks if t.get('task_type') == args.type]
            
            # 表示
            if args.format == "json":
                print(json.dumps(tasks, indent=2, ensure_ascii=False, default=str))
            elif args.format == "detail":
                self._show_tasks_detail(tasks)
            else:
                self._show_tasks_table(tasks)
            
            return CommandResult(success=True)
            
        except Exception as e:
            if args.debug:
                import traceback
                traceback.print_exc()
            return CommandResult(success=False, message=f"エラー: {str(e)}")
    
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
            status = task.get('status', 'unknown')
            if status == 'completed':
                status_text = "[green]✅[/green]"
            elif status == 'failed':
                status_text = "[red]❌[/red]"
            else:
                status_text = "[yellow]⏳[/yellow]"
            
            # プロンプトを短縮
            prompt = task.get('prompt', '')
            if len(prompt) > 37:
                prompt = prompt[:37] + "..."
            
            # 作成日時をフォーマット
            created_at = task.get('created_at', '')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('T', ' '))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            table.add_row(
                task.get('task_id', ''),
                task.get('task_type', 'general'),
                task.get('worker', ''),
                status_text,
                created_at,
                prompt
            )
        
        console.print(table)
        
        if not tasks:
            console.print("[yellow]📭 タスクが見つかりません[/yellow]")
    
    def _show_tasks_detail(self, tasks):
        """タスク詳細表示"""
        for task in tasks:
            self._display_task_panel(task)
            console.print()
    
    def _show_task_detail(self, db, task_id, format):
        """特定タスクの詳細表示"""
        task = db.get_task_by_id(task_id)
        
        if not task:
            return CommandResult(
                success=False,
                message=f"タスクID '{task_id}' が見つかりません"
            )
        
        if format == "json":
            print(json.dumps(task, indent=2, ensure_ascii=False, default=str))
        else:
            self._display_task_panel(task)
        
        return CommandResult(success=True)
    
    def _display_task_panel(self, task):
        """タスク情報をパネル表示"""
        status = task.get('status', 'unknown')
        if status == 'completed':
            status_icon = "✅"
            status_color = "green"
        elif status == 'failed':
            status_icon = "❌"
            status_color = "red"
        else:
            status_icon = "⏳"
            status_color = "yellow"
        
        # 要約があれば表示
        summary = task.get('summary', '要約なし')
        if summary == 'None' or not summary:
            summary = '要約なし'
        
        # 応答を短縮
        response = task.get('response', '')
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
        
        console.print(Panel(
            content.strip(),
            title=f"📋 タスク詳細: {task.get('task_id', '')}",
            expand=False
        ))

def main():
    """メイン関数"""
    command = AITasksCommand()
    return command.run()

if __name__ == "__main__":
    sys.exit(main())
