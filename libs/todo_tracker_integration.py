#!/usr/bin/env python3
"""
TodoList and Task Tracker Integration System
TodoListとタスクトラッカーの完全統合システム
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.postgres_claude_task_tracker import (
    PostgreSQLClaudeTaskTracker,
    TaskPriority,
    TaskStatus,
    TaskType,
    create_postgres_task_tracker,
)

logger = logging.getLogger(__name__)


class TodoTrackerIntegration:
    """TodoListとタスクトラッカーの統合管理クラス"""

    def __init__(self, auto_sync: bool = True, sync_interval: int = 300, user_id: str = "claude_elder"):
        """
        初期化

        Args:
            auto_sync: 自動同期の有効化
            sync_interval: 同期間隔（秒）
            user_id: ユーザーID（担当者として使用）
        """
        self.auto_sync = auto_sync
        self.sync_interval = sync_interval
        self.user_id = user_id
        # UUIDを使用して一意のセッションIDを生成
        self.session_id = f"session-{uuid.uuid4().hex[:8]}"
        self.tracker: Optional[PostgreSQLClaudeTaskTracker] = None
        self._running = False
        self._sync_task = None
        self._todo_cache: List[Dict] = []
        self._last_sync = None

    async def initialize(self):
        """初期化処理"""
        self.tracker = await create_postgres_task_tracker()
        logger.info("TodoTracker Integration initialized")

        if self.auto_sync:
            await self.start_auto_sync()

    async def start_auto_sync(self):
        """自動同期の開始"""
        if self._running:
            logger.warning("Auto sync already running")
            return

        self._running = True
        self._sync_task = asyncio.create_task(self._auto_sync_loop())
        logger.info(f"Auto sync started (interval: {self.sync_interval}s)")

    async def stop_auto_sync(self):
        """自動同期の停止"""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Auto sync stopped")

    async def _auto_sync_loop(self):
        """自動同期ループ"""
        while self._running:
            try:
                await self.sync_both_ways()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Auto sync error: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機

    async def sync_both_ways(self, personal_only: bool = True):
        """双方向同期の実行
        
        Args:
            personal_only: 自分のタスクのみ同期するか
        """
        try:
            # 1. 現在のTodoListを取得（シミュレーション）
            todos = self.get_current_todos()

            # 2. TodoList → タスクトラッカー
            if todos:
                synced_to_tracker = await self.tracker.sync_with_todo_list(todos)
                logger.info(f"Synced {synced_to_tracker} todos to tracker")

            # 3. タスクトラッカー → TodoList
            if personal_only:
                # 自分のタスクのみ取得
                tasks = await self.tracker.list_tasks(
                    assigned_to=self.user_id,
                    limit=20
                )
                tracker_todos = self._format_tasks_to_todos(tasks)
            else:
                tracker_todos = await self.tracker.sync_tracker_to_todo_list()
            
            self.update_todo_list(tracker_todos)
            logger.info(f"Synced {len(tracker_todos)} tasks from tracker (user: {self.user_id})")

            self._last_sync = datetime.now()

        except Exception as e:
            logger.error(f"Sync error: {e}")
            raise

    def get_current_todos(self) -> List[Dict]:
        """
        現在のTodoListを取得
        注: 実際の実装では、Claude CodeのTodoReadからデータを取得
        """
        # デモ用: キャッシュから返す
        return self._todo_cache

    def update_todo_list(self, todos: List[Dict]):
        """
        TodoListを更新
        注: 実際の実装では、Claude CodeのTodoWriteにデータを送信
        """
        self._todo_cache = todos
        logger.info(f"Updated todo cache with {len(todos)} items")

    async def create_task_with_todo_sync(self, **kwargs) -> str:
        """
        タスク作成とTodoList同期

        Args:
            **kwargs: タスク作成パラメータ

        Returns:
            str: タスクID
        """
        # デフォルト値を設定
        kwargs.setdefault("assigned_to", self.user_id)
        kwargs.setdefault("created_by", self.user_id)
        
        # タグにユーザーとセッション情報を追加
        tags = kwargs.get("tags", [])
        tags.extend([f"user-{self.user_id}", f"{self.session_id}"])
        kwargs["tags"] = list(set(tags))  # 重複排除
        
        # メタデータにセッション情報を追加
        metadata = kwargs.get("metadata", {})
        metadata.update({
            "session_id": self.session_id,
            "user_id": self.user_id
        })
        kwargs["metadata"] = metadata
        
        # タスクを作成
        task_id = await self.tracker.create_task(**kwargs)

        # TodoListに追加
        todo = {
            "id": f"task-{task_id}",
            "content": kwargs["title"],
            "status": "pending",
            "priority": kwargs.get("priority", TaskPriority.MEDIUM).value.lower()
        }

        # 現在のTodoListに追加
        current_todos = self.get_current_todos()
        current_todos.append(todo)
        self.update_todo_list(current_todos)

        logger.info(f"Created personal task {task_id} for user {self.user_id}")
        return task_id

    async def update_task_with_todo_sync(self, task_id: str, **kwargs):
        """
        タスク更新とTodoList同期

        Args:
            task_id: タスクID
            **kwargs: 更新パラメータ
        """
        # タスクを更新
        await self.tracker.update_task(task_id, **kwargs)

        # TodoListも更新
        if "status" in kwargs:
            await self.sync_both_ways()

        logger.info(f"Updated task {task_id} with todo sync")

    def _format_tasks_to_todos(self, tasks: List[Dict]) -> List[Dict]:
        """タスクリストをTodoList形式に変換"""
        todos = []
        for task in tasks:
            if task["status"] in ["pending", "in_progress"]:
                todo = {
                    "id": task.get("metadata", {}).get("todo_id") or f"task-{task['task_id']}",
                    "content": task["title"],
                    "status": self._map_status_to_todo(task["status"]),
                    "priority": self._map_priority_to_todo(task["priority"])
                }
                todos.append(todo)
        return todos

    def _map_status_to_todo(self, status: str) -> str:
        """TaskStatusをTodoListステータスにマッピング"""
        mapping = {
            "pending": "pending",
            "in_progress": "in_progress",
            "completed": "completed",
            "failed": "pending",
            "cancelled": "completed",
            "review": "in_progress",
            "blocked": "pending"
        }
        return mapping.get(status, "pending")

    def _map_priority_to_todo(self, priority: str) -> str:
        """TaskPriorityをTodoList優先度にマッピング"""
        mapping = {
            "critical": "high",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        return mapping.get(priority, "medium")

    async def get_my_tasks(self, status_filter: Optional[List[str]] = None) -> List[Dict]:
        """自分のタスクを取得
        
        Args:
            status_filter: ステータスフィルター
            
        Returns:
            List[Dict]: タスクリスト
        """
        tasks = await self.tracker.list_tasks(assigned_to=self.user_id)
        
        # ステータスフィルターがある場合は適用
        if status_filter:
            filtered_tasks = []
            for task in tasks:
                if task.get("status") in status_filter:
                    filtered_tasks.append(task)
            tasks = filtered_tasks
            
        logger.info(f"Retrieved {len(tasks)} personal tasks for {self.user_id}")
        return tasks

    async def get_pending_tasks_from_previous_sessions(self) -> List[Dict]:
        """
        前回のセッションから未完了タスクを取得
        
        Returns:
            List[Dict]: 未完了タスクリスト
        """
        # 自分の未完了タスクを取得（現在のセッション以外）
        all_my_tasks = await self.tracker.list_tasks(
            assigned_to=self.user_id
        )
        
        # pendingとin_progressのタスクのみフィルター
        active_tasks = []
        for task in all_my_tasks:
            if task.get("status") in ["pending", "in_progress"]:
                active_tasks.append(task)
        
        # 現在のセッション以外のタスクをフィルター
        previous_tasks = []
        for task in active_tasks:
            task_tags = task.get("tags", [])
            task_session = None
            
            # タスクのセッションIDを抽出
            for tag in task_tags:
                if tag.startswith("session-"):
                    task_session = tag
                    break
            
            # 現在のセッション以外のタスクを取得
            if task_session and task_session != self.session_id:
                previous_tasks.append(task)
        
        logger.info(f"Found {len(previous_tasks)} pending tasks from previous sessions")
        return previous_tasks

    async def inherit_pending_tasks(self, confirm_prompt: bool = True) -> int:
        """
        前回のセッションから未完了タスクを引き継ぎ
        
        Args:
            confirm_prompt: 確認プロンプトを表示するか
            
        Returns:
            int: 引き継いだタスク数
        """
        previous_tasks = await self.get_pending_tasks_from_previous_sessions()
        
        if not previous_tasks:
            logger.info("No pending tasks from previous sessions")
            return 0
        
        if confirm_prompt:
            print(f"\n📋 前回のセッションから {len(previous_tasks)} 個の未完了タスクが見つかりました:")
            for task in previous_tasks[:5]:  # 最大5件表示
                status_emoji = "⏳" if task["status"] == "pending" else "🔄"
                print(f"  {status_emoji} {task['title']}")
            
            if len(previous_tasks) > 5:
                print(f"  ... 他 {len(previous_tasks) - 5} 件")
            
            response = input("\n引き継ぎますか？ (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ 引き継ぎをキャンセルしました")
                return 0
        
        # タスクを現在のセッションに移行
        inherited_count = 0
        for task in previous_tasks:
            try:
                # タグを更新（現在のセッションに変更）
                current_tags = task.get("tags", [])
                new_tags = []
                
                for tag in current_tags:
                    if not tag.startswith("session-"):
                        new_tags.append(tag)
                
                # 現在のセッションタグを追加
                new_tags.append(self.session_id)
                
                # メタデータを更新
                current_metadata = task.get("metadata", {})
                current_metadata["session_id"] = self.session_id
                current_metadata["inherited_from"] = task.get("metadata", {}).get("session_id")
                current_metadata["inherited_at"] = datetime.now().isoformat()
                
                # タスクを更新（metadataをJSON文字列に変換）
                await self.tracker.update_task(
                    task["task_id"],
                    tags=new_tags,
                    metadata=json.dumps(current_metadata)
                )
                
                inherited_count += 1
                logger.info(f"Inherited task: {task['task_id']} - {task['title']}")
                
            except Exception as e:
                logger.error(f"Failed to inherit task {task['task_id']}: {e}")
        
        if inherited_count > 0:
            print(f"✅ {inherited_count} 個のタスクを現在のセッションに引き継ぎました")
            
            # TodoListを同期して引き継いだタスクを反映
            await self.sync_both_ways(personal_only=True)
        
        return inherited_count

    async def auto_inherit_if_pending(self) -> bool:
        """
        未完了タスクがある場合は自動で引き継ぎ提案
        
        Returns:
            bool: 引き継ぎを実行したか
        """
        previous_tasks = await self.get_pending_tasks_from_previous_sessions()
        
        if not previous_tasks:
            return False
        
        # 3個以下なら自動で提案、それ以上は明示的な操作を推奨
        if len(previous_tasks) <= 3:
            inherited = await self.inherit_pending_tasks(confirm_prompt=True)
            return inherited > 0
        else:
            print(f"\n💡 前回のセッションから {len(previous_tasks)} 個の未完了タスクがあります")
            print("   多くのタスクがあるため、以下のコマンドで引き継ぎを確認してください:")
            print(f"   todo-tracker-sync resume --user {self.user_id}")
            return False

    async def get_sync_status(self) -> Dict:
        """同期状態の取得"""
        tracker_stats = await self.tracker.get_task_statistics()
        
        # 自分のタスク統計も取得
        my_tasks = await self.get_my_tasks()
        my_stats = {
            "total": len(my_tasks),
            "pending": len([t for t in my_tasks if t["status"] == "pending"]),
            "in_progress": len([t for t in my_tasks if t["status"] == "in_progress"]),
            "completed": len([t for t in my_tasks if t["status"] == "completed"])
        }
        
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "auto_sync_enabled": self.auto_sync,
            "sync_interval": self.sync_interval,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "todo_count": len(self._todo_cache),
            "my_tasks_stats": my_stats,
            "global_tracker_stats": tracker_stats,
            "sync_running": self._running
        }

    async def import_todos_from_json(self, json_path: str) -> int:
        """JSONファイルからTodoListをインポート"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                todos = json.load(f)

            self._todo_cache = todos
            synced = await self.tracker.sync_with_todo_list(todos)
            logger.info(f"Imported {synced} todos from {json_path}")
            return synced

        except Exception as e:
            logger.error(f"Import error: {e}")
            raise

    async def export_todos_to_json(self, json_path: str):
        """TodoListをJSONファイルにエクスポート"""
        try:
            todos = await self.tracker.sync_tracker_to_todo_list()
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(todos, f, ensure_ascii=False, indent=2)

            logger.info(f"Exported {len(todos)} todos to {json_path}")

        except Exception as e:
            logger.error(f"Export error: {e}")
            raise


