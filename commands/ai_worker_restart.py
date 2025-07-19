#!/usr/bin/env python3
"""
ワーカー再起動
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import subprocess

import psutil
from rich.console import Console

from commands.base_command import BaseCommand, CommandResult


class AIWorkerRestartCommand(BaseCommand):
    """ワーカー再起動コマンド"""

    def __init__(self):
        super().__init__(
            name="ai-worker-restart", description="ワーカー再起動", version="1.0.0"
        )
        self.console = Console()

    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument(
            "worker_type",
            choices=["task", "pm", "result", "dialog", "all"],
            help="再起動するワーカータイプ",
        )
        self.parser.add_argument("--force", "-f", action="store_true", help="強制再起動")

    def execute(self, args) -> CommandResult:
        """実行"""
        worker_map = {
            "task": "task_worker.py",
            "pm": "pm_worker.py",
            "result": "result_worker.py",
            "dialog": "dialog_task_worker.py",
        }

        if args.worker_type == "all":
            workers_to_restart = list(worker_map.values())
        else:
            workers_to_restart = [worker_map[args.worker_type]]

        results = []
        for worker_file in workers_to_restart:
            self.console.print(f"🔄 {worker_file} を再起動中...", style="yellow")

            # プロセス停止
            killed = self._kill_worker(worker_file, args.force)
            if killed:
                self.console.print(f"  ✅ プロセス停止完了", style="green")
            else:
                self.console.print(f"  ⚠️  プロセスが見つかりませんでした", style="yellow")

            # プロセス起動
            started = self._start_worker(worker_file)
            if started:
                self.console.print(f"  ✅ プロセス起動完了", style="green")
                results.append(True)
            else:
                self.console.print(f"  ❌ プロセス起動失敗", style="red")
                results.append(False)

        if all(results):
            return CommandResult(success=True, message="すべてのワーカーの再起動が完了しました")
        else:
            return CommandResult(success=False, message="一部のワーカーの再起動に失敗しました")

    def _kill_worker(self, worker_file: str, force: bool = False) -> bool:
        """ワーカープロセス停止"""
        killed = False
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline", [])
                if cmdline and worker_file in " ".join(cmdline):
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    proc.wait(timeout=5)
                    killed = True
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied):
                pass
        return killed

    def _start_worker(self, worker_file: str) -> bool:
        """ワーカープロセス起動"""
        try:
            worker_path = Path(f"/home/aicompany/ai_co/workers/{worker_file}")
            if not worker_path.exists():
                return False

            # tmux内で起動
            session_name = "elders_guild"
            window_name = worker_file.replace(".py", "")

            subprocess.run(
                [
                    "tmux",
                    "new-window",
                    "-t",
                    f"{session_name}:",
                    "-n",
                    window_name,
                    f"cd /home/aicompany/ai_co && source venv/bin/activate && python3 workers/{worker_file}",
                ],
                check=True,
            )

            return True
        except subprocess.CalledProcessError:
            return False


def main():
    command = AIWorkerRestartCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
