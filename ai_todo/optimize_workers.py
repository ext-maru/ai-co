#!/usr/bin/env python3
"""
Worker Optimization Script
51個のプロセスを効率的に削減・最適化
"""

import sys
import time
from pathlib import Path

import psutil

sys.path.append(str(Path(__file__).parent.parent))

from libs.worker_load_balancer import WorkerLoadBalancer


def main():
    print("⚡ Worker Optimization - プロセス削減実行")
    print("=" * 60)

    balancer = WorkerLoadBalancer(max_workers=15, target_cpu=60.0)

    # 現在の詳細スキャン
    workers = balancer.scan_workers()
    print(f"🔍 発見されたワーカー: {len(workers)}個")

    for worker in workers:
        try:
            proc = psutil.Process(worker.pid)
            cmdline = " ".join(proc.cmdline()) if proc.cmdline() else ""
            print(f"   PID {worker.pid}: {worker.name} - {cmdline[:80]}...")
        except:
            print(f"   PID {worker.pid}: {worker.name} - (詳細取得不可)")

    # 終了対象の特定
    targets = balancer.identify_optimization_targets(workers)
    candidates = targets["candidates_for_termination"]

    print(f"\n🎯 終了候補: {len(candidates)}個")

    if candidates:
        # 安全な終了を試行
        terminated_count = 0
        for worker in candidates:
            try:
                proc = psutil.Process(worker.pid)
                cmdline = " ".join(proc.cmdline()) if proc.cmdline() else ""

                # 重要プロセスをスキップ
                if any(
                    critical in cmdline
                    for critical in ["claude", "dashboard_server.py"]
                ):
                    print(f"   ⚠️  保護: {worker.name} (PID: {worker.pid}) - 重要プロセス")
                    continue

                # 重複workerのみ終了
                if "worker" in cmdline and (
                    "slack_polling" in cmdline or "error_intelligence" in cmdline
                ):
                    print(f"   🗑️  終了: {worker.name} (PID: {worker.pid})")
                    proc.terminate()
                    time.sleep(1)

                    if proc.is_running():
                        proc.kill()

                    terminated_count += 1

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"   ⚠️  スキップ: {worker.name} (PID: {worker.pid}) - アクセス拒否")

        print(f"\n✅ 最適化完了: {terminated_count}個のワーカーを終了")

        # 結果確認
        time.sleep(3)
        new_workers = balancer.scan_workers()
        print(f"📊 最適化後: {len(new_workers)}個のワーカーが稼働中")

        reduction = len(workers) - len(new_workers)
        print(f"🎉 削減効果: {reduction}個のプロセスを削減 ({len(workers)} → {len(new_workers)})")

    else:
        print("💡 終了可能なワーカーが見つかりませんでした")

    # 最終レポート
    final_status = balancer.get_current_status()
    print(f"\n📈 最終状況:")
    print(f"   総ワーカー数: {final_status['metrics']['total_workers']}")
    print(f"   システム負荷: {final_status['metrics']['system_load']:.1f}%")
    print(f"   平均メモリ: {final_status['metrics']['avg_memory']:.1f}MB")


if __name__ == "__main__":
    main()
