#!/usr/bin/env python3
"""
会話詳細
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AIConvInfoCommand(BaseCommand):
    """会話詳細"""

    def __init__(self):
        super().__init__(name="ai-conv-info", description="会話詳細", version="1.0.0")

    def execute(self, args) -> CommandResult:
        """実行"""
        # TODO: 実装
        return CommandResult(success=True, message="会話詳細機能は開発中です")


def main():
    command = AIConvInfoCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
