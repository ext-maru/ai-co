#!/usr/bin/env python3
"""
AI Command Executor 使用例
AIがコマンドを作成して自動実行させるサンプル
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import time

from libs.ai_command_helper import AICommandHelper


def main():
    helper = AICommandHelper()

    print("🤖 AI Command Executor Example")
    print("=" * 50)

    # 1. システム情報取得コマンドを作成
    print("\n1. Creating system info command...")
    bash_cmd = """
echo "=== System Information ==="
echo "Hostname: $(hostname)"
echo "OS: $(uname -s)"
echo "Kernel: $(uname -r)"
echo "CPU cores: $(nproc)"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Disk usage:"
df -h | grep -E "^/dev"
echo "Python processes:"
ps aux | grep python | grep -v grep | wc -l
"""
    result = helper.create_bash_command(bash_cmd, "system_info")
    print(result)

    # 2. Pythonバージョン確認コマンド
    print("\n2. Creating Python check command...")
    python_cmd = """
import sys
import platform
import importlib.util

print("=== Python Environment ===")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Machine: {platform.machine()}")

# Check for important packages
packages = ['pika', 'requests', 'psutil']
for pkg in packages:
    spec = importlib.util.find_spec(pkg)
    if spec is not None:
        print(f"✓ {pkg} is installed")
    else:
        print(f"✗ {pkg} is NOT installed")
"""
    result = helper.create_python_command(python_cmd, "python_check")
    print(result)

    # 3. 保留中のコマンドを確認
    print("\n3. Pending commands:")
    pending = helper.list_pending_commands()
    for cmd in pending:
        print(f"  - {cmd}")

    print("\n⏳ Waiting for execution (5 seconds)...")
    print("Note: Make sure the Command Executor Worker is running!")
    print("Run: ./scripts/start-command-executor.sh")

    # 実行を待つ
    time.sleep(10)

    # 4. 結果を確認
    print("\n4. Checking results...")

    # システム情報の結果
    result = helper.check_results("system_info")
    if "status" in result and result["status"] != "not_found":
        print(f"\nSystem Info Result: {result.get('status', 'Unknown')}")
        if "log_file" in result:
            print(f"Log file: {result['log_file']}")

    # Pythonチェックの結果
    result = helper.check_results("python_check")
    if "status" in result and result["status"] != "not_found":
        print(f"\nPython Check Result: {result.get('status', 'Unknown')}")
        if "log_file" in result:
            print(f"Log file: {result['log_file']}")

    # 5. 最新のログを表示
    print("\n5. Latest log content:")
    print("-" * 50)
    latest_log = helper.get_latest_log()
    print(latest_log[:500] + "..." if len(latest_log) > 500 else latest_log)

    print("\n✅ Example completed!")
    print("\nTo see all logs, check: /home/aicompany/ai_co/ai_commands/logs/")


if __name__ == "__main__":
    main()
