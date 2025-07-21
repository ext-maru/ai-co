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
        if len(args) < 1:
            return CommandResult(
                success=False, 
                message="Usage: ai-worker-rm <worker_name> [--force]"
            )
        
        worker_name = args[0]
        force = "--force" in args
        
        try:
            # ワーカー設定ファイルを確認
            workers_dir = Path(__file__).parent.parent / "workers"
            worker_config_path = workers_dir / f"{worker_name}_config.json"
            
            if not worker_config_path.exists():
                return CommandResult(
                    success=False, 
                    message=f"❌ ワーカー '{worker_name}' が見つかりません"
                )
            
            # ワーカー情報を読み込み
            import json
            with open(worker_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 稼働中のワーカーの確認
            if config.get("status") == "active" and not force:
                return CommandResult(
                    success=False,
                    message=f"❌ ワーカー '{worker_name}' は稼働中です。"
                           f"強制削除するには --force を使用してください"
                )
            
            # ワーカー設定ファイルを削除
            worker_config_path.unlink()
            
            # ワーカーログファイルがあれば削除
            log_dir = Path(__file__).parent.parent / "logs"
            worker_log_path = log_dir / f"{worker_name}.log"
            if worker_log_path.exists():
                worker_log_path.unlink()
            
            return CommandResult(
                success=True, 
                message=f"✅ ワーカー '{worker_name}' を削除しました"
            )
            
        except Exception as e:
            return CommandResult(
                success=False, 
                message=f"❌ ワーカー削除エラー: {e}"
            )


def main():
    command = AIWorkerRmCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
