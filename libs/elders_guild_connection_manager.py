"""
Elders Guild Connection Manager - 高度な接続管理・負荷分散システム
Created: 2025-07-11
Author: Claude Elder
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from enum import Enum
import random
import time
from contextlib import asynccontextmanager
import statistics

import asyncpg
import redis.asyncio as redis
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

class ConnectionType(Enum):
    """接続タイプ"""
    MASTER = "master"
    SLAVE = "slave"
    POOLED = "pooled"
    DIRECT = "direct"

class LoadBalanceStrategy(Enum):
    """負荷分散戦略"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    RESPONSE_TIME = "response_time"

@dataclass
class DatabaseNode:
    """データベースノード設定"""
    host: str
    port: int
    database: str
    username: str
    password: str
    connection_type: ConnectionType = ConnectionType.MASTER
    weight: int = 1
    max_connections: int = 100
    min_connections: int = 5
    is_active: bool = True

    # 統計情報
    current_connections: int = 0
    total_connections: int = 0
    response_times: List[float] = field(default_factory=list)
    error_count: int = 0
    last_error: Optional[str] = None
    last_health_check: Optional[datetime] = None

    def get_connection_string(self) -> str:
        """接続文字列の生成"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_async_connection_string(self) -> str:
        """非同期接続文字列の生成"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def add_response_time(self, response_time: float):
        """レスポンス時間の記録"""
        self.response_times.append(response_time)
        # 最新100件のみ保持
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]

    def get_average_response_time(self) -> float:
        """平均レスポンス時間の取得"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    def get_connection_usage(self) -> float:
        """接続使用率の取得"""
        if self.max_connections == 0:
            return 0.0
        return self.current_connections / self.max_connections

@dataclass
class ConnectionPoolConfig:
    """接続プール設定"""
    # 基本設定
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True

    # 負荷分散設定
    load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.LEAST_CONNECTIONS
    health_check_interval: int = 30
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60

    # 接続設定
    connection_timeout: int = 10
    command_timeout: int = 30

    # Redis設定
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # 監視設定
    enable_monitoring: bool = True
    metrics_retention_hours: int = 24

# ============================================================================
# Load Balancer
# ============================================================================

class LoadBalancer:
    """負荷分散器"""

    def __init__(self, config: ConnectionPoolConfig):
        self.config = config
        self.last_used_index = 0

    def select_node(self, nodes: List[DatabaseNode], connection_type: ConnectionType) -> Optional[DatabaseNode]:
        """ノードの選択"""
        # アクティブなノードをフィルタ
        active_nodes = [node for node in nodes if node.is_active and node.connection_type == connection_type]

        if not active_nodes:
            return None

        if self.config.load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_select(active_nodes)
        elif self.config.load_balance_strategy == LoadBalanceStrategy.RANDOM:
            return self._random_select(active_nodes)
        elif self.config.load_balance_strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(active_nodes)
        elif self.config.load_balance_strategy == LoadBalanceStrategy.WEIGHTED:
            return self._weighted_select(active_nodes)
        elif self.config.load_balance_strategy == LoadBalanceStrategy.RESPONSE_TIME:
            return self._response_time_select(active_nodes)
        else:
            return self._round_robin_select(active_nodes)

    def _round_robin_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """ラウンドロビン選択"""
        self.last_used_index = (self.last_used_index + 1) % len(nodes)
        return nodes[self.last_used_index]

    def _random_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """ランダム選択"""
        return random.choice(nodes)

    def _least_connections_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """最小接続数選択"""
        return min(nodes, key=lambda node: node.current_connections)

    def _weighted_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """重み付き選択"""
        weights = [node.weight for node in nodes]
        return random.choices(nodes, weights=weights, k=1)[0]

    def _response_time_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """レスポンス時間ベース選択"""
        # レスポンス時間の逆数で重み付け
        weights = []
        for node in nodes:
            avg_response = node.get_average_response_time()
            if avg_response > 0:
                weights.append(1.0 / avg_response)
            else:
                weights.append(1.0)

        return random.choices(nodes, weights=weights, k=1)[0]

# ============================================================================
# Circuit Breaker
# ============================================================================

class CircuitBreaker:
    """サーキットブレーカー"""

    def __init__(self, threshold: int = 5, timeout: int = 60):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs):
        """関数呼び出しの管理"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """リセット試行の判定"""
        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) > self.timeout

    def _on_success(self):
        """成功時の処理"""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """失敗時の処理"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.threshold:
            self.state = "OPEN"

