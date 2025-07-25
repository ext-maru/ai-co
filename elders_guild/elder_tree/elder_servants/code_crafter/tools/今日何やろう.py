#!/usr/bin/env python3
"""
今日何やろう - 日次機能提案システム
ユーザーが覚えやすいコマンド名でアクセス
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    """日次提案システムを実行"""
    script_path = PROJECT_ROOT / "scripts" / "daily_feature_proposal.py"

    # 引数をそのまま渡す
    cmd = [sys.executable, str(script_path)] + sys.argv[1:]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 中断されました")
        sys.exit(0)


if __name__ == "__main__":
    main()
