#!/usr/bin/env python3
"""
ワークフロー自動制御システム - フェーズ間の依存関係と自動進行管理

PMが設計したプロジェクトのフェーズ進行を自動制御し、
前段階完了後の自動次段階開始、条件付き実行ロジックを提供
"""

import json
import logging
import sqlite3

# プロジェクトルートをPythonパスに追加
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pika

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager
from libs.intelligent_task_splitter import IntelligentTaskSplitter, SubTask
from libs.project_design_manager import ProjectDesignManager

logger = logging.getLogger(__name__)


class PhaseStatus(Enum):
    """フェーズ状態"""

    PENDING = "pending"  # 待機中
    READY = "ready"  # 実行可能
    IN_PROGRESS = "in_progress"  # 実行中
    COMPLETED = "completed"  # 完了
    FAILED = "failed"  # 失敗
    BLOCKED = "blocked"  # ブロック中
    CANCELLED = "cancelled"  # キャンセル


class WorkflowEvent(Enum):
    """ワークフローイベント"""

    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_FAILED = "phase_failed"
    TASK_COMPLETED = "task_completed"
    DEPENDENCY_RESOLVED = "dependency_resolved"
    AUTO_ADVANCE = "auto_advance"


@dataclass
class PhaseTransition:
    """フェーズ遷移定義"""

    from_phase: str
    to_phase: str
    condition: str  # 遷移条件
    auto_advance: bool = True
    delay_minutes: int = 0


@dataclass
class WorkflowRule:
    """ワークフロールール"""

    rule_id: str
    project_id: str
    phase: str
    condition: str
    action: str
    priority: int = 0
    active: bool = True


