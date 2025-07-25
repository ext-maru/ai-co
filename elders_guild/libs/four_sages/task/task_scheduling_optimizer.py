#!/usr/bin/env python3
"""
タスクスケジューリング最適化エンジン - Task Sage統合コンポーネント
Created: 2025-07-17
Author: Claude Elder
"""

import asyncio
import heapq
import logging

# プロジェクトルートインポート
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.lightweight_logger import get_logger
from libs.four_sages.task.dynamic_priority_engine import DynamicPriorityEngine
from libs.four_sages.task.execution_time_predictor import ExecutionTimePredictor
from libs.four_sages.task.task_sage import (
    TaskDependency,
    TaskEntry,
    TaskPriority,
    TaskStatus,
)

logger = get_logger("task_scheduling_optimizer")


@dataclass
class ScheduledTask:
    """スケジュール済みタスク"""

    task: TaskEntry
    dynamic_priority: float
    predicted_time: float
    scheduled_start: datetime
    scheduled_end: datetime
    parallel_group: int
    dependencies_met: bool


@dataclass
class SchedulingConstraint:
    """スケジューリング制約"""

    max_parallel_tasks: int = 10
    max_daily_hours: float = 8.0
    working_hours_start: int = 9  # 9:00
    working_hours_end: int = 18  # 18:00
    respect_due_dates: bool = True
    allow_overtime: bool = False
    buffer_time_percent: float = 0.2  # 20%バッファ


