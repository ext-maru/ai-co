#!/usr/bin/env python3
"""
WSL クイックスタート用スクリプト
PC起動時やWSL再開時に即座に実行する軽量版
"""

import os
import subprocess
import sys
from pathlib import Path


def quick_start():
    """クイックスタート実行"""
    print("🚀 Elders Guild WSL クイックスタート")
    print("=" * 50)

    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("1️⃣ RabbitMQ 状態確認...")
    try:
        result = subprocess.run(["systemctl", "is-active", "rabbitmq-server"], capture_output=True, text=True)
        if result.stdout.strip() == "active":
            print("   ✅ RabbitMQ 正常稼働中")
        else:
            print("   ⚠️  RabbitMQ 停止中 - 手動起動が必要")
            print("   💡 実行: sudo systemctl start rabbitmq-server")
    except Exception as e:
        print(f"   ❌ RabbitMQ 確認エラー: {e}")

    print("\n2️⃣ ウォッチドッグ起動...")
    try:
        # 既存のウォッチドッグを停止
        subprocess.run(["pkill", "-f", "elder_watchdog.sh"], capture_output=True)

        # 新しいウォッチドッグを起動
        subprocess.Popen(
            ["nohup", "bash", "elder_watchdog.sh"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )
        print("   ✅ エルダーウォッチドッグ起動完了")

    except Exception as e:
        print(f"   ❌ ウォッチドッグ起動エラー: {e}")

    print("\n3️⃣ エルダー監視起動...")
    try:
        # 既存の監視を停止
        subprocess.run(["pkill", "-f", "start_elder_monitoring.py"], capture_output=True)

        # 新しい監視を起動
        subprocess.Popen(
            ["nohup", sys.executable, "start_elder_monitoring.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )
        print("   ✅ エルダー監視起動完了")

    except Exception as e:
        print(f"   ❌ エルダー監視起動エラー: {e}")

    print("\n4️⃣ ワーカー状態確認...")
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        worker_count = 0
        for line in result.stdout.split("\n"):
            if "worker" in line.lower() and "python" in line and "grep" not in line:
                worker_count += 1

        print(f"   📊 ワーカープロセス: {worker_count}個")

        if worker_count < 3:
            print("   🔧 ワーカー不足 - 自動修復実行中...")
            if Path("check_and_fix_workers.py").exists():
                subprocess.run([sys.executable, "check_and_fix_workers.py"])

    except Exception as e:
        print(f"   ❌ ワーカー確認エラー: {e}")

    print("\n5️⃣ システム状態保存...")
    try:
        subprocess.run([sys.executable, "scripts/wsl_sleep_recovery_system.py"], capture_output=True)
        print("   ✅ システム状態保存完了")
    except Exception as e:
        print(f"   ❌ 状態保存エラー: {e}")

    print("\n" + "=" * 50)
    print("✅ Elders Guild WSL クイックスタート完了!")
    print("💡 詳細ログ: logs/wsl_recovery.log")
    print("=" * 50)


if __name__ == "__main__":
    quick_start()