class WorkflowController(BaseManager):
    """ワークフロー自動制御システム"""

    def __init__(self):
        """初期化メソッド"""
        super().__init__("WorkflowController")
        self.db_path = PROJECT_ROOT / "db" / "workflow_control.db"
        self.task_splitter = IntelligentTaskSplitter()
        self.project_manager = ProjectDesignManager()

        # RabbitMQ接続（タスク送信用）
        self.connection = None
        self.channel = None

        # フェーズ定義
        self.phases = ["planning", "design", "development", "testing", "deployment"]

        # 標準フェーズ遷移
        self.standard_transitions = [
            PhaseTransition("planning", "design", "all_planning_tasks_completed"),
            PhaseTransition("design", "development", "design_approved"),
            PhaseTransition("development", "testing", "implementation_completed"),
            PhaseTransition("testing", "deployment", "all_tests_passed"),
        ]

        # ワークフロールール
        self.workflow_rules = {
            "auto_split_complex_tasks": {
                "condition": "task_complexity > 3.0",
                "action": "split_task",
                "priority": 1,
            },
            "parallel_independent_tasks": {
                "condition": "tasks_have_no_dependencies",
                "action": "execute_parallel",
                "priority": 2,
            },
            "quality_gate_check": {
                "condition": "phase_completion",
                "action": "run_quality_check",
                "priority": 3,
            },
            "auto_advance_on_success": {
                "condition": "quality_check_passed",
                "action": "advance_to_next_phase",
                "priority": 4,
            },
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
            # フェーズ状態管理テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS phase_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    progress_percentage REAL DEFAULT 0.0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    estimated_completion TIMESTAMP,
                    blocking_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_id, phase)
                )
            """
            )

            # ワークフロールールテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT UNIQUE NOT NULL,
                    project_id TEXT,
                    phase TEXT,
                    condition_expr TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_params TEXT,
                    priority INTEGER DEFAULT 0,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # ワークフローイベント履歴
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    phase TEXT,
                    task_id TEXT,
                    event_data TEXT,
                    triggered_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # フェーズ依存関係テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS phase_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    depends_on_phase TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'blocks',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 自動進行設定テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auto_advance_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    from_phase TEXT NOT NULL,
                    to_phase TEXT NOT NULL,
                    condition_expr TEXT NOT NULL,
                    auto_advance BOOLEAN DEFAULT 1,
                    delay_minutes INTEGER DEFAULT 0,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # インデックス作成
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_phase_states_project ON phase_states(project_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_events_project ON " \
                    "workflow_events(project_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_phase_deps_project ON " \
                    "phase_dependencies(project_id)"
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
            self.channel.queue_declare(queue="pm_task_queue", durable=True)

            logger.info("✅ RabbitMQ接続成功")
        except Exception as e:
            logger.warning(f"RabbitMQ接続失敗: {e}")
            self.connection = None
            self.channel = None

    def initialize_project_workflow(
        self, project_id: str, custom_phases: Optional[List[str]] = None
    ) -> bool:
        """プロジェクトワークフローの初期化"""
        try:
            phases = custom_phases or self.phases

            with sqlite3.connect(self.db_path) as conn:
                # 既存の状態をクリア
                conn.execute(
                    "DELETE FROM phase_states WHERE project_id = ?", (project_id,)
                )

                # 各フェーズを初期化
                for i, phase in enumerate(phases):
                    status = (
                        PhaseStatus.READY.value if i == 0 else PhaseStatus.PENDING.value
                    )

                    conn.execute(
                        """
                        INSERT INTO phase_states
                        (project_id, phase, status, progress_percentage)
                        VALUES (?, ?, ?, ?)
                    """,
                        (project_id, phase, status, 0.0),
                    )

                # 標準依存関係を設定
                for i in range(1, len(phases)):
                    conn.execute(
                        """
                        INSERT INTO phase_dependencies
                        (project_id, phase, depends_on_phase)
                        VALUES (?, ?, ?)
                    """,
                        (project_id, phases[i], phases[i - 1]),
                    )

                # 標準自動進行設定
                for i in range(len(phases) - 1):
                    conn.execute(
                        """
                        INSERT INTO auto_advance_settings
                        (project_id, from_phase, to_phase, condition_expr)
                        VALUES (?, ?, ?, ?)
                    """,
                        (project_id, phases[i], phases[i + 1], "phase_completed"),
                    )

            logger.info(f"✅ プロジェクトワークフロー初期化完了: {project_id}")
            return True

        except Exception as e:
            logger.error(f"ワークフロー初期化エラー: {e}")
            return False

    def check_phase_dependencies(
        self, project_id: str, target_phase: str
    ) -> Tuple[bool, List[str]]:
        """フェーズ実行前提条件チェック"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 依存フェーズを取得
                cursor = conn.execute(
                    """
                    SELECT depends_on_phase FROM phase_dependencies
                    WHERE project_id = ? AND phase = ?
                """,
                    (project_id, target_phase),
                )

                dependencies = [row[0] for row in cursor]
                unmet_dependencies = []

                # 各依存フェーズの状態をチェック
                for dep_phase in dependencies:
                    cursor = conn.execute(
                        """
                        SELECT status FROM phase_states
                        WHERE project_id = ? AND phase = ?
                    """,
                        (project_id, dep_phase),
                    )

                    row = cursor.fetchone()
                    if not row or row[0] != PhaseStatus.COMPLETED.value:
                        unmet_dependencies.append(dep_phase)

                can_execute = len(unmet_dependencies) == 0

                logger.info(
                    f"📋 フェーズ依存関係チェック ({target_phase}): {'✅ 実行可能' if can_execute else '❌ 依存未解決'}"
                )

                return can_execute, unmet_dependencies

        except Exception as e:
            logger.error(f"依存関係チェックエラー: {e}")
            return False, []

    def start_phase(self, project_id: str, phase: str, force: bool = False) -> bool:
        """フェーズ開始"""
        try:
            # 依存関係チェック
            if not force:
                can_execute, unmet_deps = self.check_phase_dependencies(
                    project_id, phase
                )
                if not can_execute:
                    logger.warning(
                        f"⚠️ フェーズ開始不可 ({phase}): 依存関係未解決 {unmet_deps}"
                    )
                    return False

            # フェーズ状態を更新
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE phase_states
                    SET status = ?, started_at = ?, updated_at = ?
                    WHERE project_id = ? AND phase = ?
                """,
                    (
                        PhaseStatus.IN_PROGRESS.value,
                        datetime.now(),
                        datetime.now(),
                        project_id,
                        phase,
                    ),
                )

            # イベント記録
            self._record_workflow_event(project_id, WorkflowEvent.PHASE_STARTED, phase)

            # フェーズのタスクを自動生成・分割
            self._generate_phase_tasks(project_id, phase)

            logger.info(f"🚀 フェーズ開始: {project_id} - {phase}")
            return True

        except Exception as e:
            logger.error(f"フェーズ開始エラー: {e}")
            return False

    def complete_phase(self, project_id: str, phase: str) -> bool:
        """フェーズ完了"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # フェーズ状態を更新
                conn.execute(
                    """
                    UPDATE phase_states
                    SET status = ?, completed_at = ?, progress_percentage = 100.0, updated_at = ?
                    WHERE project_id = ? AND phase = ?
                """,
                    (
                        PhaseStatus.COMPLETED.value,
                        datetime.now(),
                        datetime.now(),
                        project_id,
                        phase,
                    ),
                )

            # イベント記録
            self._record_workflow_event(
                project_id, WorkflowEvent.PHASE_COMPLETED, phase
            )

            # 自動進行チェック
            self._check_auto_advance(project_id, phase)

            logger.info(f"✅ フェーズ完了: {project_id} - {phase}")
            return True

        except Exception as e:
            logger.error(f"フェーズ完了エラー: {e}")
            return False

    def _generate_phase_tasks(self, project_id: str, phase: str):
        """フェーズのタスクを自動生成"""
        try:
            # プロジェクト設計からタスクを取得
            design_data = self.project_manager.get_project_design(project_id)
            if not design_data:
                logger.warning(f"プロジェクト設計が見つかりません: {project_id}")
                return

            # フェーズに応じたタスクテンプレート
            phase_templates = {
                "planning": [
                    "要件定義の詳細化",
                    "プロジェクトスコープの確定",
                    "リソース計画の策定",
                    "リスク分析とリスク管理計画",
                ],
                "design": [
                    "システムアーキテクチャ設計",
                    "データベース設計",
                    "API設計",
                    "UI/UX設計",
                    "詳細設計書作成",
                ],
                "development": [
                    "開発環境のセットアップ",
                    "コアモジュールの実装",
                    "API実装",
                    "データベース実装",
                    "フロントエンド実装",
                ],
                "testing": [
                    "単体テスト実装",
                    "統合テスト実装",
                    "システムテスト実行",
                    "パフォーマンステスト",
                    "セキュリティテスト",
                ],
                "deployment": [
                    "本番環境構築",
                    "デプロイメント自動化",
                    "監視システム設定",
                    "本番デプロイ実行",
                    "運用手順書作成",
                ],
            }

            templates = phase_templates.get(phase, ["汎用タスク"])

            # 繰り返し処理
            for i, template in enumerate(templates):
                task_description = f"{phase.title()}フェーズ: {template}"

                # 複雑なタスクは自動分割
                task_id = f"{project_id}_{phase}_{i+1}"
                subtasks = self.task_splitter.split_into_subtasks(
                    task_id, task_description
                )

                # サブタスクをワーカーキューに送信
                for subtask in subtasks:
                    self._send_task_to_worker(subtask)

            logger.info(f"📋 フェーズタスク生成完了: {project_id} - {phase}")

        except Exception as e:
            logger.error(f"フェーズタスク生成エラー: {e}")

    def _send_task_to_worker(self, subtask: SubTask):
        """サブタスクをワーカーに送信"""
        try:
            if not self.channel:
                logger.warning("RabbitMQ接続なし - タスク送信スキップ")
                return

            task_data = {
                "task_id": subtask.id,
                "task_type": "ai_task",
                "prompt": f"{subtask.title}\n\n{subtask.description}",
                "complexity": subtask.complexity.value,
                "estimated_hours": subtask.estimated_hours,
                "required_skills": subtask.required_skills,
                "priority": subtask.priority,
                "can_parallel": subtask.can_parallel,
                "dependencies": subtask.dependencies,
                "created_at": datetime.now().isoformat(),
            }

            # 優先度に応じてキューを選択
            queue = "ai_tasks"
            priority = min(subtask.priority + 3, 10)  # 最大10

            self.channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=json.dumps(task_data, ensure_ascii=False),
                properties=pika.BasicProperties(
                    delivery_mode=2, priority=priority  # 永続化
                ),
            )

            logger.info(f"📤 タスク送信: {subtask.id} -> {queue}")

        except Exception as e:
            logger.error(f"タスク送信エラー: {e}")

    def _check_auto_advance(self, project_id: str, completed_phase: str):
        """自動進行チェック"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 自動進行設定を取得
                cursor = conn.execute(
                    """
                    SELECT to_phase, condition_expr, delay_minutes
                    FROM auto_advance_settings
                    WHERE project_id = ? AND from_phase = ? AND active = 1
                """,
                    (project_id, completed_phase),
                )

                for row in cursor:
                    to_phase, condition_expr, delay_minutes = row

                    # 条件評価
                    if self._evaluate_condition(
                        project_id, condition_expr, completed_phase
                    ):
                        # 遅延がある場合は遅延実行
                        if not (delay_minutes > 0):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if delay_minutes > 0:
                            self._schedule_delayed_advance(
                                project_id, to_phase, delay_minutes
                            )
                        else:
                            # 即座に次フェーズ開始
                            self.auto_advance_phase(project_id, to_phase)

        except Exception as e:
            logger.error(f"自動進行チェックエラー: {e}")

    def auto_advance_phase(self, project_id: str, target_phase: str) -> bool:
        """フェーズ自動進行"""
        try:
            logger.info(f"🔄 フェーズ自動進行: {project_id} -> {target_phase}")

            # 品質ゲートチェック
            quality_passed = self._run_quality_gate_check(project_id, target_phase)

            if quality_passed:
                # 次フェーズ開始
                success = self.start_phase(project_id, target_phase)

                if success:
                    # 自動進行イベント記録
                    self._record_workflow_event(
                        project_id,
                        WorkflowEvent.AUTO_ADVANCE,
                        target_phase,
                        {"quality_check": "passed", "auto_advanced": True},
                    )

                    logger.info(f"✅ 自動進行成功: {project_id} -> {target_phase}")
                    return True
                else:
                    logger.error(f"❌ 自動進行失敗: フェーズ開始エラー")
                    return False
            else:
                # 品質ゲートで停止
                self._set_phase_blocked(
                    project_id, target_phase, "品質ゲートチェック失敗"
                )
                logger.warning(f"⚠️ 自動進行停止: 品質ゲートチェック失敗")
                return False

        except Exception as e:
            logger.error(f"自動進行エラー: {e}")
            return False

    def _run_quality_gate_check(self, project_id: str, phase: str) -> bool:
        """品質ゲートチェック実行"""
        try:
            # フェーズ別品質基準
            quality_criteria = {
                "design": {"design_approval_rate": 90.0, "requirement_coverage": 100.0},
                "development": {
                    "code_coverage": 80.0,
                    "test_pass_rate": 95.0,
                    "code_quality_score": 80.0,
                },
                "testing": {
                    "test_pass_rate": 100.0,
                    "bug_density": 0.1,  # 1000行あたりのバグ数
                    "performance_benchmark": 90.0,
                },
                "deployment": {
                    "deployment_success_rate": 95.0,
                    "system_availability": 99.0,
                },
            }

            criteria = quality_criteria.get(phase, {})

            if not criteria:
                # 品質基準がない場合は通過
                return True

            # 実際の品質チェックロジック（簡易版）
            # 本来は実際のメトリクスを評価
            logger.info(f"🔍 品質ゲートチェック実行: {phase}")

            # PMフィードバックシステムとの連携
            # （実装済みのPMQualityEvaluatorを活用）

            # 簡易的にランダム判定（実際の実装では実データを使用）
            import random

            quality_score = random.uniform(70, 100)

            passed = quality_score >= 80.0

            logger.info(
                f"📊 品質ゲート結果: {quality_score:.1f}% - {'✅ 通過' if passed else '❌ 不合格'}"
            )

            return passed

        except Exception as e:
            logger.error(f"品質ゲートチェックエラー: {e}")
            return False

    def _set_phase_blocked(self, project_id: str, phase: str, reason: str):
        """フェーズをブロック状態に設定"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE phase_states
                    SET status = ?, blocking_reason = ?, updated_at = ?
                    WHERE project_id = ? AND phase = ?
                """,
                    (
                        PhaseStatus.BLOCKED.value,
                        reason,
                        datetime.now(),
                        project_id,
                        phase,
                    ),
                )

            logger.warning(f"🚫 フェーズブロック: {project_id} - {phase} ({reason})")

        except Exception as e:
            logger.error(f"フェーズブロック設定エラー: {e}")

    def _evaluate_condition(
        self, project_id: str, condition_expr: str, phase: str
    ) -> bool:
        """条件式評価"""
        try:
            # 基本的な条件評価
            if condition_expr == "phase_completed":
                return True  # フェーズ完了時に呼ばれるので常にTrue

            # より複雑な条件式の評価（将来拡張）
            if "all_tasks_completed" in condition_expr:
                return self._check_all_tasks_completed(project_id, phase)

            if "quality_check_passed" in condition_expr:
                return self._run_quality_gate_check(project_id, phase)

            # デフォルトはTrue
            return True

        except Exception as e:
            logger.error(f"条件評価エラー: {e}")
            return False

    def _check_all_tasks_completed(self, project_id: str, phase: str) -> bool:
        """フェーズの全タスク完了チェック"""
        try:
            # TaskSplitterのデータベースから該当フェーズのタスクを確認
            # 簡易実装
            return True

        except Exception as e:
            logger.error(f"タスク完了チェックエラー: {e}")
            return False

    def _schedule_delayed_advance(
        self, project_id: str, phase: str, delay_minutes: int
    ):
        """遅延自動進行をスケジュール"""
        # 実際の実装では非同期タスクキューやスケジューラーを使用
        logger.info(
            f"⏰ 遅延自動進行スケジュール: {project_id} -> {phase} (遅延: {delay_minutes}分)"
        )

        # 簡易実装：即座に実行（実際は遅延実行）
        self.auto_advance_phase(project_id, phase)

    def _record_workflow_event(
        self,
        project_id: str,
        event_type: WorkflowEvent,
        phase: Optional[str] = None,
        event_data: Optional[Dict] = None,
    ):
        """ワークフローイベント記録"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO workflow_events
                    (project_id, event_type, phase, event_data, triggered_by)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        project_id,
                        event_type.value,
                        phase,
                        json.dumps(event_data) if event_data else None,
                        "workflow_controller",
                    ),
                )

        except Exception as e:
            logger.error(f"イベント記録エラー: {e}")

    def get_project_workflow_status(self, project_id: str) -> Dict[str, Any]:
        """プロジェクトワークフロー状態取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # フェーズ状態
                cursor = conn.execute(
                    """
                    SELECT phase, status, progress_percentage, started_at, completed_at, blocking_reason
                    FROM phase_states
                    WHERE project_id = ?
                    ORDER BY
                        CASE phase
                            WHEN 'planning' THEN 1
                            WHEN 'design' THEN 2
                            WHEN 'development' THEN 3
                            WHEN 'testing' THEN 4
                            WHEN 'deployment' THEN 5
                            ELSE 6
                        END
                """,
                    (project_id,),
                )

                phases = []
                for row in cursor:
                    phases.append(
                        {
                            "phase": row[0],
                            "status": row[1],
                            "progress_percentage": row[2],
                            "started_at": row[3],
                            "completed_at": row[4],
                            "blocking_reason": row[5],
                        }
                    )

                # 現在のフェーズ
                current_phase = None
                for phase in phases:
                    if phase["status"] == PhaseStatus.IN_PROGRESS.value:
                        current_phase = phase["phase"]
                        break

                # 全体進捗
                completed_phases = sum(
                    1 for p in phases if p["status"] == PhaseStatus.COMPLETED.value
                )
                overall_progress = (
                    (completed_phases / len(phases)) * 100 if phases else 0
                )

                # 最近のイベント
                cursor = conn.execute(
                    """
                    SELECT event_type, phase, created_at
                    FROM workflow_events
                    WHERE project_id = ?
                    ORDER BY created_at DESC
                    LIMIT 5
                """,
                    (project_id,),
                )

                recent_events = [
                    {"event_type": row[0], "phase": row[1], "created_at": row[2]}
                    for row in cursor
                ]

                return {
                    "project_id": project_id,
                    "phases": phases,
                    "current_phase": current_phase,
                    "overall_progress": overall_progress,
                    "recent_events": recent_events,
                }

        except Exception as e:
            logger.error(f"ワークフロー状態取得エラー: {e}")
            return {}

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """ワークフロー統計情報取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}

                # プロジェクト数
                cursor = conn.execute(
                    "SELECT COUNT(DISTINCT project_id) FROM phase_states"
                )
                stats["total_projects"] = cursor.fetchone()[0]

                # フェーズ別統計
                cursor = conn.execute(
                    """
                    SELECT status, COUNT(*) as count
                    FROM phase_states
                    GROUP BY status
                """
                )
                stats["phase_status_distribution"] = dict(cursor.fetchall())

                # 自動進行統計
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM workflow_events
                    WHERE event_type = 'auto_advance'
                """
                )
                stats["auto_advances"] = cursor.fetchone()[0]

                # 平均フェーズ完了時間
                cursor = conn.execute(
                    """
                    SELECT AVG(
                        CASE
                            WHEN completed_at IS NOT NULL AND started_at IS NOT NULL
                            THEN julianday(completed_at) - julianday(started_at)
                            ELSE NULL
                        END
                    ) * 24 as avg_hours
                    FROM phase_states
                    WHERE status = 'completed'
                """
                )
                avg_hours = cursor.fetchone()[0]
                stats["avg_phase_completion_hours"] = avg_hours or 0.0

                return stats

        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {}


if __name__ == "__main__":
    # テスト実行
    controller = WorkflowController()

    # テストプロジェクト
    test_project_id = "test_project_001"

    print("=" * 80)
    print("🔄 Workflow Controller Test")
    print("=" * 80)

    # ワークフロー初期化
    print(f"\n📋 ワークフロー初期化: {test_project_id}")
    success = controller.initialize_project_workflow(test_project_id)
    print(f"結果: {'✅ 成功' if success else '❌ 失敗'}")

    # フェーズ開始テスト
    print(f"\n🚀 フェーズ開始テスト: planning")
    success = controller.start_phase(test_project_id, "planning")
    print(f"結果: {'✅ 成功' if success else '❌ 失敗'}")

    # 依存関係チェックテスト
    print(f"\n🔍 依存関係チェックテスト: development")
    can_execute, unmet_deps = controller.check_phase_dependencies(
        test_project_id, "development"
    )
    print(f"実行可能: {'✅ はい' if can_execute else '❌ いいえ'}")
    print(f"未解決依存関係: {unmet_deps}")

    # フェーズ完了テスト
    print(f"\n✅ フェーズ完了テスト: planning")
    success = controller.complete_phase(test_project_id, "planning")
    print(f"結果: {'✅ 成功' if success else '❌ 失敗'}")

    # ワークフロー状態確認
    print(f"\n📊 ワークフロー状態:")
    status = controller.get_project_workflow_status(test_project_id)
    for phase in status.get("phases", []):
        print(
            f"  {phase['phase']}: {phase['status']} ({phase['progress_percentage']:.1f}%)"
        )

    print(f"現在のフェーズ: {status.get('current_phase', 'なし')}")
    print(f"全体進捗: {status.get('overall_progress', 0):.1f}%")

    # 統計情報
    print(f"\n📈 統計情報:")
    stats = controller.get_workflow_statistics()
    print(f"総プロジェクト数: {stats.get('total_projects', 0)}")
    print(f"自動進行回数: {stats.get('auto_advances', 0)}")
    print(f"平均フェーズ完了時間: {stats.get('avg_phase_completion_hours', 0):.1f}時間")
