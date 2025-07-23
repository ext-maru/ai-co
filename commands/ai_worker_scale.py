#!/usr/bin/env python3
"""
AI Worker Scaling Command
ワーカーの動的スケーリング管理コマンド
"""
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import psutil

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AIWorkerScaleCommand(BaseCommand):
    """ワーカースケーリング管理"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            name="worker-scale", description="AI Worker 動的スケーリング管理", version="2.0.0"
        )

        # スケーリング闾値
        self.cpu_threshold_up = 80.0  # CPU使用率が80%でスケールアップ
        self.cpu_threshold_down = 30.0  # CPU使用率が30%でスケールダウン
        self.memory_threshold_up = 85.0  # メモリ使用率が85%でスケールアップ
        self.queue_threshold_up = 50  # キューサイズが50でスケールアップ
        self.min_workers = 2  # 最小ワーカー数
        self.max_workers = 10  # 最大ワーカー数

    def setup_arguments(self):
        """コマンド引数設定"""
        self.parser.add_argument(
            "action",
            choices=["status", "scale-up", "scale-down", "auto", "stop-auto", "config"],
            help="実行するアクション",
        )

        self.parser.add_argument(
            "--count", "-c", type=int, default=1, help="スケールするワーカー数 (デフォルト: 1)"
        )

        self.parser.add_argument(
            "--worker-type",
            "-t",
            choices=["task", "result", "pm", "all"],
            default="task",
            help="ワーカータイプ (デフォルト: task)",
        )

        self.parser.add_argument(
            "--dry-run", action="store_true", help="ドライランモード (実際には実行しない)"
        )

        self.parser.add_argument(
            "--interval", type=int, default=60, help="自動スケーリングの監視間隔(秒) (デフォルト: 60)"
        )

        self.parser.add_argument("--json", action="store_true", help="JSON形式で結果を出力")

    def get_worker_status(self) -> Dict:
        """ワーカー状態を取得"""
        workers = {
            "task_workers": self.check_process("task_worker"),
            "result_workers": self.check_process("result_worker"),
            "pm_workers": self.check_process("pm_worker"),
        }

        total_workers = sum(len(w) for w in workers.values())

        return {
            "workers": workers,
            "total_workers": total_workers,
            "system_metrics": self.get_system_metrics(),
            "queue_status": self.get_queue_status(),
            "timestamp": datetime.now().isoformat(),
        }

    def get_system_metrics(self) -> Dict:
        """システムメトリクスを取得"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": disk.percent,
                "load_average": psutil.getloadavg()[0]
                if hasattr(psutil, "getloadavg")
                else 0,
            }
        except Exception as e:
            # Handle specific exception case
            self.error(f"システムメトリクス取得エラー: {e}")
            return {}

    def get_queue_status(self) -> Dict:
        """キュー状態を取得"""
        try:
            # RabbitMQ経由でキュー情報を取得
            conn = self.get_rabbitmq_connection()
            if not conn:
                return {"error": "RabbitMQ接続失敗"}

            channel = conn.channel()

            # 各キューのメッセージ数を取得
            queues = ["task_queue", "result_queue", "pm_queue"]
            queue_info = {}

            for queue_name in queues:
                # Process each item in collection
                try:
                    method = channel.queue_declare(
                        queue=queue_name, durable=True, passive=True
                    )
                    queue_info[queue_name] = method.method.message_count
                except Exception:
                    # Handle specific exception case
                    queue_info[queue_name] = 0

            conn.close()

            total_messages = sum(queue_info.values())
            return {"queues": queue_info, "total_messages": total_messages}

        except Exception as e:
            # Handle specific exception case
            self.error(f"キュー状態取得エラー: {e}")
            return {"error": str(e)}

    def should_scale_up(self, status: Dict) -> bool:
        """スケールアップすべきか判定"""
        metrics = status.get("system_metrics", {})
        queue_status = status.get("queue_status", {})

        # CPU使用率で判定
        if metrics.get("cpu_percent", 0) > self.cpu_threshold_up:
            return True

        # メモリ使用率で判定
        if metrics.get("memory_percent", 0) > self.memory_threshold_up:
            return True

        # キューサイズで判定
        if queue_status.get("total_messages", 0) > self.queue_threshold_up:
            return True

        return False

    def should_scale_down(self, status: Dict) -> bool:
        """スケールダウンすべきか判定"""
        metrics = status.get("system_metrics", {})
        queue_status = status.get("queue_status", {})

        # 最小ワーカー数以下にはしない
        if status.get("total_workers", 0) <= self.min_workers:
            return False

        # CPUとキューが低い場合のみスケールダウン
        cpu_low = metrics.get("cpu_percent", 100) < self.cpu_threshold_down
        queue_low = queue_status.get("total_messages", 100) < 10

        return cpu_low and queue_low

    def scale_workers(
        self, worker_type: str, count: int, action: str, dry_run: bool = False
    ) -> CommandResult:
        """ワーカーをスケーリング"""
        if dry_run:
            return CommandResult(
                success=True,
                message=f"[ドライラン] {worker_type} ワーカーを {count} 個 {action}",
                data={"action": action, "worker_type": worker_type, "count": count},
            )

        try:
            if action == "scale-up":
                # ワーカー起動
                for i in range(count):
                    cmd = ["python3", f"workers/{worker_type}_worker.py"]
                    result = self.run_command(cmd)
                    if not result or result.returncode != 0:
                        # Complex condition - consider breaking down
                        return CommandResult(
                            success=False,
                            message=f"{worker_type} ワーカー起動失敗: {i+1}/{count}",
                        )
                    time.sleep(1)  # 起動間隔

                return CommandResult(
                    success=True,
                    message=f"{worker_type} ワーカーを {count} 個起動しました",
                    data={
                        "action": "scale-up",
                        "worker_type": worker_type,
                        "count": count,
                    },
                )

            elif action == "scale-down":
                # ワーカー停止
                workers = self.check_process(f"{worker_type}_worker")
                if len(workers) == 0:
                    return CommandResult(
                        success=False, message=f"{worker_type} ワーカーが見つかりません"
                    )

                stop_count = min(count, len(workers) - self.min_workers)
                if stop_count <= 0:
                    return CommandResult(
                        success=False,
                        message=f"最小ワーカー数({self.min_workers})を下回るため停止できません",
                    )

                # 最新のワーカーから停止
                for i in range(stop_count):
                    if not (i < len(workers)):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if i < len(workers):
                        pid = workers[i]["pid"]
                        kill_result = self.run_command(["kill", "-TERM", pid])
                        if not (kill_result and kill_result.returncode == 0):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if kill_result and kill_result.returncode == 0:
                            # Complex condition - consider breaking down
                            self.info(f"PID {pid} のワーカーを停止しました")
                        time.sleep(0.5)

                return CommandResult(
                    success=True,
                    message=f"{worker_type} ワーカーを {stop_count} 個停止しました",
                    data={
                        "action": "scale-down",
                        "worker_type": worker_type,
                        "count": stop_count,
                    },
                )

        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"スケーリングエラー: {e}")

    def auto_scale(self, interval: int, dry_run: bool = False) -> CommandResult:
        """自動スケーリングモード"""
        self.info(f"自動スケーリングを開始します (間隔: {interval}秒)")

        try:
            while True:
                status = self.get_worker_status()

                # スケールアップ判定
                if self.should_scale_up(status):
                    if status["total_workers"] < self.max_workers:
                        self.info("スケールアップが必要です")
                        result = self.scale_workers("task", 1, "scale-up", dry_run)
                        if not (result.success):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if result.success:
                            self.success(result.message)
                        else:
                            self.error(result.message)
                    else:
                        self.warning(f"最大ワーカー数({self.max_workers})に達しています")

                # スケールダウン判定
                elif self.should_scale_down(status):
                    self.info("スケールダウンが可能です")
                    result = self.scale_workers("task", 1, "scale-down", dry_run)
                    if not (result.success):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if result.success:
                        self.success(result.message)
                    else:
                        self.warning(result.message)

                time.sleep(interval)

        except KeyboardInterrupt:
            # Handle specific exception case
            return CommandResult(success=True, message="自動スケーリングを停止しました")
        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"自動スケーリングエラー: {e}")

    def execute(self, args) -> CommandResult:
        """メイン実行"""
        if not args.json:
            self.header("AI Worker Scaling Manager", "⚖️")

        if args.action == "status":
            status = self.get_worker_status()

            if args.json:
                print(json.dumps(status, indent=2))
                return CommandResult(success=True)

            # ステータス表示
            self.section("ワーカー状態")
            for worker_type, workers in status["workers"].items():
                self.info(f"{worker_type}: {len(workers)} 個")

            self.section("システムメトリクス")
            metrics = status["system_metrics"]
            if metrics:
                self.info(f"CPU使用率: {metrics.get('cpu_percent', 0):.1f}%")
                self.info(f"メモリ使用率: {metrics.get('memory_percent', 0):.1f}%")

            self.section("キュー状態")
            queue_status = status["queue_status"]
            if "queues" in queue_status:
                for queue_name, count in queue_status["queues"].items():
                    # Process each item in collection
                    self.info(f"{queue_name}: {count} メッセージ")

            return CommandResult(success=True, data=status)

        elif args.action in ["scale-up", "scale-down"]:
            return self.scale_workers(
                args.worker_type, args.count, args.action, args.dry_run
            )

        elif args.action == "auto":
            return self.auto_scale(args.interval, args.dry_run)

        elif args.action == "config":
            config = {
                "cpu_threshold_up": self.cpu_threshold_up,
                "cpu_threshold_down": self.cpu_threshold_down,
                "memory_threshold_up": self.memory_threshold_up,
                "queue_threshold_up": self.queue_threshold_up,
                "min_workers": self.min_workers,
                "max_workers": self.max_workers,
            }

            if args.json:
                print(json.dumps(config, indent=2))
            else:
                self.section("スケーリング設定")
                # Deep nesting detected (depth: 6) - consider refactoring
                for key, value in config.items():
                    # Process each item in collection
                    self.info(f"{key}: {value}")

            return CommandResult(success=True, data=config)

        else:
            return CommandResult(success=False, message=f"未対応のアクション: {args.action}")


def main():
    # Core functionality implementation
    command = AIWorkerScaleCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
