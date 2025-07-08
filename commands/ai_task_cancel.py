#!/usr/bin/env python3
"""
タスクキャンセル
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult

class AITaskCancelCommand(BaseCommand):
    """タスクキャンセル"""
    
    def __init__(self):
        super().__init__(
            name="ai-task-cancel",
            description="タスクキャンセル",
            version="1.0.0"
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        # TODO: 実装
        return CommandResult(
            success=True,
            message="タスクキャンセル機能は開発中です"
        )

def main():
    command = AITaskCancelCommand()
    sys.exit(command.run())

if __name__ == "__main__":
    main()
