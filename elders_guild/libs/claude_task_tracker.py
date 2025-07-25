#!/usr/bin/env python3
"""
Claude Task Tracker - PostgreSQL Migration Wrapper
既存のSQLite版インターフェースを維持しながらPostgreSQLに切り替え
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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


class ClaudeTaskTracker:
    """
    Claude Task Tracker - PostgreSQL移行版
    既存のAPIを維持しながらPostgreSQLバックエンドを使用
    """

    def __init__(self, db_path: Optional[str] = None, use_postgres: bool = True):
        """
        初期化

        Args:
            db_path: SQLiteデータベースパス（互換性のため保持、未使用）
            use_postgres: PostgreSQL使用フラグ（常にTrue）
        """
        self.use_postgres = True
        self.postgres_tracker = None
        self._initialized = False

        # 既存のSQLite属性との互換性
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = (
                Path(__file__).parent.parent / "data" / "claude_task_tracker.db"
            )

        logger.info("Claude Task Tracker (PostgreSQL) initialized")

    async def _ensure_initialized(self):
        """PostgreSQLトラッカーの初期化を確保"""
        if not self._initialized:
            self.postgres_tracker = await create_postgres_task_tracker()
            self._initialized = True

    def _run_async(self, coro):
        """非同期関数を同期的に実行"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 既にイベントループが実行中の場合は新しいタスクとして実行
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # イベントループが存在しない場合は新しく作成
            return asyncio.run(coro)

    async def _create_task_async(self, *args, **kwargs):
        """非同期タスク作成"""
        await self._ensure_initialized()
        return await self.postgres_tracker.create_task(*args, **kwargs)

    def create_task(
        self,
        title: str,
        task_type: TaskType,
        priority: TaskPriority = TaskPriority.MEDIUM,
        description: str = "",
        created_by: str = "claude_elder",
        assigned_to: Optional[str] = None,
        estimated_duration_minutes: Optional[int] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ) -> str:
        """
        新規タスク作成（同期インターフェース）

        Args:
            title: タスクタイトル
            task_type: タスクタイプ
            priority: 優先度
            description: 詳細説明
            created_by: 作成者
            assigned_to: 担当者
            estimated_duration_minutes: 推定時間（分）
            due_date: 期限
            tags: タグリスト
            metadata: メタデータ
            context: コンテキスト

        Returns:
            str: タスクID
        """
        return self._run_async(
            self._create_task_async(
                title=title,
                task_type=task_type,
                priority=priority,
                description=description,
                created_by=created_by,
                assigned_to=assigned_to,
                estimated_duration_minutes=estimated_duration_minutes,
                due_date=due_date,
                tags=tags,
                metadata=metadata,
                context=context,
            )
        )

    async def _get_task_async(self, task_id: str):
        """非同期タスク取得"""
        await self._ensure_initialized()
        return await self.postgres_tracker.get_task(task_id)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスク情報取得（同期インターフェース）

        Args:
            task_id: タスクID

        Returns:
            Optional[Dict]: タスク情報
        """
        return self._run_async(self._get_task_async(task_id))

    async def _update_task_async(self, task_id: str, **kwargs):
        """非同期タスク更新"""
        await self._ensure_initialized()
        return await self.postgres_tracker.update_task(task_id, **kwargs)

    def update_task(self, task_id: str, **kwargs) -> bool:
        """
        タスク更新（同期インターフェース）

        Args:
            task_id: タスクID
            **kwargs: 更新フィールド

        Returns:
            bool: 更新成功フラグ
        """
        return self._run_async(self._update_task_async(task_id, **kwargs))

    async def _list_tasks_async(self, **kwargs):
        """非同期タスクリスト取得"""
        await self._ensure_initialized()
        return await self.postgres_tracker.list_tasks(**kwargs)

    def list_tasks(self, **kwargs) -> List[Dict[str, Any]]:
        """
        タスクリスト取得（同期インターフェース）

        Args:
            **kwargs: フィルター条件

        Returns:
            List[Dict]: タスクリスト
        """
        return self._run_async(self._list_tasks_async(**kwargs))

    async def _get_task_statistics_async(self):
        """非同期タスク統計取得"""
        await self._ensure_initialized()
        return await self.postgres_tracker.get_task_statistics()

    def get_task_statistics(self) -> Dict[str, Any]:
        """
        タスク統計情報取得（同期インターフェース）

        Returns:
            Dict: 統計情報
        """
        return self._run_async(self._get_task_statistics_async())

    async def _delete_task_async(self, task_id: str, archive: bool = True):
        """非同期タスク削除"""
        await self._ensure_initialized()
        return await self.postgres_tracker.delete_task(task_id, archive=archive)

    def delete_task(self, task_id: str, archive: bool = True) -> bool:
        """
        タスク削除（同期インターフェース）

        Args:
            task_id: タスクID
            archive: アーカイブフラグ

        Returns:
            bool: 削除成功フラグ
        """
        return self._run_async(self._delete_task_async(task_id, archive=archive))

    async def _health_check_async(self):
        """非同期ヘルスチェック"""
        await self._ensure_initialized()
        return await self.postgres_tracker.health_check()

    def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック（同期インターフェース）

        Returns:
            Dict: ヘルス情報
        """
        return self._run_async(self._health_check_async())

    # 互換性メソッド（SQLite版で使用されていたメソッド）

    def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """保留中タスクの取得"""
        return self.list_tasks(status=TaskStatus.PENDING, limit=limit)

    def get_in_progress_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """進行中タスクの取得"""
        return self.list_tasks(status=TaskStatus.IN_PROGRESS, limit=limit)

    def get_completed_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """完了タスクの取得"""
        return self.list_tasks(status=TaskStatus.COMPLETED, limit=limit)

    def mark_task_started(self, task_id: str) -> bool:
        """タスクを開始済みにマーク"""
        return self.update_task(task_id, status=TaskStatus.IN_PROGRESS)

    def mark_task_completed(self, task_id: str, result: Optional[str] = None) -> bool:
        """タスクを完了にマーク"""
        return self.update_task(task_id, status=TaskStatus.COMPLETED, result=result)

    def mark_task_failed(
        self, task_id: str, error_message: Optional[str] = None
    ) -> bool:
        """タスクを失敗にマーク"""
        return self.update_task(
            task_id, status=TaskStatus.FAILED, error_message=error_message
        )

    async def close(self):
        """リソースの解放"""
        if self.postgres_tracker:
            await self.postgres_tracker.close()
            self._initialized = False

    def __del__(self):
        """デストラクタ"""
        if self._initialized and self.postgres_tracker:
            try:
                # 同期的にcloseを実行
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 既存ループでタスクをスケジュール
                        loop.create_task(self.close())
                    else:
                        # 新しいループでcloseを実行
                        asyncio.run(self.close())
                except RuntimeError:
                    # イベントループが利用できない場合は直接クリーンアップ
                    if hasattr(self.postgres_tracker, "_connection_manager"):
                        # Deep nesting detected (depth: 5) - consider refactoring
                        try:
                            self.postgres_tracker._connection_manager.emergency_shutdown()
                        except Exception:
                            pass
            except Exception:
                pass


