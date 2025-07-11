"""
Elders Guild Database Manager - 4賢者統合データベース管理
Created: 2025-07-11
Author: Claude Elder
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib
import uuid
from contextlib import asynccontextmanager

import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector
import redis.asyncio as redis
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class DatabaseConfig:
    """データベース設定クラス"""
    host: str = "localhost"
    port: int = 5432
    database: str = "elders_guild"
    username: str = "elder_admin"
    password: str = "elders_guild_2025"

    # Connection pooling
    min_connections: int = 5
    max_connections: int = 100

    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # PgBouncer configuration
    pgbouncer_host: str = "localhost"
    pgbouncer_port: int = 6432

    # Performance settings
    embedding_dimension: int = 1536
    similarity_threshold: float = 0.8
    max_search_results: int = 10

# ============================================================================
# Database Connection Manager
# ============================================================================

class DatabaseManager:
    """4賢者統合データベース管理クラス"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.engine = None
        self.session_maker = None

    async def initialize(self):
        """データベース接続の初期化"""
        try:
            # PostgreSQL接続プール作成
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                init=self._init_connection
            )

            # Redis接続
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                decode_responses=True
            )

            # SQLAlchemy async engine
            database_url = f"postgresql+asyncpg://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
            self.engine = create_async_engine(database_url, pool_pre_ping=True)
            self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

            logger.info("Database connections initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise

    async def _init_connection(self, connection):
        """接続初期化処理"""
        await register_vector(connection)
        await connection.execute("SET search_path TO knowledge_sage, task_sage, incident_sage, rag_sage, system_metadata, public")

    async def close(self):
        """接続クローズ"""
        if self.pool:
            await self.pool.close()
        if self.redis_client:
            await self.redis_client.close()
        if self.engine:
            await self.engine.dispose()

    @asynccontextmanager
    async def get_connection(self):
        """データベース接続取得"""
        async with self.pool.acquire() as connection:
            yield connection

    @asynccontextmanager
    async def get_session(self):
        """SQLAlchemy セッション取得"""
        async with self.session_maker() as session:
            yield session

# ============================================================================
# Knowledge Sage Database Manager
# ============================================================================

@dataclass
class KnowledgeEntity:
    """知識エンティティデータクラス"""
    id: Optional[str] = None
    title: str = ""
    content: str = ""
    content_type: str = "text"
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    parent_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = 1
    access_count: int = 0
    last_accessed: Optional[datetime] = None

class KnowledgeSageManager:
    """Knowledge Sage データベース管理"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def create_knowledge(self, knowledge: KnowledgeEntity) -> str:
        """知識の作成"""
        async with self.db_manager.get_connection() as conn:
            query = """
            INSERT INTO knowledge_sage.knowledge_entities
            (title, content, content_type, embedding, metadata, category, tags, quality_score, parent_id, created_by, updated_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            """

            embedding_list = knowledge.embedding.tolist() if knowledge.embedding is not None else None

            result = await conn.fetchrow(
                query,
                knowledge.title,
                knowledge.content,
                knowledge.content_type,
                embedding_list,
                json.dumps(knowledge.metadata),
                knowledge.category,
                knowledge.tags,
                knowledge.quality_score,
                knowledge.parent_id,
                knowledge.created_by,
                knowledge.updated_by
            )

            knowledge_id = str(result['id'])

            # Cache the knowledge
            await self._cache_knowledge(knowledge_id, knowledge)

            logger.info(f"Created knowledge entity: {knowledge_id}")
            return knowledge_id

    async def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeEntity]:
        """知識の取得"""
        # First check cache
        cached = await self._get_cached_knowledge(knowledge_id)
        if cached:
            return cached

        async with self.db_manager.get_connection() as conn:
            query = """
            SELECT id, title, content, content_type, embedding, metadata, category, tags,
                   quality_score, parent_id, created_at, updated_at, created_by, updated_by,
                   version, access_count, last_accessed
            FROM knowledge_sage.knowledge_entities
            WHERE id = $1
            """

            result = await conn.fetchrow(query, knowledge_id)
            if not result:
                return None

            knowledge = KnowledgeEntity(
                id=str(result['id']),
                title=result['title'],
                content=result['content'],
                content_type=result['content_type'],
                embedding=np.array(result['embedding']) if result['embedding'] else None,
                metadata=json.loads(result['metadata']) if result['metadata'] else {},
                category=result['category'],
                tags=result['tags'] or [],
                quality_score=result['quality_score'],
                parent_id=str(result['parent_id']) if result['parent_id'] else None,
                created_at=result['created_at'],
                updated_at=result['updated_at'],
                created_by=result['created_by'],
                updated_by=result['updated_by'],
                version=result['version'],
                access_count=result['access_count'],
                last_accessed=result['last_accessed']
            )

            # Update access count
            await self._update_access_count(knowledge_id)

            # Cache the knowledge
            await self._cache_knowledge(knowledge_id, knowledge)

            return knowledge

    async def semantic_search(self, query_embedding: np.ndarray,
                            similarity_threshold: float = 0.8,
                            max_results: int = 10,
                            category: Optional[str] = None) -> List[Tuple[KnowledgeEntity, float]]:
        """セマンティック検索"""
        async with self.db_manager.get_connection() as conn:
            query = """
            SELECT id, title, content, content_type, embedding, metadata, category, tags,
                   quality_score, parent_id, created_at, updated_at, created_by, updated_by,
                   version, access_count, last_accessed,
                   1 - (embedding <=> $1) as similarity
            FROM knowledge_sage.knowledge_entities
            WHERE embedding IS NOT NULL
            AND 1 - (embedding <=> $1) > $2
            """

            params = [query_embedding.tolist(), similarity_threshold]

            if category:
                query += " AND category = $3"
                params.append(category)
                query += " ORDER BY embedding <=> $1 LIMIT $4"
                params.append(max_results)
            else:
                query += " ORDER BY embedding <=> $1 LIMIT $3"
                params.append(max_results)

            results = await conn.fetch(query, *params)

            knowledge_list = []
            for result in results:
                knowledge = KnowledgeEntity(
                    id=str(result['id']),
                    title=result['title'],
                    content=result['content'],
                    content_type=result['content_type'],
                    embedding=np.array(result['embedding']) if result['embedding'] else None,
                    metadata=json.loads(result['metadata']) if result['metadata'] else {},
                    category=result['category'],
                    tags=result['tags'] or [],
                    quality_score=result['quality_score'],
                    parent_id=str(result['parent_id']) if result['parent_id'] else None,
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    created_by=result['created_by'],
                    updated_by=result['updated_by'],
                    version=result['version'],
                    access_count=result['access_count'],
                    last_accessed=result['last_accessed']
                )

                similarity = float(result['similarity'])
                knowledge_list.append((knowledge, similarity))

            return knowledge_list

    async def fulltext_search(self, query: str, max_results: int = 10) -> List[KnowledgeEntity]:
        """全文検索"""
        async with self.db_manager.get_connection() as conn:
            search_query = """
            SELECT id, title, content, content_type, embedding, metadata, category, tags,
                   quality_score, parent_id, created_at, updated_at, created_by, updated_by,
                   version, access_count, last_accessed,
                   ts_rank(search_vector, plainto_tsquery('japanese', $1)) as rank_ja,
                   ts_rank(search_vector, plainto_tsquery('english', $1)) as rank_en
            FROM knowledge_sage.knowledge_entities
            WHERE search_vector @@ (plainto_tsquery('japanese', $1) || plainto_tsquery('english', $1))
            ORDER BY GREATEST(
                ts_rank(search_vector, plainto_tsquery('japanese', $1)),
                ts_rank(search_vector, plainto_tsquery('english', $1))
            ) DESC
            LIMIT $2
            """

            results = await conn.fetch(search_query, query, max_results)

            knowledge_list = []
            for result in results:
                knowledge = KnowledgeEntity(
                    id=str(result['id']),
                    title=result['title'],
                    content=result['content'],
                    content_type=result['content_type'],
                    embedding=np.array(result['embedding']) if result['embedding'] else None,
                    metadata=json.loads(result['metadata']) if result['metadata'] else {},
                    category=result['category'],
                    tags=result['tags'] or [],
                    quality_score=result['quality_score'],
                    parent_id=str(result['parent_id']) if result['parent_id'] else None,
                    created_at=result['created_at'],
                    updated_at=result['updated_at'],
                    created_by=result['created_by'],
                    updated_by=result['updated_by'],
                    version=result['version'],
                    access_count=result['access_count'],
                    last_accessed=result['last_accessed']
                )
                knowledge_list.append(knowledge)

            return knowledge_list

    async def update_knowledge(self, knowledge_id: str, updates: Dict[str, Any]) -> bool:
        """知識の更新"""
        async with self.db_manager.get_connection() as conn:
            set_clauses = []
            values = []
            param_count = 1

            for key, value in updates.items():
                if key == 'embedding' and isinstance(value, np.ndarray):
                    value = value.tolist()
                elif key == 'metadata' and isinstance(value, dict):
                    value = json.dumps(value)

                set_clauses.append(f"{key} = ${param_count}")
                values.append(value)
                param_count += 1

            # Always update version and updated_at
            set_clauses.append(f"version = version + 1")
            set_clauses.append(f"updated_at = NOW()")

            query = f"""
            UPDATE knowledge_sage.knowledge_entities
            SET {', '.join(set_clauses)}
            WHERE id = ${param_count}
            """
            values.append(knowledge_id)

            result = await conn.execute(query, *values)

            # Clear cache
            await self._clear_knowledge_cache(knowledge_id)

            return result == "UPDATE 1"

    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """知識の削除"""
        async with self.db_manager.get_connection() as conn:
            query = "DELETE FROM knowledge_sage.knowledge_entities WHERE id = $1"
            result = await conn.execute(query, knowledge_id)

            # Clear cache
            await self._clear_knowledge_cache(knowledge_id)

            return result == "DELETE 1"

    async def _cache_knowledge(self, knowledge_id: str, knowledge: KnowledgeEntity):
        """知識のキャッシュ"""
        if self.db_manager.redis_client:
            cache_key = f"knowledge:{knowledge_id}"
            cache_data = {
                'id': knowledge.id,
                'title': knowledge.title,
                'content': knowledge.content,
                'content_type': knowledge.content_type,
                'metadata': json.dumps(knowledge.metadata),
                'category': knowledge.category,
                'tags': json.dumps(knowledge.tags),
                'quality_score': knowledge.quality_score,
                'parent_id': knowledge.parent_id,
                'created_by': knowledge.created_by,
                'updated_by': knowledge.updated_by,
                'version': knowledge.version,
                'access_count': knowledge.access_count
            }

            await self.db_manager.redis_client.hset(cache_key, mapping=cache_data)
            await self.db_manager.redis_client.expire(cache_key, 3600)  # 1 hour TTL

    async def _get_cached_knowledge(self, knowledge_id: str) -> Optional[KnowledgeEntity]:
        """キャッシュから知識を取得"""
        if not self.db_manager.redis_client:
            return None

        cache_key = f"knowledge:{knowledge_id}"
        cached_data = await self.db_manager.redis_client.hgetall(cache_key)

        if not cached_data:
            return None

        try:
            knowledge = KnowledgeEntity(
                id=cached_data.get('id'),
                title=cached_data.get('title', ''),
                content=cached_data.get('content', ''),
                content_type=cached_data.get('content_type', 'text'),
                metadata=json.loads(cached_data.get('metadata', '{}')),
                category=cached_data.get('category'),
                tags=json.loads(cached_data.get('tags', '[]')),
                quality_score=float(cached_data.get('quality_score', 0.0)),
                parent_id=cached_data.get('parent_id'),
                created_by=cached_data.get('created_by'),
                updated_by=cached_data.get('updated_by'),
                version=int(cached_data.get('version', 1)),
                access_count=int(cached_data.get('access_count', 0))
            )
            return knowledge
        except Exception as e:
            logger.error(f"Error deserializing cached knowledge: {e}")
            return None

    async def _clear_knowledge_cache(self, knowledge_id: str):
        """知識のキャッシュをクリア"""
        if self.db_manager.redis_client:
            cache_key = f"knowledge:{knowledge_id}"
            await self.db_manager.redis_client.delete(cache_key)

    async def _update_access_count(self, knowledge_id: str):
        """アクセス数の更新"""
        async with self.db_manager.get_connection() as conn:
            query = """
            UPDATE knowledge_sage.knowledge_entities
            SET access_count = access_count + 1, last_accessed = NOW()
            WHERE id = $1
            """
            await conn.execute(query, knowledge_id)

# ============================================================================
# Task Sage Database Manager
# ============================================================================

@dataclass
class TaskEntity:
    """タスクエンティティデータクラス"""
    id: Optional[str] = None
    name: str = ""
    description: str = ""
    status: str = "pending"
    priority: int = 5
    created_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: Optional[timedelta] = None
    retry_count: int = 0
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None

class TaskSageManager:
    """Task Sage データベース管理"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def create_task(self, task: TaskEntity) -> str:
        """タスクの作成"""
        async with self.db_manager.get_connection() as conn:
            query = """
            INSERT INTO task_sage.tasks
            (name, description, status, priority, scheduled_at, deadline, dependencies,
             resource_requirements, created_by, assigned_to)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """

            result = await conn.fetchrow(
                query,
                task.name,
                task.description,
                task.status,
                task.priority,
                task.scheduled_at,
                task.deadline,
                task.dependencies,
                json.dumps(task.resource_requirements),
                task.created_by,
                task.assigned_to
            )

            task_id = str(result['id'])
            logger.info(f"Created task: {task_id}")
            return task_id

    async def get_task(self, task_id: str) -> Optional[TaskEntity]:
        """タスクの取得"""
        async with self.db_manager.get_connection() as conn:
            query = """
            SELECT id, name, description, status, priority, created_at, scheduled_at,
                   started_at, completed_at, deadline, dependencies, resource_requirements,
                   result, error_message, execution_time, retry_count, created_by, assigned_to
            FROM task_sage.tasks
            WHERE id = $1
            """

            result = await conn.fetchrow(query, task_id)
            if not result:
                return None

            task = TaskEntity(
                id=str(result['id']),
                name=result['name'],
                description=result['description'],
                status=result['status'],
                priority=result['priority'],
                created_at=result['created_at'],
                scheduled_at=result['scheduled_at'],
                started_at=result['started_at'],
                completed_at=result['completed_at'],
                deadline=result['deadline'],
                dependencies=result['dependencies'] or [],
                resource_requirements=json.loads(result['resource_requirements']) if result['resource_requirements'] else {},
                result=json.loads(result['result']) if result['result'] else {},
                error_message=result['error_message'],
                execution_time=result['execution_time'],
                retry_count=result['retry_count'],
                created_by=result['created_by'],
                assigned_to=result['assigned_to']
            )

            return task

    async def update_task_status(self, task_id: str, status: str,
                               result: Optional[Dict[str, Any]] = None,
                               error_message: Optional[str] = None) -> bool:
        """タスクステータスの更新"""
        async with self.db_manager.get_connection() as conn:
            updates = ['status = $2']
            values = [task_id, status]
            param_count = 3

            if status == 'running':
                updates.append('started_at = NOW()')
            elif status in ['completed', 'failed']:
                updates.append('completed_at = NOW()')
                if result:
                    updates.append(f'result = ${param_count}')
                    values.append(json.dumps(result))
                    param_count += 1
                if error_message:
                    updates.append(f'error_message = ${param_count}')
                    values.append(error_message)
                    param_count += 1

            query = f"""
            UPDATE task_sage.tasks
            SET {', '.join(updates)}
            WHERE id = $1
            """

            result = await conn.execute(query, *values)
            return result == "UPDATE 1"

    async def get_pending_tasks(self, limit: int = 100) -> List[TaskEntity]:
        """実行待ちタスクの取得"""
        async with self.db_manager.get_connection() as conn:
            query = """
            SELECT id, name, description, status, priority, created_at, scheduled_at,
                   started_at, completed_at, deadline, dependencies, resource_requirements,
                   result, error_message, execution_time, retry_count, created_by, assigned_to
            FROM task_sage.tasks
            WHERE status = 'pending'
            AND (scheduled_at IS NULL OR scheduled_at <= NOW())
            ORDER BY priority DESC, created_at ASC
            LIMIT $1
            """

            results = await conn.fetch(query, limit)

            tasks = []
            for result in results:
                task = TaskEntity(
                    id=str(result['id']),
                    name=result['name'],
                    description=result['description'],
                    status=result['status'],
                    priority=result['priority'],
                    created_at=result['created_at'],
                    scheduled_at=result['scheduled_at'],
                    started_at=result['started_at'],
                    completed_at=result['completed_at'],
                    deadline=result['deadline'],
                    dependencies=result['dependencies'] or [],
                    resource_requirements=json.loads(result['resource_requirements']) if result['resource_requirements'] else {},
                    result=json.loads(result['result']) if result['result'] else {},
                    error_message=result['error_message'],
                    execution_time=result['execution_time'],
                    retry_count=result['retry_count'],
                    created_by=result['created_by'],
                    assigned_to=result['assigned_to']
                )
                tasks.append(task)

            return tasks

# ============================================================================
# Unified Elders Guild Database Manager
# ============================================================================

class EldersGuildDatabaseManager:
    """エルダーズギルド統合データベース管理"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.db_manager = DatabaseManager(self.config)
        self.knowledge_sage = KnowledgeSageManager(self.db_manager)
        self.task_sage = TaskSageManager(self.db_manager)

    async def initialize(self):
        """データベースの初期化"""
        await self.db_manager.initialize()
        logger.info("Elders Guild Database Manager initialized")

    async def close(self):
        """データベース接続のクローズ"""
        await self.db_manager.close()
        logger.info("Elders Guild Database Manager closed")

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        health_status = {
            "database": "unknown",
            "redis": "unknown",
            "timestamp": datetime.now().isoformat()
        }

        try:
            # PostgreSQL health check
            async with self.db_manager.get_connection() as conn:
                await conn.fetchval("SELECT 1")
                health_status["database"] = "healthy"
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"

        try:
            # Redis health check
            if self.db_manager.redis_client:
                await self.db_manager.redis_client.ping()
                health_status["redis"] = "healthy"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"

        return health_status

# ============================================================================
# Example Usage
# ============================================================================

async def main():
    """使用例"""
    config = DatabaseConfig()
    db_manager = EldersGuildDatabaseManager(config)

    try:
        await db_manager.initialize()

        # Health check
        health = await db_manager.health_check()
        print(f"Health Status: {health}")

        # Create sample knowledge
        knowledge = KnowledgeEntity(
            title="エルダーズギルドアーキテクチャ",
            content="エルダーズギルドは4つの賢者からなるAI統合プラットフォームです。",
            content_type="text",
            embedding=np.random.rand(1536),  # Sample embedding
            metadata={"source": "documentation", "language": "ja"},
            category="architecture",
            tags=["elders", "guild", "architecture"],
            quality_score=0.9,
            created_by="Claude Elder"
        )

        knowledge_id = await db_manager.knowledge_sage.create_knowledge(knowledge)
        print(f"Created knowledge: {knowledge_id}")

        # Retrieve knowledge
        retrieved = await db_manager.knowledge_sage.get_knowledge(knowledge_id)
        print(f"Retrieved knowledge: {retrieved.title}")

        # Semantic search
        search_results = await db_manager.knowledge_sage.semantic_search(
            np.random.rand(1536),
            similarity_threshold=0.5,
            max_results=5
        )
        print(f"Search results: {len(search_results)}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
