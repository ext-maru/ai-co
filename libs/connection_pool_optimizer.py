"""
Connection Pool Optimizer for Auto Issue Processor A2A
Phase 3 implementation - Network efficiency through intelligent connection management
"""
import asyncio
import aiohttp
import time
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from collections import deque, defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Metrics for connection pool optimization"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retry_count: int = 0
    average_response_time: float = 0.0
    connection_pool_usage: float = 0.0
    rate_limit_hits: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    concurrent_requests: int = 0
    warmed_connections: int = 0
    pool_reuse_count: int = 0
    failover_count: int = 0
    deduplicated_requests: int = 0


@dataclass
class APICallBatch:
    """Batch of API calls"""
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    data: Optional[Any] = None
    priority: int = 5
    calls: List['APICallBatch'] = field(default_factory=list)


@dataclass
class ConnectionHealth:
    """Connection health status"""
    total_connections: int
    healthy_connections: int
    unhealthy_connections: int
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class RetryStrategy:
    """Retry configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)


class RateLimiter:
    """Intelligent rate limiter"""
    
    def __init__(self, limit_per_hour: int = 5000):
        self.limit_per_hour = limit_per_hour
        self._current_usage = 0
        self._usage_window = deque()
        self._last_reset = datetime.now()
    
    async def acquire(self) -> bool:
        """Acquire rate limit token"""
        now = datetime.now()
        
        # Reset hourly counter
        if now - self._last_reset > timedelta(hours=1):
            self._current_usage = 0
            self._last_reset = now
            self._usage_window.clear()
        
        # Remove old entries from sliding window
        cutoff = now - timedelta(hours=1)
        while self._usage_window and self._usage_window[0] < cutoff:
            self._usage_window.popleft()
            if self._current_usage > 0:
                self._current_usage -= 1
        
        if self._current_usage < self.limit_per_hour:
            self._current_usage += 1
            self._usage_window.append(now)
            return True
        
        return False
    
    def get_remaining(self) -> int:
        """Get remaining quota"""
        return max(0, self.limit_per_hour - self._current_usage)
    
    def get_reset_time(self) -> datetime:
        """Get next reset time"""
        return self._last_reset + timedelta(hours=1)


class ConnectionPool:
    """Intelligent connection pool"""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._connections: List[aiohttp.ClientSession] = []
        self._available: deque = deque()
        self._active: Set[aiohttp.ClientSession] = set()
        self._lock = asyncio.Lock()
    
    async def acquire_connection(self) -> Optional[aiohttp.ClientSession]:
        """Acquire connection from pool"""
        async with self._lock:
            if self._available:
                conn = self._available.popleft()
                self._active.add(conn)
                return conn
            elif len(self._connections) < self.max_size:
                # Create new connection
                connector = aiohttp.TCPConnector(
                    limit=100,
                    limit_per_host=10,
                    keepalive_timeout=30
                )
                session = aiohttp.ClientSession(connector=connector)
                self._connections.append(session)
                self._active.add(session)
                return session
            
            return None  # Pool exhausted
    
    async def release_connection(self, conn: aiohttp.ClientSession) -> None:
        """Release connection back to pool"""
        async with self._lock:
            if conn in self._active:
                self._active.remove(conn)
                self._available.append(conn)
    
    @property
    def available_connections(self) -> int:
        """Get number of available connections"""
        return len(self._available)
    
    @property
    def active_connections(self) -> int:
        """Get number of active connections"""
        return len(self._active)
    
    async def resize(self, new_size: int) -> None:
        """Resize pool"""
        async with self._lock:
            if new_size > self.max_size:
                # Grow pool
                self.max_size = new_size
            elif new_size < self.max_size:
                # Shrink pool
                excess = len(self._connections) - new_size
                for _ in range(excess):
                    if self._available:
                        conn = self._available.pop()
                        await conn.close()
                        self._connections.remove(conn)
                self.max_size = new_size


class ConnectionPoolOptimizer:
    """Advanced connection pool optimizer"""
    
    def __init__(self, max_connections: int = 20, rate_limit_per_hour: int = 5000,
                 retry_attempts: int = 3, connection_timeout: int = 30):
        self.max_connections = max_connections
        self.rate_limit_per_hour = rate_limit_per_hour
        self.retry_attempts = retry_attempts
        self.connection_timeout = connection_timeout
        
        self.metrics = ConnectionMetrics()
        self.rate_limiter = RateLimiter(rate_limit_per_hour)
        self.retry_strategy = RetryStrategy(max_attempts=retry_attempts)
        
        self._connection_pool: Optional[ConnectionPool] = None
        self._response_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutes default
        
        self._request_queue = asyncio.PriorityQueue()
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
        self._failover_endpoints: List[str] = []
        self._current_endpoint_index = 0
        
        self._bandwidth_limit_mbps: Optional[float] = None
        self._last_bandwidth_check = time.time()
        self._bytes_sent = 0
    
    async def get_connection_pool(self) -> ConnectionPool:
        """Get or create connection pool"""
        if self._connection_pool is None:
            self._connection_pool = ConnectionPool(self.max_connections)
        return self._connection_pool
    
    async def create_batches(self, calls: List[APICallBatch], 
                           max_batch_size: int = 10) -> List[APICallBatch]:
        """Create intelligent batches from API calls"""
        # Group by similar characteristics
        groups = defaultdict(list)
        
        for call in calls:
            # Group by domain and method
            key = f"{call.method}:{self._get_domain(call.url)}"
            groups[key].append(call)
        
        batches = []
        for group_calls in groups.values():
            # Split into batches of max_batch_size
            for i in range(0, len(group_calls), max_batch_size):
                batch_calls = group_calls[i:i + max_batch_size]
                batch = APICallBatch(
                    method=batch_calls[0].method,
                    url="batch",
                    calls=batch_calls
                )
                batches.append(batch)
        
        return batches
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    async def execute_with_retry(self, func: Callable) -> Any:
        """Execute function with retry strategy"""
        last_exception = None
        
        for attempt in range(self.retry_strategy.max_attempts):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                self.metrics.retry_count += 1
                
                if attempt < self.retry_strategy.max_attempts - 1:
                    delay = self.retry_strategy.get_delay(attempt)
                    await asyncio.sleep(delay)
        
        # All retries failed
        raise last_exception
    
    async def check_connection_health(self) -> ConnectionHealth:
        """Check health of all connections"""
        pool = await self.get_connection_pool()
        
        total = len(pool._connections)
        healthy = 0
        
        for conn in pool._connections:
            if not conn.closed:
                healthy += 1
        
        return ConnectionHealth(
            total_connections=total,
            healthy_connections=healthy,
            unhealthy_connections=total - healthy
        )
    
    async def warm_connections(self, count: int) -> None:
        """Pre-warm connections"""
        pool = await self.get_connection_pool()
        
        for _ in range(count):
            conn = await pool.acquire_connection()
            if conn:
                self.metrics.warmed_connections += 1
                await pool.release_connection(conn)
    
    async def execute_concurrent_requests(self, urls: List[str]) -> List[Any]:
        """Execute multiple requests concurrently"""
        semaphore = asyncio.Semaphore(self.max_connections)
        
        async def bounded_request(url):
            async with semaphore:
                return await self._make_request(url)
        
        self.metrics.concurrent_requests += len(urls)
        tasks = [bounded_request(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_remaining_quota(self) -> int:
        """Get remaining API quota"""
        return self.rate_limiter.get_remaining()
    
    def should_throttle_requests(self) -> bool:
        """Check if should throttle requests"""
        remaining = self.get_remaining_quota()
        return remaining < (self.rate_limit_per_hour * 0.1)  # Less than 10%
    
    async def execute_pooled_requests(self, urls: List[str]) -> List[Any]:
        """Execute requests using connection pooling"""
        pool = await self.get_connection_pool()
        results = []
        
        for url in urls:
            conn = await pool.acquire_connection()
            if conn:
                try:
                    result = await self._make_request(url)
                    results.append(result)
                    self.metrics.pool_reuse_count += 1
                finally:
                    await pool.release_connection(conn)
            else:
                # Pool exhausted, make direct request
                result = await self._make_request(url)
                results.append(result)
        
        return results
    
    def configure_failover(self, endpoints: List[str]) -> None:
        """Configure failover endpoints"""
        self._failover_endpoints = endpoints
        self._current_endpoint_index = 0
    
    async def make_request_with_failover(self, path: str) -> Any:
        """Make request with automatic failover"""
        if not self._failover_endpoints:
            raise ValueError("No failover endpoints configured")
        
        for i, endpoint in enumerate(self._failover_endpoints):
            try:
                url = f"{endpoint}{path}"
                return await self._make_request(url)
            except Exception as e:
                if i == len(self._failover_endpoints) - 1:
                    # Last endpoint failed
                    raise e
                
                # Try next endpoint
                self.metrics.failover_count += 1
                continue
    
    def enable_caching(self, ttl_seconds: int = 300) -> None:
        """Enable response caching"""
        self._cache_ttl = ttl_seconds
    
    async def make_cached_request(self, url: str) -> Any:
        """Make request with caching"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        
        # Check cache
        if cache_key in self._response_cache:
            timestamp = self._cache_timestamps[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self._cache_ttl):
                self.metrics.cache_hits += 1
                return self._response_cache[cache_key]
        
        # Cache miss or expired
        self.metrics.cache_misses += 1
        result = await self._make_request(url)
        
        # Store in cache
        self._response_cache[cache_key] = result
        self._cache_timestamps[cache_key] = datetime.now()
        
        return result
    
    async def add_to_queue(self, request: APICallBatch) -> None:
        """Add request to priority queue"""
        # Use negative priority for max-heap behavior
        await self._request_queue.put((-request.priority, request))
    
    async def get_next_request(self) -> APICallBatch:
        """Get next highest priority request"""
        priority, request = await self._request_queue.get()
        return request
    
    def set_bandwidth_limit(self, mbps: float) -> None:
        """Set bandwidth limit"""
        self._bandwidth_limit_mbps = mbps
    
    async def send_data_with_throttling(self, data: str) -> None:
        """Send data with bandwidth throttling"""
        if not self._bandwidth_limit_mbps:
            return
        
        data_size_mb = len(data.encode('utf-8')) / (1024 * 1024)
        max_rate_mb_per_second = self._bandwidth_limit_mbps / 8  # Convert to MB/s
        
        if data_size_mb > 0:
            required_time = data_size_mb / max_rate_mb_per_second
            await asyncio.sleep(required_time)
        
        self._bytes_sent += len(data.encode('utf-8'))
    
    async def use_connection(self, conn: aiohttp.ClientSession) -> None:
        """Use connection for a request"""
        # Simulate using connection
        await asyncio.sleep(0.01)
    
    async def execute_with_timeout(self, func: Callable) -> Any:
        """Execute function with timeout"""
        return await asyncio.wait_for(func(), timeout=self.connection_timeout)
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export optimizer metrics"""
        cache_total = self.metrics.cache_hits + self.metrics.cache_misses
        cache_hit_ratio = (self.metrics.cache_hits / cache_total * 100 
                          if cache_total > 0 else 0)
        
        return {
            'total_requests': self.metrics.total_requests,
            'successful_requests': self.metrics.successful_requests,
            'failed_requests': self.metrics.failed_requests,
            'average_response_time': self.metrics.average_response_time,
            'connection_pool_usage': self.metrics.connection_pool_usage,
            'rate_limit_hits': self.metrics.rate_limit_hits,
            'cache_hit_ratio': cache_hit_ratio,
            'concurrent_requests': self.metrics.concurrent_requests,
            'pool_reuse_count': self.metrics.pool_reuse_count,
            'failover_count': self.metrics.failover_count,
            'remaining_quota': self.get_remaining_quota()
        }
    
    async def resize_pool(self, new_size: int) -> None:
        """Resize connection pool"""
        pool = await self.get_connection_pool()
        await pool.resize(new_size)
    
    async def auto_scale_pool(self) -> None:
        """Auto-scale pool based on usage"""
        if self.metrics.total_requests > 100:  # High usage
            current_size = self.max_connections
            new_size = min(current_size * 2, 50)  # Cap at 50
            await self.resize_pool(new_size)
            self.max_connections = new_size
    
    async def make_deduplicated_request(self, url: str) -> Any:
        """Make request with deduplication"""
        if url in self._pending_requests:
            # Request already pending, wait for result
            self.metrics.deduplicated_requests += 1
            return await self._pending_requests[url]
        
        # Create new request
        future = asyncio.Future()
        self._pending_requests[url] = future
        
        try:
            result = await self._make_request(url)
            future.set_result(result)
            return result
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            # Clean up
            if url in self._pending_requests:
                del self._pending_requests[url]
    
    async def _make_request(self, url: str) -> Any:
        """Make HTTP request (mock implementation)"""
        # Check rate limit
        if not await self.rate_limiter.acquire():
            self.metrics.rate_limit_hits += 1
            raise Exception("Rate limit exceeded")
        
        # Simulate request
        start_time = time.time()
        
        try:
            # Mock successful response
            await asyncio.sleep(0.1)  # Simulate network delay
            
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            
            response_time = time.time() - start_time
            self.metrics.average_response_time = (
                (self.metrics.average_response_time * (self.metrics.total_requests - 1) + response_time) /
                self.metrics.total_requests
            )
            
            return {"status": "success", "url": url, "data": "mock response"}
            
        except Exception as e:
            self.metrics.failed_requests += 1
            raise