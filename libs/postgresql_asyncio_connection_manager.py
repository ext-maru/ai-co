#!/usr/bin/env python3
"""
PostgreSQL AsyncIO Connection Manager - シングルトンパターン実装
非同期接続プールのライフサイクル管理とイベントループ競合回避

エルダーズギルド PostgreSQL統合 - 安定性重視設計
"""

import asyncio
import atexit
import logging
import os
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import asyncpg

logger = logging.getLogger(__name__)


class PostgreSQLConnectionManager:
    """
    PostgreSQL接続マネージャー - シングルトンパターン

    特徴:
    - シングルトンパターンによる接続プール一元管理
    - イベントループ競合回避
    - グレースフルシャットダウン
    - スレッドセーフ設計
    - 自動回復機能
    """

    _instance = None
    _lock = threading.Lock()
    _pools = {}  # ループごとの接続プール管理
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """シングルトンパターン実装"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, **config):
        """
        初期化（シングルトンなので1回のみ実行）

        Args:
            **config: PostgreSQL接続設定
        """
        if self._initialized:
            return

        # 接続設定
        self.config = {
            "host": config.get("host", os.getenv("POSTGRES_HOST", "localhost")),
            "port": config.get("port", int(os.getenv("POSTGRES_PORT", 5432))),
            "database": config.get(
                "database", os.getenv("POSTGRES_DATABASE", "elders_knowledge")
            ),
            "user": config.get("user", os.getenv("POSTGRES_USER", "elders_guild")),
            "password": config.get(
                "password", os.getenv("POSTGRES_PASSWORD", "")
            ),
        }

        # プール設定
        self.pool_config = {
            "min_size": config.get("min_size", 2),
            "max_size": config.get("max_size", 10),
            "command_timeout": config.get("command_timeout", 60),
            "server_settings": {"application_name": "elders_guild_claude_elder"},
        }

        # 状態管理
        self._shutdown_event = asyncio.Event()
        # WeakSetの代わりに通常のsetを使用（PoolConnectionProxyはweak referenceできない）
        self._active_connections = set()
        self._connection_lock = threading.Lock()

        # シャットダウンハンドラ登録
        atexit.register(self._emergency_shutdown)

        self._initialized = True
        logger.info("PostgreSQL Connection Manager initialized (Singleton)")

    @classmethod
    async def get_instance(cls, **config) -> "PostgreSQLConnectionManager":
        """
        インスタンス取得（非同期初期化付き）

        Args:
            **config: PostgreSQL接続設定

        Returns:
            PostgreSQLConnectionManager: シングルトンインスタンス
        """
        instance = cls(**config)
        await instance._ensure_pool()
        return instance

    async def _ensure_pool(self):
        """現在のイベントループに対する接続プールを確保"""
        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)

            if loop_id not in self._pools or self._pools[loop_id] is None:
                logger.info(f"Creating new connection pool for loop {loop_id}")

                # 接続プール作成
                pool = await asyncpg.create_pool(**self.config, **self.pool_config)

                self._pools[loop_id] = pool

                # ループ終了時のクリーンアップ設定
                loop.add_signal_handler = getattr(loop, "add_signal_handler", None)
                if hasattr(loop, "add_signal_handler"):
                    try:
                        import signal

                        loop.add_signal_handler(
                            signal.SIGTERM, self._create_shutdown_task, loop_id
                        )
                        loop.add_signal_handler(
                            signal.SIGINT, self._create_shutdown_task, loop_id
                        )
                    except (NotImplementedError, RuntimeError):
                        # Windowsやサブスレッドでは signal handler を設定できない
                        pass

                logger.info(f"Connection pool created successfully for loop {loop_id}")

        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def _create_shutdown_task(self, loop_id):
        """シャットダウンタスク作成"""
        try:
            loop = asyncio.get_running_loop()
            if id(loop) == loop_id:
                loop.create_task(self._close_pool(loop_id))
        except RuntimeError:
            pass

    async def _close_pool(self, loop_id):
        """指定されたループの接続プールを閉じる"""
        if loop_id in self._pools and self._pools[loop_id]:
            try:
                await self._pools[loop_id].close()
                logger.info(f"Connection pool closed for loop {loop_id}")
            except Exception as e:
                logger.error(f"Error closing pool for loop {loop_id}: {e}")
            finally:
                self._pools[loop_id] = None

    @asynccontextmanager
    async def get_connection(self):
        """
        データベース接続取得（コンテキストマネージャー）

        Yields:
            asyncpg.Connection: データベース接続
        """
        await self._ensure_pool()

        loop_id = id(asyncio.get_running_loop())
        pool = self._pools.get(loop_id)

        if not pool:
            raise RuntimeError("Connection pool not available")

        connection_id = str(uuid4())
        connection = None

        try:
            connection = await pool.acquire()

            # スレッドセーフに接続を追跡
            with self._connection_lock:
                self._active_connections.add(connection_id)

            logger.debug(f"Connection acquired: {connection_id}")
            yield connection

        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise

        finally:
            if connection:
                try:
                    await pool.release(connection)
                    # 接続追跡から削除
                    with self._connection_lock:
                        self._active_connections.discard(connection_id)
                    logger.debug(f"Connection released: {connection_id}")
                except Exception as e:
                    logger.error(f"Error releasing connection {connection_id}: {e}")

    async def execute_query(self, query: str, *args) -> Any:
        """
        クエリ実行（単発実行用）

        Args:
            query: SQLクエリ
            *args: クエリパラメータ

        Returns:
            Any: クエリ実行結果
        """
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)

    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        """
        単一レコード取得

        Args:
            query: SQLクエリ
            *args: クエリパラメータ

        Returns:
            Optional[Dict]: 取得レコード
        """
        async with self.get_connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_all(self, query: str, *args) -> list:
        """
        複数レコード取得

        Args:
            query: SQLクエリ
            *args: クエリパラメータ

        Returns:
            list: 取得レコードリスト
        """
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def execute_transaction(self, operations: list) -> bool:
        """
        トランザクション実行

        Args:
            operations: 実行操作のリスト [(query, args), ...]

        Returns:
            bool: 実行成功フラグ
        """
        async with self.get_connection() as conn:
            async with conn.transaction():
                try:
                    for query, args in operations:
                        await conn.execute(query, *args)
                    return True
                except Exception as e:
                    logger.error(f"Transaction failed: {e}")
                    raise

    async def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック実行

        Returns:
            Dict: ヘルス情報
        """
        try:
            start_time = datetime.now()
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            loop_id = id(asyncio.get_running_loop())
            pool = self._pools.get(loop_id)

            with self._connection_lock:
                active_count = len(self._active_connections)

            return {
                "status": "healthy",
                "database": "connected",
                "response_time_ms": round(response_time, 2),
                "pool_size": len(pool._holders) if pool else 0,
                "active_connections": active_count,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def close_all_pools(self):
        """全ての接続プールを閉じる"""
        logger.info("Closing all connection pools...")

        for loop_id, pool in list(self._pools.items()):
            if pool:
                try:
                    await pool.close()
                    logger.info(f"Pool closed for loop {loop_id}")
                except Exception as e:
                    logger.error(f"Error closing pool {loop_id}: {e}")

        self._pools.clear()
        logger.info("All connection pools closed")

    def _emergency_shutdown(self):
        """緊急シャットダウン（同期実行）"""
        logger.warning("Emergency shutdown initiated")

        # 残存する接続プールの緊急クローズ
        for loop_id, pool in list(self._pools.items()):
            if pool:
                try:
                    # 同期的にクローズを試行（asyncio.run は避ける）
                    if hasattr(pool, "_con_count"):
                        logger.warning(
                            f"Emergency: Abandoning pool {loop_id} with {pool._con_count} connections"
                        )
                except Exception as e:
                    logger.error(f"Emergency shutdown error: {e}")

        self._pools.clear()

        # 接続追跡もクリア
        with self._connection_lock:
            self._active_connections.clear()


class EventLoopSafeWrapper:
    """
    イベントループセーフラッパー
    既存のイベントループとの競合を回避して非同期操作を実行
    """

    @staticmethod
    def run_async(coro, timeout: Optional[float] = None):
        """
        非同期コルーチンを安全に実行

        Args:
            coro: 実行するコルーチン
            timeout: タイムアウト（秒）

        Returns:
            Any: 実行結果
        """
        try:
            # 既存のイベントループを確認
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # 既存ループが動作中の場合は ThreadPoolExecutor を使用
                import concurrent.futures

                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        if timeout:
                            return new_loop.run_until_complete(
                                asyncio.wait_for(coro, timeout=timeout)
                            )
                        else:
                            return new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=timeout)

            else:
                # 既存ループが停止中の場合は直接実行
                if timeout:
                    return loop.run_until_complete(
                        asyncio.wait_for(coro, timeout=timeout)
                    )
                else:
                    return loop.run_until_complete(coro)

        except RuntimeError:
            # イベントループが存在しない場合は新規作成
            if timeout:
                return asyncio.run(asyncio.wait_for(coro, timeout=timeout))
            else:
                return asyncio.run(coro)