# CLIインターフェース
async def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="TodoList and Task Tracker Integration")
    parser.add_argument("command", choices=["sync", "status", "import", "export", "daemon", "my-tasks", "resume"])
    parser.add_argument("--file", help="JSON file path for import/export")
    parser.add_argument("--interval", type=int, default=300, help="Sync interval in seconds")
    parser.add_argument("--user", default="claude_elder", help="User ID for personal tasks")
    parser.add_argument("--all", action="store_true", help="Sync all tasks, not just personal")
    parser.add_argument("--auto-inherit", action="store_true", help="Auto inherit pending tasks on sync")
    parser.add_argument("--force", action="store_true", help="Force inherit without confirmation")
    args = parser.parse_args()

    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 統合システム初期化
    integration = TodoTrackerIntegration(
        auto_sync=(args.command == "daemon"),
        sync_interval=args.interval,
        user_id=args.user
    )
    await integration.initialize()

    try:
        if args.command == "sync":
            # 自動継承チェック
            if args.auto_inherit:
                await integration.auto_inherit_if_pending()
            
            # 手動同期
            await integration.sync_both_ways(personal_only=not args.all)
            print(f"✅ Sync completed for user: {args.user}")
            
            # 初回同期時に継承提案（auto-inheritが指定されていない場合）
            if not args.auto_inherit:
                await integration.auto_inherit_if_pending()

        elif args.command == "status":
            # ステータス表示
            status = await integration.get_sync_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))

        elif args.command == "my-tasks":
            # 自分のタスク一覧
            tasks = await integration.get_my_tasks()
            print(f"\n📋 {args.user}'s Tasks ({len(tasks)} total):\n")
            for task in tasks:
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "🚫",
                    "review": "👀",
                    "blocked": "🚧"
                }.get(task["status"], "❓")
                
                priority_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(task["priority"], "⚪")
                
                print(f"{status_emoji} {priority_emoji} [{task['task_id'][:8]}] {task['title']}")
                if task.get("tags"):
                    print(f"   🏷️  Tags: {', '.join(task['tags'])}")
            print()

        elif args.command == "resume":
            # セッション継承
            inherited = await integration.inherit_pending_tasks(
                confirm_prompt=not args.force
            )
            if inherited == 0:
                print("📭 引き継ぐタスクはありませんでした")

        elif args.command == "import":
            # インポート
            if not args.file:
                print("❌ Please specify --file")
                return
            count = await integration.import_todos_from_json(args.file)
            print(f"✅ Imported {count} todos")

        elif args.command == "export":
            # エクスポート
            if not args.file:
                print("❌ Please specify --file")
                return
            await integration.export_todos_to_json(args.file)
            print(f"✅ Exported to {args.file}")

        elif args.command == "daemon":
            # デーモンモード
            print(f"🔄 Starting sync daemon (interval: {args.interval}s)")
            print("Press Ctrl+C to stop")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                await integration.stop_auto_sync()
                print("\n👋 Daemon stopped")

    finally:
        # クリーンアップ
        if integration._running:
            await integration.stop_auto_sync()


if __name__ == "__main__":
    asyncio.run(main())