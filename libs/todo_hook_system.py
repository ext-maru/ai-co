#!/usr/bin/env python3
"""
Todo Hook System for Claude Code Integration
Claude CodeのTodoList操作をフックして自動同期
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TodoHookSystem:
    """TodoList操作のフックシステム"""

    def __init__(self, integration_module=None):
        """
        初期化

        Args:
            integration_module: TodoTrackerIntegrationインスタンス
        """
        self.integration = integration_module
        self.hook_file = Path.home() / ".claude_todo_hook"
        self.last_todos: List[Dict] = []
        self._monitor_task = None
        self._running = False

    async def start_monitoring(self):
        """TodoListの監視開始"""
        if self._running:
            logger.warning("Todo monitoring already running")
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Todo monitoring started")

    async def stop_monitoring(self):
        """TodoListの監視停止"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Todo monitoring stopped")

    async def _monitor_loop(self):
        """監視ループ"""
        while self._running:
            try:
                # フックファイルをチェック
                if self.hook_file.exists():
                    await self._process_hook_file()

                await asyncio.sleep(1)  # 1秒ごとにチェック

            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)

    async def _process_hook_file(self):
        """フックファイルの処理"""
        try:
            with open(self.hook_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # TodoListデータを抽出
            todos = self._extract_todos_from_content(content)
            
            if todos and todos != self.last_todos:
                logger.info(f"Detected todo change: {len(todos)} items")
                
                # 統合モジュールに通知
                if self.integration:
                    self.integration.update_todo_list(todos)
                    await self.integration.sync_both_ways()

                self.last_todos = todos

            # 処理済みファイルを削除
            self.hook_file.unlink()

        except Exception as e:
            logger.error(f"Hook file processing error: {e}")

    def _extract_todos_from_content(self, content: str) -> List[Dict]:
        """コンテンツからTodoListデータを抽出"""
        try:
            # JSON形式のTodoListを探す
            json_match = re.search(r'\[{.*?}\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            # 構造化されたテキスト形式を探す
            todos = []
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('- '):
                    # 簡易的なパース
                    parts = line.strip('- ').split('|')
                    if len(parts) >= 3:
                        todos.append({
                            "id": f"todo-{len(todos)+1}",
                            "content": parts[0].strip(),
                            "status": parts[1].strip() if len(parts) > 1 else "pending",
                            "priority": parts[2].strip() if len(parts) > 2 else "medium"
                        })

            return todos

        except Exception as e:
            logger.error(f"Todo extraction error: {e}")
            return []

    def create_hook_file(self, todos: List[Dict]):
        """フックファイルの作成（デバッグ用）"""
        try:
            with open(self.hook_file, 'w', encoding='utf-8') as f:
                json.dump(todos, f, ensure_ascii=False, indent=2)
            logger.info(f"Created hook file with {len(todos)} todos")
        except Exception as e:
            logger.error(f"Hook file creation error: {e}")


class TodoCommandWrapper:
    """TodoList操作コマンドのラッパー"""

    def __init__(self):
        self.commands = {
            "todo-add": self._add_todo,
            "todo-update": self._update_todo,
            "todo-complete": self._complete_todo,
            "todo-list": self._list_todos,
            "todo-sync": self._sync_todos
        }

    async def execute(self, command: str, args: List[str]):
        """コマンド実行"""
        if command in self.commands:
            return await self.commands[command](args)
        else:
            raise ValueError(f"Unknown command: {command}")

    async def _add_todo(self, args: List[str]):
        """Todo追加"""
        if len(args) < 1:
            return "Usage: todo-add <content> [priority]"

        content = args[0]
        priority = args[1] if len(args) > 1 else "medium"

        # TodoTrackerIntegrationを使用してタスク作成
        from libs.todo_tracker_integration import TodoTrackerIntegration
        from libs.postgres_claude_task_tracker import TaskType, TaskPriority
        
        integration = TodoTrackerIntegration()
        await integration.initialize()

        # 優先度をEnumに変換
        priority_map = {
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW
        }
        priority_enum = priority_map.get(priority.lower(), TaskPriority.MEDIUM)

        task_id = await integration.create_task_with_todo_sync(
            title=content,
            task_type=TaskType.FEATURE,
            priority=priority_enum,
            created_by="todo_command"
        )

        return f"✅ Added todo: {content} (ID: {task_id})"

    async def _update_todo(self, args: List[str]):
        """Todo更新"""
        if len(args) < 2:
            return "Usage: todo-update <id> <status>"

        todo_id = args[0]
        status = args[1]

        # タスクIDを抽出
        task_id = todo_id.replace("task-", "") if todo_id.startswith("task-") else todo_id

        from libs.todo_tracker_integration import TodoTrackerIntegration
        integration = TodoTrackerIntegration()
        await integration.initialize()

        await integration.update_task_with_todo_sync(
            task_id=task_id,
            status=status
        )

        return f"✅ Updated todo: {todo_id} -> {status}"

    async def _complete_todo(self, args: List[str]):
        """Todo完了"""
        if len(args) < 1:
            return "Usage: todo-complete <id>"

        todo_id = args[0]
        return await self._update_todo([todo_id, "completed"])

    async def _list_todos(self, args: List[str]):
        """Todo一覧"""
        from libs.todo_tracker_integration import TodoTrackerIntegration
        integration = TodoTrackerIntegration()
        await integration.initialize()

        # タスクトラッカーから取得
        todos = await integration.tracker.sync_tracker_to_todo_list()

        if not todos:
            return "📋 No active todos"

        result = "📋 Active Todos:\n"
        for todo in todos:
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅"
            }.get(todo["status"], "❓")

            priority_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(todo["priority"], "⚪")

            result += f"{status_emoji} {priority_emoji} [{todo['id']}] {todo['content']}\n"

        return result

    async def _sync_todos(self, args: List[str]):
        """Todo同期"""
        from libs.todo_tracker_integration import TodoTrackerIntegration
        integration = TodoTrackerIntegration()
        await integration.initialize()

        await integration.sync_both_ways()
        status = await integration.get_sync_status()

        return f"✅ Sync completed\n📊 Status: {json.dumps(status, indent=2)}"


# CLI実行
async def main():
    """メイン関数"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: todo-hook <command> [args...]")
        print("Commands: add, update, complete, list, sync")
        return

    command = f"todo-{sys.argv[1]}"
    args = sys.argv[2:]

    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    wrapper = TodoCommandWrapper()
    
    try:
        result = await wrapper.execute(command, args)
        print(result)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())