# モジュールレベルのユーティリティ関数
async def get_postgres_manager(**config) -> PostgreSQLConnectionManager:
    """
    PostgreSQL接続マネージャー取得

    Args:
        **config: 接続設定

    Returns:
        PostgreSQLConnectionManager: 接続マネージャー
    """
    return await PostgreSQLConnectionManager.get_instance(**config)


def run_postgres_operation(coro, timeout: Optional[float] = None):
    """
    PostgreSQL操作を安全に実行

    Args:
        coro: 実行するコルーチン
        timeout: タイムアウト（秒）

    Returns:
        Any: 実行結果
    """
    return EventLoopSafeWrapper.run_async(coro, timeout=timeout)


# 使用例とテスト
async def main():
    """使用例とテスト"""
    try:
        # 接続マネージャー取得
        manager = await get_postgres_manager()

        # ヘルスチェック
        health = await manager.health_check()
        print(f"Health check: {health}")

        # テストクエリ実行
        result = await manager.fetch_one("SELECT 1 as test_value")
        print(f"Test query result: {result}")

        # トランザクションテスト
        operations = [
            ("SELECT 'transaction_test' as operation", []),
        ]
        tx_result = await manager.execute_transaction(operations)
        print(f"Transaction result: {tx_result}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 安全な実行
    run_postgres_operation(main())
