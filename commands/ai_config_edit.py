#!/usr/bin/env python3
"""
設定編集
"""
import sys
import json
import argparse
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult

class AIConfigEditCommand(BaseCommand):
    """設定編集"""
    
    def __init__(self):
        super().__init__(
            name="ai-config-edit",
            description="設定編集",
            version="1.0.0"
        )
    
    def add_arguments(self, parser: argparse.ArgumentParser):
        """引数定義"""
        parser.add_argument(
            '--config-file', '-f',
            type=str,
            default='configs/config.json',
            help='設定ファイルのパス'
        )
        parser.add_argument(
            '--key', '-k',
            type=str,
            required=True,
            help='設定キー'
        )
        parser.add_argument(
            '--value', '-v',
            type=str,
            help='設定値（指定しない場合は現在の値を表示）'
        )
        parser.add_argument(
            '--delete', '-d',
            action='store_true',
            help='設定を削除'
        )
        parser.add_argument(
            '--list', '-l',
            action='store_true',
            help='全設定を表示'
        )
    
    def execute(self, args) -> CommandResult:
        """実行"""
        try:
            config_path = Path(args.config_file)
            
            # 設定ファイルの読み込み
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
                config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 全設定表示
            if args.list:
                if config:
                    return CommandResult(
                        success=True,
                        message="現在の設定:\n" + json.dumps(config, indent=2, ensure_ascii=False)
                    )
                else:
                    return CommandResult(
                        success=True,
                        message="設定ファイルが空です"
                    )
            
            # 設定の削除
            if args.delete:
                if args.key in config:
                    del config[args.key]
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    return CommandResult(
                        success=True,
                        message=f"設定 '{args.key}' を削除しました"
                    )
                else:
                    return CommandResult(
                        success=False,
                        message=f"設定 '{args.key}' が見つかりません"
                    )
            
            # 値の取得
            if args.value is None:
                if args.key in config:
                    return CommandResult(
                        success=True,
                        message=f"{args.key} = {config[args.key]}"
                    )
                else:
                    return CommandResult(
                        success=False,
                        message=f"設定 '{args.key}' が見つかりません"
                    )
            
            # 値の設定
            config[args.key] = args.value
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return CommandResult(
                success=True,
                message=f"設定 '{args.key}' を '{args.value}' に設定しました"
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"設定編集エラー: {str(e)}"
            )

def main():
    command = AIConfigEditCommand()
    sys.exit(command.run())

if __name__ == "__main__":
    main()
