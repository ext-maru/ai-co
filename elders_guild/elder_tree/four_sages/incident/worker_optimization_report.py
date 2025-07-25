#!/usr/bin/env python3
"""
Worker Optimization Report Generator
システム管理者向けの詳細な最適化レポート
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import psutil

sys.path.append(str(Path(__file__).parent.parent))

from libs.worker_load_balancer import WorkerLoadBalancer

def generate_detailed_report():
    print("📋 Worker Optimization Report Generator")
    print("=" * 60)

    balancer = WorkerLoadBalancer(max_workers=15, target_cpu=60.0)

    # 詳細スキャン
    workers = balancer.scan_workers()
    metrics = balancer.analyze_load_distribution(workers)
    targets = balancer.identify_optimization_targets(workers)

    report = {
        "timestamp": datetime.now().isoformat(),
        "system_overview": {
            "total_workers": metrics.total_workers,
            "active_workers": metrics.active_workers,
            "idle_workers": metrics.idle_workers,
            "avg_cpu": metrics.avg_cpu,
            "avg_memory": metrics.avg_memory,
            "system_load": metrics.system_load,
        },
        "worker_details": [],
        "optimization_targets": {
            "high_cpu": len(targets["high_cpu"]),
            "high_memory": len(targets["high_memory"]),
            "idle_long": len(targets["idle_long"]),
            "redundant": len(targets["redundant"]),
            "termination_candidates": len(targets["candidates_for_termination"]),
        },
        "termination_commands": [],
        "recommendations": [],
    }

    print(f"🔍 分析中: {len(workers)}個のワーカープロセス")

    # 各ワーカーの詳細分析
    for worker in workers:
        try:
            proc = psutil.Process(worker.pid)
            cmdline = " ".join(proc.cmdline()) if proc.cmdline() else ""

            worker_info = {
                "pid": worker.pid,
                "name": worker.name,
                "cmdline": cmdline,
                "cpu_percent": worker.cpu_percent,
                "memory_mb": worker.memory_mb,
                "status": worker.status,
                "uptime_hours": (datetime.now() - worker.start_time).total_seconds()
                / 3600,
                "category": "unknown",
            }

            # カテゴリ分類
            if "error_intelligence_worker" in cmdline:
                worker_info["category"] = "error_intelligence"
            elif "slack_polling_worker" in cmdline:
                worker_info["category"] = "slack_polling"
            elif "dashboard_server" in cmdline:
                worker_info["category"] = "dashboard"
            elif "claude" in cmdline:
                worker_info["category"] = "claude_cli"
            elif any(w in cmdline for w in ["worker", "task"]):
                worker_info["category"] = "task_worker"

            # 終了推奨判定
            is_termination_candidate = False
            termination_reason = []

            if worker.cpu_percent < 0.5 and worker_info["uptime_hours"] > 1:
                is_termination_candidate = True
                termination_reason.append("low_cpu_long_idle")

            if (
                worker_info["category"] == "error_intelligence"
                and len(
                    [
                        w
                        for w in workers
                        if "error_intelligence_worker"
                        in (
                            " ".join(psutil.Process(w.pid).cmdline())
                            if psutil.Process(w.pid).cmdline()
                            else ""
                        )
                    ]
                )
                > 2
            ):
                is_termination_candidate = True
                termination_reason.append("redundant_error_worker")

            worker_info["termination_candidate"] = is_termination_candidate
            worker_info["termination_reason"] = termination_reason

            # 終了コマンド生成（管理者用）
            if is_termination_candidate and worker_info["category"] not in [
                "dashboard",
                "claude_cli",
            ]:
                report["termination_commands"].append(
                    {
                        "pid": worker.pid,
                        "command": f"sudo kill -TERM {worker.pid}",
                        "force_command": f"sudo kill -KILL {worker.pid}",
                        "reason": ", ".join(termination_reason),
                    }
                )

            report["worker_details"].append(worker_info)

        except Exception as e:
            print(f"   ⚠️  エラー (PID {worker.pid}): {e}")

    # カテゴリ別統計
    category_stats = {}
    for worker in report["worker_details"]:
        cat = worker["category"]
        if cat not in category_stats:
            category_stats[cat] = {"count": 0, "total_memory": 0, "total_cpu": 0}
        category_stats[cat]["count"] += 1
        category_stats[cat]["total_memory"] += worker["memory_mb"]
        category_stats[cat]["total_cpu"] += worker["cpu_percent"]

    report["category_statistics"] = category_stats

    # 推奨事項生成
    recommendations = []

    # 重複error_intelligenceワーカー
    error_workers = [
        w for w in report["worker_details"] if w["category"] == "error_intelligence"
    ]
    if len(error_workers) > 2:
        recommendations.append(
            f"{len(error_workers)}個のerror_intelligence_workerが稼働中。2個まで削減推奨"
        )

    # アイドルワーカー
    idle_workers = [
        w
        for w in report["worker_details"]
        if w["cpu_percent"] < 0.5 and w["uptime_hours"] > 1
    ]
    if len(idle_workers) > 3:
        recommendations.append(f"{len(idle_workers)}個の長時間アイドルワーカーの終了推奨")

    # メモリ使用量
    high_memory = [w for w in report["worker_details"] if w["memory_mb"] > 100]
    if len(high_memory) > 0:
        recommendations.append(f"{len(high_memory)}個の高メモリ使用ワーカーの監視推奨")

    report["recommendations"] = recommendations

    # レポート出力
    output_file = (

    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # コンソール出力
    print(f"\n📊 分析結果:")
    print(f"   総ワーカー数: {report['system_overview']['total_workers']}")
    print(f"   終了候補: {len(report['termination_commands'])}個")

    print(f"\n📂 カテゴリ別統計:")
    for category, stats in category_stats.items():
        print(
            (
                f"f"   {category}: {stats['count']}個 (平均CPU: {stats['total_cpu']/stats['count']:0.1f}%, 平均メモリ: "
                f"{stats['total_memory']/stats['count']:0.1f}MB)""
            )
        )

    print(f"\n🎯 終了推奨ワーカー:")
    for cmd in report["termination_commands"][:5]:  # 上位5個
        print(f"   PID {cmd['pid']}: {cmd['command']} # {cmd['reason']}")

    print(f"\n💡 推奨事項:")
    for rec in recommendations:
        print(f"   • {rec}")

    print(f"\n📄 詳細レポート保存: {output_file}")

    return report

if __name__ == "__main__":
    generate_detailed_report()
