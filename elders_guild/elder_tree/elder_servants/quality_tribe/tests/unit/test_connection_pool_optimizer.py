"""
Test suite for Connection Pool Optimizer
Phase 3 implementation - Network efficiency optimization
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from datetime import datetime, timedelta

from elders_guild.elder_tree.connection_pool_optimizer import (
    ConnectionPoolOptimizer,
    ConnectionPool,
    RateLimiter,
    RetryStrategy,
    ConnectionMetrics,
    APICallBatch,
    ConnectionHealth
)


class TestConnectionPoolOptimizer:
    """Test suite for connection pool optimization"""
    
    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance"""
        return ConnectionPoolOptimizer(
            max_connections=10,
            rate_limit_per_hour=5000,
            retry_attempts=3,
            connection_timeout=30
        )
    
    def test_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.max_connections == 10
        assert optimizer.rate_limit_per_hour == 5000
        assert optimizer.retry_attempts == 3
        assert optimizer.connection_timeout == 30
        assert optimizer.metrics.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_connection_pool_creation(self, optimizer):
        """Test connection pool creation and management"""
        pool = await optimizer.get_connection_pool()
        
        assert isinstance(pool, ConnectionPool)
        assert pool.max_size == 10
        assert pool.available_connections >= 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, optimizer):
        """Test rate limiting functionality"""
        rate_limiter = optimizer.rate_limiter
        
        # Should allow initial requests
        for i in range(5):
            allowed = await rate_limiter.acquire()
            assert allowed is True
        
        # Simulate rate limit hit
        rate_limiter._current_usage = rate_limiter.limit_per_hour
        
        allowed = await rate_limiter.acquire()
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_intelligent_batching(self, optimizer):
        """Test intelligent API call batching"""
        # Create multiple API calls
        calls = []
        for i in range(20):
            call = APICallBatch(
                method='GET',
                url=f'https://api.github.com/repos/user/repo/issues/{i}',
                headers={'Authorization': 'token xyz'}
            )
            calls.append(call)
        
        # Batch them
        batches = await optimizer.create_batches(calls, max_batch_size=5)
        
        assert len(batches) == 4  # 20/5 = 4 batches
        for batch in batches:
            assert len(batch.calls) <= 5
    
    @pytest.mark.asyncio
    async def test_retry_strategy(self, optimizer):
        """Test retry with exponential backoff"""
        retry_strategy = RetryStrategy(
            max_attempts=3,
            initial_delay=1.0,
            backoff_factor=2.0
        )
        
        optimizer.retry_strategy = retry_strategy
        
        # Mock failing request
        async def failing_request():
            raise aiohttp.ClientError("Connection failed")
        
        start_time = time.time()
        
        with pytest.raises(aiohttp.ClientError):
            await optimizer.execute_with_retry(failing_request)
        
        elapsed = time.time() - start_time
        # Should have waited: 1 + 2 + 4 = 7 seconds minimum
        assert elapsed >= 6  # Allow some variance
        assert optimizer.metrics.retry_count >= 2
    
    @pytest.mark.asyncio
    async def test_connection_health_monitoring(self, optimizer):
        """Test connection health monitoring"""
        pool = await optimizer.get_connection_pool()
        
        # Add mock connections
        for i in range(5):
            conn = Mock()
            conn.is_connected = True
            conn.last_used = datetime.now()
            pool._connections.append(conn)
        
        # Check health
        health_report = await optimizer.check_connection_health()
        
        assert isinstance(health_report, ConnectionHealth)
        assert health_report.total_connections == 5
        assert health_report.healthy_connections <= 5
    
    @pytest.mark.asyncio
    async def test_connection_warming(self, optimizer):
        """Test connection pre-warming"""
        # Warm up connections
        await optimizer.warm_connections(count=5)
        
        pool = await optimizer.get_connection_pool()
        assert pool.available_connections >= 5
        assert optimizer.metrics.warmed_connections >= 5
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, optimizer):
        """Test concurrent request handling"""
        # Mock successful responses
        async def mock_request(url):
            await asyncio.sleep(0.1)  # Simulate network delay
            return {"status": "success", "url": url}
        
        optimizer._make_request = mock_request
        
        # Create multiple concurrent requests
        urls = [f"https://api.github.com/test/{i}" for i in range(10)]
        
        start_time = time.time()
        results = await optimizer.execute_concurrent_requests(urls)
        elapsed = time.time() - start_time
        
        assert len(results) == 10
        assert elapsed < 1.0  # Should be much faster than 1 second (10 * 0.1)
        assert optimizer.metrics.concurrent_requests >= 10
    
    @pytest.mark.asyncio
    async def test_api_quota_management(self, optimizer):
        """Test API quota management"""
        # Set low quota for testing
        optimizer.rate_limiter.limit_per_hour = 100
        optimizer.rate_limiter._current_usage = 95
        
        # Check remaining quota
        remaining = optimizer.get_remaining_quota()
        assert remaining == 5
        
        # Should throttle when approaching limit
        should_throttle = optimizer.should_throttle_requests()
        assert should_throttle is True
    
    @pytest.mark.asyncio
    async def test_connection_pooling_efficiency(self, optimizer):
        """Test connection pooling efficiency"""
        # Make multiple requests to same host
        urls = [f"https://api.github.com/test/{i}" for i in range(20)]
        
        async def mock_request(url):
            return {"data": f"response for {url}"}
        
        optimizer._make_request = mock_request
        
        # Execute requests
        start_time = time.time()
        results = await optimizer.execute_pooled_requests(urls)
        elapsed = time.time() - start_time
        
        assert len(results) == 20
        assert optimizer.metrics.pool_reuse_count > 0
    
    @pytest.mark.asyncio
    async def test_failover_mechanism(self, optimizer):
        """Test connection failover"""
        # Configure multiple endpoints
        primary_endpoint = "https://api.github.com"
        fallback_endpoint = "https://api-fallback.github.com"
        
        optimizer.configure_failover([primary_endpoint, fallback_endpoint])
        
        # Mock primary failure
        async def mock_request_with_failover(url):
            if "api.github.com" in url:
                raise aiohttp.ClientError("Primary endpoint down")
            return {"data": "fallback response"}
        
        optimizer._make_request = mock_request_with_failover
        
        result = await optimizer.make_request_with_failover("/test")
        assert result["data"] == "fallback response"
        assert optimizer.metrics.failover_count > 0
    
    @pytest.mark.asyncio
    async def test_response_caching(self, optimizer):
        """Test response caching"""
        # Enable caching
        optimizer.enable_caching(ttl_seconds=300)
        
        url = "https://api.github.com/test/cache"
        
        # First request - should cache
        async def mock_request(url):
            return {"data": "cached response", "timestamp": time.time()}
        
        optimizer._make_request = mock_request
        
        result1 = await optimizer.make_cached_request(url)
        result2 = await optimizer.make_cached_request(url)
        
        # Second request should be from cache (same timestamp)
        assert result1["timestamp"] == result2["timestamp"]
        assert optimizer.metrics.cache_hits > 0
    
    @pytest.mark.asyncio
    async def test_request_prioritization(self, optimizer):
        """Test request priority handling"""
        # Create requests with different priorities
        high_priority = APICallBatch(
            method='GET',
            url='https://api.github.com/urgent',
            priority=10
        )
        
        low_priority = APICallBatch(
            method='GET',
            url='https://api.github.com/normal',
            priority=1
        )
        
        # Add to queue
        await optimizer.add_to_queue(low_priority)
        await optimizer.add_to_queue(high_priority)
        
        # Should process high priority first
        next_request = await optimizer.get_next_request()
        assert next_request.priority == 10
    
    @pytest.mark.asyncio
    async def test_bandwidth_optimization(self, optimizer):
        """Test bandwidth usage optimization"""
        # Configure bandwidth limits
        optimizer.set_bandwidth_limit(mbps=10)
        
        # Large request that should be throttled
        large_data = "x" * (1024 * 1024)  # 1MB
        
        start_time = time.time()
        await optimizer.send_data_with_throttling(large_data)
        elapsed = time.time() - start_time
        
        # Should take time due to bandwidth limiting
        assert elapsed > 0.1  # At least 100ms for 1MB at 10Mbps
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, optimizer):
        """Test complete connection lifecycle"""
        pool = await optimizer.get_connection_pool()
        
        # Get connection
        conn = await pool.acquire_connection()
        assert conn is not None
        assert pool.active_connections > 0
        
        # Use connection
        await optimizer.use_connection(conn)
        
        # Release connection
        await pool.release_connection(conn)
        assert pool.available_connections > pool.active_connections
    
    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, optimizer):
        """Test connection timeout handling"""
        # Mock slow request
        async def slow_request():
            await asyncio.sleep(2)  # 2 second delay
            return {"data": "slow response"}
        
        # Set short timeout
        optimizer.connection_timeout = 1  # 1 second
        
        start_time = time.time()
        with pytest.raises(asyncio.TimeoutError):
            await optimizer.execute_with_timeout(slow_request)
        
        elapsed = time.time() - start_time
        assert elapsed < 1.5  # Should timeout quickly
    
    def test_metrics_export(self, optimizer):
        """Test metrics export"""
        metrics = optimizer.export_metrics()
        
        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "average_response_time" in metrics
        assert "connection_pool_usage" in metrics
        assert "rate_limit_hits" in metrics
        assert "cache_hit_ratio" in metrics
    
    @pytest.mark.asyncio
    async def test_adaptive_pool_sizing(self, optimizer):
        """Test adaptive connection pool sizing"""
        # Start with small pool
        initial_size = 5
        await optimizer.resize_pool(initial_size)
        
        # Simulate high load
        for _ in range(20):
            optimizer.metrics.total_requests += 1
        
        # Should auto-scale up
        await optimizer.auto_scale_pool()
        
        pool = await optimizer.get_connection_pool()
        assert pool.max_size > initial_size
    
    @pytest.mark.asyncio
    async def test_request_deduplication(self, optimizer):
        """Test duplicate request detection and merging"""
        url = "https://api.github.com/same-request"
        
        # Submit multiple identical requests
        tasks = [
            optimizer.make_deduplicated_request(url)
            for _ in range(5)
        ]
        
        async def mock_request(url):
            await asyncio.sleep(0.1)
            return {"data": "single response"}
        
        optimizer._make_request = mock_request
        
        results = await asyncio.gather(*tasks)
        
        # All should get same result
        assert all(r["data"] == "single response" for r in results)
        assert optimizer.metrics.deduplicated_requests >= 4  # 4 were deduplicated