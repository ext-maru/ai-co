"""
Elders Guild Unified Event Bus - 統合イベントバスシステム
Created: 2025-07-11
Author: Claude Elder
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum
from contextlib import asynccontextmanager
import weakref
import inspect
from collections import defaultdict

import asyncpg
import redis.asyncio as redis
from pydantic import BaseModel, Field
import aiohttp

logger = logging.getLogger(__name__)

# ============================================================================
# Event System Types
# ============================================================================

class EventType(Enum):
    """イベントタイプ"""
    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_HEALTH_CHECK = "system.health_check"

    # Sage Events
    SAGE_KNOWLEDGE_CREATED = "sage.knowledge.created"
    SAGE_KNOWLEDGE_UPDATED = "sage.knowledge.updated"
    SAGE_KNOWLEDGE_DELETED = "sage.knowledge.deleted"
    SAGE_KNOWLEDGE_SEARCHED = "sage.knowledge.searched"

    SAGE_TASK_CREATED = "sage.task.created"
    SAGE_TASK_STARTED = "sage.task.started"
    SAGE_TASK_COMPLETED = "sage.task.completed"
    SAGE_TASK_FAILED = "sage.task.failed"
    SAGE_TASK_CANCELLED = "sage.task.cancelled"

    SAGE_INCIDENT_CREATED = "sage.incident.created"
    SAGE_INCIDENT_RESOLVED = "sage.incident.resolved"
    SAGE_INCIDENT_ESCALATED = "sage.incident.escalated"

    SAGE_RAG_QUERY_PROCESSED = "sage.rag.query.processed"
    SAGE_RAG_DOCUMENT_INDEXED = "sage.rag.document.indexed"

    # User Events
    USER_SESSION_STARTED = "user.session.started"
    USER_SESSION_ENDED = "user.session.ended"
    USER_QUERY_SUBMITTED = "user.query.submitted"
    USER_FEEDBACK_PROVIDED = "user.feedback.provided"

    # Integration Events
    INTEGRATION_SYNC_REQUIRED = "integration.sync.required"
    INTEGRATION_CONFLICT_DETECTED = "integration.conflict.detected"
    INTEGRATION_RECOVERY_COMPLETED = "integration.recovery.completed"

    # Custom Events
    CUSTOM_EVENT = "custom.event"

class EventPriority(Enum):
    """イベント優先度"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class EventStatus(Enum):
    """イベント処理状態"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Event:
    """イベントデータクラス"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.CUSTOM_EVENT
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING

    # Tracing information
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Processing information
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'metadata': self.metadata,
            'priority': self.priority.value,
            'status': self.status.value,
            'correlation_id': self.correlation_id,
            'causation_id': self.causation_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """辞書から復元"""
        event = cls()
        event.id = data.get('id', str(uuid.uuid4()))
        event.type = EventType(data.get('type', EventType.CUSTOM_EVENT.value))
        event.source = data.get('source', 'unknown')
        event.timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        event.data = data.get('data', {})
        event.metadata = data.get('metadata', {})
        event.priority = EventPriority(data.get('priority', EventPriority.NORMAL.value))
        event.status = EventStatus(data.get('status', EventStatus.PENDING.value))
        event.correlation_id = data.get('correlation_id')
        event.causation_id = data.get('causation_id')
        event.user_id = data.get('user_id')
        event.session_id = data.get('session_id')
        event.retry_count = data.get('retry_count', 0)
        event.max_retries = data.get('max_retries', 3)
        event.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))

        if data.get('processed_at'):
            event.processed_at = datetime.fromisoformat(data['processed_at'])

        return event

# ============================================================================
# Event Handler System
# ============================================================================

EventHandler = Callable[[Event], Union[Any, asyncio.coroutine]]

