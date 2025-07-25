#!/usr/bin/env python3
"""
スケーリング状態の確認
"""
import sys

sys.path.append("/root/ai_co")

import argparse
import json
from datetime import datetime

from core.monitoring.scaling_policy import ScalingPolicy
from core.monitoring.worker_monitor import WorkerMonitor


def show_scaling_status(output_format="text", sections=None):
    """スケーリング状態を表示"""
    monitor = WorkerMonitor()
    policy = ScalingPolicy()

    # 現在のメトリクス
    metrics = monitor.get_all_metrics()

    # 次のアクション予測
    action, target = policy.should_scale(metrics)

    # スケーリング履歴
    stats = policy.get_scaling_stats()

    # データ構造化
    data = {
        "timestamp": datetime.now().isoformat(),
        "current_status": {
            "active_workers": metrics["active_workers"],
            "queue_length": metrics["queue_length"],
            "system": {
                "cpu_percent": metrics["system"]["cpu_percent"],
                "memory_percent": metrics["system"]["memory_percent"],
                "load_average": metrics["system"]["load_average"],
            },
        },
        "worker_details": metrics["worker_details"],
        "scaling_config": {
            "min_workers": policy.config["MIN_WORKERS"],
            "max_workers": policy.config["MAX_WORKERS"],
            "scale_up_threshold": policy.config["SCALE_UP_QUEUE_LENGTH"],
            "scale_down_threshold": policy.config["SCALE_DOWN_QUEUE_LENGTH"],
            "cooldown_seconds": policy.config["COOLDOWN_SECONDS"],
        },
        "next_action": {"action": action, "target_workers": target},
        "scaling_stats": stats,
    }

    if output_format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data

    # テキスト形式での表示
    if sections is None or "status" in sections:
        print("=== 🔄 ワーカー動的管理状態 ===")
        print(f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")

        print("📊 現在の状態:")
        print(f"  稼働中ワーカー: {metrics['active_workers']}")
        print(f"  キュー長: {metrics['queue_length']}")
        print(f"  CPU使用率: {metrics['system']['cpu_percent']:0.1f}%")
        print(f"  メモリ使用率: {metrics['system']['memory_percent']:0.1f}%")
        print(f"  ロードアベレージ: {metrics['system']['load_average']:0.2f}")

    if sections is None or "workers" in sections:
        print("\n📋 ワーカー詳細:")
        for worker in metrics["worker_details"]:
            print(
                f"  {worker['worker_id']} - PID: {worker['pid']}, CPU: {worker['cpu']}%, Mem: {worker['mem']}%"
            )

    if sections is None or "config" in sections:
        print("\n⚙️ スケーリング設定:")
        print(f"  最小ワーカー数: {policy.config['MIN_WORKERS']}")
        print(f"  最大ワーカー数: {policy.config['MAX_WORKERS']}")
        print(f"  スケールアップ閾値: キュー長 > {policy.config['SCALE_UP_QUEUE_LENGTH']}")
        print(f"  スケールダウン閾値: キュー長 <= {policy.config['SCALE_DOWN_QUEUE_LENGTH']}")
        print(f"  クールダウン期間: {policy.config['COOLDOWN_SECONDS']}秒")

    if sections is None or "prediction" in sections:
        print(f"\n🎯 次のスケーリング判定: {action}")
        if action != "none":
            print(f"  推奨ワーカー数: {target}")

    if sections is None or "stats" in sections:
        print(f"\n📈 スケーリング統計:")
        print(f"  総スケーリング回数: {stats['total_scaling']}")
        print(f"  スケールアップ: {stats['scale_ups']}回")
        print(f"  スケールダウン: {stats['scale_downs']}回")
        if stats["last_scaling"]:
            print(f"  最終スケーリング: {stats['last_scaling']}")

    return data


def main():
    """mainメソッド"""
    parser = argparse.ArgumentParser(
        description="Worker scaling status monitor - View current scaling state and predictions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Show all scaling information
  %(prog)s --sections status workers # Show only current status and worker details
  %(prog)s --json                   # Output in JSON format
  %(prog)s --sections stats --json  # Show only statistics in JSON format
        """,
    )

    parser.add_argument(
        "--sections",
        "-s",
        nargs="*",
        choices=["status", "workers", "config", "prediction", "stats"],
        help="Information sections to display (default: all). Available: status, workers, config, prediction, stats",
    )

    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output results in JSON format instead of human-readable text",
    )

    parser.add_argument(
        "--watch",
        "-w",
        type=int,
        metavar="SECONDS",
        help="Watch mode: continuously update display every N seconds",
    )

    args = parser.parse_args()

    output_format = "json" if args.json else "text"

    if args.watch:
        import time

        try:
            while True:
                if output_format == "text":
                    print("\033[2J\033[H")  # Clear screen
                show_scaling_status(output_format=output_format, sections=args.sections)
                if output_format == "text":
                    print(f"\n更新間隔: {args.watch}秒 (Ctrl+C で終了)")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\n監視を終了します。")
    else:
        show_scaling_status(output_format=output_format, sections=args.sections)


if __name__ == "__main__":
    main()
