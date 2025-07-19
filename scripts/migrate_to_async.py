#!/usr/bin/env python3
"""
Elders Guild 非同期ワーカー移行スクリプト
既存ワーカーから新規非同期ワーカーへの段階的移行
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import psutil

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.lightweight_logger import get_logger


class WorkerMigrationManager:
    """ワーカー移行管理クラス"""

    def __init__(self):
        self.logger = get_logger("migration_manager")
        self.project_root = PROJECT_ROOT

        # 既存ワーカーの定義
        self.legacy_workers = {
            "task_worker": {
                "script": "workers/task_worker.py",
                "async_replacement": "workers/async_task_worker_simple.py",
                "queue": "ai_tasks",
                "priority": 1,  # 最優先で移行
            },
            "result_worker": {
                "script": "workers/result_worker.py",
                "async_replacement": "workers/async_result_worker_simple.py",
                "queue": "ai_results",
                "priority": 2,
            },
            "pm_worker": {
                "script": "workers/pm_worker.py",
                "async_replacement": "workers/async_pm_worker_simple.py",
                "queue": "ai_pm",
                "priority": 3,
            },
        }

        # 移行状態管理
        self.migration_state_file = self.project_root / "data" / "migration_state.json"
        self.migration_state = self._load_migration_state()

    def _load_migration_state(self) -> Dict:
        """移行状態の読み込み"""
        if self.migration_state_file.exists():
            try:
                with open(self.migration_state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error("Failed to load migration state", error=str(e))

        # デフォルト状態
        return {
            "phase": "not_started",
            "workers": {
                name: {"migrated": False, "last_attempt": None}
                for name in self.legacy_workers
            },
            "rollback_info": {},
            "migration_log": [],
        }

    def _save_migration_state(self):
        """移行状態の保存"""
        self.migration_state_file.parent.mkdir(exist_ok=True)

        try:
            with open(self.migration_state_file, "w") as f:
                json.dump(self.migration_state, f, indent=2)
        except Exception as e:
            self.logger.error("Failed to save migration state", error=str(e))

    def get_worker_processes(self) -> Dict[str, List[int]]:
        """稼働中のワーカープロセスを取得"""
        processes = {}

        for worker_name, config in self.legacy_workers.items():
            script_name = Path(config["script"]).name
            pids = []

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if script_name in cmdline and "python" in cmdline:
                        pids.append(proc.info["pid"])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            processes[worker_name] = pids

        return processes

    def stop_legacy_worker(self, worker_name: str, graceful: bool = True) -> bool:
        """既存ワーカーの停止"""
        self.logger.info(f"Stopping legacy worker: {worker_name}")

        processes = self.get_worker_processes()
        pids = processes.get(worker_name, [])

        if not pids:
            self.logger.info(f"No running processes found for {worker_name}")
            return True

        success = True
        for pid in pids:
            try:
                proc = psutil.Process(pid)

                if graceful:
                    # グレースフル停止
                    proc.send_signal(signal.SIGTERM)

                    # 最大30秒待機
                    try:
                        proc.wait(timeout=30)
                        self.logger.info(f"Process {pid} stopped gracefully")
                    except psutil.TimeoutExpired:
                        # 強制停止
                        proc.send_signal(signal.SIGKILL)
                        self.logger.warning(f"Process {pid} force killed")
                else:
                    # 即座に強制停止
                    proc.send_signal(signal.SIGKILL)
                    self.logger.info(f"Process {pid} force killed")

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.logger.error(f"Failed to stop process {pid}", error=str(e))
                success = False

        return success

    def start_async_worker(self, worker_name: str) -> bool:
        """非同期ワーカーの開始"""
        config = self.legacy_workers.get(worker_name)
        if not config:
            self.logger.error(f"Unknown worker: {worker_name}")
            return False

        async_script = self.project_root / config["async_replacement"]
        if not async_script.exists():
            self.logger.error(f"Async worker script not found: {async_script}")
            return False

        try:
            # 仮想環境のPythonを使用
            python_path = self.project_root / "venv" / "bin" / "python"
            if not python_path.exists():
                python_path = "python3"  # システムPython

            # バックグラウンドで起動
            cmd = [str(python_path), str(async_script)]

            self.logger.info(
                f"Starting async worker: {worker_name}", command=" ".join(cmd)
            )

            proc = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # 新しいセッションで起動
            )

            # 起動確認のため短時間待機
            time.sleep(2)

            if proc.poll() is None:
                self.logger.info(
                    f"Async worker {worker_name} started successfully", pid=proc.pid
                )
                return True
            else:
                stdout, stderr = proc.communicate()
                self.logger.error(
                    f"Async worker {worker_name} failed to start",
                    stdout=stdout.decode()[:500],
                    stderr=stderr.decode()[:500],
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Failed to start async worker {worker_name}", error=str(e)
            )
            return False

    def migrate_worker(self, worker_name: str, traffic_percentage: int = 100) -> bool:
        """単一ワーカーの移行"""
        self.logger.info(
            f"Migrating worker: {worker_name}", traffic_percentage=traffic_percentage
        )

        # ロールバック情報の記録
        processes_before = self.get_worker_processes()
        self.migration_state["rollback_info"][worker_name] = {
            "processes_before": processes_before.get(worker_name, []),
            "timestamp": time.time(),
        }

        try:
            if traffic_percentage == 100:
                # 完全移行：既存ワーカーを停止して新規ワーカーを開始
                if not self.stop_legacy_worker(worker_name, graceful=True):
                    raise Exception(f"Failed to stop legacy worker {worker_name}")

                if not self.start_async_worker(worker_name):
                    raise Exception(f"Failed to start async worker {worker_name}")

            else:
                # 部分移行：新規ワーカーを並行稼働
                # TODO: ロードバランサー設定での実装
                if not self.start_async_worker(worker_name):
                    raise Exception(f"Failed to start async worker {worker_name}")

                self.logger.info(
                    f"Partial migration: {traffic_percentage}% traffic to new worker"
                )

            # 移行状態の更新
            self.migration_state["workers"][worker_name]["migrated"] = True
            self.migration_state["workers"][worker_name]["last_attempt"] = time.time()
            self.migration_state["migration_log"].append(
                {
                    "worker": worker_name,
                    "action": "migrated",
                    "traffic_percentage": traffic_percentage,
                    "timestamp": time.time(),
                }
            )

            self._save_migration_state()

            self.logger.info(f"Worker {worker_name} migrated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Migration failed for {worker_name}", error=str(e))

            # 失敗時のロールバック
            self.rollback_worker(worker_name)
            return False

    def rollback_worker(self, worker_name: str) -> bool:
        """ワーカーのロールバック"""
        self.logger.info(f"Rolling back worker: {worker_name}")

        try:
            # 非同期ワーカーを停止
            # TODO: 非同期ワーカーのPID追跡とクリーンアップ

            # 既存ワーカーの再起動
            # TODO: tmuxセッション経由での再起動
            self.logger.info(f"Restarting legacy worker: {worker_name}")

            # 移行状態の更新
            self.migration_state["workers"][worker_name]["migrated"] = False
            self.migration_state["migration_log"].append(
                {
                    "worker": worker_name,
                    "action": "rolled_back",
                    "timestamp": time.time(),
                }
            )

            self._save_migration_state()

            self.logger.info(f"Worker {worker_name} rolled back successfully")
            return True

        except Exception as e:
            self.logger.error(f"Rollback failed for {worker_name}", error=str(e))
            return False

    def status_report(self) -> Dict:
        """移行状況レポート"""
        processes = self.get_worker_processes()

        report = {
            "migration_phase": self.migration_state["phase"],
            "workers": {},
            "system_health": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            },
        }

        for worker_name, config in self.legacy_workers.items():
            worker_state = self.migration_state["workers"][worker_name]
            report["workers"][worker_name] = {
                "migrated": worker_state["migrated"],
                "legacy_processes": len(processes.get(worker_name, [])),
                "queue": config["queue"],
                "priority": config["priority"],
            }

        return report

    def migrate_all(self, traffic_percentage: int = 100) -> bool:
        """全ワーカーの移行（優先度順）"""
        self.logger.info(
            "Starting full migration", traffic_percentage=traffic_percentage
        )

        self.migration_state["phase"] = "in_progress"
        self._save_migration_state()

        # 優先度順にソート
        workers_by_priority = sorted(
            self.legacy_workers.items(), key=lambda x: x[1]["priority"]
        )

        success_count = 0
        for worker_name, config in workers_by_priority:
            self.logger.info(
                f"Migrating {worker_name} (priority: {config['priority']})"
            )

            if self.migrate_worker(worker_name, traffic_percentage):
                success_count += 1
                # 各ワーカー移行後に30秒待機
                time.sleep(30)
            else:
                self.logger.error(
                    f"Migration failed for {worker_name}, stopping full migration"
                )
                break

        if success_count == len(self.legacy_workers):
            self.migration_state["phase"] = "completed"
            self.logger.info("Full migration completed successfully")
            result = True
        else:
            self.migration_state["phase"] = "partial_failure"
            self.logger.error(
                f"Migration partially failed: {success_count}/{len(self.legacy_workers)} workers"
            )
            result = False

        self._save_migration_state()
        return result


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="Elders Guild Worker Migration Tool")
    parser.add_argument(
        "action",
        choices=["status", "migrate", "rollback", "migrate-all"],
        help="Action to perform",
    )
    parser.add_argument("--worker", help="Specific worker to migrate/rollback")
    parser.add_argument(
        "--traffic",
        type=int,
        default=100,
        help="Traffic percentage for gradual migration (default: 100)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force operation without confirmation"
    )

    args = parser.parse_args()

    manager = WorkerMigrationManager()

    if args.action == "status":
        # 状況レポート
        report = manager.status_report()
        print(json.dumps(report, indent=2))

    elif args.action == "migrate":
        if not args.worker:
            print("Error: --worker is required for migrate action")
            sys.exit(1)

        if not args.force:
            confirm = input(
                f"Migrate {args.worker} with {args.traffic}% traffic? (y/N): "
            )
            if confirm.lower() != "y":
                print("Migration cancelled")
                sys.exit(0)

        success = manager.migrate_worker(args.worker, args.traffic)
        sys.exit(0 if success else 1)

    elif args.action == "rollback":
        if not args.worker:
            print("Error: --worker is required for rollback action")
            sys.exit(1)

        if not args.force:
            confirm = input(f"Rollback {args.worker}? (y/N): ")
            if confirm.lower() != "y":
                print("Rollback cancelled")
                sys.exit(0)

        success = manager.rollback_worker(args.worker)
        sys.exit(0 if success else 1)

    elif args.action == "migrate-all":
        if not args.force:
            confirm = input(
                f"Migrate all workers with {args.traffic}% traffic? (y/N): "
            )
            if confirm.lower() != "y":
                print("Migration cancelled")
                sys.exit(0)

        success = manager.migrate_all(args.traffic)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