class EventHandlerRegistry:
    """イベントハンドラーレジストリ"""

    def __init__(self):
        self.handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self.middleware: List[EventHandler] = []
        self.error_handlers: List[EventHandler] = []
        self.weak_refs: Set[weakref.ref] = set()

    def register_handler(self, event_type: EventType, handler: EventHandler):
        """イベントハンドラーの登録"""
        if inspect.iscoroutinefunction(handler):
            self.handlers[event_type].append(handler)
        else:
            # 同期関数を非同期でラップ
            async def async_wrapper(event: Event):
                return handler(event)
            self.handlers[event_type].append(async_wrapper)

        logger.info(f"Registered handler for {event_type.value}")

    def register_middleware(self, middleware: EventHandler):
        """ミドルウェアの登録"""
        if inspect.iscoroutinefunction(middleware):
            self.middleware.append(middleware)
        else:
            async def async_wrapper(event: Event):
                return middleware(event)
            self.middleware.append(async_wrapper)

        logger.info("Registered middleware")

    def register_error_handler(self, handler: EventHandler):
        """エラーハンドラーの登録"""
        if inspect.iscoroutinefunction(handler):
            self.error_handlers.append(handler)
        else:
            async def async_wrapper(event: Event):
                return handler(event)
            self.error_handlers.append(async_wrapper)

        logger.info("Registered error handler")

    def get_handlers(self, event_type: EventType) -> List[EventHandler]:
        """イベントハンドラーの取得"""
        return self.handlers.get(event_type, [])

    def get_middleware(self) -> List[EventHandler]:
        """ミドルウェアの取得"""
        return self.middleware

    def get_error_handlers(self) -> List[EventHandler]:
        """エラーハンドラーの取得"""
        return self.error_handlers

    def unregister_handler(self, event_type: EventType, handler: EventHandler):
        """イベントハンドラーの登録解除"""
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                logger.info(f"Unregistered handler for {event_type.value}")
            except ValueError:
                pass

# ============================================================================
# Event Store
# ============================================================================

