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

    def __init__(self, auto_sync: bool = True, sync_interval: int = 300):
        """
        初期化

        Args:
            auto_sync: 自動同期の有効化
            sync_interval: 同期間隔（秒）
        """
        self.auto_sync = auto_sync
        self.sync_interval = sync_interval
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

    async def sync_both_ways(self):
        """双方向同期の実行"""
        try:
            # 1. 現在のTodoListを取得（シミュレーション）
            todos = self.get_current_todos()

            # 2. TodoList → タスクトラッカー
            if todos:
                synced_to_tracker = await self.tracker.sync_with_todo_list(todos)
                logger.info(f"Synced {synced_to_tracker} todos to tracker")

            # 3. タスクトラッカー → TodoList
            tracker_todos = await self.tracker.sync_tracker_to_todo_list()
            self.update_todo_list(tracker_todos)
            logger.info(f"Synced {len(tracker_todos)} tasks from tracker")

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

        logger.info(f"Created task {task_id} with todo sync")
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

    async def get_sync_status(self) -> Dict:
        """同期状態の取得"""
        tracker_stats = await self.tracker.get_task_statistics()
        
        return {
            "auto_sync_enabled": self.auto_sync,
            "sync_interval": self.sync_interval,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "todo_count": len(self._todo_cache),
            "tracker_stats": tracker_stats,
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
    parser.add_argument("command", choices=["sync", "status", "import", "export", "daemon"])
    parser.add_argument("--file", help="JSON file path for import/export")
    parser.add_argument("--interval", type=int, default=300, help="Sync interval in seconds")
    args = parser.parse_args()

    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 統合システム初期化
    integration = TodoTrackerIntegration(
        auto_sync=(args.command == "daemon"),
        sync_interval=args.interval
    )
    await integration.initialize()

    try:
        if args.command == "sync":
            # 手動同期
            await integration.sync_both_ways()
            print("✅ Sync completed")

        elif args.command == "status":
            # ステータス表示
            status = await integration.get_sync_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))

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