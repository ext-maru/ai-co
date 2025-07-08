#!/usr/bin/env python3
"""
AI Company WebUI - Simple web interface
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult

class AIWebUICommand(BaseCommand):
    """WebUI コマンド"""
    
    def __init__(self):
        super().__init__(
            name="ai-webui",
            description="Web UI起動",
            version="1.0.0"
        )
    
    def setup_arguments(self):
        """引数設定"""
        self.parser.add_argument(
            '--port', '-p',
            type=int,
            default=5555,
            help='ポート番号（デフォルト: 5555）'
        )
        self.parser.add_argument(
            '--host',
            default='localhost',
            help='ホスト名（デフォルト: localhost）'
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            print(f"🌐 AI Company WebUI Starting...")
            print(f"URL: http://{args.host}:{args.port}")
            print(f"")
            print(f"📋 利用可能な機能:")
            print(f"  - システム監視ダッシュボード")
            print(f"  - ワーカー状態確認")
            print(f"  - キュー状態確認")
            print(f"  - タスク履歴確認")
            print(f"")
            print(f"⚠️  終了するには Ctrl+C を押してください")
            print(f"")
            
            # dashboard_server.pyを実行
            from web.dashboard_server import DashboardServer
            
            server = DashboardServer(host=args.host, port=args.port)
            server.run()
            
            return CommandResult(success=True)
            
        except KeyboardInterrupt:
            print(f"\n🛑 WebUI サーバーを停止しました")
            return CommandResult(success=True)
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"WebUI起動エラー: {str(e)}"
            )

def main():
    command = AIWebUICommand()
    sys.exit(command.run())

if __name__ == "__main__":
    main()