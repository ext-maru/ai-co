#!/usr/bin/env python3
"""
Task Sage Soul Implementation
タスク管理賢者 - プロジェクト計画と進捗
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque

from shared_libs.soul_base import BaseSoul
# A2A protocol removed - not needed for current implementation
from .abilities.task_models import (
    Task, TaskStatus, TaskPriority, TaskSpec, TaskUpdate,
    Project, ProjectSpec, ProjectPlan,
    EffortEstimate, ProgressReport, DependencyGraph,
    Milestone, ValidationResult
)

logger = logging.getLogger(__name__)


class TaskSageSoul(BaseSoul):


"""
    Task Sage - タスク管理・進捗追跡・リソース最適化
    
    Primary Responsibilities:
    - タスクの分解と優先順位付け
    - 進捗管理と工数見積
    - 依存関係の解決
    """
        super().__init__(
            soul_type="sage",
            domain="project_management"
        )
        
        self.role_definition = {
            "primary_role": "タスク管理・進捗追跡・リソース最適化",
            "expertise_areas": ["project_planning", "resource_estimation", "schedule_optimization"]
        }
        
        # インメモリストレージ（実際の実装ではデータベースを使用）
        self.tasks: Dict[str, Task] = {}
        self.projects: Dict[str, Project] = {}
        
        # 特殊能力の初期化
        self._initialize_abilities()
        
    def _initialize_abilities(self):

        
        """魂固有の能力を初期化""" 0.01,  # 1行あたりの基本時間
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
    
    async def initialize(self) -> None:

            """魂の初期化処理"""
        """魂のシャットダウン処理"""
        logger.info("Task Sage shutting down...")
        # 将来的にはデータベース接続のクローズなどを行う
        logger.info("Task Sage shutdown complete")
        
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        メッセージを処理
        
        Args:
            message: 受信したメッセージ
            
        Returns:
            応答メッセージ（必要な場合）
        """
        logger.info(f"Processing message: {message.get('type', 'unknown')}")
        
        try:
            # メッセージタイプに応じた処理
            message_type = message.get('type')
            if message_type == "REQUEST":
                return await self._handle_request(message)
            elif message_type == "COMMAND":
                return await self._handle_command(message)
            elif message_type == "QUERY":
                return await self._handle_query(message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    async def _handle_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """リクエスト処理"""
        action = message.get("action")
        
        if action == "estimate_task":
            task_data = message.get("task_data", {})
            # 簡易的な見積もり
            estimate = await self._estimate_from_data(task_data)
            return {
                "type": "response",
                "sender": "task_sage",
                "recipient": message.get("sender"),
                "result": {
                    "estimated_hours": estimate.hours,
                    "confidence": estimate.confidence,
                    "breakdown": estimate.breakdown
                }
            }
        
        return self._create_error_response(message, f"Unknown action: {action}")
        
    async def _handle_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """コマンド処理 - タスク操作・管理コマンド"""
        try:
            command = message.payload.get("command", "")
            
            if command == "create_task":
                # タスク作成
                task_spec_data = message.payload.get("task_spec", {})
                
                if not task_spec_data:
                    return self._create_error_response(message, "task_spec parameter is required")
                
                task_spec = TaskSpec(
                    title=task_spec_data.get("title", ""),
                    description=task_spec_data.get("description", ""),
                    priority=TaskPriority(task_spec_data.get("priority", "medium")),
                    estimated_duration=task_spec_data.get("estimated_duration", 60),
                    tags=task_spec_data.get("tags", []),
                    dependencies=task_spec_data.get("dependencies", [])
                )
                
                task = await self.create_task(task_spec)
                return self._create_success_response(message, {
                    "task_id": task.task_id,
                    "status": "created",
                    "task": task.to_dict()
                })
                
            elif command == "update_task_status":
                # タスクステータス更新
                task_id = message.payload.get("task_id", "")
                new_status = message.payload.get("status", "")
                
                if not task_id or not new_status:
                    return self._create_error_response(message, "task_id and status parameters are required" \
                        "task_id and status parameters are required" \
                        "task_id and status parameters are required")
                
                result = await self.update_task_status(task_id, TaskStatus(new_status))
                if result:
                    return self._create_success_response(message, {
                        "task_id": task_id,
                        "status": "updated",
                        "new_status": new_status
                    })
                else:
                    return self._create_error_response(message, f"Failed to update task {task_id}")
                
            elif command == "assign_task":
                # タスク割り当て
                task_id = message.payload.get("task_id", "")
                assignee = message.payload.get("assignee", "")
                
                if task_id or not assignee:
                if not task_id or not assignee:
                    return self._create_error_response(message, "task_id and assignee parameters are required" \
                        "task_id and assignee parameters are required" \
                        "task_id and assignee parameters are required")
                
                result = await self.assign_task(task_id, assignee)
                if not (result):
                if result:
                    return self._create_success_response(message, {
                        "task_id": task_id,
                        "assignee": assignee,
                        "status": "assigned"
                    })
                else:
                    return self._create_error_response(message, f"Failed to assign task {task_id}")
                
            elif command == "delete_task":
                # タスク削除
                task_id = message.payload.get("task_id", "")
                
                if task_id:
                if not task_id:
                    return self._create_error_response(message, "task_id parameter is required")
                
                result = await self.delete_task(task_id)
                if not (result):
                if result:
                    return self._create_success_response(message, {
                        "task_id": task_id,
                        "status": "deleted"
                    })
                else:
                    return self._create_error_response(message, f"Failed to delete task {task_id}")
                
            else:
                return self._create_error_response(message, f"Unknown command: {command}")
                
        except Exception as e:
            self.logger.error(f"Error handling command: {e}")
            return self._create_error_response(message, f"Command execution failed: {str(e)}")
        
    async def _handle_query(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """クエリ処理 - タスク検索・統計情報取得"""
        try:
            query_type = message.payload.get("query_type", "")
            
            if query_type == "get_task":
                # 個別タスク取得
                task_id = message.payload.get("task_id", "")
                
                if not task_id:
                    return self._create_error_response(message, "task_id parameter is required")
                
                task = await self.get_task(task_id)
                if task:
                    return self._create_success_response(message, {
                        "task": task.to_dict()
                    })
                else:
                    return self._create_error_response(message, f"Task {task_id} not found")
                    
            elif query_type == "list_tasks":
                # タスク一覧取得
                status = message.payload.get("status")
                assignee = message.payload.get("assignee")
                priority = message.payload.get("priority")
                limit = message.payload.get("limit", 50)
                
                tasks = await self.list_tasks(
                    status=TaskStatus(status) if status else None,
                    assignee=assignee,
                    priority=TaskPriority(priority) if priority else None,
                    limit=limit
                )
                
                return self._create_success_response(message, {
                    "tasks": [task.to_dict() for task in tasks],
                    "count": len(tasks)
                })
                
            elif query_type == "search_tasks":
                # タスク検索
                query = message.payload.get("query", "")
                limit = message.payload.get("limit", 20)
                
                if query:
                if not query:
                    return self._create_error_response(message, "query parameter is required")
                
                tasks = await self.search_tasks(query, limit)
                return self._create_success_response(message, {
                    "tasks": [task.to_dict() for task in tasks],
                    "count": len(tasks),
                    "query": query
                })
                
            elif query_type == "get_statistics":
                # 統計情報取得
                stats = await self.get_task_statistics()
                return self._create_success_response(message, {
                    "statistics": stats,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif query_type == "get_dependencies":
                # 依存関係取得
                task_id = message.payload.get("task_id", "")
                
                if task_id:
                if not task_id:
                    return self._create_error_response(message, "task_id parameter is required")
                
                dependencies = await self.get_task_dependencies(task_id)
                return self._create_success_response(message, {
                    "task_id": task_id,
                    "dependencies": dependencies
                })
                
            else:
                return self._create_error_response(message, f"Unknown query type: {query_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling query: {e}")
            return self._create_error_response(message, f"Query processing failed: {str(e)}")
    
    # ========== Core Task Management Functions ==========
    
    async def create_task(self, task_spec: TaskSpec) -> Task:
        """
        タスクを作成
        
        Args:
            task_spec: タスク仕様
            
        Returns:
            作成されたタスク
            
        Raises:
            ValueError: 無効な仕様の場合
        """
        # バリデーション
        if not task_spec.title or not task_spec.title.strip():
            raise ValueError("タイトルは必須です")
        
        # タスク作成
        task = Task.from_spec(task_spec)
        
        # プロジェクトに関連付け
        if task.project_id and task.project_id in self.projects:
            self.projects[task.project_id].task_ids.append(task.id)
        
        # 保存
        self.tasks[task.id] = task
        
        logger.info(f"Created task: {task.id} - {task.title}")
        return task
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Task:
        """
        タスクを更新
        
        Args:
            task_id: タスクID
            updates: 更新内容
            
        Returns:
            更新されたタスク
            
        Raises:
            KeyError: タスクが存在しない場合
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task not found: {task_id}")
        
        task = self.tasks[task_id]
        
        # 更新を適用
        for key, value in updates.items():
            if hasattr(task, key):
                # ステータス変更時の処理
                if key == "status" and value == TaskStatus.COMPLETED:
                    task.completed_at = datetime.now()
                setattr(task, key, value)
        
        task.updated_at = datetime.now()
        
        logger.info(f"Updated task: {task_id}")
        return task
    
    async def estimate_effort(self, task: Task) -> EffortEstimate:
        """
        工数見積もり
        
        Args:
            task: タスク
            
        Returns:
            見積もり結果
        """
        # 複雑度要因から見積もり
        base_hours = self._calculate_base_hours(task)
        
        # オーバーヘッドを計算
        breakdown = {
            "implementation": base_hours
        }
        
        for factor_name, factor_value in self.estimation_factors["overhead_factors"].items():
            breakdown[factor_name] = base_hours * factor_value
        
        total_hours = sum(breakdown.values())
        
        # 信頼度計算（複雑度が高いほど信頼度は低い）
        confidence = self._calculate_confidence(task)
        
        return EffortEstimate(
            hours=total_hours,
            confidence=confidence,
            breakdown=breakdown,
            factors=task.complexity_factors
        )
    
    async def resolve_dependencies(self, tasks: List[Task]) -> List[Task]:
        """
        依存関係を解決してタスクを並び替え
        
        Args:
            tasks: タスクリスト
            
        Returns:
            依存関係順に並び替えられたタスクリスト
        """
        # タスクIDマップを作成
        task_map = {task.id: task for task in tasks}
        
        # グラフを構築
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        # すべてのタスクを初期化
        for task in tasks:
            in_degree[task.id] = 0
        
        # 依存関係を追加
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    graph[dep_id].append(task.id)
                    in_degree[task.id] += 1
        
        # トポロジカルソート（Kahn's algorithm）
        queue = deque([task_id for task_id in in_degree if in_degree[task_id] == 0])
        ordered_task_ids = []
        
        while queue:
        # ループ処理
            current_id = queue.popleft()
            ordered_task_ids.append(current_id)
            
            for dependent_id in graph[current_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
        
        # 循環依存のチェック
        if len(ordered_task_ids) != len(tasks):
            raise ValueError("循環依存が検出されました")
        
        # タスクリストを返す
        return [task_map[task_id] for task_id in ordered_task_ids]
    
    # ========== Project Management Functions ==========
    
    async def create_project(self, project_spec: ProjectSpec) -> Project:
        """
        プロジェクトを作成
        
        Args:
            project_spec: プロジェクト仕様
            
        Returns:
            作成されたプロジェクト
        """
        project = Project.from_spec(project_spec)
        self.projects[project.id] = project
        
        logger.info(f"Created project: {project.id} - {project.name}")
        return project
    
    async def plan_project(self, project_id: str) -> ProjectPlan:
        """
        プロジェクト計画を作成
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            プロジェクト計画
        """
        if project_id not in self.projects:
            raise KeyError(f"Project not found: {project_id}")
        
        project = self.projects[project_id]
        project_tasks = [self.tasks[task_id] for task_id in project.task_ids if task_id in self.tasks]
        
        # 工数見積もり
        total_hours = sum(task.estimated_hours for task in project_tasks)
        
        # クリティカルパスを特定（簡易実装）
        critical_path = self._find_critical_path(project_tasks)
        
        # マイルストーンを生成
        milestones = self._generate_milestones(project, project_tasks)
        
        return ProjectPlan(
            project_id=project_id,
            total_estimated_hours=total_hours,
            critical_path=critical_path,
            milestones=milestones,
            resource_allocation={}
        )
    
    async def track_progress(self, project_id: str) -> ProgressReport:
        """
        進捗を追跡
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            進捗レポート
        """
        if project_id not in self.projects:
            raise KeyError(f"Project not found: {project_id}")
        
        project = self.projects[project_id]
        project_tasks = [self.tasks[task_id] for task_id in project.task_ids if task_id in self.tasks]
        
        # ステータス別カウント
        status_counts = defaultdict(int)
        for task in project_tasks:
            status_counts[task.status] += 1
        
        # 時間計算
        hours_spent = sum(task.actual_hours for task in project_tasks)
        hours_remaining = sum(
            task.estimated_hours - task.actual_hours 
            for task in project_tasks 
            if task.status != TaskStatus.COMPLETED
        )
        
        # 完了率計算
        total_tasks = len(project_tasks)
        completed_tasks = status_counts[TaskStatus.COMPLETED]
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return ProgressReport(
            project_id=project_id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=status_counts[TaskStatus.IN_PROGRESS],
            blocked_tasks=status_counts[TaskStatus.BLOCKED],
            completion_percentage=completion_percentage,
            hours_spent=hours_spent,
            hours_remaining=hours_remaining
        )
    
    # ========== Helper Functions ==========
    
    def _calculate_base_hours(self, task: Task) -> float:
        """基本工数を計算"""
        # 複雑度要因から計算
        factors = task.complexity_factors
        
        # コード行数ベース
        if "lines_of_code" in factors:
            loc = factors["lines_of_code"]
            base = loc * self.estimation_factors["base_hours_per_loc"]
        else:
            # デフォルト値
            base = task.estimated_hours if task.estimated_hours > 0 else 5.0
        
        # 複雑度による調整
        if "cyclomatic_complexity" in factors:
            complexity = factors["cyclomatic_complexity"]
            if complexity < 10:
                multiplier = self.estimation_factors["complexity_multipliers"]["low"]
            elif complexity < 20:
                multiplier = self.estimation_factors["complexity_multipliers"]["medium"]
            elif complexity < 30:
                multiplier = self.estimation_factors["complexity_multipliers"]["high"]
            else:
                multiplier = self.estimation_factors["complexity_multipliers"]["critical"]
            
            base *= multiplier
        
        return base
    
    def _calculate_confidence(self, task: Task) -> float:
        """見積もり信頼度を計算"""
        confidence = 0.8  # ベース信頼度
        
        # 複雑度が高いほど信頼度を下げる
        if "cyclomatic_complexity" in task.complexity_factors:
            complexity = task.complexity_factors["cyclomatic_complexity"]
            if complexity > 30:
                confidence -= 0.3
            elif complexity > 20:
                confidence -= 0.2
            elif complexity > 10:
                confidence -= 0.1
        
        # 依存関係が多いほど信頼度を下げる
        dependency_count = len(task.dependencies)
        if dependency_count > 5:
            confidence -= 0.2
        elif dependency_count > 3:
            confidence -= 0.1
        
        return max(0.1, min(1.0, confidence))
    
    def _find_critical_path(self, tasks: List[Task]) -> List[str]:
        """クリティカルパスを特定（簡易実装）"""
        # 実際の実装では、各タスクの最早開始時刻と最遅開始時刻を計算
        # ここでは最も依存関係が深いパスを返す簡易実装
        
        if not tasks:
            return []
        
        # 依存関係の深さを計算
        depths = {}
        
        def calculate_depth(task_id: str, task_map: Dict[str, Task]) -> int:
            """calculate_depthメソッド"""
            if task_id in depths:
                return depths[task_id]
            
            task = task_map.get(task_id)
            if not task or not task.dependencies:
                depths[task_id] = 0
                return 0
            
            max_depth = 0
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    depth = calculate_depth(dep_id, task_map)
                    max_depth = max(max_depth, depth + 1)
            
            depths[task_id] = max_depth
            return max_depth
        
        task_map = {task.id: task for task in tasks}
        for task in tasks:
            calculate_depth(task.id, task_map)
        
        # 最も深いパスを構築
        if not depths:
            return []
        
        deepest_task_id = max(depths.keys(), key=lambda k: depths[k])
        path = [deepest_task_id]
        
        # パスを逆方向に辿る
        current_task = task_map[deepest_task_id]
        while current_task.dependencies:
            # 最も深い依存を選択
            next_id = max(
                (dep_id for dep_id in current_task.dependencies if dep_id in task_map),
                key=lambda k: depths.get(k, 0),
                default=None
            )
            if next_id:
                path.insert(0, next_id)
                current_task = task_map[next_id]
            else:
                break
        
        return path
    
    def _generate_milestones(self, project: Project, tasks: List[Task]) -> List[Milestone]:
        """マイルストーンを生成"""
        if not tasks:
            return []
        
        # タスクを優先度でグループ化
        priority_groups = defaultdict(list)
        for task in tasks:
            priority_groups[task.priority].append(task)
        
        milestones = []
        
        # 各優先度グループをマイルストーンとして設定
        for priority in sorted(priority_groups.keys(), key=lambda p: p.value, reverse=True):
            group_tasks = priority_groups[priority]
            if group_tasks:
                # グループの最遅期限を計算
                due_dates = [task.due_date for task in group_tasks if task.due_date]
                target_date = max(due_dates) if due_dates else datetime.now() + timedelta(days=7)
                
                milestone = Milestone(
                    id=f"milestone_{len(milestones) + 1}",
                    name=f"{priority.name}優先度タスク完了",
                    target_date=target_date,
                    task_ids=[task.id for task in group_tasks]
                )
                milestones.append(milestone)
        
        return milestones
    
    async def _estimate_from_data(self, task_data: Dict[str, Any]) -> EffortEstimate:
        """データから工数を見積もる（簡易版）"""
        # 技術とスコープから基本時間を決定
        base_hours = 10.0  # デフォルト
        
        technology = task_data.get("technology", "").lower()
        scope = task_data.get("scope", "medium").lower()
        
        # 技術による調整
        tech_multipliers = {
            "python": 1.0,
            "javascript": 1.1,
            "typescript": 1.2,
            "rust": 1.5,
            "c++": 1.8
        }
        
        # スコープによる調整
        scope_multipliers = {
            "small": 0.5,
            "medium": 1.0,
            "large": 2.0,
            "extra-large": 4.0
        }
        
        tech_mult = tech_multipliers.get(technology, 1.0)
        scope_mult = scope_multipliers.get(scope, 1.0)
        
        estimated_hours = base_hours * tech_mult * scope_mult
        
        # 分解
        breakdown = {
            "implementation": estimated_hours * 0.5,
            "testing": estimated_hours * 0.3,
            "documentation": estimated_hours * 0.2
        }
        
        return EffortEstimate(
            hours=estimated_hours,
            confidence=0.7,
            breakdown=breakdown
        )

    # === Task Sage核心機能実装 ===
    
    async def update_task_status(self, task_id: str, new_status: TaskStatus) -> bool:
        """タスクステータス更新機能 - Task Sage核心機能"""
        try:
            self.logger.info(f"Updating task status: {task_id} -> {new_status.value}")
            
            # タスク存在確認
            if task_id not in self.tasks:
                self.logger.error(f"Task not found: {task_id}")
                return False
            
            # タスク取得
            task = self.tasks[task_id]
            old_status = task.status
            
            # ステータス変更検証
            if not self._validate_status_transition(old_status, new_status):
                self.logger.error(f"Invalid status transition: {old_status.value} -> {new_status.value}" \
                    "Invalid status transition: {old_status.value} -> {new_status.value}" \
                    "Invalid status transition: {old_status.value} -> {new_status.value}")
                return False
            
            # ステータス更新
            task.status = new_status
            task.updated_at = datetime.now()
            
            # ステータス別処理
            if new_status == TaskStatus.IN_PROGRESS:
                task.started_at = datetime.now()
                
            elif new_status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
                
                # 完了時間計算
                if task.started_at:
                    task.actual_duration = (task.completed_at - task.started_at).total_seconds() / 3600
                
                # 依存タスクの解放
                await self._unlock_dependent_tasks(task_id)
                
            elif new_status == TaskStatus.CANCELLED:
                task.cancelled_at = datetime.now()
                await self._handle_task_cancellation(task_id)
            
            # 統計更新
            await self._update_task_statistics()
            
            # タスク永続化
            await self._persist_task(task)
            
            # 関連者通知
            await self._notify_task_status_change(task, old_status, new_status)
            
            self.logger.info(f"Task status updated successfully: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update task status: {e}")
            return False
    
    async def assign_task(self, task_id: str, assignee: str) -> bool:
        """タスク割り当て機能 - Task Sage核心機能"""
        try:
            self.logger.info(f"Assigning task: {task_id} -> {assignee}")
            
            # タスク存在確認
            if task_id not in self.tasks:
                self.logger.error(f"Task not found: {task_id}")
                return False
            
            # 担当者妥当性確認
            if not await self._validate_assignee(assignee):
                self.logger.error(f"Invalid assignee: {assignee}")
                return False
            
            task = self.tasks[task_id]
            old_assignee = task.assignee
            
            # 割り当て実行
            task.assignee = assignee
            task.assigned_at = datetime.now()
            task.updated_at = datetime.now()
            
            # ステータス更新（必要に応じて）
            if task.status == TaskStatus.TODO:
                task.status = TaskStatus.ASSIGNED
            
            # ワークロード管理
            await self._update_assignee_workload(assignee, task_id, "add")
            if old_assignee and old_assignee != assignee:
                await self._update_assignee_workload(old_assignee, task_id, "remove")
            
            # 通知処理
            await self._notify_task_assignment(task, old_assignee, assignee)
            
            # タスク永続化
            await self._persist_task(task)
            
            self.logger.info(f"Task assigned successfully: {task_id} -> {assignee}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to assign task: {e}")
            return False
    
    async def delete_task(self, task_id: str) -> bool:
        """タスク削除機能 - Task Sage核心機能"""
        try:
            self.logger.info(f"Deleting task: {task_id}")
            
            # タスク存在確認
            if task_id not in self.tasks:
                self.logger.error(f"Task not found: {task_id}")
                return False
            
            task = self.tasks[task_id]
            
            # 削除前検証
            if not await self._validate_task_deletion(task):
                self.logger.error(f"Task deletion not allowed: {task_id}")
                return False
            
            # 依存関係の処理
            await self._handle_dependencies_on_deletion(task_id)
            
            # サブタスクの処理
            await self._handle_subtasks_on_deletion(task_id)
            
            # ワークロード調整
            if task.assignee:
                await self._update_assignee_workload(task.assignee, task_id, "remove")
            
            # アーカイブ処理
            await self._archive_task(task)
            
            # タスク削除
            del self.tasks[task_id]
            
            # プロジェクトからの削除
            for project in self.projects.values():
                if task_id in project.task_ids:
                    project.task_ids.remove(task_id)
            
            # 統計更新
            await self._update_task_statistics()
            
            # 通知処理
            await self._notify_task_deletion(task)
            
            self.logger.info(f"Task deleted successfully: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete task: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """タスク取得機能 - Task Sage核心機能"""
        try:
            self.logger.debug(f"Getting task: {task_id}")
            
            # タスク存在確認
            if task_id not in self.tasks:
                self.logger.warning(f"Task not found: {task_id}")
                return None
            
            task = self.tasks[task_id]
            
            # アクセス記録
            task.access_count = getattr(task, 'access_count', 0) + 1
            task.last_accessed = datetime.now()
            
            # タスクの拡張情報取得
            extended_task = await self._enrich_task_data(task)
            
            self.logger.debug(f"Task retrieved: {task_id}")
            return extended_task
            
        except Exception as e:
            self.logger.error(f"Failed to get task: {e}")
            return None
    
    async def list_tasks(self, status: Optional[TaskStatus] = None, assignee: Optional[str] = None, 
                        priority: Optional[TaskPriority] = None, limit: int = 50) -> List[Task]:
        """タスク一覧取得機能 - Task Sage核心機能"""
        try:
            self.logger.debug(f"Listing tasks: status={status}, assignee={assignee}, priority={priority}, " \
                "Listing tasks: status={status}, assignee={assignee}, priority={priority}, " \
                "limit={limit}")
            
            # フィルタリング
            filtered_tasks = []
            for task in self.tasks.values():
                # ステータスフィルタ
                if status and task.status != status:
                    continue
                
                # 担当者フィルタ
                if assignee and task.assignee != assignee:
                    continue
                
                # 優先度フィルタ
                if priority and task.priority != priority:
                    continue
                
                filtered_tasks.append(task)
            
            # ソート（優先度 → 更新日時）
            sorted_tasks = sorted(filtered_tasks, 
                                 key=lambda t: (t.priority.value, t.updated_at), reverse=True)
            
            # 制限適用
            limited_tasks = sorted_tasks[:limit]
            
            # タスクの拡張
            enriched_tasks = []
            for task in limited_tasks:
                enriched_task = await self._enrich_task_data(task)
                enriched_tasks.append(enriched_task)
            
            self.logger.debug(f"Listed {len(enriched_tasks)} tasks")
            return enriched_tasks
            
        except Exception as e:
            self.logger.error(f"Failed to list tasks: {e}")
            return []
    
    async def search_tasks(self, query: str, limit: int = 20) -> List[Task]:
        """タスク検索機能 - Task Sage核心機能"""
        try:
            self.logger.info(f"Searching tasks: query='{query}', limit={limit}")
            
            if not query.strip():
                return []
            
            query_lower = query.lower()
            search_results = []
            
            # 全タスクを検索
            for task in self.tasks.values():
                relevance_score = 0.0
                
                # タイトル検索
                if query_lower in task.title.lower():
                    relevance_score += 1.0
                
                # 説明検索
                if query_lower in task.description.lower():
                    relevance_score += 0.7
                
                # タグ検索
                if hasattr(task, 'tags'):
                    for tag in task.tags:
                        if not (query_lower in tag.lower()):
                        if query_lower in tag.lower():
                            relevance_score += 0.5
                
                # 担当者検索
                if task.assignee and query_lower in task.assignee.lower():
                    relevance_score += 0.3
                
                # カテゴリ検索
                if hasattr(task, 'category') and query_lower in task.category.lower():
                    relevance_score += 0.4
                
                if relevance_score > 0:
                    task_with_score = await self._enrich_task_data(task)
                    task_with_score.search_relevance = relevance_score
                    search_results.append(task_with_score)
            
            # 関連度順ソート
            sorted_results = sorted(search_results, 
                                  key=lambda t: (t.search_relevance, t.priority.value), 
                                  reverse=True)
            
            limited_results = sorted_results[:limit]
            
            self.logger.info(f"Task search completed: {len(limited_results)} results found")
            return limited_results
            
        except Exception as e:
            self.logger.error(f"Task search failed: {e}")
            return []
    
    async def get_task_statistics(self) -> Dict[str, Any]:

            """タスク統計取得機能 - Task Sage核心機能"""
            self.logger.debug("Generating task statistics")
            
            total_tasks = len(self.tasks)
            
            if total_tasks == 0:
                return {
                    "total_tasks": 0,
                    "status_distribution": {},
                    "priority_distribution": {},
                    "assignee_distribution": {},
                    "completion_rate": 0.0,
                    "average_completion_time": 0.0,
                    "overdue_tasks": 0
                }
            
            # ステータス分布
            status_counts = {}
            for status in TaskStatus:
                status_counts[status.value] = sum(1 for task in self.tasks.values() if task.status == status)
            
            # 優先度分布
            priority_counts = {}
            for priority in TaskPriority:
                priority_counts[priority.value] = sum(1 for task in self.tasks.values() if task.priority == priority)
            
            # 担当者分布
            assignee_counts = {}
            for task in self.tasks.values():
                if task.assignee:
                    assignee_counts[task.assignee] = assignee_counts.get(task.assignee, 0) + 1
                else:
                    assignee_counts["unassigned"] = assignee_counts.get("unassigned", 0) + 1
            
            # 完了率計算
            completed_tasks = status_counts.get(TaskStatus.COMPLETED.value, 0)
            completion_rate = (completed_tasks / total_tasks) * 100
            
            # 平均完了時間計算
            completion_times = []
            for task in self.tasks.values():
                if hasattr(task, 'actual_duration') and task.actual_duration:
                    completion_times.append(task.actual_duration)
            
            average_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0.0
            
            # 期限遅れタスク数
            overdue_count = await self._count_overdue_tasks()
            
            # プロジェクト統計
            project_stats = await self._calculate_project_statistics()
            
            statistics = {
                "total_tasks": total_tasks,
                "status_distribution": status_counts,
                "priority_distribution": priority_counts,
                "assignee_distribution": assignee_counts,
                "completion_rate": round(completion_rate, 2),
                "average_completion_time": round(average_completion_time, 2),
                "overdue_tasks": overdue_count,
                "project_statistics": project_stats,
                "generated_at": datetime.now().isoformat()
            }
            
            self.logger.debug("Task statistics generated successfully")
            return statistics
            
        except Exception as e:
            self.logger.error(f"Failed to generate task statistics: {e}")
            return {"error": str(e)}
    
    async def get_task_dependencies(self, task_id: str) -> List[str]:
        """タスク依存関係取得機能 - Task Sage核心機能"""
        try:
            self.logger.debug(f"Getting task dependencies: {task_id}")
            
            # タスク存在確認
            if task_id not in self.tasks:
                self.logger.error(f"Task not found: {task_id}")
                return []
            
            task = self.tasks[task_id]
            dependencies = []
            
            # 直接依存関係
            if hasattr(task, 'dependencies') and task.dependencies:
                dependencies.extend(task.dependencies)
            
            # プロジェクト依存関係
            project_deps = await self._get_project_dependencies(task_id)
            dependencies.extend(project_deps)
            
            # 階層依存関係（親子関係）
            hierarchical_deps = await self._get_hierarchical_dependencies(task_id)
            dependencies.extend(hierarchical_deps)
            
            # 重複除去・検証
            unique_dependencies = list(set(dependencies))
            validated_dependencies = []
            
            for dep_id in unique_dependencies:
                if dep_id in self.tasks:
                    validated_dependencies.append(dep_id)
                else:
                    self.logger.warning(f"Invalid dependency found: {dep_id}")
            
            self.logger.debug(f"Found {len(validated_dependencies)} dependencies for task {task_id}" \
                "Found {len(validated_dependencies)} dependencies for task {task_id}" \
                "Found {len(validated_dependencies)} dependencies for task {task_id}")
            return validated_dependencies
            
        except Exception as e:
            self.logger.error(f"Failed to get task dependencies: {e}")
            return []
    
    # === Task Sage補助機能実装 ===
    
    def _validate_status_transition(self, old_status: TaskStatus, new_status: TaskStatus) -> bool:
        """ステータス遷移検証"""
        valid_transitions = {
            TaskStatus.TODO: [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.ASSIGNED: [TaskStatus.IN_PROGRESS, TaskStatus.TODO, TaskStatus.CANCELLED],
            TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.ON_HOLD, TaskStatus.CANCELLED],
            TaskStatus.ON_HOLD: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.COMPLETED: [TaskStatus.IN_PROGRESS],  # 再オープン
            TaskStatus.CANCELLED: [TaskStatus.TODO, TaskStatus.ASSIGNED]  # 復活
        }
        
        return new_status in valid_transitions.get(old_status, [])
    
    async def _unlock_dependent_tasks(self, completed_task_id: str):
        """依存タスクの解放"""
        for task in self.tasks.values():
            if hasattr(task, 'dependencies') and completed_task_id in task.dependencies:
                task.dependencies.remove(completed_task_id)
                if not task.dependencies and task.status == TaskStatus.TODO:
                    await self.update_task_status(task.id, TaskStatus.ASSIGNED)
    
    async def _handle_task_cancellation(self, task_id: str):
        """タスクキャンセル処理"""
        # 依存タスクの処理
        dependent_tasks = [t for t in self.tasks.values() 
                          if hasattr(t, 'dependencies') and task_id in t.dependencies]
        
        for dep_task in dependent_tasks:
            self.logger.warning(f"Task {dep_task.id} depends on cancelled task {task_id}")
    
    async def _validate_assignee(self, assignee: str) -> bool:
        """担当者妥当性確認"""
        # 模擬検証（実際の実装では認証システム連携）
        return bool(assignee and assignee.strip())
    
    async def _update_assignee_workload(self, assignee: str, task_id: str, action: str):
        """担当者ワークロード更新"""
        self.logger.debug(f"Updating workload: {assignee} {action} {task_id}")
    
    async def _notify_task_assignment(self, task: Task, old_assignee: str, new_assignee: str):
        """タスク割り当て通知"""
        self.logger.debug(f"Notifying assignment: {task.id} {old_assignee} -> {new_assignee}")
    
    async def _validate_task_deletion(self, task: Task) -> bool:
        """タスク削除検証"""
        # 進行中タスクの削除禁止
        if task.status == TaskStatus.IN_PROGRESS:
            return False
        
        # 依存タスク存在確認
        dependent_count = sum(1 for t in self.tasks.values() 
                            if hasattr(t, 'dependencies') and task.id in t.dependencies)
        
        return dependent_count == 0
    
    async def _handle_dependencies_on_deletion(self, task_id: str):
        """削除時依存関係処理"""
        for task in self.tasks.values():
            if hasattr(task, 'dependencies') and task_id in task.dependencies:
                task.dependencies.remove(task_id)
    
    async def _handle_subtasks_on_deletion(self, task_id: str):
        """削除時サブタスク処理"""
        subtasks = [t for t in self.tasks.values() 
                   if hasattr(t, 'parent_id') and t.parent_id == task_id]
        
        for subtask in subtasks:
            subtask.parent_id = None
    
    async def _archive_task(self, task: Task):
        """タスクアーカイブ"""
        self.logger.debug(f"Archiving task: {task.id}")
    
    async def _notify_task_deletion(self, task: Task):
        """タスク削除通知"""
        self.logger.debug(f"Notifying deletion: {task.id}")
    
    async def _enrich_task_data(self, task: Task) -> Task:
        """タスクデータ拡張"""
        # 依存関係情報追加
        if not hasattr(task, 'dependencies'):
            task.dependencies = []
        
        # 進捗情報追加
        if not hasattr(task, 'progress_percentage'):
            task.progress_percentage = self._calculate_task_progress(task)
        
        return task
    
    def _calculate_task_progress(self, task: Task) -> float:
        """タスク進捗計算"""
        if task.status == TaskStatus.COMPLETED:
            return 100.0
        elif task.status == TaskStatus.IN_PROGRESS:
            return 50.0  # 模擬進捗
        else:
            return 0.0
    
    async def _count_overdue_tasks(self) -> int:

            """期限遅れタスク数計算"""
            if hasattr(task, 'due_date') and task.due_date:
                if task.due_date < current_time and task.status != TaskStatus.COMPLETED:
                    overdue_count += 1
        
        return overdue_count
    
    async def _calculate_project_statistics(self) -> Dict[str, Any]:

                    """プロジェクト統計計算""" len(self.projects),
            "active_projects": sum(1 for p in self.projects.values() if p.status == "active"),
            "completed_projects": sum(1 for p in self.projects.values() if p.status == "completed")
        }
    
    async def _get_project_dependencies(self, task_id: str) -> List[str]:
        """プロジェクト依存関係取得"""
        dependencies = []
        
        for project in self.projects.values():
            if task_id in project.task_ids:
                # プロジェクト内の他タスクとの依存関係
                other_tasks = [tid for tid in project.task_ids if tid != task_id]
                dependencies.extend(other_tasks[:2])  # 模擬依存関係
        
        return dependencies
    
    async def _get_hierarchical_dependencies(self, task_id: str) -> List[str]:
        """階層依存関係取得"""
        task = self.tasks[task_id]
        dependencies = []
        
        # 親タスクとの依存関係
        if hasattr(task, 'parent_id') and task.parent_id:
            dependencies.append(task.parent_id)
        
        return dependencies
    
    async def _update_task_statistics(self):

            """タスク統計更新""" Task):
        """タスク永続化"""
        self.logger.debug(f"Persisting task: {task.id}")
    
    async def _notify_task_status_change(
        self,
        task: Task,
        old_status: TaskStatus,
        new_status: TaskStatus
    ):

    """タスクステータス変更通知""" {task.id} {old_status.value} -> {new_status.value}" \
            "Notifying status change: {task.id} {old_status.value} -> {new_status.value}" \
            "Notifying status change: {task.id} {old_status.value} -> {new_status.value}")


async def main():



"""魂のメインループ"""
    asyncio.run(main())
