"""
State Manager Component

ワーカーの状態を保存・復元するコンポーネント
"""

import json
import logging
import os
import pickle
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class StateManager:
    """ワーカー状態の保存と復元を管理"""

    def __init__(self, state_dir: str = "/home/aicompany/ai_co/data/worker_states"):
        """
        初期化

        Args:
            state_dir: 状態ファイルを保存するディレクトリ
        """
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)

        self.state_cache = {}
        logger.info(f"StateManager initialized with directory: {state_dir}")

    def save_worker_state(self, worker_name: str, state_data: Dict[str, Any]) -> bool:
        """
        ワーカーの状態を保存

        Args:
            worker_name: ワーカー名
            state_data: 保存する状態データ

        Returns:
            成功した場合True
        """
        try:
            # 状態データに追加情報を付与
            full_state = {
                "worker_name": worker_name,
                "timestamp": datetime.now().isoformat(),
                "state_data": state_data,
                "queue_state": self._get_queue_state(worker_name),
                "process_info": self._get_process_info(state_data),
            }

            # ファイルに保存
            state_file = os.path.join(self.state_dir, f"{worker_name}_state.json")
            with open(state_file, "w") as f:
                json.dump(full_state, f, indent=2, ensure_ascii=False)

            # キャッシュにも保存
            self.state_cache[worker_name] = full_state

            logger.info(f"Saved state for {worker_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save state for {worker_name}: {e}")
            return False

    def restore_worker_state(self, worker_name: str) -> Optional[Dict[str, Any]]:
        """
        ワーカーの状態を復元

        Args:
            worker_name: ワーカー名

        Returns:
            復元された状態データ、存在しない場合None
        """
        try:
            # キャッシュから取得を試みる
            if worker_name in self.state_cache:
                return self.state_cache[worker_name]

            # ファイルから読み込み
            state_file = os.path.join(self.state_dir, f"{worker_name}_state.json")
            if os.path.exists(state_file):
                with open(state_file, "r") as f:
                    full_state = json.load(f)

                # キャッシュに保存
                self.state_cache[worker_name] = full_state

                logger.info(f"Restored state for {worker_name}")
                return full_state

            logger.warning(f"No saved state found for {worker_name}")
            return None

        except Exception as e:
            logger.error(f"Failed to restore state for {worker_name}: {e}")
            return None

    def _get_queue_state(self, worker_name: str) -> Dict[str, Any]:
        """
        キューの状態を取得

        Args:
            worker_name: ワーカー名

        Returns:
            キュー状態
        """
        queue_state = {"saved_at": datetime.now().isoformat()}

        # ワーカーごとのキュー名マッピング
        queue_mapping = {
            "task_worker": "worker_tasks",
            "pm_worker": "ai_tasks",
            "result_worker": "results",
            "error_intelligence_worker": "error_intelligence",
        }

        queue_name = queue_mapping.get(worker_name)
        if queue_name:
            try:
                import subprocess

                # キューの状態を取得
                cmd = f"sudo rabbitmqctl list_queues name messages consumers | grep {queue_name}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split()
                    if len(parts) >= 3:
                        queue_state["queue_name"] = queue_name
                        queue_state["messages"] = int(parts[1])
                        queue_state["consumers"] = int(parts[2])

            except Exception as e:
                logger.error(f"Failed to get queue state: {e}")

        return queue_state

    def _get_process_info(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        プロセス情報を取得

        Args:
            state_data: 健康状態データ

        Returns:
            プロセス情報
        """
        process_info = {}

        # 健康状態データからプロセス情報を抽出
        checks = state_data.get("checks", {})
        process = checks.get("process", {})
        resources = checks.get("resources", {})

        if process.get("exists"):
            process_info["pid"] = process.get("pid")
            process_info["status"] = process.get("status")
            process_info["cpu_percent"] = resources.get("cpu_percent", 0)
            process_info["memory_mb"] = resources.get("memory_mb", 0)

        return process_info

    def save_recovery_checkpoint(
        self, worker_name: str, recovery_stage: str, data: Dict[str, Any]
    ) -> bool:
        """
        復旧プロセスのチェックポイントを保存

        Args:
            worker_name: ワーカー名
            recovery_stage: 復旧ステージ
            data: チェックポイントデータ

        Returns:
            成功した場合True
        """
        try:
            checkpoint = {
                "worker_name": worker_name,
                "recovery_stage": recovery_stage,
                "timestamp": datetime.now().isoformat(),
                "data": data,
            }

            # チェックポイントファイルに保存
            checkpoint_file = os.path.join(
                self.state_dir, f"{worker_name}_checkpoint.json"
            )

            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved checkpoint for {worker_name} at stage {recovery_stage}")
            return True

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False

    def get_recovery_checkpoint(self, worker_name: str) -> Optional[Dict[str, Any]]:
        """
        復旧チェックポイントを取得

        Args:
            worker_name: ワーカー名

        Returns:
            チェックポイントデータ
        """
        try:
            checkpoint_file = os.path.join(
                self.state_dir, f"{worker_name}_checkpoint.json"
            )

            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, "r") as f:
                    return json.load(f)

            return None

        except Exception as e:
            logger.error(f"Failed to get checkpoint: {e}")
            return None

    def cleanup_old_states(self, days: int = 7):
        """
        古い状態ファイルをクリーンアップ

        Args:
            days: 保持日数
        """
        try:
            import glob
            from datetime import timedelta

            cutoff_time = datetime.now() - timedelta(days=days)

            # 状態ファイルを検索
            state_files = glob.glob(os.path.join(self.state_dir, "*_state.json"))
            checkpoint_files = glob.glob(
                os.path.join(self.state_dir, "*_checkpoint.json")
            )

            cleaned_count = 0

            for file_path in state_files + checkpoint_files:
                try:
                    # ファイルの更新時刻を確認
                    mtime = os.path.getmtime(file_path)
                    file_time = datetime.fromtimestamp(mtime)

                    if file_time < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.info(f"Removed old state file: {file_path}")

                except Exception as e:
                    logger.error(f"Failed to clean up {file_path}: {e}")

            logger.info(f"Cleaned up {cleaned_count} old state files")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def get_all_saved_states(self) -> Dict[str, Dict[str, Any]]:
        """
        保存されている全ての状態を取得

        Returns:
            ワーカー名をキーとした状態辞書
        """
        all_states = {}

        try:
            import glob

            state_files = glob.glob(os.path.join(self.state_dir, "*_state.json"))

            for file_path in state_files:
                try:
                    with open(file_path, "r") as f:
                        state = json.load(f)
                        worker_name = state.get("worker_name")
                        if worker_name:
                            all_states[worker_name] = state

                except Exception as e:
                    logger.error(f"Failed to read {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to get all states: {e}")

        return all_states
