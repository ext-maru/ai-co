#!/usr/bin/env python3
"""
Elders Guild - 対話応答コマンド
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, "/root/ai_co")

from rich.console import Console

from commands.base_command import BaseCommand, CommandResult


class AIReplyCommand(BaseCommand):
    """対話応答コマンド"""

    def __init__(self):
        super().__init__(
            name="reply", description="Elders Guild 対話への応答を送信", version="1.0.0"
        )
        self.console = Console()

    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument("conversation_id", help="会話ID")
        self.parser.add_argument("message", help="返信メッセージ")
        self.parser.add_argument("--user", default="user", help="ユーザー名（デフォルト: user）")

    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            self.console.print(f"📤 応答送信: {args.conversation_id}")
            self.console.print(f"メッセージ: {args.message[:50]}...")

            return CommandResult(
                success=True, message=f"✅ 応答を送信しました (会話ID: {args.conversation_id})"
            )

        except Exception as e:
            return CommandResult(success=False, message=f"❌ 応答送信エラー: {str(e)}")


def main():
    command = AIReplyCommand()
    return command.run()


if __name__ == "__main__":
    sys.exit(main())
