"""
Test suite for Advanced Process Pool
Phase 2 implementation - Process pooling optimization
"""
import pytest
import asyncio
import time
import multiprocessing as mp
from unittest.mock import Mock, patch, MagicMock
import psutil
from concurrent.futures import TimeoutError

from libs.advanced_process_pool import (
    AdvancedProcessPool,
    ProcessWorker,
    ProcessHealth,
    PoolMetrics,
    WorkItem,
    ProcessPoolConfig
)


class TestAdvancedProcessPool:
    """Test suite for advanced process pool management"""
    
    @pytest.fixture
    def pool_config(self):
        """Create pool configuration"""
        return ProcessPoolConfig(
            min_workers=2,
            max_workers=8,
            warm_pool_size=2,
            max_tasks_per_worker=100,
            worker_timeout=30,
            health_check_interval=5
        )
    
    @pytest.fixture
    def pool(self, pool_config):
        """Create process pool instance"""
        pool = AdvancedProcessPool(pool_config)
        yield pool
        pool.shutdown()
    
    def test_initialization(self, pool, pool_config):
        """Test pool initialization"""
        assert pool.config == pool_config
        assert pool.active_workers == 0
        assert pool.warm_pool_size == 2
        assert pool.metrics.total_tasks == 0
    
    def test_warm_pool_creation(self, pool):
        """Test warm pool pre-creation"""
        pool.initialize_warm_pool()
        
        # Wait for warm pool to be ready
        time.sleep(0.5)
        
        assert pool.get_warm_pool_size() == 2
        assert pool.active_workers == 0  # Warm pool not counted as active
    
    @pytest.mark.asyncio
    async def test_submit_task(self, pool):
        """Test task submission"""
        # Use module-level function to avoid pickle issues
        import operator
        
        pool.start()
        result = await pool.submit(operator.mul, 5, 2)
        
        assert result == 10
        assert pool.metrics.total_tasks == 1
        assert pool.metrics.successful_tasks == 1
    
    @pytest.mark.asyncio
    async def test_batch_submission(self, pool):
        """Test batch task submission"""
        # Use built-in pow function
        pool.start()
        tasks = [(pow, i, 2) for i in range(10)]
        results = await pool.submit_batch(tasks)
        
        assert len(results) == 10
        assert results == [i ** 2 for i in range(10)]
        assert pool.metrics.total_tasks == 10
    
    def test_worker_health_check(self, pool):
        """Test worker health monitoring"""
        pool.start()
        
        # Submit a task to create workers
        pool.submit_sync(lambda: 42)
        time.sleep(0.5)
        
        health_status = pool.get_worker_health()
        assert len(health_status) > 0
        
        for worker_id, health in health_status.items():
            assert isinstance(health, ProcessHealth)
            assert health.status == "healthy"
            assert health.cpu_percent >= 0
            assert health.memory_mb >= 0
    
    def test_worker_recycling(self, pool):
        """Test worker recycling after max tasks"""
        pool.config.max_tasks_per_worker = 3
        pool.start()
        
        initial_worker_id = None
        
        # Submit tasks up to the limit
        for i in range(4):
            result = pool.submit_sync(lambda x: x, i)
            if i == 0:
                initial_worker_id = pool._get_current_worker_id()
        
        # Worker should be recycled after 3 tasks
        final_worker_id = pool._get_current_worker_id()
        assert initial_worker_id != final_worker_id
    
    def test_memory_sharing(self, pool):
        """Test shared memory optimization"""
        import numpy as np
        
        # Create shared array
        shared_array = pool.create_shared_array('float64', (1000, 1000))
        shared_array[:] = np.random.rand(1000, 1000)
        
        def process_shared_data(array_name):
            arr = pool.get_shared_array(array_name)
            return arr.mean()
        
        pool.start()
        result = pool.submit_sync(process_shared_data, 'shared_data')
        
        assert isinstance(result, float)
        assert 0 <= result <= 1
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, pool):
        """Test task timeout handling"""
        def slow_task():
            time.sleep(5)
            return "completed"
        
        pool.start()
        
        with pytest.raises(TimeoutError):
            await pool.submit(slow_task, timeout=1)
        
        assert pool.metrics.failed_tasks == 1
        assert pool.metrics.timeout_tasks == 1
    
    def test_graceful_shutdown(self, pool):
        """Test graceful shutdown"""
        pool.start()
        
        # Submit some tasks
        futures = []
        for i in range(5):
            future = pool.submit_async(lambda x: x * 2, i)
            futures.append(future)
        
        # Shutdown gracefully
        pool.shutdown(wait=True, timeout=5)
        
        # All tasks should complete
        results = [f.result() for f in futures]
        assert results == [0, 2, 4, 6, 8]
        assert pool.is_shutdown
    
    def test_force_shutdown(self, pool):
        """Test forced shutdown"""
        def infinite_task():
            while True:
                time.sleep(0.1)
        
        pool.start()
        pool.submit_async(infinite_task)
        
        # Force shutdown
        pool.shutdown(wait=False)
        
        assert pool.is_shutdown
        assert pool.active_workers == 0
    
    def test_auto_scaling(self, pool):
        """Test automatic scaling based on load"""
        pool.start()
        pool.enable_auto_scaling()
        
        # Submit many tasks to trigger scaling
        tasks = [pool.submit_async(lambda: time.sleep(0.1)) for _ in range(20)]
        
        # Wait for scaling
        time.sleep(0.5)
        
        # Should have scaled up
        assert pool.active_workers > pool.config.min_workers
        
        # Wait for tasks to complete
        for task in tasks:
            task.result()
        
        # Wait for scaling down
        time.sleep(pool.config.scale_down_delay + 1)
        
        # Should scale back down
        assert pool.active_workers <= pool.config.min_workers + 1
    
    def test_process_affinity(self, pool):
        """Test CPU affinity setting"""
        if not hasattr(psutil.Process, 'cpu_affinity'):
            pytest.skip("CPU affinity not supported on this platform")
        
        pool.start()
        pool.set_cpu_affinity([0, 1])  # Bind to first two CPUs
        
        # Submit task and check affinity
        def get_affinity():
            return psutil.Process().cpu_affinity()
        
        result = pool.submit_sync(get_affinity)
        assert set(result).issubset({0, 1})
    
    def test_metrics_collection(self, pool):
        """Test metrics collection and export"""
        pool.start()
        
        # Submit various tasks
        pool.submit_sync(lambda: 42)  # Success
        pool.submit_sync(lambda: 1/0)  # Failure
        
        time.sleep(0.1)
        
        metrics = pool.export_metrics()
        
        assert metrics['total_tasks'] == 2
        assert metrics['successful_tasks'] == 1
        assert metrics['failed_tasks'] == 1
        assert 'avg_task_duration' in metrics
        assert 'worker_utilization' in metrics
    
    @pytest.mark.asyncio
    async def test_priority_queue(self, pool):
        """Test priority-based task execution"""
        results = []
        
        def task(value, priority):
            results.append((value, priority))
            return value
        
        pool.start()
        
        # Submit tasks with different priorities
        await pool.submit(task, args=(1, 'low'), priority=1)
        await pool.submit(task, args=(2, 'high'), priority=10)
        await pool.submit(task, args=(3, 'medium'), priority=5)
        
        # High priority should execute first
        time.sleep(0.5)
        assert results[0][1] == 'high'
    
    def test_worker_isolation(self, pool):
        """Test process isolation"""
        def create_global():
            import __main__
            __main__.test_var = "isolated"
            return True
        
        def check_global():
            import __main__
            return hasattr(__main__, 'test_var')
        
        pool.start()
        
        # Create variable in one worker
        pool.submit_sync(create_global)
        
        # Check in another worker (should not exist)
        result = pool.submit_sync(check_global)
        assert result is False  # Isolated
    
    def test_error_recovery(self, pool):
        """Test error recovery mechanisms"""
        error_count = 0
        
        def flaky_task():
            nonlocal error_count
            error_count += 1
            """flaky_taskメソッド"""
            if error_count < 3:
                raise Exception("Temporary error")
            return "success"
        
        pool.start()
        pool.enable_retry(max_retries=3)
        
        result = pool.submit_sync(flaky_task)
        assert result == "success"
        assert pool.metrics.retry_count == 2
    
    def test_resource_limits(self, pool):
        """Test resource limit enforcement"""
        pool.config.max_memory_per_worker = 100  # 100MB limit
        pool.start()
        
        def memory_intensive_task():
            # Try to allocate large array
            """memory_intensive_taskメソッド"""
            import numpy as np
            try:
                arr = np.zeros((1000, 1000, 100))  # ~800MB
                return "allocated"
            except MemoryError:
                return "limited"
        
        result = pool.submit_sync(memory_intensive_task)
        assert result == "limited"
    
    def test_warm_pool_performance(self, pool):
        """Test performance improvement with warm pool"""
        pool.initialize_warm_pool()
        time.sleep(0.5)
        
        # Measure cold start
        cold_start = time.time()
        pool.submit_sync(lambda: 42)
        cold_duration = time.time() - cold_start
        
        # Measure warm start
        warm_start = time.time()
        pool.submit_sync(lambda: 42)
        warm_duration = time.time() - warm_start
        
        # Warm start should be faster
        assert warm_duration < cold_duration * 0.5
    
    def test_distributed_lock(self, pool):
        """Test distributed locking mechanism"""
        counter = pool.create_shared_value('i', 0)
        lock = pool.create_lock('counter_lock')
        
        def increment_counter():
            """increment_counterメソッド"""
            with lock:
                current = counter.value
                time.sleep(0.01)  # Simulate work
                counter.value = current + 1
        
        pool.start()
        
        # Submit concurrent increments
        futures = [pool.submit_async(increment_counter) for _ in range(10)]
        
        # Wait for completion
        for f in futures:
            f.result()
        
        assert counter.value == 10  # No race condition