#!/usr/bin/env python3
"""
騎士団巡回警備システム状況確認スクリプト
"""

import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_watchdog_processes():
    """ウォッチドッグプロセスの確認"""
    print("🔍 ウォッチドッグプロセス確認")
    print("-" * 40)

    # プロセス確認
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        watchdog_processes = []

        for line in result.stdout.split("\n"):
            if any(keyword in line.lower() for keyword in ["watchdog", "patrol", "guard", "monitor"]):
                if "grep" not in line and line.strip():
                    watchdog_processes.append(line.strip())

        if watchdog_processes:
            print(f"✅ 発見されたプロセス: {len(watchdog_processes)}個")
            for proc in watchdog_processes:
                print(f"  - {proc}")
        else:
            print("⚠️ アクティブなウォッチドッグプロセスなし")

    except Exception as e:
        print(f"❌ プロセス確認エラー: {e}")


def check_knight_files():
    """騎士団関連ファイルの確認"""
    print("\n🛡️ 騎士団ファイル確認")
    print("-" * 40)

    knight_files = []
    watchdog_files = []

    # ファイル検索
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for file in files:
            if any(keyword in file.lower() for keyword in ["knight", "watchdog", "patrol", "guard"]):
                file_path = Path(root) / file
                if "knight" in file.lower():
                    knight_files.append(file_path)
                elif "watchdog" in file.lower():
                    watchdog_files.append(file_path)

    print(f"騎士団ファイル: {len(knight_files)}個")
    for file in knight_files[:10]:  # 最初の10個を表示
        print(f"  - {file.relative_to(PROJECT_ROOT)}")

    print(f"\nウォッチドッグファイル: {len(watchdog_files)}個")
    for file in watchdog_files:
        print(f"  - {file.relative_to(PROJECT_ROOT)}")


def check_logs():
    """ログファイルの確認"""
    print("\n📋 ログファイル確認")
    print("-" * 40)

    log_files = [
        "logs/elder_watchdog.log",
        "logs/elder_monitoring.log",
        "logs/knights_patrol.log",
        "logs/system_health.log",
    ]

    for log_file in log_files:
        log_path = PROJECT_ROOT / log_file
        if log_path.exists():
            try:
                # 最新の10行を取得
                result = subprocess.run(["tail", "-10", str(log_path)], capture_output=True, text=True)
                last_lines = result.stdout.strip().split("\n")

                if last_lines and last_lines[0]:
                    print(f"✅ {log_file} (最新: {last_lines[-1][:50]}...)")
                else:
                    print(f"⚠️ {log_file} (空またはエラー)")
            except Exception as e:
                print(f"❌ {log_file} 読み込みエラー: {e}")
        else:
            print(f"❌ {log_file} 見つかりません")


def check_system_health():
    """システムヘルスの確認"""
    print("\n🏥 システムヘルス確認")
    print("-" * 40)

    # メモリ使用量
    try:
        result = subprocess.run(["free", "-h"], capture_output=True, text=True)
        memory_line = result.stdout.split("\n")[1]
        print(f"メモリ: {memory_line}")
    except Exception as e:
        print(f"メモリ確認エラー: {e}")

    # CPU使用率
    try:
        result = subprocess.run(["top", "-bn1"], capture_output=True, text=True)
        cpu_line = [line for line in result.stdout.split("\n") if "Cpu(s)" in line][0]
        print(f"CPU: {cpu_line}")
    except Exception as e:
        print(f"CPU確認エラー: {e}")

    # ディスク使用量
    try:
        result = subprocess.run(["df", "-h", "."], capture_output=True, text=True)
        disk_line = result.stdout.split("\n")[1]
        print(f"ディスク: {disk_line}")
    except Exception as e:
        print(f"ディスク確認エラー: {e}")


def check_knight_services():
    """騎士団サービスの確認"""
    print("\n⚔️ 騎士団サービス確認")
    print("-" * 40)

    # RabbitMQ状態
    try:
        result = subprocess.run(["systemctl", "is-active", "rabbitmq-server"], capture_output=True, text=True)
        print(f"RabbitMQ: {result.stdout.strip()}")
    except Exception as e:
        print(f"RabbitMQ確認エラー: {e}")

    # Python プロセス（ワーカー関連）
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        worker_count = 0
        for line in result.stdout.split("\n"):
            if "worker" in line.lower() and "python" in line and "grep" not in line:
                worker_count += 1

        print(f"ワーカープロセス: {worker_count}個")
    except Exception as e:
        print(f"ワーカー確認エラー: {e}")


def start_patrol_if_needed():
    """必要に応じて巡回を開始"""
    print("\n🚀 巡回開始判定")
    print("-" * 40)

    # elder_watchdog.sh の実行状況確認
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        watchdog_running = False

        for line in result.stdout.split("\n"):
            if "elder_watchdog.sh" in line and "grep" not in line:
                watchdog_running = True
                break

        if watchdog_running:
            print("✅ エルダーウォッチドッグは既に稼働中です")
        else:
            print("⚠️ エルダーウォッチドッグが停止しています")

            # 手動開始の提案
            watchdog_path = PROJECT_ROOT / "elder_watchdog.sh"
            if watchdog_path.exists():
                print(f"💡 手動開始: nohup {watchdog_path} > /dev/null 2>&1 &")
            else:
                print("❌ ウォッチドッグスクリプトが見つかりません")

    except Exception as e:
        print(f"❌ 巡回開始判定エラー: {e}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("🛡️ 騎士団巡回警備システム状況確認")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"プロジェクト: {PROJECT_ROOT}")

    # 各種確認を実行
    check_watchdog_processes()
    check_knight_files()
    check_logs()
    check_system_health()
    check_knight_services()
    start_patrol_if_needed()

    print("\n" + "=" * 60)
    print("✅ 騎士団巡回警備システム状況確認完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
