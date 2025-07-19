#!/usr/bin/env python3
"""
並列実行管理システム - 独立したタスクの並列実行と効率的なリソース管理

IntelligentTaskSplitterで分割された独立タスクを効率的に並列実行し、
リソースの最適化とタスクの優先度管理を行う
"""

import json
import logging
import sqlite3

# プロジェクトルートをPythonパスに追加
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pika

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager
from libs.intelligent_task_splitter import (
    IntelligentTaskSplitter,
    SubTask,
    TaskComplexity,
)

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """実行状態"""

    PENDING = "pending"  # 待機中
    RUNNING = "running"  # 実行中
    COMPLETED = "completed"  # 完了
    FAILED = "failed"  # 失敗
    CANCELLED = "cancelled"  # キャンセル
    TIMEOUT = "timeout"  # タイムアウト
    DEPENDENCY_BLOCKED = "dependency_blocked"  # 依存関係でブロック


class ResourceType(Enum):
    """リソースタイプ"""

    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    DISK = "disk"
    WORKER = "worker"


@dataclass
class ExecutionGroup:
    """並列実行グループ"""

    group_id: str
    project_id: str
    phase: str
    tasks: List[SubTask]
    max_parallel: int
    priority: int
    estimated_duration: float
    resource_requirements: Dict[ResourceType, float]
    created_at: datetime


@dataclass
class ExecutionResult:
    """実行結果"""

    task_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration: float
    output: str
    error: Optional[str]
    resource_usage: Dict[ResourceType, float]
    worker_id: Optional[str]


