#!/usr/bin/env python3
"""
設定再読込
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AIConfigReloadCommand(BaseCommand):
    """設定再読込"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="ai-config-reload", description="設定再読込", version="1.0.0")

    def execute(self, args) -> CommandResult:
        """実行"""
        config_file = args[0] if len(args) > 0 else None
        
        try:
            reloaded_files = []
            
            # デフォルト設定ファイルの場所
            config_paths = [
                Path(__file__).parent.parent / "configs" / "ai_config.json",
                Path(__file__).parent.parent / "configs" / "worker_config.json",
                Path.home() / ".ai_co_config.json"
            ]
            
            # 特定の設定ファイルが指定された場合
            if config_file:
                specific_path = Path(config_file)
                if not specific_path.exists():
                    return CommandResult(
                        success=False,
                        message=f"❌ 設定ファイルが見つかりません: {config_file}"
                    )
                config_paths = [specific_path]
            
            # 設定ファイルを順次処理
            import json
            for config_path in config_paths:
                if config_path.exists():
                    try:
                        # 設定ファイルの妥当性をチェック
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        
                        # 基本的な妥当性チェック
                        if not isinstance(config_data, dict):
                            raise ValueError("設定ファイルは辞書形式である必要があります")
                        
                        reloaded_files.append(str(config_path))
                        
                    except json.JSONDecodeError as e:
                        # Handle specific exception case
                        return CommandResult(
                            success=False,
                            message=f"❌ JSONエラー in {config_path}: {e}"
                        )
                    except Exception as e:
                        # Handle specific exception case
                        return CommandResult(
                            success=False,
                            message=f"❌ 設定ファイルエラー in {config_path}: {e}"
                        )
            
            if not reloaded_files:
                return CommandResult(
                    success=False,
                    message="❌ 有効な設定ファイルが見つかりませんでした"
                )
            
            # 設定の一時保存（リロード通知用）
            reload_marker = Path(__file__).parent.parent / "tmp" / "config_reloaded.marker"
            reload_marker.parent.mkdir(exist_ok=True)
            
            from datetime import datetime
            with open(reload_marker, 'w') as f:
                f.write(f"Config reloaded at: {datetime.now().isoformat()}\n")
                f.write(f"Files: {', '.join(reloaded_files)}\n")
            
            return CommandResult(
                success=True, 
                message=f"✅ 設定を再読み込みしました:\n" + 
                       "\n".join(f"   - {f}" for f in reloaded_files)
            )
            
        except Exception as e:
            # Handle specific exception case
            return CommandResult(
                success=False, 
                message=f"❌ 設定再読み込みエラー: {e}"
            )


def main():
    # Core functionality implementation
    command = AIConfigReloadCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
