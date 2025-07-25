#!/usr/bin/env python3
"""
Worker Load Balancer - Dynamic Process Optimization
51個のプロセスを効率的に管理・負荷分散
"""

import json
import logging
import queue
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class WorkerProcess:
    """ワーカープロセス情報"""

    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    status: str
    start_time: datetime
    task_count: int = 0
    last_activity: Optional[datetime] = None

@dataclass
class LoadMetrics:
    """負荷メトリクス"""

    total_workers: int
    active_workers: int
    idle_workers: int
    avg_cpu: float
    avg_memory: float
    total_tasks: int
    system_load: float

class WorkerLoadBalancer:
    """ワーカー負荷分散システム"""

    def __init__(self, max_workers: int = 20, target_cpu: float = 70.0):
        """初期化メソッド"""
        self.max_workers = max_workers
        self.target_cpu = target_cpu
        self.workers: Dict[int, WorkerProcess] = {}
        self.task_queue = queue.Queue()
        self.metrics_history = deque(maxlen=100)
        self.running = False
        self.monitor_thread = None

    def scan_workers(self) -> List[WorkerProcess]:
        """現在のワーカープロセスをスキャン"""
        workers = []

        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_info", "status", "create_time"]
        ):
            try:
                info = proc.info

                # AI関連プロセスを特定
                cmdline = " ".join(proc.cmdline()) if proc.cmdline() else ""
                if any(
                    keyword in info["name"].lower() for keyword in ["python", "python3"]
                ):
                    if any(
                        pattern in cmdline
                        for pattern in ["worker", "claude", "ai_co", "dashboard"]
                    ):
                        worker = WorkerProcess(
                            pid=info["pid"],
                            name=info["name"],
                            cpu_percent=info["cpu_percent"] or 0.0,
                            memory_mb=(
                                info["memory_info"].rss / 1024 / 1024
                                if info["memory_info"]
                                else 0.0
                            ),
                            status=info["status"],
                            start_time=datetime.fromtimestamp(info["create_time"]),
                        )
                        workers.append(worker)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return workers

    def analyze_load_distribution(self, workers: List[WorkerProcess]) -> LoadMetrics:
        """負荷分散状況を分析"""
        if not workers:
            return LoadMetrics(0, 0, 0, 0.0, 0.0, 0, 0.0)

        active_workers = [w for w in workers if w.cpu_percent > 1.0]
        idle_workers = [w for w in workers if w.cpu_percent <= 1.0]

        avg_cpu = sum(w.cpu_percent for w in workers) / len(workers)
        avg_memory = sum(w.memory_mb for w in workers) / len(workers)
        total_tasks = sum(w.task_count for w in workers)

        # システム全体の負荷
        system_load = psutil.cpu_percent()

        return LoadMetrics(
            total_workers=len(workers),
            active_workers=len(active_workers),
            idle_workers=len(idle_workers),
            avg_cpu=avg_cpu,
            avg_memory=avg_memory,
            total_tasks=total_tasks,
            system_load=system_load,
        )

    def identify_optimization_targets(
        self, workers: List[WorkerProcess]
    ) -> Dict[str, List[WorkerProcess]]:
        """最適化対象を特定"""
        targets = {
            "high_cpu": [],
            "high_memory": [],
            "idle_long": [],
            "redundant": [],
            "candidates_for_termination": [],
        }

        now = datetime.now()

        for worker in workers:
            # 高CPU使用率
            if worker.cpu_percent > 80.0:
                targets["high_cpu"].append(worker)

            # 高メモリ使用率
            if worker.memory_mb > 500.0:
                targets["high_memory"].append(worker)

            # 長時間アイドル
            idle_time = (now - worker.start_time).total_seconds()
            if worker.cpu_percent < 0.5 and idle_time > 1800:  # 30分以上アイドル
                targets["idle_long"].append(worker)

            # 重複プロセス
            similar_workers = [
                w for w in workers if w.name == worker.name and w.pid != worker.pid
            ]
            if len(similar_workers) > 2:  # 同名プロセスが3個以上
                targets["redundant"].append(worker)

        # 終了候補（アイドル + 重複）
        targets["candidates_for_termination"] = list(
            set(targets["idle_long"] + targets["redundant"])
        )

        return targets

    def calculate_optimal_worker_count(self, metrics: LoadMetrics) -> int:
        """最適ワーカー数を計算"""
        # システム負荷に基づく動的調整
        if metrics.system_load > 90:
            return max(1, metrics.total_workers - 5)  # 大幅削減
        elif metrics.system_load > 80:
            return max(5, metrics.total_workers - 3)  # 中程度削減
        elif metrics.system_load < 30:
            return min(self.max_workers, metrics.total_workers + 2)  # 増加
        else:
            return min(self.max_workers, max(8, metrics.total_workers))  # 維持

    def terminate_worker(self, worker: WorkerProcess, force: bool = False) -> bool:
        """ワーカーを安全に終了"""
        try:
            proc = psutil.Process(worker.pid)

            # クリティカルプロセスのチェック (claude、dashboard_serverは保護)
            cmdline = " ".join(proc.cmdline()) if proc.cmdline() else ""
            if not force and any(
                critical in cmdline for critical in ["claude", "dashboard_server"]
            ):
                logger.info(
                    f"Skipping critical process {worker.name} (PID: {worker.pid})"
                )
                return False

            # 先にSIGTERMで穏やかに終了を試行
            proc.terminate()
            time.sleep(2)

            # まだ生きていればSIGKILL
            if proc.is_running():
                proc.kill()
                time.sleep(1)

            logger.info(f"Terminated worker {worker.name} (PID: {worker.pid})")
            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Could not terminate worker {worker.pid}: {e}")
            return False

    def optimize_worker_distribution(self) -> Dict[str, any]:
        """ワーカー分散を最適化"""
        workers = self.scan_workers()
        metrics = self.analyze_load_distribution(workers)
        targets = self.identify_optimization_targets(workers)
        optimal_count = self.calculate_optimal_worker_count(metrics)

        optimization_result = {
            "timestamp": datetime.now().isoformat(),
            "before": {
                "worker_count": metrics.total_workers,
                "avg_cpu": metrics.avg_cpu,
                "avg_memory": metrics.avg_memory,
                "system_load": metrics.system_load,
            },
            "optimization_actions": [],
            "terminated_workers": [],
            "after": {},
        }

        # 過剰なワーカーを終了
        if metrics.total_workers > optimal_count:
            workers_to_terminate = targets["candidates_for_termination"][
                : metrics.total_workers - optimal_count
            ]

            for worker in workers_to_terminate:
                if self.terminate_worker(worker):
                    optimization_result["terminated_workers"].append(
                        {
                            "pid": worker.pid,
                            "name": worker.name,
                            "reason": "idle_or_redundant",
                        }
                    )
                    optimization_result["optimization_actions"].append(
                        f"Terminated {worker.name} (PID: {worker.pid})"
                    )

        # 最適化後の状態を測定
        time.sleep(3)  # プロセス終了の反映を待つ
        updated_workers = self.scan_workers()
        updated_metrics = self.analyze_load_distribution(updated_workers)

        optimization_result["after"] = {
            "worker_count": updated_metrics.total_workers,
            "avg_cpu": updated_metrics.avg_cpu,
            "avg_memory": updated_metrics.avg_memory,
            "system_load": updated_metrics.system_load,
            "reduction": metrics.total_workers - updated_metrics.total_workers,
        }

        # メトリクス履歴に追加
        self.metrics_history.append(updated_metrics)

        return optimization_result

    def start_monitoring(self):
        """負荷監視を開始"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Worker load balancer monitoring started")

    def stop_monitoring(self):
        """負荷監視を停止"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Worker load balancer monitoring stopped")

    def _monitor_loop(self):
        """監視ループ"""
        while self.running:
            try:
                workers = self.scan_workers()
                metrics = self.analyze_load_distribution(workers)

                # 自動最適化の閾値チェック
                if metrics.total_workers > self.max_workers or metrics.system_load > 85:
                    logger.info(
                        f"Auto-optimization triggered: {metrics.total_workers} workers, " \
                            "{metrics.system_load}% system load"
                    )
                    self.optimize_worker_distribution()

                self.metrics_history.append(metrics)
                time.sleep(30)  # 30秒間隔で監視

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # エラー時は1分待機

    def get_current_status(self) -> Dict[str, any]:
        """現在の状態を取得"""
        workers = self.scan_workers()
        metrics = self.analyze_load_distribution(workers)
        targets = self.identify_optimization_targets(workers)

        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_workers": metrics.total_workers,
                "active_workers": metrics.active_workers,
                "idle_workers": metrics.idle_workers,
                "avg_cpu": metrics.avg_cpu,
                "avg_memory": metrics.avg_memory,
                "system_load": metrics.system_load,
            },
            "optimization_targets": {
                "high_cpu_count": len(targets["high_cpu"]),
                "high_memory_count": len(targets["high_memory"]),
                "idle_long_count": len(targets["idle_long"]),
                "redundant_count": len(targets["redundant"]),
                "termination_candidates": len(targets["candidates_for_termination"]),
            },
            "recommendations": self._generate_recommendations(metrics, targets),
        }

    def _generate_recommendations(
        self, metrics: LoadMetrics, targets: Dict[str, List[WorkerProcess]]
    ) -> List[str]:
        """最適化推奨事項を生成"""
        recommendations = []

        if metrics.total_workers > self.max_workers:
            recommendations.append(
                f"{metrics.total_workers - self.max_workers}個のワーカーを削減推奨"
            )

        if metrics.system_load > 80:
            recommendations.append("システム負荷が高いため、ワーカー数の削減が必要")

        if len(targets["idle_long"]) > 0:
            recommendations.append(
                f"{len(targets['idle_long'])}個の長時間アイドルワーカーの終了推奨"
            )

        if len(targets["redundant"]) > 0:
            recommendations.append(
                f"{len(targets['redundant'])}個の重複ワーカーの統合推奨"
            )

        if metrics.avg_cpu < 20 and metrics.total_workers > 10:
            recommendations.append("低CPU使用率のため、ワーカー数の最適化推奨")

        return recommendations

    def export_metrics_report(self, output_path: str):
        """メトリクスレポートをエクスポート"""
        report_data = {
            "export_timestamp": datetime.now().isoformat(),
            "current_status": self.get_current_status(),
            "metrics_history": [
                {
                    "total_workers": m.total_workers,
                    "active_workers": m.active_workers,
                    "avg_cpu": m.avg_cpu,
                    "avg_memory": m.avg_memory,
                    "system_load": m.system_load,
                }
                for m in list(self.metrics_history)
            ],
            "optimization_summary": {
                "max_workers_limit": self.max_workers,
                "target_cpu_threshold": self.target_cpu,
                "monitoring_active": self.running,
            },
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Metrics report exported to {output_path}")

def main():
    """メイン実行関数"""
    print("🔧 Worker Load Balancer - 負荷分散最適化システム")
    print("=" * 60)

    balancer = WorkerLoadBalancer(max_workers=20, target_cpu=70.0)

    # 現在の状態確認
    print("📊 現在の状態分析中...")
    status = balancer.get_current_status()

    print(f"\n📈 現在のワーカー状況:")
    print(f"   総ワーカー数: {status['metrics']['total_workers']}")
    print(f"   アクティブ: {status['metrics']['active_workers']}")
    print(f"   アイドル: {status['metrics']['idle_workers']}")
    print(f"   平均CPU: {status['metrics']['avg_cpu']:0.1f}%")
    print(f"   平均メモリ: {status['metrics']['avg_memory']:0.1f}MB")
    print(f"   システム負荷: {status['metrics']['system_load']:0.1f}%")

    print(f"\n🎯 最適化対象:")
    for key, count in status["optimization_targets"].items():
        if count > 0:
            print(f"   {key}: {count}個")

    print(f"\n💡 推奨事項:")
    for rec in status["recommendations"]:
        print(f"   • {rec}")

    # 最適化実行
    if status["optimization_targets"]["termination_candidates"] > 0:
        print(f"\n⚡ 最適化実行中...")
        result = balancer.optimize_worker_distribution()

        print(f"✅ 最適化完了:")
        print(
            f"   ワーカー数: {result['before']['worker_count']} → {result['after']['worker_count']}"
        )
        print(
            f"   システム負荷: {result['before']['system_load']:0.1f}% → {result['after']['system_load']:0.1f}%"
        )
        print(f"   終了したワーカー: {len(result['terminated_workers'])}個")

        if result["terminated_workers"]:
            print(f"\n🗑️ 終了したワーカー:")
            for worker in result["terminated_workers"]:
                print(
                    f"   • {worker['name']} (PID: {worker['pid']}) - {worker['reason']}"
                )

    # レポート保存
    balancer.export_metrics_report(

    )
    print(f"\n📄 詳細レポートを保存しました")

    print(f"\n🎉 Worker Load Balancer 最適化完了！")

if __name__ == "__main__":
    main()
