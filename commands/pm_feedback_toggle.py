#!/usr/bin/env python3
"""
PM フィードバック機能 オン/オフ切り替えコマンド
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pika

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class PMFeedbackToggleCommand(BaseCommand):
    """PMフィードバック機能の有効/無効を切り替える"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            name="pm-feedback-toggle",
            description="PMフィードバック機能の有効/無効を切り替え",
            version="1.0.0",
        )

    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            # パラメータ解析
            enable = True  # デフォルトは有効
            if args and len(args) > 0:
                # Complex condition - consider breaking down
                enable = args[0].lower() in [
                    "true",
                    "1",
                    "on",
                    "enable",
                    "enabled",
                    "yes",
                    "y",
                ]

            # PMタスクキューにメッセージ送信
            task_data = {
                "task_id": f"feedback_toggle_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "command": "toggle_feedback",
                "params": {"enable": enable},
            }

            success = self._send_pm_command(task_data)

            if success:
                status = "有効" if enable else "無効"
                return CommandResult(
                    success=True, message=f"✅ PMフィードバック機能を{status}に設定しました"
                )
            else:
                return CommandResult(success=False, message="❌ PMフィードバック設定の送信に失敗しました")

        except Exception as e:
            # Handle specific exception case
            return CommandResult(success=False, message=f"❌ エラー: {str(e)}")

    def _send_pm_command(self, task_data: dict) -> bool:
        """PMワーカーにコマンド送信"""
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()

            # pm_task_queueに送信
            channel.queue_declare(queue="pm_task_queue", durable=True)

            channel.basic_publish(
                exchange="",
                routing_key="pm_task_queue",
                body=json.dumps(task_data, ensure_ascii=False),
                properties=pika.BasicProperties(delivery_mode=2, priority=8),  # 永続化
            )

            connection.close()
            return True

        except Exception as e:
            # Handle specific exception case
            print(f"❌ RabbitMQ送信エラー: {e}")
            return False


def main():
    # Core functionality implementation
    command = PMFeedbackToggleCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
