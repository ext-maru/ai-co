#!/usr/bin/env python3
"""
キュー状態確認
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pika
from rich.console import Console
from rich.table import Table

from commands.base_command import BaseCommand, CommandResult


class AIQueueCommand(BaseCommand):
    """キュー状態確認コマンド"""

    def __init__(self):
        super().__init__(name="ai-queue", description="キュー状態確認", version="1.0.0")
        self.console = Console()

    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument("--json", action="store_true", help="JSON形式で出力")
        self.parser.add_argument("--watch", "-w", action="store_true", help="リアルタイム監視")

    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            # RabbitMQ接続
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()

            # キュー情報取得
            queues = [
                "ai_tasks",
                "ai_pm",
                "ai_results",
                "dialog_task_queue",
                "dialog_response_queue",
                "user_input_queue",
            ]

            queue_info = {}
            for queue_name in queues:
                try:
                    method = channel.queue_declare(queue=queue_name, passive=True)
                    queue_info[queue_name] = {
                        "messages": method.method.message_count,
                        "consumers": method.method.consumer_count,
                    }
                except Exception:
                    queue_info[queue_name] = {"messages": 0, "consumers": 0}

            connection.close()

            if args.json:
                import json

                return CommandResult(
                    success=True, message=json.dumps(queue_info, indent=2)
                )

            # テーブル表示
            table = Table(title="🔄 Elders Guild キュー状態")
            table.add_column("キュー名", style="cyan")
            table.add_column("メッセージ数", justify="right", style="yellow")
            table.add_column("コンシューマー数", justify="right", style="green")

            for queue_name, info in queue_info.items():
                table.add_row(queue_name, str(info["messages"]), str(info["consumers"]))

            self.console.print(table)

            # サマリー
            total_messages = sum(info["messages"] for info in queue_info.values())
            if total_messages > 0:
                self.console.print(
                    f"\n⚠️  処理待ちメッセージ: {total_messages}件", style="yellow"
                )
            else:
                self.console.print("\n✅ すべてのキューが空です", style="green")

            return CommandResult(success=True)

        except Exception as e:
            return CommandResult(success=False, message=f"キュー情報の取得に失敗: {str(e)}")


def main():
    command = AIQueueCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
