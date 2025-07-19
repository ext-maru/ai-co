#!/usr/bin/env python3
"""
Elders Guild プロジェクト管理マネージャー
要件定義から本番反映まで全フェーズを管理
"""

import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseManager, get_config


class ProjectDesignManager(BaseManager):
    """プロジェクト全体のライフサイクル管理"""

    def __init__(self):
        super().__init__()
        self.db_path = PROJECT_ROOT / "db" / "project_designs.db"
        self.design_folder = PROJECT_ROOT / "project_designs"
        self._init_database()
        self._init_folders()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _init_database(self):
        """データベース初期化"""
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # SQLファイルを読み込んで実行
        sql_file = PROJECT_ROOT / "db" / "project_designs.sql"
        if sql_file.exists():
            with open(sql_file, "r", encoding="utf-8") as f:
                sql = f.read()

            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(sql)
                conn.commit()

    def _init_folders(self):
        """設計書フォルダ構造の初期化"""
        folders = [
            "requirements",  # 要件定義書
            "designs",  # 設計書
            "development",  # 開発成果物
            "tests",  # テスト結果
            "deployments",  # 本番反映記録
        ]

        for folder in folders:
            folder_path = self.design_folder / folder
            folder_path.mkdir(parents=True, exist_ok=True)

    def create_project(self, task_id: str, name: str, description: str) -> str:
        """新規プロジェクト作成"""
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO projects (project_id, task_id, name, description)
                VALUES (?, ?, ?, ?)
            """,
                (project_id, task_id, name, description),
            )

            # 全フェーズの進捗レコードを作成
            phases = ["planning", "design", "development", "testing", "deployment"]
            for phase in phases:
                status = "in_progress" if phase == "planning" else "not_started"
                conn.execute(
                    """
                    INSERT INTO phase_progress (project_id, phase, status)
                    VALUES (?, ?, ?)
                """,
                    (project_id, phase, status),
                )

            conn.commit()

        # プロジェクトフォルダ作成
        project_folder = self.design_folder / project_id
        project_folder.mkdir(exist_ok=True)

        self.logger.info(f"Project created: {project_id} - {name}")
        return project_id

    def add_requirement(
        self, project_id: str, type: str, description: str, priority: str = "normal"
    ) -> str:
        """要件定義追加"""
        req_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO requirements
                (requirement_id, project_id, type, description, priority)
                VALUES (?, ?, ?, ?, ?)
            """,
                (req_id, project_id, type, description, priority),
            )
            conn.commit()

        # 要件定義書として保存
        req_doc = {
            "requirement_id": req_id,
            "project_id": project_id,
            "type": type,
            "description": description,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
        }

        req_file = self.design_folder / "requirements" / f"{req_id}.json"
        with open(req_file, "w", encoding="utf-8") as f:
            json.dump(req_doc, f, ensure_ascii=False, indent=2)

        return req_id

    def create_design(
        self, project_id: str, design_type: str, content: Dict[str, Any]
    ) -> str:
        """設計書作成"""
        design_id = f"des_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO designs (design_id, project_id, type, content)
                VALUES (?, ?, ?, ?)
            """,
                (design_id, project_id, design_type, json.dumps(content)),
            )
            conn.commit()

        # 設計書ファイルとして保存
        design_file = self.design_folder / "designs" / f"{design_id}.json"
        with open(design_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "design_id": design_id,
                    "project_id": project_id,
                    "type": design_type,
                    "content": content,
                    "created_at": datetime.now().isoformat(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        return design_id

    def create_development_task(
        self,
        project_id: str,
        design_id: Optional[str],
        name: str,
        description: str,
        assigned_worker: str = "task_worker",
    ) -> str:
        """開発タスク作成"""
        dev_task_id = f"dev_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO development_tasks
                (dev_task_id, project_id, design_id, name, description, assigned_worker)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    dev_task_id,
                    project_id,
                    design_id,
                    name,
                    description,
                    assigned_worker,
                ),
            )
            conn.commit()

        return dev_task_id

    def update_task_status(
        self, dev_task_id: str, status: str, result: Optional[Dict[str, Any]] = None
    ):
        """タスクステータス更新"""
        with sqlite3.connect(self.db_path) as conn:
            if status == "completed":
                conn.execute(
                    """
                    UPDATE development_tasks
                    SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE dev_task_id = ?
                """,
                    (status, json.dumps(result) if result else None, dev_task_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE development_tasks
                    SET status = ?, result = ?
                    WHERE dev_task_id = ?
                """,
                    (status, json.dumps(result) if result else None, dev_task_id),
                )
            conn.commit()

    def record_test_result(
        self,
        project_id: str,
        dev_task_id: Optional[str],
        test_type: str,
        status: str,
        details: Dict[str, Any],
    ):
        """テスト結果記録"""
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO test_results
                (test_id, project_id, dev_task_id, test_type, status, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    test_id,
                    project_id,
                    dev_task_id,
                    test_type,
                    status,
                    json.dumps(details),
                ),
            )
            conn.commit()

        # テスト結果ファイル保存
        test_file = self.design_folder / "tests" / f"{test_id}.json"
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "test_id": test_id,
                    "project_id": project_id,
                    "dev_task_id": dev_task_id,
                    "test_type": test_type,
                    "status": status,
                    "details": details,
                    "executed_at": datetime.now().isoformat(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def update_phase_status(
        self, project_id: str, phase: str, status: str, notes: str = ""
    ):
        """フェーズステータス更新"""
        with sqlite3.connect(self.db_path) as conn:
            if status == "in_progress":
                conn.execute(
                    """
                    UPDATE phase_progress
                    SET status = ?, started_at = CURRENT_TIMESTAMP, notes = ?
                    WHERE project_id = ? AND phase = ?
                """,
                    (status, notes, project_id, phase),
                )
            elif status == "completed":
                conn.execute(
                    """
                    UPDATE phase_progress
                    SET status = ?, completed_at = CURRENT_TIMESTAMP, notes = ?
                    WHERE project_id = ? AND phase = ?
                """,
                    (status, notes, project_id, phase),
                )
            else:
                conn.execute(
                    """
                    UPDATE phase_progress
                    SET status = ?, notes = ?
                    WHERE project_id = ? AND phase = ?
                """,
                    (status, notes, project_id, phase),
                )
            conn.commit()

    def add_project_file(
        self, project_id: str, file_path: str, file_type: str, phase: str
    ):
        """プロジェクトファイル登録"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO project_files (project_id, file_path, file_type, phase)
                VALUES (?, ?, ?, ?)
            """,
                (project_id, file_path, file_type, phase),
            )
            conn.commit()

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """プロジェクトステータス取得"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # プロジェクト基本情報
            project = conn.execute(
                """
                SELECT * FROM projects WHERE project_id = ?
            """,
                (project_id,),
            ).fetchone()

            if not project:
                return {}

            # フェーズ進捗
            phases = conn.execute(
                """
                SELECT * FROM phase_progress
                WHERE project_id = ?
                ORDER BY
                    CASE phase
                        WHEN 'planning' THEN 1
                        WHEN 'design' THEN 2
                        WHEN 'development' THEN 3
                        WHEN 'testing' THEN 4
                        WHEN 'deployment' THEN 5
                    END
            """,
                (project_id,),
            ).fetchall()

            # 開発タスク
            tasks = conn.execute(
                """
                SELECT * FROM development_tasks
                WHERE project_id = ?
                ORDER BY created_at DESC
            """,
                (project_id,),
            ).fetchall()

            # テスト結果サマリー
            test_summary = conn.execute(
                """
                SELECT
                    test_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM test_results
                WHERE project_id = ?
                GROUP BY test_type
            """,
                (project_id,),
            ).fetchall()

            return {
                "project": dict(project),
                "phases": [dict(p) for p in phases],
                "tasks": [dict(t) for t in tasks],
                "test_summary": [dict(t) for t in test_summary],
                "current_phase": self._get_current_phase(phases),
            }

    def _get_current_phase(self, phases: List[sqlite3.Row]) -> str:
        """現在のフェーズを判定"""
        for phase in phases:
            if phase["status"] == "in_progress":
                return phase["phase"]
        return "completed"

    def generate_project_report(self, project_id: str) -> str:
        """プロジェクトレポート生成"""
        status = self.get_project_status(project_id)
        if not status:
            return "プロジェクトが見つかりません"

        project = status["project"]
        report = f"""
