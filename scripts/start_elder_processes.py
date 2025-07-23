#!/usr/bin/env python3
"""
エルダープロセス起動スクリプト
Elder Process Launcher - エルダーズツリーの起動管理

プロセス分離アーキテクチャに基づいてエルダープロセスを起動
"""

import subprocess
import time
import sys
import os
import signal
from pathlib import Path
from typing import List, Dict, Optional

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ElderProcessManager:
    """エルダープロセス管理"""

    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.log_dir = PROJECT_ROOT / "logs" / "elders"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # プロセス定義
        self.elder_configs = [
            {
                "name": "grand_elder",
                "script": "processes/grand_elder_process.py",
                "port": 5000,
                "delay": 0,
            },
            {
                "name": "claude_elder",
                "script": "processes/claude_elder_process.py",
                "port": 5001,
                "delay": 2,  # グランドエルダー起動後2秒待機
            },
            {
                "name": "knowledge_sage",
                "script": "processes/knowledge_sage_process.py",
                "port": 5002,
                "delay": 1,
            },
            {
                "name": "task_sage",
                "script": "processes/task_sage_process.py",
                "port": 5003,
                "delay": 1,
            },
            {
                "name": "incident_sage",
                "script": "processes/incident_sage_process.py",
                "port": 5004,
                "delay": 1,
            },
            {
                "name": "rag_sage",
                "script": "processes/rag_sage_process.py",
                "port": 5005,
                "delay": 1,
            },
        ]

    def check_redis(self) -> bool:
        """Redis接続確認"""
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379)
            r.ping()
            print("✅ Redis is running")
            return True
        except Exception as e:
            print(f"❌ Redis is not running: {e}")
            print("Please start Redis first: redis-server")
            return False

    def start_process(self, config: Dict) -> Optional[subprocess.Popen]:
        """個別プロセス起動"""
        name = config["name"]
        script_path = PROJECT_ROOT / config["script"]

        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            return None

        # 遅延
        if config["delay"] > 0:
            print(f"⏳ Waiting {config['delay']}s before starting {name}...")
            time.sleep(config["delay"])

        print(f"🚀 Starting {name}...")

        try:
            # ログファイル
            log_file = self.log_dir / f"{name}_launcher.log"

            # プロセス起動
            with open(log_file, "w") as log:
                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    cwd=str(PROJECT_ROOT),
                    env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
                )

            self.processes[name] = process
            print(f"✅ {name} started (PID: {process.pid})")

            # プロセスが正常に起動したか確認
            time.sleep(1)
            if process.poll() is not None:
                print(f"❌ {name} failed to start")
                return None

            return process

        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None

    def start_all(self):
        """全エルダープロセス起動"""
        print("🌳 Starting Elder Tree...")
        print("=" * 50)

        # Redis確認
        if not self.check_redis():
            return False

        # 各プロセスを順番に起動
        for config in self.elder_configs:
            process = self.start_process(config)
            if not process:
                print(f"❌ Failed to start {config['name']}, aborting...")
                self.stop_all()
                return False

        print("\n✅ All Elder processes started successfully!")
        print(f"Total processes: {len(self.processes)}")
        return True

    def stop_all(self):
        """全プロセス停止"""
        print("\n🛑 Stopping all Elder processes...")

        for name, process in self.processes.items():
            try:
                print(f"Stopping {name} (PID: {process.pid})...")
                process.terminate()

                # 正常終了を待つ
                try:
                    process.wait(timeout=5)
                    print(f"✅ {name} stopped")
                except subprocess.TimeoutExpired:
                    # 強制終了
                    print(f"⚠️  {name} not responding, force killing...")
                    process.kill()
                    process.wait()

            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")

        self.processes.clear()
        print("✅ All processes stopped")

    def monitor(self):
        """プロセス監視"""
        print("\n📊 Monitoring Elder processes (Press Ctrl+C to stop)...")
        print("-" * 60)

        try:
            # ループ処理
            while True:
                status_lines = []
                all_running = True

                for name, process in self.processes.items():
                    if process.poll() is None:
                        status = "🟢 Running"
                    else:
                        status = f"🔴 Stopped (exit code: {process.returncode})"
                        all_running = False

                    status_lines.append(f"{name:20} | PID: {process.pid:6} | {status}")

                # 画面クリア（簡易版）
                print("\033[H\033[J", end="")
                print("📊 Elder Process Monitor")
                print("-" * 60)
                print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 60)

                for line in status_lines:
                    print(line)

                print("-" * 60)
                print("Press Ctrl+C to stop all processes")

                # プロセスが停止していたら警告
                if not all_running:
                    print("\n⚠️  Some processes have stopped!")

                time.sleep(2)

        except KeyboardInterrupt:
            print("\n\nReceived interrupt signal")

    def run(self):
        """メイン実行"""
        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # プロセス起動
        if self.start_all():
            # 監視開始
            self.monitor()

        # 終了処理
        self.stop_all()

    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        print(f"\nReceived signal {signum}")
        # 監視ループを抜けるためにKeyboardInterruptを発生
        raise KeyboardInterrupt


def main():
    """メイン関数"""
    print("🏛️ Elder Process Manager v1.0")
    print("=" * 60)

    manager = ElderProcessManager()

    # コマンドライン引数処理
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "start":
            # デーモンモードで起動
            if manager.start_all():
                print("\nProcesses started in background")
                print("Use 'ps aux | grep elder' to check status")

        elif command == "stop":
            # プロセスファイルから停止
            print("Stopping processes...")
            # TODO: PIDファイルベースの停止実装

        else:
            print(f"Unknown command: {command}")
            print("Usage: start_elder_processes.py [start|stop]")

    else:
        # インタラクティブモード
        manager.run()


if __name__ == "__main__":
    main()
