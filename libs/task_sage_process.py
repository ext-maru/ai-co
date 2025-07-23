#!/usr/bin/env python3
"""
タスク賢者プロセス
Task Sage Process - プロジェクト管理専門プロセス

タスクの優先順位付けと進捗管理を担当
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

from libs.elder_process_base import (
    ElderProcessBase, ElderRole, SageType, MessageType, ElderMessage
)


class ProjectPhase(Enum):
    """プロジェクトフェーズ"""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


class TaskPriority(Enum):
    """タスク優先度"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class Project:
    """プロジェクト"""
    def __init__(self, project_id:
        """初期化メソッド"""
    str, name: str, description: str):
        self.project_id = project_id
        self.name = name
        self.description = description
        self.phase = ProjectPhase.PLANNING
        self.tasks: List[str] = []  # タスクIDリスト
        self.created_at = datetime.now()
        self.deadline: Optional[datetime] = None
        self.progress = 0.0


class Task:
    """タスク"""
    def __init__(self, task_id:
        """初期化メソッド"""
    str, project_id: str, title: str,
                 priority: TaskPriority = TaskPriority.MEDIUM):
        self.task_id = task_id
        self.project_id = project_id
        self.title = title
        self.priority = priority
        self.status = "pending"
        self.assigned_to: Optional[str] = None
        self.dependencies: List[str] = []
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.estimated_hours = 0
        self.actual_hours = 0


