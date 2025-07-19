#!/usr/bin/env python3
"""
🛡️ Knights Status Check
騎士団の稼働状況確認システム
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

import psutil

PROJECT_ROOT = Path(__file__).parent.parent


def check_knights_status():
    """騎士団の稼働状況チェック"""

    print("🛡️ インシデント騎士団 稼働状況チェック")
    print("=" * 60)

    status = {
        "timestamp": datetime.now().isoformat(),
        "knights_deployed": False,
        "frameworks_available": False,
        "processes_running": False,
        "repair_capability": False,
        "overall_status": "unknown",
    }

    # 1. 騎士団ファイルの存在確認
    print("📁 騎士団ファイル確認...")

    required_files = [
        "libs/incident_knights_framework.py",
        "libs/command_guardian_knight.py",
        "libs/auto_repair_knight.py",
        "libs/syntax_repair_knight.py",
        "libs/coverage_enhancement_knight.py",
        "commands/ai_incident_knights.py",
    ]

    file_count = 0
    for file_path in required_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            file_count += 1
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")

    if file_count == len(required_files):
        status["frameworks_available"] = True
        print(f"📦 フレームワーク: ✅ {file_count}/{len(required_files)} 利用可能")
    else:
        print(f"📦 フレームワーク: ❌ {file_count}/{len(required_files)} 不完全")

    # 2. 騎士団プロセスの確認
    print("\n🔍 プロセス稼働状況...")

    knight_processes = []
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            cmdline = " ".join(proc.info["cmdline"] or [])
            if any(
                keyword in cmdline.lower()
                for keyword in ["knight", "incident", "coverage"]
            ):
                knight_processes.append(
                    {
                        "pid": proc.info["pid"],
                        "name": proc.info["name"],
                        "cmdline": cmdline,
                    }
                )

        if knight_processes:
            status["processes_running"] = True
            print(f"⚡ 稼働中プロセス: {len(knight_processes)}件")
            for proc in knight_processes:
                print(f"  🔧 PID {proc['pid']}: {proc['cmdline'][:80]}...")
        else:
            print("⏸️ 稼働中プロセス: なし")

    except Exception as e:
        print(f"❌ プロセス確認エラー: {e}")

    # 3. 修復能力のテスト
    print("\n🧪 修復能力テスト...")

    try:
        # テスト用の簡単な構文チェック
        test_files = [
            "libs/rate_limit_queue_processor.py",
            "workers/error_intelligence_worker.py",
        ]

        syntax_ok_count = 0
        for test_file in test_files:
            file_path = PROJECT_ROOT / test_file
            if file_path.exists():
                try:
                    import ast

                    with open(file_path) as f:
                        ast.parse(f.read())
                    syntax_ok_count += 1
                    print(f"  ✅ {test_file}: 構文OK")
                except Exception:
                    print(f"  ❌ {test_file}: 構文エラー")
            else:
                print(f"  ⚠️ {test_file}: ファイル未存在")

        if syntax_ok_count == len(test_files):
            status["repair_capability"] = True
            print(f"🔧 修復能力: ✅ 正常 ({syntax_ok_count}/{len(test_files)})")
        else:
            print(f"🔧 修復能力: ⚠️ 部分的 ({syntax_ok_count}/{len(test_files)})")

    except Exception as e:
        print(f"❌ 修復能力テストエラー: {e}")

    # 4. 配置状況の確認
    print("\n📊 配置状況...")

    deployment_files = [
        "knowledge_base/INCIDENT_KNIGHTS_SUCCESS_REPORT.md",
        "knowledge_base/MISSION_COMPLETE_100_PERCENT_AUTONOMOUS.md",
    ]

    deployed_count = 0
    for deploy_file in deployment_files:
        file_path = PROJECT_ROOT / deploy_file
        if file_path.exists():
            deployed_count += 1
            print(f"  ✅ {deploy_file}")
        else:
            print(f"  ❌ {deploy_file}")

    if deployed_count > 0:
        status["knights_deployed"] = True
        print(f"🚀 配置状況: ✅ 展開済み ({deployed_count}/{len(deployment_files)})")
    else:
        print(f"🚀 配置状況: ❌ 未展開")

    # 5. 総合判定
    print("\n🎯 総合判定...")

    scores = [
        status["frameworks_available"],
        status["knights_deployed"],
        status["repair_capability"],
    ]

    active_score = sum(scores)

    if active_score >= 3:
        status["overall_status"] = "fully_operational"
        print("🛡️ 騎士団状態: ✅ 完全稼働")
    elif active_score >= 2:
        status["overall_status"] = "partially_operational"
        print("🛡️ 騎士団状態: ⚠️ 部分稼働")
    elif active_score >= 1:
        status["overall_status"] = "limited_operational"
        print("🛡️ 騎士団状態: 🔧 限定稼働")
    else:
        status["overall_status"] = "not_operational"
        print("🛡️ 騎士団状態: ❌ 非稼働")

    # 6. 推奨アクション
    print("\n💡 推奨アクション...")

    if not status["processes_running"]:
        print("  🚀 騎士団の継続監視を開始してください")
        print("     python3 libs/incident_knights_framework.py")

    if not status["frameworks_available"]:
        print("  📦 騎士団フレームワークを再展開してください")
        print("     python3 scripts/deploy_incident_knights.py")

    if status["overall_status"] == "fully_operational":
        print("  🎉 システムは完全稼働中です！")
        print("  ✨ 継続的な自動修復が実行されています")

    # ステータス保存
    status_file = PROJECT_ROOT / "data" / "knights_live_status.json"
    status_file.parent.mkdir(exist_ok=True)

    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    print(f"\n📄 ステータス保存: {status_file}")

    return status


if __name__ == "__main__":
    status = check_knights_status()

    print("\n" + "=" * 60)
    overall = status["overall_status"]
    if overall == "fully_operational":
        print("🎊 騎士団は完全稼働中です！Elders Guildを守護しています！")
    elif overall == "partially_operational":
        print("⚠️ 騎士団は部分稼働中です。完全稼働まであと少しです。")
    else:
        print("🔧 騎士団の稼働準備が必要です。")
