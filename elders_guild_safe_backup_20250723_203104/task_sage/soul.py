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
    pass


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
        pass

        
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
        pass

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
    
    async def _handle_request(self, message: Dict[str, Any]) -> Dict[str, Any]action = message.get("action")
    """リクエスト処理"""
        :
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
        """コマンド処理"""
        # 実装予定
        pass
        
    async def _handle_query(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """クエリ処理"""
        # 実装予定
        pass
    
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


async def main():
    pass

        """魂のメインループ"""
    asyncio.run(main())
