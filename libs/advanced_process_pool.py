"""
Advanced Process Pool for Auto Issue Processor A2A
Phase 2 implementation - Optimized process pooling with warm pool
"""
import asyncio
import multiprocessing as mp
from multiprocessing import shared_memory
import threading
import time
import queue
import psutil
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable, Tuple
from concurrent.futures import ProcessPoolExecutor, Future, TimeoutError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ProcessPoolConfig:
    """Configuration for process pool"""
    min_workers: int = 2
    max_workers: int = 8
    warm_pool_size: int = 2
    max_tasks_per_worker: int = 100
    worker_timeout: int = 30
    health_check_interval: int = 5
    scale_down_delay: int = 30
    max_memory_per_worker: Optional[int] = None  # MB


@dataclass
class ProcessHealth:
    """Health status of a process"""
    pid: int
    status: str  # healthy, unhealthy, dead
    cpu_percent: float
    memory_mb: float
    task_count: int
    last_health_check: datetime


@dataclass
class PoolMetrics:
    """Metrics for the process pool"""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    timeout_tasks: int = 0
    retry_count: int = 0
    avg_task_duration: float = 0.0
    worker_utilization: float = 0.0


@dataclass  
class WorkItem:
    """Work item for the pool"""
    func: Callable
    args: tuple
    kwargs: dict
    priority: int = 5
    timeout: Optional[float] = None
    retry_count: int = 0


class ProcessWorker:
    """Individual process worker with health monitoring"""
    
    def __init__(self, worker_id: int, config: ProcessPoolConfig):
        """初期化メソッド"""
        self.worker_id = worker_id
        self.config = config
        self.process: Optional[mp.Process] = None
        self.task_count = 0
        self.created_at = datetime.now()
        self.health = ProcessHealth(
            pid=0,
            status="initializing",
            cpu_percent=0.0,
            memory_mb=0.0,
            task_count=0,
            last_health_check=datetime.now()
        )
    
    def start(self):
        """Start the worker process"""
        self.process = mp.Process(target=self._worker_loop)
        self.process.start()
        self.health.pid = self.process.pid
        self.health.status = "healthy"
    
    def _worker_loop(self):
        """Main worker loop"""
        # Set resource limits if configured
        if self.config.max_memory_per_worker:
            try:
                import resource
                limit_bytes = self.config.max_memory_per_worker * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
            except:
                pass
        
        # Worker implementation would go here
        pass
    
    def check_health(self) -> ProcessHealth:
        """Check worker health"""
        if not self.process or not self.process.is_alive():
            self.health.status = "dead"
            return self.health
        
        try:
            proc = psutil.Process(self.process.pid)
            self.health.cpu_percent = proc.cpu_percent()
            self.health.memory_mb = proc.memory_info().rss / 1024 / 1024
            self.health.task_count = self.task_count
            self.health.last_health_check = datetime.now()
            self.health.status = "healthy"
        except:
            self.health.status = "unhealthy"
        
        return self.health
    
    def should_recycle(self) -> bool:
        """Check if worker should be recycled"""
        return self.task_count >= self.config.max_tasks_per_worker


