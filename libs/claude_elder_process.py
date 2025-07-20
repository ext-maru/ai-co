#!/usr/bin/env python3
"""
クロードエルダープロセス
Claude Elder Process - 開発実行責任者プロセス

4賢者を統括し、開発タスクを実行するプロセス
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from libs.elder_process_base import (
    ElderProcessBase, ElderRole, SageType, MessageType, ElderMessage
)


class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class DevelopmentTask:
    """開発タスク"""
    def __init__(self, task_id: str, description: str, priority: int = 5):
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.assigned_sage: Optional[str] = None
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None


class ClaudeElderProcess(ElderProcessBase):
    """
    クロードエルダー - 開発実行責任者プロセス

    責務:
    - 開発タスクの管理と実行
    - 4賢者への指示と協調
    - グランドエルダーへの報告
    - 開発品質の保証
    """

    def __init__(self):
        super().__init__(
            elder_name="claude_elder",
            elder_role=ElderRole.CLAUDE_ELDER,
            port=5001
        )

        # クロードエルダー固有の状態
        self.task_queue: List[DevelopmentTask] = []
        self.active_tasks: Dict[str, DevelopmentTask] = {}
        self.sage_status: Dict[str, Dict[str, Any]] = {
            "knowledge_sage": {"status": "unknown", "capacity": 1.0},
            "task_sage": {"status": "unknown", "capacity": 1.0},
            "incident_sage": {"status": "unknown", "capacity": 1.0},
            "rag_sage": {"status": "unknown", "capacity": 1.0}
        }

        # 開発統計
        self.dev_stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_completion_time": 0,
            "sage_utilization": {}
        }

    async def initialize(self):
        """初期化処理"""
        self.logger.info("🤖 Initializing Claude Elder...")

        # 4賢者の状態確認
        await self._check_sage_availability()

        # 開発環境の準備
        await self._prepare_development_environment()

        self.logger.info("✅ Claude Elder initialization completed")

    async def process(self):
        """メイン処理"""
        # タスクキューの処理
        if self.task_queue:
            await self._process_task_queue()

        # アクティブタスクの監視
        await self._monitor_active_tasks()

        # 賢者の負荷分散
        await self._balance_sage_load()

        # 定期報告（1時間ごと）
        if hasattr(self, '_last_report') and \
           (datetime.now() - self._last_report).total_seconds() > 3600:
            await self._send_periodic_report()

    async def handle_message(self, message: ElderMessage):
        """メッセージ処理"""
        self.logger.info(f"Received {message.message_type.value} from {message.source_elder}")

        if message.message_type == MessageType.COMMAND:
            await self._handle_command(message)
        elif message.message_type == MessageType.REPORT:
            await self._handle_sage_report(message)
        elif message.message_type == MessageType.QUERY:
            await self._handle_query(message)

    def register_handlers(self):
        """追加のメッセージハンドラー登録"""
        # 基本的なハンドラーで十分
        pass

    async def on_cleanup(self):
        """クリーンアップ処理"""
        # 未完了タスクの保存
        await self._save_pending_tasks()

        # 最終報告
        await self._send_final_report()

    # プライベートメソッド

    async def _check_sage_availability(self):
        """4賢者の利用可能性確認"""
        for sage_name in self.sage_status.keys():
            status_query = ElderMessage(
                message_id=f"sage_check_{sage_name}_{datetime.now().timestamp()}",
                source_elder=self.elder_name,
                target_elder=sage_name,
                message_type=MessageType.QUERY,
                payload={"query_type": "availability"},
                priority=8,
                requires_ack=True
            )

            await self.send_message(status_query)

    async def _prepare_development_environment(self):
        """開発環境の準備"""
        # TODO: 実際の環境準備処理
        self.logger.info("Development environment prepared")

    async def _process_task_queue(self):
        """タスクキューの処理"""
        # 優先度順にソート
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)

        for task in self.task_queue[:]:
            # 適切な賢者を選択
            assigned_sage = self._select_sage_for_task(task)

            if assigned_sage:
                # タスクを割り当て
                await self._assign_task_to_sage(task, assigned_sage)
                self.task_queue.remove(task)
                self.active_tasks[task.task_id] = task

    def _select_sage_for_task(self, task: DevelopmentTask) -> Optional[str]:
        """タスクに適した賢者を選択"""
        # タスクの内容に基づいて賢者を選択
        description_lower = task.description.lower()

        if any(keyword in description_lower for keyword in ["knowledge", "document", "learn"]):
            sage_type = "knowledge_sage"
        elif any(keyword in description_lower for keyword in ["task", "project", "plan"]):
            sage_type = "task_sage"
        elif any(keyword in description_lower for keyword in ["bug", "error", "incident"]):
            sage_type = "incident_sage"
        elif any(keyword in description_lower for keyword in ["search", "find", "analyze"]):
            sage_type = "rag_sage"
        else:
            # デフォルトはタスク賢者
            sage_type = "task_sage"

        # 利用可能性と負荷を確認
        sage_info = self.sage_status.get(sage_type)
        if sage_info and sage_info['status'] == 'active' and sage_info['capacity'] > 0.2:
            return sage_type

        # 代替賢者を探す
        for alt_sage, info in self.sage_status.items():
            if info['status'] == 'active' and info['capacity'] > 0.3:
                return alt_sage

        return None

    async def _assign_task_to_sage(self, task: DevelopmentTask, sage_name: str):
        """賢者にタスクを割り当て"""
        task.assigned_sage = sage_name
        task.status = TaskStatus.ASSIGNED

        assign_msg = ElderMessage(
            message_id=f"task_assign_{task.task_id}",
            source_elder=self.elder_name,
            target_elder=sage_name,
            message_type=MessageType.COMMAND,
            payload={
                "command": "execute_task",
                "task_id": task.task_id,
                "description": task.description,
                "priority": task.priority
            },
            priority=task.priority,
            requires_ack=True
        )

        await self.send_message(assign_msg)

        # 賢者の負荷を更新
        self.sage_status[sage_name]['capacity'] *= 0.8

        self.logger.info(f"Task {task.task_id} assigned to {sage_name}")

    async def _monitor_active_tasks(self):
        """アクティブタスクの監視"""
        for task_id, task in list(self.active_tasks.items()):
            if task.status == TaskStatus.IN_PROGRESS:
                # タイムアウトチェック
                elapsed = (datetime.now() - task.created_at).total_seconds()
                if elapsed > 3600:  # 1時間以上
                    self.logger.warning(f"Task {task_id} is taking too long")
                    await self._handle_task_timeout(task)

    async def _balance_sage_load(self):
        """賢者の負荷分散"""
        # 負荷の偏りを検出
        capacities = [info['capacity'] for info in self.sage_status.values()]
        if max(capacities) - min(capacities) > 0.5:
            # 負荷の再分配が必要
            await self._redistribute_tasks()

    async def _handle_command(self, message: ElderMessage):
        """コマンド処理"""
        command = message.payload.get('command')

        if command == 'create_task':
            # 新規タスク作成
            task = DevelopmentTask(
                task_id=f"task_{datetime.now().timestamp()}",
                description=message.payload.get('description', ''),
                priority=message.payload.get('priority', 5)
            )
            self.task_queue.append(task)

        elif command == 'emergency_protocol':
            # 緊急プロトコル
            await self._activate_emergency_protocol()

    async def _handle_sage_report(self, message: ElderMessage):
        """賢者からの報告処理"""
        sage_name = message.source_elder
        report_type = message.payload.get('type')

        if report_type == 'task_complete':
            task_id = message.payload.get('task_id')
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = message.payload.get('result')

                # 統計更新
                self.dev_stats['tasks_completed'] += 1

                # グランドエルダーへ報告
                await self._report_task_completion(task)

                # タスクをアクティブリストから削除
                del self.active_tasks[task_id]

                # 賢者の負荷を回復
                if sage_name in self.sage_status:
                    self.sage_status[sage_name]['capacity'] = min(1.0,
                        self.sage_status[sage_name]['capacity'] + 0.3)

        elif report_type == 'status':
            # 賢者のステータス更新
            if sage_name in self.sage_status:
                self.sage_status[sage_name].update(message.payload.get('status', {}))

    async def _handle_query(self, message: ElderMessage):
        """クエリ処理"""
        query_type = message.payload.get('query_type')

        if query_type == 'task_status':
            # タスクステータスの問い合わせ
            task_id = message.payload.get('task_id')
            status = self._get_task_status(task_id)

            response_msg = ElderMessage(
                message_id=f"status_response_{message.message_id}",
                source_elder=self.elder_name,
                target_elder=message.source_elder,
                message_type=MessageType.REPORT,
                payload={"task_id": task_id, "status": status},
                priority=message.priority
            )

            await self.send_message(response_msg)

    def _get_task_status(self, task_id: str) -> Dict[str, Any]:
        """タスクステータス取得"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task.status.value,
                "assigned_sage": task.assigned_sage,
                "created_at": task.created_at.isoformat()
            }

        return {"task_id": task_id, "status": "not_found"}

    async def _report_task_completion(self, task: DevelopmentTask):
        """タスク完了をグランドエルダーに報告"""
        report_msg = ElderMessage(
            message_id=f"task_complete_report_{task.task_id}",
            source_elder=self.elder_name,
            target_elder="grand_elder_maru",
            message_type=MessageType.REPORT,
            payload={
                "type": "task_complete",
                "task_id": task.task_id,
                "description": task.description,
                "duration": (task.completed_at - task.created_at).total_seconds(),
                "assigned_sage": task.assigned_sage,
                "result": task.result
            },
            priority=6
        )

        await self.send_message(report_msg)

    async def _send_periodic_report(self):
        """定期報告"""
        report_msg = ElderMessage(
            message_id=f"periodic_report_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder="grand_elder_maru",
            message_type=MessageType.REPORT,
            payload={
                "type": "periodic",
                "stats": self.dev_stats,
                "active_tasks": len(self.active_tasks),
                "pending_tasks": len(self.task_queue),
                "sage_status": self.sage_status
            },
            priority=5
        )

        await self.send_message(report_msg)
        self._last_report = datetime.now()

    async def _handle_task_timeout(self, task: DevelopmentTask):
        """タスクタイムアウト処理"""
        # 賢者に状態確認
        if task.assigned_sage:
            check_msg = ElderMessage(
                message_id=f"task_check_{task.task_id}",
                source_elder=self.elder_name,
                target_elder=task.assigned_sage,
                message_type=MessageType.QUERY,
                payload={
                    "query_type": "task_progress",
                    "task_id": task.task_id
                },
                priority=8
            )

            await self.send_message(check_msg)

    async def _redistribute_tasks(self):
        """タスクの再分配"""
        self.logger.info("Redistributing tasks for load balancing...")

        # TODO: 実際の再分配ロジック
        pass

    async def _activate_emergency_protocol(self):
        """緊急プロトコル起動"""
        self.logger.warning("🚨 Activating emergency protocol")

        # 全賢者に緊急モード通知
        for sage_name in self.sage_status.keys():
            emergency_msg = ElderMessage(
                message_id=f"emergency_{sage_name}_{datetime.now().timestamp()}",
                source_elder=self.elder_name,
                target_elder=sage_name,
                message_type=MessageType.EMERGENCY,
                payload={
                    "protocol": "emergency",
                    "actions": ["Suspend non-critical tasks", "Focus on emergency"]
                },
                priority=10
            )

            await self.send_message(emergency_msg)

    async def _save_pending_tasks(self):
        """未完了タスクの保存"""
        # TODO: タスクの永続化
        pending_count = len(self.task_queue) + len(self.active_tasks)
        self.logger.info(f"Saving {pending_count} pending tasks...")

    async def _send_final_report(self):
        """最終報告"""
        final_report = ElderMessage(
            message_id=f"final_report_{datetime.now().timestamp()}",
            source_elder=self.elder_name,
            target_elder="grand_elder_maru",
            message_type=MessageType.REPORT,
            payload={
                "type": "shutdown",
                "final_stats": self.dev_stats,
                "pending_tasks": len(self.task_queue) + len(self.active_tasks)
            },
            priority=8
        )

        await self.send_message(final_report)


# プロセス起動
if __name__ == "__main__":
    from libs.elder_process_base import run_elder_process
    run_elder_process(ClaudeElderProcess)
