#!/usr/bin/env python3
"""
ヘルプ表示
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult
import subprocess

class AIHelpCommand(BaseCommand):
    """ヘルプコマンド"""
    
    def __init__(self):
        super().__init__(
            name="ai-help",
            description="ヘルプ表示",
            version="1.0.0"
        )
    
    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument(
            'command',
            nargs='?',
            help='ヘルプを表示するコマンド'
        )
        self.parser.add_argument(
            '--list', '-l',
            action='store_true',
            help='全コマンド一覧'
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        if args.list:
            return self._list_commands()
        
        if args.command:
            return self._show_command_help(args.command)
        
        # 全般的なヘルプ
        help_text = """
🚀 Elders Guild - 自律進化AI基盤

【基本コマンド】
  ai-start         システム起動
  ai-stop          システム停止
  ai-status        状態確認
  ai-send          タスク送信

【タスク実行】
  ai-code          コード生成（ai-send ... code のショートカット）
  ai-dialog        対話型タスク開始
  ai-reply         対話応答

【管理コマンド】
  ai-workers       ワーカー管理
  ai-tasks         タスク一覧
  ai-logs          ログ確認
  ai-config        設定管理

【高度な機能】
  ai-rag-search    RAG検索
  ai-evolve        自己進化実行
  ai-stats         統計情報

【使用例】
  ai-send "Pythonでファイル管理システムを作成" code
  ai-dialog "複雑なWebアプリケーションを設計したい"
  ai-logs task -f --grep ERROR

詳細なヘルプ: ai-help <コマンド名>
全コマンド一覧: ai-help --list
"""
        return CommandResult(success=True, message=help_text)
    
    def _list_commands(self) -> CommandResult:
        """全コマンド一覧"""
        commands = []
        bin_dir = Path("/home/aicompany/ai_co/bin")
        
        for cmd_file in sorted(bin_dir.glob("ai-*")):
            if cmd_file.is_file() and cmd_file.name != "ai_launcher.py":
                commands.append(cmd_file.name)
        
        message = "利用可能なコマンド一覧:\n\n"
        for cmd in commands:
            message += f"  {cmd}\n"
        
        return CommandResult(success=True, message=message)
    
    def _show_command_help(self, command: str) -> CommandResult:
        """コマンドのヘルプ表示"""
        if not command.startswith("ai-"):
            command = f"ai-{command}"
        
        try:
            result = subprocess.run([command, "--help"], capture_output=True, text=True)
            return CommandResult(
                success=True,
                message=result.stdout
            )
        except FileNotFoundError:
            return CommandResult(
                success=False,
                message=f"コマンドが見つかりません: {command}"
            )

def main():
    command = AIHelpCommand()
    sys.exit(command.run())

if __name__ == "__main__":
    main()
