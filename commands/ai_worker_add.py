#!/usr/bin/env python3
"""
ワーカー追加
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from commands.base_command import BaseCommand, CommandResult


class AIWorkerAddCommand(BaseCommand):
    """ワーカー追加"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__(name="ai-worker-add", description="ワーカー追加", version="1.0.0")

    def execute(self, args) -> CommandResult:
        """実行"""
        if len(args) < 1:
            return CommandResult(
                success=False, 
                message="Usage: ai-worker-add <worker_name> [worker_type] [config_file]"
            )
        
        worker_name = args[0]
        worker_type = args[1] if len(args) > 1 else "generic"
        config_file = args[2] if len(args) > 2 else None
        
        try:
            # ワーカー設定ディレクトリを確認・作成
            workers_dir = Path(__file__).parent.parent / "workers"
            workers_dir.mkdir(exist_ok=True)
            
            worker_config_path = workers_dir / f"{worker_name}_config.json"
            
            # 基本ワーカー設定を作成
            import json
            from datetime import datetime
            
            config = {
                "worker_name": worker_name,
                "worker_type": worker_type,
                "status": "inactive",
                "created_at": datetime.now().isoformat(),
                "enabled": True,
                "config": {
                    "max_concurrent_tasks": 1,
                    "timeout_seconds": 300
                }
            }
            
            # 設定ファイルが指定されている場合は読み込み
            if config_file and Path(config_file).exists():
                # Complex condition - consider breaking down
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config["config"].update(user_config)
            
            # ワーカー設定ファイルを保存
            with open(worker_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return CommandResult(
                success=True, 
                message=f"✅ ワーカー '{worker_name}' ({worker_type}) を追加しました\n"
                       f"   設定ファイル: {worker_config_path}"
            )
            
        except Exception as e:
            # Handle specific exception case
            return CommandResult(
                success=False, 
                message=f"❌ ワーカー追加エラー: {e}"
            )


def main():
    # Core functionality implementation
    command = AIWorkerAddCommand()
    sys.exit(command.run())


if __name__ == "__main__":
    main()