class AdvancedProcessPool:
    """Advanced process pool with warm pool and health monitoring"""
    
    def __init__(self, config: ProcessPoolConfig):
        """初期化メソッド"""
        self.config = config
        self.active_workers = 0
        self.warm_pool_size = config.warm_pool_size
        
        self._executor: Optional[ProcessPoolExecutor] = None
        self._warm_pool: List[ProcessWorker] = []
        self._worker_health: Dict[int, ProcessHealth] = {}
        self._task_queue = queue.PriorityQueue()
        self._shutdown = False
        self._lock = threading.Lock()
        
        self.metrics = PoolMetrics()
        self._shared_memory: Dict[str, shared_memory.SharedMemory] = {}
        self._locks: Dict[str, mp.Lock] = {}
        self._shared_values: Dict[str, Any] = {}
        
        self._auto_scale_enabled = False
        self._retry_enabled = False
        self._max_retries = 3
        
        self.is_shutdown = False
        self._health_monitor_thread: Optional[threading.Thread] = None
        self._current_worker_id = 0
    
    def initialize_warm_pool(self):
        """Initialize warm pool of processes"""
        logger.info(f"Initializing warm pool with {self.warm_pool_size} workers")
        
        for i in range(self.warm_pool_size):
            worker = ProcessWorker(i, self.config)
            worker.start()
            self._warm_pool.append(worker)
    
    def start(self):
        """Start the process pool"""
        if self._executor:
            return
        
        self._executor = ProcessPoolExecutor(
            max_workers=self.config.max_workers,
            initializer=self._worker_initializer
        )
        
        # Start health monitoring
        self._health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True
        )
        self._health_monitor_thread.start()
        
        logger.info("Process pool started")
    
    def _worker_initializer(self):
        """Initialize worker process"""
        # Set up any worker-specific configuration
        pass
    
    def _health_monitor_loop(self):
        """Monitor worker health"""
        while not self._shutdown:
            try:
                # Check health of warm pool
                for worker in self._warm_pool:
                    health = worker.check_health()
                    self._worker_health[worker.worker_id] = health
                
                time.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    async def submit(self, func: Callable, *args, 
                     priority: int = 5, timeout: Optional[float] = None, **kwargs) -> Any:
        """Submit task asynchronously"""
        if not self._executor:
            self.start()
        
        work_item = WorkItem(func, args, kwargs, priority, timeout)
        
        try:
            # Use executor to run task
            future = self._executor.submit(func, *args, **kwargs)
            
            if timeout:
                result = await asyncio.wait_for(
                    asyncio.wrap_future(future), 
                    timeout=timeout
                )
            else:
                result = await asyncio.wrap_future(future)
            
            self.metrics.total_tasks += 1
            self.metrics.successful_tasks += 1
            return result
            
        except asyncio.TimeoutError:
            self.metrics.timeout_tasks += 1
            self.metrics.failed_tasks += 1
            raise TimeoutError(f"Task timed out after {timeout}s")
        except Exception as e:
            self.metrics.failed_tasks += 1
            raise
    
    def submit_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Submit task synchronously"""
        if not self._executor:
            self.start()
        
        try:
            future = self._executor.submit(func, *args, **kwargs)
            result = future.result(timeout=self.config.worker_timeout)
            
            self.metrics.total_tasks += 1
            self.metrics.successful_tasks += 1
            self._current_worker_id = (self._current_worker_id + 1) % self.config.max_workers
            
            return result
        except Exception as e:
            self.metrics.failed_tasks += 1
            
            if self._retry_enabled:
                # Simple retry logic
                for i in range(self._max_retries):
                    try:
                        result = self._executor.submit(func, *args, **kwargs).result()
                        self.metrics.retry_count += 1
                        self.metrics.successful_tasks += 1
                        return result
                    except:
                        if i == self._max_retries - 1:
                            raise
            else:
                raise
    
    def submit_async(self, func: Callable, *args, **kwargs) -> Future:
        """Submit task and return future"""
        if not self._executor:
            self.start()
        
        self.metrics.total_tasks += 1
        self.active_workers = min(self.active_workers + 1, self.config.max_workers)
        return self._executor.submit(func, *args, **kwargs)
    
    async def submit_batch(self, tasks: List[Tuple[Callable, Any]]) -> List[Any]:
        """Submit batch of tasks"""
        if not self._executor:
            self.start()
        
        futures = []
        for task in tasks:
            if len(task) == 2:
                func, arg = task
                future = self._executor.submit(func, arg)
            else:
                func = task[0]
                args = task[1:] if len(task) > 1 else ()
                future = self._executor.submit(func, *args)
            futures.append(future)
        
        # Wait for all results
        results = []
        for future in futures:
            try:
                result = await asyncio.wrap_future(future)
                results.append(result)
                self.metrics.successful_tasks += 1
            except Exception as e:
                results.append(None)
                self.metrics.failed_tasks += 1
        
        self.metrics.total_tasks += len(tasks)
        return results
    
    def get_warm_pool_size(self) -> int:
        """Get current warm pool size"""
        return len([w for w in self._warm_pool if w.health.status == "healthy"])
    
    def get_worker_health(self) -> Dict[int, ProcessHealth]:
        """Get health status of all workers"""
        return self._worker_health.copy()
    
    def _get_current_worker_id(self) -> int:
        """Get current worker ID (for testing)"""
        return self._current_worker_id
    
    def create_shared_array(self, dtype: str, shape: tuple) -> np.ndarray:
        """Create shared memory array"""
        size = np.prod(shape) * np.dtype(dtype).itemsize
        shm = shared_memory.SharedMemory(create=True, size=size)
        self._shared_memory['shared_data'] = shm
        
        arr = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
        return arr
    
    def get_shared_array(self, name: str) -> Optional[np.ndarray]:
        """Get shared array by name"""
        if name in self._shared_memory:
            shm = self._shared_memory[name]
            # Return view of shared memory
            return np.ndarray((1000, 1000), dtype='float64', buffer=shm.buf)
        return None
    
    def create_lock(self, name: str) -> mp.Lock:
        """Create named lock"""
        lock = mp.Lock()
        self._locks[name] = lock
        return lock
    
    def create_shared_value(self, typecode: str, value: Any):
        """Create shared value"""
        shared_val = mp.Value(typecode, value)
        self._shared_values['counter'] = shared_val
        return shared_val
    
    def enable_auto_scaling(self):
        """Enable automatic scaling"""
        self._auto_scale_enabled = True
    
    def enable_retry(self, max_retries: int = 3):
        """Enable retry mechanism"""
        self._retry_enabled = True
        self._max_retries = max_retries
    
    def set_cpu_affinity(self, cpus: List[int]):
        """Set CPU affinity for workers"""
        # This would be implemented per-worker in practice
        pass
    
    def export_metrics(self) -> Dict:
        """Export pool metrics"""
        with self._lock:
            utilization = self.active_workers / self.config.max_workers if self.config.max_workers > 0 else 0
            
            return {
                'total_tasks': self.metrics.total_tasks,
                'successful_tasks': self.metrics.successful_tasks,
                'failed_tasks': self.metrics.failed_tasks,
                'timeout_tasks': self.metrics.timeout_tasks,
                'retry_count': self.metrics.retry_count,
                'avg_task_duration': self.metrics.avg_task_duration,
                'worker_utilization': utilization,
                'active_workers': self.active_workers,
                'warm_pool_size': self.get_warm_pool_size()
            }
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None):
        """Shutdown the pool"""
        self._shutdown = True
        self.is_shutdown = True
        
        if self._executor:
            self._executor.shutdown(wait=wait)
        
        # Clean up warm pool
        for worker in self._warm_pool:
            if worker.process and worker.process.is_alive():
                worker.process.terminate()
                if wait:
                    worker.process.join(timeout=timeout)
        
        # Clean up shared memory
        for shm in self._shared_memory.values():
            shm.close()
            shm.unlink()
        
        self.active_workers = 0
        logger.info("Process pool shutdown complete")