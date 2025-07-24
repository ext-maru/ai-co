"""
📋 Task Sage Business Logic - Elder Loop対応
TaskSageSoulからビジネスロジックを分離抽出

Knowledge Sageパターンを適用した完全分離アーキテクチャ
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path
import json
from uuid import uuid4

# Task models import path adjustment
import sys
sys.path.append("/home/aicompany/ai_co/elders_guild/src")
from task_sage.abilities.task_models import (
    Task, TaskStatus, TaskPriority, TaskSpec, TaskUpdate,
    Project, ProjectSpec, ProjectPlan,
    EffortEstimate, ProgressReport, DependencyGraph,
    Milestone, ValidationResult
)

logger = logging.getLogger(__name__)


class TaskProcessor:
    pass


"""
    📋 Task Sage Pure Business Logic Processor
    
    フレームワーク非依存の純粋なタスク管理ビジネスロジック
    Knowledge Sageパターンに準拠した分離設計
    """
        """TaskProcessor初期化"""
        # インメモリストレージ（将来的にはデータベース対応）
        self.tasks: Dict[str, Task] = {}
        self.projects: Dict[str, Project] = {}
        
        # 工数見積もりパラメータ
        self.estimation_factors = {
            "base_hours_per_loc": 0.01,  # 1行あたりの基本時間
            "complexity_multipliers": {
                "low": 1.0,
                "medium": 1.5,
                "high": 2.5,
                "critical": 4.0
            },
            "overhead_factors": {
                "analysis": 0.2,      # 分析時間（全体の20%）
                "testing": 0.3,       # テスト時間（全体の30%）
                "documentation": 0.1, # ドキュメント時間（全体の10%）
                "review": 0.15        # レビュー時間（全体の15%）
            }
        }
        
        logger.info("TaskProcessor initialized")
    
    async def process_action(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        アクション処理の統一エントリーポイント
        
        Args:
            action: 実行するアクション名
            data: アクションパラメータ
            
        Returns:
            処理結果辞書
        """
        try:
            # アクション別処理分岐
            if action == "create_task":
                return await self._create_task(data)
            elif action == "get_task":
                return await self._get_task(data)
            elif action == "update_task":
                return await self._update_task(data)
            elif action == "delete_task":
                return await self._delete_task(data)
            elif action == "list_tasks":
                return await self._list_tasks(data)
            elif action == "search_tasks":
                return await self._search_tasks(data)
            elif action == "estimate_effort":
                return await self._estimate_effort(data)
            elif action == "resolve_dependencies":
                return await self._resolve_dependencies(data)
            elif action == "create_project":
                return await self._create_project(data)
            elif action == "get_project":
                return await self._get_project(data)
            elif action == "list_projects":
                return await self._list_projects(data)
            elif action == "get_statistics":
                return await self._get_statistics(data)
            elif action == "get_task_progress":
                return await self._get_task_progress(data)
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Error processing action {action}: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    # === タスク管理コア機能 ===
    
    async def _create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク作成"""
        try:
            # TaskSpec作成
            priority_value = data.get("priority", TaskPriority.MEDIUM.value)
            if isinstance(priority_value, int):
                # 数値の場合、対応するTaskPriorityを取得
                priority_mapping = {1: TaskPriority.LOW, 2: TaskPriority.MEDIUM, 3: TaskPriority.HIGH, 4: TaskPriority.CRITICAL, 5: TaskPriority.BLOCKER}
                priority = priority_mapping.get(priority_value, TaskPriority.MEDIUM)
            else:
                priority = TaskPriority(priority_value)
            
            task_spec = TaskSpec(
                title=data["title"],
                description=data.get("description", ""),
                estimated_hours=data.get("estimated_hours", 0.0),
                priority=priority,
                tags=data.get("tags", []),
                project_id=data.get("project_id"),
                assignee=data.get("assignee"),
                due_date=data.get("due_date"),
                dependencies=data.get("dependencies", []),
                complexity_factors=data.get("complexity_factors", {})
            )
            
            # Task作成
            task = Task.from_spec(task_spec)
            task.updated_at = datetime.now()
            
            # ストレージに保存
            self.tasks[task.id] = task
            
            logger.info(f"Task created: {task.id} - {task.title}")
            
            return {
                "success": True,
                "data": {
                    "task_id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "estimated_hours": task.estimated_hours,
                    "created_at": task.created_at.isoformat(),
                    "tags": task.tags
                },
                "message": f"タスク '{task.title}' を作成しました"
            }
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise
    
    async def _get_task(self, data: Dict[str, Any]) -> Dict[str, Any]task_id = data.get("task_id"):
    """スク取得""":
        if not task_id:
            raise ValueError("task_id is required")
        
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        return {
            "success": True,
            "data": {
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "priority": task.priority.value,
                "assignee": task.assignee,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "dependencies": task.dependencies,
                "subtasks": task.subtasks,
                "tags": task.tags,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "project_id": task.project_id,
                "complexity_factors": task.complexity_factors
            }
        }
    
    async def _update_task(self, data: Dict[str, Any]) -> Dict[str, Any]task_id = data.get("task_id"):
    """スク更新""":
        if not task_id:
            raise ValueError("task_id is required")
        
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # 更新フィールド適用
        updates = data.get("updates", {})
        
        if "status" in updates:
            try:
                task.status = TaskStatus(updates["status"])
                if task.status == TaskStatus.COMPLETED:
                    task.completed_at = datetime.now()
            except ValueError:
                raise ValueError(f"Invalid status: {updates['status']}")
        
        if "priority" in updates:
            try:
                priority_value = updates["priority"]
                if isinstance(priority_value, int):
                    priority_mapping = {1: TaskPriority.LOW, 2: TaskPriority.MEDIUM, 3: TaskPriority.HIGH, 4: TaskPriority.CRITICAL, 5: TaskPriority.BLOCKER}
                    task.priority = priority_mapping.get(priority_value, TaskPriority.MEDIUM)
                else:
                    task.priority = TaskPriority(priority_value)
            except ValueError:
                raise ValueError(f"Invalid priority: {updates['priority']}")
        
        if "assignee" in updates:
            task.assignee = updates["assignee"]
        
        if "estimated_hours" in updates:
            task.estimated_hours = updates["estimated_hours"]
        
        if "actual_hours" in updates:
            task.actual_hours = updates["actual_hours"]
        
        if "tags" in updates:
            task.tags = updates["tags"]
        
        if "due_date" in updates:
            task.due_date = updates["due_date"]
        
        if "description" in updates:
            task.description = updates["description"]
        
        task.updated_at = datetime.now()
        
        logger.info(f"Task updated: {task_id}")
        
        return {
            "success": True,
            "data": {
                "task_id": task.id,
                "title": task.title,
                "status": task.status.value,
                "updated_at": task.updated_at.isoformat()
            },
            "message": f"タスク '{task.title}' を更新しました"
        }
    
    async def _delete_task(self, data: Dict[str, Any]) -> Dict[str, Any]task_id = data.get("task_id"):
    """スク削除""":
        if not task_id:
            raise ValueError("task_id is required")
        
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # 依存関係チェック（他のタスクがこのタスクに依存していないか）
        dependent_tasks = [
            t for t in self.tasks.values() 
            if task_id in t.dependencies
        ]
        
        if dependent_tasks:
            dependent_titles = [t.title for t in dependent_tasks]
            raise ValueError(f"Cannot delete task: {len(dependent_tasks)} tasks depend on it: {dependent_titles}")
        
        # 削除実行
        title = task.title
        del self.tasks[task_id]
        
        logger.info(f"Task deleted: {task_id} - {title}")
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "title": title
            },
            "message": f"タスク '{title}' を削除しました"
        }
    
    async def _list_tasks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク一覧取得"""
        # フィルタリングオプション
        status_filter = data.get("status")
        project_id_filter = data.get("project_id")
        assignee_filter = data.get("assignee")
        priority_filter = data.get("priority")
        
        # タスクフィルタリング
        filtered_tasks = list(self.tasks.values())
        
        if status_filter:
            filtered_tasks = [t for t in filtered_tasks if t.status.value == status_filter]
        
        if project_id_filter:
            filtered_tasks = [t for t in filtered_tasks if t.project_id == project_id_filter]
        
        if assignee_filter:
            filtered_tasks = [t for t in filtered_tasks if t.assignee == assignee_filter]
        
        if priority_filter:
            filtered_tasks = [t for t in filtered_tasks if t.priority.value == priority_filter]
        
        # ソート（優先度・作成日時）
        filtered_tasks.sort(key=lambda t: (t.priority.value, t.created_at), reverse=True)
        
        # レスポンス作成
        task_summaries = []
        for task in filtered_tasks:
            task_summaries.append({
                "task_id": task.id,
                "title": task.title,
                "status": task.status.value,
                "priority": task.priority.value,
                "assignee": task.assignee,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "created_at": task.created_at.isoformat(),
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "tags": task.tags
            })
        
        return {
            "success": True,
            "data": {
                "tasks": task_summaries,
                "total_count": len(task_summaries),
                "filters_applied": {
                    "status": status_filter,
                    "project_id": project_id_filter,
                    "assignee": assignee_filter,
                    "priority": priority_filter
                }
            }
        }
    
    async def _search_tasks(self, data: Dict[str, Any]) -> Dict[str, Any]query = data.get("query", "").lower().strip():
    """スク検索""":
        if not query:
            raise ValueError("Search query is required")
        
        # 検索実行
        matching_tasks = []
        for task in self.tasks.values():
            # タイトル・説明・タグでの検索
            if (query in task.title.lower() or 
                query in task.description.lower() or
                any(query in tag.lower() for tag in task.tags)):
                matching_tasks.append(task)
        
        # ソート（優先度・関連度）
        matching_tasks.sort(key=lambda t: (t.priority.value, t.created_at), reverse=True)
        
        # レスポンス作成
        search_results = []
        for task in matching_tasks:
            search_results.append({
                "task_id": task.id,
                "title": task.title,
                "description": task.description[:200] + "..." if len(task.description) > 200 else task.description,
                "status": task.status.value,
                "priority": task.priority.value,
                "tags": task.tags,
                "created_at": task.created_at.isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "query": query,
                "results": search_results,
                "total_matches": len(search_results)
            }
        }
    
    # === 工数見積もり・分析機能 ===
    
    async def _estimate_effort(self, data: Dict[str, Any]) -> Dict[str, Any]task_id = data.get("task_id")complexity_factors = data.get("complexity_factors", {})
    """数見積もり"""
        :
        if task_id:
            task = self.tasks.get(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
            complexity_factors = task.complexity_factors
        
        # 基本工数計算
        base_hours = complexity_factors.get("lines_of_code", 1000) * self.estimation_factors["base_hours_per_loc"]
        
        # 複雑度乗数適用
        complexity = complexity_factors.get("complexity", "medium")
        complexity_multiplier = self.estimation_factors["complexity_multipliers"].get(complexity, 1.5)
        implementation_hours = base_hours * complexity_multiplier
        
        # オーバーヘッド計算
        overhead_hours = {}
        total_overhead = 0
        for phase, factor in self.estimation_factors["overhead_factors"].items():
            overhead_hours[phase] = implementation_hours * factor
            total_overhead += overhead_hours[phase]
        
        # 総工数
        total_hours = implementation_hours + total_overhead
        
        # 信頼度計算（複雑度・依存関係数に基づく）
        dependencies_count = len(complexity_factors.get("dependencies", []))
        confidence = max(0.3, 1.0 - (complexity_multiplier - 1.0) * 0.2 - dependencies_count * 0.05)
        confidence = min(confidence, 0.95)
        
        # 詳細内訳
        breakdown = {
            "implementation": implementation_hours,
            **overhead_hours,
            "total": total_hours
        }
        
        estimate = EffortEstimate(
            hours=total_hours,
            confidence=confidence,
            breakdown=breakdown,
            factors=complexity_factors
        )
        
        return {
            "success": True,
            "data": {
                "estimated_hours": estimate.hours,
                "confidence": estimate.confidence,
                "breakdown": estimate.breakdown,
                "complexity_factors": estimate.factors,
                "calculation_details": {
                    "base_hours_per_loc": self.estimation_factors["base_hours_per_loc"],
                    "complexity": complexity,
                    "complexity_multiplier": complexity_multiplier
                }
            }
        }
    
    async def _resolve_dependencies(self, data: Dict[str, Any]) -> Dict[str, Any]task_ids = data.get("task_ids", []):
    """スク依存関係解決（トポロジカルソート）"""
        
        # 指定されたタスクIDがない場合は全タスクを対象:
        if not task_ids:
            target_tasks = list(self.tasks.values())
        else:
            target_tasks = [self.tasks[tid] for tid in task_ids if tid in self.tasks]
        
        if not target_tasks:
            raise ValueError("No valid tasks found for dependency resolution")
        
        # グラフ構築
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        task_map = {task.id: task for task in target_tasks}
        
        for task in target_tasks:
            in_degree[task.id] = 0
        
        for task in target_tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    graph[dep_id].append(task.id)
                    in_degree[task.id] += 1
        
        # トポロジカルソート（Kahn's Algorithm）
        queue = deque([task_id for task_id in in_degree if in_degree[task_id] == 0])
        ordered_task_ids = []
        
        while queue:
            current_id = queue.popleft()
            ordered_task_ids.append(current_id)
            
            for neighbor_id in graph[current_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)
        
        # 循環依存チェック
        if len(ordered_task_ids) != len(target_tasks):
            unresolved = [tid for tid in task_map.keys() if tid not in ordered_task_ids]
            raise ValueError(f"Circular dependency detected among tasks: {unresolved}")
        
        # ソート結果作成
        ordered_tasks = []
        for task_id in ordered_task_ids:
            task = task_map[task_id]
            ordered_tasks.append({
                "task_id": task.id,
                "title": task.title,
                "priority": task.priority.value,
                "estimated_hours": task.estimated_hours,
                "dependencies": task.dependencies,
                "order": len(ordered_tasks) + 1
            })
        
        return {
            "success": True,
            "data": {
                "ordered_tasks": ordered_tasks,
                "total_tasks": len(ordered_tasks),
                "total_estimated_hours": sum(task.estimated_hours for task in target_tasks)
            }
        }
    
    # === プロジェクト管理機能 ===
    
    async def _create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """プロジェクト作成"""
        try:
            project_spec = ProjectSpec(
                name=data["name"],
                description=data.get("description", ""),
                target_completion=data.get("target_completion"),
                resource_constraints=data.get("resource_constraints", {}),
                tags=data.get("tags", [])
            )
            
            project = Project(
                id=str(uuid4()),
                name=project_spec.name,
                description=project_spec.description,
                target_completion=project_spec.target_completion,
                resource_constraints=project_spec.resource_constraints,
                tags=project_spec.tags,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.projects[project.id] = project
            
            logger.info(f"Project created: {project.id} - {project.name}")
            
            return {
                "success": True,
                "data": {
                    "project_id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "created_at": project.created_at.isoformat(),
                    "tags": project.tags
                },
                "message": f"プロジェクト '{project.name}' を作成しました"
            }
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise
    
    async def _get_project(self, data: Dict[str, Any]) -> Dict[str, Any]project_id = data.get("project_id"):
    """ロジェクト取得""":
        if not project_id:
            raise ValueError("project_id is required")
        
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # プロジェクト内タスク取得
        project_tasks = [t for t in self.tasks.values() if t.project_id == project_id]
        task_summaries = []
        for task in project_tasks:
            task_summaries.append({
                "task_id": task.id,
                "title": task.title,
                "status": task.status.value,
                "priority": task.priority.value,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours
            })
        
        return {
            "success": True,
            "data": {
                "project_id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "target_completion": project.target_completion.isoformat() if project.target_completion else None,
                "tags": project.tags,
                "resource_constraints": project.resource_constraints,
                "tasks": task_summaries,
                "task_count": len(task_summaries),
                "total_estimated_hours": sum(t.estimated_hours for t in project_tasks),
                "total_actual_hours": sum(t.actual_hours for t in project_tasks)
            }
        }
    
    async def _list_projects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """プロジェクト一覧取得"""
        projects_list = []
        for project in self.projects.values():
            # プロジェクトのタスク統計
            project_tasks = [t for t in self.tasks.values() if t.project_id == project.id]
            
            projects_list.append({
                "project_id": project.id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
                "target_completion": project.target_completion.isoformat() if project.target_completion else None,
                "tags": project.tags,
                "task_count": len(project_tasks),
                "completed_tasks": len([t for t in project_tasks if t.status == TaskStatus.COMPLETED]),
                "total_estimated_hours": sum(t.estimated_hours for t in project_tasks),
                "total_actual_hours": sum(t.actual_hours for t in project_tasks)
            })
        
        # ソート（作成日時降順）
        projects_list.sort(key=lambda p: p["created_at"], reverse=True)
        
        return {
            "success": True,
            "data": {
                "projects": projects_list,
                "total_count": len(projects_list)
            }
        }
    
    # === 統計・レポート機能 ===
    
    async def _get_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """統計情報取得"""
        # タスク統計
        total_tasks = len(self.tasks)
        status_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        
        total_estimated_hours = 0
        total_actual_hours = 0
        
        for task in self.tasks.values():
            status_counts[task.status.value] += 1
            priority_counts[task.priority.value] += 1
            total_estimated_hours += task.estimated_hours
            total_actual_hours += task.actual_hours
        
        # プロジェクト統計
        total_projects = len(self.projects)
        
        # 時間効率計算
        efficiency = (total_actual_hours / total_estimated_hours * 100) if total_estimated_hours > 0 else 0
        
        # 完了率計算
        completed_tasks = status_counts[TaskStatus.COMPLETED.value]
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "success": True,
            "data": {
                "timestamp": datetime.now().isoformat(),
                "task_statistics": {
                    "total_tasks": total_tasks,
                    "status_breakdown": dict(status_counts),
                    "priority_breakdown": dict(priority_counts),
                    "completion_rate": round(completion_rate, 2)
                },
                "project_statistics": {
                    "total_projects": total_projects
                },
                "time_statistics": {
                    "total_estimated_hours": round(total_estimated_hours, 2),
                    "total_actual_hours": round(total_actual_hours, 2),
                    "efficiency_percentage": round(efficiency, 2)
                },
                "system_health": {
                    "memory_usage": f"{len(self.tasks) + len(self.projects)} objects",
                    "active_processor": "TaskProcessor"
                }
            }
        }
    
    async def _get_task_progress(self, data: Dict[str, Any]) -> Dict[str, Any]project_id = data.get("project_id"):
    """スク進捗レポート"""
        
        # 対象タスク決定:
        if project_id:
            target_tasks = [t for t in self.tasks.values() if t.project_id == project_id]
        else:
            target_tasks = list(self.tasks.values())
        
        if not target_tasks:
            return {
                "success": True,
                "data": {
                    "progress_summary": "No tasks found",
                    "total_tasks": 0
                }
            }
        
        # 進捗計算
        progress_by_status = defaultdict(list)
        for task in target_tasks:
            progress_by_status[task.status.value].append({
                "task_id": task.id,
                "title": task.title,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
                "priority": task.priority.value
            })
        
        # 進捗率計算
        completed_count = len(progress_by_status[TaskStatus.COMPLETED.value])
        in_progress_count = len(progress_by_status[TaskStatus.IN_PROGRESS.value])
        total_count = len(target_tasks)
        
        overall_progress = (completed_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "success": True,
            "data": {
                "progress_summary": {
                    "total_tasks": total_count,
                    "completed_tasks": completed_count,
                    "in_progress_tasks": in_progress_count,
                    "overall_progress_percentage": round(overall_progress, 2)
                },
                "progress_by_status": dict(progress_by_status),
                "project_id": project_id
            }
        }


# === 初期化・テスト支援 ===

async def main():
    pass

            """TaskProcessor動作テスト""" "Task Sage A2A変換",
        "description": "Knowledge Sageパターンを適用してTask SageをA2A対応",
        "estimated_hours": 12.0,
        "priority": TaskPriority.HIGH.value,
        "tags": ["a2a", "elder-loop", "task-sage"],
        "complexity_factors": {
            "lines_of_code": 1500,
            "complexity": "high",
            "dependencies": ["knowledge-sage"]
        }
    })
    
    print(f"✅ Task creation result: {task_result['success']}")
    
    # 統計情報取得
    stats_result = await processor.process_action("get_statistics", {})
    print(f"📊 Statistics: {stats_result['data']['task_statistics']['total_tasks']} tasks")
    
    print("🎉 TaskProcessor業務ロジック動作確認完了！")


if __name__ == "__main__":
    asyncio.run(main())