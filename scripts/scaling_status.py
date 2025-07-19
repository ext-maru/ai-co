#!/usr/bin/env python3
from pathlib import Path

"""
スケーリング状態の確認
"""
import sys

sys.path.append(str(Path(__file__).parent.parent))

import json
from datetime import datetime

from libs.scaling_policy import ScalingPolicy
from libs.worker_monitor import WorkerMonitor


def show_scaling_status():
    """スケーリング状態を表示"""
    monitor = WorkerMonitor()
    policy = ScalingPolicy()

    print("=== 🔄 ワーカー動的管理状態 ===")
    print(f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # 現在のメトリクス
    metrics = monitor.get_all_metrics()

    print("📊 現在の状態:")
    print(f"  稼働中ワーカー: {metrics['active_workers']}")
    print(f"  キュー長: {metrics['queue_length']}")
    print(f"  CPU使用率: {metrics['system']['cpu_percent']:.1f}%")
    print(f"  メモリ使用率: {metrics['system']['memory_percent']:.1f}%")
    print(f"  ロードアベレージ: {metrics['system']['load_average']:.2f}")

    print("\n📋 ワーカー詳細:")
    for worker in metrics["worker_details"]:
        print(
            f"  {worker['worker_id']} - PID: {worker['pid']}, CPU: {worker['cpu']}%, Mem: {worker['mem']}%"
        )

    print("\n⚙️ スケーリング設定:")
    print(f"  最小ワーカー数: {policy.config['MIN_WORKERS']}")
    print(f"  最大ワーカー数: {policy.config['MAX_WORKERS']}")
    print(f"  スケールアップ閾値: キュー長 > {policy.config['SCALE_UP_QUEUE_LENGTH']}")
    print(
        f"  スケールダウン閾値: キュー長 <= {policy.config['SCALE_DOWN_QUEUE_LENGTH']}"
    )
    print(f"  クールダウン期間: {policy.config['COOLDOWN_SECONDS']}秒")

    # 次のアクション予測
    action, target = policy.should_scale(metrics)
    print(f"\n🎯 次のスケーリング判定: {action}")
    if action != "none":
        print(f"  推奨ワーカー数: {target}")

    # スケーリング履歴
    stats = policy.get_scaling_stats()
    print(f"\n📈 スケーリング統計:")
    print(f"  総スケーリング回数: {stats['total_scaling']}")
    print(f"  スケールアップ: {stats['scale_ups']}回")
    print(f"  スケールダウン: {stats['scale_downs']}回")
    if stats["last_scaling"]:
        print(f"  最終スケーリング: {stats['last_scaling']}")


if __name__ == "__main__":
    show_scaling_status()
