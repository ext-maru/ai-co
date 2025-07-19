"""
タスク賢者 (Task Sage)
プロジェクト管理、タスク追跡、進捗管理を提供
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ..base_sage import BaseSage


class TaskStatus(Enum):
    """タスクステータス"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """タスク優先度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskSage(BaseSage):
    """タスク賢者 - プロジェクト管理とタスク追跡"""

    def __init__(self, data_path: str = "data/tasks"):
        super().__init__("Task")

        self.data_path = data_path
        self.db_path = os.path.join(data_path, "tasks.db")

        # データベース初期化
        self._init_database()

        # タスクカテゴリ
        self.categories = [
            "development",
            "bug_fix",
            "feature",
            "documentation",
            "testing",
            "deployment",
            "maintenance",
            "research",
        ]

        self.logger.info("Task Sage ready for project management")

    def _init_database(self):
        """タスクデータベースの初期化"""
        os.makedirs(self.data_path, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # タスクテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    category TEXT NOT NULL DEFAULT 'general',
                    assignee TEXT,
                    estimateHours INTEGER,
                    actualHours INTEGER DEFAULT 0,
                    parent_task_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_date TIMESTAMP,
                    completed_at TIMESTAMP,
                    tags TEXT,
                    metadata TEXT,
                    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
                )
            """
            )

            # タスク依存関係テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    depends_on_task_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id),
                    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id),
                    UNIQUE(task_id, depends_on_task_id)
                )
            """
            )

            # タスクログテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """
            )

            # プロジェクトテーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """
            )

            # プロジェクトタスク関連テーブル
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_tasks (
                    project_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (task_id) REFERENCES tasks(id),
                    PRIMARY KEY (project_id, task_id)
                )
            """
            )

            # インデックス作成
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_priority ON tasks(priority)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_category ON tasks(category)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_assignee ON tasks(assignee)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_due_date ON tasks(due_date)"
            )

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスク賢者のリクエスト処理"""
        start_time = datetime.now()

        try:
            request_type = request.get("type", "unknown")

            if request_type == "create_task":
                result = await self._create_task(request)
            elif request_type == "update_task":
                result = await self._update_task(request)
            elif request_type == "get_task":
                result = await self._get_task(request)
            elif request_type == "list_tasks":
                result = await self._list_tasks(request)
            elif request_type == "delete_task":
                result = await self._delete_task(request)
            elif request_type == "create_project":
                result = await self._create_project(request)
            elif request_type == "get_project_status":
                result = await self._get_project_status(request)
            elif request_type == "add_dependency":
                result = await self._add_dependency(request)
            elif request_type == "get_schedule":
                result = await self._get_schedule(request)
            elif request_type == "get_analytics":
                result = await self._get_analytics(request)
            elif request_type == "bulk_update":
                result = await self._bulk_update(request)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "supported_types": [
                        "create_task",
                        "update_task",
                        "get_task",
                        "list_tasks",
                        "delete_task",
                        "create_project",
                        "get_project_status",
                        "add_dependency",
                        "get_schedule",
                        "get_analytics",
                        "bulk_update",
                    ],
                }

            # 処理時間を計算
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            result["processing_time_ms"] = processing_time

            await self.log_request(request, result)
            return result

        except Exception as e:
            await self.log_error(e, {"request": request})
            return {"success": False, "error": str(e), "sage": self.sage_name}

    async def _create_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """新規タスク作成"""
        title = request.get("title", "")
        description = request.get("description", "")
        status = request.get("status", TaskStatus.PENDING.value)
        priority = request.get("priority", TaskPriority.MEDIUM.value)
        category = request.get("category", "general")
        assignee = request.get("assignee")
        estimate_hours = request.get("estimateHours")
        parent_task_id = request.get("parentTaskId")
        due_date = request.get("dueDate")
        tags = request.get("tags", [])
        metadata = request.get("metadata", {})

        if not title:
            return {"success": False, "error": "Task title is required"}

        task_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # タスク作成
            cursor.execute(
                """
                INSERT INTO tasks
                (id, title, description, status, priority, category, assignee,
                 estimateHours, parent_task_id, due_date, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    title,
                    description,
                    status,
                    priority,
                    category,
                    assignee,
                    estimate_hours,
                    parent_task_id,
                    due_date,
                    json.dumps(tags),
                    json.dumps(metadata),
                ),
            )

            # ログ記録
            cursor.execute(
                """
                INSERT INTO task_logs (task_id, action, new_value, user_id)
                VALUES (?, 'created', ?, ?)
            """,
                (task_id, json.dumps({"title": title, "status": status}), assignee),
            )

        return {
            "success": True,
            "task_id": task_id,
            "message": "Task created successfully",
        }

    async def _update_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスク更新"""
        task_id = request.get("task_id")
        updates = request.get("updates", {})
        user_id = request.get("user_id")

        if not task_id:
            return {"success": False, "error": "Task ID is required"}

        allowed_fields = [
            "title",
            "description",
            "status",
            "priority",
            "category",
            "assignee",
            "estimateHours",
            "actualHours",
            "due_date",
            "tags",
            "metadata",
        ]

        update_fields = []
        params = []
        logs = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 既存データ取得
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            existing_task = cursor.fetchone()

            if not existing_task:
                return {"success": False, "error": "Task not found"}

            # 更新フィールド処理
            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")

                    if field in ["tags", "metadata"] and isinstance(
                        value, (list, dict)
                    ):
                        params.append(json.dumps(value))
                    else:
                        params.append(value)

                    # ログ用の古い値を記録
                    old_value = existing_task[allowed_fields.index(field) + 1]  # id以外から
                    logs.append((field, old_value, value))

            if not update_fields:
                return {"success": False, "error": "No valid fields to update"}

            # ステータス変更時の特別処理
            if "status" in updates and updates["status"] == TaskStatus.COMPLETED.value:
                update_fields.append("completed_at = ?")
                params.append(datetime.now().isoformat())

            params.append(datetime.now().isoformat())  # updated_at
            params.append(task_id)

            # タスク更新
            cursor.execute(
                f"""
                UPDATE tasks
                SET {', '.join(update_fields)}, updated_at = ?
                WHERE id = ?
            """,
                params,
            )

            # ログ記録
            for field, old_value, new_value in logs:
                cursor.execute(
                    """
                    INSERT INTO task_logs (task_id, action, old_value, new_value, user_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        task_id,
                        f"updated_{field}",
                        str(old_value),
                        str(new_value),
                        user_id,
                    ),
                )

        return {
            "success": True,
            "message": "Task updated successfully",
            "updated_fields": list(updates.keys()),
        }

    async def _get_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスク詳細取得"""
        task_id = request.get("task_id")

        if not task_id:
            return {"success": False, "error": "Task ID is required"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # タスク詳細取得
            cursor.execute(
                """
                SELECT * FROM tasks WHERE id = ?
            """,
                (task_id,),
            )

            task_row = cursor.fetchone()
            if not task_row:
                return {"success": False, "error": "Task not found"}

            # カラム名取得
            columns = [description[0] for description in cursor.description]
            task = dict(zip(columns, task_row))

            # JSON フィールドをパース
            if task.get("tags"):
                task["tags"] = json.loads(task["tags"])
            if task.get("metadata"):
                task["metadata"] = json.loads(task["metadata"])

            # 依存関係取得
            cursor.execute(
                """
                SELECT t.id, t.title, t.status
                FROM task_dependencies td
                JOIN tasks t ON td.depends_on_task_id = t.id
                WHERE td.task_id = ?
            """,
                (task_id,),
            )
            dependencies = [
                {"id": row[0], "title": row[1], "status": row[2]}
                for row in cursor.fetchall()
            ]

            # サブタスク取得
            cursor.execute(
                """
                SELECT id, title, status, priority
                FROM tasks
                WHERE parent_task_id = ?
            """,
                (task_id,),
            )
            subtasks = [
                {"id": row[0], "title": row[1], "status": row[2], "priority": row[3]}
                for row in cursor.fetchall()
            ]

            task["dependencies"] = dependencies
            task["subtasks"] = subtasks

        return {"success": True, "task": task}

    async def _list_tasks(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスク一覧取得"""
        filters = request.get("filters", {})
        sort_by = request.get("sort_by", "created_at")
        sort_order = request.get("sort_order", "DESC")
        limit = request.get("limit", 50)
        offset = request.get("offset", 0)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # WHERE句構築
            where_conditions = []
            params = []

            for field, value in filters.items():
                if field in ["status", "priority", "category", "assignee"]:
                    where_conditions.append(f"{field} = ?")
                    params.append(value)
                elif field == "due_date_range":
                    if "start" in value:
                        where_conditions.append("due_date >= ?")
                        params.append(value["start"])
                    if "end" in value:
                        where_conditions.append("due_date <= ?")
                        params.append(value["end"])

            where_clause = (
                " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            # クエリ実行
            query = f"""
                SELECT * FROM tasks
                {where_clause}
                ORDER BY {sort_by} {sort_order}
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cursor.execute(query, params)
            task_rows = cursor.fetchall()

            # カラム名取得
            columns = [description[0] for description in cursor.description]

            tasks = []
            for row in task_rows:
                task = dict(zip(columns, row))

                # JSON フィールドをパース
                if task.get("tags"):
                    task["tags"] = json.loads(task["tags"])
                if task.get("metadata"):
                    task["metadata"] = json.loads(task["metadata"])

                tasks.append(task)

            # 総数取得
            count_query = f"SELECT COUNT(*) FROM tasks{where_clause}"
            cursor.execute(count_query, params[:-2])  # limit, offsetを除く
            total_count = cursor.fetchone()[0]

        return {
            "success": True,
            "tasks": tasks,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    async def _delete_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスク削除"""
        task_id = request.get("task_id")
        user_id = request.get("user_id")

        if not task_id:
            return {"success": False, "error": "Task ID is required"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # タスク存在確認
            cursor.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()

            if not task:
                return {"success": False, "error": "Task not found"}

            # ログ記録
            cursor.execute(
                """
                INSERT INTO task_logs (task_id, action, old_value, user_id)
                VALUES (?, 'deleted', ?, ?)
            """,
                (task_id, json.dumps({"title": task[0]}), user_id),
            )

            # 関連データ削除
            cursor.execute(
                "DELETE FROM task_dependencies WHERE task_id = ? OR depends_on_task_id = ?",
                (task_id, task_id),
            )
            cursor.execute("DELETE FROM project_tasks WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

        return {"success": True, "message": "Task deleted successfully"}

    async def _create_project(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """プロジェクト作成"""
        name = request.get("name", "")
        description = request.get("description", "")
        start_date = request.get("start_date")
        end_date = request.get("end_date")
        metadata = request.get("metadata", {})

        if not name:
            return {"success": False, "error": "Project name is required"}

        project_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO projects (id, name, description, start_date, end_date, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    project_id,
                    name,
                    description,
                    start_date,
                    end_date,
                    json.dumps(metadata),
                ),
            )

        return {
            "success": True,
            "project_id": project_id,
            "message": "Project created successfully",
        }

    async def _get_project_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """プロジェクト状況取得"""
        project_id = request.get("project_id")

        if not project_id:
            return {"success": False, "error": "Project ID is required"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # プロジェクト情報取得
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project_row = cursor.fetchone()

            if not project_row:
                return {"success": False, "error": "Project not found"}

            # プロジェクトタスク統計
            cursor.execute(
                """
                SELECT
                    t.status,
                    COUNT(*) as count,
                    COALESCE(SUM(t.estimateHours), 0) as estimated_hours,
                    COALESCE(SUM(t.actualHours), 0) as actual_hours
                FROM project_tasks pt
                JOIN tasks t ON pt.task_id = t.id
                WHERE pt.project_id = ?
                GROUP BY t.status
            """,
                (project_id,),
            )

            status_stats = {}
            total_estimated = 0
            total_actual = 0

            for row in cursor.fetchall():
                status, count, estimated, actual = row
                status_stats[status] = {
                    "count": count,
                    "estimated_hours": estimated,
                    "actual_hours": actual,
                }
                total_estimated += estimated
                total_actual += actual

            # 進捗計算
            completed_count = status_stats.get(TaskStatus.COMPLETED.value, {}).get(
                "count", 0
            )
            total_count = sum(stat["count"] for stat in status_stats.values())
            progress = (completed_count / total_count * 100) if total_count > 0 else 0

        return {
            "success": True,
            "project_id": project_id,
            "status_statistics": status_stats,
            "progress_percentage": round(progress, 2),
            "total_estimated_hours": total_estimated,
            "total_actual_hours": total_actual,
            "efficiency": round((total_estimated / total_actual * 100), 2)
            if total_actual > 0
            else 0,
        }

    async def _add_dependency(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスク依存関係追加"""
        task_id = request.get("task_id")
        depends_on_task_id = request.get("depends_on_task_id")

        if not task_id or not depends_on_task_id:
            return {
                "success": False,
                "error": "Both task_id and depends_on_task_id are required",
            }

        if task_id == depends_on_task_id:
            return {"success": False, "error": "Task cannot depend on itself"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 両方のタスクが存在するかチェック
            cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE id IN (?, ?)",
                (task_id, depends_on_task_id),
            )
            if cursor.fetchone()[0] != 2:
                return {"success": False, "error": "One or both tasks not found"}

            # 既存の依存関係チェック
            cursor.execute(
                """
                SELECT COUNT(*) FROM task_dependencies
                WHERE task_id = ? AND depends_on_task_id = ?
            """,
                (task_id, depends_on_task_id),
            )

            if cursor.fetchone()[0] > 0:
                return {"success": False, "error": "Dependency already exists"}

            # 循環依存チェック（簡易版）
            cursor.execute(
                """
                SELECT COUNT(*) FROM task_dependencies
                WHERE task_id = ? AND depends_on_task_id = ?
            """,
                (depends_on_task_id, task_id),
            )

            if cursor.fetchone()[0] > 0:
                return {"success": False, "error": "Circular dependency detected"}

            # 依存関係追加
            cursor.execute(
                """
                INSERT INTO task_dependencies (task_id, depends_on_task_id)
                VALUES (?, ?)
            """,
                (task_id, depends_on_task_id),
            )

        return {"success": True, "message": "Dependency added successfully"}

    async def _get_schedule(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """スケジュール取得"""
        start_date = request.get("start_date")
        end_date = request.get("end_date")
        assignee = request.get("assignee")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            where_conditions = ["due_date IS NOT NULL"]
            params = []

            if start_date:
                where_conditions.append("due_date >= ?")
                params.append(start_date)

            if end_date:
                where_conditions.append("due_date <= ?")
                params.append(end_date)

            if assignee:
                where_conditions.append("assignee = ?")
                params.append(assignee)

            where_clause = " AND ".join(where_conditions)

            cursor.execute(
                f"""
                SELECT id, title, status, priority, assignee, due_date, estimateHours
                FROM tasks
                WHERE {where_clause}
                ORDER BY due_date ASC
            """,
                params,
            )

            tasks = []
            for row in cursor.fetchall():
                tasks.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "status": row[2],
                        "priority": row[3],
                        "assignee": row[4],
                        "due_date": row[5],
                        "estimate_hours": row[6],
                    }
                )

        return {
            "success": True,
            "schedule": tasks,
            "period": {"start_date": start_date, "end_date": end_date},
        }

    async def _get_analytics(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスク分析データ取得"""
        period_days = request.get("period_days", 30)

        start_date = (datetime.now() - timedelta(days=period_days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 完了タスク統計
            cursor.execute(
                """
                SELECT
                    COUNT(*) as completed_count,
                    AVG(actualHours) as avg_actual_hours,
                    AVG(estimateHours) as avg_estimated_hours
                FROM tasks
                WHERE status = 'completed' AND completed_at >= ?
            """,
                (start_date,),
            )

            completed_stats = cursor.fetchone()

            # カテゴリ別統計
            cursor.execute(
                """
                SELECT category, COUNT(*) as count
                FROM tasks
                WHERE created_at >= ?
                GROUP BY category
                ORDER BY count DESC
            """,
                (start_date,),
            )

            category_stats = cursor.fetchall()

            # 優先度別統計
            cursor.execute(
                """
                SELECT priority, COUNT(*) as count
                FROM tasks
                WHERE created_at >= ?
                GROUP BY priority
                ORDER BY
                    CASE priority
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END
            """,
                (start_date,),
            )

            priority_stats = cursor.fetchall()

            # 担当者別統計
            cursor.execute(
                """
                SELECT
                    assignee,
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
                FROM tasks
                WHERE assignee IS NOT NULL AND created_at >= ?
                GROUP BY assignee
                ORDER BY total_tasks DESC
            """,
                (start_date,),
            )

            assignee_stats = cursor.fetchall()

        analytics = {
            "period_days": period_days,
            "completed_tasks": {
                "count": completed_stats[0] or 0,
                "avg_actual_hours": round(completed_stats[1] or 0, 2),
                "avg_estimated_hours": round(completed_stats[2] or 0, 2),
            },
            "category_distribution": [
                {"category": cat, "count": count} for cat, count in category_stats
            ],
            "priority_distribution": [
                {"priority": priority, "count": count}
                for priority, count in priority_stats
            ],
            "assignee_performance": [
                {
                    "assignee": assignee,
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "completion_rate": round((completed / total * 100), 2)
                    if total > 0
                    else 0,
                }
                for assignee, total, completed in assignee_stats
            ],
        }

        return {"success": True, "analytics": analytics}

    async def _bulk_update(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """一括更新"""
        task_ids = request.get("task_ids", [])
        updates = request.get("updates", {})
        user_id = request.get("user_id")

        if not task_ids:
            return {"success": False, "error": "Task IDs are required"}

        if not updates:
            return {"success": False, "error": "Updates are required"}

        allowed_fields = ["status", "priority", "assignee", "category"]
        update_fields = []
        params = []

        for field, value in updates.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)

        if not update_fields:
            return {"success": False, "error": "No valid fields to update"}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # バルク更新
            placeholders = ",".join(["?"] * len(task_ids))
            params.extend([datetime.now().isoformat()])
            params.extend(task_ids)

            cursor.execute(
                f"""
                UPDATE tasks
                SET {', '.join(update_fields)}, updated_at = ?
                WHERE id IN ({placeholders})
            """,
                params,
            )

            updated_count = cursor.rowcount

            # ログ記録
            for task_id in task_ids:
                cursor.execute(
                    """
                    INSERT INTO task_logs (task_id, action, new_value, user_id)
                    VALUES (?, 'bulk_updated', ?, ?)
                """,
                    (task_id, json.dumps(updates), user_id),
                )

        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Updated {updated_count} tasks",
        }

    def get_capabilities(self) -> List[str]:
        """タスク賢者の能力一覧"""
        return [
            "create_task",
            "update_task",
            "get_task",
            "list_tasks",
            "delete_task",
            "create_project",
            "get_project_status",
            "add_dependency",
            "get_schedule",
            "get_analytics",
            "bulk_update",
            "task_management",
            "project_tracking",
            "dependency_management",
        ]
