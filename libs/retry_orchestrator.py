#!/usr/bin/env python3
"""
リトライオーケストレーター
修正後のタスクリトライを管理し、成功を確認する
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging
from enum import Enum

# プロジェクトルートをPythonパスに追加
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager, get_config
from libs.slack_notifier import SlackNotifier


class RetryStatus(Enum):
    """リトライステータス"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"


class RetryOrchestrator(BaseManager):
    """修正後のリトライを管理するオーケストレーター"""

    def __init__(self):
        super().__init__("RetryOrchestrator")
        self.config = get_config()
        self.slack_notifier = SlackNotifier()

        # リトライ設定
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 5,  # 秒
            "max_delay": 300,  # 5分
            "backoff_factor": 2,
            "jitter": True,
        }

        # リトライ履歴（メモリ内管理）
        self.retry_history = {}

        # カテゴリ別リトライ戦略
        self.retry_strategies = {
            "dependency": {
                "max_retries": 3,
                "base_delay": 10,
                "verify_before_retry": True,
            },
            "filesystem": {
                "max_retries": 2,
                "base_delay": 5,
                "verify_before_retry": True,
            },
            "network": {
                "max_retries": 5,
                "base_delay": 30,
                "exponential_backoff": True,
            },
            "rabbitmq": {
                "max_retries": 3,
                "base_delay": 20,
                "health_check_required": True,
            },
            "permission": {
                "max_retries": 2,
                "base_delay": 5,
                "verify_before_retry": True,
            },
        }

    def initialize(self) -> bool:
        """初期化処理"""
        return True

    def should_retry(self, task_info: Dict, error_info: Dict, fix_result: Dict) -> Dict:
        """リトライすべきかを判断"""
        decision = {
            "should_retry": False,
            "reason": "",
            "delay": 0,
            "retry_count": 0,
            "max_retries": self.retry_config["max_retries"],
        }

        task_id = task_info.get("task_id")
        if not task_id:
            decision["reason"] = "No task_id provided"
            return decision

        # リトライ履歴を確認
        retry_info = self.retry_history.get(
            task_id, {"count": 0, "last_attempt": None, "status": RetryStatus.PENDING}
        )

        # 最大リトライ数チェック
        category = error_info.get("category", "unknown")
        strategy = self.retry_strategies.get(category, self.retry_config)
        max_retries = strategy.get("max_retries", self.retry_config["max_retries"])

        if retry_info["count"] >= max_retries:
            decision["reason"] = f"Max retries ({max_retries}) exceeded"
            decision["retry_count"] = retry_info["count"]
            decision["max_retries"] = max_retries
            self._update_retry_status(task_id, RetryStatus.MAX_RETRIES_EXCEEDED)
            return decision

        # 修正が成功した場合のみリトライ
        if not fix_result.get("success"):
            decision["reason"] = "Fix was not successful"
            return decision

        # カテゴリ別の判断
        if category in self.retry_strategies:
            strategy_decision = self._apply_category_strategy(
                category, task_info, error_info, fix_result, retry_info
            )
            if not strategy_decision["should_retry"]:
                decision.update(strategy_decision)
                return decision

        # リトライ決定
        decision["should_retry"] = True
        decision["reason"] = "Fix successful, retrying original task"
        decision["delay"] = self._calculate_delay(retry_info["count"], strategy)
        decision["retry_count"] = retry_info["count"] + 1
        decision["max_retries"] = max_retries

        return decision

    def orchestrate_retry(
        self, task_info: Dict, error_info: Dict, fix_result: Dict
    ) -> Dict:
        """リトライを実行"""
        result = {
            "retry_attempted": False,
            "retry_success": False,
            "retry_count": 0,
            "final_status": None,
            "elapsed_time": 0,
            "error": None,
        }

        start_time = time.time()
        task_id = task_info.get("task_id")

        try:
            # リトライ判断
            retry_decision = self.should_retry(task_info, error_info, fix_result)

            if not retry_decision["should_retry"]:
                result["final_status"] = "retry_not_needed"
                result["error"] = retry_decision["reason"]
                return result

            # リトライ情報更新
            self._update_retry_info(task_id, retry_decision["retry_count"])
            result["retry_count"] = retry_decision["retry_count"]

            # 遅延実行
            if retry_decision["delay"] > 0:
                self.logger.info(
                    f"Waiting {retry_decision['delay']}s before retry "
                    f"(attempt {retry_decision['retry_count']}/{retry_decision['max_retries']})"
                )
                time.sleep(retry_decision["delay"])

            # タスクの再構築
            retry_task = self._rebuild_task(task_info, error_info, fix_result)

            # リトライ実行
            retry_result = self._execute_retry(retry_task, error_info)

            if retry_result["success"]:
                result["retry_attempted"] = True
                result["retry_success"] = True
                result["final_status"] = RetryStatus.SUCCESS.value
                self._update_retry_status(task_id, RetryStatus.SUCCESS)

                # 成功通知
                self._notify_retry_success(task_info, retry_decision["retry_count"])
            else:
                result["retry_attempted"] = True
                result["error"] = retry_result.get("error", "Retry failed")

                # 追加リトライが必要か判断
                if retry_decision["retry_count"] < retry_decision["max_retries"]:
                    result["final_status"] = RetryStatus.IN_PROGRESS.value
                    self._update_retry_status(task_id, RetryStatus.IN_PROGRESS)
                else:
                    result["final_status"] = RetryStatus.FAILED.value
                    self._update_retry_status(task_id, RetryStatus.FAILED)
                    self._notify_retry_failure(task_info, retry_decision["retry_count"])

        except Exception as e:
            result["error"] = str(e)
            result["final_status"] = "error"
            self.logger.error(f"Error in retry orchestration: {e}")

        finally:
            result["elapsed_time"] = time.time() - start_time

        return result

    def _apply_category_strategy(
        self,
        category: str,
        task_info: Dict,
        error_info: Dict,
        fix_result: Dict,
        retry_info: Dict,
    ) -> Dict:
        """カテゴリ別の戦略を適用"""
        strategy = self.retry_strategies[category]
        decision = {"should_retry": True, "reason": ""}

        # 検証が必要な場合
        if strategy.get("verify_before_retry"):
            if not self._verify_fix_persistence(category, fix_result):
                decision["should_retry"] = False
                decision["reason"] = "Fix verification failed"
                return decision

        # ヘルスチェックが必要な場合
        if strategy.get("health_check_required"):
            if not self._perform_health_check(category):
                decision["should_retry"] = False
                decision["reason"] = "Health check failed"
                return decision

        return decision

    def _calculate_delay(self, retry_count: int, strategy: Dict) -> float:
        """リトライ遅延を計算"""
        base_delay = strategy.get("base_delay", self.retry_config["base_delay"])

        if strategy.get("exponential_backoff"):
            delay = base_delay * (self.retry_config["backoff_factor"] ** retry_count)
            delay = min(delay, self.retry_config["max_delay"])
        else:
            delay = base_delay

        # ジッター追加
        if self.retry_config["jitter"]:
            import random

            jitter = random.uniform(0, delay * 0.1)  # 最大10%のジッター
            delay += jitter

        return delay

    def _update_retry_info(self, task_id: str, retry_count: int):
        """リトライ情報を更新"""
        self.retry_history[task_id] = {
            "count": retry_count,
            "last_attempt": datetime.now(),
            "status": RetryStatus.IN_PROGRESS,
        }

    def _update_retry_status(self, task_id: str, status: RetryStatus):
        """リトライステータスを更新"""
        if task_id in self.retry_history:
            self.retry_history[task_id]["status"] = status

    def _rebuild_task(
        self, original_task: Dict, error_info: Dict, fix_result: Dict
    ) -> Dict:
        """リトライ用にタスクを再構築"""
        retry_task = original_task.copy()

        # リトライメタデータを追加
        retry_task["retry_metadata"] = {
            "original_error": error_info.get("error_text", ""),
            "fix_applied": fix_result.get("strategy_used", ""),
            "fix_command": fix_result.get("command_executed", ""),
            "retry_timestamp": datetime.now().isoformat(),
        }

        # リトライカウントを更新
        retry_task["retry_count"] = retry_task.get("retry_count", 0) + 1

        return retry_task

    def _execute_retry(self, retry_task: Dict, error_info: Dict) -> Dict:
        """リトライを実行"""
        from libs.task_sender import TaskSender

        try:
            sender = TaskSender()

            # 元のキューを特定
            worker_type = error_info.get("worker_type", "task")
            queue_map = {"task": "ai_tasks", "pm": "ai_pm", "result": "ai_results"}
            target_queue = queue_map.get(worker_type, "ai_tasks")

            # タスクを送信
            sender.send_to_queue(target_queue, retry_task)

            # 実際の結果確認を実装
            # タスクIDを生成
            task_id = retry_task.get("task_id", str(uuid.uuid4()))

            # 結果を待つ（最大30秒）
            max_wait_time = 30
            check_interval = 1
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                # 結果キューまたはデータベースから結果を取得
                result = self._check_task_result(task_id, target_queue)

                if result is not None:
                    # 結果が見つかった
                    if result.get("status") == "completed":
                        return {
                            "success": True,
                            "result": result.get("result"),
                            "execution_time": elapsed_time,
                        }
                    elif result.get("status") == "failed":
                        return {
                            "success": False,
                            "error": result.get("error", "Task failed"),
                            "execution_time": elapsed_time,
                        }

                # まだ処理中
                time.sleep(check_interval)
                elapsed_time += check_interval

            # タイムアウト
            return {
                "success": False,
                "error": "Task execution timed out",
                "timeout": max_wait_time,
            }

        except Exception as e:
            self.logger.error(f"Retry execution failed: {e}")
            return {"success": False, "error": str(e)}

    def _check_task_result(self, task_id: str, queue_name: str) -> Optional[Dict]:
        """タスクの結果を確認"""
        try:
            # タスク結果データベースから確認
            result_file = PROJECT_ROOT / "data" / "task_results" / f"{task_id}.json"
            if result_file.exists():
                with open(result_file, "r") as f:
                    return json.load(f)

            # キューから結果を確認（RabbitMQ接続が必要な場合）
            # ここでは簡易的にファイルベースで実装
            queue_result_file = (
                PROJECT_ROOT / "data" / "queue_results" / queue_name / f"{task_id}.json"
            )
            if queue_result_file.exists():
                with open(queue_result_file, "r") as f:
                    return json.load(f)

            # ワーカーステータスファイルから確認
            worker_status_file = (
                PROJECT_ROOT / "data" / "worker_status" / f"{task_id}_status.json"
            )
            if worker_status_file.exists():
                with open(worker_status_file, "r") as f:
                    status_data = json.load(f)
                    # ステータスデータを結果形式に変換
                    if status_data.get("completed"):
                        return {
                            "status": "completed",
                            "result": status_data.get("result"),
                            "timestamp": status_data.get("timestamp"),
                        }
                    elif status_data.get("failed"):
                        return {
                            "status": "failed",
                            "error": status_data.get("error", "Unknown error"),
                            "timestamp": status_data.get("timestamp"),
                        }

            # 結果が見つからない場合はNone
            return None

        except Exception as e:
            self.logger.error(f"Error checking task result: {e}")
            return None

    def _verify_fix_persistence(self, category: str, fix_result: Dict) -> bool:
        """修正が永続的かを検証"""
        # カテゴリ別の検証ロジック
        if category == "dependency":
            # パッケージがインストールされているか確認
            if "pip install" in fix_result.get("command_executed", ""):
                package = fix_result.get("command_executed", "").split()[-1]
                return self._check_package_installed(package)

        elif category == "filesystem":
            # ファイル/ディレクトリが存在するか確認
            return True  # AutoFixExecutorで既に検証済み

        elif category == "permission":
            # 権限が正しく設定されているか確認
            return True  # AutoFixExecutorで既に検証済み

        return True

    def _check_package_installed(self, package: str) -> bool:
        """パッケージがインストールされているか確認"""
        try:
            import subprocess

            result = subprocess.run(
                ["pip", "show", package], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _perform_health_check(self, category: str) -> bool:
        """サービスのヘルスチェック"""
        if category == "rabbitmq":
            return self._check_rabbitmq_health()
        elif category == "network":
            return self._check_network_health()
        return True

    def _check_rabbitmq_health(self) -> bool:
        """RabbitMQのヘルスチェック"""
        try:
            import subprocess

            result = subprocess.run(
                ["sudo", "rabbitmqctl", "status"], capture_output=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def _check_network_health(self) -> bool:
        """ネットワークのヘルスチェック"""
        try:
            import subprocess

            result = subprocess.run(
                ["ping", "-c", "1", "8.8.8.8"], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _notify_retry_success(self, task_info: Dict, retry_count: int):
        """リトライ成功を通知"""
        message = f"""
✅ **タスクリトライ成功**

**タスクID**: {task_info.get('task_id')}
**リトライ回数**: {retry_count}
**タスクタイプ**: {task_info.get('task_type')}

エラー修正後のリトライが成功しました。
"""
        try:
            self.slack_notifier.send_message(message)
        except:
            self.logger.warning("Slack notification failed")

    def _notify_retry_failure(self, task_info: Dict, retry_count: int):
        """リトライ失敗を通知"""
        message = f"""
❌ **タスクリトライ失敗**

**タスクID**: {task_info.get('task_id')}
**試行回数**: {retry_count}
**タスクタイプ**: {task_info.get('task_type')}

修正後もタスクの実行に失敗しました。
手動での確認が必要です。
"""
        try:
            self.slack_notifier.send_message(message)
        except:
            self.logger.warning("Slack notification failed")

    def get_retry_statistics(self) -> Dict:
        """リトライ統計を取得"""
        total_tasks = len(self.retry_history)
        status_counts = {}

        for task_id, info in self.retry_history.items():
            status = (
                info["status"].value
                if isinstance(info["status"], RetryStatus)
                else info["status"]
            )
            status_counts[status] = status_counts.get(status, 0) + 1

        successful = status_counts.get(RetryStatus.SUCCESS.value, 0)
        failed = status_counts.get(RetryStatus.FAILED.value, 0)
        in_progress = status_counts.get(RetryStatus.IN_PROGRESS.value, 0)
        max_retries_exceeded = status_counts.get(
            RetryStatus.MAX_RETRIES_EXCEEDED.value, 0
        )

        return {
            "total_retry_tasks": total_tasks,
            "successful_retries": successful,
            "failed_retries": failed,
            "in_progress": in_progress,
            "max_retries_exceeded": max_retries_exceeded,
            "success_rate": (successful / total_tasks * 100) if total_tasks > 0 else 0,
            "status_breakdown": status_counts,
        }

    def cleanup_old_entries(self, hours: int = 24):
        """古いエントリをクリーンアップ"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        tasks_to_remove = []
        for task_id, info in self.retry_history.items():
            if info["last_attempt"] and info["last_attempt"] < cutoff_time:
                if info["status"] in [
                    RetryStatus.SUCCESS,
                    RetryStatus.FAILED,
                    RetryStatus.MAX_RETRIES_EXCEEDED,
                ]:
                    tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.retry_history[task_id]

        self.logger.info(f"Cleaned up {len(tasks_to_remove)} old retry entries")

        return len(tasks_to_remove)


if __name__ == "__main__":
    # テスト実行
    orchestrator = RetryOrchestrator()

    # テストケース
    task_info = {"task_id": "test_task_001", "task_type": "code", "prompt": "Test task"}

    error_info = {
        "category": "dependency",
        "error_text": "ModuleNotFoundError: No module named 'requests'",
        "worker_type": "task",
    }

    fix_result = {
        "success": True,
        "strategy_used": "dependency.pip_install",
        "command_executed": "pip install requests",
    }

    print("=== RetryOrchestrator Test ===")

    # リトライ判断テスト
    decision = orchestrator.should_retry(task_info, error_info, fix_result)
    print(f"Retry decision: {json.dumps(decision, indent=2)}")

    # リトライ実行テスト
    result = orchestrator.orchestrate_retry(task_info, error_info, fix_result)
    print(f"\nRetry result: {json.dumps(result, indent=2)}")

    # 統計情報
    stats = orchestrator.get_retry_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")