class ParallelExecutionManager(BaseManager):
    """並列実行管理システム"""

    def __init__(self, max_workers: int = 4):
        super().__init__("ParallelExecutionManager")
        self.db_path = PROJECT_ROOT / "db" / "parallel_execution.db"
        self.max_workers = max_workers
        self.task_splitter = IntelligentTaskSplitter()

        # ThreadPoolExecutor for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # RabbitMQ接続
        self.connection = None
        self.channel = None

        # 実行状態管理
        self.running_tasks: Dict[str, threading.Thread] = {}
        self.execution_groups: Dict[str, ExecutionGroup] = {}
        self.resource_usage: Dict[ResourceType, float] = {
            ResourceType.CPU: 0.0,
            ResourceType.MEMORY: 0.0,
            ResourceType.NETWORK: 0.0,
            ResourceType.DISK: 0.0,
            ResourceType.WORKER: 0.0,
        }

        # リソース制限設定
        self.resource_limits = {
            ResourceType.CPU: 80.0,  # CPU使用率80%まで
            ResourceType.MEMORY: 70.0,  # メモリ使用率70%まで
            ResourceType.NETWORK: 60.0,  # ネットワーク使用率60%まで
            ResourceType.DISK: 50.0,  # ディスク使用率50%まで
            ResourceType.WORKER: 100.0,  # ワーカー100%まで
        }

        # 実行統計
        self.execution_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "parallel_groups": 0,
            "avg_execution_time": 0.0,
            "resource_efficiency": 0.0,
        }

        self.initialize()

    def initialize(self) -> bool:
        """初期化処理"""
        try:
            self._init_database()
            self._connect_rabbitmq()
            return True
        except Exception as e:
            self.handle_error(e, "初期化")
            return False

    def _init_database(self):
        """データベース初期化"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # 実行グループテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_groups (
                    group_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    task_count INTEGER NOT NULL,
                    max_parallel INTEGER NOT NULL,
                    priority INTEGER DEFAULT 0,
                    estimated_duration REAL,
                    resource_requirements TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """
            )

            # 並列実行履歴テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_history (
                    execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    worker_id TEXT,
                    status TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration REAL,
                    output TEXT,
                    error TEXT,
                    resource_usage TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES execution_groups(group_id)
                )
            """
            )

            # リソース使用状況テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS resource_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_type TEXT NOT NULL,
                    usage_percentage REAL NOT NULL,
                    limit_percentage REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 実行統計テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_statistics (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_tasks INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    parallel_groups INTEGER DEFAULT 0,
                    avg_execution_time REAL DEFAULT 0.0,
                    resource_efficiency REAL DEFAULT 0.0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # インデックス作成
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_execution_groups_project ON execution_groups(project_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_execution_history_task ON execution_history(task_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_resource_usage_type ON resource_usage(resource_type)"
            )

    def _connect_rabbitmq(self):
        """RabbitMQ接続"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters("localhost")
            )
            self.channel = self.connection.channel()

            # キュー宣言
            self.channel.queue_declare(
                queue="ai_tasks", durable=True, arguments={"x-max-priority": 10}
            )
            self.channel.queue_declare(
                queue="parallel_tasks", durable=True, arguments={"x-max-priority": 10}
            )

            logger.info("✅ RabbitMQ接続成功")
        except Exception as e:
            logger.warning(f"RabbitMQ接続失敗: {e}")
            self.connection = None
            self.channel = None

    def create_execution_group(
        self,
        project_id: str,
        phase: str,
        tasks: List[SubTask],
        max_parallel: int = None,
    ) -> str:
        """実行グループ作成"""
        try:
            group_id = (
                f"group_{project_id}_{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # 並列実行可能数を決定
            if max_parallel is None:
                parallel_tasks = [t for t in tasks if t.can_parallel]
                max_parallel = min(len(parallel_tasks), self.max_workers)

            # リソース要件を計算
            resource_requirements = self._calculate_resource_requirements(tasks)

            # 実行時間を推定
            estimated_duration = self._estimate_execution_time(tasks, max_parallel)

            # 実行グループを作成
            execution_group = ExecutionGroup(
                group_id=group_id,
                project_id=project_id,
                phase=phase,
                tasks=tasks,
                max_parallel=max_parallel,
                priority=max([t.priority for t in tasks]),
                estimated_duration=estimated_duration,
                resource_requirements=resource_requirements,
                created_at=datetime.now(),
            )

            # データベースに保存
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO execution_groups
                    (group_id, project_id, phase, task_count, max_parallel, priority,
                     estimated_duration, resource_requirements, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        group_id,
                        project_id,
                        phase,
                        len(tasks),
                        max_parallel,
                        execution_group.priority,
                        estimated_duration,
                        json.dumps(
                            {k.value: v for k, v in resource_requirements.items()}
                        ),
                        ExecutionStatus.PENDING.value,
                    ),
                )

            self.execution_groups[group_id] = execution_group

            logger.info(f"📦 実行グループ作成: {group_id} ({len(tasks)}タスク, 並列度{max_parallel})")
            return group_id

        except Exception as e:
            logger.error(f"実行グループ作成エラー: {e}")
            return ""

    def execute_group_parallel(self, group_id: str) -> bool:
        """グループの並列実行"""
        try:
            if group_id not in self.execution_groups:
                logger.error(f"実行グループが見つかりません: {group_id}")
                return False

            execution_group = self.execution_groups[group_id]

            # リソースチェック
            if not self._check_resource_availability(
                execution_group.resource_requirements
            ):
                logger.warning(f"リソース不足により実行延期: {group_id}")
                return False

            logger.info(f"🚀 並列実行開始: {group_id}")

            # 実行開始時刻を記録
            start_time = datetime.now()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE execution_groups
                    SET status = ?, started_at = ?
                    WHERE group_id = ?
                """,
                    (ExecutionStatus.RUNNING.value, start_time, group_id),
                )

            # タスクを依存関係に基づいて分離
            independent_tasks, dependent_tasks = self._separate_tasks_by_dependencies(
                execution_group.tasks
            )

            # 独立タスクを並列実行
            parallel_results = []
            if independent_tasks:
                parallel_results = self._execute_tasks_parallel(
                    independent_tasks, execution_group.max_parallel
                )

            # 依存関係のあるタスクを順次実行
            sequential_results = []
            if dependent_tasks:
                sequential_results = self._execute_tasks_sequential(dependent_tasks)

            # 全結果をまとめる
            all_results = parallel_results + sequential_results

            # 実行完了処理
            self._complete_group_execution(group_id, all_results, start_time)

            # 統計を更新
            self._update_execution_statistics(all_results)

            logger.info(f"✅ 並列実行完了: {group_id} ({len(all_results)}タスク)")
            return True

        except Exception as e:
            logger.error(f"並列実行エラー: {e}")
            return False

    def _separate_tasks_by_dependencies(
        self, tasks: List[SubTask]
    ) -> Tuple[List[SubTask], List[SubTask]]:
        """タスクを依存関係に基づいて分離"""
        independent_tasks = []
        dependent_tasks = []

        for task in tasks:
            if not task.dependencies or len(task.dependencies) == 0:
                independent_tasks.append(task)
            else:
                dependent_tasks.append(task)

        logger.info(f"📊 タスク分離: 独立{len(independent_tasks)}, 依存{len(dependent_tasks)}")
        return independent_tasks, dependent_tasks

    def _execute_tasks_parallel(
        self, tasks: List[SubTask], max_parallel: int
    ) -> List[ExecutionResult]:
        """並列タスク実行"""
        try:
            logger.info(f"🔄 並列実行開始: {len(tasks)}タスク (並列度{max_parallel})")

            # 優先度でソート
            tasks.sort(key=lambda t: t.priority, reverse=True)

            # 並列実行
            results = []
            future_to_task = {}

            with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                # タスクを投入
                for task in tasks:
                    future = executor.submit(self._execute_single_task, task)
                    future_to_task[future] = task

                # 結果を収集
                for future in as_completed(future_to_task, timeout=300):  # 5分タイムアウト
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"✅ 並列タスク完了: {task.id}")
                    except Exception as e:
                        logger.error(f"❌ 並列タスク失敗: {task.id} - {e}")
                        results.append(
                            ExecutionResult(
                                task_id=task.id,
                                status=ExecutionStatus.FAILED,
                                start_time=datetime.now(),
                                end_time=datetime.now(),
                                duration=0.0,
                                output="",
                                error=str(e),
                                resource_usage={},
                                worker_id=None,
                            )
                        )

            logger.info(f"🎯 並列実行完了: {len(results)}結果")
            return results

        except Exception as e:
            logger.error(f"並列実行エラー: {e}")
            return []

    def _execute_tasks_sequential(self, tasks: List[SubTask]) -> List[ExecutionResult]:
        """依存関係のあるタスクの順次実行"""
        try:
            logger.info(f"🔄 順次実行開始: {len(tasks)}タスク")

            # 依存関係を考慮して実行順序を決定
            ordered_tasks = self._order_tasks_by_dependencies(tasks)

            results = []
            for task in ordered_tasks:
                # 依存関係チェック
                if self._check_task_dependencies(task, results):
                    result = self._execute_single_task(task)
                    results.append(result)
                    logger.info(f"✅ 順次タスク完了: {task.id}")
                else:
                    logger.warning(f"⚠️ 依存関係未解決: {task.id}")
                    results.append(
                        ExecutionResult(
                            task_id=task.id,
                            status=ExecutionStatus.DEPENDENCY_BLOCKED,
                            start_time=datetime.now(),
                            end_time=datetime.now(),
                            duration=0.0,
                            output="",
                            error="依存関係未解決",
                            resource_usage={},
                            worker_id=None,
                        )
                    )

            logger.info(f"🎯 順次実行完了: {len(results)}結果")
            return results

        except Exception as e:
            logger.error(f"順次実行エラー: {e}")
            return []

    def _execute_single_task(self, task: SubTask) -> ExecutionResult:
        """単一タスクの実行"""
        start_time = datetime.now()

        try:
            logger.info(f"🔥 タスク実行開始: {task.id}")

            # リソース使用量を予測・記録
            predicted_resource_usage = self._predict_resource_usage(task)
            self._update_resource_usage(predicted_resource_usage, add=True)

            # タスクをワーカーキューに送信
            if self.channel:
                task_data = {
                    "task_id": task.id,
                    "task_type": "parallel_task",
                    "prompt": f"{task.title}\n\n{task.description}",
                    "complexity": task.complexity.value,
                    "estimated_hours": task.estimated_hours,
                    "required_skills": task.required_skills,
                    "priority": task.priority,
                    "can_parallel": task.can_parallel,
                    "dependencies": task.dependencies,
                    "created_at": datetime.now().isoformat(),
                }

                self.channel.basic_publish(
                    exchange="",
                    routing_key="parallel_tasks",
                    body=json.dumps(task_data, ensure_ascii=False),
                    properties=pika.BasicProperties(
                        delivery_mode=2, priority=min(task.priority + 3, 10)  # 永続化
                    ),
                )

                # 実行完了をシミュレート（実際は結果待ち）
                execution_time = self._simulate_execution_time(task)
                time.sleep(min(execution_time, 1.0))  # 最大1秒待機

                output = f"タスク実行完了: {task.title}"
                status = ExecutionStatus.COMPLETED
                error = None

            else:
                # RabbitMQ接続がない場合のシミュレーション
                execution_time = self._simulate_execution_time(task)
                time.sleep(min(execution_time, 0.5))  # 最大0.5秒待機

                output = f"[シミュレーション] タスク実行: {task.title}"
                status = ExecutionStatus.COMPLETED
                error = None

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # リソース使用量を解除
            self._update_resource_usage(predicted_resource_usage, add=False)

            result = ExecutionResult(
                task_id=task.id,
                status=status,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                output=output,
                error=error,
                resource_usage=predicted_resource_usage,
                worker_id=f"worker_{threading.current_thread().ident}",
            )

            # データベースに記録
            self._save_execution_result(result)

            logger.info(f"✅ タスク実行完了: {task.id} ({duration:.1f}秒)")
            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(f"❌ タスク実行失敗: {task.id} - {e}")

            return ExecutionResult(
                task_id=task.id,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                output="",
                error=str(e),
                resource_usage={},
                worker_id=None,
            )

    def _order_tasks_by_dependencies(self, tasks: List[SubTask]) -> List[SubTask]:
        """依存関係に基づいてタスクを並び替え"""
        ordered = []
        remaining = tasks.copy()

        while remaining:
            # 依存関係のないタスクを探す
            ready_tasks = []
            for task in remaining:
                if not task.dependencies or all(
                    dep in [t.id for t in ordered] for dep in task.dependencies
                ):
                    ready_tasks.append(task)

            if not ready_tasks:
                # 循環依存関係の可能性
                logger.warning("循環依存関係検出 - 残りタスクを強制追加")
                ready_tasks = remaining

            # 優先度でソート
            ready_tasks.sort(key=lambda t: t.priority, reverse=True)

            # 最初のタスクを追加
            task = ready_tasks[0]
            ordered.append(task)
            remaining.remove(task)

        return ordered

    def _check_task_dependencies(
        self, task: SubTask, completed_results: List[ExecutionResult]
    ) -> bool:
        """タスクの依存関係チェック"""
        if not task.dependencies:
            return True

        completed_task_ids = {
            result.task_id
            for result in completed_results
            if result.status == ExecutionStatus.COMPLETED
        }

        return all(dep_id in completed_task_ids for dep_id in task.dependencies)

    def _calculate_resource_requirements(
        self, tasks: List[SubTask]
    ) -> Dict[ResourceType, float]:
        """リソース要件計算"""
        requirements = {resource: 0.0 for resource in ResourceType}

        for task in tasks:
            # 複雑度に基づいてリソース要件を計算
            complexity_factor = {
                TaskComplexity.SIMPLE: 1.0,
                TaskComplexity.MODERATE: 2.0,
                TaskComplexity.COMPLEX: 4.0,
                TaskComplexity.VERY_COMPLEX: 8.0,
            }.get(task.complexity, 2.0)

            requirements[ResourceType.CPU] += complexity_factor * 10
            requirements[ResourceType.MEMORY] += complexity_factor * 5
            requirements[ResourceType.NETWORK] += complexity_factor * 2
            requirements[ResourceType.DISK] += complexity_factor * 1
            requirements[ResourceType.WORKER] += 1

        return requirements

    def _estimate_execution_time(
        self, tasks: List[SubTask], max_parallel: int
    ) -> float:
        """実行時間推定"""
        # 並列実行可能タスクと順次実行タスクを分離
        parallel_tasks = [t for t in tasks if t.can_parallel]
        sequential_tasks = [t for t in tasks if not t.can_parallel]

        # 並列実行時間 = 最長タスク時間 * (タスク数 / 並列度)
        parallel_time = 0.0
        if parallel_tasks:
            avg_parallel_time = sum(t.estimated_hours for t in parallel_tasks) / len(
                parallel_tasks
            )
            parallel_time = avg_parallel_time * (len(parallel_tasks) / max_parallel)

        # 順次実行時間 = 全タスク時間の合計
        sequential_time = sum(t.estimated_hours for t in sequential_tasks)

        return parallel_time + sequential_time

    def _check_resource_availability(
        self, requirements: Dict[ResourceType, float]
    ) -> bool:
        """リソース可用性チェック"""
        for resource_type, required in requirements.items():
            current_usage = self.resource_usage.get(resource_type, 0.0)
            limit = self.resource_limits.get(resource_type, 100.0)

            if current_usage + required > limit:
                logger.warning(
                    f"リソース不足: {resource_type.value} ({current_usage + required} > {limit})"
                )
                return False

        return True

    def _predict_resource_usage(self, task: SubTask) -> Dict[ResourceType, float]:
        """タスクのリソース使用量予測"""
        complexity_factor = {
            TaskComplexity.SIMPLE: 1.0,
            TaskComplexity.MODERATE: 2.0,
            TaskComplexity.COMPLEX: 4.0,
            TaskComplexity.VERY_COMPLEX: 8.0,
        }.get(task.complexity, 2.0)

        return {
            ResourceType.CPU: complexity_factor * 5,
            ResourceType.MEMORY: complexity_factor * 3,
            ResourceType.NETWORK: complexity_factor * 1,
            ResourceType.DISK: complexity_factor * 0.5,
            ResourceType.WORKER: 1,
        }

    def _update_resource_usage(
        self, usage: Dict[ResourceType, float], add: bool = True
    ):
        """リソース使用量更新"""
        factor = 1 if add else -1

        for resource_type, amount in usage.items():
            current = self.resource_usage.get(resource_type, 0.0)
            self.resource_usage[resource_type] = max(0.0, current + (amount * factor))

    def _simulate_execution_time(self, task: SubTask) -> float:
        """実行時間シミュレーション"""
        base_time = {
            TaskComplexity.SIMPLE: 0.1,
            TaskComplexity.MODERATE: 0.3,
            TaskComplexity.COMPLEX: 0.5,
            TaskComplexity.VERY_COMPLEX: 1.0,
        }.get(task.complexity, 0.3)

        return base_time * (1 + task.estimated_hours * 0.1)

    def _save_execution_result(self, result: ExecutionResult):
        """実行結果をデータベースに保存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO execution_history
                    (task_id, group_id, worker_id, status, start_time, end_time,
                     duration, output, error, resource_usage)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        result.task_id,
                        "current_group",  # 実際のgroup_idを使用
                        result.worker_id,
                        result.status.value,
                        result.start_time,
                        result.end_time,
                        result.duration,
                        result.output,
                        result.error,
                        json.dumps(
                            {k.value: v for k, v in result.resource_usage.items()}
                        ),
                    ),
                )
        except Exception as e:
            logger.error(f"実行結果保存エラー: {e}")

    def _complete_group_execution(
        self, group_id: str, results: List[ExecutionResult], start_time: datetime
    ):
        """グループ実行完了処理"""
        try:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 実行状態を決定
            failed_count = sum(1 for r in results if r.status == ExecutionStatus.FAILED)
            status = (
                ExecutionStatus.COMPLETED
                if failed_count == 0
                else ExecutionStatus.FAILED
            )

            # データベース更新
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE execution_groups
                    SET status = ?, completed_at = ?
                    WHERE group_id = ?
                """,
                    (status.value, end_time, group_id),
                )

            # 統計更新
            self.execution_stats["parallel_groups"] += 1

            logger.info(
                f"📊 グループ実行完了: {group_id} ({duration:.1f}秒, 成功{len(results)-failed_count}/{len(results)})"
            )

        except Exception as e:
            logger.error(f"グループ実行完了処理エラー: {e}")

    def _update_execution_statistics(self, results: List[ExecutionResult]):
        """実行統計更新"""
        try:
            completed_count = sum(
                1 for r in results if r.status == ExecutionStatus.COMPLETED
            )
            failed_count = sum(1 for r in results if r.status == ExecutionStatus.FAILED)
            avg_duration = (
                sum(r.duration for r in results) / len(results) if results else 0.0
            )

            # 統計更新
            self.execution_stats["total_tasks"] += len(results)
            self.execution_stats["completed_tasks"] += completed_count
            self.execution_stats["failed_tasks"] += failed_count
            self.execution_stats["avg_execution_time"] = avg_duration

            # データベースに保存
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO execution_statistics
                    (total_tasks, completed_tasks, failed_tasks, parallel_groups, avg_execution_time)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        self.execution_stats["total_tasks"],
                        self.execution_stats["completed_tasks"],
                        self.execution_stats["failed_tasks"],
                        self.execution_stats["parallel_groups"],
                        self.execution_stats["avg_execution_time"],
                    ),
                )

        except Exception as e:
            logger.error(f"統計更新エラー: {e}")

    def get_execution_status(self, group_id: str) -> Dict[str, Any]:
        """実行状態取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # グループ情報取得
                cursor = conn.execute(
                    """
                    SELECT project_id, phase, task_count, max_parallel, status,
                           started_at, completed_at, estimated_duration
                    FROM execution_groups WHERE group_id = ?
                """,
                    (group_id,),
                )

                row = cursor.fetchone()
                if not row:
                    return {"error": "グループが見つかりません"}

                group_info = {
                    "group_id": group_id,
                    "project_id": row[0],
                    "phase": row[1],
                    "task_count": row[2],
                    "max_parallel": row[3],
                    "status": row[4],
                    "started_at": row[5],
                    "completed_at": row[6],
                    "estimated_duration": row[7],
                }

                # 実行履歴取得
                cursor = conn.execute(
                    """
                    SELECT task_id, status, start_time, end_time, duration, error
                    FROM execution_history WHERE group_id = ?
                    ORDER BY start_time
                """,
                    (group_id,),
                )

                tasks = []
                for row in cursor:
                    tasks.append(
                        {
                            "task_id": row[0],
                            "status": row[1],
                            "start_time": row[2],
                            "end_time": row[3],
                            "duration": row[4],
                            "error": row[5],
                        }
                    )

                group_info["tasks"] = tasks
                return group_info

        except Exception as e:
            logger.error(f"実行状態取得エラー: {e}")
            return {"error": str(e)}

    def get_resource_usage(self) -> Dict[str, Any]:
        """現在のリソース使用状況取得"""
        return {
            "current_usage": {k.value: v for k, v in self.resource_usage.items()},
            "limits": {k.value: v for k, v in self.resource_limits.items()},
            "utilization": {
                k.value: (v / self.resource_limits[k] * 100)
                if self.resource_limits[k] > 0
                else 0
                for k, v in self.resource_usage.items()
            },
        }

    def get_execution_statistics(self) -> Dict[str, Any]:
        """実行統計取得"""
        return self.execution_stats.copy()

    def shutdown(self):
        """シャットダウン処理"""
        try:
            logger.info("🔄 ParallelExecutionManager シャットダウン開始")

            # ThreadPoolExecutorを停止
            if hasattr(self, "executor"):
                self.executor.shutdown(wait=True)

            # RabbitMQ接続を閉じる
            if self.connection and not self.connection.is_closed:
                self.connection.close()

            logger.info("✅ ParallelExecutionManager シャットダウン完了")

        except Exception as e:
            logger.error(f"シャットダウンエラー: {e}")