# ============================================================================
# Connection Manager
# ============================================================================

class ConnectionManager:
    """接続マネージャー"""

    def __init__(self, config: ConnectionPoolConfig):
        self.config = config
        self.nodes: List[DatabaseNode] = []
        self.pools: Dict[str, asyncpg.Pool] = {}
        self.engines: Dict[str, Any] = {}
        self.load_balancer = LoadBalancer(config)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.health_check_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'avg_response_time': 0.0
        }

    async def initialize(self):
        """接続マネージャーの初期化"""
        # Redis接続
        self.redis_client = redis.Redis(
            host=self.config.redis_host,
            port=self.config.redis_port,
            db=self.config.redis_db,
            decode_responses=True
        )

        # 各ノードの接続プールを作成
        for node in self.nodes:
            await self._create_connection_pool(node)

            # サーキットブレーカーの初期化
            self.circuit_breakers[node.host] = CircuitBreaker(
                threshold=self.config.circuit_breaker_threshold,
                timeout=self.config.circuit_breaker_timeout
            )

        # ヘルスチェック開始
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        # 監視タスク開始
        if self.config.enable_monitoring:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info(f"Connection manager initialized with {len(self.nodes)} nodes")

    def add_node(self, node: DatabaseNode):
        """ノードの追加"""
        self.nodes.append(node)

    async def _create_connection_pool(self, node: DatabaseNode):
        """接続プールの作成"""
        try:
            # asyncpg プール
            pool = await asyncpg.create_pool(
                host=node.host,
                port=node.port,
                database=node.database,
                user=node.username,
                password=node.password,
                min_size=node.min_connections,
                max_size=node.max_connections,
                command_timeout=self.config.command_timeout,
                init=self._init_connection
            )
            self.pools[node.host] = pool

            # SQLAlchemy エンジン
            engine = create_async_engine(
                node.get_async_connection_string(),
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping
            )
            self.engines[node.host] = engine

            logger.info(f"Connection pool created for {node.host}:{node.port}")

        except Exception as e:
            logger.error(f"Failed to create connection pool for {node.host}:{node.port}: {e}")
            node.is_active = False
            node.error_count += 1
            node.last_error = str(e)

    async def _init_connection(self, connection):
        """接続の初期化"""
        # pgvector 拡張の登録
        try:
            from pgvector.asyncpg import register_vector
            await register_vector(connection)
        except ImportError:
            pass

        # 検索パスの設定
        await connection.execute(
            "SET search_path TO knowledge_sage, task_sage, incident_sage, rag_sage, system_metadata, public"
        )

    @asynccontextmanager
    async def get_connection(self, connection_type: ConnectionType = ConnectionType.MASTER):
        """接続の取得"""
        node = self.load_balancer.select_node(self.nodes, connection_type)
        if not node:
            raise Exception(f"No available {connection_type.value} nodes")

        start_time = time.time()

        try:
            # サーキットブレーカーチェック
            circuit_breaker = self.circuit_breakers.get(node.host)
            if circuit_breaker and circuit_breaker.state == "OPEN":
                raise Exception(f"Circuit breaker is OPEN for {node.host}")

            # 接続プールから接続を取得
            pool = self.pools.get(node.host)
            if not pool:
                raise Exception(f"No connection pool for {node.host}")

            async with pool.acquire() as connection:
                node.current_connections += 1
                node.total_connections += 1
                self.connection_stats['total_connections'] += 1
                self.connection_stats['active_connections'] += 1

                try:
                    yield connection

                    # 成功時の処理
                    response_time = time.time() - start_time
                    node.add_response_time(response_time)

                    if circuit_breaker:
                        circuit_breaker._on_success()

                finally:
                    node.current_connections -= 1
                    self.connection_stats['active_connections'] -= 1

        except Exception as e:
            # 失敗時の処理
            node.error_count += 1
            node.last_error = str(e)
            self.connection_stats['failed_connections'] += 1

            if circuit_breaker:
                circuit_breaker._on_failure()

            logger.error(f"Connection error for {node.host}: {e}")
            raise

    @asynccontextmanager
    async def get_read_connection(self):
        """読み取り専用接続の取得"""
        # スレーブがあればスレーブを使用、なければマスターを使用
        slave_nodes = [node for node in self.nodes if node.connection_type == ConnectionType.SLAVE and node.is_active]

        if slave_nodes:
            async with self.get_connection(ConnectionType.SLAVE) as conn:
                yield conn
        else:
            async with self.get_connection(ConnectionType.MASTER) as conn:
                yield conn

    @asynccontextmanager
    async def get_write_connection(self):
        """書き込み専用接続の取得"""
        async with self.get_connection(ConnectionType.MASTER) as conn:
            yield conn

    async def execute_query(self, query: str, *args, connection_type: ConnectionType = ConnectionType.MASTER):
        """クエリの実行"""
        async with self.get_connection(connection_type) as conn:
            return await conn.fetch(query, *args)

    async def execute_write_query(self, query: str, *args):
        """書き込みクエリの実行"""
        async with self.get_write_connection() as conn:
            return await conn.execute(query, *args)

    async def _health_check_loop(self):
        """ヘルスチェックループ"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _perform_health_checks(self):
        """ヘルスチェック実行"""
        for node in self.nodes:
            try:
                start_time = time.time()

                # 接続テスト
                pool = self.pools.get(node.host)
                if pool:
                    async with pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")

                    # レスポンス時間の記録
                    response_time = time.time() - start_time
                    node.add_response_time(response_time)

                    # ノードを有効化
                    if not node.is_active:
                        node.is_active = True
                        logger.info(f"Node {node.host} is back online")

                node.last_health_check = datetime.now()

            except Exception as e:
                logger.warning(f"Health check failed for {node.host}: {e}")
                node.error_count += 1
                node.last_error = str(e)

                # 連続エラーでノードを無効化
                if node.error_count >= 3:
                    node.is_active = False
                    logger.warning(f"Node {node.host} marked as inactive")

    async def _monitoring_loop(self):
        """監視ループ"""
        while True:
            try:
                await asyncio.sleep(60)  # 1分間隔
                await self._collect_metrics()
            except Exception as e:
                logger.error(f"Monitoring error: {e}")

    async def _collect_metrics(self):
        """メトリクスの収集"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'nodes': [],
            'connection_stats': self.connection_stats.copy()
        }

        # ノード別メトリクス
        for node in self.nodes:
            node_metrics = {
                'host': node.host,
                'port': node.port,
                'connection_type': node.connection_type.value,
                'is_active': node.is_active,
                'current_connections': node.current_connections,
                'total_connections': node.total_connections,
                'error_count': node.error_count,
                'avg_response_time': node.get_average_response_time(),
                'connection_usage': node.get_connection_usage()
            }
            metrics['nodes'].append(node_metrics)

        # 全体統計の更新
        if self.nodes:
            total_response_times = []
            for node in self.nodes:
                total_response_times.extend(node.response_times)

            if total_response_times:
                self.connection_stats['avg_response_time'] = statistics.mean(total_response_times)

        # Redis に保存
        if self.redis_client:
            await self.redis_client.setex(
                f"elders_guild:connection_metrics:{int(time.time())}",
                3600,  # 1時間保持
                json.dumps(metrics)
            )

    async def get_connection_statistics(self) -> Dict[str, Any]:
        """接続統計の取得"""
        stats = {
            'total_nodes': len(self.nodes),
            'active_nodes': len([node for node in self.nodes if node.is_active]),
            'inactive_nodes': len([node for node in self.nodes if not node.is_active]),
            'master_nodes': len([node for node in self.nodes if node.connection_type == ConnectionType.MASTER]),
            'slave_nodes': len([node for node in self.nodes if node.connection_type == ConnectionType.SLAVE]),
            'connection_stats': self.connection_stats.copy(),
            'nodes': []
        }

        # ノード別統計
        for node in self.nodes:
            node_stats = {
                'host': node.host,
                'port': node.port,
                'connection_type': node.connection_type.value,
                'is_active': node.is_active,
                'current_connections': node.current_connections,
                'total_connections': node.total_connections,
                'error_count': node.error_count,
                'avg_response_time': node.get_average_response_time(),
                'connection_usage': node.get_connection_usage(),
                'last_health_check': node.last_health_check.isoformat() if node.last_health_check else None
            }
            stats['nodes'].append(node_stats)

        return stats

    async def failover_to_backup(self, failed_node: DatabaseNode):
        """バックアップへのフェイルオーバー"""
        logger.warning(f"Failing over from {failed_node.host}")

        # 失敗したノードを無効化
        failed_node.is_active = False

        # 利用可能なノードを確認
        active_nodes = [node for node in self.nodes if node.is_active]

        if not active_nodes:
            logger.critical("No active nodes available!")
            raise Exception("All database nodes are down")

        logger.info(f"Failover completed. {len(active_nodes)} nodes available")

    async def close(self):
        """接続マネージャーのクローズ"""
        # タスクの停止
        if self.health_check_task:
            self.health_check_task.cancel()

        if self.monitoring_task:
            self.monitoring_task.cancel()

        # 接続プールのクローズ
        for pool in self.pools.values():
            await pool.close()

        # エンジンのクローズ
        for engine in self.engines.values():
            await engine.dispose()

        # Redis接続のクローズ
        if self.redis_client:
            await self.redis_client.close()

        logger.info("Connection manager closed")