# プロジェクトレポート: {project['name']}

## 概要
- **プロジェクトID**: {project['project_id']}
- **タスクID**: {project['task_id']}
- **説明**: {project['description']}
- **ステータス**: {project['status']}
- **作成日時**: {project['created_at']}

## フェーズ進捗
"""

        for phase in status["phases"]:
            status_icon = (
                "✅"
                if phase["status"] == "completed"
                else "🔄"
                if phase["status"] == "in_progress"
                else "⏳"
            )
            report += f"- **{phase['phase'].title()}**: {status_icon} {phase['status']}"
            if phase["started_at"]:
                report += f" (開始: {phase['started_at']})"
            if phase["completed_at"]:
                report += f" (完了: {phase['completed_at']})"
            report += "\n"

        report += "\n## 開発タスク\n"
        for task in status["tasks"]:
            status_icon = (
                "✅"
                if task["status"] == "completed"
                else "❌"
                if task["status"] == "failed"
                else "🔄"
            )
            report += f"- {status_icon} **{task['name']}** ({task['status']})\n"

        if status["test_summary"]:
            report += "\n## テスト結果\n"
            for test in status["test_summary"]:
                report += f"- **{test['test_type']}**: {test['passed']}/{test['total']} passed"
                if test["failed"] > 0:
                    report += f" ({test['failed']} failed)"
                report += "\n"

        return report


# 使用例
if __name__ == "__main__":
    manager = ProjectDesignManager()

    # プロジェクト作成例
    project_id = manager.create_project(
        task_id="code_20250102_123456", name="新規API開発", description="ユーザー管理APIの開発"
    )

    # 要件定義
    manager.add_requirement(
        project_id=project_id,
        type="functional",
        description="ユーザー登録機能",
        priority="high",
    )

    # 設計書作成
    design_id = manager.create_design(
        project_id=project_id,
        design_type="api",
        content={
            "endpoints": [
                {"method": "POST", "path": "/users", "description": "ユーザー作成"},
                {"method": "GET", "path": "/users/{id}", "description": "ユーザー取得"},
            ],
            "database": {
                "table": "users",
                "columns": ["id", "name", "email", "created_at"],
            },
        },
    )

    # レポート生成
    print(manager.generate_project_report(project_id))
