#!/usr/bin/env python3
"""
PM フィードバック統計情報取得コマンド
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pika

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class PMFeedbackStatsCommand(BaseCommand):
    """PMフィードバック統計情報を取得"""

    def __init__(self):
        super().__init__(
            name="pm-feedback-stats", description="PMフィードバック統計情報を取得", version="1.0.0"
        )

    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            # PMタスクキューにメッセージ送信
            task_data = {
                "task_id": f"feedback_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "command": "feedback_stats",
                "params": {},
            }

            success = self._send_pm_command(task_data)

            if success:
                return CommandResult(
                    success=True, message="📊 PMフィードバック統計情報を要求しました。Slackで結果を確認できます。"
                )
            else:
                return CommandResult(success=False, message="❌ PMフィードバック統計要求の送信に失敗しました")

        except Exception as e:
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
            print(f"❌ RabbitMQ送信エラー: {e}")
            return False


def main():
    command = PMFeedbackStatsCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
