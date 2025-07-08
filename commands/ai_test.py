#!/usr/bin/env python3
"""
AI Company テスト実行コマンド
scripts/ai-testを呼び出す
"""
import sys
import subprocess
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from commands.base_command import BaseCommand, CommandResult

class AITestCommand(BaseCommand):
    """テスト実行コマンド"""
    
    def __init__(self):
        super().__init__(
            name="ai-test",
            description="AI Companyのテストを実行します",
            version="1.0.0"
        )
    
    def setup_parser(self, parser):
        """パーサー設定"""
        parser.add_argument(
            'test_target',
            nargs='?',
            default='quick',
            help='テストターゲット (quick/full/unit/integration/coverage/watch/report/clean) または特定のファイル/ディレクトリ'
        )
        parser.add_argument(
            '-p', '--pattern',
            help='特定パターンのテストのみ実行'
        )
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='詳細出力'
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        # scripts/ai-testスクリプトのパス
        test_script = PROJECT_ROOT / 'scripts' / 'ai-test'
        
        if not test_script.exists():
            return CommandResult(
                success=False,
                message=f"テストスクリプトが見つかりません: {test_script}"
            )
        
        # コマンドを構築
        cmd = [str(test_script)]
        
        # テストターゲットを追加
        if hasattr(args, 'test_target') and args.test_target:
            # patternオプションの場合は特別処理
            if args.pattern:
                cmd.extend(['-p', args.pattern])
            else:
                cmd.append(args.test_target)
        
        # verboseオプション
        if hasattr(args, 'verbose') and args.verbose:
            cmd.append('-v')
        
        # 残りの引数を追加（重複を避ける）
        remaining_args = []
        skip_next = False
        for i, arg in enumerate(sys.argv[2:]):  # ai-test以降の引数
            if skip_next:
                skip_next = False
                continue
            if arg in ['-p', '--pattern', '-v', '--verbose']:
                if arg in ['-p', '--pattern'] and i+1 < len(sys.argv[2:]):
                    skip_next = True
                continue
            if arg not in cmd and arg != args.test_target:
                remaining_args.append(arg)
        
        cmd.extend(remaining_args)
        
        try:
            # スクリプトを実行
            result = subprocess.run(cmd, check=False)
            
            return CommandResult(
                success=(result.returncode == 0),
                message=""  # 出力はスクリプトが直接行う
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"テスト実行中にエラーが発生しました: {str(e)}"
            )

def main():
    command = AITestCommand()
    return command.run()

if __name__ == "__main__":
    sys.exit(main())
