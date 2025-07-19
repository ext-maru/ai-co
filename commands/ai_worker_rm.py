#!/usr/bin/env python3
"""
ワーカー削除
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AIWorkerRmCommand(BaseCommand):
    """ワーカー削除"""

    def __init__(self):
        super().__init__(name="ai-worker-rm", description="ワーカー削除", version="1.0.0")

    def execute(self, args) -> CommandResult:
        """実行"""
        # TODO: 実装
        return CommandResult(success=True, message="ワーカー削除機能は開発中です")


def main():
    command = AIWorkerRmCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