class TaskSageProcess(ElderProcessBase):
    """
    タスク賢者 - プロジェクト管理専門プロセス

    責務:
    - プロジェクトとタスクの管理
    - 優先順位の最適化
    - 進捗の追跡とレポート
    - リソース配分の提案
    """

    def __init__(self):
        """初期化メソッド"""
        super().__init__(
            elder_name="task_sage",
            elder_role=ElderRole.SAGE,
            sage_type=SageType.TASK,
            port=5003
        )

        # プロジェクト管理
        self.projects: Dict[str, Project] = {}
        self.tasks: Dict[str, Task] = {}

        # スケジュール管理
        self.schedule: List[Dict[str, Any]] = []
        self.resource_allocation: Dict[str, float] = {}

        # パス設定
        self.data_dir = Path("data/task_sage")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """初期化処理"""
        self.logger.info("📋 Initializing Task Sage...")

        # 既存プロジェクトの読み込み
        await self._load_projects()

        # スケジュールの読み込み
        await self._load_schedule()

        self.logger.info(f"✅ Task Sage initialized with {len(self.projects)} projects")

    async def process(self):
        """メイン処理"""
        # タスクの優先順位最適化（10分ごと）
        if not hasattr(self, '_last_optimization') or \
           (datetime.now() - self._last_optimization).total_seconds() > 600:
            await self._optimize_task_priorities()
            self._last_optimization = datetime.now()

        # 進捗レポート（30分ごと）
        if not hasattr(self, '_last_report') or \
           (datetime.now() - self._last_report).total_seconds() > 1800:
            await self._generate_progress_report()
            self._last_report = datetime.now()

        # デッドライン監視
        await self._monitor_deadlines()

    async def handle_message(self, message: ElderMessage):
        """メッセージ処理"""
        self.logger.info(f"Received {message.message_type.value} from {message.source_elder}")

        if message.message_type == MessageType.COMMAND:
            await self._handle_command(message)
        elif message.message_type == MessageType.QUERY:
            await self._handle_query(message)
        elif message.message_type == MessageType.REPORT:
            await self._handle_report(message)

    def register_handlers(self):
        """追加のメッセージハンドラー登録"""
        # 基本ハンドラーで十分
        pass

    async def on_cleanup(self):
        """クリーンアップ処理"""
        # プロジェクトとタスクの保存
        await self._save_projects()

        # スケジュールの保存
        await self._save_schedule()

    # プライベートメソッド

    async def _load_projects(self):
        """プロジェクトの読み込み"""
        projects_file = self.data_dir / "projects.json"
        if projects_file.exists():
            try:
                with open(projects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # プロジェクト復元
                    for proj_data in data.get('projects', []):
                        project = Project(
                            project_id=proj_data['id'],
                            name=proj_data['name'],
                            description=proj_data['description']
                        )
                        project.phase = ProjectPhase(proj_data['phase'])
                        project.tasks = proj_data.get('tasks', [])
                        project.progress = proj_data.get('progress', 0.0)

                        self.projects[project.project_id] = project

                    # タスク復元
                    for task_data in data.get('tasks', []):
                        task = Task(
                            task_id=task_data['id'],
                            project_id=task_data['project_id'],
                            title=task_data['title'],
                            priority=TaskPriority(task_data['priority'])
                        )
                        task.status = task_data['status']
                        task.assigned_to = task_data.get('assigned_to')
                        task.dependencies = task_data.get('dependencies', [])

                        self.tasks[task.task_id] = task

                self.logger.info(f"Loaded {len(self.projects)} projects and {len(self.tasks)} tasks" \
                    "Loaded {len(self.projects)} projects and {len(self.tasks)} tasks")

            except Exception as e:
                self.logger.error(f"Failed to load projects: {e}")

    async def _load_schedule(self):
        """スケジュールの読み込み"""
        schedule_file = self.data_dir / "schedule.json"
        if schedule_file.exists():
            try:
                with open(schedule_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.schedule = data.get('schedule', [])
                    self.resource_allocation = data.get('resource_allocation', {})

                self.logger.info(f"Loaded schedule with {len(self.schedule)} items")

            except Exception as e:
                self.logger.error(f"Failed to load schedule: {e}")

    async def _save_projects(self):
        """プロジェクトの保存"""
        try:
            # プロジェクトデータ準備
            projects_data = []
            for project in self.projects.values():
                projects_data.append({
                    'id': project.project_id,
                    'name': project.name,
                    'description': project.description,
                    'phase': project.phase.value,
                    'tasks': project.tasks,
                    'progress': project.progress,
                    'created_at': project.created_at.isoformat(),
                    'deadline': project.deadline.isoformat() if project.deadline else None
                })

            # タスクデータ準備
            tasks_data = []
            for task in self.tasks.values():
                tasks_data.append({
                    'id': task.task_id,
                    'project_id': task.project_id,
                    'title': task.title,
                    'priority': task.priority.value,
                    'status': task.status,
                    'assigned_to': task.assigned_to,
                    'dependencies': task.dependencies,
                    'created_at': task.created_at.isoformat(),
                    'estimated_hours': task.estimated_hours
                })

            # 保存
            projects_file = self.data_dir / "projects.json"
            with open(projects_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'projects': projects_data,
                    'tasks': tasks_data,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            self.logger.info("Projects and tasks saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save projects: {e}")

    async def _save_schedule(self):
        """スケジュールの保存"""
        try:
            schedule_file = self.data_dir / "schedule.json"
            with open(schedule_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'schedule': self.schedule,
                    'resource_allocation': self.resource_allocation,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            self.logger.info("Schedule saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to save schedule: {e}")

    async def _handle_command(self, message: ElderMessage):
        """コマンド処理"""
        command = message.payload.get('command')

        if command == 'create_project':
            # プロジェクト作成
            await self._create_project(message.payload)

        elif command == 'create_task':
            # タスク作成
            await self._create_task(message.payload)

        elif command == 'update_task':
            # タスク更新
            await self._update_task(message.payload)

        elif command == 'execute_task':
            # タスク実行（クロードエルダーから）
            await self._execute_assigned_task(message.payload)

    async def _handle_query(self, message: ElderMessage):
        """クエリ処理"""
        query_type = message.payload.get('query_type')

        if query_type == 'project_status':
            # プロジェクトステータス照会
            project_id = message.payload.get('project_id')
            status = await self._get_project_status(project_id)

            response_msg = ElderMessage(
                message_id=f"project_status_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={'project_status': status},
                priority=message.priority
            )

            await self.send_message(response_msg)

        elif query_type == 'task_recommendations':
            # タスク推奨
            recommendations = await self._get_task_recommendations()

            response_msg = ElderMessage(
                message_id=f"recommendations_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={'recommendations': recommendations},
                priority=message.priority
            )

            await self.send_message(response_msg)

        elif query_type == 'availability':
            # 利用可能性確認
            response_msg = ElderMessage(
                message_id=f"availability_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={
                    'available': True,
                    'capacity': 0.7,
                    'active_projects': len(self.projects),
                    'active_tasks': len([t for t in self.tasks.values() if t.status == 'in_progress'])
                },
                priority=message.priority
            )

            await self.send_message(response_msg)

    async def _handle_report(self, message: ElderMessage):
        """レポート処理"""
        report_type = message.payload.get('type')

        if report_type == 'task_progress':
            # タスク進捗更新
            await self._update_task_progress(message.payload)

        elif report_type == 'resource_usage':
            # リソース使用状況
            await self._update_resource_usage(message.payload)

    async def _create_project(self, payload: Dict[str, Any]):
        """プロジェクト作成"""
        project_id = f"project_{datetime.now().timestamp()}"
        name = payload.get('name', 'Unnamed Project')
        description = payload.get('description', '')

        project = Project(project_id, name, description)
        if 'deadline' in payload:
            project.deadline = datetime.fromisoformat(payload['deadline'])

        self.projects[project_id] = project

        self.logger.info(f"Created project: {name} ({project_id})")

        # 作成通知
        await self.report_to_superior({
            'type': 'project_created',
            'project_id': project_id,
            'name': name
        })

    async def _create_task(self, payload: Dict[str, Any]):
        """タスク作成"""
        task_id = f"task_{datetime.now().timestamp()}"
        project_id = payload.get('project_id')
        title = payload.get('title', 'Unnamed Task')
        priority = TaskPriority(payload.get('priority', TaskPriority.MEDIUM.value))

        if project_id not in self.projects:
            self.logger.warning(f"Project {project_id} not found")
            return

        task = Task(task_id, project_id, title, priority)
        task.estimated_hours = payload.get('estimated_hours', 0)
        task.dependencies = payload.get('dependencies', [])

        self.tasks[task_id] = task
        self.projects[project_id].tasks.append(task_id)

        self.logger.info(f"Created task: {title} ({task_id})")

        # スケジュールに追加
        await self._add_to_schedule(task)

    async def _update_task(self, payload: Dict[str, Any]):
        """タスク更新"""
        task_id = payload.get('task_id')
        if task_id not in self.tasks:
            self.logger.warning(f"Task {task_id} not found")
            return

        task = self.tasks[task_id]

        # ステータス更新
        if 'status' in payload:
            old_status = task.status
            task.status = payload['status']

            if task.status == 'in_progress' and not task.started_at:
                task.started_at = datetime.now()
            elif task.status == 'completed' and not task.completed_at:
                task.completed_at = datetime.now()
                task.actual_hours = (task.completed_at - task.started_at).total_seconds() / 3600

                # プロジェクト進捗更新
                await self._update_project_progress(task.project_id)

            self.logger.info(f"Task {task_id} status: {old_status} -> {task.status}")

        # その他の更新
        if 'assigned_to' in payload:
            task.assigned_to = payload['assigned_to']

        if 'priority' in payload:
            task.priority = TaskPriority(payload['priority'])

    async def _optimize_task_priorities(self):
        """タスク優先順位の最適化"""
        self.logger.info("Optimizing task priorities...")

        # ペンディングタスクを取得
        pending_tasks = [t for t in self.tasks.values() if t.status == 'pending']

        # 優先順位スコア計算
        task_scores = []
        for task in pending_tasks:
            score = self._calculate_priority_score(task)
            task_scores.append((task, score))

        # スコア順にソート
        task_scores.sort(key=lambda x: x[1], reverse=True)

        # 新しいスケジュール生成
        new_schedule = []
        for task, score in task_scores[:10]:  # 上位10タスク
            new_schedule.append({
                'task_id': task.task_id,
                'project_id': task.project_id,
                'title': task.title,
                'priority_score': score,
                'estimated_start': self._estimate_start_time(task)
            })

        self.schedule = new_schedule

        # 最適化結果を報告
        await self.report_to_superior({
            'type': 'priority_optimization',
            'optimized_tasks': len(new_schedule),
            'top_priority': new_schedule[0]['title'] if new_schedule else None
        })

    def _calculate_priority_score(self, task: Task) -> float:
        """優先度スコア計算"""
        score = 0.0

        # 基本優先度
        score += (5 - task.priority.value) * 20

        # プロジェクトの締切
        project = self.projects.get(task.project_id)
        if project and project.deadline:
            days_until_deadline = (project.deadline - datetime.now()).days
            if days_until_deadline < 7:
                score += 30
            elif days_until_deadline < 14:
                score += 20
            elif days_until_deadline < 30:
                score += 10

        # 依存関係
        if not task.dependencies:
            score += 10  # 依存関係がないタスクは早めに実行

        # 経過時間
        age_days = (datetime.now() - task.created_at).days
        score += min(age_days * 2, 20)  # 古いタスクを優先

        return score

    def _estimate_start_time(self, task: Task) -> str:
        """開始時刻の推定"""
        # 簡易実装
        hours_ahead = len([t for t in self.tasks.values()
                          if t.status == 'in_progress']) * 2

        estimated_start = datetime.now() + timedelta(hours=hours_ahead)
        return estimated_start.isoformat()

    async def _generate_progress_report(self):
        """進捗レポート生成"""
        self.logger.info("Generating progress report...")

        # プロジェクト別進捗
        project_progress = {}
        for project in self.projects.values():
            total_tasks = len(project.tasks)
            completed_tasks = len([
                t for t in project.tasks
                if self.tasks.get(t) and self.tasks[t].status == 'completed'
            ])

            project_progress[project.project_id] = {
                'name': project.name,
                'phase': project.phase.value,
                'progress': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks
            }

        # 全体統計
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == 'completed'])
        in_progress_tasks = len([t for t in self.tasks.values() if t.status == 'in_progress'])

        report_msg = ElderMessage(
            message_id=f"progress_report_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder="claude_elder",
            message_type=MessageType.REPORT,
            payload={
                'type': 'progress_report',
                'overall_progress': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'project_progress': project_progress,
                'top_priorities': self.schedule[:5]
            },
            priority=6
        )

        await self.send_message(report_msg)

    async def _monitor_deadlines(self):
        """デッドライン監視"""
        alerts = []

        for project in self.projects.values():
            if project.deadline:
                days_until_deadline = (project.deadline - datetime.now()).days

                if days_until_deadline < 0:
                    alerts.append({
                        'level': 'critical',
                        'project': project.name,
                        'message': f"Project {project.name} is {-days_until_deadline} days overdue!"
                    })
                elif days_until_deadline < 3:
                    alerts.append({
                        'level': 'high',
                        'project': project.name,
                        'message': f"Project {project.name} deadline in {days_until_deadline} days!"
                    })
                elif days_until_deadline < 7:
                    alerts.append({
                        'level': 'medium',
                        'project': project.name,
                        'message': f"Project {project.name} deadline approaching ({days_until_deadline} days)"
                    })

        if alerts:
            # アラートを送信
            alert_msg = ElderMessage(
                message_id=f"deadline_alerts_{datetime.now().timestamp()}",
                source_elder=self.elder_name,
                target_elder="claude_elder",
                message_type=MessageType.REPORT,
                payload={
                    'type': 'deadline_alerts',
                    'alerts': alerts
                },
                priority=8
            )

            await self.send_message(alert_msg)

    async def _get_project_status(self, project_id: str) -> Dict[str, Any]:
        """プロジェクトステータス取得"""
        if project_id not in self.projects:
            return {'error': 'Project not found'}

        project = self.projects[project_id]

        # タスク統計
        task_stats = {
            'total': len(project.tasks),
            'completed': 0,
            'in_progress': 0,
            'pending': 0
        }

        for task_id in project.tasks:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == 'completed':
                    task_stats['completed'] += 1
                elif task.status == 'in_progress':
                    task_stats['in_progress'] += 1
                else:
                    task_stats['pending'] += 1

        return {
            'project_id': project_id,
            'name': project.name,
            'phase': project.phase.value,
            'progress': project.progress,
            'task_stats': task_stats,
            'deadline': project.deadline.isoformat() if project.deadline else None,
            'days_remaining': (project.deadline - datetime.now()).days if project.deadline else None
        }

    async def _get_task_recommendations(self) -> List[Dict[str, Any]]:
        """タスク推奨取得"""
        recommendations = []

        # 優先度の高いペンディングタスク
        high_priority_tasks = [
            t for t in self.tasks.values()
            if t.status == 'pending' and t.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]
        ]

        for task in high_priority_tasks[:5]:
            recommendations.append({
                'task_id': task.task_id,
                'title': task.title,
                'priority': task.priority.value,
                'reason': 'High priority pending task',
                'estimated_hours': task.estimated_hours
            })

        # ブロックされているタスク
        blocked_tasks = [
            t for t in self.tasks.values()
            if t.status == 'pending' and any(
                dep_id in self.tasks and self.tasks[dep_id].status != 'completed'
                for dep_id in t.dependencies
            )
        ]

        if blocked_tasks:
            recommendations.append({
                'type': 'unblock_tasks',
                'message': f"{len(blocked_tasks)} tasks are blocked by dependencies",
                'action': 'Complete dependency tasks first'
            })

        return recommendations

    async def _add_to_schedule(self, task: Task):
        """スケジュールに追加"""
        schedule_item = {
            'task_id': task.task_id,
            'project_id': task.project_id,
            'title': task.title,
            'priority_score': self._calculate_priority_score(task),
            'estimated_start': self._estimate_start_time(task),
            'added_at': datetime.now().isoformat()
        }

        self.schedule.append(schedule_item)

        # スケジュールを優先度順にソート
        self.schedule.sort(key=lambda x: x['priority_score'], reverse=True)

    async def _update_project_progress(self, project_id: str):
        """プロジェクト進捗更新"""
        if project_id not in self.projects:
            return

        project = self.projects[project_id]

        # タスク完了率を計算
        total_tasks = len(project.tasks)
        if total_tasks == 0:
            project.progress = 0.0
            return

        completed_tasks = len([
            t for t in project.tasks
            if self.tasks.get(t) and self.tasks[t].status == 'completed'
        ])

        project.progress = (completed_tasks / total_tasks) * 100

        self.logger.info(f"Project {project.name} progress: {project.progress:.1f}%")

        # フェーズ自動更新
        if project.progress == 100 and project.phase != ProjectPhase.MAINTENANCE:
            if project.phase == ProjectPhase.DEVELOPMENT:
                project.phase = ProjectPhase.TESTING
            elif project.phase == ProjectPhase.TESTING:
                project.phase = ProjectPhase.DEPLOYMENT
            elif project.phase == ProjectPhase.DEPLOYMENT:
                project.phase = ProjectPhase.MAINTENANCE

    async def _update_task_progress(self, progress_data: Dict[str, Any]):
        """タスク進捗更新"""
        task_id = progress_data.get('task_id')
        if task_id in self.tasks:
            task = self.tasks[task_id]

            if 'percent_complete' in progress_data:
                # パーセンテージベースの更新
                percent = progress_data['percent_complete']
                if percent >= 100:
                    task.status = 'completed'
                    task.completed_at = datetime.now()
                elif percent > 0 and task.status == 'pending':
                    task.status = 'in_progress'
                    task.started_at = datetime.now()

            self.logger.info(f"Task {task_id} progress updated")

    async def _update_resource_usage(self, usage_data: Dict[str, Any]):
        """リソース使用状況更新"""
        resource_id = usage_data.get('resource_id')
        usage = usage_data.get('usage', 0.0)

        self.resource_allocation[resource_id] = usage

        # リソース逼迫の警告
        if usage > 0.9:
            self.logger.warning(f"Resource {resource_id} is at {usage*100:.1f}% capacity")

    async def _execute_assigned_task(self, task_data: Dict[str, Any]):
        """割り当てられたタスクの実行"""
        task_id = task_data.get('task_id')
        description = task_data.get('description', '')

        self.logger.info(f"Executing task {task_id}: {description}")

        # タスク管理関連のタスクを実行
        if "schedule" in description.lower() or "plan" in description.lower():
            result = await self._create_schedule(task_data)
        elif "prioritize" in description.lower():
            result = await self._prioritize_tasks(task_data)
        else:
            # 一般的なタスク管理
            result = await self._general_task_management(task_data)

        # 完了報告
        completion_msg = ElderMessage(
            message_id=f"task_complete_{task_id}",
            source_elder=self.elder_name,
            target_elder="claude_elder",
            message_type=MessageType.REPORT,
            payload={
                'type': 'task_complete',
                'task_id': task_id,
                'result': result
            },
            priority=6
        )

        await self.send_message(completion_msg)

    async def _create_schedule(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """スケジュール作成"""
        # シミュレーション
        await asyncio.sleep(2)

        return {
            'status': 'completed',
            'schedule': {
                'items': len(self.schedule),
                'next_week': 15,
                'critical_path': ['task_001', 'task_003', 'task_007']
            }
        }

    async def _prioritize_tasks(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """タスク優先順位付け"""
        # 実際の優先順位最適化を実行
        await self._optimize_task_priorities()

        return {
            'status': 'completed',
            'prioritization': {
                'optimized_count': len(self.schedule),
                'top_priority': self.schedule[0]['title'] if self.schedule else None
            }
        }

    async def _general_task_management(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """一般的なタスク管理"""
        # シミュレーション
        await asyncio.sleep(1)

        return {
            'status': 'completed',
            'message': 'Task management operation completed'
        }


# プロセス起動
if __name__ == "__main__":
    from libs.elder_process_base import run_elder_process
    run_elder_process(TaskSageProcess)
