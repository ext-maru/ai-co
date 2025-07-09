import os
from typing import Generator, Optional
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import redis
from contextlib import contextmanager

from .config import settings

# Database Configuration
if settings.is_production:
    # Production: PostgreSQL with connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
else:
    # Development: SQLite for simplicity
    if settings.DATABASE_URL.startswith("postgresql"):
        engine = create_engine(
            settings.DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=True  # Enable SQL logging in development
        )
    else:
        # Fallback to SQLite for local development
        sqlite_url = "sqlite:///./ai_company.db"
        engine = create_engine(
            sqlite_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=True
        )

# Session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for schema management
metadata = MetaData()

# Redis Configuration
try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    # Test connection
    redis_client.ping()
    print("✅ Redis connection established")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    # Fallback to in-memory cache
    redis_client = None

class DatabaseManager:
    """Database manager with advanced features"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.redis_client = redis_client
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            print("✅ Database tables dropped successfully")
        except Exception as e:
            print(f"❌ Failed to drop database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection information"""
        return {
            "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
            "dialect": self.engine.dialect.name,
            "driver": self.engine.dialect.driver,
            "pool_size": getattr(self.engine.pool, 'size', None),
            "pool_checked_out": getattr(self.engine.pool, 'checkedout', None),
            "is_production": settings.is_production
        }

# Global database manager instance
db_manager = DatabaseManager()

# Dependency to get database session
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to get database session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Redis Cache Manager
class CacheManager:
    """Redis cache manager with fallback to in-memory cache"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.fallback_cache = {}  # In-memory fallback
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if self.redis_client:
            try:
                return self.redis_client.get(key)
            except Exception:
                pass
        
        return self.fallback_cache.get(key)
    
    async def set(self, key: str, value: str, expire: int = 3600):
        """Set value in cache with expiration"""
        if self.redis_client:
            try:
                self.redis_client.setex(key, expire, value)
                return
            except Exception:
                pass
        
        # Fallback to in-memory cache
        self.fallback_cache[key] = value
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass
        
        self.fallback_cache.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if self.redis_client:
            try:
                return bool(self.redis_client.exists(key))
            except Exception:
                pass
        
        return key in self.fallback_cache
    
    async def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        if self.redis_client:
            try:
                return self.redis_client.keys(pattern)
            except Exception:
                pass
        
        # Simple pattern matching for fallback
        import fnmatch
        return [key for key in self.fallback_cache.keys() if fnmatch.fnmatch(key, pattern)]
    
    async def incr(self, key: str) -> int:
        """Increment counter"""
        if self.redis_client:
            try:
                return self.redis_client.incr(key)
            except Exception:
                pass
        
        current = int(self.fallback_cache.get(key, 0))
        self.fallback_cache[key] = str(current + 1)
        return current + 1
    
    async def expire(self, key: str, seconds: int):
        """Set expiration for key"""
        if self.redis_client:
            try:
                self.redis_client.expire(key, seconds)
            except Exception:
                pass
        # Note: Fallback cache doesn't support expiration

# Global cache manager instance
cache_manager = CacheManager(redis_client)

# Database Event Listeners
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance"""
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries in development"""
    if not settings.is_production:
        conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries in development"""
    if not settings.is_production:
        total = time.time() - conn.info['query_start_time'].pop(-1)
        if total > 0.1:  # Log queries slower than 100ms
            print(f"Slow query: {total:.3f}s - {statement[:100]}...")

# Sage Data Models
class SageData:
    """Data access layer for Sage system"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    async def get_sage_status(self, sage_type: str) -> dict:
        """Get sage status with caching"""
        cache_key = f"sage_status:{sage_type}"
        cached = await self.cache.get(cache_key)
        
        if cached:
            import json
            return json.loads(cached)
        
        # Fetch from database or external API
        status = {
            "type": sage_type,
            "status": "active",
            "coverage": 66.7,
            "last_update": time.time()
        }
        
        # Cache for 5 minutes
        import json
        await self.cache.set(cache_key, json.dumps(status), 300)
        
        return status
    
    async def update_sage_status(self, sage_type: str, status: dict):
        """Update sage status"""
        cache_key = f"sage_status:{sage_type}"
        import json
        await self.cache.set(cache_key, json.dumps(status), 300)
    
    async def get_all_sages_status(self) -> dict:
        """Get status of all sages"""
        sage_types = ["incident", "knowledge", "search", "task"]
        statuses = {}
        
        for sage_type in sage_types:
            statuses[sage_type] = await self.get_sage_status(sage_type)
        
        return statuses

# Elder Council Data Models
class ElderCouncilData:
    """Data access layer for Elder Council system"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    async def get_council_status(self) -> dict:
        """Get Elder Council status"""
        cache_key = "elder_council_status"
        cached = await self.cache.get(cache_key)
        
        if cached:
            import json
            return json.loads(cached)
        
        status = {
            "active_members": 4,
            "coverage_target": 66.7,
            "current_coverage": 66.7,
            "last_session": time.time(),
            "status": "active"
        }
        
        import json
        await self.cache.set(cache_key, json.dumps(status), 600)  # 10 minutes
        
        return status
    
    async def update_council_status(self, status: dict):
        """Update Elder Council status"""
        cache_key = "elder_council_status"
        import json
        await self.cache.set(cache_key, json.dumps(status), 600)

# Global data access instances
sage_data = SageData(cache_manager)
elder_council_data = ElderCouncilData(cache_manager)

# Health Check Functions
async def check_database_health() -> dict:
    """Check database health"""
    try:
        success = db_manager.test_connection()
        info = db_manager.get_connection_info()
        
        return {
            "status": "healthy" if success else "unhealthy",
            "connection_info": info,
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

async def check_redis_health() -> dict:
    """Check Redis health"""
    try:
        if redis_client:
            redis_client.ping()
            info = redis_client.info()
            
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "timestamp": time.time()
            }
        else:
            return {
                "status": "unavailable",
                "message": "Redis not configured",
                "timestamp": time.time()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Import time for timestamps
import time