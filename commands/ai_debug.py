#!/usr/bin/env python3
"""
デバッグモード
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AIDebugCommand(BaseCommand):
    """デバッグモード"""

    def __init__(self):
        super().__init__(name="ai-debug", description="デバッグモード", version="1.0.0")

    def execute(self, args) -> CommandResult:
        """実行"""
        # TODO: 実装
        return CommandResult(success=True, message="デバッグモード機能は開発中です")


def main():
    command = AIDebugCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
