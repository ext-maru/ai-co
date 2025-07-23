#!/usr/bin/env python3
"""
Worker Controller - ワーカーの起動・停止制御
"""
import logging
import os
import signal
import subprocess
import time
from pathlib import Path

logger = logging.getLogger("WorkerController")


class WorkerController:
    def __init__(self, config_file=None):
        """ワーカー制御システムの初期化"""
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "scaling.conf"
        self.config = self._load_config(config_file)
        self.ai_company_root = Path(__file__).parent.parent

    def _load_config(self, config_file):
        """設定ファイル読み込み"""
        config = {}
        try:
            with open(config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        try:
                            config[key] = int(value)
                        except ValueError:
                            config[key] = value
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
        return config

    def start_worker(self, worker_id):
        """新しいワーカーを起動"""
        try:
            # tmuxセッションの存在確認
            check_tmux = subprocess.run(
                ["tmux", "has-session", "-t", "ai_company"], capture_output=True
            )

            if check_tmux.returncode == 0:
                # task_workerウィンドウの存在確認
                check_window = subprocess.run(
                    [
                        "tmux",
                        "list-windows",
                        "-t",
                        "ai_company",
                        "-F",
                        "#{window_name}",
                    ],
                    capture_output=True,
                    text=True,
                )

                # 適切なウィンドウを探す
                window_name = None
                for window in check_window.stdout.strip().split("\n"):
                    if "task" in window or "worker" in window:
                        window_name = window
                        break

                if not window_name:
                    # ウィンドウがなければ作成
                    subprocess.run(
                        ["tmux", "new-window", "-t", "ai_company", "-n", "task_workers"]
                    )
                    window_name = "task_workers"

                # tmuxで起動
                cmd = f"cd {self.ai_company_root} && source venv/bin/activate && python3 " \
                    "workers/task_worker.py {worker_id}"
                subprocess.run(
                    [
                        "tmux",
                        "send-keys",
                        "-t",
                        f"ai_company:{window_name}",
                        cmd,
                        "Enter",
                    ]
                )
                logger.info(f"✅ ワーカー起動 (tmux:{window_name}): {worker_id}")
            else:
                # 直接起動（バックグラウンド）
                cmd = [
                    "python3",
                    str(self.ai_company_root / "workers" / "task_worker.py"),
                    worker_id,
                ]
                subprocess.Popen(
                    cmd,
                    cwd=str(self.ai_company_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info(f"✅ ワーカー起動 (直接): {worker_id}")

            # 起動待機
            time.sleep(self.config.get("WORKER_START_DELAY", 2))
            return True

        except Exception as e:
            logger.error(f"ワーカー起動エラー: {worker_id} - {e}")
            return False

    def stop_worker(self, worker_id, graceful=True):
        """ワーカーを停止"""
        try:
            # プロセスを検索
            ps_cmd = ["ps", "aux"]
            result = subprocess.run(ps_cmd, capture_output=True, text=True)

            pid = None
            for line in result.stdout.split("\n"):
                if f"task_worker.py {worker_id}" in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = int(parts[1])
                        break

            if pid:
                if graceful:
                    # SIGTERM送信（graceful shutdown）
                    os.kill(pid, signal.SIGTERM)
                    logger.info(f"📤 SIGTERM送信: {worker_id} (PID: {pid})")

                    # 終了待機
                    timeout = self.config.get("GRACEFUL_SHUTDOWN_TIMEOUT", 30)
                    for _ in range(timeout):
                        try:
                            os.kill(pid, 0)  # プロセス存在確認
                            time.sleep(1)
                        except ProcessLookupError:
                            logger.info(f"✅ ワーカー正常終了: {worker_id}")
                            return True

                    # タイムアウトしたら強制終了
                    logger.warning(f"⚠️ Graceful shutdown タイムアウト: {worker_id}")

                # 強制終了
                try:
                    os.kill(pid, signal.SIGKILL)
                    logger.info(f"🔨 ワーカー強制終了: {worker_id}")
                except ProcessLookupError:
                    pass

                return True
            else:
                logger.warning(f"ワーカーが見つかりません: {worker_id}")
                return False

        except Exception as e:
            logger.error(f"ワーカー停止エラー: {worker_id} - {e}")
            return False

    def restart_worker(self, worker_id):
        """ワーカーを再起動"""
        logger.info(f"🔄 ワーカー再起動: {worker_id}")
        if self.stop_worker(worker_id, graceful=True):
            time.sleep(self.config.get("WORKER_STOP_DELAY", 1))
            return self.start_worker(worker_id)
        return False

    def scale_workers(self, target_num):
        """ワーカー数を指定数に調整"""
        from .worker_monitor import WorkerMonitor

        monitor = WorkerMonitor()

        current_workers = monitor.get_active_workers()
        current_num = len(current_workers)

        logger.info(f"📊 スケーリング: 現在 {current_num} → 目標 {target_num}")

        if current_num < target_num:
            # スケールアップ
            for i in range(current_num + 1, target_num + 1):
                worker_id = f"worker-{i}"
                self.start_worker(worker_id)

        elif current_num > target_num:
            # スケールダウン
            workers_to_stop = current_workers[target_num:]
            for worker in workers_to_stop:
                self.stop_worker(worker["worker_id"], graceful=True)

        return True


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    controller = WorkerController()

    print("=== Worker Controller Test ===")
    print("利用可能なメソッド:")
    print("- start_worker(worker_id)")
    print("- stop_worker(worker_id)")
    print("- restart_worker(worker_id)")
    print("- scale_workers(target_num)")