# 使用例とテスト
def main():
    """使用例とテスト"""
    tracker = ClaudeTaskTracker()

    try:
        # ヘルスチェック
        health = tracker.health_check()
        print(f"ヘルス: {health}")

        # タスク作成
        task_id = tracker.create_task(
            title="PostgreSQL移行テスト（Wrapper）",
            task_type=TaskType.FEATURE,
            priority=TaskPriority.HIGH,
            description="PostgreSQL Wrapperのテスト実行",
            tags=["migration", "postgresql", "wrapper"],
            metadata={"version": "1.0", "project": "elders_guild"},
        )
        print(f"作成したタスクID: {task_id}")

        # タスク取得
        task = tracker.get_task(task_id)
        print(f"タスク詳細: {task['name']}")

        # タスク開始
        tracker.mark_task_started(task_id)

        # 進行中タスクの確認
        in_progress = tracker.get_in_progress_tasks()
        print(f"進行中タスク: {len(in_progress)}件")

        # タスク完了
        tracker.mark_task_completed(task_id, "PostgreSQL移行テスト成功")

        # 統計
        stats = tracker.get_task_statistics()
        print(f"統計: {stats}")

    except Exception as e:
        print(f"エラー: {e}")
        import traceback

        traceback.print_exc()


# グローバルインスタンス管理
_global_tracker = None


def get_task_tracker() -> ClaudeTaskTracker:
    """タスクトラッカーのグローバルインスタンスを取得"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ClaudeTaskTracker()
    return _global_tracker


if __name__ == "__main__":
    main()
