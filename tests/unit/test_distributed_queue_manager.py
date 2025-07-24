"""
Test suite for Distributed Queue Manager
Phase 2 implementation - Queue management optimization
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from libs.distributed_queue_manager import (
    DistributedQueueManager,
    QueueItem,
    QueuePriority,
    QueueMetrics,
    BackpressureController,
    DeadLetterItem,
    RetryStrategy,
    Alert
)


class TestDistributedQueueManager:
    """Test suite for distributed queue management"""
    
    @pytest.fixture
    def queue_manager(self):
        """Create queue manager instance"""
        return DistributedQueueManager(
            max_size=1000,
            enable_dead_letter=True,
            enable_backpressure=True
        )
    
    def test_initialization(self, queue_manager):
        """Test queue manager initialization"""
        assert queue_manager.max_size == 1000
        assert queue_manager.enable_dead_letter is True
        assert queue_manager.enable_backpressure is True
        assert queue_manager.metrics.total_enqueued == 0
        assert queue_manager.metrics.total_dequeued == 0
    
    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self, queue_manager):
        """Test basic enqueue and dequeue operations"""
        item = QueueItem(
            id="test-1",
            data={"task": "process"},
            priority=QueuePriority.NORMAL
        )
        
        # Enqueue
        await queue_manager.enqueue(item)
        assert queue_manager.size() == 1
        
        # Dequeue
        dequeued = await queue_manager.dequeue()
        assert dequeued.id == "test-1"
        assert queue_manager.size() == 0
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self, queue_manager):
        """Test priority-based dequeuing"""
        # Add items with different priorities
        await queue_manager.enqueue(QueueItem("low", {}, QueuePriority.LOW))
        await queue_manager.enqueue(QueueItem("high", {}, QueuePriority.HIGH))
        await queue_manager.enqueue(QueueItem("normal", {}, QueuePriority.NORMAL))
        await queue_manager.enqueue(QueueItem("critical", {}, QueuePriority.CRITICAL))
        
        # Should dequeue in priority order
        assert (await queue_manager.dequeue()).id == "critical"
        assert (await queue_manager.dequeue()).id == "high"
        assert (await queue_manager.dequeue()).id == "normal"
        assert (await queue_manager.dequeue()).id == "low"
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, queue_manager):
        """Test batch enqueue and dequeue"""
        items = [
            QueueItem(f"item-{i}", {"index": i}, QueuePriority.NORMAL)
            for i in range(10)
        ]
        
        # Batch enqueue
        await queue_manager.enqueue_batch(items)
        assert queue_manager.size() == 10
        
        # Batch dequeue
        batch = await queue_manager.dequeue_batch(5)
        assert len(batch) == 5
        assert queue_manager.size() == 5
    
    @pytest.mark.asyncio
    async def test_backpressure_control(self, queue_manager):
        """Test backpressure mechanism"""
        queue_manager.max_size = 10
        
        # Fill queue to trigger backpressure
        for i in range(10):
            await queue_manager.enqueue(QueueItem(f"item-{i}", {}))
        
        # Check backpressure state
        assert queue_manager.is_backpressure_active()
        
        # Try to enqueue when full
        with pytest.raises(Exception) as exc_info:
            await queue_manager.enqueue(QueueItem("overflow", {}))
        assert "backpressure" in str(exc_info.value).lower()
        
        # Dequeue to relieve pressure
        await queue_manager.dequeue_batch(5)
        assert not queue_manager.is_backpressure_active()
    
    @pytest.mark.asyncio
    async def test_dead_letter_queue(self, queue_manager):
        """Test dead letter queue functionality"""
        # Create item with retry limit
        item = QueueItem("failing-item", {"error": True})
        item.retry_count = 3
        item.max_retries = 3
        
        # Process failure should move to DLQ
        await queue_manager.move_to_dead_letter(item, "Max retries exceeded")
        
        dlq_items = queue_manager.get_dead_letter_items()
        assert len(dlq_items) == 1
        assert dlq_items[0].id == "failing-item"
        assert dlq_items[0].failure_reason == "Max retries exceeded"
    
    @pytest.mark.asyncio
    async def test_retry_strategy(self, queue_manager):
        """Test retry strategy implementation"""
        strategy = RetryStrategy(
            max_attempts=3,
            initial_delay=1,
            backoff_factor=2,
            max_delay=10
        )
        
        queue_manager.set_retry_strategy(strategy)
        
        # Test retry delays
        assert strategy.get_retry_delay(1) == 1  # First retry
        assert strategy.get_retry_delay(2) == 2  # Second retry (1 * 2)
        assert strategy.get_retry_delay(3) == 4  # Third retry (2 * 2)
        assert strategy.get_retry_delay(4) == 10  # Capped at max_delay
    
    @pytest.mark.asyncio
    async def test_queue_metrics(self, queue_manager):
        """Test metrics collection"""
        # Perform operations
        for i in range(5):
            await queue_manager.enqueue(QueueItem(f"item-{i}", {}))
        
        for _ in range(3):
            await queue_manager.dequeue()
        
        metrics = queue_manager.get_metrics()
        assert metrics.total_enqueued == 5
        assert metrics.total_dequeued == 3
        assert metrics.current_size == 2
        assert metrics.avg_wait_time >= 0
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, queue_manager):
        """Test time-to-live expiration"""
        # Create item with short TTL
        item = QueueItem("expiring", {}, ttl_seconds=0.1)
        await queue_manager.enqueue(item)
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Dequeue should skip expired item
        result = await queue_manager.dequeue()
        assert result is None or result.id != "expiring"
        
        # Check expired items
        expired = queue_manager.get_expired_items()
        assert len(expired) == 1
        assert expired[0].id == "expiring"
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, queue_manager)async def producer(prefix: str, count: int)for i in range(count):
    """Test thread-safe concurrent access"""
            """producerメソッド"""
                await queue_manager.enqueue(
                    QueueItem(f"{prefix}-{i}", {})
                )
                await asyncio.sleep(0.01)
        
        async def consumer(count: int):
            """consumerメソッド"""
            items = []
            for _ in range(count):
                item = await queue_manager.dequeue()
                if item:
                    items.append(item)
                await asyncio.sleep(0.01)
            return items
        
        # Run concurrent producers and consumers
        await asyncio.gather(
            producer("p1", 10),
            producer("p2", 10),
            consumer(10),
            consumer(10)
        )
        
        # All items should be processed exactly once
        metrics = queue_manager.get_metrics()
        assert metrics.total_enqueued == 20
        assert metrics.total_dequeued == 20
    
    @pytest.mark.asyncio
    async def test_queue_persistence(self, queue_manager):
        """Test queue persistence to disk"""
        # Enable persistence
        queue_manager.enable_persistence("test_queue.db")
        
        # Add items
        for i in range(5):
            await queue_manager.enqueue(QueueItem(f"persist-{i}", {}))
        
        # Save state
        await queue_manager.save_state()
        
        # Create new queue and restore
        new_queue = DistributedQueueManager()
        await new_queue.restore_state("test_queue.db")
        
        assert new_queue.size() == 5
        item = await new_queue.dequeue()
        assert item.id == "persist-0"
    
    @pytest.mark.asyncio
    async def test_queue_monitoring(self, queue_manager):
        """Test queue monitoring and alerts"""
        # Set alert thresholds
        queue_manager.set_alert_threshold("size", 50)
        queue_manager.set_alert_threshold("wait_time", 5.0)
        
        # Fill queue to trigger size alert
        for i in range(60):
            await queue_manager.enqueue(QueueItem(f"item-{i}", {}))
        
        alerts = queue_manager.get_active_alerts()
        assert len(alerts) > 0
        assert any(a.type == "size_threshold" for a in alerts)
    
    @pytest.mark.asyncio
    async def test_selective_dequeue(self, queue_manager):
        """Test dequeue with filters"""
        # Add various items
        await queue_manager.enqueue(QueueItem("type-a", {"type": "A"}))
        await queue_manager.enqueue(QueueItem("type-b", {"type": "B"}))
        await queue_manager.enqueue(QueueItem("type-a2", {"type": "A"}))
        
        # Dequeue only type A
        item = await queue_manager.dequeue_filtered(
            lambda x: x.data.get("type") == "A"
        )
        assert item.id == "type-a"
        
        # Regular dequeue gets type B
        item = await queue_manager.dequeue()
        assert item.id == "type-b"
    
    @pytest.mark.asyncio
    async def test_queue_partitioning(self, queue_manager):
        """Test queue partitioning for scalability"""
        # Enable partitioning
        queue_manager.enable_partitioning(partitions=4)
        
        # Add items to different partitions
        for i in range(20):
            partition = i % 4
            await queue_manager.enqueue(
                QueueItem(f"item-{i}", {}),
                partition=partition
            )
        
        # Check partition distribution
        distribution = queue_manager.get_partition_distribution()
        assert len(distribution) == 4
        assert all(count == 5 for count in distribution.values())
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, queue_manager):
        """Test circuit breaker for downstream protection"""
        # Configure circuit breaker
        queue_manager.configure_circuit_breaker(
            failure_threshold=3,
            recovery_timeout=1.0
        )
        
        # Simulate failures
        for _ in range(3):
            await queue_manager.report_processing_failure("downstream_error")
        
        # Circuit should be open
        assert queue_manager.is_circuit_open()
        
        # Dequeue should be blocked
        with pytest.raises(Exception) as exc_info:
            await queue_manager.dequeue()
        assert "circuit breaker" in str(exc_info.value).lower()
        
        # Wait for recovery
        await asyncio.sleep(1.1)
        assert not queue_manager.is_circuit_open()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, queue_manager):
        """Test rate limiting for dequeue operations"""
        # Set rate limit
        queue_manager.set_rate_limit(10)  # 10 items per second
        
        # Add items
        for i in range(20):
            await queue_manager.enqueue(QueueItem(f"item-{i}", {}))
        
        # Measure dequeue rate
        start = time.time()
        count = 0
        
        while count < 15:
            item = await queue_manager.dequeue()
            if item:
                count += 1
        
        elapsed = time.time() - start
        rate = count / elapsed
        
        # Rate should be close to limit
        assert 8 <= rate <= 12  # Allow some variance
    
    def test_queue_stats_export(self, queue_manager)stats = queue_manager.export_stats()
    """Test statistics export for monitoring"""
        
        assert "queue_size" in stats
        assert "total_enqueued" in stats
        assert "total_dequeued" in stats
        assert "dead_letter_count" in stats
        assert "avg_wait_time" in stats
        assert "backpressure_events" in stats