if __name__ == "__main__":
    # テスト実行
    manager = ParallelExecutionManager(max_workers=3)

    print("=" * 80)
    print("🚀 Parallel Execution Manager Test")
    print("=" * 80)

    # テストプロジェクト
    test_project_id = "test_project_002"
    test_phase = "development"

    # テストタスク作成
    from libs.intelligent_task_splitter import SubTask, TaskComplexity, TaskType

    test_tasks = [
        SubTask(
            id="task_001",
            parent_task_id="parent_001",
            title="API実装",
            description="REST API エンドポイントの実装",
            task_type=TaskType.IMPLEMENTATION,
            complexity=TaskComplexity.MODERATE,
            estimated_hours=4.0,
            dependencies=[],
            required_skills=["Python", "FastAPI"],
            priority=5,
            can_parallel=True,
            order_index=1,
        ),
        SubTask(
            id="task_002",
            parent_task_id="parent_001",
            title="データベース実装",
            description="SQLiteデータベースの実装",
            task_type=TaskType.IMPLEMENTATION,
            complexity=TaskComplexity.MODERATE,
            estimated_hours=3.0,
            dependencies=[],
            required_skills=["SQL", "SQLite"],
            priority=4,
            can_parallel=True,
            order_index=2,
        ),
        SubTask(
            id="task_003",
            parent_task_id="parent_001",
            title="統合テスト",
            description="API とデータベースの統合テスト",
            task_type=TaskType.TESTING,
            complexity=TaskComplexity.COMPLEX,
            estimated_hours=2.0,
            dependencies=["task_001", "task_002"],
            required_skills=["pytest", "testing"],
            priority=3,
            can_parallel=False,
            order_index=3,
        ),
    ]

    # 実行グループ作成
    print(f"\n📦 実行グループ作成: {test_project_id} - {test_phase}")
    group_id = manager.create_execution_group(
        test_project_id, test_phase, test_tasks, max_parallel=2
    )
    print(f"グループID: {group_id}")

    # リソース使用状況確認
    print(f"\n📊 リソース使用状況:")
    resource_usage = manager.get_resource_usage()
    for resource, usage in resource_usage["current_usage"].items():
        limit = resource_usage["limits"][resource]
        utilization = resource_usage["utilization"][resource]
        print(f"  {resource}: {usage:.1f}/{limit:.1f} ({utilization:.1f}%)")

    # 並列実行テスト
    print(f"\n🚀 並列実行テスト開始")
    success = manager.execute_group_parallel(group_id)
    print(f"実行結果: {'✅ 成功' if success else '❌ 失敗'}")

    # 実行状態確認
    print(f"\n📋 実行状態:")
    status = manager.get_execution_status(group_id)
    print(f"  グループ状態: {status.get('status', 'Unknown')}")
    print(f"  タスク数: {status.get('task_count', 0)}")
    print(f"  並列度: {status.get('max_parallel', 0)}")

    if "tasks" in status:
        print(f"  タスク詳細:")
        for task in status["tasks"]:
            print(
                f"    {task['task_id']}: {task['status']} ({task.get('duration', 0):.1f}秒)"
            )

    # 統計情報
    print(f"\n📈 実行統計:")
    stats = manager.get_execution_statistics()
    print(f"  総タスク数: {stats['total_tasks']}")
    print(f"  完了タスク数: {stats['completed_tasks']}")
    print(f"  失敗タスク数: {stats['failed_tasks']}")
    print(f"  並列グループ数: {stats['parallel_groups']}")
    print(f"  平均実行時間: {stats['avg_execution_time']:.1f}秒")

    # シャットダウン
    manager.shutdown()
