#!/usr/bin/env python3
"""
Worker Task Flow Tracker - Worker間タスクフロー追跡システム
EldersGuildのWorker間でのタスクの流れを追跡・分析
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import logging
import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStage:
    """ワークフローステージ情報"""

    worker_type: str
    worker_id: str = ""
    status: str = "pending"  # pending, processing, completed, error
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time: float = 0.0
    input_data: Dict = None
    output_data: Dict = None
    error_info: Dict = None

    def __post_init__(self):
        if self.input_data is None:
            self.input_data = {}
        if self.output_data is None:
            self.output_data = {}
        if self.error_info is None:
            self.error_info = {}


@dataclass
class TaskFlow:
    """タスクフロー情報"""

    task_id: str
    task_type: str = ""
    status: str = "pending"  # pending, in_progress, transferring, completed, error
    created_at: datetime = None
    updated_at: datetime = None
    workflow_stages: List[WorkflowStage] = None
    total_processing_time: float = 0.0
    error_count: int = 0
    retry_attempts: int = 0
    error_history: List[Dict] = None
    source: str = "worker_system"
    metadata: Dict = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.workflow_stages is None:
            self.workflow_stages = []
        if self.error_history is None:
            self.error_history = []
        if self.metadata is None:
            self.metadata = {}


class TaskFlowTracker:
    """Worker間タスクフロー追跡システム"""

    def __init__(self):
        """TaskFlowTracker 初期化"""
        self.active_flows = {}  # task_id -> TaskFlow
        self.completed_flows = {}
        self.worker_performance = defaultdict(dict)
        self.db_path = PROJECT_ROOT / "data" / "task_flows.db"

        # データベース初期化
        self._init_database()

        logger.info("TaskFlowTracker initialized")

    def _init_database(self):
        """タスクフロー用データベース初期化"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # タスクフローテーブル
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS task_flows (
                task_id TEXT PRIMARY KEY,
                task_type TEXT,
                status TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                total_processing_time REAL,
                error_count INTEGER,
                retry_attempts INTEGER,
                source TEXT,
                metadata TEXT,
                workflow_stages TEXT
            )
            """
            )

            # フローステージテーブル
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS flow_stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                stage_index INTEGER,
                worker_type TEXT,
                worker_id TEXT,
                status TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                processing_time REAL,
                input_data TEXT,
                output_data TEXT,
                error_info TEXT,
                FOREIGN KEY (task_id) REFERENCES task_flows (task_id)
            )
            """
            )

            # エラー履歴テーブル
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS flow_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                worker_id TEXT,
                worker_type TEXT,
                error_at TIMESTAMP,
                error_type TEXT,
                error_message TEXT,
                retry_count INTEGER,
                will_retry BOOLEAN,
                FOREIGN KEY (task_id) REFERENCES task_flows (task_id)
            )
            """
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    def track_task_start(self, task_info: Dict) -> bool:
        """タスク開始を追跡"""
        try:
            task_id = task_info["task_id"]
            worker_type = task_info["worker_type"]

            # 既存のフロー確認
            if task_id in self.active_flows:
                flow = self.active_flows[task_id]

                # 既存のpendingステージを探してアクティベート
                stage_found = False
                for stage in flow.workflow_stages:
                    if stage.worker_type == worker_type and stage.status == "pending":
                        stage.worker_id = task_info["worker_id"]
                        stage.status = "processing"
                        stage.started_at = task_info.get("started_at", datetime.now())
                        stage.input_data = task_info.get("input_data", {})
                        stage_found = True
                        break

                # pendingステージが見つからない場合は新しいステージを追加
                if not stage_found:
                    stage = WorkflowStage(
                        worker_type=worker_type,
                        worker_id=task_info["worker_id"],
                        status="processing",
                        started_at=task_info.get("started_at", datetime.now()),
                        input_data=task_info.get("input_data", {}),
                    )
                    flow.workflow_stages.append(stage)

                flow.status = "in_progress"
                flow.updated_at = datetime.now()
            else:
                # 新しいフロー作成
                stage = WorkflowStage(
                    worker_type=worker_type,
                    worker_id=task_info["worker_id"],
                    status="processing",
                    started_at=task_info.get("started_at", datetime.now()),
                    input_data=task_info.get("input_data", {}),
                )

                flow = TaskFlow(
                    task_id=task_id,
                    task_type=task_info.get("task_type", ""),
                    status="in_progress",
                    workflow_stages=[stage],
                )

                self.active_flows[task_id] = flow

            # データベースに保存
            self._save_flow_to_db(flow)

            logger.info(f"Task start tracked: {task_id} on {worker_type}")
            return True

        except Exception as e:
            logger.error(f"Error tracking task start: {e}")
            return False

    def track_task_completion(self, completion_info: Dict) -> bool:
        """タスク完了を追跡"""
        try:
            task_id = completion_info["task_id"]

            if task_id not in self.active_flows:
                logger.warning(f"Task flow not found: {task_id}")
                return False

            flow = self.active_flows[task_id]

            # 現在のステージを更新（processing または error 状態のものを探す）
            current_stage = None
            for stage in reversed(flow.workflow_stages):
                if stage.worker_type == completion_info[
                    "worker_type"
                ] and stage.status in ["processing", "error"]:
                    current_stage = stage
                    break

            if not current_stage:
                logger.warning(f"Current stage not found for {task_id}")
                return False

            # ステージ完了情報を更新
            current_stage.status = completion_info.get("status", "completed")
            current_stage.completed_at = completion_info.get(
                "completed_at", datetime.now()
            )
            current_stage.processing_time = completion_info.get("processing_time", 0.0)
            current_stage.output_data = completion_info.get("output_data", {})

            # エラーから回復した場合、フローステータスも更新
            if flow.status == "error" and current_stage.status == "completed":
                flow.status = "in_progress"

            # 次のWorkerがある場合
            next_worker = completion_info.get("next_worker")
            if next_worker:
                # 次のステージを準備
                next_stage = WorkflowStage(worker_type=next_worker, status="pending")
                flow.workflow_stages.append(next_stage)
                flow.status = "transferring"
            else:
                # 全体のフロー完了
                flow.status = "completed"
                # アクティブから完了に移動
                self.completed_flows[task_id] = flow
                del self.active_flows[task_id]

            # 再試行回数更新
            if completion_info.get("retry_attempt"):
                flow.retry_attempts = completion_info["retry_attempt"]

            flow.updated_at = datetime.now()
            self._save_flow_to_db(flow)

            logger.info(f"Task completion tracked: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Error tracking task completion: {e}")
            return False

    def track_task_error(self, error_info: Dict) -> bool:
        """タスクエラーを追跡"""
        try:
            task_id = error_info["task_id"]

            if task_id not in self.active_flows:
                logger.warning(f"Task flow not found for error: {task_id}")
                return False

            flow = self.active_flows[task_id]

            # エラー情報を記録
            error_record = {
                "error_at": error_info.get("error_at", datetime.now()),
                "worker_id": error_info["worker_id"],
                "worker_type": error_info["worker_type"],
                "error_type": error_info.get("error_type", "Unknown"),
                "error_message": error_info.get("error_message", ""),
                "retry_count": error_info.get("retry_count", 0),
                "will_retry": error_info.get("will_retry", False),
            }

            flow.error_history.append(error_record)
            flow.error_count += 1
            flow.status = "error"
            flow.updated_at = datetime.now()

            # 現在のステージにエラー情報を設定
            for stage in reversed(flow.workflow_stages):
                if (
                    stage.worker_type == error_info["worker_type"]
                    and stage.status == "processing"
                ):
                    stage.status = "error"
                    stage.error_info = error_record
                    break

            # データベースにエラーを保存
            self._save_error_to_db(task_id, error_record)
            self._save_flow_to_db(flow)

            logger.warning(
                f"Task error tracked: {task_id} - {error_info.get('error_type')}"
            )
            return True

        except Exception as e:
            logger.error(f"Error tracking task error: {e}")
            return False

    def get_task_flow(self, task_id: str) -> Optional[Dict]:
        """タスクフロー情報を取得"""
        try:
            # アクティブフローから検索
            if task_id in self.active_flows:
                flow = self.active_flows[task_id]
                return self._flow_to_dict(flow)

            # 完了フローから検索
            if task_id in self.completed_flows:
                flow = self.completed_flows[task_id]
                return self._flow_to_dict(flow)

            # データベースから検索
            flow_dict = self._load_flow_from_db(task_id)
            if flow_dict:
                return flow_dict

            return None

        except Exception as e:
            logger.error(f"Error getting task flow: {e}")
            return None

    def get_active_flows(self) -> List[Dict]:
        """アクティブなフロー一覧を取得"""
        try:
            active_flows = []
            for flow in self.active_flows.values():
                active_flows.append(self._flow_to_dict(flow))

            return active_flows

        except Exception as e:
            logger.error(f"Error getting active flows: {e}")
            return []

    def calculate_flow_metrics(self, task_id: str) -> Dict:
        """フローメトリクスを計算"""
        try:
            flow_dict = self.get_task_flow(task_id)
            if not flow_dict:
                return {}

            stages = flow_dict["workflow_stages"]
            if not stages:
                return {}

            # 基本メトリクス
            total_processing_time = sum(
                stage.get("processing_time", 0) for stage in stages
            )
            total_stages = len(stages)
            average_stage_time = (
                total_processing_time / total_stages if total_stages > 0 else 0
            )

            # ボトルネック特定
            bottleneck_stage = max(stages, key=lambda s: s.get("processing_time", 0))

            # 効率性スコア（処理時間の分散を考慮）
            if total_stages > 1:
                stage_times = [stage.get("processing_time", 0) for stage in stages]
                avg_time = sum(stage_times) / len(stage_times)
                variance = sum((t - avg_time) ** 2 for t in stage_times) / len(
                    stage_times
                )
                efficiency = max(
                    0, 1 - (variance / (avg_time**2)) if avg_time > 0 else 0
                )
            else:
                efficiency = 1.0

            # ステージ別詳細
            stage_breakdown = []
            for i, stage in enumerate(stages):
                stage_breakdown.append(
                    {
                        "stage_index": i,
                        "worker_type": stage.get("worker_type"),
                        "processing_time": stage.get("processing_time", 0),
                        "percentage_of_total": (
                            (
                                stage.get("processing_time", 0)
                                / total_processing_time
                                * 100
                            )
                            if total_processing_time > 0
                            else 0
                        ),
                    }
                )

            return {
                "total_processing_time": total_processing_time,
                "total_stages": total_stages,
                "average_stage_time": average_stage_time,
                "flow_efficiency": efficiency,
                "bottleneck_stage": (
                    bottleneck_stage.get("worker_type") if bottleneck_stage else None
                ),
                "stage_breakdown": stage_breakdown,
            }

        except Exception as e:
            logger.error(f"Error calculating flow metrics: {e}")
            return {}

    def get_worker_performance_in_flows(self, worker_id: str) -> Dict:
        """フロー内でのWorkerパフォーマンスを取得"""
        try:
            # 全フローからWorkerの情報を集計
            worker_tasks = []
            total_processing_time = 0.0
            success_count = 0
            total_count = 0

            all_flows = list(self.active_flows.values()) + list(
                self.completed_flows.values()
            )

            for flow in all_flows:
                for stage in flow.workflow_stages:
                    if stage.worker_id == worker_id:
                        task_info = {
                            "task_id": flow.task_id,
                            "processing_time": stage.processing_time,
                            "status": stage.status,
                        }
                        worker_tasks.append(task_info)

                        total_processing_time += stage.processing_time
                        total_count += 1

                        if stage.status == "completed":
                            success_count += 1

            if total_count == 0:
                return {
                    "total_tasks_processed": 0,
                    "average_processing_time": 0.0,
                    "success_rate": 1.0,
                    "total_processing_time": 0.0,
                }

            # 最速・最遅タスク
            fastest_task = (
                min(worker_tasks, key=lambda t: t["processing_time"])
                if worker_tasks
                else None
            )
            slowest_task = (
                max(worker_tasks, key=lambda t: t["processing_time"])
                if worker_tasks
                else None
            )

            return {
                "total_tasks_processed": total_count,
                "average_processing_time": total_processing_time / total_count,
                "success_rate": success_count / total_count,
                "total_processing_time": total_processing_time,
                "fastest_task": fastest_task,
                "slowest_task": slowest_task,
            }

        except Exception as e:
            logger.error(f"Error getting worker performance: {e}")
            return {}

    def analyze_flow_bottlenecks(self, task_id: str) -> Dict:
        """フローのボトルネック分析"""
        try:
            flow_dict = self.get_task_flow(task_id)
            if not flow_dict:
                return {}

            stages = flow_dict["workflow_stages"]
            if not stages:
                return {}

            total_time = sum(stage.get("processing_time", 0) for stage in stages)
            if total_time == 0:
                return {}

            # 最も時間がかかったステージ
            primary_bottleneck = max(stages, key=lambda s: s.get("processing_time", 0))
            bottleneck_time = primary_bottleneck.get("processing_time", 0)

            # ボトルネックの深刻度（全体時間に占める割合）
            bottleneck_severity = bottleneck_time / total_time

            # 改善提案
            suggestions = []
            if bottleneck_severity > 0.5:
                suggestions.append(
                    f"{primary_bottleneck.get('worker_type')} の処理時間が全体の{bottleneck_severity*100:.1f}%を占めています"
                )
                suggestions.append(
                    "このWorkerのスケーリングまたは最適化を検討してください"
                )

            if bottleneck_severity > 0.3:
                suggestions.append("処理の並列化を検討してください")

            return {
                "primary_bottleneck": primary_bottleneck,
                "bottleneck_severity": bottleneck_severity,
                "improvement_suggestions": suggestions,
                "total_flow_time": total_time,
            }

        except Exception as e:
            logger.error(f"Error analyzing bottlenecks: {e}")
            return {}

    def integrate_with_status_monitor(self, status_monitor):
        """WorkerStatusMonitor と統合"""
        try:
            from libs.integrated_worker_monitor import IntegratedWorkerMonitor

            return IntegratedWorkerMonitor(self, status_monitor)
        except ImportError:
            # シンプルな統合オブジェクトを作成
            return SimpleIntegratedMonitor(self, status_monitor)

    def sync_with_task_tracker(self, task_tracker_data: Dict) -> bool:
        """TaskTracker との同期"""
        try:
            task_id = task_tracker_data["task_id"]

            # TaskTracker形式からフロー形式に変換
            task_info = {
                "task_id": task_id,
                "task_type": task_tracker_data.get("title", ""),
                "worker_type": task_tracker_data.get("assignee", "unknown"),
                "worker_id": f"{task_tracker_data.get('assignee', 'unknown')}_001",
                "started_at": datetime.now(),
            }

            # フロー作成
            stage = WorkflowStage(
                worker_type=task_info["worker_type"],
                worker_id=task_info["worker_id"],
                status=(
                    "processing"
                    if task_tracker_data.get("status") == "in_progress"
                    else "pending"
                ),
                started_at=task_info["started_at"],
            )

            flow = TaskFlow(
                task_id=task_id,
                task_type=task_info["task_type"],
                status=(
                    "in_progress"
                    if task_tracker_data.get("status") == "in_progress"
                    else "pending"
                ),
                workflow_stages=[stage],
                source="task_tracker",
            )

            self.active_flows[task_id] = flow
            self._save_flow_to_db(flow)

            logger.info(f"Task tracker sync completed: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Error syncing with task tracker: {e}")
            return False

    def _flow_to_dict(self, flow: TaskFlow) -> Dict:
        """TaskFlowオブジェクトを辞書に変換"""
        flow_dict = asdict(flow)

        # datetime オブジェクトを文字列に変換
        if flow_dict.get("created_at"):
            flow_dict["created_at"] = flow_dict["created_at"].isoformat()
        if flow_dict.get("updated_at"):
            flow_dict["updated_at"] = flow_dict["updated_at"].isoformat()

        # ステージの datetime も変換
        for stage in flow_dict.get("workflow_stages", []):
            if stage.get("started_at"):
                stage["started_at"] = stage["started_at"].isoformat()
            if stage.get("completed_at"):
                stage["completed_at"] = stage["completed_at"].isoformat()

        return flow_dict

    def _save_flow_to_db(self, flow: TaskFlow):
        """フローをデータベースに保存"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # メインフロー情報
            cursor.execute(
                """
            INSERT OR REPLACE INTO task_flows
            (task_id, task_type, status, created_at, updated_at, total_processing_time,
             error_count, retry_attempts, source, metadata, workflow_stages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    flow.task_id,
                    flow.task_type,
                    flow.status,
                    flow.created_at.isoformat(),
                    flow.updated_at.isoformat(),
                    flow.total_processing_time,
                    flow.error_count,
                    flow.retry_attempts,
                    flow.source,
                    json.dumps(flow.metadata),
                    json.dumps(
                        [asdict(stage) for stage in flow.workflow_stages], default=str
                    ),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error saving flow to database: {e}")

    def _save_error_to_db(self, task_id: str, error_record: Dict):
        """エラーをデータベースに保存"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
            INSERT INTO flow_errors
            (task_id, worker_id, worker_type, error_at, error_type, error_message, retry_count, will_retry)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    error_record["worker_id"],
                    error_record["worker_type"],
                    (
                        error_record["error_at"].isoformat()
                        if isinstance(error_record["error_at"], datetime)
                        else error_record["error_at"]
                    ),
                    error_record["error_type"],
                    error_record["error_message"],
                    error_record["retry_count"],
                    error_record["will_retry"],
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error saving error to database: {e}")

    def _load_flow_from_db(self, task_id: str) -> Optional[Dict]:
        """データベースからフローを読み込み"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM task_flows WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()

            if row:
                flow_dict = dict(row)
                # JSON フィールドをパース
                flow_dict["metadata"] = json.loads(flow_dict["metadata"])
                flow_dict["workflow_stages"] = json.loads(flow_dict["workflow_stages"])

                conn.close()
                return flow_dict

            conn.close()
            return None

        except Exception as e:
            logger.error(f"Error loading flow from database: {e}")
            return None


class SimpleIntegratedMonitor:
    """シンプルな統合モニター（統合クラスが利用できない場合）"""

    def __init__(self, flow_tracker, status_monitor):
        self.flow_tracker = flow_tracker
        self.status_monitor = status_monitor

    def register_worker(self, worker_info):
        """Worker登録"""
        return self.status_monitor.register_worker(worker_info)

    def track_worker_task_flow(self, task_flow_data):
        """Worker タスクフロー追跡"""
        return self.flow_tracker.track_task_start(task_flow_data)

    def get_combined_dashboard_data(self):
        """統合ダッシュボードデータ取得"""
        try:
            worker_data = self.status_monitor.generate_dashboard_data()
            active_flows = self.flow_tracker.get_active_flows()

            # worker_data が期待されるフォーマットでない場合の対応
            if "workers_summary" in worker_data:
                worker_status = worker_data
            else:
                worker_status = {
                    "workers_summary": {
                        "total_workers": len(self.status_monitor.workers_status)
                    },
                    "queue_status": {},
                    "system_health": {},
                    "performance_metrics": {},
                }

            return {
                "worker_status": worker_status,
                "task_flows": {
                    "active_flows": len(active_flows),
                    "flows": active_flows,
                },
                "flow_metrics": {
                    "total_flows_processed": len(self.flow_tracker.completed_flows)
                },
            }
        except Exception as e:
            logger.error(f"Error getting combined dashboard data: {e}")
            return {
                "worker_status": {"workers_summary": {"total_workers": 0}},
                "task_flows": {"active_flows": 0, "flows": []},
                "flow_metrics": {"total_flows_processed": 0},
            }


if __name__ == "__main__":
    # テスト実行
    tracker = TaskFlowTracker()

    # テスト用タスクフロー
    test_task = {
        "task_id": "TEST-001",
        "task_type": "code_generation",
        "worker_id": "task_worker_001",
        "worker_type": "task_worker",
        "started_at": datetime.now(),
        "input_data": {"prompt": "Create test function"},
    }

    tracker.track_task_start(test_task)
    print("Task flow tracking started successfully")

    # フロー情報確認
    flow = tracker.get_task_flow("TEST-001")
    print(f"Task flow: {flow}")