class EventStore:
    """イベントストア"""

    def __init__(self, db_manager, redis_client: Optional[redis.Redis] = None):
        self.db_manager = db_manager
        self.redis_client = redis_client
        self.event_buffer: List[Event] = []
        self.buffer_lock = asyncio.Lock()
        self.buffer_size_limit = 1000
        self.flush_interval = 60  # 60秒
        self.flush_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """イベントストアの初期化"""
        await self._create_event_table()

        # 定期的なフラッシュタスク開始
        self.flush_task = asyncio.create_task(self._flush_loop())

        logger.info("Event store initialized")

    async def _create_event_table(self):
        """イベントテーブルの作成"""
        if not self.db_manager.db_manager.pool:
            await self.db_manager.initialize()

        async with self.db_manager.db_manager.get_connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metadata.events (
                    id UUID PRIMARY KEY,
                    type VARCHAR(100) NOT NULL,
                    source VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    data JSONB NOT NULL DEFAULT '{}',
                    metadata JSONB NOT NULL DEFAULT '{}',
                    priority INTEGER NOT NULL DEFAULT 2,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    correlation_id UUID,
                    causation_id UUID,
                    user_id VARCHAR(100),
                    session_id UUID,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    processed_at TIMESTAMP WITH TIME ZONE,

                    -- パーティション用
                    partition_date DATE GENERATED ALWAYS AS (DATE(created_at)) STORED
                ) PARTITION BY RANGE (created_at);
            """)

            # 2025年パーティション
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metadata.events_2025
                PARTITION OF system_metadata.events
                FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
            """)

            # インデックス作成
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type_status
                ON system_metadata.events (type, status);

                CREATE INDEX IF NOT EXISTS idx_events_correlation
                ON system_metadata.events (correlation_id);

                CREATE INDEX IF NOT EXISTS idx_events_created_at
                ON system_metadata.events (created_at);

                CREATE INDEX IF NOT EXISTS idx_events_priority
                ON system_metadata.events (priority DESC);
            """)

    async def store_event(self, event: Event):
        """イベントの保存"""
        async with self.buffer_lock:
            self.event_buffer.append(event)

            # バッファサイズ制限チェック
            if len(self.event_buffer) >= self.buffer_size_limit:
                await self._flush_buffer()

        # Redis にも保存（高速アクセス用）
        if self.redis_client:
            await self._store_event_in_redis(event)

    async def _store_event_in_redis(self, event: Event):
        """Redis へのイベント保存"""
        try:
            # 最新イベントリスト
            await self.redis_client.lpush(
                f"events:{event.type.value}",
                json.dumps(event.to_dict())
            )

            # リストサイズ制限
            await self.redis_client.ltrim(f"events:{event.type.value}", 0, 999)

            # TTL設定
            await self.redis_client.expire(f"events:{event.type.value}", 3600)

        except Exception as e:
            logger.error(f"Error storing event in Redis: {e}")

    async def _flush_buffer(self):
        """バッファのフラッシュ"""
        if not self.event_buffer:
            return

        events_to_flush = self.event_buffer.copy()
        self.event_buffer.clear()

        try:
            async with self.db_manager.db_manager.get_connection() as conn:
                # バッチ挿入
                await conn.executemany("""
                    INSERT INTO system_metadata.events
                    (id, type, source, timestamp, data, metadata, priority, status,
                     correlation_id, causation_id, user_id, session_id, retry_count, max_retries, created_at, processed_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                """, [
                    (
                        event.id,
                        event.type.value,
                        event.source,
                        event.timestamp,
                        json.dumps(event.data),
                        json.dumps(event.metadata),
                        event.priority.value,
                        event.status.value,
                        event.correlation_id,
                        event.causation_id,
                        event.user_id,
                        event.session_id,
                        event.retry_count,
                        event.max_retries,
                        event.created_at,
                        event.processed_at
                    )
                    for event in events_to_flush
                ])

                logger.info(f"Flushed {len(events_to_flush)} events to database")

        except Exception as e:
            logger.error(f"Error flushing events to database: {e}")
            # エラー時はバッファに戻す
            async with self.buffer_lock:
                self.event_buffer.extend(events_to_flush)

    async def _flush_loop(self):
        """定期フラッシュループ"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                async with self.buffer_lock:
                    await self._flush_buffer()
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")

    async def get_events(self, event_type: Optional[EventType] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Event]:
        """イベントの取得"""
        async with self.db_manager.db_manager.get_connection() as conn:
            if event_type:
                query = """
                    SELECT id, type, source, timestamp, data, metadata, priority, status,
                           correlation_id, causation_id, user_id, session_id, retry_count, max_retries, created_at, processed_at
                    FROM system_metadata.events
                    WHERE type = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                """
                results = await conn.fetch(query, event_type.value, limit, offset)
            else:
                query = """
                    SELECT id, type, source, timestamp, data, metadata, priority, status,
                           correlation_id, causation_id, user_id, session_id, retry_count, max_retries, created_at, processed_at
                    FROM system_metadata.events
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                """
                results = await conn.fetch(query, limit, offset)

            events = []
            for row in results:
                event_data = {
                    'id': str(row['id']),
                    'type': row['type'],
                    'source': row['source'],
                    'timestamp': row['timestamp'].isoformat(),
                    'data': json.loads(row['data']) if row['data'] else {},
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'priority': row['priority'],
                    'status': row['status'],
                    'correlation_id': str(row['correlation_id']) if row['correlation_id'] else None,
                    'causation_id': str(row['causation_id']) if row['causation_id'] else None,
                    'user_id': row['user_id'],
                    'session_id': str(row['session_id']) if row['session_id'] else None,
                    'retry_count': row['retry_count'],
                    'max_retries': row['max_retries'],
                    'created_at': row['created_at'].isoformat(),
                    'processed_at': row['processed_at'].isoformat() if row['processed_at'] else None
                }
                events.append(Event.from_dict(event_data))

            return events

    async def update_event_status(self, event_id: str, status: EventStatus):
        """イベントステータスの更新"""
        async with self.db_manager.db_manager.get_connection() as conn:
            await conn.execute("""
                UPDATE system_metadata.events
                SET status = $1, processed_at = NOW()
                WHERE id = $2
            """, status.value, event_id)

    async def close(self):
        """イベントストアのクローズ"""
        if self.flush_task:
            self.flush_task.cancel()

        # 残りのバッファをフラッシュ
        async with self.buffer_lock:
            await self._flush_buffer()

        logger.info("Event store closed")

# ============================================================================
# Event Bus
# ============================================================================

class ElderGuildEventBus:
    """エルダーズギルド統合イベントバス"""

    def __init__(self, db_manager, redis_client: Optional[redis.Redis] = None):
        self.db_manager = db_manager
        self.redis_client = redis_client
        self.handler_registry = EventHandlerRegistry()
        self.event_store = EventStore(db_manager, redis_client)

        # 処理キュー
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.dead_letter_queue = asyncio.Queue(maxsize=1000)

        # 処理タスク
        self.processing_tasks: List[asyncio.Task] = []
        self.num_workers = 4

        # 統計情報
        self.stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'events_retried': 0,
            'processing_time_total': 0.0
        }

        self.is_running = False

    async def initialize(self):
        """イベントバスの初期化"""
        await self.event_store.initialize()

        # デフォルトハンドラーの登録
        self._register_default_handlers()

        logger.info("Event bus initialized")

    def _register_default_handlers(self):
        """デフォルトハンドラーの登録"""
        # システムイベント
        self.handler_registry.register_handler(
            EventType.SYSTEM_STARTUP,
            self._handle_system_startup
        )

        self.handler_registry.register_handler(
            EventType.SYSTEM_SHUTDOWN,
            self._handle_system_shutdown
        )

        # エラーハンドラー
        self.handler_registry.register_error_handler(
            self._handle_event_error
        )

    async def _handle_system_startup(self, event: Event):
        """システム起動イベントの処理"""
        logger.info(f"System startup event received: {event.data}")

    async def _handle_system_shutdown(self, event: Event):
        """システム終了イベントの処理"""
        logger.info(f"System shutdown event received: {event.data}")

    async def _handle_event_error(self, event: Event):
        """イベントエラーの処理"""
        logger.error(f"Event processing error: {event.id} - {event.data}")

    async def start(self):
        """イベントバス開始"""
        if self.is_running:
            return

        self.is_running = True

        # ワーカータスクの開始
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.processing_tasks.append(task)

        logger.info(f"Event bus started with {self.num_workers} workers")

    async def stop(self):
        """イベントバス停止"""
        if not self.is_running:
            return

        self.is_running = False

        # ワーカータスクの停止
        for task in self.processing_tasks:
            task.cancel()

        # 残りのイベントを処理
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                await self._process_event(event)
            except asyncio.QueueEmpty:
                break

        await self.event_store.close()

        logger.info("Event bus stopped")

    async def publish(self, event: Event):
        """イベントの発行"""
        # イベントの保存
        await self.event_store.store_event(event)

        # 処理キューに追加
        try:
            await self.event_queue.put(event)
            self.stats['events_published'] += 1
        except asyncio.QueueFull:
            logger.warning("Event queue is full, dropping event")

    async def publish_event(self, event_type: EventType,
                          source: str,
                          data: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None,
                          priority: EventPriority = EventPriority.NORMAL,
                          correlation_id: Optional[str] = None,
                          causation_id: Optional[str] = None,
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None):
        """イベントの簡単発行"""
        event = Event(
            type=event_type,
            source=source,
            data=data,
            metadata=metadata or {},
            priority=priority,
            correlation_id=correlation_id,
            causation_id=causation_id,
            user_id=user_id,
            session_id=session_id
        )

        await self.publish(event)

    async def _worker_loop(self, worker_name: str):
        """ワーカーループ"""
        logger.info(f"Worker {worker_name} started")

        while self.is_running:
            try:
                # イベントの取得
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )

                # イベントの処理
                await self._process_event(event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in worker {worker_name}: {e}")

        logger.info(f"Worker {worker_name} stopped")

    async def _process_event(self, event: Event):
        """イベントの処理"""
        start_time = asyncio.get_event_loop().time()

        try:
            # ステータス更新
            event.status = EventStatus.PROCESSING
            await self.event_store.update_event_status(event.id, EventStatus.PROCESSING)

            # ミドルウェアの実行
            for middleware in self.handler_registry.get_middleware():
                try:
                    await middleware(event)
                except Exception as e:
                    logger.error(f"Middleware error: {e}")

            # ハンドラーの実行
            handlers = self.handler_registry.get_handlers(event.type)

            if handlers:
                # 並列実行
                handler_tasks = [handler(event) for handler in handlers]
                await asyncio.gather(*handler_tasks, return_exceptions=True)

            # 成功時の処理
            event.status = EventStatus.COMPLETED
            event.processed_at = datetime.now()
            await self.event_store.update_event_status(event.id, EventStatus.COMPLETED)

            self.stats['events_processed'] += 1

        except Exception as e:
            # エラー時の処理
            await self._handle_processing_error(event, e)

        finally:
            # 処理時間の記録
            processing_time = asyncio.get_event_loop().time() - start_time
            self.stats['processing_time_total'] += processing_time

    async def _handle_processing_error(self, event: Event, error: Exception):
        """処理エラーの処理"""
        logger.error(f"Event processing failed: {event.id} - {error}")

        # リトライ判定
        if event.retry_count < event.max_retries:
            event.retry_count += 1
            event.status = EventStatus.PENDING

            # 再キューイング
            await self.event_queue.put(event)
            self.stats['events_retried'] += 1

            logger.info(f"Event {event.id} retried ({event.retry_count}/{event.max_retries})")
        else:
            # 最大リトライ回数に達した場合
            event.status = EventStatus.FAILED
            await self.event_store.update_event_status(event.id, EventStatus.FAILED)

            # デッドレターキューに追加
            try:
                await self.dead_letter_queue.put(event)
            except asyncio.QueueFull:
                logger.error("Dead letter queue is full")

            self.stats['events_failed'] += 1

            # エラーハンドラーの実行
            for error_handler in self.handler_registry.get_error_handlers():
                try:
                    await error_handler(event)
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")

    def register_handler(self, event_type: EventType, handler: EventHandler):
        """イベントハンドラーの登録"""
        self.handler_registry.register_handler(event_type, handler)

    def register_middleware(self, middleware: EventHandler):
        """ミドルウェアの登録"""
        self.handler_registry.register_middleware(middleware)

    def register_error_handler(self, handler: EventHandler):
        """エラーハンドラーの登録"""
        self.handler_registry.register_error_handler(handler)

    def on(self, event_type: EventType):
        """デコレーターでハンドラー登録"""
        def decorator(handler: EventHandler):
            self.register_handler(event_type, handler)
            return handler
        return decorator

    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報の取得"""
        queue_size = self.event_queue.qsize()
        dead_letter_size = self.dead_letter_queue.qsize()

        avg_processing_time = 0.0
        if self.stats['events_processed'] > 0:
            avg_processing_time = self.stats['processing_time_total'] / self.stats['events_processed']

        return {
            'events_published': self.stats['events_published'],
            'events_processed': self.stats['events_processed'],
            'events_failed': self.stats['events_failed'],
            'events_retried': self.stats['events_retried'],
            'queue_size': queue_size,
            'dead_letter_size': dead_letter_size,
            'avg_processing_time': avg_processing_time,
            'workers': len(self.processing_tasks),
            'is_running': self.is_running
        }

# ============================================================================
# Usage Example
# ============================================================================

async def main():
    """使用例"""
    from .elders_guild_db_manager import EldersGuildDatabaseManager, DatabaseConfig

    # データベース設定
    db_config = DatabaseConfig()
    db_manager = EldersGuildDatabaseManager(db_config)

    # Redis設定
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    # イベントバス作成
    event_bus = ElderGuildEventBus(db_manager, redis_client)

    # カスタムハンドラーの登録
    @event_bus.on(EventType.SAGE_KNOWLEDGE_CREATED)
    async def handle_knowledge_created(event: Event):
        print(f"Knowledge created: {event.data}")

    @event_bus.on(EventType.SAGE_TASK_COMPLETED)
    async def handle_task_completed(event: Event):
        print(f"Task completed: {event.data}")

    try:
        await event_bus.initialize()
        await event_bus.start()

        # イベントの発行
        await event_bus.publish_event(
            EventType.SAGE_KNOWLEDGE_CREATED,
            source="knowledge_sage",
            data={"title": "Test Knowledge", "content": "Test content"},
            metadata={"category": "test"}
        )

        await event_bus.publish_event(
            EventType.SAGE_TASK_COMPLETED,
            source="task_sage",
            data={"task_id": "task-123", "result": "success"},
            priority=EventPriority.HIGH
        )

        # 統計情報の取得
        await asyncio.sleep(2)  # 処理時間を待つ
        stats = await event_bus.get_statistics()
        print(f"Event bus statistics: {stats}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await event_bus.stop()

if __name__ == "__main__":
    asyncio.run(main())
