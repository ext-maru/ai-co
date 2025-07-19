#!/usr/bin/env python3
"""
Task WorkerでAPIキーなしでもシミュレーション応答するよう設定
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def update_env_for_simulation():
    """シミュレーションモード用の環境変数設定"""
    env_file = Path(__file__).parent.parent / ".env"

    # 現在の内容を読み込み
    if env_file.exists():
        with open(env_file, "r") as f:
            content = f.read()
    else:
        content = ""

    # シミュレーションモード設定を追加
    simulation_settings = """
# Task Worker Simulation Mode
TASK_WORKER_SIMULATION_MODE=true
TASK_WORKER_SIMULATION_RESPONSE=enabled
"""

    # 既存設定をチェック
    if "TASK_WORKER_SIMULATION_MODE" not in content:
        content += simulation_settings

        with open(env_file, "w") as f:
            f.write(content)

        print("✅ シミュレーションモード設定を追加しました")
    else:
        print("✅ シミュレーションモード設定は既に存在します")


def restart_task_worker():
    """Task Workerを再起動"""
    import subprocess
    import time

    print("🔄 Task Worker再起動中...")

    # 既存プロセスを停止
    try:
        subprocess.run(["pkill", "-f", "simple_task_worker"], check=False)
        time.sleep(2)
        print("⏹️  既存Task Worker停止")
    except:
        pass

    # 新しいプロセスを起動
    try:
        subprocess.Popen(
            ["python3", "workers/simple_task_worker.py", "--worker-id", "simple-task"],
            cwd=Path(__file__).parent.parent,
        )
        time.sleep(3)
        print("🚀 新しいTask Worker起動")
    except Exception as e:
        print(f"❌ 起動エラー: {e}")


if __name__ == "__main__":
    print("🔧 Slack対話テスト用設定")
    print("=" * 50)

    update_env_for_simulation()
    restart_task_worker()

    print("\n📋 テスト手順:")
    print("1. Slackで @pm-ai hello と入力")
    print("2. シミュレーション応答が返ることを確認")
    print("3. APIキー設定後、実際のClaude応答に切り替え")

    print("\n💡 シミュレーションモードでは以下の応答:")
    print("- hello → Hello, Elders Guild! の応答")
    print("- 複雑なタスク → 対応する実装コード例")
