"""
Task Sage - タスク調整・管理専門AI
TDD Green Phase: 実装フェーズ
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import json
from elder_tree.agents.base_agent import ElderTreeAgent
from sqlmodel import SQLModel, Field, Session, create_engine, select
from prometheus_client import Counter, Gauge
import structlog


# SQLModel Task定義
class Task(SQLModel, table=True):
    """タスクモデル"""
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, unique=True)
    title: str
    description: str
    status: str = Field(default="pending")  # pending, in_progress, completed
    priority: str = Field(default="medium")  # low, medium, high, critical
    assignee: Optional[str] = None
    estimation_hours: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    dependencies: str = Field(default="[]")  # JSON array of task_ids
    

class TaskSage(ElderTreeAgent):
    """
    Task Sage - タスク管理の専門家
    
    責務:
    - タスクの作成・更新・削除
    - タスクの割り当て・スケジューリング
    - 工数見積もり
    - 依存関係管理
    - 進捗追跡
    """
    
    def __init__(self, db_url: str = "sqlite:///tasks.db"):
        super().__init__(
            name="task_sage",
            domain="task",
            port=50052
        )
        
        # データベース初期化
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)
        
        # 追加メトリクス
        self.active_tasks = Gauge(
            'task_sage_active_tasks',
            'Number of active tasks',
            ['status', 'priority']
        )
        
        self.task_operations = Counter(
            'task_sage_operations_total',
            'Task operations',
            ['operation', 'status']
        )
        
        # ドメイン固有ハンドラー登録
        self._register_domain_handlers()
        
        self.logger.info("TaskSage initialized with database", db_url=db_url)
    
    def _register_domain_handlers(self):
        """Task Sage専用ハンドラー登録"""
        
        @self.on_message("estimate_task")
        async def handle_estimate_task(message) -> Dict[str, Any]:
            """
            タスク工数見積もり
            
            Input:
                - task_description: タスク説明
                - complexity: 複雑度（low/medium/high/very_high）
                - requirements: 要件リスト
            """
            data = message.data
            task_description = data.get("task_description", "")
            complexity = data.get("complexity", "medium")
            requirements = data.get("requirements", [])
            
            # 見積もりロジック
            base_hours = {
                "low": 4,
                "medium": 16,
                "high": 40,
                "very_high": 80
            }
            
            estimated_hours = base_hours.get(complexity, 16)
            
            # 要件による調整
            if len(requirements) > 5:
                estimated_hours *= 1.5
            
            # TDD要件なら追加時間
            if any("test" in req.lower() or "tdd" in req.lower() for req in requirements):
                estimated_hours *= 1.3
                
            # セキュリティ要件なら追加時間
            if any("security" in req.lower() or "auth" in req.lower() for req in requirements):
                estimated_hours *= 1.2
            
            # Knowledge Sageと協調して技術的複雑度を確認
            if complexity in ["high", "very_high"]:
                tech_analysis = await self.collaborate_with_sage(
                    "knowledge_sage",
                    {
                        "action": "analyze_complexity",
                        "description": task_description,
                        "technologies": requirements
                    }
                )
                # tech_analysisに基づく調整（仮実装）
                if tech_analysis:
                    estimated_hours *= 1.1
            
            estimation = {
                "hours": round(estimated_hours, 1),
                "days": round(estimated_hours / 8, 1),
                "confidence": 0.75 if complexity in ["low", "medium"] else 0.6,
                "breakdown": {
                    "design": round(estimated_hours * 0.2, 1),
                    "implementation": round(estimated_hours * 0.5, 1),
                    "testing": round(estimated_hours * 0.2, 1),
                    "documentation": round(estimated_hours * 0.1, 1)
                },
                "assumptions": [
                    f"Complexity level: {complexity}",
                    f"Number of requirements: {len(requirements)}",
                    "Includes design, implementation, testing, and documentation"
                ]
            }
            
            self.task_operations.labels(
                operation="estimate",
                status="success"
            ).inc()
            
            return {
                "status": "success",
                "estimation": estimation
            }
        
        @self.on_message("create_task")
        async def handle_create_task(message) -> Dict[str, Any]:
            """タスク作成"""
            data = message.data
            
            # タスクID生成
            task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            with Session(self.engine) as session:
                task = Task(
                    task_id=task_id,
                    title=data.get("title", "Untitled Task"),
                    description=data.get("description", ""),
                    status="pending",
                    priority=data.get("priority", "medium"),
                    assignee=data.get("assignee"),
                    estimation_hours=data.get("estimation_hours"),
                    dependencies=json.dumps(data.get("dependencies", []))
                )
                
                session.add(task)
                session.commit()
                session.refresh(task)
                
                self.active_tasks.labels(
                    status=task.status,
                    priority=task.priority
                ).inc()
                
                self.task_operations.labels(
                    operation="create",
                    status="success"
                ).inc()
                
                return {
                    "status": "success",
                    "task_id": task.task_id,
                    "task": {
                        "id": task.task_id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority
                    }
                }
        
        @self.on_message("update_task_status")
        async def handle_update_status(message) -> Dict[str, Any]:
            """タスクステータス更新"""
            task_id = message.data.get("task_id")
            new_status = message.data.get("status")
            
            with Session(self.engine) as session:
                statement = select(Task).where(Task.task_id == task_id)
                task = session.exec(statement).first()
                
                if not task:
                    return {"status": "error", "message": "Task not found"}
                
                old_status = task.status
                task.status = new_status
                task.updated_at = datetime.now()
                
                session.add(task)
                session.commit()
                
                # メトリクス更新
                self.active_tasks.labels(
                    status=old_status,
                    priority=task.priority
                ).dec()
                self.active_tasks.labels(
                    status=new_status,
                    priority=task.priority
                ).inc()
                
                # Incident Sageに通知（クリティカルタスクの場合）
                if task.priority == "critical" and new_status == "completed":
                    await self.collaborate_with_sage(
                        "incident_sage",
                        {
                            "action": "task_completed",
                            "task_id": task_id,
                            "priority": "critical"
                        }
                    )
                
                return {
                    "status": "success",
                    "task_id": task_id,
                    "new_status": new_status,
                    "old_status": old_status
                }
        
        @self.on_message("get_task_statistics")
        async def handle_get_statistics(message) -> Dict[str, Any]:
            """タスク統計情報取得"""
            with Session(self.engine) as session:
                all_tasks = session.exec(select(Task)).all()
                
                stats = {
                    "total_tasks": len(all_tasks),
                    "by_status": {},
                    "by_priority": {},
                    "average_estimation_hours": 0,
                    "completed_today": 0
                }
                
                total_hours = 0
                count_with_estimation = 0
                today = datetime.now().date()
                
                for task in all_tasks:
                    # ステータス別カウント
                    stats["by_status"][task.status] = stats["by_status"].get(task.status, 0) + 1
                    
                    # 優先度別カウント
                    stats["by_priority"][task.priority] = stats["by_priority"].get(task.priority, 0) + 1
                    
                    # 平均見積もり時間
                    if task.estimation_hours:
                        total_hours += task.estimation_hours
                        count_with_estimation += 1
                    
                    # 今日完了したタスク
                    if task.status == "completed" and task.updated_at.date() == today:
                        stats["completed_today"] += 1
                
                if count_with_estimation > 0:
                    stats["average_estimation_hours"] = round(total_hours / count_with_estimation, 1)
                
                return {
                    "status": "success",
                    "statistics": stats
                }
        
        @self.on_message("assign_task")
        async def handle_assign_task(message) -> Dict[str, Any]:
            """タスク割り当て"""
            task_id = message.data.get("task_id")
            assignee = message.data.get("assignee")
            
            with Session(self.engine) as session:
                statement = select(Task).where(Task.task_id == task_id)
                task = session.exec(statement).first()
                
                if not task:
                    return {"status": "error", "message": "Task not found"}
                
                task.assignee = assignee
                task.updated_at = datetime.now()
                
                session.add(task)
                session.commit()
                
                return {
                    "status": "success",
                    "task_id": task_id,
                    "assignee": assignee
                }
        
        @self.on_message("list_tasks")
        async def handle_list_tasks(message) -> Dict[str, Any]:
            """タスク一覧取得"""
            filters = message.data.get("filters", {})
            
            with Session(self.engine) as session:
                statement = select(Task)
                
                # フィルタリング
                if "status" in filters:
                    statement = statement.where(Task.status == filters["status"])
                if "priority" in filters:
                    statement = statement.where(Task.priority == filters["priority"])
                if "assignee" in filters:
                    statement = statement.where(Task.assignee == filters["assignee"])
                
                tasks = session.exec(statement).all()
                
                task_list = []
                for task in tasks:
                    task_list.append({
                        "task_id": task.task_id,
                        "title": task.title,
                        "status": task.status,
                        "priority": task.priority,
                        "assignee": task.assignee,
                        "estimation_hours": task.estimation_hours,
                        "created_at": task.created_at.isoformat(),
                        "updated_at": task.updated_at.isoformat()
                    })
                
                return {
                    "status": "success",
                    "tasks": task_list,
                    "count": len(task_list)
                }
        
        @self.on_message("analyze_dependencies")
        async def handle_analyze_dependencies(message) -> Dict[str, Any]:
            """タスク依存関係分析"""
            task_id = message.data.get("task_id")
            
            with Session(self.engine) as session:
                statement = select(Task).where(Task.task_id == task_id)
                task = session.exec(statement).first()
                
                if not task:
                    return {"status": "error", "message": "Task not found"}
                
                dependencies = json.loads(task.dependencies)
                
                # 依存タスクの状態確認
                dependency_status = {}
                blocking_tasks = []
                
                for dep_id in dependencies:
                    dep_statement = select(Task).where(Task.task_id == dep_id)
                    dep_task = session.exec(dep_statement).first()
                    
                    if dep_task:
                        dependency_status[dep_id] = {
                            "title": dep_task.title,
                            "status": dep_task.status,
                            "assignee": dep_task.assignee
                        }
                        
                        if dep_task.status != "completed":
                            blocking_tasks.append(dep_id)
                
                return {
                    "status": "success",
                    "task_id": task_id,
                    "dependencies": dependency_status,
                    "blocking_tasks": blocking_tasks,
                    "can_start": len(blocking_tasks) == 0
                }


# 単体実行用
async def main():
    sage = TaskSage()
    await sage.start()
    print(f"Task Sage running on port {sage.port}")
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await sage.stop()


if __name__ == "__main__":
    asyncio.run(main())