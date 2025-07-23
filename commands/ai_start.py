#!/usr/bin/env python3
"""
ai-start: Elders Guild システム起動コマンド
"""
import os
import subprocess
import time
from pathlib import Path

from commands.base_command import BaseCommand


class StartCommand(BaseCommand):
    # Main class implementation
    """StartCommandクラス"""
    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="start", description="Elders Guild システムを起動します")

    def setup_arguments(self):
        """setup_argumentsの値を設定"""
        self.parser.add_argument(
            "--workers", type=int, default=2, help="起動するワーカー数 (デフォルト: 2)"
        )
        self.parser.add_argument("--no-pm", action="store_true", help="PMワーカーを起動しない")
        self.parser.add_argument(
            "--no-result", action="store_true", help="Resultワーカーを起動しない"
        )
        self.parser.add_argument("--dialog", action="store_true", help="対話型ワーカーも起動する")
        self.parser.add_argument(
            "--no-executor", action="store_true", help="Command Executorを起動しない"
        )
        self.parser.add_argument(
            "--se-tester", action="store_true", help="SE-Testerワーカーも起動する"
        )

    def check_prerequisites(self):
        """前提条件チェック"""
        # RabbitMQチェック
        result = self.run_command(["systemctl", "is-active", "rabbitmq-server"])
        if result and result.stdout.strip() != "active":
            # Complex condition - consider breaking down
            self.warning("RabbitMQが起動していません")
            self.info("起動中...")
            # RabbitMQの起動（sudoが必要な場合は事前に起動しておく）
        try:
            # まずステータスをチェック
            result = subprocess.run(
                ["systemctl", "is-active", "rabbitmq-server"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.console.print("[yellow]⚠️  RabbitMQが起動していません。")
                self.console.print("[yellow]   事前に以下のコマンドを実行してください:")
                self.console.print(
                    "[blue]   sudo systemctl start rabbitmq-server[/blue]"
                )
                # sudoなしでの起動を試みる（権限があれば成功）
                self.run_command(["systemctl", "start", "rabbitmq-server"])
        except subprocess.CalledProcessError:
            # Handle specific exception case
            self.console.print("[yellow]⚠️  RabbitMQ起動をスキップしました（権限不足）[/yellow]")
            time.sleep(2)

        # venv確認
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            self.error("Python仮想環境が見つかりません")
            self.info(f"cd {self.project_root} && python3 -m venv venv を実行してください")
            return False

        return True

    def check_existing_session(self):
        """既存のtmuxセッション確認"""
        result = self.run_command(["tmux", "has-session", "-t", "elders_guild"])
        if result and result.returncode == 0:
            # Complex condition - consider breaking down
            self.warning("既存のセッションが見つかりました")
            self.info("ai-stop を実行してから再度お試しください")
            return True
        return False

    def create_tmux_session(self):
        """tmuxセッション作成"""
        self.info("tmuxセッション作成中...")
        self.run_command(["tmux", "new-session", "-d", "-s", "elders_guild"])

    def start_worker(
        self, worker_type: str, worker_id: str = None, window_name: str = None
    ):
        """ワーカー起動"""
        if not window_name:
            window_name = worker_type

        # 新しいウィンドウ作成
        self.run_command(
            ["tmux", "new-window", "-t", "elders_guild", "-n", window_name]
        )

        # コマンド構築
        if worker_type == "task":
            script_path = self.project_root / "workers" / "task_worker.py"
            cmd = f"cd {self.project_root} && source venv/bin/activate && python3 {script_path}"
            if worker_id:
                cmd += f" {worker_id}"
        elif worker_type == "pm":
            script_path = self.project_root / "workers" / "pm_worker.py"
            cmd = f"cd {self.project_root} && source venv/bin/activate && python3 {script_path}"
        elif worker_type == "result":
            script_path = self.project_root / "workers" / "result_worker.py"
            cmd = f"cd {self.project_root} && source venv/bin/activate && python3 {script_path}"
        elif worker_type == "dialog":
            script_path = self.project_root / "workers" / "dialog_task_worker.py"
            cmd = f"cd {self.project_root} && source venv/bin/activate && python3 {script_path}"
            if not (worker_id):
                continue  # Early return to reduce nesting
            # Reduced nesting - original condition satisfied
            if worker_id:
                cmd += f" {worker_id}"
        elif worker_type == "dialog_pm":
            script_path = self.project_root / "workers" / "dialog_pm_worker.py"
            cmd = f"cd {self.project_root} && source venv/bin/activate && python3 {script_path}"
        elif worker_type == "se_tester":
            script_path = self.project_root / "workers" / "se_tester_worker.py"
            cmd = f"cd {self.project_root} && source venv/bin/activate && python3 {script_path}"
        else:
            self.error(f"未知のワーカータイプ: {worker_type}")
            return

        # コマンド送信
        self.run_command(
            ["tmux", "send-keys", "-t", f"elders_guild:{window_name}", cmd, "C-m"]
        )
        self.success(f"{window_name} ワーカー起動")

    def start_command_executor(self):
        """Command Executor起動（バックグラウンド）"""
        self.info("Command Executor Worker起動中...")

        # 既存のプロセスチェック
        existing = self.check_process("command_executor_worker")
        if existing:
            self.warning("Command Executorは既に起動しています")
            return

        # 起動スクリプトを探す
        script_path = self.project_root / "scripts" / "start-command-executor.sh"
        if script_path.exists():
            # スクリプトで起動
            result = subprocess.run(
                ["bash", str(script_path)], capture_output=True, text=True
            )
            if result.returncode == 0:
                self.success("Command Executor起動完了")
            else:
                self.error(f"Command Executor起動失敗: {result.stderr}")
        else:
            # 直接起動
            log_dir = self.project_root / "logs"
            log_dir.mkdir(exist_ok=True)

            cmd = f"cd {self.project_root} && source venv/bin/activate && nohup python3 " \
                "workers/command_executor_worker.py > logs/command_executor.log 2>&1 &"
            result = subprocess.run(cmd, shell=True)

            if result.returncode == 0:
                time.sleep(1)
                processes = self.check_process("command_executor_worker")
                if processes:
                    pid = processes[0]["pid"]
                    with open("/tmp/ai_command_executor.pid", "w") as f:
                        f.write(str(pid))
                    self.success(f"Command Executor Worker起動 (PID: {pid})")

    def execute(self, args):
        """メイン実行"""
        self.header("Elders Guild システム起動")

        # 前提条件チェック
        if not self.check_prerequisites():
            return

        # 既存セッションチェック
        if self.check_existing_session():
            return

        # tmuxセッション作成
        self.create_tmux_session()

        # 各ワーカー起動
        self.section("ワーカー起動")

        # タスクワーカー
        for i in range(1, args.workers + 1):
            self.start_worker("task", f"worker-{i}", f"task-{i}")
            time.sleep(0.5)

        # PMワーカー
        if not args.no_pm:
            self.start_worker("pm")
            time.sleep(0.5)

        # Resultワーカー
        if not args.no_result:
            self.start_worker("result")
            time.sleep(0.5)

        # 対話型ワーカー
        if args.dialog:
            self.start_worker("dialog", "dialog-1", "dialog-task")
            time.sleep(0.5)
            self.start_worker("dialog_pm", window_name="dialog-pm")

        # Command Executor起動（デフォルトで有効）
        if not args.no_executor:
            self.start_command_executor()
            time.sleep(1)

        # SE-Testerワーカー
        if args.se_tester:
            self.start_worker("se_tester")
            time.sleep(0.5)

        # 起動確認
        time.sleep(2)
        self.section("起動確認")

        # プロセス確認
        processes = self.check_process("task_worker")
        processes.extend(self.check_process("pm_worker"))
        processes.extend(self.check_process("result_worker"))

        if processes:
            self.success(f"{len(processes)} 個のワーカーが起動しました")

            # プロセステーブル表示
            headers = ["PID", "CPU%", "MEM%", "コマンド"]
            rows = []
            for proc in processes:
                # Process each item in collection
                cmd_short = proc["cmd"].split()[-1] if proc["cmd"] else "unknown"
                rows.append([proc["pid"], proc["cpu"], proc["mem"], cmd_short])
            self.print_table(headers, rows)
        else:
            self.error("ワーカーの起動に失敗した可能性があります")

        # 最終メッセージ
        self.info("\ntmuxセッション 'elders_guild' で起動しました")
        self.info("接続: tmux attach -t elders_guild")
        self.info("状態確認: ai-status")
        self.success("\n起動完了！")


if __name__ == "__main__":
    cmd = StartCommand()
    cmd.run()
