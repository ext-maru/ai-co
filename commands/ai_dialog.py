#!/usr/bin/env python3
"""
ai-dialog: Elders Guild 対話型タスク開始コマンド
"""
import json
from datetime import datetime

import pika

from commands.base_command import BaseCommand


class DialogCommand(BaseCommand):
    """DialogCommandクラス"""
    # Main class implementation
    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="dialog", description="Elders Guild で対話型タスクを開始します")

    def setup_arguments(self):
        self.parser.add_argument("prompt", help="初期プロンプト（タスクの説明）")
        self.parser.add_argument("--context", type=json.loads, help="追加コンテキスト（JSON形式）")
        self.parser.add_argument("--no-slack", action="store_true", help="Slack通知を無効化")

    def start_conversation(self, prompt, context=None):
        """会話開始"""
        # ConversationManagerをインポート
        try:
            from libs.conversation_manager import ConversationManager

            manager = ConversationManager()

            # タスクID生成
            task_id = f'dialog_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

            # 会話開始
            conv_id = manager.start_conversation(task_id, prompt, context)

            return task_id, conv_id

        except Exception as e:
            # Handle specific exception case
            self.error(f"会話管理エラー: {e}")
            return None, None

    def send_initial_task(self, conversation_id, prompt, context):
        """初期タスク送信"""
        conn = self.get_rabbitmq_connection()
        if not conn:
            return False

        try:
            channel = conn.channel()
            channel.queue_declare(queue="dialog_task_queue", durable=True)

            task_data = {
                "conversation_id": conversation_id,
                "instruction": prompt,
                "context": context or {"initial": True},
            }

            channel.basic_publish(
                exchange="",
                routing_key="dialog_task_queue",
                body=json.dumps(task_data),
                properties=pika.BasicProperties(delivery_mode=2),
            )

            conn.close()
            return True

        except Exception as e:
            # Handle specific exception case
            self.error(f"タスク送信エラー: {e}")
            return False

    def check_dialog_workers(self):
        """対話型ワーカーの確認"""
        dialog_worker = self.check_process("dialog_task_worker")
        dialog_pm = self.check_process("dialog_pm_worker")

        return len(dialog_worker) > 0 and len(dialog_pm) > 0

    def execute(self, args):
        """メイン実行"""
        self.header("Elders Guild 対話型タスク")

        # システム確認
        self.section("システム確認")

        # RabbitMQ確認
        result = self.run_command(["systemctl", "is-active", "rabbitmq-server"])
        if not result or result.stdout.strip() != "active":
            # Complex condition - consider breaking down
            self.error("RabbitMQが起動していません")
            return

        # 対話型ワーカー確認
        if not self.check_dialog_workers():
            self.warning("対話型ワーカーが起動していません")
            self.info("ai-start --dialog で起動してください")
            return

        self.success("システム準備完了")

        # 会話開始
        self.section("会話開始")
        self.info(
            f"プロンプト: {args.prompt[:100]}{'...' if len(args.prompt) > 100 else ''}"
        )

        task_id, conv_id = self.start_conversation(args.prompt, args.context)

        if not conv_id:
            self.error("会話の開始に失敗しました")
            return

        self.success(f"会話ID: {conv_id}")

        # 初期タスク送信
        if self.send_initial_task(conv_id, args.prompt, args.context):
            self.success("タスク送信成功")
        else:
            self.error("タスク送信失敗")
            return

        # 使用方法の説明
        self.section("次のステップ")

        if not args.no_slack:
            self.info("Slackに通知が送信されます")
            self.info("質問が来たら以下のコマンドで応答してください：")
        else:
            self.info("応答は以下のコマンドで送信してください：")

        self.print(f"\n  ai-reply {conv_id} <回答内容>\n", color="cyan", bold=True)

        self.info("会話の状態確認：")
        self.print(f"  ai-tasks --conversation {conv_id}\n", color="cyan")

        self.success("対話型タスクを開始しました！")


def main():
    # Core functionality implementation
    cmd = DialogCommand()
    return cmd.run()


if __name__ == "__main__":
    import sys

    sys.exit(main())
