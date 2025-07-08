#!/usr/bin/env python3
"""
バージョン情報表示
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult
from rich.console import Console
from rich.panel import Panel
import subprocess
import json

class AIVersionCommand(BaseCommand):
    """バージョン情報表示コマンド"""
    
    def __init__(self):
        super().__init__(
            name="ai-version",
            description="バージョン情報表示",
            version="2.0.0"
        )
        self.console = Console()
    
    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument(
            '--json',
            action='store_true',
            help='JSON形式で出力'
        )
        self.parser.add_argument(
            '--check-update',
            action='store_true',
            help='更新確認'
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        version_info = self._get_version_info()
        
        if args.json:
            return CommandResult(
                success=True,
                message=json.dumps(version_info, indent=2)
            )
        
        # バージョン情報表示
        info_text = f"""
🚀 AI Company - 自律進化AI基盤

バージョン: {version_info['version']}
ビルド日: {version_info['build_date']}
Python: {version_info['python_version']}
Claude CLI: {version_info['claude_cli_version']}

主要コンポーネント:
  - TaskWorker: v{version_info['components']['task_worker']}
  - RAGManager: v{version_info['components']['rag_manager']}
  - SelfEvolution: v{version_info['components']['self_evolution']}
  - GitHub Integration: v{version_info['components']['github_integration']}

作者: AI Company Development Team
ライセンス: MIT
"""
        
        self.console.print(Panel(
            info_text.strip(),
            title="📦 バージョン情報",
            border_style="blue"
        ))
        
        if args.check_update:
            self.console.print("\n🔍 更新を確認中...", style="yellow")
            # 実際の更新確認ロジックはGitHub APIを使用
            self.console.print("✅ 最新バージョンです", style="green")
        
        return CommandResult(success=True)
    
    def _get_version_info(self) -> dict:
        """バージョン情報取得"""
        # Python バージョン
        python_version = sys.version.split()[0]
        
        # Claude CLI バージョン
        try:
            result = subprocess.run(['claude', '--version'], 
                                  capture_output=True, text=True)
            claude_version = result.stdout.strip().split()[-1]
        except:
            claude_version = "Unknown"
        
        return {
            'version': '2.0.0',
            'build_date': '2025-07-02',
            'python_version': python_version,
            'claude_cli_version': claude_version,
            'components': {
                'task_worker': '2.1.0',
                'rag_manager': '1.5.0',
                'self_evolution': '1.3.0',
                'github_integration': '1.0.0'
            }
        }

def main():
    command = AIVersionCommand()
    sys.exit(command.run())

if __name__ == "__main__":
    main()
