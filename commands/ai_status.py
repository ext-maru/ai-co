#!/usr/bin/env python3
"""
Elders Guild - システム状態確認コマンド（修正版）
"""

import subprocess
import sys
import time
from pathlib import Path

import psutil
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

# プロジェクトルートをsys.pathに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from commands.base_command import BaseCommand, CommandResult
from libs.queue_manager import QueueManager

console = Console()


class AIStatusCommand(BaseCommand):
    """システム状態確認コマンド"""

    def __init__(self):
        super().__init__(name="status", description="Elders Guild システムの状態を確認")

    def setup_arguments(self):
        """引数定義"""
        self.parser.add_argument(
            "--watch", "-w", action="store_true", help="リアルタイム監視モード"
        )
        self.parser.add_argument(
            "--interval", "-i", type=int, default=2, help="更新間隔（秒）"
        )
        self.parser.add_argument("--debug", action="store_true", help="デバッグモード")

    def execute(self, args):
        """コマンド実行"""
        try:
            if args.watch:
                self._watch_status(args.interval)
            else:
                self._show_status()
            return CommandResult(success=True)
        except Exception as e:
            if args.debug:
                import traceback

                traceback.print_exc()
            return CommandResult(success=False, message=f"エラー: {str(e)}")

    def _show_status(self):
        """状態を1回表示"""
        # システム情報
        system_info = self._get_system_info()

        # ワーカー状態
        worker_status = self._get_worker_status()

        # キュー状態
        queue_status = self._get_queue_status()

        # レイアウト作成
        layout = Layout()
        layout.split_column(
            Layout(Panel(system_info, title="🖥️  システム情報"), size=5),
            Layout(Panel(worker_status, title="👷 ワーカー状態"), size=10),
            Layout(Panel(queue_status, title="📬 キュー状態"), size=8),
        )

        console.print(layout)

    def _watch_status(self, interval):
        """リアルタイム監視"""
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                try:
                    # システム情報
                    system_info = self._get_system_info()

                    # ワーカー状態
                    worker_status = self._get_worker_status()

                    # キュー状態
                    queue_status = self._get_queue_status()

                    # レイアウト作成
                    layout = Layout()
                    layout.split_column(
                        Layout(Panel(system_info, title="🖥️  システム情報"), size=5),
                        Layout(Panel(worker_status, title="👷 ワーカー状態"), size=10),
                        Layout(Panel(queue_status, title="📬 キュー状態"), size=8),
                    )

                    live.update(layout)
                    time.sleep(interval)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    console.print(f"[red]エラー: {str(e)}[/red]")
                    break

    def _get_system_info(self):
        """システム情報取得"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(PROJECT_ROOT))

        info = f"""
CPU使用率: {cpu_percent:.1f}%
メモリ使用: {memory.percent:.1f}% ({memory.used / 1024 / 1024 / 1024:.1f}GB / {memory.total / 1024 / 1024 / 1024:.1f}GB)
ディスク使用: {disk.percent:.1f}% ({disk.used / 1024 / 1024 / 1024:.1f}GB / {disk.total / 1024 / 1024 / 1024:.1f}GB)
"""
        return info.strip()

    def _get_worker_status(self):
        """ワーカー状態取得"""
        workers = [
            ("TaskWorker", "task_worker.py"),
            ("PMWorker", "pm_worker.py"),
            ("ResultWorker", "result_worker.py"),
            ("DialogTaskWorker", "dialog_task_worker.py"),
            ("DialogPMWorker", "dialog_pm_worker.py"),
        ]

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ワーカー", style="cyan", width=20)
        table.add_column("状態", justify="center", width=10)
        table.add_column("PID", justify="right", width=8)
        table.add_column("CPU%", justify="right", width=8)
        table.add_column("メモリ", justify="right", width=10)

        for worker_name, script_name in workers:
            status, pid, cpu, mem = self._check_worker_process(script_name)

            if status == "稼働中":
                status_text = "[green]●[/green] 稼働中"
            else:
                status_text = "[red]●[/red] 停止"

            table.add_row(
                worker_name,
                status_text,
                str(pid) if pid else "-",
                f"{cpu:.1f}%" if cpu is not None else "-",
                f"{mem:.1f}MB" if mem is not None else "-",
            )

        return table

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

    def _get_queue_status(self):
        """キュー状態取得"""
        try:
            qm = QueueManager()
            queue_info = qm.get_queue_info()

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("キュー名", style="cyan", width=25)
            table.add_column("メッセージ数", justify="right", width=15)
            table.add_column("コンシューマー数", justify="right", width=18)

            for queue_name, info in queue_info.items():
                table.add_row(
                    queue_name,
                    str(info.get("messages", 0)),
                    str(info.get("consumers", 0)),
                )

            return table

        except Exception as e:
            return f"[red]キュー情報取得エラー: {str(e)}[/red]"


def main():
    """メイン関数"""
    command = AIStatusCommand()
    return command.run()


if __name__ == "__main__":
    sys.exit(main())