class TaskSchedulingOptimizer:
    """タスクスケジューリング最適化エンジン"""

    def __init__(
        self,
        task_sage,
        priority_engine: DynamicPriorityEngine,
        time_predictor: ExecutionTimePredictor,
    ):
        self.task_sage = task_sage
        self.priority_engine = priority_engine
        self.time_predictor = time_predictor
        self.constraints = SchedulingConstraint()
        self.schedule_cache = {}
        self.optimization_history = []

        logger.info("📅 TaskSchedulingOptimizer initialized")

    async def optimize_schedule(
        self, tasks: List[TaskEntry], constraints: Optional[SchedulingConstraint] = None
    ) -> List[ScheduledTask]:
        """最適なスケジュールを生成"""
        try:
            if constraints:
                self.constraints = constraints

            # キャッシュチェック
            cache_key = self._generate_cache_key(tasks)
            if cache_key in self.schedule_cache:
                cached_schedule = self.schedule_cache[cache_key]
                if datetime.now() - cached_schedule["timestamp"] < timedelta(
                    minutes=15
                ):
                    return cached_schedule["schedule"]

            # 動的優先度計算
            logger.info(f"Calculating dynamic priorities for {len(tasks)} tasks")
            for task in tasks:
                task.dynamic_priority = (
                    await self.priority_engine.calculate_dynamic_priority(task)
                )

            # 実行時間予測
            logger.info("Predicting execution times")
            for task in tasks:
                (
                    predicted_time,
                    confidence,
                ) = await self.time_predictor.predict_execution_time(task)
                task.predicted_time = predicted_time * (
                    1 + self.constraints.buffer_time_percent
                )

            # 最適スケジュール生成
            logger.info("Generating optimal schedule")
            optimized_schedule = await self._generate_optimal_schedule(
                tasks=tasks, constraints=self.constraints
            )

            # キャッシュに保存
            self.schedule_cache[cache_key] = {
                "schedule": optimized_schedule,
                "timestamp": datetime.now(),
            }

            # 最適化履歴を記録
            self._record_optimization_history(tasks, optimized_schedule)

            logger.info(
                f"Schedule optimization completed: {len(optimized_schedule)} tasks scheduled"
            )

            return optimized_schedule

        except Exception as e:
            logger.error(f"Failed to optimize schedule: {e}")
            # エラー時は単純な優先度順スケジュール
            return self._create_fallback_schedule(tasks)

    def _generate_cache_key(self, tasks: List[TaskEntry]) -> str:
        """キャッシュキーを生成"""
        task_ids = sorted([t.id for t in tasks])
        return f"schedule_{'-'.join(task_ids[:10])}_{len(tasks)}"

    async def _generate_optimal_schedule(
        self, tasks: List[TaskEntry], constraints: SchedulingConstraint
    ) -> List[ScheduledTask]:
        """最適スケジュールを生成"""
        # 依存関係グラフを構築
        dependency_graph = self._build_dependency_graph(tasks)

        # トポロジカルソートで依存関係を考慮した順序を取得
        topological_order = self._topological_sort_with_priority(
            tasks, dependency_graph
        )

        # スケジュール生成
        scheduled_tasks = []
        current_time = self._get_next_working_time(datetime.now())
        parallel_slots = [None] * constraints.max_parallel_tasks
        parallel_slot_end_times = [current_time] * constraints.max_parallel_tasks

        for task in topological_order:
            # 依存関係チェック
            dependencies_met = self._check_dependencies_met(
                task, scheduled_tasks, dependency_graph
            )

            # 最も早く空くスロットを見つける
            earliest_slot = 0
            earliest_time = parallel_slot_end_times[0]
            for i in range(1, len(parallel_slot_end_times)):
                if parallel_slot_end_times[i] < earliest_time:
                    earliest_slot = i
                    earliest_time = parallel_slot_end_times[i]

            # 依存関係のあるタスクの完了時刻を考慮
            dependency_end_time = self._get_dependency_end_time(
                task, scheduled_tasks, dependency_graph
            )
            start_time = max(earliest_time, dependency_end_time)

            # 勤務時間を考慮
            start_time = self._adjust_for_working_hours(start_time, constraints)

            # 期限を考慮
            if constraints.respect_due_dates and task.due_date:
                if start_time + timedelta(seconds=task.predicted_time) > task.due_date:
                    # 期限に間に合うように調整
                    if constraints.allow_overtime:
                        # 残業を許可
                        pass
                    else:
                        # より早いスロットを探す
                        start_time = self._find_earlier_slot(
                            task, scheduled_tasks, parallel_slot_end_times, constraints
                        )

            # タスクをスケジュール
            end_time = start_time + timedelta(seconds=task.predicted_time)

            scheduled_task = ScheduledTask(
                task=task,
                dynamic_priority=task.dynamic_priority,
                predicted_time=task.predicted_time,
                scheduled_start=start_time,
                scheduled_end=end_time,
                parallel_group=earliest_slot,
                dependencies_met=dependencies_met,
            )

            scheduled_tasks.append(scheduled_task)
            parallel_slot_end_times[earliest_slot] = end_time

        return scheduled_tasks

    def _build_dependency_graph(self, tasks: List[TaskEntry]) -> Dict[str, Set[str]]:
        """依存関係グラフを構築"""
        task_dict = {task.id: task for task in tasks}
        dependency_graph = defaultdict(set)

        for task in tasks:
            for dep in task.dependencies:
                if dep.task_id in task_dict:
        # 繰り返し処理
                    dependency_graph[task.id].add(dep.task_id)

        return dependency_graph

    def _topological_sort_with_priority(
        self, tasks: List[TaskEntry], dependency_graph: Dict[str, Set[str]]
    ) -> List[TaskEntry]:
        """優先度を考慮したトポロジカルソート"""
        # 入次数を計算
        in_degree = defaultdict(int)
        for task in tasks:
            in_degree[task.id] = 0

        for task_id, deps in dependency_graph.items():
            for dep_id in deps:
        # 繰り返し処理
                in_degree[dep_id] += 1

        # 優先度キューを使用（優先度が高い順）
        available_tasks = []
        for task in tasks:
            if in_degree[task.id] == 0:
                heapq.heappush(available_tasks, (-task.dynamic_priority, task))

        sorted_tasks = []
        task_dict = {task.id: task for task in tasks}

        while available_tasks:
        # ループ処理
            _, task = heapq.heappop(available_tasks)
            sorted_tasks.append(task)

            # このタスクに依存するタスクの入次数を減らす
            for other_task_id, deps in dependency_graph.items():
                if task.id in deps:
                    in_degree[other_task_id] -= 1
                    if in_degree[other_task_id] == 0:
                        other_task = task_dict[other_task_id]
                        heapq.heappush(
                            available_tasks, (-other_task.dynamic_priority, other_task)
                        )

        # 循環依存がある場合の処理（残りのタスクを優先度順に追加）
        remaining_tasks = [t for t in tasks if t not in sorted_tasks]
        remaining_tasks.sort(key=lambda t: t.dynamic_priority, reverse=True)
        sorted_tasks.extend(remaining_tasks)

        return sorted_tasks

    def _check_dependencies_met(
        self,
        task: TaskEntry,
        scheduled_tasks: List[ScheduledTask],
        dependency_graph: Dict[str, Set[str]],
    ) -> bool:
        """依存関係が満たされているかチェック"""
        scheduled_ids = {st.task.id for st in scheduled_tasks}
        dependencies = dependency_graph.get(task.id, set())

        return all(dep_id in scheduled_ids for dep_id in dependencies)

    def _get_dependency_end_time(
        self,
        task: TaskEntry,
        scheduled_tasks: List[ScheduledTask],
        dependency_graph: Dict[str, Set[str]],
    ) -> datetime:
        """依存タスクの最大終了時刻を取得"""
        dependencies = dependency_graph.get(task.id, set())
        if not dependencies:
            return datetime.now()

        max_end_time = datetime.now()
        for scheduled_task in scheduled_tasks:
            if scheduled_task.task.id in dependencies:
                max_end_time = max(max_end_time, scheduled_task.scheduled_end)

        return max_end_time

    def _get_next_working_time(self, time: datetime) -> datetime:
        """次の勤務時間を取得"""
        if time.hour < self.constraints.working_hours_start:
            return time.replace(
                hour=self.constraints.working_hours_start, minute=0, second=0
            )
        elif time.hour >= self.constraints.working_hours_end:
            # 翌日の勤務開始時間
            next_day = time + timedelta(days=1)
            return next_day.replace(
                hour=self.constraints.working_hours_start, minute=0, second=0
            )
        else:
            return time

    def _adjust_for_working_hours(
        self, time: datetime, constraints: SchedulingConstraint
    ) -> datetime:
        """勤務時間に合わせて調整"""
        # 週末をスキップ
        while time.weekday() >= 5:  # 土日
            time += timedelta(days=1)

        # 勤務時間外の調整
        if time.hour < constraints.working_hours_start:
            time = time.replace(
                hour=constraints.working_hours_start, minute=0, second=0
            )
        elif time.hour >= constraints.working_hours_end:
            if constraints.allow_overtime:
                # 残業を許可
                pass
            else:
                # 翌日に持ち越し
                time = self._get_next_working_time(time)

        return time

    def _find_earlier_slot(
        self,
        task: TaskEntry,
        scheduled_tasks: List[ScheduledTask],
        parallel_slot_end_times: List[datetime],
        constraints: SchedulingConstraint,
    ) -> datetime:
        """期限に間に合う早いスロットを探す"""
        if not task.due_date:
            return parallel_slot_end_times[0]

        # 期限から逆算して開始時刻を決定
        latest_start = task.due_date - timedelta(seconds=task.predicted_time)

        # 依存関係の終了時刻
        dependency_end = self._get_dependency_end_time(
            task,
            scheduled_tasks,
            self._build_dependency_graph([st.task for st in scheduled_tasks]),
        )

        # より早い時刻を選択
        return max(dependency_end, min(latest_start, parallel_slot_end_times[0]))

    def _create_fallback_schedule(self, tasks: List[TaskEntry]) -> List[ScheduledTask]:
        """フォールバックスケジュールを作成"""
        scheduled_tasks = []
        current_time = self._get_next_working_time(datetime.now())

        # 優先度順にソート
        sorted_tasks = sorted(
            tasks, key=lambda t: getattr(t, "dynamic_priority", 1.0), reverse=True
        )

        for i, task in enumerate(sorted_tasks):
            start_time = current_time
            predicted_time = getattr(task, "predicted_time", 3600.0)  # デフォルト1時間
            end_time = start_time + timedelta(seconds=predicted_time)

            scheduled_task = ScheduledTask(
                task=task,
                dynamic_priority=getattr(task, "dynamic_priority", 1.0),
                predicted_time=predicted_time,
                scheduled_start=start_time,
                scheduled_end=end_time,
                parallel_group=i % self.constraints.max_parallel_tasks,
                dependencies_met=True,
            )

            scheduled_tasks.append(scheduled_task)

            # 並列実行を考慮
            if (i + 1) % self.constraints.max_parallel_tasks == 0:
                current_time = end_time

        return scheduled_tasks

    def _record_optimization_history(
        self, tasks: List[TaskEntry], schedule: List[ScheduledTask]
    ):
        """最適化履歴を記録"""
        history_entry = {
            "timestamp": datetime.now(),
            "task_count": len(tasks),
            "scheduled_count": len(schedule),
            "total_duration": self._calculate_total_duration(schedule),
            "parallelization_factor": self._calculate_parallelization_factor(schedule),
            "deadline_compliance": self._calculate_deadline_compliance(schedule),
        }

        self.optimization_history.append(history_entry)

        # 最新100件のみ保持
        if len(self.optimization_history) > 100:
            self.optimization_history.pop(0)

    def _calculate_total_duration(self, schedule: List[ScheduledTask]) -> float:
        """スケジュール全体の所要時間を計算"""
        if not schedule:
            return 0.0

        min_start = min(st.scheduled_start for st in schedule)
        max_end = max(st.scheduled_end for st in schedule)

        return (max_end - min_start).total_seconds()

    def _calculate_parallelization_factor(self, schedule: List[ScheduledTask]) -> float:
        """並列化係数を計算"""
        if not schedule:
            return 0.0

        # 各時間帯の並列タスク数を計算
        time_slots = defaultdict(int)

        # 繰り返し処理
        for st in schedule:
            current = st.scheduled_start
            while current < st.scheduled_end:
                time_slots[current] += 1
                current += timedelta(minutes=15)  # 15分単位

        if not time_slots:
            return 1.0

        avg_parallel = sum(time_slots.values()) / len(time_slots)
        return avg_parallel

    def _calculate_deadline_compliance(self, schedule: List[ScheduledTask]) -> float:
        """期限遵守率を計算"""
        tasks_with_deadline = [st for st in schedule if st.task.due_date]
        if not tasks_with_deadline:
            return 1.0

        compliant_tasks = [
            st for st in tasks_with_deadline if st.scheduled_end <= st.task.due_date
        ]

        return len(compliant_tasks) / len(tasks_with_deadline)

    async def get_schedule_metrics(self) -> Dict[str, Any]:
        """スケジューリングメトリクスを取得"""
        if not self.optimization_history:
            return {"status": "no_data", "message": "No optimization history available"}

        recent_history = self.optimization_history[-10:]  # 最新10件

        metrics = {
            "avg_total_duration": sum(h["total_duration"] for h in recent_history)
            / len(recent_history),
            "avg_parallelization": sum(
                h["parallelization_factor"] for h in recent_history
            )
            / len(recent_history),
            "avg_deadline_compliance": sum(
                h["deadline_compliance"] for h in recent_history
            )
            / len(recent_history),
            "total_optimizations": len(self.optimization_history),
            "cache_hit_rate": len(self.schedule_cache)
            / max(1, len(self.optimization_history)),
        }

        return metrics

    def update_constraints(self, **kwargs):
        """制約条件を更新"""
        for key, value in kwargs.items():
            if hasattr(self.constraints, key):
                setattr(self.constraints, key, value)
                logger.info(f"Updated constraint {key} to {value}")

    def get_gantt_chart_data(
        self, schedule: List[ScheduledTask]
    ) -> List[Dict[str, Any]]:
        """ガントチャート用のデータを生成"""
        gantt_data = []

        for st in schedule:
            gantt_data.append(
                {
                    "task_id": st.task.id,
                    "task_name": st.task.title,
                    "start": st.scheduled_start.isoformat(),
                    "end": st.scheduled_end.isoformat(),
                    "priority": st.task.priority.value,
                    "dynamic_priority": st.dynamic_priority,
                    "parallel_group": st.parallel_group,
                    "dependencies": [dep.task_id for dep in st.task.dependencies],
                    "color": self._get_priority_color(st.task.priority),
                }
            )

        return gantt_data

    def _get_priority_color(self, priority: TaskPriority) -> str:
        """優先度に応じた色を取得"""
        color_map = {
            TaskPriority.CRITICAL: "#FF0000",  # 赤
            TaskPriority.HIGH: "#FF8C00",  # オレンジ
            TaskPriority.MEDIUM: "#FFD700",  # 黄
            TaskPriority.LOW: "#90EE90",  # 薄緑
            TaskPriority.DEFERRED: "#D3D3D3",  # グレー
        }
        return color_map.get(priority, "#4169E1")  # デフォルト青
