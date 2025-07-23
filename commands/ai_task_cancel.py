#!/usr/bin/env python3
"""
タスクキャンセル
"""
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AITaskCancelCommand(BaseCommand):
    """タスクキャンセル"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="ai-task-cancel", description="タスクキャンセル", version="1.0.0")

    def add_arguments(self, parser: argparse.ArgumentParser):
        """引数定義"""
        parser.add_argument(
            "--task-id", "-t", type=str, required=True, help="キャンセルするタスクID"
        )
        parser.add_argument("--force", "-f", action="store_true", help="強制キャンセル")
        parser.add_argument("--reason", "-r", type=str, help="キャンセル理由")

    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            # タスクトラッカーを使用してタスクをキャンセル
            from libs.claude_task_tracker import TaskTracker

            tracker = TaskTracker()

            # タスクの存在確認
            task = tracker.get_task(args.task_id)
            if not task:
                return CommandResult(
                    success=False, message=f"タスク '{args.task_id}' が見つかりません"
                )

            # タスクの状態確認
            if task.get("status") == "completed":
                return CommandResult(
                    success=False, message=f"タスク '{args.task_id}' はすでに完了しています"
                )

            if task.get("status") == "cancelled":
                return CommandResult(
                    success=False, message=f"タスク '{args.task_id}' はすでにキャンセルされています"
                )

            # 実行中タスクのキャンセル
            if task.get("status") == "running" and not args.force:
                # Complex condition - consider breaking down
                return CommandResult(
                    success=False,
                    message=f"タスク '{args.task_id}' は実行中です。強制キャンセルする場合は --force を使用してください",
                )

            # タスクキャンセル
            success = tracker.cancel_task(args.task_id, args.reason or "ユーザーがキャンセル")

            if success:
                return CommandResult(
                    success=True, message=f"タスク '{args.task_id}' をキャンセルしました"
                )
            else:
                return CommandResult(
                    success=False, message=f"タスク '{args.task_id}' のキャンセルに失敗しました"
                )

        except ImportError:
            # Handle specific exception case
            return CommandResult(success=False, message="タスクトラッカーが利用できません")
        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"タスクキャンセルエラー: {str(e)}")


def main():
    # Core functionality implementation
    command = AITaskCancelCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
