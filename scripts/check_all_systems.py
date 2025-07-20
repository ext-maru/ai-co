#!/usr/bin/env python3
"""
Elders Guild 全システムチェック
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.append("/root/ai_co")


def check_mark(status):
    return "✅" if status else "❌"


def check_system(sections=None, output_format="text"):
    results = {"core": {}, "features": {}, "workers": {}, "libraries": {}}

    # デフォルトで全セクションをチェック
    if sections is None:
        sections = ["core", "workers", "libraries", "features"]

    # 1. コアシステム
    if "core" in sections:
        if output_format == "text":
            print("【コアシステム】")

        # RabbitMQ
        try:
            result = subprocess.run(
                ["sudo", "rabbitmqctl", "status"], capture_output=True
            )
            results["core"]["RabbitMQ"] = result.returncode == 0
        except:
            results["core"]["RabbitMQ"] = False

        # Claude CLI
        try:
            result = subprocess.run(["which", "claude"], capture_output=True)
            results["core"]["Claude CLI"] = result.returncode == 0
        except:
            results["core"]["Claude CLI"] = False

        # Git設定
        try:
            result = subprocess.run(
                ["git", "config", "user.name"], capture_output=True, cwd="/root/ai_co"
            )
            results["core"]["Git設定"] = bool(result.stdout.strip())
        except:
            results["core"]["Git設定"] = False

        if output_format == "text":
            for name, status in results["core"].items():
                print(f"{check_mark(status)} {name}")

    # 2. ワーカー稼働状態
    if "workers" in sections:
        if output_format == "text":
            print("\n【ワーカー】")
        workers = ["task_worker", "pm_worker", "result_worker"]
        for worker in workers:
            ps_result = subprocess.run(
                ["pgrep", "-f", f"{worker}.py"], capture_output=True
            )
            results["workers"][worker] = ps_result.returncode == 0
            if output_format == "text":
                print(f"{check_mark(results['workers'][worker])} {worker}")

    # 3. ライブラリ機能
    print("\n【ライブラリ機能】")
    libs_to_check = {
        "RAGマネージャー": "libs.rag_manager.RAGManager",
        "Slack通知": "libs.slack_notifier.SlackNotifier",
        "自己進化": "libs.self_evolution_manager.SelfEvolutionManager",
        "ワーカー監視": "libs.worker_monitor.WorkerMonitor",
        "スケーリング": "libs.scaling_policy.ScalingPolicy",
        "ヘルスチェック": "libs.health_checker.HealthChecker",
    }

    for name, module_path in libs_to_check.items():
        try:
            module_name, class_name = module_path.rsplit(".", 1)
            exec(f"from {module_name} import {class_name}")
            results["libraries"][name] = True
        except:
            results["libraries"][name] = False
        print(f"{check_mark(results['libraries'][name])} {name}")

    # 4. 機能確認
    print("\n【実装機能】")

    # データベース
    db_file = Path("/root/ai_co/task_history.db")
    results["features"]["SQLite DB"] = db_file.exists()

    # 設定ファイル
    configs = ["slack.conf", "system.conf", "scaling.conf"]
    config_ok = all(Path(f"/root/ai_co/config/{conf}").exists() for conf in configs)
    results["features"]["設定ファイル"] = config_ok

    # 出力ディレクトリ
    output_dir = Path("/root/ai_co/output")
    results["features"]["出力管理"] = output_dir.exists() and any(output_dir.iterdir())

    # Slack Webhook
    try:
        with open("/root/ai_co/config/slack.conf", "r") as f:
            content = f.read()
            results["features"]["Slack設定"] = "hooks.slack.com" in content
    except:
        results["features"]["Slack設定"] = False

    # 自己進化実績
    evolved_files = []
    for pattern in [
        "workers/*_worker_*.py",
        "libs/*_manager_*.py",
        "scripts/evolution_*.py",
    ]:
        evolved_files.extend(Path("/root/ai_co").glob(pattern))
    results["features"]["自己進化実績"] = len(evolved_files) > 0

    for name, status in results["features"].items():
        print(f"{check_mark(status)} {name}")

    # 5. 統計情報
    print("\n【統計】")
    try:
        from features.database.task_history_db import TaskHistoryDB

        db = TaskHistoryDB()
        stats = db.get_stats()
        print(f"📊 タスク総数: {stats.get('total_tasks', 0)}")
        print(f"📁 生成ファイル: {len(list(Path('/root/ai_co/output').rglob('*.py')))}個")
        print(f"🧬 進化ファイル: {len(evolved_files)}個")
    except:
        print("📊 統計取得失敗")

    # 総合評価
    total_checks = sum(len(v) for v in results.values())
    passed_checks = sum(sum(v.values()) for v in results.values())
    score = int(passed_checks / total_checks * 100) if total_checks > 0 else 0

    print(f"\n【総合評価】")
    print(f"🎯 完成度: {score}% ({passed_checks}/{total_checks})")

    if score >= 90:
        print("🎉 Elders Guild システム完全稼働中！")
    elif score >= 70:
        print("⚠️ 一部機能に問題があります")
    else:
        print("❌ システムに重大な問題があります")

    # JSON出力の場合
    if output_format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return results

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Elders Guild system health check tool - Comprehensive system diagnostics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Check all systems
  %(prog)s --sections core workers  # Check only core and workers
  %(prog)s --json                   # Output in JSON format
  %(prog)s --sections features --json  # Check features and output JSON
        """,
    )

    parser.add_argument(
        "--sections",
        "-s",
        nargs="*",
        choices=["core", "workers", "libraries", "features"],
        help="System sections to check (default: all). Available: core, workers, libraries, features",
    )

    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output results in JSON format instead of human-readable text",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output, only return exit code (0=all pass, 1=some fail)",
    )

    args = parser.parse_args()

    output_format = "json" if args.json else "text"
    if args.quiet:
        output_format = "quiet"

    results = check_system(sections=args.sections, output_format=output_format)

    # 戻り値の計算（クワイエットモード用）
    if args.quiet:
        total_checks = sum(len(v) for v in results.values())
        passed_checks = sum(sum(v.values()) for v in results.values())
        exit_code = 0 if passed_checks == total_checks else 1
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
