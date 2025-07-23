#!/usr/bin/env python3
"""
🚀 GitHub Integration Connection Pool Manager
Iron Will Compliant - Performance Optimization
"""

import asyncio
import logging
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """
    🚀 高性能接続プール管理システム
    
    Features:
    - Dynamic pool sizing
    - Connection health monitoring
    - Automatic reconnection
    - Performance metrics
    - Resource optimization
    """
    
    def __init__(
        self,
        min_connections: int = 5,
        max_connections: int = 50,
        connection_timeout: int = 30,
        idle_timeout: int = 300
    ):
        """
        接続プール初期化
        
        Args:
            min_connections: 最小接続数
            max_connections: 最大接続数
            connection_timeout: 接続タイムアウト（秒）
            idle_timeout: アイドルタイムアウト（秒）
        """
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        
        # 接続プール
        self.active_connections = {}
        self.idle_connections = deque()
        self.connection_semaphore = asyncio.Semaphore(max_connections)
        
        # パフォーマンスメトリクス
        self.metrics = {
            "total_connections_created": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "failed_connections": 0,
            "reused_connections": 0,
            "average_response_time": 0,
            "peak_connections": 0
        }
        
        # ヘルスチェック設定
        self.health_check_interval = 60  # 秒
        self.health_check_task = None
        
        logger.info(f"ConnectionPoolManager initialized: min={min_connections}, max={max_connections}" \
            "ConnectionPoolManager initialized: min={min_connections}, max={max_connections}")
    
    async def get_connection(self, base_url: str, headers: Dict[str, str]) -> aiohttp.ClientSession:
        """
        接続取得（プールから取得または新規作成）
        
        Args:
            base_url: ベースURL
            headers: HTTPヘッダー
            
        Returns:
            aiohttp.ClientSession
        """
        async with self.connection_semaphore:
            # アイドル接続から取得を試みる
            while self.idle_connections:
                conn_info = self.idle_connections.pop()
                session = conn_info["session"]
                
                # 接続の有効性チェック
                if await self._is_connection_healthy(session):
                    self.metrics["reused_connections"] += 1
                    self.active_connections[id(session)] = conn_info
                    self._update_metrics()
                    logger.debug("Reused connection from pool")
                    return session
                else:
                    await session.close()
                    logger.debug("Closed unhealthy connection")
            
            # 新規接続作成
            session = await self._create_new_connection(base_url, headers)
            self.active_connections[id(session)] = {
                "session": session,
                "created_at": datetime.now(),
                "last_used": datetime.now(),
                "request_count": 0
            }
            
            self.metrics["total_connections_created"] += 1
            self._update_metrics()
            
            return session
    
    async def release_connection(self, session: aiohttp.ClientSession):
        """
        接続をプールに返却
        
        Args:
            session: 返却する接続
        """
        session_id = id(session)
        
        if session_id in self.active_connections:
            conn_info = self.active_connections.pop(session_id)
            conn_info["last_used"] = datetime.now()
            
            # 接続が健全で、プールに空きがある場合は保持
            if (await self._is_connection_healthy(session) and 
                len(self.idle_connections) < self.min_connections):
                self.idle_connections.append(conn_info)
                logger.debug("Connection returned to pool")
            else:
                await session.close()
                logger.debug("Connection closed")
            
            self._update_metrics()
    
    async def _create_new_connection(
        self,
        base_url: str,
        headers: Dict[str, str]
    ) -> aiohttp.ClientSession:
        """
        新規接続作成
        
        Args:
            base_url: ベースURL
            headers: HTTPヘッダー
            
        Returns:
            新規接続
        """
        try:
            # SSL設定
            connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=30,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
                force_close=False,
                keepalive_timeout=30
            )
            
            # タイムアウト設定
            timeout = aiohttp.ClientTimeout(
                total=self.connection_timeout,
                connect=10,
                sock_connect=10,
                sock_read=30
            )
            
            # セッション作成
            session = aiohttp.ClientSession(
                connector=connector,
                headers=headers,
                timeout=timeout,
                trace_configs=[self._create_trace_config()]
            )
            
            logger.debug("Created new connection")
            return session
            
        except Exception as e:
            self.metrics["failed_connections"] += 1
            logger.error(f"Failed to create connection: {str(e)}")
            raise
    
    async def _is_connection_healthy(self, session: aiohttp.ClientSession) -> bool:
        """
        接続の健全性チェック
        
        Args:
            session: チェック対象の接続
            
        Returns:
            健全な場合True
        """
        try:
            # セッションが閉じられていないかチェック
            if session.closed:
                return False
            
            # TODO: 実際のヘルスチェックエンドポイントを使用
            # ここでは簡易的なチェックのみ
            return True
            
        except Exception:
            return False
    
    def _create_trace_config(self) -> aiohttp.TraceConfig:
        """
        リクエストトレース設定作成
        
        Returns:
            トレース設定
        """
        trace_config = aiohttp.TraceConfig()
        
        async def on_request_start(session, context, params):
            """on_request_startメソッド"""
            context.start = time.time()
        
        async def on_request_end(session, context, params):
            """on_request_endメソッド"""
            elapsed = time.time() - context.start
            self._update_response_time(elapsed)
        
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)
        
        return trace_config
    
    def _update_response_time(self, elapsed: float):
        """
        レスポンスタイム更新
        
        Args:
            elapsed: 経過時間
        """
        # 移動平均で更新
        current_avg = self.metrics["average_response_time"]
        self.metrics["average_response_time"] = (current_avg * 0.9) + (elapsed * 0.1)
    
    def _update_metrics(self):
        """メトリクス更新"""
        self.metrics["active_connections"] = len(self.active_connections)
        self.metrics["idle_connections"] = len(self.idle_connections)
        
        total_connections = self.metrics["active_connections"] + self.metrics["idle_connections"]
        if total_connections > self.metrics["peak_connections"]:
            self.metrics["peak_connections"] = total_connections
    
    async def start_health_check(self):
        """ヘルスチェック開始"""
        if self.health_check_task is None:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info("Health check started")
    
    async def stop_health_check(self):
        """ヘルスチェック停止"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None
            logger.info("Health check stopped")
    
    async def _health_check_loop(self):
        """ヘルスチェックループ"""
        # ループ処理
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # アイドル接続のチェック
                healthy_connections = deque()
                
                while self.idle_connections:
                    conn_info = self.idle_connections.popleft()
                    session = conn_info["session"]
                    
                    # アイドルタイムアウトチェック
                    idle_time = (datetime.now() - conn_info["last_used"]).total_seconds()
                    
                    if idle_time < self.idle_timeout and await self._is_connection_healthy(session):
                        healthy_connections.append(conn_info)
                    else:
                        await session.close()
                        logger.debug(f"Closed idle connection (idle time: {idle_time}s)")
                
                self.idle_connections = healthy_connections
                self._update_metrics()
                
                logger.debug(f"Health check completed: {len(healthy_connections)} healthy connections" \
                    "Health check completed: {len(healthy_connections)} healthy connections")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
    
    async def close_all(self):
        """すべての接続を閉じる"""
        # ヘルスチェック停止
        await self.stop_health_check()
        
        # アクティブ接続を閉じる
        for conn_info in self.active_connections.values():
            try:
                await conn_info["session"].close()
            except Exception as e:
                logger.error(f"Error closing active connection: {str(e)}")
        
        # アイドル接続を閉じる
        while self.idle_connections:
            conn_info = self.idle_connections.pop()
            try:
                await conn_info["session"].close()
            except Exception as e:
                logger.error(f"Error closing idle connection: {str(e)}")
        
        self.active_connections.clear()
        logger.info("All connections closed")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        パフォーマンスメトリクス取得
        
        Returns:
            メトリクス辞書
        """
        return {
            **self.metrics,
            "connection_reuse_rate": self._calculate_reuse_rate(),
            "connection_efficiency": self._calculate_efficiency()
        }
    
    def _calculate_reuse_rate(self) -> float:
        """接続再利用率計算"""
        total = self.metrics["total_connections_created"] + self.metrics["reused_connections"]
        if total == 0:
            return 0.0
        return (self.metrics["reused_connections"] / total) * 100
    
    def _calculate_efficiency(self) -> float:
        """接続効率計算"""
        if self.metrics["total_connections_created"] == 0:
            return 100.0
        
        failed_rate = (self.metrics["failed_connections"] / 
                      (self.metrics["total_connections_created"] + self.metrics["failed_connections"])) * 100
        
        return 100.0 - failed_rate


# 使用例
async def example_usage():
    """使用例"""
    pool_manager = ConnectionPoolManager(
        min_connections=5,
        max_connections=20
    )
    
    try:
        # ヘルスチェック開始
        await pool_manager.start_health_check()
        
        # 接続取得
        headers = {"Authorization": "token xxx"}
        session = await pool_manager.get_connection("https://api.github.com", headers)
        
        # APIリクエスト実行
        async with session.get("/user") as response:
            data = await response.json()
            print(f"User data: {data}")
        
        # 接続返却
        await pool_manager.release_connection(session)
        
        # メトリクス表示
        metrics = pool_manager.get_metrics()
        print(f"Metrics: {metrics}")
        
    finally:
        await pool_manager.close_all()


if __name__ == "__main__":
    asyncio.run(example_usage())