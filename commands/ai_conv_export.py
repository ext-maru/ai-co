#!/usr/bin/env python3
"""
会話エクスポート
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AIConvExportCommand(BaseCommand):
    """会話エクスポート"""

    def __init__(self):
        super().__init__(name="ai-conv-export", description="会話エクスポート", version="1.0.0")

    def execute(self, args) -> CommandResult:
        """実行"""
        # TODO: 実装
        return CommandResult(success=True, message="会話エクスポート機能は開発中です")


def main():
    command = AIConvExportCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
