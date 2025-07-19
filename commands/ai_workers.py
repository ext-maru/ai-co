#!/usr/bin/env python3
"""
Elders Guild - ワーカー管理コマンド
"""

import subprocess
import sys
from pathlib import Path

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# プロジェクトルートをsys.pathに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand, CommandResult

console = Console()


class AIWorkersCommand(BaseCommand):
    """ワーカー管理コマンド"""

    def __init__(self):
        super().__init__(name="workers", description="Elders Guild ワーカーの管理")

    def setup_arguments(self):
        """引数定義"""
        self.parser.add_argument(
            "--restart",
            "-r",
            choices=["task", "pm", "result", "dialog", "all"],
            help="ワーカーを再起動",
        )
        self.parser.add_argument(
            "--stop",
            "-s",
            choices=["task", "pm", "result", "dialog", "all"],
            help="ワーカーを停止",
        )
        self.parser.add_argument("--debug", action="store_true", help="デバッグモード")

    def execute(self, args):
        """コマンド実行"""
        try:
            if args.restart:
                return self._restart_workers(args.restart)
            elif args.stop:
                return self._stop_workers(args.stop)
            else:
                return self._show_workers()
        except Exception as e:
            if args.debug:
                import traceback

                traceback.print_exc()
            return CommandResult(success=False, message=f"エラー: {str(e)}")

    def _show_workers(self):
        """ワーカー一覧表示"""
        workers = [
            ("TaskWorker", "task_worker.py", "ai_tasks"),
            ("PMWorker", "pm_worker.py", "ai_pm"),
            ("ResultWorker", "result_worker.py", "ai_results"),
            ("DialogTaskWorker", "dialog_task_worker.py", "dialog_task_queue"),
            ("DialogPMWorker", "dialog_pm_worker.py", "dialog_response_queue"),
        ]

        table = Table(title="👷 Elders Guild ワーカー状態")
        table.add_column("ワーカー名", style="cyan", width=20)
        table.add_column("スクリプト", style="white", width=25)
        table.add_column("状態", justify="center", width=10)
        table.add_column("PID", justify="right", width=8)
        table.add_column("CPU%", justify="right", width=8)
        table.add_column("メモリ", justify="right", width=10)
        table.add_column("キュー", style="magenta", width=20)

        for worker_name, script_name, queue_name in workers:
            status, pid, cpu, mem = self._check_worker_process(script_name)

            if status == "稼働中":
                status_text = "[green]●[/green] 稼働中"
            else:
                status_text = "[red]●[/red] 停止"

            table.add_row(
                worker_name,
                script_name,
                status_text,
                str(pid) if pid else "-",
                f"{cpu:.1f}%" if cpu is not None else "-",
                f"{mem:.1f}MB" if mem is not None else "-",
                queue_name,
            )

        console.print(table)
        return CommandResult(success=True)

    def _check_worker_process(self, script_name):
        """ワーカープロセスチェック"""
        try:
            for proc in psutil.process_iter(
                ["pid", "name", "cmdline", "cpu_percent", "memory_info"]
            ):
                try:
                    if proc.info["cmdline"] and script_name in " ".join(
                        proc.info["cmdline"]
                    ):
                        cpu = proc.cpu_percent()
                        mem = proc.memory_info().rss / 1024 / 1024  # MB
                        return "稼働中", proc.pid, cpu, mem
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return "停止", None, None, None
        except Exception:
            return "不明", None, None, None

    def _restart_workers(self, target):
        """ワーカー再起動"""
        console.print(f"[yellow]🔄 {target} ワーカーを再起動中...[/yellow]")

        # 停止
        self._stop_workers(target)

        # 起動
        if target == "all":
            subprocess.run(["ai-start"], check=False)
        else:
            # 個別起動（tmux内で）
            worker_map = {
                "task": "workers/task_worker.py",
                "pm": "workers/pm_worker.py",
                "result": "workers/result_worker.py",
                "dialog": "workers/dialog_task_worker.py",
            }

            if target in worker_map:
                script_path = PROJECT_ROOT / worker_map[target]
                cmd = f"cd {PROJECT_ROOT} && source venv/bin/activate && python3 {script_path}"
                subprocess.run(
                    ["tmux", "send-keys", "-t", "elders_guild", cmd, "Enter"],
                    check=False,
                )

        console.print(f"[green]✅ {target} ワーカーを再起動しました[/green]")
        return CommandResult(success=True)

    def _stop_workers(self, target):
        """ワーカー停止"""
        console.print(f"[yellow]⏹️  {target} ワーカーを停止中...[/yellow]")

        if target == "all":
            subprocess.run(["ai-stop"], check=False)
        else:
            # 個別停止
            worker_scripts = {
                "task": "task_worker.py",
                "pm": "pm_worker.py",
                "result": "result_worker.py",
                "dialog": "dialog_task_worker.py",
            }

            if target in worker_scripts:
                script_name = worker_scripts[target]
                for proc in psutil.process_iter(["pid", "cmdline"]):
                    try:
                        if proc.info["cmdline"] and script_name in " ".join(
                            proc.info["cmdline"]
                        ):
                            proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

        return CommandResult(success=True)


def main():
    """メイン関数"""
    command = AIWorkersCommand()
    return command.run()


if __name__ == "__main__":
    sys.exit(main())
