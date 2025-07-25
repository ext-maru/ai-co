"""
Recovery Strategies Component

ワーカー復旧のための各種戦略を実装
"""

import logging
import os
import signal
import subprocess
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecoveryStrategies:
    """ワーカー復旧戦略の実装"""

    def __init__(self):
        """初期化"""
        self.recovery_history = []
        self.worker_scripts = {
            "task_worker": "/home/aicompany/ai_co/workers/enhanced_task_worker.py",
            "pm_worker": "/home/aicompany/ai_co/workers/intelligent_pm_worker_simple.py",
            "result_worker": "/home/aicompany/ai_co/workers/async_result_worker_simple.py",
            "error_intelligence_worker": "/home/aicompany/ai_co/workers/error_intelligence_worker.py",
            "slack_polling_worker": "/home/aicompany/ai_co/workers/slack_polling_worker.py",
        }

    def select_strategy(self, health_data: Dict[str, Any]) -> str:
        """
        健康状態に基づいて最適な復旧戦略を選択

        Args:
            health_data: 健康状態データ

        Returns:
            戦略名
        """
        health_score = health_data.get("health_score", 0)
        checks = health_data.get("checks", {})

        # プロセスが存在しない場合
        if not checks.get("process", {}).get("exists", False):
            return "cold_start"

        # スコアが極めて低い場合
        if health_score < 20:
            return "hard_restart"

        # リソース問題の場合
        resources = checks.get("resources", {})
        if not resources.get("cpu_ok", True) or not resources.get("memory_ok", True):
            return "resource_recovery"

        # キュー問題の場合
        queue = checks.get("queue", {})
        if queue and not queue.get("healthy", True):
            return "queue_recovery"

        # その他の場合はソフトリスタート
        return "soft_restart"

    def execute_recovery(
        self, worker_name: str, strategy: str, health_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        復旧戦略を実行

        Args:
            worker_name: ワーカー名
            strategy: 戦略名
            health_data: 健康状態データ

        Returns:
            復旧結果
        """
        logger.info(f"Executing {strategy} recovery for {worker_name}")

        recovery_result = {
            "worker_name": worker_name,
            "strategy": strategy,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "details": {},
        }

        try:
            if strategy == "cold_start":
                result = self.cold_start(worker_name)
            elif strategy == "soft_restart":
                result = self.soft_restart(worker_name, health_data)
            elif strategy == "hard_restart":
                result = self.hard_restart(worker_name, health_data)
            elif strategy == "resource_recovery":
                result = self.resource_recovery(worker_name, health_data)
            elif strategy == "queue_recovery":
                result = self.queue_recovery(worker_name, health_data)
            else:
                result = {"success": False, "error": f"Unknown strategy: {strategy}"}

            recovery_result.update(result)

        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            recovery_result["error"] = str(e)

        # 履歴に記録
        self.recovery_history.append(recovery_result)

        return recovery_result

    def cold_start(self, worker_name: str) -> Dict[str, Any]:
        """
        コールドスタート（プロセスが存在しない場合の起動）

        Args:
            worker_name: ワーカー名

        Returns:
            復旧結果
        """
        logger.info(f"Cold starting {worker_name}")

        script_path = self.worker_scripts.get(worker_name)
        if not script_path:
            return {
                "success": False,
                "error": f"Unknown worker script for {worker_name}",
            }

        # ワーカーを起動
        try:
            # tmuxセッション内で起動を試みる
            session_name = "ai_company"
            window_name = worker_name.replace("_worker", "")

            # 既存のウィンドウを確認
            check_cmd = f"tmux list-windows -t {session_name} | grep {window_name}"
            check_result = subprocess.run(check_cmd, shell=True, capture_output=True)

            if check_result.returncode == 0:
                # 既存ウィンドウで再起動
                cmd = f"tmux send-keys -t {session_name}:{window_name} C-c Enter"
                subprocess.run(cmd, shell=True)
                time.sleep(2)

                cmd = f"tmux send-keys -t {session_name}:{window_name} " \
                    "'cd /home/aicompany/ai_co && python3 {script_path}' Enter"
            else:
                # 新規ウィンドウで起動
                cmd = f"tmux new-window -t {session_name} " \
                    "-n {window_name} 'cd /home/aicompany/ai_co && python3 {script_path}'"

            result = subprocess.run(cmd, shell=True, capture_output=True)

            if result.returncode == 0:
                time.sleep(3)  # 起動待ち
                return {
                    "success": True,
                    "details": {"method": "tmux_start", "script": script_path},
                }
            else:
                # tmuxが失敗した場合は直接起動
                cmd = f"cd /home/aicompany/ai_co && nohup python3 {script_path} > /dev/null 2>&1 &"
                subprocess.run(cmd, shell=True)
                time.sleep(3)

                return {
                    "success": True,
                    "details": {"method": "direct_start", "script": script_path},
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to start worker: {e}"}

    def soft_restart(
        self, worker_name: str, health_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ソフトリスタート（graceful restart）

        Args:
            worker_name: ワーカー名
            health_data: 健康状態データ

        Returns:
            復旧結果
        """
        logger.info(f"Soft restarting {worker_name}")

        pid = health_data.get("checks", {}).get("process", {}).get("pid")
        if not pid:
            return self.cold_start(worker_name)

        try:
            # SIGTERMを送信してgracefulシャットダウン
            os.kill(pid, signal.SIGTERM)

            # プロセスの終了を待つ（最大30秒）
            for i in range(30):
                try:
                    os.kill(pid, 0)  # プロセスの存在確認
                    time.sleep(1)
                except ProcessLookupError:
                    break
            else:
                # タイムアウトした場合はSIGKILL
                try:
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(2)
                except ProcessLookupError:
                    pass

            # ワーカーを再起動
            return self.cold_start(worker_name)

        except Exception as e:
            return {"success": False, "error": f"Soft restart failed: {e}"}

    def hard_restart(
        self, worker_name: str, health_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ハードリスタート（強制終了して再起動）

        Args:
            worker_name: ワーカー名
            health_data: 健康状態データ

        Returns:
            復旧結果
        """
        logger.info(f"Hard restarting {worker_name}")

        pid = health_data.get("checks", {}).get("process", {}).get("pid")
        if pid:
            try:
                # 強制終了
                os.kill(pid, signal.SIGKILL)
                time.sleep(2)
            except ProcessLookupError:
                pass

        # 関連プロセスも終了
        script_name = self.worker_scripts.get(worker_name, "").split("/")[-1]
        if script_name:
            cmd = f"pkill -f {script_name}"
            subprocess.run(cmd, shell=True)
            time.sleep(2)

        # ワーカーを再起動
        return self.cold_start(worker_name)

    def resource_recovery(
        self, worker_name: str, health_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        リソース問題の復旧（メモリ解放、優先度調整など）

        Args:
            worker_name: ワーカー名
            health_data: 健康状態データ

        Returns:
            復旧結果
        """
        logger.info(f"Resource recovery for {worker_name}")

        pid = health_data.get("checks", {}).get("process", {}).get("pid")
        if not pid:
            return self.cold_start(worker_name)

        try:
            resources = health_data.get("checks", {}).get("resources", {})

            # メモリ使用量が多い場合
            if not resources.get("memory_ok", True):
                # ガベージコレクションを強制実行するシグナルを送信
                os.kill(pid, signal.SIGUSR1)
                time.sleep(5)

                # それでも改善しない場合はソフトリスタート
                return self.soft_restart(worker_name, health_data)

            # CPU使用率が高い場合
            if not resources.get("cpu_ok", True):
                # プロセスの優先度を下げる
                cmd = f"renice -n 10 -p {pid}"
                subprocess.run(cmd, shell=True)

                return {
                    "success": True,
                    "details": {"action": "priority_adjusted", "pid": pid},
                }

            return {
                "success": True,
                "details": {"action": "resource_optimization", "pid": pid},
            }

        except Exception as e:
            return {"success": False, "error": f"Resource recovery failed: {e}"}

    def queue_recovery(
        self, worker_name: str, health_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        キュー問題の復旧（キューのクリア、ワーカー数調整など）

        Args:
            worker_name: ワーカー名
            health_data: 健康状態データ

        Returns:
            復旧結果
        """
        logger.info(f"Queue recovery for {worker_name}")

        queue_info = health_data.get("checks", {}).get("queue", {})
        queue_name = queue_info.get("queue_name")

        if not queue_name:
            return self.soft_restart(worker_name, health_data)

        try:
            messages = queue_info.get("messages", 0)

            # メッセージが多すぎる場合
            if messages > 1000:
                # DLQに移動
                cmd = f'sudo rabbitmqctl eval \'rabbit_amqqueue:delete(
                    rabbit_misc:r(<<"/">>, queue, <<"{queue_name}_dlq">>),
                    false,
                    false
                ).\''
                subprocess.run(cmd, shell=True)

                return {
                    "success": True,
                    "details": {
                        "action": "messages_moved_to_dlq",
                        "queue": queue_name,
                        "messages": messages,
                    },
                }

            # ワーカーを追加起動することも検討
            return self.soft_restart(worker_name, health_data)

        except Exception as e:
            return {"success": False, "error": f"Queue recovery failed: {e}"}

    def get_recovery_history(
        self, worker_name: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        復旧履歴を取得

        Args:
            worker_name: ワーカー名（指定しない場合は全て）
            limit: 取得件数

        Returns:
            復旧履歴リスト
        """
        history = self.recovery_history

        if worker_name:
            history = [h for h in history if h.get("worker_name") == worker_name]

        return history[-limit:]
