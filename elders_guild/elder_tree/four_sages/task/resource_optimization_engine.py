#!/usr/bin/env python3
"""
リソース最適化エンジン - Task Sage統合コンポーネント
Created: 2025-07-17
Author: Claude Elder
"""

import asyncio
import json
import logging

# プロジェクトルートインポート
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import psutil

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.lightweight_logger import get_logger
from elders_guild.elder_tree.four_sages.task.task_sage import TaskEntry, TaskResource, TaskStatus
from elders_guild.elder_tree.tracking.unified_tracking_db import UnifiedTrackingDB

logger = get_logger("resource_optimization_engine")


@dataclass
class SystemResource:
    """システムリソース情報"""

    cpu_percent: float
    cpu_cores: int
    memory_percent: float
    memory_available_gb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_send_mb: float
    network_io_recv_mb: float
    timestamp: datetime


@dataclass
class TaskResourceUsage:
    """タスクのリソース使用予測"""

    task_id: str
    cpu_usage: float  # パーセント
    memory_usage: float  # MB
    disk_io: float  # MB/s
    network_io: float  # MB/s
    estimated_duration: float  # 秒


class SystemResourceMonitor:
    """システムリソースモニター"""

    def __init__(self):
        """初期化メソッド"""
        self.history = []
        self.max_history = 100
        self._last_disk_io = None
        self._last_net_io = None
        self._last_timestamp = None

    async def get_current_usage(self) -> SystemResource:
        """現在のリソース使用状況を取得"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_cores = psutil.cpu_count()

            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)

            # ディスクI/O
            disk_io = psutil.disk_io_counters()
            current_time = datetime.now()

            if self._last_disk_io and self._last_timestamp:
                time_delta = (current_time - self._last_timestamp).total_seconds()
                disk_read_mb = (
                    (disk_io.read_bytes - self._last_disk_io.read_bytes)
                    / (1024**2)
                    / time_delta
                )
                disk_write_mb = (
                    (disk_io.write_bytes - self._last_disk_io.write_bytes)
                    / (1024**2)
                    / time_delta
                )
            else:
                disk_read_mb = 0
                disk_write_mb = 0

            self._last_disk_io = disk_io

            # ネットワークI/O
            net_io = psutil.net_io_counters()

            if self._last_net_io and self._last_timestamp:
                time_delta = (current_time - self._last_timestamp).total_seconds()
                net_send_mb = (
                    (net_io.bytes_sent - self._last_net_io.bytes_sent)
                    / (1024**2)
                    / time_delta
                )
                net_recv_mb = (
                    (net_io.bytes_recv - self._last_net_io.bytes_recv)
                    / (1024**2)
                    / time_delta
                )
            else:
                net_send_mb = 0
                net_recv_mb = 0

            self._last_net_io = net_io
            self._last_timestamp = current_time

            resource = SystemResource(
                cpu_percent=cpu_percent,
                cpu_cores=cpu_cores,
                memory_percent=memory_percent,
                memory_available_gb=memory_available_gb,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_io_send_mb=net_send_mb,
                network_io_recv_mb=net_recv_mb,
                timestamp=current_time,
            )

            # 履歴に追加
            self.history.append(resource)
            if len(self.history) > self.max_history:
                self.history.pop(0)

            return resource

        except Exception as e:
            logger.error(f"Failed to get system resources: {e}")
            # エラー時のデフォルト値
            return SystemResource(
                cpu_percent=50.0,
                cpu_cores=4,
                memory_percent=50.0,
                memory_available_gb=4.0,
                disk_io_read_mb=0,
                disk_io_write_mb=0,
                network_io_send_mb=0,
                network_io_recv_mb=0,
                timestamp=datetime.now(),
            )

    def get_average_usage(self, minutes: int = 5) -> Optional[SystemResource]:
        """指定時間内の平均使用率を取得"""
        if not self.history:
            return None

        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_data = [r for r in self.history if r.timestamp > cutoff_time]

        if not recent_data:
            return None

        # 平均値を計算
        avg_resource = SystemResource(
            cpu_percent=sum(r.cpu_percent for r in recent_data) / len(recent_data),
            cpu_cores=recent_data[0].cpu_cores,
            memory_percent=sum(r.memory_percent for r in recent_data)
            / len(recent_data),
            memory_available_gb=sum(r.memory_available_gb for r in recent_data)
            / len(recent_data),
            disk_io_read_mb=sum(r.disk_io_read_mb for r in recent_data)
            / len(recent_data),
            disk_io_write_mb=sum(r.disk_io_write_mb for r in recent_data)
            / len(recent_data),
            network_io_send_mb=sum(r.network_io_send_mb for r in recent_data)
            / len(recent_data),
            network_io_recv_mb=sum(r.network_io_recv_mb for r in recent_data)
            / len(recent_data),
            timestamp=datetime.now(),
        )

        return avg_resource


class ResourceOptimizationEngine:
    """リソース最適化エンジン"""

    def __init__(self, task_sage, tracking_db: UnifiedTrackingDB):
        """初期化メソッド"""
        self.task_sage = task_sage
        self.tracking_db = tracking_db
        self.resource_monitor = SystemResourceMonitor()
        self.resource_predictions = {}
        self.optimization_history = []

        # リソース制限設定
        self.resource_limits = {
            "cpu_percent": 80.0,  # CPU使用率上限
            "memory_percent": 85.0,  # メモリ使用率上限
            "concurrent_tasks": 10,  # 同時実行タスク数上限
            "io_threshold_mb": 100.0,  # I/O閾値 MB/s
        }

        logger.info("🔧 ResourceOptimizationEngine initialized")

    async def optimize_resource_allocation(
        self, tasks: List[TaskEntry]
    ) -> Dict[str, Any]:
        """リソース配分を最適化"""
        try:
            # 現在のリソース使用状況
            current_resources = await self.resource_monitor.get_current_usage()

            # タスク別の予想リソース消費
            task_resources = await self._predict_resource_usage(tasks)

            # 最適化アルゴリズム実行
            optimization_result = await self._run_optimization(
                tasks=tasks,
                available_resources=current_resources,
                task_requirements=task_resources,
            )

            # 最適化履歴を記録
            self.optimization_history.append(
                {
                    "timestamp": datetime.now(),
                    "task_count": len(tasks),
                    "result": optimization_result,
                }
            )

            logger.info(
                f"Resource optimization completed: {optimization_result['summary']}"
            )

            return optimization_result

        except Exception as e:
            logger.error(f"Failed to optimize resource allocation: {e}")
            return {"success": False, "error": str(e), "optimized_schedule": tasks}

    async def _predict_resource_usage(
        self, tasks: List[TaskEntry]
    ) -> Dict[str, TaskResourceUsage]:
        """タスクのリソース使用量を予測"""
        predictions = {}

        for task in tasks:
            # タスクタイプ別のデフォルト使用量
            default_usage = self._get_default_resource_usage(task)

            # 履歴データから調整
            historical_usage = await self._get_historical_resource_usage(task)

            # リソース要求から調整
            resource_multiplier = 1.0
            for resource in task.resources:
                if resource.resource_type == "cpu":
                    resource_multiplier *= resource.allocation_percentage / 100.0

            # 予測値を計算
            predicted_usage = TaskResourceUsage(
                task_id=task.id,
                cpu_usage=default_usage["cpu"] * resource_multiplier,
                memory_usage=default_usage["memory"] * resource_multiplier,
                disk_io=default_usage["disk_io"],
                network_io=default_usage["network_io"],
                estimated_duration=default_usage["duration"],
            )

            # 履歴データで調整
            if historical_usage:
                predicted_usage.cpu_usage = (
                    predicted_usage.cpu_usage * 0.3 + historical_usage["cpu"] * 0.7
                )
                predicted_usage.memory_usage = (
                    predicted_usage.memory_usage * 0.3
                    + historical_usage["memory"] * 0.7
                )

            predictions[task.id] = predicted_usage

        return predictions

    def _get_default_resource_usage(self, task: TaskEntry) -> Dict[str, float]:
        """タスクタイプ別のデフォルトリソース使用量"""
        task_type_resources = {
            "development": {
                "cpu": 30.0,
                "memory": 500.0,
                "disk_io": 10.0,
                "network_io": 5.0,
                "duration": 1800,
            },
            "maintenance": {
                "cpu": 20.0,
                "memory": 300.0,
                "disk_io": 5.0,
                "network_io": 2.0,
                "duration": 900,
            },
            "investigation": {
                "cpu": 15.0,
                "memory": 200.0,
                "disk_io": 2.0,
                "network_io": 10.0,
                "duration": 600,
            },
            "integration": {
                "cpu": 40.0,
                "memory": 800.0,
                "disk_io": 20.0,
                "network_io": 15.0,
                "duration": 2400,
            },
            "optimization": {
                "cpu": 50.0,
                "memory": 1000.0,
                "disk_io": 15.0,
                "network_io": 5.0,
                "duration": 3600,
            },
        }

        return task_type_resources.get(
            task.task_type.value,
            {
                "cpu": 25.0,
                "memory": 400.0,
                "disk_io": 5.0,
                "network_io": 5.0,
                "duration": 1200,
            },
        )

    async def _get_historical_resource_usage(
        self, task: TaskEntry
    ) -> Optional[Dict[str, float]]:
        """履歴データからリソース使用量を取得"""
        try:
            # タスクタイプ別の履歴を検索
            similar_tasks = self.tracking_db.search_tasks(limit=50)

            usage_data = []
            for task_data in similar_tasks:
                metadata = json.loads(task_data.get("metadata", "{}"))
                if metadata.get("task_type") == task.task_type.value:
                    # リソース使用量データを抽出（仮想的なデータ）
                    usage_data.append(
                        {
                            "cpu": metadata.get("cpu_usage", 25.0),
                            "memory": metadata.get("memory_usage", 400.0),
                        }
                    )

            if usage_data:
                return {
                    "cpu": sum(d["cpu"] for d in usage_data) / len(usage_data),
                    "memory": sum(d["memory"] for d in usage_data) / len(usage_data),
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get historical resource usage: {e}")
            return None

    async def _run_optimization(
        self,
        tasks: List[TaskEntry],
        available_resources: SystemResource,
        task_requirements: Dict[str, TaskResourceUsage],
    ) -> Dict[str, Any]:
        """最適化アルゴリズムを実行"""
        # 利用可能リソースを計算
        available_cpu = (
            self.resource_limits["cpu_percent"] - available_resources.cpu_percent
        )
        available_memory = (
            self.resource_limits["memory_percent"] - available_resources.memory_percent
        )

        # タスクを優先度順にソート
        sorted_tasks = sorted(
            tasks,
            key=lambda t: self.task_sage.scheduler.calculate_task_score(t),
            reverse=True,
        )

        # スケジュール結果
        scheduled_tasks = []
        parallel_groups = []
        current_group = []
        current_cpu = 0.0
        current_memory = 0.0

        for task in sorted_tasks:
            req = task_requirements.get(task.id)
            if not req:
                continue

            # リソースが収まるかチェック
            if (
                current_cpu + req.cpu_usage <= available_cpu
                and current_memory + req.memory_usage / 1024 <= available_memory
            ):
                # 現在のグループに追加
                current_group.append(task)
                current_cpu += req.cpu_usage
                current_memory += req.memory_usage / 1024
            else:
                # 新しいグループを開始
                if current_group:
                    parallel_groups.append(current_group)
                current_group = [task]
                current_cpu = req.cpu_usage
                current_memory = req.memory_usage / 1024

        # 最後のグループを追加
        if current_group:
            parallel_groups.append(current_group)

        # 最適化結果を構築
        optimization_result = {
            "success": True,
            "optimized_schedule": [task for group in parallel_groups for task in group],
            "parallel_groups": [[t.id for t in group] for group in parallel_groups],
            "resource_utilization": {
                "cpu": min(100, available_resources.cpu_percent + current_cpu),
                "memory": min(100, available_resources.memory_percent + current_memory),
            },
            "estimated_completion_time": self._estimate_total_time(
                parallel_groups, task_requirements
            ),
            "recommendations": self._generate_recommendations(
                tasks, available_resources, task_requirements, parallel_groups
            ),
            "summary": f"Scheduled {len(tasks)} tasks in {len(parallel_groups)} parallel groups",
        }

        return optimization_result

    def _estimate_total_time(
        self,
        parallel_groups: List[List[TaskEntry]],
        task_requirements: Dict[str, TaskResourceUsage],
    ) -> float:
        """全体の完了時間を推定"""
        total_time = 0.0

        for group in parallel_groups:
            # グループ内の最大実行時間
            group_time = 0.0
            for task in group:
                req = task_requirements.get(task.id)
                if req:
                    group_time = max(group_time, req.estimated_duration)
            total_time += group_time

        return total_time

    def _generate_recommendations(
        self,
        tasks: List[TaskEntry],
        available_resources: SystemResource,
        task_requirements: Dict[str, TaskResourceUsage],
        parallel_groups: List[List[TaskEntry]],
    ) -> List[str]:
        """最適化の推奨事項を生成"""
        recommendations = []

        # CPU使用率が高い場合
        if available_resources.cpu_percent > 70:
            recommendations.append(
                "High CPU usage detected. Consider deferring low-priority tasks."
            )

        # メモリ使用率が高い場合
        if available_resources.memory_percent > 80:
            recommendations.append(
                "High memory usage. Optimize memory-intensive tasks."
            )

        # 並列度が低い場合
        if len(parallel_groups) > len(tasks) / 2:
            recommendations.append(
                "Low parallelization. Consider breaking down large tasks."
            )

        # I/O負荷が高い場合
        if (
            available_resources.disk_io_read_mb + available_resources.disk_io_write_mb
        ) > 50:
            recommendations.append(
                "High I/O load. Schedule I/O-intensive tasks separately."
            )

        return recommendations

    async def monitor_resource_usage(self, task_id: str) -> Dict[str, Any]:
        """実行中タスクのリソース使用量を監視"""
        try:
            # 開始時のリソース状態
            start_resources = await self.resource_monitor.get_current_usage()

            # 監視結果を初期化
            monitoring_result = {
                "task_id": task_id,
                "start_time": datetime.now(),
                "samples": [],
                "peak_cpu": 0.0,
                "peak_memory": 0.0,
                "avg_cpu": 0.0,
                "avg_memory": 0.0,
            }

            # 定期的にサンプリング（簡易版）
            for i in range(5):  # 5秒間監視
                await asyncio.sleep(1)
                current = await self.resource_monitor.get_current_usage()

                sample = {
                    "timestamp": current.timestamp,
                    "cpu_delta": current.cpu_percent - start_resources.cpu_percent,
                    "memory_delta": current.memory_percent
                    - start_resources.memory_percent,
                }

                monitoring_result["samples"].append(sample)
                monitoring_result["peak_cpu"] = max(
                    monitoring_result["peak_cpu"], sample["cpu_delta"]
                )
                monitoring_result["peak_memory"] = max(
                    monitoring_result["peak_memory"], sample["memory_delta"]
                )

            # 平均値を計算
            if monitoring_result["samples"]:
                monitoring_result["avg_cpu"] = sum(
                    s["cpu_delta"] for s in monitoring_result["samples"]
                ) / len(monitoring_result["samples"])
                monitoring_result["avg_memory"] = sum(
                    s["memory_delta"] for s in monitoring_result["samples"]
                ) / len(monitoring_result["samples"])

            return monitoring_result

        except Exception as e:
            logger.error(f"Failed to monitor resource usage: {e}")
            return {"task_id": task_id, "error": str(e)}

    def get_resource_efficiency_score(self) -> float:
        """リソース効率スコアを計算"""
        try:
            # 直近の平均使用率を取得
            avg_usage = self.resource_monitor.get_average_usage(minutes=10)
            if not avg_usage:
                return 0.5

            # 効率スコアを計算（0-1）
            cpu_efficiency = min(
                1.0, avg_usage.cpu_percent / self.resource_limits["cpu_percent"]
            )
            memory_efficiency = min(
                1.0, avg_usage.memory_percent / self.resource_limits["memory_percent"]
            )

            # I/O効率
            io_total = avg_usage.disk_io_read_mb + avg_usage.disk_io_write_mb
            io_efficiency = 1.0 - min(
                1.0, io_total / self.resource_limits["io_threshold_mb"]
            )

            # 総合スコア
            efficiency_score = (
                cpu_efficiency * 0.4 + memory_efficiency * 0.4 + io_efficiency * 0.2
            )

            return efficiency_score

        except Exception as e:
            logger.error(f"Failed to calculate efficiency score: {e}")
            return 0.5
