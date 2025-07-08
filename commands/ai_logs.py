#!/usr/bin/env python3
"""
AI Company - ログ表示コマンド
"""

import sys
from pathlib import Path
import subprocess
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from datetime import datetime

# プロジェクトルートをsys.pathに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand, CommandResult

console = Console()

class AILogsCommand(BaseCommand):
    """ログ表示コマンド"""
    
    def __init__(self):
        super().__init__(
            name="logs",
            description="AI Company のログを表示"
        )
        self.logs_dir = self.project_root / "logs"
    
    def setup_arguments(self):
        """引数定義"""
        self.parser.add_argument(
            "target",
            nargs="?",
            choices=["task", "pm", "result", "dialog", "all"],
            default="all",
            help="表示するログ"
        )
        self.parser.add_argument(
            "--tail", "-t",
            type=int,
            default=50,
            help="表示する行数（デフォルト: 50）"
        )
        self.parser.add_argument(
            "--follow", "-f",
            action="store_true",
            help="リアルタイム表示（tail -f）"
        )
        self.parser.add_argument(
            "--list", "-l",
            action="store_true",
            help="ログファイル一覧を表示"
        )
        self.parser.add_argument(
            "--grep", "-g",
            help="検索文字列でフィルタ"
        )
        self.parser.add_argument(
            "--since",
            help="指定時刻以降のログを表示（例: '10m', '1h', '2023-01-01'）"
        )
        self.parser.add_argument(
            "--debug",
            action="store_true",
            help="デバッグモード"
        )
    
    def execute(self, args):
        """コマンド実行"""
        try:
            if args.list:
                return self._list_log_files()
            else:
                return self._show_logs(args)
        except Exception as e:
            if args.debug:
                import traceback
                traceback.print_exc()
            return CommandResult(success=False, message=f"エラー: {str(e)}")
    
    def _list_log_files(self):
        """ログファイル一覧を表示"""
        if not self.logs_dir.exists():
            return CommandResult(success=False, message="ログディレクトリが存在しません")
        
        log_files = list(self.logs_dir.glob("*.log"))
        
        if not log_files:
            console.print("[yellow]ログファイルが見つかりません[/yellow]")
            return CommandResult(success=True)
        
        table = Table(title="📜 ログファイル一覧")
        table.add_column("ファイル名", style="cyan")
        table.add_column("サイズ", justify="right")
        table.add_column("最終更新", style="white")
        
        for log_file in sorted(log_files):
            stat = log_file.stat()
            size = self._format_size(stat.st_size)
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            table.add_row(
                log_file.name,
                size,
                mtime
            )
        
        console.print(table)
        return CommandResult(success=True)
    
    def _show_logs(self, args):
        """ログを表示"""
        # ログファイルの選択
        if args.target == "all":
            log_files = list(self.logs_dir.glob("*.log"))
        else:
            log_map = {
                "task": "task_worker.log",
                "pm": "pm_worker.log",
                "result": "result_worker.log",
                "dialog": "dialog_task_worker.log"
            }
            log_file = self.logs_dir / log_map.get(args.target, f"{args.target}.log")
            log_files = [log_file] if log_file.exists() else []
        
        if not log_files:
            return CommandResult(success=False, message="指定されたログファイルが見つかりません")
        
        # ログ表示
        for log_file in log_files:
            if len(log_files) > 1:
                console.print(f"\n[bold cyan]📄 {log_file.name}[/bold cyan]")
                console.print("-" * 50)
            
            if args.follow:
                # リアルタイム表示
                self._tail_follow(log_file, args.grep)
            else:
                # 通常表示
                self._tail_file(log_file, args.tail, args.grep, args.since)
        
        return CommandResult(success=True)
    
    def _tail_file(self, log_file: Path, lines: int, grep: str = None, since: str = None):
        """ファイルの末尾を表示"""
        try:
            # tail コマンドを使用
            cmd = ["tail", f"-n{lines}", str(log_file)]
            
            if grep:
                # grep でフィルタ
                tail_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
                grep_proc = subprocess.Popen(
                    ["grep", "--color=never", grep],
                    stdin=tail_proc.stdout,
                    stdout=subprocess.PIPE,
                    text=True
                )
                tail_proc.stdout.close()
                output = grep_proc.communicate()[0]
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)
                output = result.stdout
            
            if output:
                # シンタックスハイライト
                syntax = Syntax(output, "log", theme="monokai", line_numbers=False)
                console.print(syntax)
            else:
                console.print("[yellow]表示するログがありません[/yellow]")
                
        except Exception as e:
            console.print(f"[red]ログ読み込みエラー: {e}[/red]")
    
    def _tail_follow(self, log_file: Path, grep: str = None):
        """リアルタイムでログを表示"""
        try:
            console.print(f"[green]リアルタイムログ表示中... (Ctrl+C で終了)[/green]\n")
            
            cmd = ["tail", "-f", str(log_file)]
            
            if grep:
                # tail -f | grep パターン
                tail_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
                grep_proc = subprocess.Popen(
                    ["grep", "--line-buffered", "--color=never", grep],
                    stdin=tail_proc.stdout,
                    stdout=subprocess.PIPE,
                    text=True
                )
                tail_proc.stdout.close()
                
                for line in grep_proc.stdout:
                    console.print(line.rstrip())
            else:
                # tail -f のみ
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
                
                for line in proc.stdout:
                    console.print(line.rstrip())
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]ログ表示を終了しました[/yellow]")
        except Exception as e:
            console.print(f"[red]リアルタイム表示エラー: {e}[/red]")
    
    def _format_size(self, size: int) -> str:
        """ファイルサイズをフォーマット"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

def main():
    """メイン関数"""
    command = AILogsCommand()
    return command.run()

if __name__ == "__main__":
    sys.exit(main())
