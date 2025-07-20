"""
Task Sage - タスク管理・計画立案賢者

タスクの分析、計画立案、進捗管理を担当するエルダーズギルドの賢者。
"""

import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """タスクオブジェクト"""
    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    dependencies: List[str] = None
    tags: List[str] = None
    assignee: Optional[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []


class TaskSage:
    """タスク管理・計画立案賢者"""

    def __init__(self):
        """Task Sageを初期化"""
        self.logger = logger
        self.tasks: Dict[str, Task] = {}
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.task_history = []
        
        self.logger.info("📋 Task Sage初期化完了")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        タスク処理要求を処理
        
        Args:
            request: リクエスト
                - type: 要求タイプ (create_plan, analyze_task, etc.)
                - title: タスクタイトル
                - description: タスク説明
                - priority: 優先度
                
        Returns:
            Dict[str, Any]: 処理結果
        """
        try:
            request_type = request.get("type", "unknown")
            self.logger.info(f"📋 Task Sage処理開始: {request_type}")

            if request_type == "create_plan":
                return await self._create_task_plan(request)
            elif request_type == "analyze_task":
                return await self._analyze_task(request)
            elif request_type == "track_progress":
                return await self._track_progress(request)
            elif request_type == "optimize_workflow":
                return await self._optimize_workflow(request)
            elif request_type == "estimate_effort":
                return await self._estimate_effort(request)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown request type: {request_type}",
                    "supported_types": [
                        "create_plan", "analyze_task", "track_progress", 
                        "optimize_workflow", "estimate_effort"
                    ]
                }

        except Exception as e:
            self.logger.error(f"Task Sage処理エラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sage": "task"
            }

    async def _create_task_plan(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスク実行計画を作成"""
        try:
            title = request.get("title", "")
            description = request.get("description", "")
            priority = request.get("priority", "medium")

            # タスクを分析してサブタスクに分解
            subtasks = self._decompose_task(title, description)
            
            # 依存関係を分析
            dependencies = self._analyze_dependencies(subtasks)
            
            # 時間見積もり
            estimates = self._estimate_task_durations(subtasks)
            
            # 実行順序を最適化
            execution_order = self._optimize_execution_order(subtasks, dependencies)

            task_id = str(uuid.uuid4())
            plan = {
                "task_id": task_id,
                "title": title,
                "description": description,
                "priority": priority,
                "subtasks": subtasks,
                "dependencies": dependencies,
                "estimates": estimates,
                "execution_order": execution_order,
                "total_estimated_hours": sum(estimates.values()),
                "recommended_approach": self._get_recommended_approach(title, description),
                "risk_factors": self._identify_risk_factors(title, description),
                "success_criteria": self._define_success_criteria(title, description)
            }

            # タスクを保存
            task = Task(
                id=task_id,
                title=title,
                description=description,
                priority=TaskPriority(priority),
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                estimated_hours=plan["total_estimated_hours"]
            )
            self.tasks[task_id] = task

            return {
                "status": "success",
                "sage": "task",
                "plan": plan,
                "confidence": 0.85,
                "recommendations": [
                    "計画に従って段階的に実装してください",
                    "各サブタスクの完了後に進捗を確認してください",
                    "リスク要因に注意して実装を進めてください"
                ]
            }

        except Exception as e:
            raise Exception(f"Task plan creation error: {e}")

    async def _analyze_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """タスクを分析"""
        try:
            task_id = request.get("task_id")
            title = request.get("title", "")
            description = request.get("description", "")

            analysis = {
                "complexity_score": self._calculate_complexity(title, description),
                "effort_estimate": self._estimate_effort_hours(title, description),
                "skill_requirements": self._identify_required_skills(title, description),
                "potential_blockers": self._identify_potential_blockers(title, description),
                "recommended_resources": self._recommend_resources(title, description),
                "testing_strategy": self._suggest_testing_strategy(title, description)
            }

            return {
                "status": "success",
                "sage": "task",
                "analysis": analysis,
                "confidence": 0.8
            }

        except Exception as e:
            raise Exception(f"Task analysis error: {e}")

    async def _track_progress(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """進捗を追跡"""
        try:
            task_id = request.get("task_id")
            progress_data = request.get("progress", {})

            if task_id and task_id in self.tasks:
                task = self.tasks[task_id]
                
                # 進捗を更新
                if "status" in progress_data:
                    task.status = TaskStatus(progress_data["status"])
                if "actual_hours" in progress_data:
                    task.actual_hours = progress_data["actual_hours"]
                
                task.updated_at = datetime.now()

                # 進捗分析
                progress_analysis = {
                    "completion_percentage": self._calculate_completion_percentage(task),
                    "time_variance": self._calculate_time_variance(task),
                    "status": task.status.value,
                    "next_actions": self._suggest_next_actions(task),
                    "blockers": self._identify_current_blockers(task)
                }

                return {
                    "status": "success",
                    "sage": "task",
                    "progress": progress_analysis,
                    "confidence": 0.9
                }
            else:
                return {
                    "status": "error",
                    "error": "Task not found",
                    "sage": "task"
                }

        except Exception as e:
            raise Exception(f"Progress tracking error: {e}")

    async def _optimize_workflow(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """ワークフローを最適化"""
        try:
            tasks = request.get("tasks", [])
            constraints = request.get("constraints", {})

            optimization = {
                "optimal_sequence": self._find_optimal_sequence(tasks),
                "parallel_opportunities": self._identify_parallel_tasks(tasks),
                "resource_allocation": self._optimize_resource_allocation(tasks),
                "bottleneck_analysis": self._analyze_bottlenecks(tasks),
                "efficiency_improvements": self._suggest_efficiency_improvements(tasks)
            }

            return {
                "status": "success",
                "sage": "task",
                "optimization": optimization,
                "confidence": 0.8
            }

        except Exception as e:
            raise Exception(f"Workflow optimization error: {e}")

    async def _estimate_effort(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """作業量を見積もり"""
        try:
            title = request.get("title", "")
            description = request.get("description", "")
            complexity_factors = request.get("complexity_factors", {})

            estimate = {
                "base_estimate_hours": self._estimate_effort_hours(title, description),
                "complexity_multiplier": self._calculate_complexity_multiplier(complexity_factors),
                "uncertainty_range": self._calculate_uncertainty_range(title, description),
                "confidence_level": self._calculate_estimate_confidence(title, description),
                "breakdown": self._create_effort_breakdown(title, description)
            }

            final_estimate = estimate["base_estimate_hours"] * estimate["complexity_multiplier"]
            
            return {
                "status": "success",
                "sage": "task",
                "estimate": {
                    **estimate,
                    "final_estimate_hours": final_estimate,
                    "range_min": final_estimate * 0.8,
                    "range_max": final_estimate * 1.3
                },
                "confidence": estimate["confidence_level"]
            }

        except Exception as e:
            raise Exception(f"Effort estimation error: {e}")

    def _decompose_task(self, title: str, description: str) -> List[Dict[str, Any]]:
        """タスクをサブタスクに分解"""
        # 簡易的な分解ロジック（実際はより複雑な分析が必要）
        subtasks = []
        
        # キーワードベースの分解
        if "実装" in title or "implement" in title.lower():
            subtasks.extend([
                {"name": "要件分析", "type": "analysis"},
                {"name": "設計", "type": "design"},
                {"name": "実装", "type": "coding"},
                {"name": "テスト", "type": "testing"},
                {"name": "ドキュメント作成", "type": "documentation"}
            ])
        elif "修正" in title or "fix" in title.lower():
            subtasks.extend([
                {"name": "問題調査", "type": "investigation"},
                {"name": "原因分析", "type": "analysis"},
                {"name": "修正実装", "type": "coding"},
                {"name": "テスト", "type": "testing"}
            ])
        else:
            # デフォルト分解
            subtasks.extend([
                {"name": "計画", "type": "planning"},
                {"name": "実行", "type": "execution"},
                {"name": "検証", "type": "verification"}
            ])

        return subtasks

    def _analyze_dependencies(self, subtasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """依存関係を分析"""
        dependencies = {}
        
        for i, task in enumerate(subtasks):
            task_name = task["name"]
            dependencies[task_name] = []
            
            # 前のタスクに依存する基本パターン
            if i > 0:
                dependencies[task_name].append(subtasks[i-1]["name"])
            
            # 特定の依存関係
            if task["type"] == "testing":
                for prev_task in subtasks[:i]:
                    if prev_task["type"] == "coding":
                        if prev_task["name"] not in dependencies[task_name]:
                            dependencies[task_name].append(prev_task["name"])

        return dependencies

    def _estimate_task_durations(self, subtasks: List[Dict[str, Any]]) -> Dict[str, float]:
        """タスクの所要時間を見積もり"""
        duration_map = {
            "analysis": 2.0,
            "design": 3.0,
            "coding": 5.0,
            "testing": 2.0,
            "documentation": 1.0,
            "investigation": 1.5,
            "planning": 1.0,
            "execution": 4.0,
            "verification": 1.5
        }
        
        estimates = {}
        for task in subtasks:
            task_type = task.get("type", "execution")
            estimates[task["name"]] = duration_map.get(task_type, 2.0)
        
        return estimates

    def _optimize_execution_order(self, subtasks: List[Dict[str, Any]], dependencies: Dict[str, List[str]]) -> List[str]:
        """実行順序を最適化（トポロジカルソート）"""
        # 簡易的なトポロジカルソート
        result = []
        remaining = set(task["name"] for task in subtasks)
        
        while remaining:
            # 依存関係のないタスクを探す
            ready_tasks = []
            for task_name in remaining:
                deps = dependencies.get(task_name, [])
                if all(dep not in remaining for dep in deps):
                    ready_tasks.append(task_name)
            
            if not ready_tasks:
                # 循環依存の可能性、残りを順次追加
                ready_tasks = [next(iter(remaining))]
            
            # 最初に見つかったタスクを追加
            task_to_add = ready_tasks[0]
            result.append(task_to_add)
            remaining.remove(task_to_add)
        
        return result

    def _get_recommended_approach(self, title: str, description: str) -> List[str]:
        """推奨アプローチを取得"""
        approaches = []
        
        if "プレースホルダー" in title or "placeholder" in title.lower():
            approaches.extend([
                "既存の実装パターンを参考にする",
                "段階的に機能を実装する",
                "テスト駆動開発(TDD)を採用する"
            ])
        
        if "エラー" in title or "error" in title.lower():
            approaches.extend([
                "ログを詳細に調査する",
                "再現手順を明確にする",
                "修正後の回帰テストを実装する"
            ])
        
        if not approaches:
            approaches = [
                "要件を明確に定義する",
                "小さく始めて段階的に拡張する",
                "コードレビューを実施する"
            ]
        
        return approaches

    def _identify_risk_factors(self, title: str, description: str) -> List[str]:
        """リスク要因を特定"""
        risks = []
        
        if "統合" in title or "integration" in title.lower():
            risks.append("システム間の互換性問題")
        
        if "データベース" in description or "database" in description.lower():
            risks.append("データ整合性の問題")
        
        if "API" in description:
            risks.append("外部API依存による障害")
        
        return risks

    def _define_success_criteria(self, title: str, description: str) -> List[str]:
        """成功基準を定義"""
        criteria = [
            "すべてのテストが通過する",
            "コードレビューで承認される",
            "ドキュメントが更新される"
        ]
        
        if "パフォーマンス" in description:
            criteria.append("性能要件を満たす")
        
        if "セキュリティ" in description:
            criteria.append("セキュリティ監査を通過する")
        
        return criteria

    def _calculate_complexity(self, title: str, description: str) -> float:
        """複雑度を計算（0.0-1.0）"""
        complexity = 0.3  # ベース複雑度
        
        # キーワードベースの複雑度計算
        high_complexity_keywords = ["統合", "migration", "refactor", "architecture"]
        medium_complexity_keywords = ["API", "database", "algorithm"]
        
        for keyword in high_complexity_keywords:
            if keyword in title.lower() or keyword in description.lower():
                complexity += 0.2
        
        for keyword in medium_complexity_keywords:
            if keyword in title.lower() or keyword in description.lower():
                complexity += 0.1
        
        return min(complexity, 1.0)

    def _estimate_effort_hours(self, title: str, description: str) -> float:
        """作業時間を見積もり"""
        base_hours = 4.0  # ベース時間
        
        # タイトルと説明の長さに基づく調整
        text_length = len(title) + len(description)
        if text_length > 200:
            base_hours += 2.0
        elif text_length > 100:
            base_hours += 1.0
        
        # 複雑度による調整
        complexity = self._calculate_complexity(title, description)
        base_hours *= (1 + complexity)
        
        return round(base_hours, 1)

    def _identify_required_skills(self, title: str, description: str) -> List[str]:
        """必要スキルを特定"""
        skills = ["Python"]  # ベーススキル
        
        if "API" in description:
            skills.append("REST API")
        if "データベース" in description or "database" in description.lower():
            skills.append("Database")
        if "フロントエンド" in description or "frontend" in description.lower():
            skills.append("Frontend")
        if "Docker" in description:
            skills.append("Docker")
        
        return skills

    def _identify_potential_blockers(self, title: str, description: str) -> List[str]:
        """潜在的な障害を特定"""
        blockers = []
        
        if "外部" in description or "external" in description.lower():
            blockers.append("外部システムの可用性")
        if "権限" in description or "permission" in description.lower():
            blockers.append("権限設定の問題")
        if "環境" in description or "environment" in description.lower():
            blockers.append("環境設定の複雑さ")
        
        return blockers

    def _recommend_resources(self, title: str, description: str) -> List[str]:
        """推奨リソースを提案"""
        resources = ["公式ドキュメント"]
        
        if "Python" in description:
            resources.append("Python公式ドキュメント")
        if "API" in description:
            resources.append("RESTful API設計ガイド")
        if "テスト" in description:
            resources.append("pytest公式ガイド")
        
        return resources

    def _suggest_testing_strategy(self, title: str, description: str) -> List[str]:
        """テスト戦略を提案"""
        strategy = ["ユニットテスト"]
        
        if "統合" in title or "integration" in title.lower():
            strategy.append("統合テスト")
        if "API" in description:
            strategy.append("APIテスト")
        if "UI" in description or "フロントエンド" in description:
            strategy.append("E2Eテスト")
        
        return strategy

    # 以下、その他のヘルパーメソッド（簡略実装）
    def _calculate_completion_percentage(self, task: Task) -> float:
        return 50.0 if task.status == TaskStatus.IN_PROGRESS else (100.0 if task.status == TaskStatus.COMPLETED else 0.0)

    def _calculate_time_variance(self, task: Task) -> float:
        if task.estimated_hours and task.actual_hours:
            return ((task.actual_hours - task.estimated_hours) / task.estimated_hours) * 100
        return 0.0

    def _suggest_next_actions(self, task: Task) -> List[str]:
        if task.status == TaskStatus.PENDING:
            return ["タスクを開始してください"]
        elif task.status == TaskStatus.IN_PROGRESS:
            return ["進捗を確認してください", "必要に応じてヘルプを求めてください"]
        return ["タスクをレビューしてください"]

    def _identify_current_blockers(self, task: Task) -> List[str]:
        return ["特になし"] if task.status != TaskStatus.BLOCKED else ["調査が必要"]

    def _find_optimal_sequence(self, tasks: List[Dict]) -> List[str]:
        return [task.get("name", f"task_{i}") for i, task in enumerate(tasks)]

    def _identify_parallel_tasks(self, tasks: List[Dict]) -> List[List[str]]:
        return []

    def _optimize_resource_allocation(self, tasks: List[Dict]) -> Dict[str, str]:
        return {}

    def _analyze_bottlenecks(self, tasks: List[Dict]) -> List[str]:
        return []

    def _suggest_efficiency_improvements(self, tasks: List[Dict]) -> List[str]:
        return ["自動化の機会を探してください"]

    def _calculate_complexity_multiplier(self, factors: Dict) -> float:
        return 1.2

    def _calculate_uncertainty_range(self, title: str, description: str) -> Dict[str, float]:
        return {"min_factor": 0.8, "max_factor": 1.3}

    def _calculate_estimate_confidence(self, title: str, description: str) -> float:
        return 0.7

    def _create_effort_breakdown(self, title: str, description: str) -> Dict[str, float]:
        return {
            "analysis": 0.2,
            "implementation": 0.6,
            "testing": 0.2
        }


# 互換性のための関数
def setup(*args, **kwargs):
    """セットアップ関数"""
    logger.info("📋 Task Sage セットアップ")
    return TaskSage()


def main(*args, **kwargs):
    """メイン関数"""
    logger.info("📋 Task Sage 実行")
    sage = TaskSage()
    return sage


# Export
__all__ = ["TaskSage", "Task", "TaskPriority", "TaskStatus", "setup", "main"]