# ============================================================================
# Usage Example
# ============================================================================

async def main():
    """使用例"""
    # 設定
    config = ConnectionPoolConfig(
        pool_size=20,
        max_overflow=30,
        load_balance_strategy=LoadBalanceStrategy.LEAST_CONNECTIONS,
        health_check_interval=30,
        enable_monitoring=True
    )

    # 接続マネージャーの作成
    manager = ConnectionManager(config)

    # マスターノードの追加
    master_node = DatabaseNode(
        host="localhost",
        port=5432,
        database="elders_guild",
        username="elder_admin",
        password="elders_guild_2025",
        connection_type=ConnectionType.MASTER,
        max_connections=100
    )
    manager.add_node(master_node)

    # スレーブノードの追加
    slave_node = DatabaseNode(
        host="localhost",
        port=5433,
        database="elders_guild",
        username="elder_admin",
        password="elders_guild_2025",
        connection_type=ConnectionType.SLAVE,
        max_connections=50
    )
    manager.add_node(slave_node)

    try:
        await manager.initialize()

        # 読み取りクエリ（スレーブで実行）
        async with manager.get_read_connection() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM knowledge_sage.knowledge_entities")
            print(f"Total knowledge entities: {result}")

        # 書き込みクエリ（マスターで実行）
        async with manager.get_write_connection() as conn:
            await conn.execute("""
                INSERT INTO system_metadata.configurations (key, value, description)
                VALUES ('test_key', '{"test": "value"}', 'Test configuration')
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """)

        # 統計情報の取得
        stats = await manager.get_connection_statistics()
        print(f"Connection statistics: {json.dumps(stats, indent=2)}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
