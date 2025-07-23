#!/usr/bin/env python3
"""
A2A（AI-to-AI通信）状況確認スクリプト（短縮版）
"""

import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_a2a_implementation():
    """A2A実装状況の確認"""
    print("📋 A2A実装状況:")

    a2a_files = [
        "libs/a2a_communication.py",
        "commands/ai_a2a.py",
        "libs/elder_servant_a2a_optimization.py",
        "examples/four_sages_a2a_demo.py",
    ]

    for file_path in a2a_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path} (見つかりません)")


def check_system_status():
    """システム状態の確認"""
    print("\n🔍 システム状態:")

    # RabbitMQ状態
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "rabbitmq-server"],
            capture_output=True,
            text=True,
        )
        print(f"  RabbitMQ: {result.stdout.strip()}")
    except Exception as e:
        print(f"  RabbitMQ: エラー - {e}")

    # プロセス確認
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        agent_processes = 0
        for line in result.stdout.split("\n"):
            if any(
                keyword in line.lower()
                for keyword in ["elder", "sage", "council", "a2a"]
            ):
                agent_processes += 1
        print(f"  エージェント関連プロセス: {agent_processes}個")
    except Exception as e:
        print(f"  プロセス確認エラー: {e}")


def check_elder_council_status():
    """エルダー評議会の状態確認"""
    print("\n🏛️ エルダー評議会状況:")

    # 評議会要請文書をチェック
    council_requests = list(PROJECT_ROOT.glob("knowledge_base/*council*request*.md"))
    print(f"  評議会要請文書: {len(council_requests)}件")

    # 最新の要請を確認
    if council_requests:
        latest_request = max(council_requests, key=lambda x: x.stat().st_mtime)
        mod_time = datetime.fromtimestamp(latest_request.stat().st_mtime)
        print(f"  最新要請: {latest_request.name}")
        print(f"  作成日時: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")


def check_communication_logs():
    """通信ログの確認"""
    print("\n📡 通信ログ状況:")

    log_files = [
        "logs/elder_monitoring.log",
        "logs/elder_watchdog.log",
        "logs/a2a_communication.log",
        "logs/a2a_monitoring.log",
    ]

    for log_file in log_files:
        log_path = PROJECT_ROOT / log_file
        if log_path.exists():
            size = log_path.stat().st_size
            mod_time = datetime.fromtimestamp(log_path.stat().st_mtime)
            print(
                f"  ✅ {log_file} ({size:,} bytes, 更新: {mod_time.strftime('%H:%M:%S')})"
            )
        else:
            print(f"  ❌ {log_file} (見つかりません)")


def check_a2a_database():
    """A2A監視データベースの確認"""
    print("\n💾 A2A監視データベース:")

    db_path = PROJECT_ROOT / "db" / "a2a_monitoring.db"
    if db_path.exists():
        try:
            with sqlite3.connect(db_path) as conn:
                # 通信記録をチェック
                cursor = conn.execute("SELECT COUNT(*) FROM a2a_communications")
                comm_count = cursor.fetchone()[0]

                # システムヘルス記録をチェック
                cursor = conn.execute("SELECT COUNT(*) FROM system_health")
                health_count = cursor.fetchone()[0]

                print("  ✅ データベース存在")
                print(f"  通信記録: {comm_count}件")
                print(f"  ヘルス記録: {health_count}件")

                # 最新の記録を確認
                cursor = conn.execute(
                    """
                    SELECT timestamp, source_agent, target_agent, message_type, status
                    FROM a2a_communications
                    ORDER BY timestamp DESC LIMIT 3
                """
                )

                recent_comms = cursor.fetchall()
                if recent_comms:
                    print("  最新通信:")
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for comm in recent_comms:
                        print(f"    - {comm[1]} → {comm[2]} ({comm[3]}): {comm[4]}")

        except Exception as e:
            print(f"  ❌ データベース読み込みエラー: {e}")
    else:
        print("  ❌ データベース未作成")


def check_a2a_demo():
    """A2Aデモの実行テスト"""
    print("\n🎮 A2Aデモテスト:")

    demo_file = PROJECT_ROOT / "examples" / "four_sages_a2a_demo.py"
    if demo_file.exists():
        try:
            # デモの軽量実行（構文チェック）
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(demo_file)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("  ✅ デモスクリプト構文OK")
            else:
                print(f"  ❌ デモスクリプト構文エラー: {result.stderr}")

        except Exception as e:
            print(f"  ❌ デモテストエラー: {e}")
    else:
        print("  ❌ デモファイルが見つかりません")


def generate_a2a_summary():
    """A2A状況サマリーの生成"""
    print("\n" + "=" * 60)
    print("📊 A2A（AI-to-AI通信）状況サマリー")
    print("=" * 60)

    # 実装完了度
    implementation_files = [
        "libs/a2a_communication.py",
        "commands/ai_a2a.py",
        "libs/elder_servant_a2a_optimization.py",
        "examples/four_sages_a2a_demo.py",
    ]

    implemented = sum(1 for f in implementation_files if (PROJECT_ROOT / f).exists())
    implementation_rate = (implemented / len(implementation_files)) * 100

    print(
        f"実装完了度: {implementation_rate:.0f}% ({implemented}/{len(implementation_files)})"
    )

    # RabbitMQ状態
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "rabbitmq-server"],
            capture_output=True,
            text=True,
        )
        rabbitmq_status = result.stdout.strip()
        print(f"RabbitMQ: {rabbitmq_status}")
    except:
        print("RabbitMQ: 確認不可")

    # エルダー評議会承認状況
    council_requests = list(PROJECT_ROOT.glob("knowledge_base/*council*request*.md"))
    print(f"評議会承認: {len(council_requests)}件の要請")

    # 監視システム状態
    db_path = PROJECT_ROOT / "db" / "a2a_monitoring.db"
    if db_path.exists():
        print("監視システム: 稼働中")
    else:
        print("監視システム: 初期化中")

    print("\n💡 推奨アクション:")

    if implementation_rate < 100:
        print("  - 残りのA2Aコンポーネントの実装を完了")

    if rabbitmq_status != "active":
        print("  - RabbitMQの起動（A2A通信に必要）")

    if not db_path.exists():
        print("  - A2A監視システムの初期化")

    print("  - Phase 1パイロット導入の準備")
    print("  - 4賢者間通信テストの実行")


def main():
    """メイン処理"""
    print("🤖 A2A（AI-to-AI通信）状況確認")
    print("=" * 60)

    check_a2a_implementation()
    check_system_status()
    check_elder_council_status()
    check_communication_logs()
    check_a2a_database()
    check_a2a_demo()
    generate_a2a_summary()


if __name__ == "__main__":
    main()
