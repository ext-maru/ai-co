#!/usr/bin/env python3
"""
Elders Guild インタラクティブメニュー
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AICommand(BaseCommand):
    """Elders Guild メインコマンド"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            name="ai", description="Elders Guild インタラクティブメニュー", version="1.0.0"
        )

    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument("subcommand", nargs="?", help="サブコマンド")

    def execute(self, args) -> CommandResult:
        """実行"""
        if args.subcommand:
            # サブコマンドとして実行
            return self._run_subcommand(args.subcommand, sys.argv[2:])

        # メニュー表示
        menu_text = """
🚀 Elders Guild インタラクティブメニュー

【基本操作】
  ai-status    - システム状態確認
  ai-send      - タスク送信
  ai-workers   - ワーカー管理

【高度な機能】
  ai-queue     - キュー状態
  ai-stats     - 統計情報
  ai-config    - 設定管理

【ヘルプ】
  ai-help      - 詳細ヘルプ

使用例: ai status
"""
        return CommandResult(success=True, message=menu_text)

    def _run_subcommand(self, command: str, args: list = None) -> CommandResult:
        """サブコマンド実行"""
        if args is None:
            args = []

        import subprocess

        try:
            result = subprocess.run(
                [f"ai-{command}"] + args, capture_output=True, text=True
            )
            return CommandResult(
                success=result.returncode == 0,
                message=result.stdout if result.returncode == 0 else result.stderr,
            )
        except FileNotFoundError:
            # Handle specific exception case
            return CommandResult(success=False, message=f"コマンドが見つかりません: ai-{command}")


def main():
    # Core functionality implementation
    command = AICommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
